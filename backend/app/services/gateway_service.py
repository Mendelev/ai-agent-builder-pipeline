from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from app.models.project import Project, RequirementsGatewayAudit, Requirement
from app.schemas.gateway import (
    RequirementsGatewayRequest, 
    RequirementsGatewayResponse, 
    AuditReference,
    GatewayActionEnum
)
from app.core.logging_config import get_logger
from fastapi import HTTPException

logger = get_logger(__name__)


class GatewayService:
    """Service for handling requirements gateway state transitions"""
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        "REQS_REFINING": {
            "finalizar": "REQS_READY",
            "planejar": "REQS_READY", 
            "validar_codigo": "CODE_VALIDATION_REQUESTED"
        }
    }
    
    # Action to reason mapping
    ACTION_REASONS = {
        "finalizar": "User chose to finalize requirements",
        "planejar": "User chose to proceed to planning",
        "validar_codigo": "User requested code validation"
    }

    @classmethod
    def validate_project_state(cls, project: Project, action: str) -> None:
        """
        Validate that the project can transition via gateway with the given action
        
        Args:
            project: The project to validate
            action: The requested action
            
        Raises:
            HTTPException: If transition is invalid
        """
        current_state = project.status
        
        # Check if current state allows gateway transitions
        if current_state not in cls.VALID_TRANSITIONS:
            raise HTTPException(
                status_code=400,
                detail={
                    "detail": f"Invalid state transition: project in {current_state} state cannot transition via gateway",
                    "error_code": "INVALID_STATE_TRANSITION",
                    "current_state": current_state,
                    "requested_action": action
                }
            )
        
        # Check if the specific action is valid for current state
        if action not in cls.VALID_TRANSITIONS[current_state]:
            valid_actions = list(cls.VALID_TRANSITIONS[current_state].keys())
            raise HTTPException(
                status_code=400,
                detail={
                    "detail": f"Invalid action '{action}' for project in {current_state} state. Valid actions: {valid_actions}",
                    "error_code": "INVALID_ACTION_FOR_STATE",
                    "current_state": current_state,
                    "requested_action": action
                }
            )

    @classmethod
    def validate_project_requirements(cls, project: Project) -> None:
        """
        Validate that project has at least one requirement
        
        Args:
            project: The project to validate
            
        Raises:
            HTTPException: If project has no requirements
        """
        if not project.requirements or len(project.requirements) == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "detail": "Project must have at least one requirement to proceed through gateway",
                    "error_code": "NO_REQUIREMENTS",
                    "current_state": project.status
                }
            )

    @classmethod
    def check_idempotency(cls, db: Session, request_id: UUID) -> Optional[RequirementsGatewayAudit]:
        """
        Check if this request has already been processed (idempotency check)
        
        Args:
            db: Database session
            request_id: The request ID to check
            
        Returns:
            Existing audit record if found, None otherwise
        """
        return db.query(RequirementsGatewayAudit).filter(
            RequirementsGatewayAudit.request_id == request_id
        ).first()

    @classmethod
    def execute_transition(
        cls, 
        db: Session, 
        project: Project, 
        request: RequirementsGatewayRequest
    ) -> RequirementsGatewayResponse:
        """
        Execute the state transition with full validation and audit trail
        
        Args:
            db: Database session
            project: The project to transition
            request: The gateway request
            
        Returns:
            Gateway response with transition details and audit reference
        """
        action = request.action
        correlation_id = request.correlation_id or uuid4()
        request_id = request.request_id
        
        logger.info(
            "Processing gateway transition",
            extra={
                "project_id": str(project.id),
                "current_state": project.status,
                "action": action,
                "correlation_id": str(correlation_id),
                "request_id": str(request_id)
            }
        )
        
        # Check idempotency first
        existing_audit = cls.check_idempotency(db, request_id)
        if existing_audit:
            logger.info(
                "Request already processed, returning cached response",
                extra={
                    "project_id": str(project.id),
                    "request_id": str(request_id),
                    "audit_id": str(existing_audit.id)
                }
            )
            
            # Return response based on existing audit
            return RequirementsGatewayResponse(
                from_state=existing_audit.from_state,
                to_state=existing_audit.to_state,
                reason=cls.ACTION_REASONS[existing_audit.action],
                audit_ref=AuditReference(
                    correlation_id=existing_audit.correlation_id,
                    request_id=existing_audit.request_id,
                    project_id=existing_audit.project_id,
                    timestamp=existing_audit.created_at,
                    action=existing_audit.action,
                    user_id=existing_audit.user_id
                )
            )
        
        # Validate project state and requirements
        cls.validate_project_state(project, action)
        cls.validate_project_requirements(project)
        
        # Get target state
        current_state = project.status
        target_state = cls.VALID_TRANSITIONS[current_state][action]
        
        # Execute the transition
        project.status = target_state
        
        # Create audit record
        audit_record = RequirementsGatewayAudit(
            project_id=project.id,
            correlation_id=correlation_id,
            request_id=request_id,
            action=action,
            from_state=current_state,
            to_state=target_state,
            user_id=None  # TODO: Extract from authentication context when available
        )
        
        db.add(audit_record)
        db.commit()
        db.refresh(project)
        db.refresh(audit_record)
        
        logger.info(
            "Gateway transition completed successfully",
            extra={
                "project_id": str(project.id),
                "from_state": current_state,
                "to_state": target_state,
                "action": action,
                "audit_id": str(audit_record.id)
            }
        )
        
        # Return response
        return RequirementsGatewayResponse(
            from_state=current_state,
            to_state=target_state,
            reason=cls.ACTION_REASONS[action],
            audit_ref=AuditReference(
                correlation_id=audit_record.correlation_id,
                request_id=audit_record.request_id,
                project_id=audit_record.project_id,
                timestamp=audit_record.created_at,
                action=audit_record.action,
                user_id=audit_record.user_id
            )
        )

    @classmethod
    def get_project_gateway_history(
        cls, 
        db: Session, 
        project_id: UUID
    ) -> list[RequirementsGatewayAudit]:
        """
        Get all gateway transition history for a project
        
        Args:
            db: Database session
            project_id: The project ID
            
        Returns:
            List of audit records for the project
        """
        return db.query(RequirementsGatewayAudit).filter(
            RequirementsGatewayAudit.project_id == project_id
        ).order_by(RequirementsGatewayAudit.created_at.desc()).all()