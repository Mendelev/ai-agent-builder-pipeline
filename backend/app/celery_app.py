"""
Celery application configuration
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "ai_agent_pipeline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.analyst",  # R3: Requirement refinement tasks
        "app.tasks.git_clone",  # C1: Git repository clone tasks
        # Future: "app.tasks.code_validator",  # C3: Code validation tasks
        # Future: "app.tasks.planner",  # P2: Planning tasks
        # Future: "app.tasks.prompt_generator",  # PR4: Prompt generation tasks
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # Hard limit: 5 minutes
    task_soft_time_limit=240,  # Soft limit: 4 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_default_queue="default",
    task_routes={
        "app.tasks.analyst.*": {"queue": "q_analyst"},
        "app.tasks.git_clone.*": {"queue": "celery"},
        # Future routes:
        # "app.tasks.code_validator.*": {"queue": "q_code_validator"},
        # "app.tasks.planner.*": {"queue": "q_planner"},
        # "app.tasks.prompt_generator.*": {"queue": "q_prompts"},
    },
    # Queue-specific concurrency (can be overridden at worker start)
    worker_concurrency=4,
)

# Optional: Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {}
