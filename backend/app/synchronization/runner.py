import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.github_integration.client import GitHubClient
from app.github_integration.dispatcher import SyncDispatcher
from app.github_integration.repository import ConnectionRepository
from app.github_integration.service import ConnectionStateService
from app.pull_requests.repository import PullRequestRepository
from app.pull_requests.service import PullRequestService
from app.repositories.repository import RepositoryRepository
from app.repositories.service import RepositoryService
from app.synchronization.dispatcher import CelerySyncDispatcher
from app.synchronization.repository import SyncRunRepository
from app.synchronization.service import SynchronizationService, SyncOutcome


@asynccontextmanager
async def _service(
    http_transport: httpx.AsyncBaseTransport | None = None,
    *,
    budget_seconds: int | None = None,
    max_requests: int | None = None,
) -> AsyncIterator[SynchronizationService]:
    """Wire up the services for one job run.

    Each run gets its own database engine without a connection pool: Celery runs
    every task in a fresh event loop, and pooled connections cannot move between
    loops. `http_transport` lets tests replace the network.
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        async with (
            httpx.AsyncClient(timeout=15.0, transport=http_transport) as http,
            async_sessionmaker(engine, expire_on_commit=False)() as session,
        ):
            github = GitHubClient(
                client_id=settings.github_app_client_id,
                client_secret=settings.github_app_client_secret.get_secret_value(),
                http=http,
                app_id=settings.github_app_id,
                app_slug=settings.github_app_slug,
                private_key_path=settings.github_app_private_key_path,
            )
            yield SynchronizationService(
                runs=SyncRunRepository(session),
                connections=ConnectionStateService(repository=ConnectionRepository(session)),
                repositories=RepositoryService(repository=RepositoryRepository(session)),
                pull_requests=PullRequestService(repository=PullRequestRepository(session)),
                github=github,
                budget_seconds=(
                    settings.sync_run_budget_seconds if budget_seconds is None else budget_seconds
                ),
                max_requests=(
                    settings.sync_run_max_requests if max_requests is None else max_requests
                ),
                rate_reserve=settings.sync_rate_limit_reserve,
            )
    finally:
        await engine.dispose()


async def run_repository_list_sync(
    connection_id: uuid.UUID,
    trigger: str,
    *,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> SyncOutcome:
    async with _service(http_transport) as service:
        return await service.refresh_repository_list(connection_id, trigger)


async def run_pull_request_sync(
    connection_id: uuid.UUID,
    trigger: str,
    *,
    http_transport: httpx.AsyncBaseTransport | None = None,
    budget_seconds: int | None = None,
    max_requests: int | None = None,
) -> SyncOutcome:
    async with _service(
        http_transport, budget_seconds=budget_seconds, max_requests=max_requests
    ) as service:
        return await service.sync_pull_requests(connection_id, trigger)


async def run_dispatch_due_syncs(dispatcher: SyncDispatcher | None = None) -> int:
    async with _service() as service:
        return await service.dispatch_due_syncs(dispatcher or CelerySyncDispatcher())
