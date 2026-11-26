from celery import Celery
from celery.signals import setup_logging

from app.common.logging import configure_logging
from app.config import get_settings

REPOSITORY_LIST_TASK = "sync.repository_list"
PULL_REQUESTS_TASK = "sync.pull_requests"
DISPATCH_DUE_TASK = "sync.dispatch_due"

_settings = get_settings()


@setup_logging.connect
def _use_structured_logging(**_: object) -> None:
    # Replaces Celery's default log setup so worker logs are JSON and redacted too.
    configure_logging()


celery_app = Celery(
    "devpulse",
    broker=_settings.redis_url,
    # Imported by name so the API can send tasks without importing task code.
    include=["app.synchronization.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Job state lives in PostgreSQL (sync_runs), so no result backend is needed.
    task_ignore_result=True,
    # Re-deliver a task if the worker dies mid-run; tasks are safe to run twice.
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=540,
    task_time_limit=600,
    broker_connection_retry_on_startup=True,
    # Fail fast when Redis is down instead of hanging a web request.
    broker_transport_options={"socket_connect_timeout": 2},
    task_publish_retry_policy={
        "max_retries": 1,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    },
    # Celery Beat (run exactly one instance) queues a check of every connection on this interval.
    beat_schedule={
        "dispatch-due-syncs": {
            "task": DISPATCH_DUE_TASK,
            "schedule": float(_settings.sync_interval_seconds),
        },
    },
)
