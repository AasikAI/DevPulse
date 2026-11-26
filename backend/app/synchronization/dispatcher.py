import asyncio
import logging
import uuid

from app.synchronization.celery_app import REPOSITORY_LIST_TASK, celery_app

logger = logging.getLogger(__name__)


class CelerySyncDispatcher:
    """Queues background jobs. Only internal IDs are sent, never credentials."""

    async def dispatch_repository_list(self, connection_id: uuid.UUID, trigger: str) -> bool:
        try:
            # send_task blocks while talking to Redis, so keep it off the event loop.
            await asyncio.to_thread(
                celery_app.send_task,
                REPOSITORY_LIST_TASK,
                args=[str(connection_id)],
                kwargs={"trigger": trigger},
            )
        except Exception as exc:
            # The connection is already saved; the next scheduled run picks the work up.
            logger.error(
                "could not queue a background job",
                extra={"connection_id": str(connection_id), "error": type(exc).__name__},
            )
            return False
        return True
