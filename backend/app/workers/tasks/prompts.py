# backend/app/workers/tasks/prompts.py
from celery import Task
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.observability import get_logger, agent_duration
from app.services.prompt_service import PromptService
from app.schemas.prompt import PromptGenerateRequest
from uuid import UUID
import time
from typing import Dict, Any

logger = get_logger(__name__)

class PromptTask(Task):
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
    base=PromptTask,
    name="prompts.generate",
    max_retries=3,
    default_retry_delay=60
)
def generate_prompts(
    self,
    project_id: str,
    plan_id: Optional[str],
    include_code: bool
) -> Dict[str, Any]:
    """
    Generate prompt bundle for a project plan
    """
    start_time = time.time()
    
    try:
        project_uuid = UUID(project_id)
        plan_uuid = UUID(plan_id) if plan_id else None
        
        logger.info(f"Starting prompt generation for project {project_id}")
        
        # Create request
        request = PromptGenerateRequest(
            include_code=include_code,
            plan_id=plan_uuid
        )
        
        # Generate prompts
        bundle = PromptService.generate_prompts(
            self.db,
            project_uuid,
            request
        )
        
        duration = time.time() - start_time
        
        # Record metric
        agent_duration.labels(task='prompts.generate').observe(duration)
        
        result = {
            "project_id": project_id,
            "bundle_id": str(bundle.id),
            "status": "completed",
            "version": bundle.version,
            "total_prompts": bundle.total_prompts,
            "include_code": bundle.include_code,
            "duration_seconds": round(duration, 2)
        }
        
        logger.info(f"Prompt generation completed for project {project_id}", extra=result)
        return result
        
    except Exception as e:
        duration = time.time() - start_time
# backend/app/workers/tasks/prompts.py (continued)
        agent_duration.labels(task='prompts.generate').observe(duration)
        
        logger.error(f"Error generating prompts for project {project_id}: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)
        
        return {
            "project_id": project_id,
            "status": "failed",
            "error": str(e),
            "duration_seconds": round(duration, 2)
        }