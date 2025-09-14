# backend/app/api/v1/requirements.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.core.observability import get_logger
from app.schemas.requirement import (
    RequirementBulkCreate,
    RequirementResponse,
    RefineRequest,
    FinalizeRequest,
    ExportFormat
)
from app.services.requirement_service import RequirementService
from app.workers.tasks.requirements import refine_requirements
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter(prefix="/projects/{project_id}/requirements", tags=["requirements"])
logger = get_logger(__name__)

@router.post("", response_model=List[RequirementResponse])
async def create_requirements(
    project_id: UUID,
    payload: RequirementBulkCreate,
    db: Session = Depends(get_db)
):
    """Bulk create or update requirements (max 100MB payload)"""
    try:
        requirements = RequirementService.create_bulk(
            db, project_id, payload.requirements
        )
        return requirements
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create requirements: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("", response_model=List[RequirementResponse])
async def list_requirements(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """List all requirements for a project"""
    try:
        requirements = RequirementService.list_requirements(db, project_id)
        return requirements
    except Exception as e:
        logger.error(f"Failed to list requirements: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/refine")
async def refine_requirements(
    project_id: UUID,
    request: RefineRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Queue refinement job for requirements"""
    try:
        # Verify project exists
        from app.models import Project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Queue Celery task
        task = refine_requirements.delay(str(project_id))
        
        return {
            "message": "Refinement job queued",
            "task_id": task.id,
            "project_id": str(project_id)
        }
    except Exception as e:
        logger.error(f"Failed to queue refinement: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/finalize")
async def finalize_requirements(
    project_id: UUID,
    request: FinalizeRequest,
    db: Session = Depends(get_db)
):
    """Mark project as REQS_READY"""
    try:
        success = RequirementService.finalize_requirements(
            db, project_id, request.force
        )
        return {
            "message": "Project marked as REQS_READY",
            "project_id": str(project_id),
            "success": success
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to finalize requirements: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/export")
async def export_requirements(
    project_id: UUID,
    format: str = Query("json", regex="^(json|md)$"),
    db: Session = Depends(get_db)
):
    """Export requirements in JSON or Markdown format"""
    try:
        requirements = RequirementService.list_requirements(db, project_id)
        
        if not requirements:
            raise HTTPException(status_code=404, detail="No requirements found")
        
        if format == "json":
            content = RequirementService.export_json(requirements)
            return JSONResponse(content=content)
        else:  # markdown
            content = RequirementService.export_markdown(requirements)
            return PlainTextResponse(content=content, media_type="text/markdown")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export requirements: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")