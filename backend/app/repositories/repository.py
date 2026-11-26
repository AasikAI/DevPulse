import uuid
from datetime import datetime
from typing import Any
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

    async def list_available(
        self, *, connection_id: uuid.UUID, search: str | None, limit: int, offset: int
    ) -> tuple[list[GithubRepository], int]:
        """One page of available repositories by name, and the total matching the search."""
        conditions = [
            GithubRepository.connection_id == connection_id,
            GithubRepository.is_available.is_(True),
        ]
        if search:
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            conditions.append(GithubRepository.full_name.ilike(f"%{escaped}%", escape="\\"))
        total = (
            await self._db.execute(
                select(func.count()).select_from(GithubRepository).where(*conditions)
            )
        ).scalar_one()
        rows = (
            await self._db.execute(
                select(GithubRepository)
                .where(*conditions)
                .order_by(func.lower(GithubRepository.full_name), GithubRepository.id)
                .limit(limit)
                .offset(offset)
            )
        ).scalars()
        return list(rows), total

    async def count_selected(self, *, connection_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(func.count())
            .select_from(GithubRepository)
            .where(
                GithubRepository.connection_id == connection_id,
                GithubRepository.is_available.is_(True),
                GithubRepository.is_selected.is_(True),
            )
        )
        return result.scalar_one()

    async def find_owned(
        self, *, connection_id: uuid.UUID, repository_ids: set[uuid.UUID]
    ) -> list[GithubRepository]:
        """Only repositories of this connection; anything else is simply not returned."""
        if not repository_ids:
            return []
        result = await self._db.execute(
            select(GithubRepository).where(
                GithubRepository.connection_id == connection_id,
                GithubRepository.id.in_(repository_ids),
            )
        )
        return list(result.scalars())

    async def set_selected(
        self,
        *,
        connection_id: uuid.UUID,
        repository_ids: set[uuid.UUID],
        selected: bool,
        now: datetime,
    ) -> int:
        """Change the selection of these repositories; rows already in that state are untouched.

        Returns how many repositories actually changed.
        """
        if not repository_ids:
            return 0
        result = await self._db.execute(
            update(GithubRepository)
            .where(
                GithubRepository.connection_id == connection_id,
                GithubRepository.id.in_(repository_ids),
                GithubRepository.is_selected.is_(not selected),
            )
            .values(
                is_selected=selected,
                selected_at=now if selected else None,
                updated_at=now,
            )
        )
        return result.rowcount

    async def list_for_sync(self, *, connection_id: uuid.UUID) -> list[GithubRepository]:
        """Selected, available repositories; the least recently synced first."""
        result = await self._db.execute(
            select(GithubRepository)
            .where(
                GithubRepository.connection_id == connection_id,
                GithubRepository.is_selected.is_(True),
                GithubRepository.is_available.is_(True),
            )
            .order_by(GithubRepository.last_synced_at.asc().nulls_first(), GithubRepository.full_name)
        )
        return list(result.scalars())

    async def is_tracked(self, *, repository_id: uuid.UUID, connection_id: uuid.UUID) -> bool:
        """Still selected and available? Checked between pages, since the user can unselect mid-run."""
        result = await self._db.execute(
            select(GithubRepository.id).where(
                GithubRepository.id == repository_id,
                GithubRepository.connection_id == connection_id,
                GithubRepository.is_selected.is_(True),
                GithubRepository.is_available.is_(True),
            )
        )
        return result.scalar_one_or_none() is not None

    async def update_sync_state(
        self, *, repository_id: uuid.UUID, values: dict[str, Any], now: datetime
    ) -> None:
        """Save import progress. Does not commit, so it can join a page's transaction."""
        allowed = {
            "backfill_cursor",
            "backfill_started_at",
            "backfill_completed_at",
            "incremental_watermark",
            "last_synced_at",
        }
        if not set(values) <= allowed:
            raise ValueError("unknown sync state field")
        await self._db.execute(
            update(GithubRepository)
            .where(GithubRepository.id == repository_id)
            .values(**values, updated_at=now)
        )

    async def mark_unavailable(self, *, repository_id: uuid.UUID, now: datetime) -> None:
        await self._db.execute(
            update(GithubRepository)
            .where(GithubRepository.id == repository_id)
            .values(is_available=False, updated_at=now)
        )
