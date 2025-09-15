# backend/app/workers/tasks/requirements.py
import random
import time
from typing import Any, Dict
from uuid import UUID

from celery import Task

from app.core.database import SessionLocal
from app.core.observability import agent_duration, get_logger
from app.models import Project, Requirement, RequirementIteration, RequirementQuestion
from app.workers.celery_app import celery_app

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


@celery_app.task(bind=True, base=RefineTask, name="reqs.refine", max_retries=3, default_retry_delay=60)
def refine_requirements(self, project_id: str) -> Dict[str, Any]:
    """
    Refine requirements by analyzing them and generating questions or marking as coherent.
    """
    start_time = time.time()

    try:
        project_uuid = UUID(project_id)
        logger.info(f"Starting refinement for project {project_id}")

        # Get project and requirements
        project = self.db.query(Project).filter(Project.id == project_uuid).first()
        if not project:
            logger.error(f"Project {project_id} not found")
            return {"error": f"Project {project_id} not found", "status": "failed"}

        requirements = self.db.query(Requirement).filter(Requirement.project_id == project_uuid).all()

        if not requirements:
            logger.info(f"No requirements found for project {project_id}")
            return {"message": "No requirements to refine", "status": "completed"}

        refined_count = 0
        questions_generated = 0
        already_coherent = 0

        # Analyze each requirement
        for req in requirements:
            if req.is_coherent:
                already_coherent += 1
                continue

            # Simulate LangGraph agent processing
            time.sleep(random.uniform(0.05, 0.15))

            questions_needed = []

            # Check acceptance criteria
            if not req.acceptance_criteria:
                questions_needed.append(
                    f"What are the specific acceptance criteria for '{req.title}'? Please provide measurable success criteria."
                )
            elif len(req.acceptance_criteria) < 2 and req.priority in ["high", "critical"]:
                questions_needed.append(
                    f"The {req.priority} priority requirement '{req.key}' has only {len(req.acceptance_criteria)} acceptance criterion. Can you provide additional criteria?"
                )

            # Check dependencies for high priority items
            if req.priority in ["high", "critical"] and len(req.dependencies) == 0:
                # Check if it really needs dependencies
                other_reqs = [r for r in requirements if r.key != req.key]
                if other_reqs:
                    questions_needed.append(
                        f"Does the {req.priority} priority requirement '{req.key}' depend on any other requirements? Available: {', '.join([r.key for r in other_reqs[:5]])}"
                    )

            # Check description completeness
            if not req.description or len(req.description) < 20:
                questions_needed.append(
                    f"The requirement '{req.key}' lacks a detailed description. Can you elaborate on the implementation details?"
                )

            if questions_needed:
                # Generate questions
                for question_text in questions_needed:
                    existing_q = (
                        self.db.query(RequirementQuestion)
                        .filter(
                            RequirementQuestion.requirement_id == req.id, RequirementQuestion.question == question_text
                        )
                        .first()
                    )

                    if not existing_q:
                        question = RequirementQuestion(requirement_id=req.id, question=question_text, is_resolved=False)
                        self.db.add(question)
                        questions_generated += 1
            else:
                # backend/app/workers/tasks/requirements.py (continued)
                # Mark as coherent if all checks pass
                req.is_coherent = True
                refined_count += 1

                # Create iteration record
                last_iteration = (
                    self.db.query(RequirementIteration)
                    .filter(RequirementIteration.requirement_id == req.id)
                    .order_by(RequirementIteration.version.desc())
                    .first()
                )

                new_version = (last_iteration.version + 1) if last_iteration else 1

                iteration = RequirementIteration(
                    requirement_id=req.id,
                    version=new_version,
                    changes={"action": "marked_coherent", "by": "refine_task"},
                    created_by="system",
                )
                self.db.add(iteration)

                logger.info(f"Marked requirement {req.key} as coherent")

        self.db.commit()

        duration = time.time() - start_time

        # Record metric
        agent_duration.labels(task="reqs.refine").observe(duration)

        result = {
            "project_id": project_id,
            "status": "completed",
            "total_requirements": len(requirements),
            "already_coherent": already_coherent,
            "refined_count": refined_count,
            "questions_generated": questions_generated,
            "duration_seconds": round(duration, 2),
        }

        logger.info(f"Refinement completed for project {project_id}", extra=result)
        return result

    except Exception as e:
        duration = time.time() - start_time
        agent_duration.labels(task="reqs.refine").observe(duration)

        logger.error(f"Error refining requirements for project {project_id}: {str(e)}")

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        return {"project_id": project_id, "status": "failed", "error": str(e), "duration_seconds": round(duration, 2)}
