import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.synchronization.models import SyncRun


class SyncRunRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def commit(self) -> None:
        await self._db.commit()

    async def rollback(self) -> None:
        await self._db.rollback()

    async def start_run(
        self,
        *,
        connection_id: uuid.UUID,
        kind: str,
        trigger: str,
        now: datetime,
        stale_before: datetime,
    ) -> uuid.UUID | None:
        """Record a new running job, or return None if one is already running.

        A running row older than `stale_before` belongs to a worker that died, so
        it is closed as failed first. The partial unique index then lets only one
        concurrent caller insert; the others get None and should do nothing.
        """
        await self._db.execute(
            update(SyncRun)
            .where(
                SyncRun.connection_id == connection_id,
                SyncRun.status == "running",
                SyncRun.started_at < stale_before,
            )
            .values(status="failed", error_category="abandoned", finished_at=now)
        )
        statement = (
            pg_insert(SyncRun)
            .values(
                id=uuid.uuid4(),
                connection_id=connection_id,
                kind=kind,
                trigger=trigger,
                status="running",
                started_at=now,
            )
            .on_conflict_do_nothing(
                index_elements=[SyncRun.connection_id], index_where=SyncRun.status == "running"
            )
            .returning(SyncRun.id)
        )
        run_id = (await self._db.execute(statement)).scalar_one_or_none()
        await self._db.commit()
        return run_id

    async def finish_run(
        self, *, run_id: uuid.UUID, status: str, error_category: str | None, now: datetime
    ) -> None:
        await self._db.execute(
            update(SyncRun)
            .where(SyncRun.id == run_id)
            .values(status=status, error_category=error_category, finished_at=now)
        )
        await self._db.commit()
