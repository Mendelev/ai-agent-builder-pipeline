# backend/app/workers/tasks/requirements.py
from celery import Task
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.observability import get_logger
from app.models import Project, Requirement, RequirementQuestion
from uuid import UUID
import time
import random

logger = get_logger(__name__)

class RefineTask(Task):
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
    base=RefineTask,
    name="reqs.refine",
    max_retries=3,
    default_retry_delay=60
)
def refine_requirements(self, project_id: str):
    """
    Refine requirements by analyzing them and generating questions or marking as coherent.
    This is a placeholder implementation - replace with actual LangGraph logic.
    """
    start_time = time.time()
    
    try:
        project_uuid = UUID(project_id)
        
        # Get project and requirements
        project = self.db.query(Project).filter(Project.id == project_uuid).first()
        if not project:
            logger.error(f"Project {project_id} not found")
            return {"error": f"Project {project_id} not found"}
        
        requirements = self.db.query(Requirement).filter(
            Requirement.project_id == project_uuid
        ).all()
        
        if not requirements:
            logger.info(f"No requirements found for project {project_id}")
            return {"message": "No requirements to refine"}
        
        refined_count = 0
        questions_generated = 0
        
        for req in requirements:
            if req.is_coherent:
                continue
            
            # Placeholder logic - replace with actual LangGraph agent
            # Simulate analysis time
            time.sleep(random.uniform(0.1, 0.3))
            
            # Simple heuristic: requirements with dependencies and acceptance criteria are coherent
            if req.acceptance_criteria and len(req.acceptance_criteria) >= 2:
                if req.priority in ["high", "critical"] or len(req.dependencies) == 0:
                    req.is_coherent = True
                    refined_count += 1
                    logger.info(f"Marked requirement {req.key} as coherent")
            else:
                # Generate clarifying questions
                if not req.acceptance_criteria:
                    question = RequirementQuestion(
                        requirement_id=req.id,
                        question=f"What are the specific acceptance criteria for '{req.title}'?",
                        is_resolved=False
                    )
                    self.db.add(question)
                    questions_generated += 1
                
                if req.priority in ["high", "critical"] and not req.dependencies:
                    question = RequirementQuestion(
                        requirement_id=req.id,
                        question=f"Does the {req.priority} priority requirement '{req.key}' have any dependencies?",
                        is_resolved=False
                    )
                    self.db.add(question)
                    questions_generated += 1
        
        self.db.commit()
        
        duration = time.time() - start_time
        
        result = {
            "project_id": project_id,
            "total_requirements": len(requirements),
            "refined_count": refined_count,
            "questions_generated": questions_generated,
            "duration_seconds": duration
        }
        
        logger.info(f"Refinement completed", extra=result)
        
        # Emit metric (placeholder - integrate with actual metrics system)
        # metrics.histogram("agent_duration_seconds", duration, tags={"task": "reqs.refine"})
        
        return result
        
    except Exception as e:
        logger.error(f"Error refining requirements: {str(e)}")
        self.retry(countdown=60, exc=e)