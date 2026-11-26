from typing import Protocol
import uuid


class SyncDispatcher(Protocol):
    """Asks the background workers to run a job. Implemented in `synchronization`.

    Defined here, as a protocol, so services can start jobs without importing
    Celery and so tests can record what was requested.
    """

    async def dispatch_repository_list(self, connection_id: uuid.UUID, trigger: str) -> bool:
        """Queue a repository-list job. Returns False when it could not be queued."""
        ...
