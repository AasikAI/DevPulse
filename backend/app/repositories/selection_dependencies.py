from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.github_integration.connection_dependencies import get_connection_state_service
from app.github_integration.dispatcher import SyncDispatcher
from app.github_integration.service import ConnectionStateService
from app.repositories.repository import RepositoryRepository
from app.repositories.selection_service import RepositorySelectionService
from app.synchronization.dependencies import get_sync_dispatcher


def get_selection_service(
    db: AsyncSession = Depends(get_db),
    connections: ConnectionStateService = Depends(get_connection_state_service),
    dispatcher: SyncDispatcher = Depends(get_sync_dispatcher),
) -> RepositorySelectionService:
    return RepositorySelectionService(
        repository=RepositoryRepository(db), connections=connections, dispatcher=dispatcher
    )
