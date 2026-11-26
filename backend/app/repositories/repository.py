import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.github_integration.schemas import GitHubRepositoryInfo
from app.repositories.models import GithubRepository


class RepositoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def commit(self) -> None:
        await self._db.commit()

    async def upsert_many(
        self, *, connection_id: uuid.UUID, repositories: list[GitHubRepositoryInfo], now: datetime
    ) -> None:
        """Insert new repositories and refresh names; safe to run twice."""
        if not repositories:
            return
        statement = pg_insert(GithubRepository).values(
            [
                {
                    "id": uuid.uuid4(),
                    "connection_id": connection_id,
                    "github_repo_id": repo.id,
                    "owner_login": repo.owner_login,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "is_private": repo.is_private,
                    "is_available": True,
                    "updated_at": now,
                }
                for repo in repositories
            ]
        )
        statement = statement.on_conflict_do_update(
            constraint="uq_repositories_connection_repo",
            set_={
                "owner_login": statement.excluded.owner_login,
                "name": statement.excluded.name,
                "full_name": statement.excluded.full_name,
                "is_private": statement.excluded.is_private,
                "is_available": True,
                "updated_at": now,
            },
        )
        await self._db.execute(statement)

    async def mark_missing_unavailable(
        self, *, connection_id: uuid.UUID, seen_github_ids: list[int], now: datetime
    ) -> None:
        """Repositories the App no longer sees are hidden, not deleted."""
        await self._db.execute(
            update(GithubRepository)
            .where(
                GithubRepository.connection_id == connection_id,
                GithubRepository.is_available.is_(True),
                GithubRepository.github_repo_id.not_in(seen_github_ids),
            )
            .values(is_available=False, updated_at=now)
        )

    async def count_available(self, *, connection_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(func.count())
            .select_from(GithubRepository)
            .where(
                GithubRepository.connection_id == connection_id,
                GithubRepository.is_available.is_(True),
            )
        )
        return result.scalar_one()
