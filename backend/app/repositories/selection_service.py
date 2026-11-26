import logging
import uuid
from collections.abc import Callable
from datetime import datetime

from app.common.clock import utcnow
from app.github_integration.dispatcher import SyncDispatcher
from app.github_integration.service import ConnectionStateService
from app.identity.schemas import CurrentUser
from app.repositories.errors import (
    NoConnectionError,
    RepositoryNotFoundError,
    RepositoryUnavailableError,
)
from app.repositories.repository import RepositoryRepository
from app.repositories.schemas import (
    RepositoryItem,
    RepositoryListResponse,
    SelectionResponse,
)

logger = logging.getLogger(__name__)


class RepositorySelectionService:
    """Which of the user's repositories DevPulse should track."""

    def __init__(
        self,
        *,
        repository: RepositoryRepository,
        connections: ConnectionStateService,
        dispatcher: SyncDispatcher,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._repository = repository
        self._connections = connections
        self._dispatcher = dispatcher
        self._clock = clock

    async def list_repositories(
        self, user: CurrentUser, *, search: str | None, page: int, page_size: int
    ) -> RepositoryListResponse:
        connection = await self._connections.get_for_user(user.id)
        if connection is None:
            raise NoConnectionError()
        rows, total = await self._repository.list_available(
            connection_id=connection.id,
            search=(search or "").strip() or None,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        selected_count = await self._repository.count_selected(connection_id=connection.id)
        return RepositoryListResponse(
            list_status="ready" if connection.repositories_synced_at else "syncing",
            refreshed_at=connection.repositories_synced_at,
            total=total,
            selected_count=selected_count,
            page=page,
            page_size=page_size,
            items=[RepositoryItem.model_validate(row) for row in rows],
        )

    async def save_selection(
        self, user: CurrentUser, *, select: list[uuid.UUID], unselect: list[uuid.UUID]
    ) -> SelectionResponse:
        """Apply the changes all together or not at all.

        A repository that is not the user's looks the same as one that does not exist.
        Only repositories the App can still access may be selected; unselecting is
        always allowed, so a repository that disappeared from GitHub can still be dropped.
        Unselecting keeps the repository's stored data.
        """
        connection = await self._connections.get_for_user(user.id)
        if connection is None:
            raise NoConnectionError()

        select_ids, unselect_ids = set(select), set(unselect)
        owned = {
            row.id: row
            for row in await self._repository.find_owned(
                connection_id=connection.id, repository_ids=select_ids | unselect_ids
            )
        }
        if set(owned) != select_ids | unselect_ids:
            raise RepositoryNotFoundError()
        if any(not owned[repo_id].is_available for repo_id in select_ids):
            raise RepositoryUnavailableError()

        now = self._clock()
        newly_selected = await self._repository.set_selected(
            connection_id=connection.id, repository_ids=select_ids, selected=True, now=now
        )
        await self._repository.set_selected(
            connection_id=connection.id, repository_ids=unselect_ids, selected=False, now=now
        )
        await self._repository.commit()
        if newly_selected:
            # Queued only after the commit, so the worker sees the new selection.
            queued = await self._dispatcher.dispatch_pull_requests(
                connection.id, "selection_saved"
            )
            if not queued:
                # The selection is saved; the scheduled run picks the repositories up.
                logger.warning(
                    "could not queue the pull request job",
                    extra={"connection_id": str(connection.id)},
                )
        return SelectionResponse(
            selected_count=await self._repository.count_selected(connection_id=connection.id)
        )
