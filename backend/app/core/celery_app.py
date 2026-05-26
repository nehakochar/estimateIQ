"""
celery_app.py — Celery application instance and configuration.

What is Celery?
  Celery is a task queue.  Instead of making the user wait while the
  server does slow work (like parsing a 50-page PDF), we hand the work
  off to a background worker process and return immediately.

  Flow:
    FastAPI → sends task message → Redis (broker)
    Celery worker → picks up message → runs task → stores result → Redis

How Celery connects to Redis:
  - `broker`  = where task messages are sent (Redis queue)
  - `backend` = where task results are stored (Redis key-value)
  Both point to the same Redis instance here for simplicity.

The `include` list:
  Celery needs to know which Python modules contain task definitions
  so it can import them when the worker starts.  Add every new task
  module to this list.
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "estimateiq",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        # Phase 3: document parsing tasks
        "app.tasks.processing_tasks",
        # Phase 5: hierarchical chunking tasks
        "app.tasks.chunking_tasks",
        # Phase 6: semantic chunking + classification tasks
        "app.tasks.semantic_chunking_tasks",
        # Phase 8: embedding tasks
        "app.tasks.embedding_tasks",
    ],
)

celery_app.conf.update(
    # Serialization format — JSON is human-readable and safe.
    # Never use "pickle" in production (security risk).
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Keep task results in Redis for 24 hours, then auto-delete.
    # This prevents Redis from filling up with old results.
    result_expires=86_400,  # seconds = 24 hours

    # Worker settings
    # worker_prefetch_multiplier=1 means each worker fetches one task
    # at a time.  Good for long-running tasks like document parsing.
    worker_prefetch_multiplier=1,

    # Suppress the Celery 6.0 deprecation warning about broker retries.
    # Setting this explicitly opts in to the new behaviour now.
    broker_connection_retry_on_startup=True,
)
