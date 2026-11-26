from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.repositories.repository import RepositoryRepository
from app.repositories.service import RepositoryService


def get_repository_service(db: AsyncSession = Depends(get_db)) -> RepositoryService:
    return RepositoryService(repository=RepositoryRepository(db))
