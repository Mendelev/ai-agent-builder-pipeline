# backend/app/workers/beat_schedule.py (continued)
from celery.schedules import crontab

from app.workers.celery_app import celery_app

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    "cleanup-workdirs": {
        "task": "maintenance.cleanup_workdirs",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        "options": {"queue": "maintenance"},
    },
    "cleanup-dedup-keys": {
        "task": "maintenance.cleanup_expired_dedup",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
        "options": {"queue": "maintenance"},
    },
    "process-domain-events": {
        "task": "maintenance.process_domain_events",
        "schedule": 60.0,  # Every minute
        "options": {"queue": "maintenance"},
    },
    "retry-failed-tasks": {
        "task": "maintenance.retry_failed_tasks",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
        "options": {"queue": "maintenance"},
    },
    "audit-log-retention": {
        "task": "maintenance.enforce_retention",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        "options": {"queue": "maintenance"},
    },
}

# Configure retry backoff
celery_app.conf.task_default_retry_delay = 60  # 1 minute
celery_app.conf.task_max_retries = 3
celery_app.conf.task_retry_backoff = True
celery_app.conf.task_retry_backoff_max = 600  # 10 minutes max
celery_app.conf.task_retry_jitter = True
