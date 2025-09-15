# backend/app/api/v1/prompts.py
from typing import Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.observability import get_logger
from app.schemas.prompt import PromptBundleResponse, PromptBundleSummary, PromptGenerateRequest, TaskPendingResponse
from app.services.prompt_service import PromptService
from app.workers.tasks.prompts import generate_prompts as generate_prompts_task

router = APIRouter(prefix="/projects/{project_id}/prompts", tags=["prompts"])
logger = get_logger(__name__)


@router.post("/generate", response_model=Union[PromptBundleSummary, TaskPendingResponse])
async def generate_prompts(project_id: UUID, request: PromptGenerateRequest, db: Session = Depends(get_db)):
    """Generate prompt bundle from plan"""
    try:
        # Verify project exists
        from app.models import Plan, Project

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Verify plan exists
        if request.plan_id:
            plan = db.query(Plan).filter(Plan.id == request.plan_id, Plan.project_id == project_id).first()
            if not plan:
                raise HTTPException(status_code=404, detail=f"Plan {request.plan_id} not found")
        else:
            plan = db.query(Plan).filter(Plan.project_id == project_id).order_by(Plan.version.desc()).first()
            if not plan:
                raise HTTPException(status_code=400, detail="No plan found for project")

        # Queue prompt generation task
        task = generate_prompts_task.apply_async(
            args=[str(project_id), str(request.plan_id) if request.plan_id else str(plan.id), request.include_code],
            queue="default",
        )

        logger.info(f"Queued prompt generation task {task.id} for project {project_id}")

        # For synchronous demo, wait for task completion
        try:
            result = task.get(timeout=30)

            if result["status"] == "completed":
                # Fetch the generated bundle
                bundle = PromptService.get_latest_bundle(db, project_id)
                if bundle:
                    return PromptBundleSummary(
                        id=bundle.id,
                        project_id=bundle.project_id,
                        plan_id=bundle.plan_id,
                        version=bundle.version,
                        total_prompts=bundle.total_prompts,
                        include_code=bundle.include_code,
                        created_at=bundle.created_at,
                    )
                else:
                    raise HTTPException(status_code=500, detail="Prompts were generated but could not be retrieved")
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "Prompt generation failed"))

        except Exception as e:
            logger.warning(f"Task execution timeout or error: {e}")
            # Return task info for async tracking
            return TaskPendingResponse(
                message="Prompt generation in progress",
                task_id=str(task.id),
                project_id=str(project_id),
                status="pending",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate prompts: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate prompts")


@router.get("/latest", response_model=Optional[PromptBundleResponse])
async def get_latest_prompts(project_id: UUID, db: Session = Depends(get_db)):
    """Get the latest prompt bundle for a project"""
    try:
        bundle = PromptService.get_latest_bundle(db, project_id)

        if not bundle:
            raise HTTPException(status_code=404, detail=f"No prompt bundle found for project {project_id}")

        logger.info(f"Retrieved latest prompt bundle v{bundle.version} for project {project_id}")
        return bundle

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest prompts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve prompts")


@router.get("/bundles/{bundle_id}/download")
async def download_prompt_bundle(project_id: UUID, bundle_id: UUID, db: Session = Depends(get_db)):
    """Download prompt bundle as ZIP file"""
    try:
        # Verify bundle belongs to project
        from app.models import PromptBundle

        bundle = (
            db.query(PromptBundle).filter(PromptBundle.id == bundle_id, PromptBundle.project_id == project_id).first()
        )

        if not bundle:
            raise HTTPException(status_code=404, detail=f"Bundle {bundle_id} not found for project {project_id}")

        # Create ZIP file
        zip_content = PromptService.create_bundle_zip(db, bundle_id)

        # Return ZIP file
        filename = f"prompts_{project_id}_{bundle.version}.zip"

        logger.info(f"Downloading prompt bundle {bundle_id} for project {project_id}")

        return Response(
            content=zip_content,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download bundle: {e}")
        raise HTTPException(status_code=500, detail="Failed to download bundle")
