from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "estimateiq",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        # register task modules here as you create them
        # e.g. "app.tasks.estimate_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
