# backend/tests/test_orchestration_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Project
from app.models.orchestration import ProjectState, AuditLog, EventType, AgentType
import uuid

def test_get_project_status(client: TestClient, sample_project: Project, db_session: Session):
    """Test getting project status with events."""
    # Add audit logs
    audit1 = AuditLog(
        project_id=sample_project.id,
        event_type=EventType.STATE_TRANSITION,
        action="State changed to REQS_READY",
        success=True
    )
    audit2 = AuditLog(
        project_id=sample_project.id,
        event_type=EventType.AGENT_COMPLETED,
        agent_type=AgentType.REFINE,
        action="Refinement completed",
        success=True
    )
    db_session.add(audit1)
    db_session.add(audit2)
    db_session.commit()
    
    response = client.get(f"/api/v1/projects/{sample_project.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_project.id)
    assert data["name"] == sample_project.name
    assert "recent_events" in data
    assert len(data["recent_events"]) >= 2

def test_get_audit_logs_paginated(client: TestClient, sample_project: Project, db_session: Session):
    """Test paginated audit log retrieval."""
    # Create multiple audit logs
    for i in range(25):
        audit = AuditLog(
            project_id=sample_project.id,
            event_type=EventType.SYSTEM_EVENT,
            action=f"Test action {i}",
            success=True
        )
        db_session.add(audit)
    db_session.commit()
    
    # Get first page
    response = client.get(
        f"/api/v1/projects/{sample_project.id}/audit?page=1&page_size=10"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 25
    assert data["total_pages"] == 3
    
    # Get second page
    response = client.get(
        f"/api/v1/projects/{sample_project.id}/audit?page=2&page_size=10"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10

def test_retry_agent_execution(client: TestClient, sample_project: Project):
    """Test agent retry endpoint."""
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/retry/refine",
        json={
            "agent": "REFINE",
            "force": False,
            "metadata": {"test": "data"}
        }
    )
    
    # Should fail because project is in wrong state
    assert response.status_code in [400, 500]

def test_retry_invalid_agent(client: TestClient, sample_project: Project):
    """Test retry with invalid agent type."""
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/retry/invalid_agent",
        json={
            "agent": "REQUIREMENTS",  # Valid in JSON, but URL has invalid agent
            "force": False
        }
    )
    
    assert response.status_code == 400
    assert "Invalid agent type" in response.json()["detail"]

def test_get_project_status_not_found(client: TestClient):
    """Test getting status for non-existent project."""
    non_existent_id = uuid.uuid4()
    response = client.get(f"/api/v1/projects/{non_existent_id}")
    
    assert response.status_code == 404
    assert "detail" in response.json()

def test_get_audit_logs_invalid_event_type(client: TestClient, sample_project: Project):
    """Test audit logs with invalid event type."""
    response = client.get(
        f"/api/v1/projects/{sample_project.id}/audit?event_type=INVALID_TYPE"
    )
    
    assert response.status_code == 400
    assert "Invalid event type" in response.json()["detail"]

def test_get_audit_logs_not_found(client: TestClient):
    """Test audit logs for non-existent project."""
    non_existent_id = uuid.uuid4()
    response = client.get(f"/api/v1/projects/{non_existent_id}/audit")
    
    # Should return 200 with empty results, not 500
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0

def test_retry_agent_invalid_project(client: TestClient):
    """Test retry agent for non-existent project."""
    non_existent_id = uuid.uuid4()
    response = client.post(
        f"/api/v1/projects/{non_existent_id}/retry/refine",
        json={
            "agent": "REFINE",
            "force": False
        }
    )
    
    assert response.status_code in [400, 500]