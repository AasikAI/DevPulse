import asyncio
import inspect
import logging
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.github_integration.errors import GitHubRateLimitedError, GitHubUnavailableError
from app.synchronization import tasks
from app.synchronization.celery_app import REPOSITORY_LIST_TASK, celery_app
from app.synchronization.dispatcher import CelerySyncDispatcher
from app.synchronization.retry import MAX_DELAY_SECONDS, MAX_RETRIES, retry_delay_seconds
from app.synchronization.service import SyncOutcome


async def run_task(*args, **kwargs):
    """Celery runs tasks in a plain thread with no event loop; do the same here."""
    return await asyncio.to_thread(tasks.sync_repository_list.apply, *args, **kwargs)


# --- The task is a thin entry point ------------------------------------------------------------


def test_the_task_accepts_an_internal_id_and_a_trigger_but_no_credentials():
    parameters = list(inspect.signature(tasks.sync_repository_list.run).parameters)

    assert parameters == ["connection_id", "trigger"]
    assert tasks.sync_repository_list.name == REPOSITORY_LIST_TASK


async def test_the_task_hands_the_connection_id_to_the_service(monkeypatch):
    runner = AsyncMock(return_value=SyncOutcome.SUCCEEDED)
    monkeypatch.setattr(tasks, "run_repository_list_sync", runner)
    connection_id = uuid.uuid4()

    result = await run_task(args=[str(connection_id), "connected"])

    assert result.successful()
    runner.assert_awaited_once_with(connection_id, "connected")


async def test_the_task_is_registered_with_the_worker_app():
    assert REPOSITORY_LIST_TASK in celery_app.tasks


# --- Retries ---------------------------------------------------------------------------------------


async def test_temporary_github_problems_are_retried_a_bounded_number_of_times(monkeypatch):
    runner = AsyncMock(side_effect=GitHubUnavailableError())
    monkeypatch.setattr(tasks, "run_repository_list_sync", runner)

    result = await run_task(args=[str(uuid.uuid4())], throw=False)

    assert result.failed()
    assert runner.await_count == MAX_RETRIES + 1


async def test_a_rate_limit_is_retried_like_any_temporary_problem(monkeypatch):
    runner = AsyncMock(side_effect=GitHubRateLimitedError(retry_after=30, reset_at=None))
    monkeypatch.setattr(tasks, "run_repository_list_sync", runner)

    result = await run_task(args=[str(uuid.uuid4())], throw=False)

    assert result.failed()
    assert runner.await_count == MAX_RETRIES + 1


async def test_an_unexpected_error_is_tried_once_more_and_then_stops(monkeypatch):
    runner = AsyncMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(tasks, "run_repository_list_sync", runner)

    result = await run_task(args=[str(uuid.uuid4())], throw=False)

    assert result.failed()
    assert runner.await_count == 2


async def test_a_job_that_finds_lost_access_is_not_retried(monkeypatch):
    runner = AsyncMock(return_value=SyncOutcome.NEEDS_ATTENTION)
    monkeypatch.setattr(tasks, "run_repository_list_sync", runner)

    result = await run_task(args=[str(uuid.uuid4())])

    assert result.successful()
    assert runner.await_count == 1


def test_retry_delay_grows_with_each_attempt_and_is_capped():
    middle = lambda: 0.5  # noqa: E731
    delays = [retry_delay_seconds(n, rng=middle) for n in range(8)]

    assert delays == sorted(delays)
    assert delays[0] == 45  # 60 s base, half fixed plus half jitter
    assert max(delays) <= MAX_DELAY_SECONDS
    assert delays[-1] == int(MAX_DELAY_SECONDS * 0.75)


def test_retry_delay_stays_inside_its_jitter_window():
    low = retry_delay_seconds(2, rng=lambda: 0.0)
    high = retry_delay_seconds(2, rng=lambda: 0.999999)

    assert low == 120  # half of 240 s
    assert 238 <= high <= 240


def test_a_rate_limit_wait_is_honoured_but_capped():
    assert retry_delay_seconds(0, retry_after=100, rng=lambda: 0.0) == 100
    assert retry_delay_seconds(0, retry_after=10 * 3600, rng=lambda: 0.0) == MAX_DELAY_SECONDS


# --- Queueing --------------------------------------------------------------------------------------------


async def test_queueing_sends_only_the_connection_id_and_trigger(monkeypatch):
    send_task = MagicMock()
    monkeypatch.setattr(celery_app, "send_task", send_task)
    connection_id = uuid.uuid4()

    queued = await CelerySyncDispatcher().dispatch_repository_list(connection_id, "connected")

    assert queued is True
    send_task.assert_called_once_with(
        REPOSITORY_LIST_TASK, args=[str(connection_id)], kwargs={"trigger": "connected"}
    )


async def test_a_queue_failure_is_reported_not_raised(monkeypatch, caplog):
    monkeypatch.setattr(celery_app, "send_task", MagicMock(side_effect=ConnectionError("redis://:secret@host")))
    caplog.set_level(logging.DEBUG)

    queued = await CelerySyncDispatcher().dispatch_repository_list(uuid.uuid4(), "connected")

    assert queued is False
    assert "secret" not in " ".join(f"{r.getMessage()} {r.__dict__}" for r in caplog.records)
