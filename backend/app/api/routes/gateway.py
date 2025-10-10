from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.models.project import Project
from app.schemas.gateway import (
    RequirementsGatewayRequest,
    RequirementsGatewayResponse,
    RequirementsGatewayAuditRead
)
from app.services.gateway_service import GatewayService
from app.core.logging_config import get_logger

router = APIRouter(prefix="/requirements", tags=["requirements-gateway"])
logger = get_logger(__name__)


@router.post(
    "/{project_id}/gateway", 
    response_model=RequirementsGatewayResponse,
    status_code=status.HTTP_200_OK,
    summary="Requirements Gateway",
    description="Controls project state transitions based on user decisions after requirements refinement"
)
def requirements_gateway(
    project_id: UUID,
    request: RequirementsGatewayRequest,
    db: Session = Depends(get_db)
):
    """
    Process requirements gateway transition based on user decision.
    
    Valid transitions from REQS_REFINING state:
    - finalizar → REQS_READY (finalize requirements)
    - planejar → REQS_READY (proceed to planning) 
    - validar_codigo → CODE_VALIDATION_REQUESTED (request code validation)
    
    Args:
        project_id: UUID of the project to transition
        request: Gateway request with action and optional tracking IDs
        db: Database session
        
    Returns:
        Gateway response with transition details and audit reference
        
    Raises:
        HTTPException 404: Project not found
        HTTPException 400: Invalid state transition or missing requirements
    """
    logger.info(
        "Requirements gateway request received",
        extra={
            "project_id": str(project_id),
            "action": request.action,
            "request_id": str(request.request_id),
            "correlation_id": str(request.correlation_id) if request.correlation_id else None
        }
    )
    
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        logger.warning(
            "Project not found",
            extra={"project_id": str(project_id)}
        )
        raise HTTPException(
            status_code=404, 
            detail="Project not found"
        )
    
    # Execute transition via service
    try:
        response = GatewayService.execute_transition(db, project, request)
        
        logger.info(
            "Requirements gateway transition successful",
            extra={
                "project_id": str(project_id),
                "from_state": response.from_state,
                "to_state": response.to_state,
                "action": request.action,
                "audit_id": str(response.audit_ref.correlation_id)
            }
        )
        
        return response
        
    except HTTPException:
        # Re-raise FastAPI HTTP exceptions from service layer
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in requirements gateway",
            extra={
                "project_id": str(project_id),
                "action": request.action,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error during gateway transition"
        )


@router.get(
    "/{project_id}/gateway/history",
    response_model=List[RequirementsGatewayAuditRead],
    summary="Gateway History",
    description="Get all gateway transition history for a project"
)
def get_gateway_history(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all gateway transition history for a project.
    
    Args:
        project_id: UUID of the project
        db: Database session
        
    Returns:
        List of gateway audit records for the project
        
    Raises:
        HTTPException 404: Project not found
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    
    # Get gateway history
    history = GatewayService.get_project_gateway_history(db, project_id)
    
    logger.info(
        "Gateway history retrieved",
        extra={
            "project_id": str(project_id),
            "history_count": len(history)
        }
    )
    
    return history