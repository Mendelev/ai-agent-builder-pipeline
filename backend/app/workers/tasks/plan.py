# backend/app/workers/tasks/plan.py
from celery import Task
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.observability import get_logger, agent_duration
from app.services.plan_service import PlanService
from app.schemas.plan import PlanGenerateRequest
from uuid import UUID
import time
from typing import Dict, Any

logger = get_logger(__name__)

class PlanTask(Task):
    """Base task with database session management"""
    
    def __init__(self):
        self.db = None
    
    def before_start(self, task_id, args, kwargs):
        """Initialize database session"""
        self.db = SessionLocal()
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Cleanup database session"""
        if self.db:
            self.db.close()

@celery_app.task(
    bind=True,
    base=PlanTask,
    name="plan.generate",
    max_retries=3,
    default_retry_delay=60
)
def generate_plan(self, project_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate execution plan from requirements
    """
    start_time = time.time()
    
    try:
        project_uuid = UUID(project_id)
        logger.info(f"Starting plan generation for project {project_id}")
        
        # Parse options
        plan_request = PlanGenerateRequest(**options)
        
        # Generate plan
        plan = PlanService.generate_plan(
            self.db,
            project_uuid,
            plan_request
        )
        
        duration = time.time() - start_time
        
        # Record metric
        agent_duration.labels(task='plan.generate').observe(duration)
        
        result = {
            "project_id": project_id,
            "plan_id": str(plan.id),
            "status": "completed",
            "version": plan.version,
            "total_phases": len(plan.phases),
            "total_duration_days": plan.total_duration_days,
            "coverage_percentage": plan.coverage_percentage,
            "risk_score": plan.risk_score,
            "duration_seconds": round(duration, 2)
        }
        
        logger.info(f"Plan generation completed for project {project_id}", extra=result)
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        agent_duration.labels(task='plan.generate').observe(duration)
        
        logger.error(f"Error generating plan for project {project_id}: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)
        
        return {
            "project_id": project_id,
            "status": "failed",
            "error": str(e),
            "duration_seconds": round(duration, 2)
        }