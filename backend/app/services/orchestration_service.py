# backend/app/services/orchestration_service.py
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta, UTC
from app.models import Project
from app.models.orchestration import (
    ProjectState, StateHistory, AuditLog, DomainEvent,
    DedupKey, EventType, AgentType
)
from app.services.state_machine import StateMachine
from app.core.redis_client import RedisClient
from app.core.observability import get_logger
import json

logger = get_logger(__name__)

class OrchestrationService:
    @staticmethod
    def transition_state(
        db: Session,
        project_id: UUID,
        to_state: ProjectState,
        reason: str = None,
        triggered_by: str = "system",
        metadata: Dict[str, Any] = None
    ) -> Tuple[bool, Optional[str]]:
        """Transition project to new state"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False, f"Project {project_id} not found"
        
        current_state = ProjectState(project.status)
        
        # Validate transition
        valid, error = StateMachine.validate_transition(current_state, to_state)
        if not valid:
            logger.warning(f"Invalid state transition for project {project_id}: {error}")
            return False, error
        
        # Record state history
        history = StateHistory(
            project_id=project_id,
            from_state=current_state,
            to_state=to_state,
            transition_reason=reason,
            triggered_by=triggered_by,
            metadata=metadata or {}
        )
        db.add(history)
        
        # Update project state
        project.status = to_state.value
        
        # Create domain event
        event = DomainEvent(
            aggregate_id=project_id,
            aggregate_type="project",
            event_name=f"state_changed_to_{to_state.value.lower()}",
            event_data={
                "from_state": current_state.value,
                "to_state": to_state.value,
                "reason": reason,
                "triggered_by": triggered_by
            },
            metadata=metadata or {}
        )
        db.add(event)
        
        # Audit log
        audit = AuditLog(
            project_id=project_id,
            event_type=EventType.STATE_TRANSITION,
            action=f"State transition: {current_state.value} -> {to_state.value}",
            details={
                "from_state": current_state.value,
                "to_state": to_state.value,
                "reason": reason
            },
            user_id=triggered_by if triggered_by != "system" else None,
            success=True
        )
        db.add(audit)
        
        db.commit()
        
        logger.info(
            f"Project {project_id} transitioned from {current_state.value} to {to_state.value}",
            extra={"project_id": str(project_id), "from_state": current_state.value, "to_state": to_state.value}
        )
        
        return True, None
    
    @staticmethod
    def check_and_get_dedup(
        db: Session,
        redis_client: RedisClient,
        project_id: UUID,
        agent_type: AgentType,
        input_data: Dict[str, Any],
        ttl_seconds: int = 3600
    ) -> Optional[DedupKey]:
        """Check for duplicate execution and get cached result"""
        input_hash = StateMachine.compute_input_hash(agent_type.value, input_data)
        
        # Try to acquire lock
        lock_key = f"dedup_lock:{project_id}:{agent_type.value}:{input_hash}"
        if not redis_client.set_nx(lock_key, "1", ttl=30):  # 30 second lock
            logger.info(f"Duplicate execution detected for {agent_type.value} on project {project_id}")
            
            # Check for existing result
            existing = db.query(DedupKey).filter(
                DedupKey.project_id == project_id,
                DedupKey.agent_type == agent_type,
                DedupKey.input_hash == input_hash,
                DedupKey.expires_at > datetime.now(UTC)
            ).first()
            
            return existing
        
        # Create new dedup key
        dedup = DedupKey(
            project_id=project_id,
            agent_type=agent_type,
            input_hash=input_hash,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        )
        db.add(dedup)
        db.commit()
        
        return None
    
    @staticmethod
    def record_agent_execution(
        db: Session,
        project_id: UUID,
        agent_type: AgentType,
        correlation_id: str,
        success: bool,
        duration_ms: float,
        details: Dict[str, Any] = None,
        error_message: str = None
    ):
        """Record agent execution in audit log"""
        audit = AuditLog(
            project_id=project_id,
            correlation_id=correlation_id,
            event_type=EventType.AGENT_COMPLETED if success else EventType.AGENT_FAILED,
            agent_type=agent_type,
            action=f"Agent {agent_type.value} execution",
            details=details or {},
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        db.add(audit)
        
        # Create domain event
        event = DomainEvent(
            aggregate_id=project_id,
            aggregate_type="project",
            event_name=f"agent_{agent_type.value.lower()}_{'completed' if success else 'failed'}",
            event_data={
                "agent": agent_type.value,
                "success": success,
                "duration_ms": duration_ms,
                "error": error_message
            },
            metadata={"correlation_id": correlation_id}
        )
        db.add(event)
        
        db.commit()
    
    @staticmethod
    def get_project_status(db: Session, project_id: UUID) -> Dict[str, Any]:
        """Get project status with recent events"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Get recent events
        recent_events = db.query(AuditLog).filter(
            AuditLog.project_id == project_id
        ).order_by(desc(AuditLog.created_at)).limit(10).all()
        
        # Get state history
        state_history = db.query(StateHistory).filter(
            StateHistory.project_id == project_id
        ).order_by(desc(StateHistory.created_at)).limit(5).all()
        
        return {
            "id": project.id,
            "name": project.name,
            "state": project.status,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "extra_metadata": getattr(project, 'extra_metadata', {}),
            "recent_events": [
                {
                    "type": event.event_type.value,
                    "action": event.action,
                    "success": event.success,
                    "created_at": event.created_at.isoformat()
                }
                for event in recent_events
            ],
            "state_history": [
                {
                    "from": history.from_state.value if history.from_state else None,
                    "to": history.to_state.value,
                    "reason": history.transition_reason,
                    "created_at": history.created_at.isoformat()
                }
                for history in state_history
            ]
        }
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        project_id: UUID,
        page: int = 1,
        page_size: int = 50,
        event_type: Optional[EventType] = None
    ) -> Dict[str, Any]:
        """Get paginated audit logs"""
        query = db.query(AuditLog).filter(AuditLog.project_id == project_id)
        
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        
        total = query.count()
        
        logs = query.order_by(desc(AuditLog.created_at))\
                   .offset((page - 1) * page_size)\
                   .limit(page_size)\
                   .all()
        
        return {
            "items": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    @staticmethod
    def retry_agent(
        db: Session,
        redis_client: RedisClient,
        project_id: UUID,
        agent_type: AgentType,
        force: bool = False,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Retry an agent execution"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        current_state = ProjectState(project.status)
        
        # Check if retry is allowed in current state
        if not force and not StateMachine.can_retry_in_state(current_state, agent_type.value):
            raise ValueError(f"Cannot retry {agent_type.value} in state {current_state.value}")
        
        # Check for existing execution
        if not force:
            dedup = OrchestrationService.check_and_get_dedup(
                db, redis_client, project_id, agent_type, metadata or {}
            )
            if dedup and dedup.result:
                return {
                    "task_id": dedup.task_id,
                    "status": "cached",
                    "result": dedup.result
                }
        
        # Record retry attempt
        audit = AuditLog(
            project_id=project_id,
            event_type=EventType.RETRY_ATTEMPTED,
            agent_type=agent_type,
            action=f"Retry {agent_type.value}",
            details={"force": force, "metadata": metadata},
            success=True
        )
        db.add(audit)
        db.commit()
        
        # Queue the appropriate task
        from app.workers.tasks.requirements import refine_requirements
        from app.workers.tasks.plan import generate_plan
        from app.workers.tasks.prompts import generate_prompts
        
        task = None
        if agent_type == AgentType.REFINE:
            task = refine_requirements.delay(str(project_id))
        elif agent_type == AgentType.PLAN:
            task = generate_plan.delay(str(project_id), metadata or {})
        elif agent_type == AgentType.PROMPTS:
            task = generate_prompts.delay(str(project_id), None, False)
        
        if task:
            return {
                "task_id": task.id,
                "status": "queued",
                "agent": agent_type.value
            }
        
        raise ValueError(f"No task handler for agent {agent_type.value}")