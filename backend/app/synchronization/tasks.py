import asyncio
import logging
import uuid

from celery import Task

from app.github_integration.errors import GitHubUnavailableError
from app.synchronization.celery_app import REPOSITORY_LIST_TASK, celery_app
from app.synchronization.retry import MAX_RETRIES, retry_delay_seconds
from app.synchronization.runner import run_repository_list_sync

logger = logging.getLogger(__name__)

# Unexpected errors get one more try, then stop; the next scheduled run starts fresh.
UNEXPECTED_ERROR_RETRIES = 1


@celery_app.task(bind=True, name=REPOSITORY_LIST_TASK, max_retries=MAX_RETRIES)
def sync_repository_list(self: Task, connection_id: str, trigger: str = "schedule") -> None:
    """Fetch the repositories a connection's App installation can access.

    Receives only the internal connection ID. All logic lives in the service.
    """
    try:
        asyncio.run(run_repository_list_sync(uuid.UUID(connection_id), trigger))
    except GitHubUnavailableError as exc:
        # Temporary: GitHub down or rate limiting. Retry later with a growing delay.
        raise self.retry(
            exc=exc, countdown=retry_delay_seconds(self.request.retries, exc.retry_after)
        ) from exc
    except Exception as exc:
        if self.request.retries >= UNEXPECTED_ERROR_RETRIES:
            raise
        raise self.retry(
            exc=exc, countdown=retry_delay_seconds(self.request.retries), max_retries=UNEXPECTED_ERROR_RETRIES
        ) from exc
