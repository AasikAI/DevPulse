import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.github_integration.errors import GitHubRateLimitedError, GitHubUnavailableError
from app.synchronization.runner import run_repository_list_sync
from app.synchronization.service import SyncOutcome
from tests.fake_github import FAKE_INSTALLATION_TOKEN, FakeGitHub, make_repo
from tests.helpers import make_connection, scalar


async def run(github: FakeGitHub, connection_id: uuid.UUID, trigger: str = "schedule") -> SyncOutcome:
    return await run_repository_list_sync(
        connection_id, trigger, http_transport=httpx.MockTransport(github.handler)
    )


async def rows(sql: str) -> list[tuple]:
    async with SessionLocal() as session:
        return [tuple(row) for row in (await session.execute(text(sql))).all()]


# --- Scenario: after connecting, DevPulse fetches the repositories ----------------------


async def test_the_repositories_the_app_can_access_are_stored(github: FakeGitHub):
    connection_id = await make_connection()

    outcome = await run(github, connection_id, "connected")

    assert outcome == SyncOutcome.SUCCEEDED
    assert await rows("SELECT github_repo_id, full_name, is_private, is_available FROM repositories ORDER BY github_repo_id") == [
        (1, "octocat/repo-1", False, True),
        (2, "octocat/repo-2", False, True),
        (3, "octocat/repo-3", True, True),
    ]
    assert await scalar("SELECT repositories_synced_at IS NOT NULL FROM github_connections") is True
    assert await rows("SELECT kind, trigger, status, error_category FROM sync_runs") == [
        ("repository_list", "connected", "succeeded", None)
    ]


async def test_running_the_job_again_does_not_create_duplicates(github: FakeGitHub):
    connection_id = await make_connection()

    await run(github, connection_id)
    await run(github, connection_id)

    assert await scalar("SELECT count(*) FROM repositories") == 3
    assert await scalar("SELECT count(*) FROM sync_runs WHERE status = 'succeeded'") == 2


async def test_a_large_account_is_stored_across_all_pages(github: FakeGitHub):
    github.repositories = [make_repo(i) for i in range(1, 251)]
    connection_id = await make_connection()

    await run(github, connection_id)

    assert await scalar("SELECT count(*) FROM repositories") == 250


async def test_a_renamed_repository_is_updated_not_duplicated(github: FakeGitHub):
    connection_id = await make_connection()
    await run(github, connection_id)
    github.repositories[0] = make_repo(1, "renamed", owner="octocat")

    await run(github, connection_id)

    assert await scalar("SELECT count(*) FROM repositories WHERE github_repo_id = 1") == 1
    assert await scalar("SELECT full_name FROM repositories WHERE github_repo_id = 1") == "octocat/renamed"


async def test_a_repository_the_app_can_no_longer_see_is_hidden_and_kept(github: FakeGitHub):
    connection_id = await make_connection()
    await run(github, connection_id)
    removed = github.repositories.pop()  # repo 3

    await run(github, connection_id)

    assert await scalar("SELECT is_available FROM repositories WHERE github_repo_id = 3") is False
    assert await scalar("SELECT count(*) FROM repositories") == 3  # row kept

    github.repositories.append(removed)
    await run(github, connection_id)
    assert await scalar("SELECT is_available FROM repositories WHERE github_repo_id = 3") is True


async def test_removing_every_repository_hides_them_all(github: FakeGitHub):
    connection_id = await make_connection()
    await run(github, connection_id)
    github.repositories.clear()

    await run(github, connection_id)

    assert await scalar("SELECT count(*) FROM repositories WHERE is_available") == 0


async def test_each_connection_only_gets_its_own_repositories(github: FakeGitHub):
    first = await make_connection(github_user_id=1001, installation_id=5001)
    other = await make_connection(github_user_id=2002, installation_id=6002)
    github.installations[6002] = {**github.installations[5001], "id": 6002}

    await run(github, first)

    assert await scalar(f"SELECT count(*) FROM repositories WHERE connection_id = '{first}'") == 3
    assert await scalar(f"SELECT count(*) FROM repositories WHERE connection_id = '{other}'") == 0


# --- Scenario: Access is removed on GitHub -------------------------------------------------


@pytest.mark.parametrize(
    "problem, reason",
    [
        ("revoked", "access_revoked"),
        ("suspended", "suspended"),
        ("permission", "permission_missing"),
    ],
)
async def test_lost_access_stops_the_job_and_marks_the_connection(github: FakeGitHub, problem, reason):
    connection_id = await make_connection()
    if problem == "revoked":
        github.installations.clear()
    elif problem == "suspended":
        github.installations[5001]["suspended_at"] = "2026-11-01T00:00:00Z"
    else:
        github.installations[5001]["permissions"] = {"metadata": "read"}

    outcome = await run(github, connection_id)  # returns normally: nothing to retry

    assert outcome == SyncOutcome.NEEDS_ATTENTION
    assert await rows("SELECT status, status_reason FROM github_connections") == [("needs_attention", reason)]
    assert await rows("SELECT status, error_category FROM sync_runs") == [("failed", reason)]


async def test_a_connection_that_needs_attention_is_not_fetched(github: FakeGitHub):
    connection_id = await make_connection(status="needs_attention", reason="access_revoked")

    outcome = await run(github, connection_id)

    assert outcome == SyncOutcome.SKIPPED_NOT_ACTIVE
    assert github.requests == []
    assert await scalar("SELECT count(*) FROM sync_runs") == 0


# --- Scenario: GitHub is temporarily unavailable -------------------------------------------


async def test_a_github_outage_keeps_earlier_data_and_asks_for_a_retry(github: FakeGitHub):
    connection_id = await make_connection()
    await run(github, connection_id)
    github.unavailable = True

    with pytest.raises(GitHubUnavailableError):
        await run(github, connection_id)

    assert await scalar("SELECT count(*) FROM repositories WHERE is_available") == 3
    assert await scalar("SELECT status FROM github_connections") == "active"
    assert await rows("SELECT status, error_category FROM sync_runs ORDER BY started_at") == [
        ("succeeded", None),
        ("failed", "github_unavailable"),
    ]


async def test_a_failure_halfway_through_the_list_stores_nothing_partial(github: FakeGitHub):
    github.repositories = [make_repo(i) for i in range(1, 251)]
    github.repositories_error_on_page = (2, 503)
    connection_id = await make_connection()

    with pytest.raises(GitHubUnavailableError):
        await run(github, connection_id)

    assert await scalar("SELECT count(*) FROM repositories") == 0
    assert await scalar("SELECT repositories_synced_at IS NULL FROM github_connections") is True


async def test_a_short_rate_limit_asks_for_a_retry(github: FakeGitHub):
    github.token_error = (
        403,
        {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(time.time()) + 120)},
        {"message": "API rate limit exceeded"},
    )
    connection_id = await make_connection()

    with pytest.raises(GitHubRateLimitedError) as raised:
        await run(github, connection_id)

    assert raised.value.retry_after <= 120
    assert await scalar("SELECT status FROM sync_runs") == "rate_limited"


async def test_a_long_rate_limit_ends_the_run_without_retrying(github: FakeGitHub):
    github.token_error = (
        403,
        {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(time.time()) + 3 * 3600)},
        {"message": "API rate limit exceeded"},
    )
    connection_id = await make_connection()

    outcome = await run(github, connection_id)

    assert outcome == SyncOutcome.RATE_LIMITED
    assert await rows("SELECT status, error_category FROM sync_runs") == [("rate_limited", "rate_limited")]
    assert await scalar("SELECT status FROM github_connections") == "active"


# --- Duplicate delivery -------------------------------------------------------------------------


async def test_a_second_delivery_while_one_is_running_does_nothing(github: FakeGitHub):
    connection_id = await make_connection()
    async with SessionLocal() as session:
        await session.execute(
            text(
                "INSERT INTO sync_runs (id, connection_id, kind, trigger, status, started_at) "
                "VALUES (gen_random_uuid(), :c, 'repository_list', 'schedule', 'running', now())"
            ),
            {"c": connection_id},
        )
        await session.commit()

    outcome = await run(github, connection_id)

    assert outcome == SyncOutcome.SKIPPED_ALREADY_RUNNING
    assert github.requests == []
    assert await scalar("SELECT count(*) FROM sync_runs") == 1


async def test_a_run_left_behind_by_a_crashed_worker_does_not_block_forever(github: FakeGitHub):
    connection_id = await make_connection()
    async with SessionLocal() as session:
        await session.execute(
            text(
                "INSERT INTO sync_runs (id, connection_id, kind, trigger, status, started_at) "
                "VALUES (gen_random_uuid(), :c, 'repository_list', 'schedule', 'running', :started)"
            ),
            {"c": connection_id, "started": datetime.now(UTC) - timedelta(minutes=30)},
        )
        await session.commit()

    outcome = await run(github, connection_id)

    assert outcome == SyncOutcome.SUCCEEDED
    assert await rows("SELECT status, error_category FROM sync_runs ORDER BY started_at") == [
        ("failed", "abandoned"),
        ("succeeded", None),
    ]


async def test_concurrent_deliveries_never_leave_duplicates_or_two_running_rows(github: FakeGitHub):
    connection_id = await make_connection()

    outcomes = await asyncio.gather(*(run(github, connection_id) for _ in range(4)))

    assert SyncOutcome.SUCCEEDED in outcomes
    assert await scalar("SELECT count(*) FROM repositories") == 3
    assert await scalar("SELECT count(*) FROM sync_runs WHERE status = 'running'") == 0


async def test_the_database_allows_only_one_running_job_per_connection():
    connection_id = await make_connection()
    insert = text(
        "INSERT INTO sync_runs (id, connection_id, kind, trigger, status, started_at) "
        "VALUES (gen_random_uuid(), :c, 'repository_list', 'schedule', 'running', now())"
    )
    async with SessionLocal() as session:
        await session.execute(insert, {"c": connection_id})
        await session.commit()
        with pytest.raises(IntegrityError):
            await session.execute(insert, {"c": connection_id})
            await session.commit()


async def test_a_job_for_an_unknown_connection_is_ignored(github: FakeGitHub):
    outcome = await run(github, uuid.uuid4())

    assert outcome == SyncOutcome.SKIPPED_NOT_FOUND
    assert github.requests == []


# --- Credentials -------------------------------------------------------------------------------


async def test_the_installation_token_is_never_stored_or_logged(github: FakeGitHub, caplog):
    caplog.set_level(logging.DEBUG)
    connection_id = await make_connection()

    await run(github, connection_id)

    dump = await scalar(
        "SELECT coalesce((SELECT string_agg(row_to_json(c)::text, '') FROM github_connections c), '')"
        " || coalesce((SELECT string_agg(row_to_json(r)::text, '') FROM repositories r), '')"
        " || coalesce((SELECT string_agg(row_to_json(s)::text, '') FROM sync_runs s), '')"
    )
    logged = " ".join(
        f"{record.getMessage()} {sorted(map(str, record.__dict__.values()))}" for record in caplog.records
    )
    assert FAKE_INSTALLATION_TOKEN not in dump
    assert FAKE_INSTALLATION_TOKEN not in logged
    assert "BEGIN" not in logged
