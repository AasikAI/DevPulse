import logging
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import StrEnum

from app.common.clock import utcnow
from app.common.errors import NotConfiguredError
from app.github_integration.client import GitHubClient
from app.github_integration.errors import (
    GitHubAccessError,
    GitHubRateLimitedError,
    GitHubUnavailableError,
)
from app.github_integration.service import ConnectionStateService
from app.repositories.service import RepositoryService
from app.synchronization.repository import SyncRunRepository
from app.synchronization.retry import RATE_LIMIT_RETRY_CEILING_SECONDS

logger = logging.getLogger(__name__)

REPOSITORY_LIST_KIND = "repository_list"
# A "running" row older than this is a worker that died; it no longer blocks new runs.
STALE_RUN_AFTER = timedelta(minutes=20)


class SyncOutcome(StrEnum):
    SUCCEEDED = "succeeded"
    NEEDS_ATTENTION = "needs_attention"
    RATE_LIMITED = "rate_limited"
    SKIPPED_NOT_FOUND = "skipped_not_found"
    SKIPPED_NOT_ACTIVE = "skipped_not_active"
    SKIPPED_ALREADY_RUNNING = "skipped_already_running"


class SynchronizationService:
    """Background use cases. Celery tasks call this and nothing else."""

    def __init__(
        self,
        *,
        runs: SyncRunRepository,
        connections: ConnectionStateService,
        repositories: RepositoryService,
        github: GitHubClient,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._runs = runs
        self._connections = connections
        self._repositories = repositories
        self._github = github
        self._clock = clock

    async def refresh_repository_list(
        self, connection_id: uuid.UUID, trigger: str
    ) -> SyncOutcome:
        """Fetch the repositories the App can access and store them.

        Safe to run twice: repositories are upserted, and a second concurrent run
        for the same connection exits without doing anything. Temporary GitHub
        problems raise so the task can retry; lost access marks the connection
        as needing attention and does not.
        """
        log = {"connection_id": str(connection_id), "trigger": trigger}
        connection = await self._connections.get_for_sync(connection_id)
        if connection is None:
            logger.warning("repository list job for an unknown connection", extra=log)
            return SyncOutcome.SKIPPED_NOT_FOUND
        if connection.status != "active":
            logger.info("repository list job skipped: connection needs attention", extra=log)
            return SyncOutcome.SKIPPED_NOT_ACTIVE

        now = self._clock()
        run_id = await self._runs.start_run(
            connection_id=connection_id,
            kind=REPOSITORY_LIST_KIND,
            trigger=trigger,
            now=now,
            stale_before=now - STALE_RUN_AFTER,
        )
        if run_id is None:
            logger.info("repository list job skipped: already running", extra=log)
            return SyncOutcome.SKIPPED_ALREADY_RUNNING
        log["sync_run_id"] = str(run_id)

        try:
            # The installation token lives only in this call and is never stored or logged.
            token = await self._github.create_installation_token(connection.installation_id)
            repositories = await self._github.list_installation_repositories(token)
            del token
            await self._repositories.sync_from_github(
                connection_id=connection_id, repositories=repositories
            )
            await self._connections.mark_repositories_synced(connection_id)
            await self._finish(run_id, "succeeded", None)
            logger.info(
                "repository list synced", extra={**log, "repository_count": len(repositories)}
            )
            return SyncOutcome.SUCCEEDED
        except GitHubAccessError as exc:
            await self._runs.rollback()
            await self._finish(run_id, "failed", exc.reason)
            await self._connections.mark_needs_attention(connection_id, exc.reason)
            logger.warning("github access problem", extra={**log, "reason": exc.reason})
            return SyncOutcome.NEEDS_ATTENTION
        except GitHubRateLimitedError as exc:
            await self._runs.rollback()
            await self._finish(run_id, "rate_limited", "rate_limited")
            logger.warning("github rate limit reached", extra=log)
            if exc.retry_after is None or exc.retry_after <= RATE_LIMIT_RETRY_CEILING_SECONDS:
                raise
            # Too far away to retry inside this task; the next scheduled run tries again.
            return SyncOutcome.RATE_LIMITED
        except GitHubUnavailableError:
            await self._runs.rollback()
            await self._finish(run_id, "failed", "github_unavailable")
            raise
        except NotConfiguredError:
            await self._runs.rollback()
            await self._finish(run_id, "failed", "not_configured")
            raise
        except Exception:
            await self._runs.rollback()
            await self._finish(run_id, "failed", "unexpected")
            logger.exception("repository list job failed unexpectedly", extra=log)
            raise

    async def _finish(self, run_id: uuid.UUID, status: str, error_category: str | None) -> None:
        await self._runs.finish_run(
            run_id=run_id, status=status, error_category=error_category, now=self._clock()
        )
