import uuid
from collections.abc import Callable
from datetime import datetime

from app.common.clock import utcnow
from app.github_integration.schemas import GitHubRepositoryInfo
from app.repositories.repository import RepositoryRepository


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
