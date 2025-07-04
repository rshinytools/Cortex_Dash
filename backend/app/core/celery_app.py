# ABOUTME: Celery configuration for asynchronous task processing
# ABOUTME: Handles background jobs for data pipeline, reports, and long-running operations

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "clinical_dashboard",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.clinical_modules.pipeline.tasks",
        "app.clinical_modules.data_sources.tasks",
        "app.clinical_modules.exports.tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
    task_track_started=True,
    task_time_limit=3600,  # Hard time limit of 1 hour
    task_soft_time_limit=3300,  # Soft time limit of 55 minutes
    worker_prefetch_multiplier=1,  # Disable prefetching for better task distribution
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks to prevent memory leaks
    
    # Task routing
    task_routes={
        "app.clinical_modules.pipeline.tasks.*": {"queue": "pipeline"},
        "app.clinical_modules.data_sources.tasks.*": {"queue": "data_sources"},
        "app.clinical_modules.exports.tasks.*": {"queue": "exports"},
    },
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 60 seconds
    task_max_retries=settings.MAX_PIPELINE_RETRIES,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-scheduled-pipelines": {
        "task": "app.clinical_modules.pipeline.tasks.check_scheduled_pipelines",
        "schedule": 300.0,  # Every 5 minutes
    },
    "cleanup-temp-files": {
        "task": "app.clinical_modules.pipeline.tasks.cleanup_temp_files",
        "schedule": 3600.0,  # Every hour
    },
    "generate-scheduled-reports": {
        "task": "app.clinical_modules.exports.tasks.generate_scheduled_reports",
        "schedule": 600.0,  # Every 10 minutes
    },
}