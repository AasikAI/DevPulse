import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from app.common.clock import utcnow
from app.common.errors import NotConfiguredError
from app.github_integration.client import PULL_REQUESTS_PER_PAGE, GitHubClient
from app.github_integration.dispatcher import SyncDispatcher
from app.github_integration.errors import (
    GitHubAccessError,
    GitHubRateLimitedError,
    GitHubRepositoryGoneError,
    GitHubUnavailableError,
)
from app.github_integration.schemas import ConnectionInfo
from app.github_integration.service import ConnectionStateService
from app.pull_requests.service import PullRequestService
from app.repositories.schemas import SyncRepository
from app.repositories.service import RepositoryService
from app.synchronization.repository import SyncRunRepository
from app.synchronization.retry import RATE_LIMIT_RETRY_CEILING_SECONDS

logger = logging.getLogger(__name__)

REPOSITORY_LIST_KIND = "repository_list"
PULL_REQUESTS_KIND = "pull_requests"
# A "running" row older than this is a worker that died; it no longer blocks new runs.
STALE_RUN_AFTER = timedelta(minutes=20)
# Pull requests changed in the last minutes before the watermark are read again, as a safety margin.
WATERMARK_OVERLAP = timedelta(minutes=5)
REVIEWS_BATCH_SIZE = 20


class SyncOutcome(StrEnum):
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    NEEDS_ATTENTION = "needs_attention"
    RATE_LIMITED = "rate_limited"
    SKIPPED_NOT_FOUND = "skipped_not_found"
    SKIPPED_NOT_ACTIVE = "skipped_not_active"
    SKIPPED_ALREADY_RUNNING = "skipped_already_running"
    SKIPPED_RATE_LIMITED = "skipped_rate_limited"


@dataclass
class SyncBudget:
    """Tells a run when to stop: before the task time limit, a request cap, or GitHub's hourly limit.

    Stopping early is normal for a big history. The progress is saved and the
    next run carries on from there.
    """

    github: GitHubClient
    clock: Callable[[], datetime]
    deadline: datetime
    max_requests: int  # 0 means no cap
    rate_reserve: int
    start_requests: int = 0

    def exhausted(self) -> bool:
        if self.clock() >= self.deadline:
            return True
        if self.max_requests and self.github.request_count - self.start_requests >= self.max_requests:
            return True
        remaining = self.github.rate_limit_remaining
        return remaining is not None and remaining < self.rate_reserve


Work = Callable[[ConnectionInfo, str, dict[str, Any]], Awaitable[str]]


class SynchronizationService:
    """Background use cases. Celery tasks call this and nothing else."""

    def __init__(
        self,
        *,
        runs: SyncRunRepository,
        connections: ConnectionStateService,
        repositories: RepositoryService,
        pull_requests: PullRequestService,
        github: GitHubClient,
        clock: Callable[[], datetime] = utcnow,
        budget_seconds: int = 480,
        max_requests: int = 0,
        rate_reserve: int = 200,
    ) -> None:
        self._runs = runs
        self._connections = connections
        self._repositories = repositories
        self._pull_requests = pull_requests
        self._github = github
        self._clock = clock
        self._budget_seconds = budget_seconds
        self._max_requests = max_requests
        self._rate_reserve = rate_reserve

    # --- Entry points ----------------------------------------------------------------------

    async def refresh_repository_list(
        self, connection_id: uuid.UUID, trigger: str
    ) -> SyncOutcome:
        """Fetch the repositories the App can access and store them."""
        return await self._run(connection_id, trigger, REPOSITORY_LIST_KIND, self._repository_list_work)

    async def sync_pull_requests(self, connection_id: uuid.UUID, trigger: str) -> SyncOutcome:
        """Refresh the repository list, then import pull requests for the selected repositories."""
        return await self._run(connection_id, trigger, PULL_REQUESTS_KIND, self._pull_requests_work)

    async def dispatch_due_syncs(self, dispatcher: SyncDispatcher) -> int:
        """Queue one pull request job for every connection that is due. Returns how many."""
        due = await self._connections.list_due_ids()
        for connection_id in due:
            await dispatcher.dispatch_pull_requests(connection_id, "schedule")
        logger.info("scheduled syncs queued", extra={"connection_count": len(due)})
        return len(due)

    # --- The shared run lifecycle ----------------------------------------------------------

    async def _run(
        self, connection_id: uuid.UUID, trigger: str, kind: str, work: Work
    ) -> SyncOutcome:
        """Run one job safely: one at a time per connection, with errors sorted into
        retryable (raised), needs-attention (recorded), and unexpected (raised, logged).

        Safe to run twice: data is upserted, and a second concurrent run for the same
        connection exits without doing anything.
        """
        log: dict[str, Any] = {"connection_id": str(connection_id), "trigger": trigger, "kind": kind}
        connection = await self._connections.get_for_sync(connection_id)
        if connection is None:
            logger.warning("sync job for an unknown connection", extra=log)
            return SyncOutcome.SKIPPED_NOT_FOUND
        if connection.status != "active":
            logger.info("sync job skipped: connection needs attention", extra=log)
            return SyncOutcome.SKIPPED_NOT_ACTIVE

        now = self._clock()
        if trigger == "schedule" and connection.rate_limited_until and connection.rate_limited_until > now:
            logger.info("sync job skipped: waiting out a rate limit", extra=log)
            return SyncOutcome.SKIPPED_RATE_LIMITED

        run_id = await self._runs.start_run(
            connection_id=connection_id,
            kind=kind,
            trigger=trigger,
            now=now,
            stale_before=now - STALE_RUN_AFTER,
        )
        if run_id is None:
            logger.info("sync job skipped: already running", extra=log)
            return SyncOutcome.SKIPPED_ALREADY_RUNNING
        log["sync_run_id"] = str(run_id)

        try:
            # The installation token lives only inside this run and is never stored or logged.
            token = await self._github.create_installation_token(connection.installation_id)
            result = await work(connection, token, log)
            if kind == PULL_REQUESTS_KIND:
                await self._connections.mark_sync_success(connection_id)
            await self._finish(run_id, result, None)
            logger.info("sync finished", extra={**log, "result": result})
            return SyncOutcome(result)
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
            # Too far away to retry inside this task: wait it out, then the schedule resumes.
            until = exc.reset_at or self._clock() + timedelta(seconds=exc.retry_after)
            await self._connections.mark_rate_limited(connection_id, until)
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
            logger.exception("sync job failed unexpectedly", extra=log)
            raise

    async def _finish(self, run_id: uuid.UUID, status: str, error_category: str | None) -> None:
        await self._runs.finish_run(
            run_id=run_id, status=status, error_category=error_category, now=self._clock()
        )

    # --- The work of each kind of run ---------------------------------------------------------

    async def _repository_list_work(
        self, connection: ConnectionInfo, token: str, log: dict[str, Any]
    ) -> str:
        await self._refresh_repositories(connection, token, log)
        return "succeeded"

    async def _refresh_repositories(
        self, connection: ConnectionInfo, token: str, log: dict[str, Any]
    ) -> None:
        repositories = await self._github.list_installation_repositories(token)
        await self._repositories.sync_from_github(
            connection_id=connection.id, repositories=repositories
        )
        await self._connections.mark_repositories_synced(connection.id)
        logger.info("repository list synced", extra={**log, "repository_count": len(repositories)})

    async def _pull_requests_work(
        self, connection: ConnectionInfo, token: str, log: dict[str, Any]
    ) -> str:
        # Always refresh the list first, so new repositories reach the selection page.
        await self._refresh_repositories(connection, token, log)

        budget = SyncBudget(
            github=self._github,
            clock=self._clock,
            deadline=self._clock() + timedelta(seconds=self._budget_seconds),
            max_requests=self._max_requests,
            rate_reserve=self._rate_reserve,
            start_requests=self._github.request_count,
        )
        repositories = await self._repositories.list_for_sync(connection_id=connection.id)

        # Phase 1: bring in the pull requests of every selected repository.
        for repo in repositories:
            try:
                finished = await self._import_repository(connection, token, repo, budget, log)
            except GitHubRepositoryGoneError:
                await self._drop_unavailable(repo, log)
                continue
            if not finished:
                return "partial"

        # Phase 2: with what is left of the budget, read review state.
        for repo in repositories:
            try:
                finished = await self._load_reviews(connection, token, repo, budget, log)
            except GitHubRepositoryGoneError:
                await self._drop_unavailable(repo, log)
                continue
            if not finished:
                return "partial"
        return "succeeded"

    async def _drop_unavailable(self, repo: SyncRepository, log: dict[str, Any]) -> None:
        logger.warning("repository is gone on github", extra={**log, "repository_id": str(repo.id)})
        await self._repositories.mark_unavailable(repository_id=repo.id)

    # --- Phase 1: pull requests ------------------------------------------------------------------

    async def _import_repository(
        self,
        connection: ConnectionInfo,
        token: str,
        repo: SyncRepository,
        budget: SyncBudget,
        log: dict[str, Any],
    ) -> bool:
        """True when this repository is up to date for this run; False when the budget ran out."""
        if repo.backfill_completed_at is None:
            return await self._backfill(connection, token, repo, budget)
        return await self._incremental(connection, token, repo, budget)

    async def _tracked(self, connection: ConnectionInfo, repo: SyncRepository) -> bool:
        return await self._repositories.is_tracked(
            repository_id=repo.id, connection_id=connection.id
        )

    async def _backfill(
        self, connection: ConnectionInfo, token: str, repo: SyncRepository, budget: SyncBudget
    ) -> bool:
        """Import the whole history, oldest first, a page at a time.

        Each page and the cursor pointing past it are committed together, so a stop
        at any moment loses nothing and repeats at most one page.
        """
        started = repo.backfill_started_at
        if started is None:
            started = self._clock()
            await self._repositories.stage_sync_state(
                repository_id=repo.id, backfill_started_at=started
            )
            await self._runs.commit()

        page = repo.backfill_cursor
        while True:
            if budget.exhausted():
                return False
            if not await self._tracked(connection, repo):
                return True  # unselected during the run: leave it as it is
            pull_requests = await self._github.list_pull_requests(
                token, full_name=repo.full_name, sort="created", direction="asc", page=page
            )
            await self._pull_requests.stage_page(
                repository_id=repo.id, pull_requests=pull_requests
            )
            if len(pull_requests) < PULL_REQUESTS_PER_PAGE:
                now = self._clock()
                await self._repositories.stage_sync_state(
                    repository_id=repo.id,
                    backfill_completed_at=now,
                    # Anything that changed while the import ran is caught by the next pass.
                    incremental_watermark=started,
                    last_synced_at=now,
                )
                await self._runs.commit()
                return True
            page += 1
            await self._repositories.stage_sync_state(repository_id=repo.id, backfill_cursor=page)
            await self._runs.commit()

    async def _incremental(
        self, connection: ConnectionInfo, token: str, repo: SyncRepository, budget: SyncBudget
    ) -> bool:
        """Read recently updated pull requests until reaching ones older than the watermark."""
        assert repo.incremental_watermark is not None
        run_started = self._clock()
        cutoff = repo.incremental_watermark - WATERMARK_OVERLAP
        page = 1
        while True:
            if budget.exhausted():
                return False  # the watermark stays, so the next run starts again from the top
            if not await self._tracked(connection, repo):
                return True
            pull_requests = await self._github.list_pull_requests(
                token, full_name=repo.full_name, sort="updated", direction="desc", page=page
            )
            await self._pull_requests.stage_page(
                repository_id=repo.id, pull_requests=pull_requests
            )
            await self._runs.commit()
            reached_old = bool(pull_requests) and pull_requests[-1].updated_at < cutoff
            if len(pull_requests) < PULL_REQUESTS_PER_PAGE or reached_old:
                await self._repositories.stage_sync_state(
                    repository_id=repo.id,
                    incremental_watermark=run_started,
                    last_synced_at=run_started,
                )
                await self._runs.commit()
                return True
            page += 1

    # --- Phase 2: review state -------------------------------------------------------------------

    async def _load_reviews(
        self,
        connection: ConnectionInfo,
        token: str,
        repo: SyncRepository,
        budget: SyncBudget,
        log: dict[str, Any],
    ) -> bool:
        """Read reviews for pull requests that lack them: open ones first, then the newest.

        Each result is saved right after its request, so a stop keeps all progress.
        """
        while True:
            if not await self._tracked(connection, repo):
                return True
            backlog = await self._pull_requests.reviews_backlog(
                repository_id=repo.id, limit=REVIEWS_BATCH_SIZE
            )
            if not backlog:
                return True
            for pull_request in backlog:
                if budget.exhausted():
                    return False
                review_state = await self._github.get_review_state(
                    token, full_name=repo.full_name, number=pull_request.number
                )
                await self._pull_requests.save_review_state(
                    pull_request_id=pull_request.id,
                    review_state=review_state,
                    loaded_for=pull_request.updated_at_gh,
                )
