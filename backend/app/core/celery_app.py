from celery import Celery
from celery.signals import worker_process_init
from app.core.config import settings

celery_app = Celery(
    "estimateiq",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.processing_tasks",    # parse document → save parsed_content
        "app.tasks.extraction_tasks",    # LLM extraction → extracted_requirements
        "app.tasks.estimation_tasks",    # LLM estimation → requirement_estimates
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=86_400,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)


@worker_process_init.connect
def init_worker_logging(**kwargs):
    """Set up file logging in every forked Celery worker process."""
    from app.core.logging_config import setup_logging
    setup_logging()

