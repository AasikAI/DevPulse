import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.models import OAuthState, User, UserSession


@dataclass(frozen=True)
class ConsumedState:
    nonce_hash: str
    user_id: uuid.UUID | None


class IdentityRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def commit(self) -> None:
        await self._db.commit()

    async def create_oauth_state(
        self,
        *,
        state_hash: str,
        nonce_hash: str,
        purpose: str,
        expires_at: datetime,
        user_id: uuid.UUID | None = None,
    ) -> None:
        self._db.add(
            OAuthState(
                state_hash=state_hash,
                nonce_hash=nonce_hash,
                purpose=purpose,
                user_id=user_id,
                expires_at=expires_at,
            )
        )
        await self._db.flush()

    async def consume_oauth_state(
        self, *, state_hash: str, purpose: str, now: datetime
    ) -> ConsumedState | None:
        """Mark a valid state as used and return what it was bound to.

        A single UPDATE makes this atomic: of two concurrent callbacks with the
        same state, only one matches the `consumed_at IS NULL` condition.
        """
        result = await self._db.execute(
            update(OAuthState)
            .where(
                OAuthState.state_hash == state_hash,
                OAuthState.purpose == purpose,
                OAuthState.consumed_at.is_(None),
                OAuthState.expires_at > now,
            )
            .values(consumed_at=now)
            .returning(OAuthState.nonce_hash, OAuthState.user_id)
        )
        row = result.one_or_none()
        return None if row is None else ConsumedState(nonce_hash=row[0], user_id=row[1])

    async def purge_oauth_states_expired_before(self, cutoff: datetime) -> None:
        await self._db.execute(delete(OAuthState).where(OAuthState.expires_at < cutoff))

    async def upsert_user(
        self,
        *,
        github_user_id: int,
        login: str,
        name: str | None,
        avatar_url: str | None,
        email: str | None,
        now: datetime,
    ) -> User:
        """Create the user or refresh their GitHub profile fields, keyed on GitHub's ID."""
        statement = pg_insert(User).values(
            id=uuid.uuid4(),
            github_user_id=github_user_id,
            login=login,
            name=name,
            avatar_url=avatar_url,
            email=email,
            updated_at=now,
            last_login_at=now,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[User.github_user_id],
            set_={
                "login": statement.excluded.login,
                "name": statement.excluded.name,
                "avatar_url": statement.excluded.avatar_url,
                "email": statement.excluded.email,
                "updated_at": now,
                "last_login_at": now,
            },
        ).returning(User)
        result = await self._db.execute(
            statement, execution_options={"populate_existing": True}
        )
        return result.scalar_one()

    async def create_session(
        self, *, user_id: uuid.UUID, token_hash: str, now: datetime, expires_at: datetime
    ) -> None:
        self._db.add(
            UserSession(
                user_id=user_id,
                token_hash=token_hash,
                created_at=now,
                expires_at=expires_at,
            )
        )
        await self._db.flush()

    async def get_user_for_active_session(
        self, *, token_hash: str, now: datetime
    ) -> User | None:
        result = await self._db.execute(
            select(User)
            .join(UserSession, UserSession.user_id == User.id)
            .where(
                UserSession.token_hash == token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def revoke_session(self, *, token_hash: str, now: datetime) -> None:
        await self._db.execute(
            update(UserSession)
            .where(UserSession.token_hash == token_hash, UserSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
