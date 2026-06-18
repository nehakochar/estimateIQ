from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "estimateiq",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.processing_tasks",    # parse document → save parsed_content
        "app.tasks.extraction_tasks",    # LLM extraction → extracted_requirements
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
