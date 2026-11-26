from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta

from app.common.clock import utcnow
from app.github_integration.service import ConnectionStateService
from app.identity.schemas import CurrentUser
from app.pull_requests.repository import PullRequestRepository
from app.pull_requests.schemas import (
    PullRequestSummaryResponse,
    PullRequestTotals,
    ReviewStateCounts,
    WeeklyCount,
)
from app.repositories.service import RepositoryService
from app.synchronization.status_service import SyncStatusService

# Data is out of date when it has not been refreshed for this many scheduled intervals.
STALE_AFTER_INTERVALS = 3


class PullRequestSummaryService:
    """The dashboard's pull request numbers, read from the database only.

    This service has no GitHub client on purpose: opening the dashboard never calls GitHub.
    """

    def __init__(
        self,
        *,
        repository: PullRequestRepository,
        connections: ConnectionStateService,
        repositories: RepositoryService,
        sync_status: SyncStatusService,
        sync_interval_seconds: int,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._repository = repository
        self._connections = connections
        self._repositories = repositories
        self._sync_status = sync_status
        self._stale_after = timedelta(seconds=sync_interval_seconds * STALE_AFTER_INTERVALS)
        self._clock = clock

    async def summarize(self, user: CurrentUser, *, weeks: int) -> PullRequestSummaryResponse:
        now = self._clock()
        first_week = _monday(now.date()) - timedelta(weeks=weeks - 1)
        connection = await self._connections.get_for_user(user.id)
        if connection is None:
            return self._empty(first_week, weeks, status="not_connected")

        # Only the user's own selected repositories the App can still access.
        repositories = await self._repositories.list_for_sync(connection_id=connection.id)
        repository_ids = [repo.id for repo in repositories]
        opened_by_week, merged_by_week = await self._repository.weekly_counts(
            repository_ids=repository_ids,
            since=datetime.combine(first_week, time.min, tzinfo=UTC),
        )
        weekly = [
            WeeklyCount(
                week_start=first_week + timedelta(weeks=i),
                opened=opened_by_week.get(first_week + timedelta(weeks=i), 0),
                merged=merged_by_week.get(first_week + timedelta(weeks=i), 0),
            )
            for i in range(weeks)
        ]
        by_review = await self._repository.open_by_review_state(repository_ids=repository_ids)
        finished = sum(1 for repo in repositories if repo.backfill_completed_at is not None)
        stale_reason = await self._stale_reason(
            connection.id, connection.last_successful_sync_at, now, has_repositories=bool(repositories)
        )

        return PullRequestSummaryResponse(
            connection_status=(
                "needs_attention" if connection.status == "needs_attention" else "active"
            ),
            connection_reason=connection.status_reason,
            repository_count=len(repositories),
            weeks=weeks,
            window_start=first_week,
            last_updated_at=connection.last_successful_sync_at,
            is_stale=stale_reason is not None,
            stale_reason=stale_reason,
            history_complete=finished == len(repositories),
            history_repositories_total=len(repositories),
            history_repositories_complete=finished,
            totals=PullRequestTotals(
                open_now=sum(by_review.values()),
                opened_in_window=sum(week.opened for week in weekly),
                merged_in_window=sum(week.merged for week in weekly),
            ),
            open_by_review_state=ReviewStateCounts(**by_review),
            weekly=weekly,
        )

    async def _stale_reason(
        self,
        connection_id,
        last_updated_at: datetime | None,
        now: datetime,
        *,
        has_repositories: bool,
    ) -> str | None:
        if not has_repositories:
            return None  # nothing is being tracked, so nothing can be out of date
        if await self._sync_status.last_pull_request_run_failed(connection_id):
            return "last_run_failed"
        if last_updated_at is not None and now - last_updated_at > self._stale_after:
            return "not_updated_recently"
        return None

    @staticmethod
    def _empty(first_week: date, weeks: int, *, status: str) -> PullRequestSummaryResponse:
        return PullRequestSummaryResponse(
            connection_status=status,
            connection_reason=None,
            repository_count=0,
            weeks=weeks,
            window_start=first_week,
            last_updated_at=None,
            is_stale=False,
            stale_reason=None,
            history_complete=True,
            history_repositories_total=0,
            history_repositories_complete=0,
            totals=PullRequestTotals(open_now=0, opened_in_window=0, merged_in_window=0),
            open_by_review_state=ReviewStateCounts(),
            weekly=[],
        )


def _monday(day: date) -> date:
    return day - timedelta(days=day.weekday())
