# backend/tests/test_prompts_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Project, Plan, PlanPhase, Requirement, PromptBundle
from unittest.mock import patch, MagicMock
import uuid

def test_generate_prompts_no_plan(client: TestClient, sample_project: Project):
    """Test prompt generation fails without plan."""
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/prompts/generate",
        json={
            "include_code": False
        }
    )
    
    assert response.status_code == 400
    assert "No plan found" in response.json()["detail"]

def test_generate_prompts_with_plan(
    client: TestClient,
    sample_project: Project,
    db_session: Session
):
    """Test successful prompt generation."""
    # Create plan with phases
    plan = Plan(
        project_id=sample_project.id,
        version=1,
        source="requirements",
        total_duration_days=20.0
    )
    db_session.add(plan)
    db_session.flush()
    
    phase = PlanPhase(
        plan_id=plan.id,
        phase_id="PH-01",
        sequence=1,
        title="Implementation Phase",
        objective="Implement core features",
        estimated_days=10.0,
        requirements_covered=["REQ-001"],
        activities=["Design", "Implement", "Test"],
        deliverables=["Working feature"],
        definition_of_done=["Tests passing"]
    )
    db_session.add(phase)
    
    # Create requirement
    req = Requirement(
        project_id=sample_project.id,
        key="REQ-001",
        title="Core Feature",
        priority="high",
        acceptance_criteria=["Works correctly"],
        is_coherent=True
    )
    db_session.add(req)
    db_session.commit()
    
    with patch('app.workers.tasks.prompts.generate_prompts.apply_async') as mock_task:
        mock_result = MagicMock()
        mock_result.get.return_value = {
            "status": "completed",
            "bundle_id": str(uuid.uuid4()),
            "version": 1,
            "total_prompts": 1
        }
        mock_task.return_value = mock_result
        
        response = client.post(
            f"/api/v1/projects/{sample_project.id}/prompts/generate",
            json={
                "include_code": True,
                "plan_id": str(plan.id)
            }
        )
        
        assert response.status_code in [200, 202]

def test_get_latest_prompts(client: TestClient, sample_project: Project, db_session: Session):
    """Test retrieving latest prompt bundle."""
    # Create bundle
    bundle = PromptBundle(
        project_id=sample_project.id,
        plan_id=uuid.uuid4(),
        version=1,
        include_code=False,
        context_md="# Test Context",
        total_prompts=2
    )
    db_session.add(bundle)
    db_session.flush()  # Assign ID to bundle
    
    # Add prompt items
    from app.models import PromptItem
    prompt1 = PromptItem(
        bundle_id=bundle.id,
        phase_id="PH-01",
        sequence=1,
        title="Phase 1",
        content_md="# Phase 1 Prompt"
    )
    prompt2 = PromptItem(
        bundle_id=bundle.id,
        phase_id="PH-02",
        sequence=2,
        title="Phase 2",
        content_md="# Phase 2 Prompt"
    )
    db_session.add(prompt1)
    db_session.add(prompt2)
    db_session.commit()
    
    # Get latest bundle
    response = client.get(f"/api/v1/projects/{sample_project.id}/prompts/latest")
    
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert data["total_prompts"] == 2
    assert len(data["prompts"]) == 2

def test_download_bundle_zip(client: TestClient, sample_project: Project, db_session: Session):
    """Test downloading prompt bundle as ZIP."""
    # Create bundle with prompts
    plan_id = uuid.uuid4()
    bundle = PromptBundle(
        project_id=sample_project.id,
        plan_id=plan_id,
        version=1,
        include_code=True,
        context_md="# Project Context\n\nTest context",
        total_prompts=1
    )
    db_session.add(bundle)
    db_session.flush()
    
    from app.models import PromptItem
    prompt = PromptItem(
        bundle_id=bundle.id,
        phase_id="PH-01",
        sequence=1,
        title="Test Phase",
        content_md="# Phase 1\n\nTest prompt content",
        metadata={"requirements": ["REQ-001"]}
    )
    db_session.add(prompt)
    db_session.commit()
    
    # Download ZIP
    response = client.get(
        f"/api/v1/projects/{sample_project.id}/prompts/bundles/{bundle.id}/download"
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]
    
    # Verify ZIP content
    import zipfile
    import io
    
    zip_data = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_data, 'r') as zip_file:
        files = zip_file.namelist()
        assert "context.md" in files
        assert "metadata.json" in files
        assert "README.md" in files
        assert any("prompts/" in f for f in files)

def test_download_nonexistent_bundle(client: TestClient, sample_project: Project):
    """Test downloading non-existent bundle returns 404."""
    fake_id = uuid.uuid4()
    
    response = client.get(
        f"/api/v1/projects/{sample_project.id}/prompts/bundles/{fake_id}/download"
    )
    
    assert response.status_code == 404