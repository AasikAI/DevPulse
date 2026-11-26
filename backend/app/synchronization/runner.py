import uuid

import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.github_integration.client import GitHubClient
from app.github_integration.repository import ConnectionRepository
from app.github_integration.service import ConnectionStateService
from app.repositories.repository import RepositoryRepository
from app.repositories.service import RepositoryService
from app.synchronization.repository import SyncRunRepository
from app.synchronization.service import SynchronizationService, SyncOutcome


async def run_repository_list_sync(
    connection_id: uuid.UUID,
    trigger: str,
    *,
    http_transport: httpx.AsyncBaseTransport | None = None,
) -> SyncOutcome:
    """Wire up the services for one job run and execute it.

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
            service = SynchronizationService(
                runs=SyncRunRepository(session),
                connections=ConnectionStateService(repository=ConnectionRepository(session)),
                repositories=RepositoryService(repository=RepositoryRepository(session)),
                github=github,
            )
            return await service.refresh_repository_list(connection_id, trigger)
    finally:
        await engine.dispose()
