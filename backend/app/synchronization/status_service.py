import uuid

from app.synchronization.repository import SyncRunRepository

PULL_REQUESTS_KIND = "pull_requests"

# A run that ended this way means the stored data could not be brought up to date.
FAILED_STATUSES = {"failed", "rate_limited"}


class SyncStatusService:
    """Read-only view of background job results, for screens that show data freshness."""

    def __init__(self, *, runs: SyncRunRepository) -> None:
        self._runs = runs

    async def last_pull_request_run_failed(self, connection_id: uuid.UUID) -> bool:
        """True when the most recent finished pull request run failed or was rate limited.

        A partial run (stopped at its budget, carrying on next time) is not a failure.
        """
        status = await self._runs.latest_finished_status(
            connection_id=connection_id, kind=PULL_REQUESTS_KIND
        )
        return status in FAILED_STATUSES
