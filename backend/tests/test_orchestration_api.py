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
            "agent": "INVALID",
            "force": False
        }
    )
    
    assert response.status_code == 400
    assert "Invalid agent type" in response.json()["detail"]