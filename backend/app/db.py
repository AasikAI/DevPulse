from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)

# expire_on_commit=False keeps loaded attributes usable after commit,
# which matters in async code where lazy reloads are not allowed.
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class for all ORM models (used by Alembic in part B)."""


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
