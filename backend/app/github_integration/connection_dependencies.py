from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.github_integration.client import GitHubClient
from app.github_integration.dependencies import get_github_client
from app.github_integration.dispatcher import SyncDispatcher
from app.github_integration.repository import ConnectionRepository
from app.github_integration.service import ConnectionService, ConnectionStateService
from app.identity.dependencies import get_identity_service
from app.identity.service import IdentityService
from app.repositories.dependencies import get_repository_service
from app.repositories.service import RepositoryService
from app.synchronization.dependencies import get_sync_dispatcher


def get_connection_state_service(db: AsyncSession = Depends(get_db)) -> ConnectionStateService:
    return ConnectionStateService(repository=ConnectionRepository(db))


def get_connection_service(
    db: AsyncSession = Depends(get_db),
    identity: IdentityService = Depends(get_identity_service),
    repositories: RepositoryService = Depends(get_repository_service),
    github: GitHubClient = Depends(get_github_client),
    dispatcher: SyncDispatcher = Depends(get_sync_dispatcher),
) -> ConnectionService:
    return ConnectionService(
        repository=ConnectionRepository(db),
        identity=identity,
        repositories=repositories,
        github=github,
        dispatcher=dispatcher,
    )
