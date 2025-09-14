# backend/tests/test_requirements_api.py
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Project, Requirement, ProjectStatus
from unittest.mock import patch, MagicMock

def test_create_requirements_bulk(client: TestClient, sample_project: Project, sample_requirements_data):
    """Test bulk create requirements."""
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["key"] == "REQ-001"
    assert data[0]["priority"] == "high"
    assert len(data[0]["acceptance_criteria"]) == 4

def test_create_requirements_validation_error(client: TestClient, sample_project: Project):
    """Test requirements validation."""
    invalid_data = [{
        "key": "invalid key with spaces",
        "title": "Test",
        "priority": "invalid_priority"
    }]
    
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": invalid_data}
    )
    
    assert response.status_code == 422

def test_create_requirements_payload_limit(client: TestClient, sample_project: Project):
    """Test payload size limit."""
    # Create 101 requirements (exceeds limit)
    huge_data = [
        {
            "key": f"REQ-{i:03d}",
            "title": f"Requirement {i}",
            "priority": "medium"
        }
        for i in range(101)
    ]
    
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": huge_data}
    )
    
    assert response.status_code == 422
    assert "Maximum 100 requirements" in response.json()["detail"][0]["msg"]

def test_list_requirements(client: TestClient, sample_project: Project, sample_requirements_data):
    """Test listing requirements."""
    # Create requirements
    client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    # List them
    response = client.get(f"/api/v1/projects/{sample_project.id}/requirements")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert any(req["key"] == "REQ-001" for req in data)
    assert any(req["key"] == "REQ-003" for req in data)

def test_export_json(client: TestClient, sample_project: Project, sample_requirements_data):
    """Test JSON export."""
    # Create requirements
    client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    # Export as JSON
    response = client.get(f"/api/v1/projects/{sample_project.id}/requirements/export?format=json")
    
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert "requirements" in data
    assert len(data["requirements"]) == 3
    assert "exported_at" in data
    assert data["total"] == 3

def test_export_markdown(client: TestClient, sample_project: Project, sample_requirements_data):
    """Test Markdown export."""
    # Create requirements
    client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    # Export as Markdown
    response = client.get(f"/api/v1/projects/{sample_project.id}/requirements/export?format=md")
    
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    content = response.text
    assert "# Requirements Export" in content
    assert "REQ-001" in content
    assert "Critical Priority" in content
    assert "High Priority" in content

def test_finalize_requirements(client: TestClient, sample_project: Project, sample_requirements_data, db_session: Session):
    """Test finalizing requirements."""
    # Create requirements
    client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    # Mark all as coherent
    requirements = db_session.query(Requirement).filter(Requirement.project_id == sample_project.id).all()
    for req in requirements:
        req.is_coherent = True
    db_session.commit()
    
    # Finalize
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/requirements/finalize",
        json={"force": False}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["forced"] is False
    
    # Check project status
    db_session.refresh(sample_project)
    assert sample_project.status == ProjectStatus.REQS_READY

def test_finalize_requirements_force(client: TestClient, sample_project: Project, sample_requirements_data):
    """Test force finalize."""
    # Create requirements (not coherent)
    client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    # Force finalize
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/requirements/finalize",
        json={"force": True}
    )
    
    assert response.status_code == 200
    assert response.json()["forced"] is True

def test_finalize_requirements_validation_failures(client: TestClient, sample_project: Project):
    """Test finalize validation."""
    # Create requirement with circular dependency
    circular_reqs = [
        {"key": "A", "title": "A", "dependencies": ["B"]},
        {"key": "B", "title": "B", "dependencies": ["C"]},
        {"key": "C", "title": "C", "dependencies": ["A"]}
    ]
    
    client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": circular_reqs}
    )
    
    # Try to finalize
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/requirements/finalize",
        json={"force": False}
    )
    
    assert response.status_code == 400
    assert "circular dependencies" in response.json()["detail"].lower()

@patch('app.workers.tasks.requirements.refine_requirements.apply_async')
def test_refine_requirements(mock_task, client: TestClient, sample_project: Project, sample_requirements_data):
    """Test queueing refinement job."""
    # Mock Celery task
    mock_task.return_value = MagicMock(id="test-task-123")
    
    # Create requirements
    client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    # Queue refinement
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/requirements/refine",
        json={"context": "Additional context for refinement"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "test-task-123"
    assert data["project_id"] == str(sample_project.id)
    assert data["status"] == "pending"
    
    # Verify task was called
    mock_task.assert_called_once_with(
        args=[str(sample_project.id)],
        queue='default'
    )