from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.synchronization.repository import SyncRunRepository
from app.synchronization.status_service import SyncStatusService


def get_sync_status_service(db: AsyncSession = Depends(get_db)) -> SyncStatusService:
    return SyncStatusService(runs=SyncRunRepository(db))
