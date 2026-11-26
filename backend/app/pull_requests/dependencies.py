from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import get_db
from app.github_integration.connection_dependencies import get_connection_state_service
from app.github_integration.service import ConnectionStateService
from app.pull_requests.repository import PullRequestRepository
from app.pull_requests.summary_service import PullRequestSummaryService
from app.repositories.dependencies import get_repository_service
from app.repositories.service import RepositoryService
from app.synchronization.status_dependencies import get_sync_status_service
from app.synchronization.status_service import SyncStatusService


def get_summary_service(
    db: AsyncSession = Depends(get_db),
    connections: ConnectionStateService = Depends(get_connection_state_service),
    repositories: RepositoryService = Depends(get_repository_service),
    sync_status: SyncStatusService = Depends(get_sync_status_service),
    settings: Settings = Depends(get_settings),
) -> PullRequestSummaryService:
    return PullRequestSummaryService(
        repository=PullRequestRepository(db),
        connections=connections,
        repositories=repositories,
        sync_status=sync_status,
        sync_interval_seconds=settings.sync_interval_seconds,
    )
