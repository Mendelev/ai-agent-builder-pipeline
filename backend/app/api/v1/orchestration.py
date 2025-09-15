# backend/app/api/v1/orchestration.py
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.observability import correlation_id_var, get_logger
from app.core.redis_client import redis_client
from app.models.orchestration import AgentType, EventType
from app.schemas.orchestration import AuditLogPage, ProjectStatusResponse, RetryRequest, RetryResponse
from app.services.orchestration_service import OrchestrationService

router = APIRouter(tags=["orchestration"])
logger = get_logger(__name__)


@router.get("/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project_status(project_id: UUID, db: Session = Depends(get_db)):
    """Get project status with recent events"""
    try:
        status = OrchestrationService.get_project_status(db, project_id)

        logger.info(f"Retrieved status for project {project_id}")
        return ProjectStatusResponse(**status)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get project status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve project status")


@router.get("/projects/{project_id}/audit", response_model=AuditLogPage)
async def get_audit_logs(
    project_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=100),
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get paginated audit logs for a project"""
    try:
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

        result = OrchestrationService.get_audit_logs(db, project_id, page, page_size, event_type_enum)

        logger.info(f"Retrieved audit logs for project {project_id}, page {page}")
        return AuditLogPage(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")


@router.post("/projects/{project_id}/retry/{agent}", response_model=RetryResponse)
async def retry_agent_execution(project_id: UUID, agent: str, request: RetryRequest, db: Session = Depends(get_db)):
    """Retry an agent execution for a project"""
    try:
        # Validate agent type
        try:
            agent_type = AgentType(agent.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent}")

        # Get correlation ID
        correlation_id = correlation_id_var.get()

        # Attempt retry
        result = OrchestrationService.retry_agent(
            db, redis_client, project_id, agent_type, request.force, request.metadata
        )

        logger.info(
            f"Retry requested for agent {agent} on project {project_id}",
            extra={"project_id": str(project_id), "agent": agent, "correlation_id": correlation_id, "result": result},
        )

        return RetryResponse(
            task_id=result.get("task_id", ""),
            agent=agent,
            status=result.get("status", "queued"),
            message=f"Agent {agent} retry {'queued' if result.get('status') != 'cached' else 'using cached result'}",
        )

    except HTTPException:
        raise  # Re-raise HTTPException without catching it in generic Exception handler
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to retry agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry agent execution")
