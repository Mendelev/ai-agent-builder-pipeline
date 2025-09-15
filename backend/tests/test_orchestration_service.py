# backend/tests/test_orchestration_service.py
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.redis_client import RedisClient
from app.models import Project
from app.models.orchestration import AgentType, DedupKey, ProjectState
from app.services.orchestration_service import OrchestrationService
from app.services.state_machine import StateMachine


def test_transition_state_valid(db_session: Session, sample_project: Project):
    """Test valid state transition."""
    sample_project.status = ProjectState.DRAFT.value
    db_session.commit()

    success, error = OrchestrationService.transition_state(
        db_session, sample_project.id, ProjectState.REQS_REFINING, reason="Starting refinement", triggered_by="user123"
    )

    assert success is True
    assert error is None

    db_session.refresh(sample_project)
    assert sample_project.status == ProjectState.REQS_REFINING.value

    # Check state history was created
    from app.models.orchestration import StateHistory

    history = db_session.query(StateHistory).filter(StateHistory.project_id == sample_project.id).first()

    assert history is not None
    assert history.from_state == ProjectState.DRAFT
    assert history.to_state == ProjectState.REQS_REFINING
    assert history.transition_reason == "Starting refinement"


def test_transition_state_invalid(db_session: Session, sample_project: Project):
    """Test invalid state transition."""
    sample_project.status = ProjectState.DRAFT.value
    db_session.commit()

    success, error = OrchestrationService.transition_state(
        db_session, sample_project.id, ProjectState.DONE, reason="Invalid jump"  # Invalid transition
    )

    assert success is False
    assert "Invalid transition" in error

    db_session.refresh(sample_project)
    assert sample_project.status == ProjectState.DRAFT.value


def test_check_and_get_dedup_new(db_session: Session, sample_project: Project):
    """Test deduplication for new execution."""
    redis_client = MagicMock(spec=RedisClient)
    redis_client.set_nx.return_value = True  # Lock acquired

    input_data = {"test": "data"}

    result = OrchestrationService.check_and_get_dedup(
        db_session, redis_client, sample_project.id, AgentType.REFINE, input_data, ttl_seconds=3600
    )

    assert result is None  # No existing execution

    # Check dedup key was created
    dedup = (
        db_session.query(DedupKey)
        .filter(DedupKey.project_id == sample_project.id, DedupKey.agent_type == AgentType.REFINE)
        .first()
    )

    assert dedup is not None
    assert dedup.input_hash == StateMachine.compute_input_hash("REFINE", input_data)


def test_check_and_get_dedup_existing(db_session: Session, sample_project: Project):
    """Test deduplication with existing execution."""
    redis_client = MagicMock(spec=RedisClient)
    redis_client.set_nx.return_value = False  # Lock not acquired

    # Create existing dedup key
    input_data = {"test": "data"}
    input_hash = StateMachine.compute_input_hash("REFINE", input_data)

    existing_dedup = DedupKey(
        project_id=sample_project.id,
        agent_type=AgentType.REFINE,
        input_hash=input_hash,
        task_id="existing-task-123",
        result={"status": "completed"},
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    db_session.add(existing_dedup)
    db_session.commit()

    result = OrchestrationService.check_and_get_dedup(
        db_session, redis_client, sample_project.id, AgentType.REFINE, input_data, ttl_seconds=3600
    )

    assert result is not None
    assert result.task_id == "existing-task-123"
    assert result.result["status"] == "completed"


def test_record_agent_execution(db_session: Session, sample_project: Project):
    """Test recording agent execution."""
    OrchestrationService.record_agent_execution(
        db_session,
        sample_project.id,
        AgentType.PLAN,
        correlation_id="corr-123",
        success=True,
        duration_ms=1500.5,
        details={"phases": 5},
        error_message=None,
    )

    # Check audit log
    from app.models.orchestration import AuditLog, EventType

    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.project_id == sample_project.id, AuditLog.agent_type == AgentType.PLAN)
        .first()
    )

    assert audit is not None
    assert audit.event_type == EventType.AGENT_COMPLETED
    assert audit.success is True
    assert audit.duration_ms == 1500.5
    assert audit.correlation_id == "corr-123"

    # Check domain event
    from app.models.orchestration import DomainEvent

    event = (
        db_session.query(DomainEvent)
        .filter(DomainEvent.aggregate_id == sample_project.id, DomainEvent.event_name == "agent_plan_completed")
        .first()
    )

    assert event is not None
    assert event.event_data["success"] is True


def test_get_project_status(db_session: Session, sample_project: Project):
    """Test getting project status with events."""
    # Add some audit logs
    from app.models.orchestration import AuditLog, EventType

    for i in range(3):
        audit = AuditLog(
            project_id=sample_project.id, event_type=EventType.SYSTEM_EVENT, action=f"Action {i}", success=True
        )
        db_session.add(audit)
    db_session.commit()

    status = OrchestrationService.get_project_status(db_session, sample_project.id)

    assert status["id"] == sample_project.id
    assert status["name"] == sample_project.name
    assert len(status["recent_events"]) == 3
    assert "state_history" in status


def test_get_audit_logs_pagination(db_session: Session, sample_project: Project):
    """Test paginated audit log retrieval."""
    from app.models.orchestration import AuditLog, EventType

    # Create 15 audit logs
    for i in range(15):
        audit = AuditLog(
            project_id=sample_project.id, event_type=EventType.SYSTEM_EVENT, action=f"Action {i}", success=True
        )
        db_session.add(audit)
    db_session.commit()

    # Get first page
    result = OrchestrationService.get_audit_logs(db_session, sample_project.id, page=1, page_size=10)

    assert len(result["items"]) == 10
    assert result["total"] == 15
    assert result["total_pages"] == 2

    # Get second page
    result = OrchestrationService.get_audit_logs(db_session, sample_project.id, page=2, page_size=10)

    assert len(result["items"]) == 5


def test_retry_agent_allowed(db_session: Session, sample_project: Project):
    """Test retrying agent in allowed state."""
    redis_client = MagicMock(spec=RedisClient)
    redis_client.set_nx.return_value = True

    sample_project.status = ProjectState.REQS_REFINING.value
    db_session.commit()

    # Mock the celery task
    with patch("app.workers.tasks.requirements.refine_requirements.delay") as mock_task:
        mock_task.return_value = MagicMock(id="test-task-123")

        result = OrchestrationService.retry_agent(
            db_session, redis_client, sample_project.id, AgentType.REFINE, force=False, metadata={"test": "data"}
        )

        assert result["task_id"] == "test-task-123"
        assert result["status"] == "queued"

    # Check retry was recorded
    from app.models.orchestration import AuditLog, EventType

    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.project_id == sample_project.id, AuditLog.event_type == EventType.RETRY_ATTEMPTED)
        .first()
    )

    assert audit is not None


def test_retry_agent_not_allowed(db_session: Session, sample_project: Project):
    """Test retrying agent in wrong state."""
    redis_client = MagicMock(spec=RedisClient)

    sample_project.status = ProjectState.DONE.value
    db_session.commit()

    with pytest.raises(ValueError) as exc:
        OrchestrationService.retry_agent(db_session, redis_client, sample_project.id, AgentType.REFINE, force=False)

    assert "Cannot retry" in str(exc.value)


def test_retry_agent_with_force(db_session: Session, sample_project: Project):
    """Test force retry bypasses state check."""
    redis_client = MagicMock(spec=RedisClient)

    sample_project.status = ProjectState.DONE.value
    db_session.commit()

    # Mock the celery task
    with patch("app.workers.tasks.requirements.refine_requirements.delay") as mock_task:
        mock_task.return_value = MagicMock(id="test-task-456")

        # Should not raise error with force=True
        result = OrchestrationService.retry_agent(
            db_session, redis_client, sample_project.id, AgentType.REFINE, force=True  # Bypass state check
        )

        assert result["task_id"] == "test-task-456"
        assert result["status"] == "queued"
