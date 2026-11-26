import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import text

from app.db import SessionLocal
from app.github_integration.errors import GitHubRateLimitedError, GitHubUnavailableError
from app.github_integration.schemas import GitHubRepositoryInfo
from app.synchronization.runner import (
    run_dispatch_due_syncs,
    run_pull_request_sync,
    run_repository_list_sync,
)
from app.synchronization.service import SyncOutcome
from tests.conftest import RecordingDispatcher
from tests.fake_github import (
    FAKE_INSTALLATION_TOKEN,
    FakeGitHub,
    make_pr,
    make_review,
)
from tests.helpers import make_connection, scalar, store_repositories

REPO_1 = "octocat/repo-1"
REPO_2 = "octocat/repo-2"


async def rows(sql: str, **params) -> list[tuple]:
    async with SessionLocal() as session:
        return [tuple(row) for row in (await session.execute(text(sql), params)).all()]


async def execute(sql: str, **params) -> None:
    async with SessionLocal() as session:
        await session.execute(text(sql), params)
        await session.commit()


async def tracking(github: FakeGitHub, *github_ids: int, **connection_args) -> uuid.UUID:
    """A connection whose repositories are stored, with these repositories selected."""
    connection_id = await make_connection(**connection_args)
    await store_repositories(
        connection_id,
        [
            GitHubRepositoryInfo(
                id=r["id"],
                name=r["name"],
                full_name=r["full_name"],
                owner_login=r["owner"]["login"],
                is_private=r["private"],
            )
            for r in github.repositories
        ],
    )
    await execute(
        "UPDATE repositories SET is_selected = true WHERE github_repo_id = ANY(:ids) AND connection_id = :c",
        ids=list(github_ids),
        c=connection_id,
    )
    return connection_id


async def sync(
    github: FakeGitHub, connection_id: uuid.UUID, trigger: str = "schedule", **kwargs
) -> SyncOutcome:
    return await run_pull_request_sync(
        connection_id, trigger, http_transport=httpx.MockTransport(github.handler), **kwargs
    )


def many(count: int, **kwargs) -> list[dict]:
    return [make_pr(n, **kwargs) for n in range(1, count + 1)]


# --- Scenario: The scheduled job stores pull request data ------------------------------------


async def test_pull_requests_of_the_selected_repositories_are_stored(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    github.pull_requests[REPO_2] = many(2)
    connection_id = await tracking(github, 1)

    outcome = await sync(github, connection_id, "selection_saved")

    assert outcome == SyncOutcome.SUCCEEDED
    assert await scalar("SELECT count(*) FROM pull_requests") == 3
    assert github.pull_list_calls(REPO_2) == []  # repo-2 is not selected, so never fetched


async def test_pull_request_fields_are_stored_and_nothing_else(github: FakeGitHub):
    github.pull_requests[REPO_1] = [
        make_pr(1, state="open", draft=True, title="Add login", author="alice", branch="login"),
        make_pr(2, state="closed"),
        make_pr(3, state="closed", merged="2026-02-02T09:00:00Z", author=None),
    ]
    connection_id = await tracking(github, 1)

    await sync(github, connection_id)

    assert await rows(
        "SELECT number, state, is_draft, title, author_login, head_branch, merged_at IS NOT NULL "
        "FROM pull_requests ORDER BY number"
    ) == [
        (1, "open", True, "Add login", "alice", "login", False),
        (2, "closed", False, "Change 2", "alice", "feature-2", False),
        (3, "merged", False, "Change 3", None, None, True),
    ]
    dump = await scalar("SELECT string_agg(row_to_json(p)::text, '') FROM pull_requests p")
    assert "SECRET BODY TEXT" not in dump  # bodies and labels are never kept


async def test_running_again_does_not_create_duplicates(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(5)
    connection_id = await tracking(github, 1)

    await sync(github, connection_id)
    await sync(github, connection_id)

    assert await scalar("SELECT count(*) FROM pull_requests") == 5
    assert await scalar("SELECT count(*) FROM sync_runs WHERE kind = 'pull_requests' AND status = 'succeeded'") == 2


async def test_the_whole_history_is_imported_across_all_pages(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(120)  # 50 + 50 + 20
    connection_id = await tracking(github, 1)

    await sync(github, connection_id)

    assert await scalar("SELECT count(*) FROM pull_requests") == 120
    assert await rows(
        "SELECT backfill_completed_at IS NOT NULL, incremental_watermark IS NOT NULL, last_synced_at IS NOT NULL FROM repositories WHERE github_repo_id = 1"
    ) == [(True, True, True)]


async def test_the_repository_list_is_refreshed_on_every_run(github: FakeGitHub):
    connection_id = await tracking(github)  # nothing selected
    github.repositories.append({**github.repositories[0], "id": 4, "name": "brand-new", "full_name": "octocat/brand-new"})

    outcome = await sync(github, connection_id)

    assert outcome == SyncOutcome.SUCCEEDED
    assert await scalar("SELECT count(*) FROM repositories WHERE github_repo_id = 4") == 1
    assert github.pull_list_calls() == []  # nothing selected, so no pull request calls


# --- Scenario: a large history finishes over several runs -------------------------------------


async def test_a_run_stops_at_its_budget_and_the_next_run_continues(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(120)
    connection_id = await tracking(github, 1)

    first = await sync(github, connection_id, max_requests=1)
    after_first = await rows("SELECT backfill_cursor, backfill_completed_at IS NULL FROM repositories WHERE github_repo_id = 1")
    pulls_after_first = await scalar("SELECT count(*) FROM pull_requests")
    second = await sync(github, connection_id, max_requests=1)
    pulls_after_second = await scalar("SELECT count(*) FROM pull_requests")
    third = await sync(github, connection_id, max_requests=1)

    assert (first, second, third) == (SyncOutcome.PARTIAL,) * 3
    assert after_first == [(2, True)]
    assert (pulls_after_first, pulls_after_second) == (50, 100)
    assert await scalar("SELECT count(*) FROM pull_requests") == 120
    assert await scalar("SELECT backfill_completed_at IS NOT NULL FROM repositories WHERE github_repo_id = 1") is True
    assert await rows("SELECT status FROM sync_runs WHERE kind = 'pull_requests' ORDER BY started_at") == [("partial",)] * 3


async def test_a_partial_run_counts_as_a_successful_update(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(120)
    connection_id = await tracking(github, 1)

    await sync(github, connection_id, max_requests=1)

    assert await scalar("SELECT last_successful_sync_at IS NOT NULL FROM github_connections") is True


async def test_a_page_and_its_cursor_are_saved_together_so_a_failure_loses_nothing(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(120)
    github.pulls_error_on_page = {2: 503}
    connection_id = await tracking(github, 1)

    with pytest.raises(GitHubUnavailableError):
        await sync(github, connection_id)

    assert await scalar("SELECT count(*) FROM pull_requests") == 50
    assert await scalar("SELECT backfill_cursor FROM repositories WHERE github_repo_id = 1") == 2

    github.pulls_error_on_page = {}
    github.requests.clear()
    await sync(github, connection_id)

    assert await scalar("SELECT count(*) FROM pull_requests") == 120
    # It resumed at page 2 instead of starting again.
    assert [r.url.params["page"] for r in github.pull_list_calls()][0] == "2"


async def test_the_run_stops_when_its_time_budget_is_used_up(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    connection_id = await tracking(github, 1)

    outcome = await sync(github, connection_id, budget_seconds=0)

    assert outcome == SyncOutcome.PARTIAL
    assert github.pull_list_calls() == []


async def test_the_run_stops_when_github_says_the_hourly_limit_is_nearly_used(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    github.rate_remaining = 100  # below the reserve of 200
    connection_id = await tracking(github, 1)

    outcome = await sync(github, connection_id)

    assert outcome == SyncOutcome.PARTIAL
    assert await scalar("SELECT count(*) FROM pull_requests") == 3  # the page it read is kept
    assert github.review_calls() == []


# --- Scenario: I stop tracking a repository ----------------------------------------------------------


async def test_unselecting_stops_fetching_and_keeps_the_stored_data(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    connection_id = await tracking(github, 1)
    await sync(github, connection_id)
    await execute("UPDATE repositories SET is_selected = false")
    github.requests.clear()

    await sync(github, connection_id)

    assert github.pull_list_calls() == []
    assert await scalar("SELECT count(*) FROM pull_requests") == 3


async def test_a_repository_unselected_during_a_run_stops_being_fetched(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(120)
    connection_id = await tracking(github, 1)

    async def handler(request: httpx.Request) -> httpx.Response:
        response = github.handler(request)
        if request.url.path == f"/repos/{REPO_1}/pulls":
            # The user unselects the repository while its first page is being fetched.
            await execute("UPDATE repositories SET is_selected = false")
        return response

    outcome = await run_pull_request_sync(
        connection_id, "schedule", http_transport=httpx.MockTransport(handler)
    )

    assert outcome == SyncOutcome.SUCCEEDED
    assert len(github.pull_list_calls()) == 1  # no more pages after the unselect
    assert await scalar("SELECT count(*) FROM pull_requests") == 50  # what was read is kept
    assert await scalar("SELECT backfill_completed_at IS NULL FROM repositories WHERE github_repo_id = 1") is True


async def test_selecting_again_resumes_an_unfinished_import_where_it_stopped(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(120)
    connection_id = await tracking(github, 1)
    await sync(github, connection_id, max_requests=1)
    await execute("UPDATE repositories SET is_selected = false")
    await sync(github, connection_id)
    await execute("UPDATE repositories SET is_selected = true WHERE github_repo_id = 1")
    github.requests.clear()

    await sync(github, connection_id, max_requests=1)

    assert github.pull_list_calls()[0].url.params["page"] == "2"
    assert await scalar("SELECT count(*) FROM pull_requests") == 100


async def test_selecting_again_after_a_finished_import_catches_up_on_changes(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    connection_id = await tracking(github, 1)
    await sync(github, connection_id)
    await execute("UPDATE repositories SET is_selected = false")
    github.pull_requests[REPO_1][0] = make_pr(1, state="closed", merged="2099-01-01T00:00:00Z", updated="2099-01-01T00:00:00Z")
    github.pull_requests[REPO_1].append(make_pr(4, state="open", created="2099-01-02T00:00:00Z"))
    await execute("UPDATE repositories SET is_selected = true WHERE github_repo_id = 1")

    await sync(github, connection_id)

    assert await scalar("SELECT state FROM pull_requests WHERE number = 1") == "merged"
    assert await scalar("SELECT count(*) FROM pull_requests") == 4


# --- After the history: only what changed ---------------------------------------------------------------


async def test_later_runs_read_recently_updated_pull_requests_and_stop_at_old_ones(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(120)  # all old
    connection_id = await tracking(github, 1)
    await sync(github, connection_id)
    watermark_before = await scalar("SELECT incremental_watermark FROM repositories WHERE github_repo_id = 1")
    github.requests.clear()

    await sync(github, connection_id)

    calls = github.pull_list_calls()
    assert len(calls) == 1  # page 1 only: everything on it is older than the watermark
    assert (calls[0].url.params["sort"], calls[0].url.params["direction"]) == ("updated", "desc")
    assert await scalar("SELECT incremental_watermark FROM repositories WHERE github_repo_id = 1") > watermark_before


async def test_changed_and_new_pull_requests_are_picked_up(github: FakeGitHub):
    github.pull_requests[REPO_1] = [make_pr(1, state="open"), make_pr(2, state="open")]
    connection_id = await tracking(github, 1)
    await sync(github, connection_id)
    github.pull_requests[REPO_1][0] = make_pr(1, state="closed", merged="2099-01-01T00:00:00Z", updated="2099-01-01T00:00:00Z")
    github.pull_requests[REPO_1].append(make_pr(3, state="open", created="2099-01-02T00:00:00Z"))

    await sync(github, connection_id)

    assert await rows("SELECT number, state FROM pull_requests ORDER BY number") == [
        (1, "merged"),
        (2, "open"),
        (3, "open"),
    ]


# --- Review state ----------------------------------------------------------------------------------------


async def test_review_state_is_filled_in_after_the_pull_requests(github: FakeGitHub):
    github.pull_requests[REPO_1] = [make_pr(1, state="open"), make_pr(2), make_pr(3), make_pr(4)]
    github.reviews[(REPO_1, 1)] = [make_review("bob", "APPROVED", 1)]
    github.reviews[(REPO_1, 2)] = [make_review("bob", "CHANGES_REQUESTED", 2)]
    github.reviews[(REPO_1, 3)] = [make_review("bob", "COMMENTED", 3)]
    connection_id = await tracking(github, 1)

    outcome = await sync(github, connection_id)

    assert outcome == SyncOutcome.SUCCEEDED
    assert await rows("SELECT number, review_state FROM pull_requests ORDER BY number") == [
        (1, "approved"),
        (2, "changes_requested"),
        (3, "commented"),
        (4, "none"),
    ]


async def test_open_pull_requests_get_their_reviews_before_old_closed_ones(github: FakeGitHub):
    github.pull_requests[REPO_1] = [
        make_pr(1, state="closed", merged="2026-03-01T00:00:00Z", updated="2026-03-01T00:00:00Z"),
        make_pr(2, state="open", updated="2026-01-05T00:00:00Z"),
    ]
    connection_id = await tracking(github, 1)

    await sync(github, connection_id, max_requests=2)  # one list call and one review call

    assert await rows("SELECT number, review_state IS NOT NULL FROM pull_requests ORDER BY number") == [
        (1, False),
        (2, True),
    ]


async def test_reviews_are_not_read_again_while_a_pull_request_is_unchanged(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    connection_id = await tracking(github, 1)
    await sync(github, connection_id)
    assert len(github.review_calls()) == 3
    github.requests.clear()

    await sync(github, connection_id)
    assert github.review_calls() == []

    github.pull_requests[REPO_1][2] = make_pr(3, updated="2099-01-01T00:00:00Z")
    github.requests.clear()
    await sync(github, connection_id)

    assert [r.url.path for r in github.review_calls()] == [f"/repos/{REPO_1}/pulls/3/reviews"]


async def test_review_progress_is_kept_when_a_later_request_fails(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    github.reviews_fail_after = 2
    connection_id = await tracking(github, 1)

    with pytest.raises(GitHubUnavailableError):
        await sync(github, connection_id)

    assert await scalar("SELECT count(*) FROM pull_requests WHERE review_state IS NOT NULL") == 2
    assert await scalar("SELECT count(*) FROM pull_requests") == 3  # the pull requests themselves are safe


# --- Scenario: GitHub is temporarily unavailable -------------------------------------------------------------


async def test_a_github_outage_keeps_earlier_data_and_asks_for_a_retry(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    connection_id = await tracking(github, 1)
    await sync(github, connection_id)
    github.pulls_error = (503, {}, {"message": "unavailable"})

    with pytest.raises(GitHubUnavailableError):
        await sync(github, connection_id)

    assert await scalar("SELECT count(*) FROM pull_requests") == 3
    assert await scalar("SELECT status FROM github_connections") == "active"
    assert await rows("SELECT status, error_category FROM sync_runs WHERE kind = 'pull_requests' ORDER BY started_at") == [
        ("succeeded", None),
        ("failed", "github_unavailable"),
    ]


async def test_a_failed_run_does_not_count_as_an_update(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    github.pulls_error = (503, {}, {})
    connection_id = await tracking(github, 1)

    with pytest.raises(GitHubUnavailableError):
        await sync(github, connection_id)

    assert await scalar("SELECT last_successful_sync_at IS NULL FROM github_connections") is True


# --- Rate limits ----------------------------------------------------------------------------------------------


def exhausted(seconds_until_reset: int) -> tuple[int, dict, dict]:
    return (
        403,
        {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(time.time()) + seconds_until_reset)},
        {"message": "API rate limit exceeded"},
    )


async def test_a_short_rate_limit_asks_for_a_retry(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    github.pulls_error = exhausted(120)
    connection_id = await tracking(github, 1)

    with pytest.raises(GitHubRateLimitedError) as raised:
        await sync(github, connection_id)

    assert raised.value.retry_after <= 120
    assert await scalar("SELECT rate_limited_until IS NULL FROM github_connections") is True


async def test_a_long_rate_limit_pauses_the_schedule_for_that_connection(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    github.pulls_error = exhausted(3 * 3600)
    connection_id = await tracking(github, 1)

    outcome = await sync(github, connection_id)

    assert outcome == SyncOutcome.RATE_LIMITED
    waiting_until = await scalar("SELECT rate_limited_until FROM github_connections")
    assert waiting_until > datetime.now(UTC) + timedelta(hours=2)

    github.requests.clear()
    skipped = await sync(github, connection_id, "schedule")
    assert skipped == SyncOutcome.SKIPPED_RATE_LIMITED
    assert github.requests == []

    # Once the wait is over the schedule works again and clears the pause.
    github.pulls_error = None
    await execute("UPDATE github_connections SET rate_limited_until = now() - interval '1 minute'")
    assert await sync(github, connection_id, "schedule") == SyncOutcome.SUCCEEDED
    assert await scalar("SELECT rate_limited_until IS NULL FROM github_connections") is True


# --- Scenario: Access is removed on GitHub ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "problem, reason",
    [("revoked", "access_revoked"), ("suspended", "suspended"), ("permission", "permission_missing")],
)
async def test_lost_access_stops_the_job_and_marks_the_connection(github: FakeGitHub, problem, reason):
    github.pull_requests[REPO_1] = many(3)
    connection_id = await tracking(github, 1)
    if problem == "revoked":
        github.installations.clear()
    elif problem == "suspended":
        github.installations[5001]["suspended_at"] = "2026-11-01T00:00:00Z"
    else:
        github.pulls_error = (403, {}, {"message": "Resource not accessible by integration"})

    outcome = await sync(github, connection_id)  # returns normally: nothing to retry

    assert outcome == SyncOutcome.NEEDS_ATTENTION
    assert await rows("SELECT status, status_reason FROM github_connections") == [("needs_attention", reason)]
    assert await rows("SELECT status, error_category FROM sync_runs") == [("failed", reason)]


async def test_a_connection_that_needs_attention_is_not_synced(github: FakeGitHub):
    connection_id = await tracking(github, 1, status="needs_attention", reason="access_revoked")

    outcome = await sync(github, connection_id)

    assert outcome == SyncOutcome.SKIPPED_NOT_ACTIVE
    assert github.requests == []


async def test_a_repository_that_is_gone_is_hidden_and_the_others_still_sync(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(2)
    github.pull_requests[REPO_2] = many(4)
    github.gone_repositories = {REPO_1}
    connection_id = await tracking(github, 1, 2)

    outcome = await sync(github, connection_id)

    assert outcome == SyncOutcome.SUCCEEDED
    assert await scalar("SELECT is_available FROM repositories WHERE github_repo_id = 1") is False
    assert await scalar("SELECT count(*) FROM pull_requests") == 4
    assert await scalar("SELECT status FROM github_connections") == "active"


# --- Duplicate delivery -----------------------------------------------------------------------------------------


async def test_a_second_delivery_while_one_is_running_does_nothing(github: FakeGitHub):
    connection_id = await tracking(github, 1)
    await execute(
        "INSERT INTO sync_runs (id, connection_id, kind, trigger, status, started_at) "
        "VALUES (gen_random_uuid(), :c, 'repository_list', 'connected', 'running', now())",
        c=connection_id,
    )

    outcome = await sync(github, connection_id, "selection_saved")

    assert outcome == SyncOutcome.SKIPPED_ALREADY_RUNNING
    assert github.requests == []


async def test_concurrent_deliveries_never_duplicate_pull_requests(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(60)
    connection_id = await tracking(github, 1)

    outcomes = await asyncio.gather(*(sync(github, connection_id) for _ in range(4)))

    assert SyncOutcome.SUCCEEDED in outcomes
    assert await scalar("SELECT count(*) FROM pull_requests") == 60
    assert await scalar("SELECT count(*) FROM sync_runs WHERE status = 'running'") == 0


async def test_each_connection_only_gets_its_own_pull_requests(github: FakeGitHub):
    github.pull_requests[REPO_1] = many(3)
    mine = await tracking(github, 1)
    other = await make_connection(github_user_id=2002, installation_id=6002)
    github.installations[6002] = {**github.installations[5001], "id": 6002}
    await run_repository_list_sync(other, "connected", http_transport=httpx.MockTransport(github.handler))
    await execute("UPDATE repositories SET is_selected = true WHERE connection_id = :c", c=other)

    await sync(github, mine)

    assert await scalar(
        "SELECT count(*) FROM pull_requests p JOIN repositories r ON r.id = p.repository_id WHERE r.connection_id = :c".replace(":c", f"'{other}'")
    ) == 0
    assert await scalar("SELECT count(*) FROM pull_requests") == 3


# --- Credentials -------------------------------------------------------------------------------------------------


async def test_no_token_is_stored_or_logged_while_syncing_pull_requests(github: FakeGitHub, caplog):
    caplog.set_level(logging.DEBUG)
    github.pull_requests[REPO_1] = many(3)
    connection_id = await tracking(github, 1)

    await sync(github, connection_id)

    dump = await scalar(
        "SELECT coalesce((SELECT string_agg(row_to_json(c)::text, '') FROM github_connections c), '')"
        " || coalesce((SELECT string_agg(row_to_json(r)::text, '') FROM repositories r), '')"
        " || coalesce((SELECT string_agg(row_to_json(p)::text, '') FROM pull_requests p), '')"
        " || coalesce((SELECT string_agg(row_to_json(s)::text, '') FROM sync_runs s), '')"
    )
    logged = " ".join(f"{r.getMessage()} {sorted(map(str, r.__dict__.values()))}" for r in caplog.records)
    assert FAKE_INSTALLATION_TOKEN not in dump
    assert FAKE_INSTALLATION_TOKEN not in logged
    assert "BEGIN" not in logged


# --- The schedule --------------------------------------------------------------------------------------------------


async def test_the_schedule_queues_every_connection_that_is_due(github: FakeGitHub):
    due = await make_connection(github_user_id=1, installation_id=11)
    nothing_selected = await make_connection(github_user_id=2, installation_id=12)
    needs_attention = await make_connection(github_user_id=3, installation_id=13, status="needs_attention", reason="suspended")
    rate_limited = await make_connection(github_user_id=4, installation_id=14)
    wait_over = await make_connection(github_user_id=5, installation_id=15)
    await execute("UPDATE github_connections SET rate_limited_until = now() + interval '2 hours' WHERE id = :c", c=rate_limited)
    await execute("UPDATE github_connections SET rate_limited_until = now() - interval '1 minute' WHERE id = :c", c=wait_over)
    recorder = RecordingDispatcher()

    queued = await run_dispatch_due_syncs(recorder)

    assert queued == 3
    assert {call[0] for call in recorder.pull_request_calls} == {due, nothing_selected, wait_over}
    assert {call[1] for call in recorder.pull_request_calls} == {"schedule"}
    assert recorder.calls == []
