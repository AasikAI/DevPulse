import asyncio
import logging
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from celery import Task
from celery.exceptions import MaxRetriesExceededError

from app.github_integration.errors import GitHubUnavailableError
from app.synchronization.celery_app import (
    DISPATCH_DUE_TASK,
    PULL_REQUESTS_TASK,
    REPOSITORY_LIST_TASK,
    celery_app,
)
from app.synchronization.retry import (
    BUSY_RETRIES,
    BUSY_RETRY_SECONDS,
    MAX_RETRIES,
    retry_delay_seconds,
)
from app.synchronization.runner import (
    run_dispatch_due_syncs,
    run_pull_request_sync,
    run_repository_list_sync,
)
from app.synchronization.service import SyncOutcome

logger = logging.getLogger(__name__)

# Unexpected errors get one more try, then stop; the next scheduled run starts fresh.
UNEXPECTED_ERROR_RETRIES = 1


def _execute(
    task: Task, make_job: Callable[[], Coroutine[Any, Any, SyncOutcome]], trigger: str
) -> None:
    """Run a job and decide whether to try again. The job itself holds all the logic."""
    try:
        outcome = asyncio.run(make_job())
    except GitHubUnavailableError as exc:
        # Temporary: GitHub down or rate limiting. Retry later with a growing delay.
        raise task.retry(
            exc=exc, countdown=retry_delay_seconds(task.request.retries, exc.retry_after)
        ) from exc
    except Exception as exc:
        if task.request.retries >= UNEXPECTED_ERROR_RETRIES:
            raise
        raise task.retry(
            exc=exc,
            countdown=retry_delay_seconds(task.request.retries),
            max_retries=UNEXPECTED_ERROR_RETRIES,
        ) from exc

    if outcome == SyncOutcome.SKIPPED_ALREADY_RUNNING and trigger != "schedule":
        # A user action (connecting, saving a selection) must not wait for the next
        # scheduled run just because another job was busy a moment ago.
        try:
            raise task.retry(countdown=BUSY_RETRY_SECONDS, max_retries=BUSY_RETRIES)
        except MaxRetriesExceededError:
            logger.warning("gave up waiting for a running job; the schedule will pick it up")


@celery_app.task(bind=True, name=REPOSITORY_LIST_TASK, max_retries=MAX_RETRIES)
def sync_repository_list(self: Task, connection_id: str, trigger: str = "schedule") -> None:
    """Fetch the repositories a connection's App installation can access.

    Receives only the internal connection ID.
    """
    _execute(self, lambda: run_repository_list_sync(uuid.UUID(connection_id), trigger), trigger)


@celery_app.task(bind=True, name=PULL_REQUESTS_TASK, max_retries=MAX_RETRIES)
def sync_pull_requests(self: Task, connection_id: str, trigger: str = "schedule") -> None:
    """Refresh a connection's repositories and import pull requests for the selected ones.

    Receives only the internal connection ID.
    """
    _execute(self, lambda: run_pull_request_sync(uuid.UUID(connection_id), trigger), trigger)


@celery_app.task(name=DISPATCH_DUE_TASK)
def dispatch_due_syncs() -> None:
    """Run by Celery Beat: queue a pull request job for every connection that is due."""
    asyncio.run(run_dispatch_due_syncs())
