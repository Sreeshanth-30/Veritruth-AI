# ──────────────────────────────────────────────────────────────
# VeriTruth AI — Celery Application Configuration
# ──────────────────────────────────────────────────────────────
from __future__ import annotations

from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "veritruth",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    # Serialisation
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_track_started=True,
    task_time_limit=600,        # 10 min hard limit
    task_soft_time_limit=540,   # 9 min soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Result expiry
    result_expires=3600,
    # Retry
    task_default_retry_delay=30,
    task_max_retries=3,
    # Queues
    task_default_queue="analysis",
    task_queues={
        "analysis": {"exchange": "analysis", "routing_key": "analysis"},
        "priority": {"exchange": "priority", "routing_key": "priority"},
    },
    task_routes={
        "app.worker.tasks.run_analysis_pipeline": {"queue": "analysis"},
        "app.worker.tasks.run_url_analysis_pipeline": {"queue": "analysis"},
        "app.worker.tasks.run_file_analysis_pipeline": {"queue": "analysis"},
    },
    # Beat schedule (periodic tasks)
    beat_schedule={
        "cleanup-stale-analyses": {
            "task": "app.worker.tasks.cleanup_stale_analyses",
            "schedule": 300.0,  # every 5 min
        },
        "refresh-source-cache": {
            "task": "app.worker.tasks.refresh_source_cache",
            "schedule": 3600.0,  # every hour
        },
    },
)
