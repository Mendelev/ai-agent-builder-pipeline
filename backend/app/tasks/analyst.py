"""
Analyst Tasks - Requirement Refinement (R3)
Celery tasks for asynchronous requirement analysis and refinement
"""
from celery import Task
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import logging

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.project import Project, Requirement
from app.models.qa_session import QASession
from app.services.analyst_service import AnalystService
from app.schemas.qa_session import Question, Answer, QualityFlags

logger = logging.getLogger(__name__)


class IdempotentTask(Task):
    """Base task class with idempotency support"""
    
    def __call__(self, *args, **kwargs):
        """Check idempotency before executing"""
        request_id = kwargs.get('request_id')
        
        if request_id:
            db = SessionLocal()
            try:
                # Check if this request_id was already processed
                existing = db.query(QASession).filter(
                    QASession.request_id == request_id
                ).first()
                
                if existing:
                    logger.info(f"Idempotent request detected: {request_id}. Returning cached result.")
                    return {
                        "status": "DUPLICATE",
                        "message": "Request already processed",
                        "qa_session_id": str(existing.id),
                        "cached": True
                    }
            finally:
                db.close()
        
        # Execute the task
        return super().__call__(*args, **kwargs)


@celery_app.task(
    name="agents.analyst.refine",
    bind=True,
    base=IdempotentTask,
    queue="q_analyst",
    soft_time_limit=120,  # 2 minutes soft limit
    time_limit=150,  # 2.5 minutes hard limit
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 5},
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def refine_requirements(
    self,
    project_id: str,
    max_rounds: int = 3,
    request_id: Optional[str] = None,
    answers: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Refine project requirements through Q&A.
    
    Args:
        project_id: UUID of the project
        max_rounds: Maximum number of refinement rounds
        request_id: Idempotency key (UUID)
        answers: Optional answers to previous questions
        
    Returns:
        {
            "status": "REQS_REFINING|REQS_READY|BLOCKED",
            "open_questions": [...],
            "refined_requirements_version": <int>?,
            "audit_ref": {...},
            "current_round": <int>,
            "max_rounds": <int>,
            "quality_flags": {...}
        }
    """
    db = SessionLocal()
    analyst = AnalystService()
    
    try:
        logger.info(f"Starting requirement refinement for project {project_id}, request_id={request_id}")
        
        # Validate project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Get current round number
        current_round = db.query(QASession).filter(
            QASession.project_id == project_id
        ).count() + 1
        
        # Check max_rounds guard-rail
        if current_round > max_rounds:
            logger.warning(f"Max rounds ({max_rounds}) exceeded for project {project_id}")
            project.status = "BLOCKED"
            db.commit()
            
            return {
                "status": "BLOCKED",
                "open_questions": None,
                "refined_requirements_version": None,
                "audit_ref": {
                    "project_id": str(project.id),
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": "max_rounds_exceeded",
                    "task_id": self.request.id
                },
                "current_round": current_round - 1,
                "max_rounds": max_rounds,
                "quality_flags": None
            }
        
        # Get project requirements
        requirements = db.query(Requirement).filter(
            Requirement.project_id == project_id
        ).all()
        
        if not requirements:
            raise ValueError(f"No requirements found for project {project_id}")
        
        # If answers provided, refine requirements first
        requirements_updated = False
        if answers:
            logger.info(f"Processing {len(answers)} answers for project {project_id}")
            refinement_result = analyst.refine_requirements_with_answers(requirements, answers)
            
            if refinement_result["total_changes"] > 0:
                # Increment requirements version
                project.requirements_version += 1
                requirements_updated = True
                logger.info(f"Requirements updated to version {project.requirements_version}")
        
        # Analyze requirements and generate questions
        questions, quality_flags = analyst.analyze_requirements(requirements, max_questions=10)
        
        # Create QA session record
        qa_session = QASession(
            id=uuid.uuid4(),
            project_id=project_id,
            request_id=request_id or str(uuid.uuid4()),
            round=current_round,
            questions=[q.model_dump() for q in questions],
            answers=[a for a in answers] if answers else None,
            quality_flags=quality_flags.model_dump() if quality_flags else None
        )
        db.add(qa_session)
        
        # Determine project status
        if len(questions) == 0:
            # No more questions - requirements are ready
            project.status = "REQS_READY"
            refined_version = project.requirements_version
            open_questions = None
        else:
            # Still have questions - continue refining
            project.status = "REQS_REFINING"
            refined_version = project.requirements_version if requirements_updated else None
            open_questions = [q.model_dump() for q in questions]
        
        # Commit changes
        db.commit()
        db.refresh(qa_session)
        
        # Build audit reference
        audit_ref = {
            "project_id": str(project.id),
            "qa_session_id": str(qa_session.id),
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": self.request.id,
            "round": current_round,
            "questions_generated": len(questions),
            "answers_processed": len(answers) if answers else 0,
            "requirements_updated": requirements_updated
        }
        
        logger.info(f"Refinement completed for project {project_id}. Status: {project.status}")
        
        return {
            "status": project.status,
            "open_questions": open_questions,
            "refined_requirements_version": refined_version,
            "audit_ref": audit_ref,
            "current_round": current_round,
            "max_rounds": max_rounds,
            "quality_flags": quality_flags.model_dump() if quality_flags else None
        }
        
    except Exception as e:
        logger.error(f"Error in refine_requirements for project {project_id}: {str(e)}", exc_info=True)
        db.rollback()
        
        # Update project status to BLOCKED on error
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.status = "BLOCKED"
                db.commit()
        except:
            pass
        
        raise
    
    finally:
        db.close()


@celery_app.task(
    name="agents.analyst.get_qa_sessions",
    bind=True,
    queue="q_analyst",
    soft_time_limit=30,
)
def get_qa_sessions(self, project_id: str) -> Dict[str, Any]:
    """
    Get all Q&A sessions for a project.
    
    Args:
        project_id: UUID of the project
        
    Returns:
        {
            "project_id": <uuid>,
            "sessions": [...],
            "total": <int>
        }
    """
    db = SessionLocal()
    
    try:
        sessions = db.query(QASession).filter(
            QASession.project_id == project_id
        ).order_by(QASession.round.asc()).all()
        
        return {
            "project_id": project_id,
            "sessions": [
                {
                    "id": str(s.id),
                    "round": s.round,
                    "questions": s.questions,
                    "answers": s.answers,
                    "quality_flags": s.quality_flags,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat()
                }
                for s in sessions
            ],
            "total": len(sessions)
        }
    
    finally:
        db.close()
