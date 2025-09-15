import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.services.orchestration_service import OrchestrationService
from app.services.state_machine import StateMachine
from app.models import Project
from app.models.orchestration import (
    ProjectState,
    StateHistory,
    AuditLog,
    DomainEvent,
    DedupKey,
    EventType,
    AgentType,
)


def _mock_query_first(return_value):
    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = return_value
    return q


def test_transition_state_valid_unit():
    project_id = uuid.uuid4()
    project = Project(id=project_id, name="Test", status=ProjectState.DRAFT)

    db: Session = MagicMock(spec=Session)
    db.query.side_effect = [_mock_query_first(project)]

    success, error = OrchestrationService.transition_state(
        db,
        project_id,
        ProjectState.REQS_REFINING,
        reason="Starting refinement",
        triggered_by="user123",
    )

    assert success is True
    assert error is None
    # History + Event + Audit
    assert db.add.call_count == 3
    db.commit.assert_called_once()
    # Project state updated
    assert project.status == ProjectState.REQS_REFINING.value


def test_transition_state_invalid_unit():
    project_id = uuid.uuid4()
    project = Project(id=project_id, name="Test", status=ProjectState.DRAFT)

    db: Session = MagicMock(spec=Session)
    db.query.side_effect = [_mock_query_first(project)]

    success, error = OrchestrationService.transition_state(
        db,
        project_id,
        ProjectState.DONE,  # invalid jump
        reason="Invalid",
    )

    assert success is False
    assert "Invalid transition" in error
    db.commit.assert_not_called()


def test_check_and_get_dedup_new_unit():
    db: Session = MagicMock(spec=Session)
    redis_client = MagicMock()
    redis_client.set_nx.return_value = True

    project_id = uuid.uuid4()
    result = OrchestrationService.check_and_get_dedup(
        db,
        redis_client,
        project_id,
        AgentType.REFINE,
        {"test": "data"},
        ttl_seconds=3600,
    )

    assert result is None
    # Should have added a DedupKey
    assert db.add.called
    added_obj = db.add.call_args[0][0]
    assert isinstance(added_obj, DedupKey)


def test_check_and_get_dedup_existing_unit():
    db: Session = MagicMock(spec=Session)
    redis_client = MagicMock()
    redis_client.set_nx.return_value = False  # lock not acquired

    project_id = uuid.uuid4()
    input_data = {"test": "data"}
    input_hash = StateMachine.compute_input_hash("REFINE", input_data)
    existing = DedupKey(
        project_id=project_id,
        agent_type=AgentType.REFINE,
        input_hash=input_hash,
        task_id="existing-task-123",
        result={"status": "completed"},
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )

    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = existing
    db.query.return_value = q

    result = OrchestrationService.check_and_get_dedup(
        db,
        redis_client,
        project_id,
        AgentType.REFINE,
        input_data,
        ttl_seconds=3600,
    )

    assert result is existing
    assert result.task_id == "existing-task-123"
    assert result.result["status"] == "completed"


def test_record_agent_execution_unit():
    db: Session = MagicMock(spec=Session)
    project_id = uuid.uuid4()

    OrchestrationService.record_agent_execution(
        db,
        project_id,
        AgentType.PLAN,
        correlation_id="corr-123",
        success=True,
        duration_ms=1500.5,
        details={"phases": 5},
        error_message=None,
    )

    # Audit + DomainEvent
    assert db.add.call_count == 2
    first_obj = db.add.call_args_list[0][0][0]
    second_obj = db.add.call_args_list[1][0][0]
    assert isinstance(first_obj, AuditLog) or isinstance(second_obj, AuditLog)
    assert isinstance(first_obj, DomainEvent) or isinstance(second_obj, DomainEvent)
    db.commit.assert_called_once()


def test_get_project_status_unit():
    db: Session = MagicMock(spec=Session)
    project_id = uuid.uuid4()
    project = Project(id=project_id, name="Proj", status=ProjectState.DRAFT)
    project.created_at = datetime.utcnow()
    project.updated_at = datetime.utcnow()

    # Project query
    project_q = _mock_query_first(project)

    # Audit logs chain
    audit1 = SimpleNamespace(
        event_type=EventType.SYSTEM_EVENT,
        action="Action 1",
        success=True,
        created_at=datetime.utcnow(),
    )
    audit_q = MagicMock()
    audit_q.filter.return_value = audit_q
    audit_q.order_by.return_value = audit_q
    audit_q.limit.return_value = audit_q
    audit_q.all.return_value = [audit1]

    # State history chain
    hist1 = SimpleNamespace(
        from_state=ProjectState.DRAFT,
        to_state=ProjectState.REQS_REFINING,
        transition_reason="Start",
        created_at=datetime.utcnow(),
    )
    hist_q = MagicMock()
    hist_q.filter.return_value = hist_q
    hist_q.order_by.return_value = hist_q
    hist_q.limit.return_value = hist_q
    hist_q.all.return_value = [hist1]

    db.query.side_effect = [project_q, audit_q, hist_q]

    status = OrchestrationService.get_project_status(db, project_id)
    assert status["id"] == project_id
    assert status["name"] == "Proj"
    assert len(status["recent_events"]) == 1
    assert len(status["state_history"]) == 1


def test_get_audit_logs_unit():
    db: Session = MagicMock(spec=Session)

    q = MagicMock()
    q.filter.return_value = q
    q.count.return_value = 15
    q.order_by.return_value = q
    q.offset.return_value = q
    q.limit.return_value = q
    q.all.return_value = [
        SimpleNamespace(event_type=EventType.SYSTEM_EVENT, action="Action", success=True)
        for _ in range(10)
    ]
    db.query.return_value = q

    result = OrchestrationService.get_audit_logs(db, uuid.uuid4(), page=2, page_size=10)
    assert len(result["items"]) == 10
    assert result["total"] == 15
    assert result["total_pages"] == 2
    assert result["page"] == 2


def test_retry_agent_allowed_unit():
    db: Session = MagicMock(spec=Session)
    project_id = uuid.uuid4()
    project = Project(id=project_id, name="Test", status=ProjectState.REQS_REFINING)
    db.query.return_value = _mock_query_first(project)

    redis_client = MagicMock()
    redis_client.set_nx.return_value = True

    with patch("app.workers.tasks.requirements.refine_requirements.delay") as mock_task:
        mock_task.return_value = SimpleNamespace(id="test-task-123")
        result = OrchestrationService.retry_agent(
            db,
            redis_client,
            project_id,
            AgentType.REFINE,
            force=False,
            metadata={"test": "data"},
        )
        assert result["task_id"] == "test-task-123"
        assert result["status"] == "queued"


def test_retry_agent_not_allowed_unit():
    db: Session = MagicMock(spec=Session)
    project_id = uuid.uuid4()
    project = Project(id=project_id, name="Test", status=ProjectState.DONE)
    db.query.return_value = _mock_query_first(project)

    redis_client = MagicMock()

    try:
        OrchestrationService.retry_agent(
            db, redis_client, project_id, AgentType.REFINE, force=False
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Cannot retry" in str(exc)


def test_retry_agent_with_force_unit():
    db: Session = MagicMock(spec=Session)
    project_id = uuid.uuid4()
    project = Project(id=project_id, name="Test", status=ProjectState.DONE)
    db.query.return_value = _mock_query_first(project)

    redis_client = MagicMock()

    with patch("app.workers.tasks.requirements.refine_requirements.delay") as mock_task:
        mock_task.return_value = SimpleNamespace(id="test-task-456")
        result = OrchestrationService.retry_agent(
            db, redis_client, project_id, AgentType.REFINE, force=True
        )
        assert result["task_id"] == "test-task-456"
        assert result["status"] == "queued"

