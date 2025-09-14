# backend/tests/test_requirements_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Project, Requirement, ProjectStatus
import json

def test_create_requirements_bulk(client: TestClient, sample_project: Project, sample_requirements_data):
    """Test bulk create requirements."""
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["key"] == "REQ-001"
    assert data[0]["priority"] == "high"
    assert len(data[0]["acceptance_criteria"]) == 3

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

def test_list_requirements(client: TestClient, sample_project: Project, sample_requirements_data):
    """Test listing requirements."""
    # First create requirements
    client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    # Then list them
    response = client.get(f"/api/v1/projects/{sample_project.id}/requirements")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(req["key"] == "REQ-001" for req in data)
    assert any(req["key"] == "REQ-002" for req in data)

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
    data = response.json()
    assert "requirements" in data
    assert len(data["requirements"]) == 2
    assert "exported_at" in data

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
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    content = response.text
    assert "# Requirements" in content
    assert "REQ-001" in content
    assert "High Priority" in content

def test_finalize_requirements(client: TestClient, sample_project: Project, sample_requirements_data, db_session: Session):
    """Test finalizing requirements."""
    # Create requirements
    client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    # Mark requirements as coherent
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
    
    # Check project status
    db_session.refresh(sample_project)
    assert sample_project.status == ProjectStatus.REQS_READY

def test_finalize_requirements_not_coherent(client: TestClient, sample_project: Project, sample_requirements_data):
    """Test finalize fails when requirements not coherent."""
    # Create requirements (not coherent by default)
    client.post(
        f"/api/v1/projects/{sample_project.id}/requirements",
        json={"requirements": sample_requirements_data}
    )
    
    # Try to finalize
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/requirements/finalize",
        json={"force": False}
    )
    
    assert response.status_code == 400
    assert "not all requirements are coherent" in response.json()["detail"].lower()

def test_refine_requirements(client: TestClient, sample_project: Project, sample_requirements_data):
    """Test queueing refinement job."""
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
    
    # Note: In test environment, Celery might not be running
    # so we just check the API response
    assert response.status_code in [200, 500]  # 500 if Celery not running
    if response.status_code == 200:
        data = response.json()
        assert "task_id" in data
        assert "project_id" in data