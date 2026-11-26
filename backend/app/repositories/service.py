import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.common.clock import utcnow
from app.github_integration.schemas import GitHubRepositoryInfo
from app.repositories.repository import RepositoryRepository
from app.repositories.schemas import SyncRepository


class RepositoryService:
    def __init__(
        self,
        *,
        repository: RepositoryRepository,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._repository = repository
        self._clock = clock

    async def sync_from_github(
        self, *, connection_id: uuid.UUID, repositories: list[GitHubRepositoryInfo]
    ) -> None:
        """Make the stored list match what the App can see right now.

        New repositories are added, renamed ones updated, and ones that
        disappeared are marked unavailable (their rows are kept). One transaction.
        """
        now = self._clock()
        await self._repository.upsert_many(
            connection_id=connection_id, repositories=repositories, now=now
        )
        await self._repository.mark_missing_unavailable(
            connection_id=connection_id,
            seen_github_ids=[repo.id for repo in repositories],
            now=now,
        )
        await self._repository.commit()

    async def count_available(self, *, connection_id: uuid.UUID) -> int:
        return await self._repository.count_available(connection_id=connection_id)

    # --- Used by the pull request sync -----------------------------------------------

    async def list_for_sync(self, *, connection_id: uuid.UUID) -> list[SyncRepository]:
        rows = await self._repository.list_for_sync(connection_id=connection_id)
        return [SyncRepository.model_validate(row) for row in rows]

    async def is_tracked(self, *, repository_id: uuid.UUID, connection_id: uuid.UUID) -> bool:
        return await self._repository.is_tracked(
            repository_id=repository_id, connection_id=connection_id
        )

    async def stage_sync_state(self, *, repository_id: uuid.UUID, **values: Any) -> None:
        """Record import progress without committing.

        The caller commits together with the pull requests it just stored, so a page
        and its cursor are saved as one unit.
        """
        await self._repository.update_sync_state(
            repository_id=repository_id, values=values, now=self._clock()
        )

    async def mark_unavailable(self, *, repository_id: uuid.UUID) -> None:
        await self._repository.mark_unavailable(repository_id=repository_id, now=self._clock())
        await self._repository.commit()
