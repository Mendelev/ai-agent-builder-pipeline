# backend/app/api/v1/plan.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from app.core.database import get_db
from app.core.observability import get_logger
from app.schemas.plan import (
    PlanGenerateRequest,
    PlanResponse,
    PlanSummary
)
from app.services.plan_service import PlanService
from app.workers.tasks.plan import generate_plan as generate_plan_task

router = APIRouter(prefix="/projects/{project_id}/plan", tags=["plan"])
logger = get_logger(__name__)

@router.post("", response_model=PlanSummary)
async def generate_plan(
    project_id: UUID,
    request: PlanGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate execution plan from requirements"""
    try:
        # Verify project exists and has requirements
        from app.models import Project, Requirement
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        req_count = db.query(Requirement).filter(
            Requirement.project_id == project_id
        ).count()
        
        if req_count == 0:
            raise HTTPException(
# backend/app/api/v1/plan.py (continued)
                status_code=400,
                detail="No requirements found. Please add requirements before generating a plan."
            )
        
        # Queue plan generation task
        task = generate_plan_task.apply_async(
            args=[str(project_id), request.model_dump()],
            queue='default'
        )
        
        logger.info(f"Queued plan generation task {task.id} for project {project_id}")
        
        # For synchronous demo, wait for task completion (in production, use async)
        try:
            result = task.get(timeout=30)
            
            if result["status"] == "completed":
                # Fetch the generated plan
                plan = PlanService.get_latest_plan(db, project_id)
                if plan:
                    return PlanSummary(
                        id=plan.id,
                        project_id=plan.project_id,
                        version=plan.version,
                        status=plan.status.value,
                        total_phases=len(plan.phases),
                        total_duration_days=plan.total_duration_days,
                        coverage_percentage=plan.coverage_percentage,
                        risk_score=plan.risk_score,
                        created_at=plan.created_at
                    )
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "Plan generation failed"))
                
        except Exception as e:
            logger.warning(f"Task execution timeout or error: {e}")
            # Return task info for async tracking
            return {
                "message": "Plan generation in progress",
                "task_id": task.id,
                "project_id": str(project_id),
                "status": "pending"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate plan")

@router.get("/latest", response_model=Optional[PlanResponse])
async def get_latest_plan(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Get the latest plan for a project"""
    try:
        plan = PlanService.get_latest_plan(db, project_id)
        
        if not plan:
            raise HTTPException(
                status_code=404,
                detail=f"No plan found for project {project_id}"
            )
        
        logger.info(f"Retrieved latest plan v{plan.version} for project {project_id}")
        return plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve plan")

@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan_by_id(
    project_id: UUID,
    plan_id: UUID,
    db: Session = Depends(get_db)
):
    """Get specific plan by ID"""
    try:
        plan = PlanService.get_plan_by_id(db, project_id, plan_id)
        
        if not plan:
            raise HTTPException(
                status_code=404,
                detail=f"Plan {plan_id} not found for project {project_id}"
            )
        
        logger.info(f"Retrieved plan {plan_id} for project {project_id}")
        return plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve plan")