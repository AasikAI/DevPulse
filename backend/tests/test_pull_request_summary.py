import uuid
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
from sqlalchemy import text

from app.db import SessionLocal
from app.github_integration.repository import ConnectionRepository
from app.github_integration.service import ConnectionStateService
from app.identity.schemas import CurrentUser
from app.pull_requests.repository import PullRequestRepository
from app.pull_requests.summary_service import PullRequestSummaryService
from app.repositories.repository import RepositoryRepository
from app.repositories.service import RepositoryService
from app.synchronization.repository import SyncRunRepository
from app.synchronization.status_service import SyncStatusService
from tests.fake_github import FakeGitHub
from tests.helpers import connect, make_connection, scalar, sign_in

# Thursday. The current UTC week starts Monday 23 Nov, so a 4-week window starts Monday 2 Nov.
NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
THIS_MONDAY = date(2026, 11, 23)


def at(year: int, month: int, day: int, hour: int = 10, minute: int = 0, second: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


async def execute(sql: str, **params) -> None:
    async with SessionLocal() as session:
        await session.execute(text(sql), params)
        await session.commit()


async def add_repository(
    connection_id: uuid.UUID,
    github_id: int,
    *,
    selected: bool = True,
    available: bool = True,
    history_done: bool = True,
) -> uuid.UUID:
    repo_id = uuid.uuid4()
    await execute(
        "INSERT INTO repositories (id, connection_id, github_repo_id, owner_login, name, full_name, is_private,"
        " is_available, is_selected, backfill_completed_at, updated_at)"
        " VALUES (:id, :c, :g, 'o', :n, :f, false, :avail, :sel, :done, now())",
        id=repo_id,
        c=connection_id,
        g=github_id,
        n=f"repo-{github_id}",
        f=f"o/repo-{github_id}",
        avail=available,
        sel=selected,
        done=NOW if history_done else None,
    )
    return repo_id


async def add_pr(
    repo_id: uuid.UUID,
    number: int,
    *,
    created: datetime,
    state: str = "closed",
    merged: datetime | None = None,
    review: str | None = None,
    draft: bool = False,
) -> None:
    await execute(
        "INSERT INTO pull_requests (id, repository_id, github_pr_id, number, state, is_draft, title, author_login,"
        " review_state, created_at_gh, updated_at_gh, merged_at, fetched_at)"
        " VALUES (gen_random_uuid(), :r, :g, :n, :s, :d, 'A title', 'someone', :rv, :c, :c, :m, now())",
        r=repo_id,
        g=900000 + number,
        n=number,
        s=state,
        d=draft,
        rv=review,
        c=created,
        m=merged,
    )


async def summarize(
    connection_id: uuid.UUID, *, weeks: int = 4, now: datetime = NOW, interval: int = 900
):
    user_id = await scalar(f"SELECT user_id FROM github_connections WHERE id = '{connection_id}'")
    github_user_id = await scalar(f"SELECT github_user_id FROM users WHERE id = '{user_id}'")
    user = CurrentUser(id=user_id, github_user_id=github_user_id, login="x", name=None, avatar_url=None, email=None)
    async with SessionLocal() as session:
        service = PullRequestSummaryService(
            repository=PullRequestRepository(session),
            connections=ConnectionStateService(repository=ConnectionRepository(session)),
            repositories=RepositoryService(repository=RepositoryRepository(session)),
            sync_status=SyncStatusService(runs=SyncRunRepository(session)),
            sync_interval_seconds=interval,
            clock=lambda: now,
        )
        return await service.summarize(user, weeks=weeks)


# --- Connection state ---------------------------------------------------------------------------


async def test_a_user_without_a_connection_gets_an_empty_not_connected_summary():
    user_id = uuid.uuid4()
    await execute(
        "INSERT INTO users (id, github_user_id, login, updated_at, last_login_at) VALUES (:i, 1, 'x', now(), now())",
        i=user_id,
    )
    async with SessionLocal() as session:
        service = PullRequestSummaryService(
            repository=PullRequestRepository(session),
            connections=ConnectionStateService(repository=ConnectionRepository(session)),
            repositories=RepositoryService(repository=RepositoryRepository(session)),
            sync_status=SyncStatusService(runs=SyncRunRepository(session)),
            sync_interval_seconds=900,
            clock=lambda: NOW,
        )
        summary = await service.summarize(
            CurrentUser(id=user_id, github_user_id=1, login="x", name=None, avatar_url=None, email=None), weeks=4
        )

    assert summary.connection_status == "not_connected"
    assert (summary.repository_count, summary.weekly) == (0, [])
    assert summary.is_stale is False


async def test_a_connection_with_nothing_selected_has_empty_weeks_and_nothing_to_wait_for():
    connection_id = await make_connection()
    await add_repository(connection_id, 1, selected=False)

    summary = await summarize(connection_id)

    assert summary.connection_status == "active"
    assert summary.repository_count == 0
    assert [w.opened + w.merged for w in summary.weekly] == [0, 0, 0, 0]
    assert summary.history_complete is True
    assert (summary.is_stale, summary.stale_reason) == (False, None)


async def test_a_connection_that_needs_attention_still_shows_its_stored_data():
    connection_id = await make_connection(status="needs_attention", reason="access_revoked")
    repo = await add_repository(connection_id, 1)
    await add_pr(repo, 1, created=at(2026, 11, 24), state="open")

    summary = await summarize(connection_id)

    assert (summary.connection_status, summary.connection_reason) == ("needs_attention", "access_revoked")
    assert summary.totals.open_now == 1


# --- Weekly buckets -------------------------------------------------------------------------------------


@pytest.mark.parametrize("weeks", [1, 4, 12, 52])
async def test_the_window_is_that_many_utc_weeks_ending_with_the_current_one(weeks):
    connection_id = await make_connection()
    await add_repository(connection_id, 1)

    summary = await summarize(connection_id, weeks=weeks)

    starts = [w.week_start for w in summary.weekly]
    assert len(starts) == weeks
    assert starts[-1] == THIS_MONDAY
    assert starts[0] == THIS_MONDAY - timedelta(weeks=weeks - 1)
    assert all(s.weekday() == 0 for s in starts)  # every bucket starts on a Monday
    assert summary.window_start == starts[0]


async def test_pull_requests_are_counted_in_the_week_they_were_opened_and_merged():
    connection_id = await make_connection()
    repo = await add_repository(connection_id, 1)
    await add_pr(repo, 1, created=at(2026, 11, 24), state="open")  # this week
    await add_pr(repo, 2, created=at(2026, 11, 25), state="open")  # this week
    await add_pr(repo, 3, created=at(2026, 11, 16), merged=at(2026, 11, 17), state="merged")  # opened and merged last week
    await add_pr(repo, 4, created=at(2026, 11, 3), merged=at(2026, 11, 25), state="merged")  # opened 3 weeks ago, merged this week

    summary = await summarize(connection_id)

    assert [(w.week_start.isoformat(), w.opened, w.merged) for w in summary.weekly] == [
        ("2026-11-02", 1, 0),
        ("2026-11-09", 0, 0),
        ("2026-11-16", 1, 1),
        ("2026-11-23", 2, 1),
    ]
    assert (summary.totals.opened_in_window, summary.totals.merged_in_window) == (4, 2)


async def test_activity_before_the_window_is_left_out_but_a_later_merge_still_counts():
    connection_id = await make_connection()
    repo = await add_repository(connection_id, 1)
    await add_pr(repo, 1, created=at(2026, 9, 1), merged=at(2026, 11, 25), state="merged")  # opened long ago

    summary = await summarize(connection_id)

    assert (summary.totals.opened_in_window, summary.totals.merged_in_window) == (0, 1)


async def test_weeks_start_on_monday_utc_at_midnight():
    connection_id = await make_connection()
    repo = await add_repository(connection_id, 1)
    await add_pr(repo, 1, created=at(2026, 11, 22, 23, 59, 59))  # Sunday night: the week before
    await add_pr(repo, 2, created=at(2026, 11, 23, 0, 0, 0))  # Monday 00:00: the new week
    await add_pr(repo, 3, created=at(2026, 11, 2, 0, 0, 0))  # first Monday of a 4-week window: included
    await add_pr(repo, 4, created=at(2026, 11, 1, 23, 59, 59))  # just before the window: excluded

    summary = await summarize(connection_id)

    assert {w.week_start.isoformat(): w.opened for w in summary.weekly} == {
        "2026-11-02": 1,
        "2026-11-09": 0,
        "2026-11-16": 1,
        "2026-11-23": 1,
    }


async def test_buckets_follow_utc_not_the_database_session_time_zone():
    connection_id = await make_connection()
    repo = await add_repository(connection_id, 1)
    await add_pr(repo, 1, created=at(2026, 11, 22, 23, 30))  # Sunday evening UTC
    async with SessionLocal() as session:
        await session.execute(text("SET TIME ZONE 'Asia/Kolkata'"))  # already Monday morning there
        service = PullRequestSummaryService(
            repository=PullRequestRepository(session),
            connections=ConnectionStateService(repository=ConnectionRepository(session)),
            repositories=RepositoryService(repository=RepositoryRepository(session)),
            sync_status=SyncStatusService(runs=SyncRunRepository(session)),
            sync_interval_seconds=900,
            clock=lambda: NOW,
        )
        user_id = await scalar(f"SELECT user_id FROM github_connections WHERE id = '{connection_id}'")
        summary = await service.summarize(
            CurrentUser(id=user_id, github_user_id=1001, login="x", name=None, avatar_url=None, email=None), weeks=4
        )

    assert {w.week_start.isoformat(): w.opened for w in summary.weekly}["2026-11-16"] == 1


# --- Open pull requests and review state -------------------------------------------------------------------


async def test_open_pull_requests_are_counted_by_review_state_including_drafts_and_old_ones():
    connection_id = await make_connection()
    repo = await add_repository(connection_id, 1)
    old = at(2025, 1, 5)  # far outside the window, but still open
    await add_pr(repo, 1, created=old, state="open", review="approved")
    await add_pr(repo, 2, created=at(2026, 11, 24), state="open", review="changes_requested")
    await add_pr(repo, 3, created=at(2026, 11, 24), state="open", review="commented", draft=True)
    await add_pr(repo, 4, created=at(2026, 11, 24), state="open", review="none")
    await add_pr(repo, 5, created=at(2026, 11, 24), state="open", review=None)  # reviews not read yet
    await add_pr(repo, 6, created=at(2026, 11, 24), state="merged", merged=at(2026, 11, 25), review="approved")
    await add_pr(repo, 7, created=at(2026, 11, 24), state="closed", review="approved")

    summary = await summarize(connection_id)

    assert summary.totals.open_now == 5
    assert summary.open_by_review_state.model_dump() == {
        "none": 1,
        "commented": 1,
        "approved": 1,
        "changes_requested": 1,
        "not_loaded": 1,
    }


# --- Which repositories count ------------------------------------------------------------------------------


async def test_unselected_repositories_are_hidden_and_come_back_when_selected_again():
    connection_id = await make_connection()
    kept = await add_repository(connection_id, 1)
    dropped = await add_repository(connection_id, 2)
    await add_pr(kept, 1, created=at(2026, 11, 24), state="open")
    await add_pr(dropped, 2, created=at(2026, 11, 24), state="open")
    assert (await summarize(connection_id)).totals.open_now == 2

    await execute("UPDATE repositories SET is_selected = false WHERE id = :r", r=dropped)
    hidden = await summarize(connection_id)
    await execute("UPDATE repositories SET is_selected = true WHERE id = :r", r=dropped)
    back = await summarize(connection_id)

    assert (hidden.repository_count, hidden.totals.open_now) == (1, 1)
    assert (back.repository_count, back.totals.open_now) == (2, 2)
    assert await scalar("SELECT count(*) FROM pull_requests") == 2  # nothing was deleted


async def test_repositories_the_app_lost_access_to_are_left_out():
    connection_id = await make_connection()
    gone = await add_repository(connection_id, 1, available=False)
    await add_pr(gone, 1, created=at(2026, 11, 24), state="open")

    summary = await summarize(connection_id)

    assert (summary.repository_count, summary.totals.open_now) == (0, 0)


async def test_only_the_users_own_pull_requests_are_counted():
    mine = await make_connection(github_user_id=1001, installation_id=5001)
    theirs = await make_connection(github_user_id=2002, installation_id=6002)
    my_repo = await add_repository(mine, 1)
    their_repo = await add_repository(theirs, 2)
    await add_pr(my_repo, 1, created=at(2026, 11, 24), state="open")
    for number in range(2, 7):
        await add_pr(their_repo, number, created=at(2026, 11, 24), state="open")

    summary = await summarize(mine)

    assert (summary.repository_count, summary.totals.open_now, summary.totals.opened_in_window) == (1, 1, 1)


# --- History progress ---------------------------------------------------------------------------------------


async def test_history_progress_counts_repositories_whose_import_has_finished():
    connection_id = await make_connection()
    await add_repository(connection_id, 1, history_done=True)
    await add_repository(connection_id, 2, history_done=False)
    await add_repository(connection_id, 3, history_done=False)

    summary = await summarize(connection_id)

    assert summary.history_complete is False
    assert (summary.history_repositories_complete, summary.history_repositories_total) == (1, 3)

    await execute("UPDATE repositories SET backfill_completed_at = now()")
    assert (await summarize(connection_id)).history_complete is True


# --- Freshness ----------------------------------------------------------------------------------------------


async def add_run(connection_id: uuid.UUID, status: str, minutes_ago: int = 1, kind: str = "pull_requests") -> None:
    await execute(
        "INSERT INTO sync_runs (id, connection_id, kind, trigger, status, started_at, finished_at)"
        " VALUES (gen_random_uuid(), :c, :k, 'schedule', :s, :t, :t)",
        c=connection_id,
        k=kind,
        s=status,
        t=NOW - timedelta(minutes=minutes_ago),
    )


async def set_last_updated(minutes_ago: int | None) -> None:
    await execute(
        "UPDATE github_connections SET last_successful_sync_at = :t",
        t=None if minutes_ago is None else NOW - timedelta(minutes=minutes_ago),
    )


async def test_recently_updated_data_is_fresh_and_shows_when_it_was_updated():
    connection_id = await make_connection()
    await add_repository(connection_id, 1)
    await set_last_updated(10)
    await add_run(connection_id, "succeeded", 10)

    summary = await summarize(connection_id)

    assert (summary.is_stale, summary.stale_reason) == (False, None)
    assert summary.last_updated_at == NOW - timedelta(minutes=10)


async def test_data_not_updated_for_three_intervals_is_out_of_date():
    connection_id = await make_connection()
    await add_repository(connection_id, 1)
    await add_run(connection_id, "succeeded", 50)

    await set_last_updated(44)
    assert (await summarize(connection_id)).is_stale is False  # 45 minutes is the limit at 15-minute intervals

    await set_last_updated(46)
    summary = await summarize(connection_id)
    assert (summary.is_stale, summary.stale_reason) == (True, "not_updated_recently")


async def test_the_out_of_date_limit_follows_the_configured_interval():
    connection_id = await make_connection()
    await add_repository(connection_id, 1)
    await add_run(connection_id, "succeeded", 5)
    await set_last_updated(5)

    assert (await summarize(connection_id, interval=60)).is_stale is True  # limit is 3 minutes
    assert (await summarize(connection_id, interval=900)).is_stale is False


@pytest.mark.parametrize("status", ["failed", "rate_limited"])
async def test_a_failed_latest_run_marks_the_data_out_of_date_right_away(status):
    connection_id = await make_connection()
    await add_repository(connection_id, 1)
    await set_last_updated(5)  # the earlier data is only five minutes old
    await add_run(connection_id, "succeeded", 20)
    await add_run(connection_id, status, 1)

    summary = await summarize(connection_id)

    assert (summary.is_stale, summary.stale_reason) == (True, "last_run_failed")
    assert summary.last_updated_at == NOW - timedelta(minutes=5)  # the earlier data and its time are kept


async def test_a_later_successful_run_clears_the_out_of_date_mark():
    connection_id = await make_connection()
    await add_repository(connection_id, 1)
    await set_last_updated(1)
    await add_run(connection_id, "failed", 20)
    await add_run(connection_id, "succeeded", 1)

    assert (await summarize(connection_id)).is_stale is False


async def test_a_partial_run_is_not_a_failure():
    connection_id = await make_connection()
    await add_repository(connection_id, 1)
    await set_last_updated(1)
    await add_run(connection_id, "partial", 1)

    assert (await summarize(connection_id)).is_stale is False


async def test_a_run_still_in_progress_and_repository_list_runs_do_not_count():
    connection_id = await make_connection()
    await add_repository(connection_id, 1)
    await set_last_updated(1)
    await add_run(connection_id, "succeeded", 5)
    await add_run(connection_id, "running", 1)
    await add_run(connection_id, "failed", 2, kind="repository_list")

    assert (await summarize(connection_id)).is_stale is False


async def test_data_that_has_never_been_updated_is_not_called_out_of_date():
    connection_id = await make_connection()
    await add_repository(connection_id, 1, history_done=False)

    summary = await summarize(connection_id)

    assert summary.last_updated_at is None
    assert summary.is_stale is False


async def test_a_first_import_that_failed_is_reported_even_without_earlier_data():
    connection_id = await make_connection()
    await add_repository(connection_id, 1, history_done=False)
    await add_run(connection_id, "failed", 1)

    summary = await summarize(connection_id)

    assert (summary.last_updated_at, summary.is_stale, summary.stale_reason) == (None, True, "last_run_failed")


# --- The API --------------------------------------------------------------------------------------------------


async def test_the_summary_requires_a_signed_in_user(browser):
    response = await browser.get("/api/pull-requests/summary")

    assert response.status_code == 401


@pytest.mark.parametrize("weeks", [0, 53, -1])
async def test_the_window_is_bounded(browser, weeks):
    await sign_in(browser)

    response = await browser.get("/api/pull-requests/summary", params={"weeks": weeks})

    assert response.status_code == 422


async def test_a_signed_in_user_without_a_connection_is_told_so_not_given_an_error(browser):
    await sign_in(browser)

    response = await browser.get("/api/pull-requests/summary")

    assert response.status_code == 200
    assert response.json()["connection_status"] == "not_connected"


async def test_the_default_window_is_twelve_weeks(browser):
    await sign_in(browser)
    await connect(browser)

    body = (await browser.get("/api/pull-requests/summary")).json()

    assert (body["weeks"], len(body["weekly"])) == (12, 12)


async def test_the_dashboard_never_calls_github(browser, github: FakeGitHub):
    await sign_in(browser)
    await connect(browser)
    connection_id = await scalar("SELECT id FROM github_connections")
    repo = await add_repository(connection_id, 1)
    await add_pr(repo, 1, created=datetime.now(UTC) - timedelta(days=1), state="open")
    github.requests.clear()

    response = await browser.get("/api/pull-requests/summary", params={"weeks": 4})

    assert response.status_code == 200
    assert response.json()["totals"]["open_now"] == 1
    assert github.requests == []


async def test_a_user_only_sees_their_own_pull_requests(new_browser, github: FakeGitHub):
    mine, theirs = new_browser(), new_browser()
    await sign_in(mine)
    await connect(mine)
    my_connection = await scalar("SELECT id FROM github_connections")
    other_connection = await make_connection(github_user_id=2002, installation_id=6002)
    await add_pr(await add_repository(my_connection, 1), 1, created=datetime.now(UTC) - timedelta(days=1), state="open")
    for number in range(2, 5):
        await add_pr(await add_repository(other_connection, number + 10), number, created=datetime.now(UTC) - timedelta(days=1), state="open")

    body = (await mine.get("/api/pull-requests/summary")).json()

    assert (body["repository_count"], body["totals"]["open_now"]) == (1, 1)


async def test_the_response_has_no_people_ids_or_credentials(browser):
    await sign_in(browser)
    await connect(browser)
    connection_id = await scalar("SELECT id FROM github_connections")
    repo = await add_repository(connection_id, 1)
    await add_pr(repo, 1, created=datetime.now(UTC) - timedelta(days=1), state="open")

    response = await browser.get("/api/pull-requests/summary")
    body = response.json()

    assert set(body) == {
        "connection_status", "connection_reason", "repository_count", "weeks", "window_start",
        "last_updated_at", "is_stale", "stale_reason", "history_complete", "history_repositories_total",
        "history_repositories_complete", "totals", "open_by_review_state", "weekly",
    }
    assert set(body["weekly"][0]) == {"week_start", "opened", "merged"}
    for forbidden in ("author", "someone", "A title", "installation", "token", "github_pr_id"):
        assert forbidden not in response.text
