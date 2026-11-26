import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.github_integration.models import GithubConnection


class ConnectionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def commit(self) -> None:
        await self._db.commit()

    async def rollback(self) -> None:
        await self._db.rollback()

    async def get_for_user(self, *, user_id: uuid.UUID) -> GithubConnection | None:
        result = await self._db.execute(
            select(GithubConnection).where(GithubConnection.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_installation_id(self, installation_id: int) -> GithubConnection | None:
        result = await self._db.execute(
            select(GithubConnection).where(GithubConnection.installation_id == installation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, connection_id: uuid.UUID) -> GithubConnection | None:
        """For background jobs, which receive the internal connection ID only."""
        result = await self._db.execute(
            select(GithubConnection).where(GithubConnection.id == connection_id)
        )
        return result.scalar_one_or_none()

    async def upsert_for_user(
        self,
        *,
        user_id: uuid.UUID,
        installation_id: int,
        github_account_id: int,
        github_account_login: str,
        account_type: str,
        permissions: dict[str, Any],
        status: str,
        status_reason: str | None,
        now: datetime,
    ) -> GithubConnection:
        """Create the user's connection or refresh it. One row per user, so repeats are safe."""
        statement = pg_insert(GithubConnection).values(
            id=uuid.uuid4(),
            user_id=user_id,
            installation_id=installation_id,
            github_account_id=github_account_id,
            github_account_login=github_account_login,
            account_type=account_type,
            permissions=permissions,
            status=status,
            status_reason=status_reason,
            last_checked_at=now,
            updated_at=now,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[GithubConnection.user_id],
            set_={
                "installation_id": statement.excluded.installation_id,
                "github_account_id": statement.excluded.github_account_id,
                "github_account_login": statement.excluded.github_account_login,
                "account_type": statement.excluded.account_type,
                "permissions": statement.excluded.permissions,
                "status": statement.excluded.status,
                "status_reason": statement.excluded.status_reason,
                "last_checked_at": now,
                "updated_at": now,
            },
        ).returning(GithubConnection)
        result = await self._db.execute(statement, execution_options={"populate_existing": True})
        return result.scalar_one()

    async def mark_needs_attention(
        self, *, connection_id: uuid.UUID, reason: str, now: datetime
    ) -> None:
        await self._db.execute(
            update(GithubConnection)
            .where(GithubConnection.id == connection_id)
            .values(
                status="needs_attention", status_reason=reason, last_checked_at=now, updated_at=now
            )
        )

    async def mark_repositories_synced(self, *, connection_id: uuid.UUID, now: datetime) -> None:
        await self._db.execute(
            update(GithubConnection)
            .where(GithubConnection.id == connection_id)
            .values(repositories_synced_at=now, last_checked_at=now, updated_at=now)
        )
