# backend/tests/test_plan_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Project, Requirement, Plan
from unittest.mock import patch, MagicMock
import uuid

def test_generate_plan_no_requirements(client: TestClient, sample_project: Project):
    """Test plan generation fails without requirements."""
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/plan",
        json={
            "source": "requirements",
            "use_code": False,
            "include_checklist": False
        }
    )
    
    assert response.status_code == 400
    assert "No requirements found" in response.json()["detail"]

def test_generate_plan_with_requirements(
    client: TestClient, 
    sample_project: Project,
    sample_requirements_data,
    db_session: Session
):
    """Test successful plan generation."""
    # Create requirements first
    from app.services.requirement_service import RequirementService
    from app.schemas.requirement import RequirementCreate
    
    req_creates = [RequirementCreate(**r) for r in sample_requirements_data]
    RequirementService.create_bulk(db_session, sample_project.id, req_creates)
    
    with patch('app.workers.tasks.plan.generate_plan.apply_async') as mock_task:
        mock_result = MagicMock()
        mock_result.get.return_value = {
            "status": "completed",
            "plan_id": str(uuid.uuid4()),
            "version": 1,
            "total_phases": 3,
            "total_duration_days": 25.0,
            "coverage_percentage": 100.0,
            "risk_score": 0.6
        }
        mock_task.return_value = mock_result
        
        response = client.post(
            f"/api/v1/projects/{sample_project.id}/plan",
            json={
                "source": "requirements",
                "use_code": False,
                "include_checklist": True,
                "constraints": {
                    "deadline_days": 90,
                    "team_size": 5
                }
            }
        )
        
        assert response.status_code in [200, 202]

def test_generate_plan_with_checklist(
    client: TestClient,
    sample_project: Project,
    db_session: Session
):
    """Test plan generation with checklist phases."""
    # Create minimal requirements
    req = Requirement(
        project_id=sample_project.id,
        key="REQ-001",
        title="Test Requirement",
        priority="medium",
        acceptance_criteria=["Test criterion"],
        is_coherent=True
    )
    db_session.add(req)
    db_session.commit()
    
    # Generate plan with checklist
    from app.services.plan_service import PlanService
    from app.schemas.plan import PlanGenerateRequest
    
    request = PlanGenerateRequest(
        source="requirements",
        include_checklist=True
    )
    
    plan = PlanService.generate_plan(db_session, sample_project.id, request)
    
    assert plan is not None
    assert len(plan.phases) >= 3  # At least 1 req phase + 2 checklist phases
    
    # Check for QA phase
    qa_phase = next((p for p in plan.phases if "Quality Assurance" in p.title), None)
    assert qa_phase is not None
    
    # Check for deployment phase
    deploy_phase = next((p for p in plan.phases if "Deployment" in p.title), None)
    assert deploy_phase is not None

def test_get_latest_plan(client: TestClient, sample_project: Project, db_session: Session):
    """Test retrieving latest plan."""
    # Create a plan
    plan = Plan(
        project_id=sample_project.id,
        version=1,
        source="requirements",
        total_duration_days=30.0,
        coverage_percentage=95.0,
        risk_score=0.5
    )
    db_session.add(plan)
    db_session.flush()  # Assign ID to plan
    
    # Add phases
    from app.models import PlanPhase
    phase = PlanPhase(
        plan_id=plan.id,
        phase_id="PH-01",
        sequence=1,
        title="Phase 1",
        objective="Test objective",
        estimated_days=10.0,
        requirements_covered=["REQ-001"]
    )
    db_session.add(phase)
    db_session.commit()
    
    # Get latest plan
    response = client.get(f"/api/v1/projects/{sample_project.id}/plan/latest")
    
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert data["total_duration_days"] == 30.0
    assert len(data["phases"]) == 1

def test_get_plan_by_id(client: TestClient, sample_project: Project, db_session: Session):
    """Test retrieving specific plan by ID."""
    # Create a plan
    plan = Plan(
        project_id=sample_project.id,
        version=1,
        source="requirements"
    )
    db_session.add(plan)
    db_session.commit()
    
    # Get plan by ID
    response = client.get(f"/api/v1/projects/{sample_project.id}/plan/{plan.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(plan.id)

def test_get_nonexistent_plan(client: TestClient, sample_project: Project):
    """Test getting non-existent plan returns 404."""
    fake_id = uuid.uuid4()
    
    response = client.get(f"/api/v1/projects/{sample_project.id}/plan/{fake_id}")
    assert response.status_code == 404
    
    response = client.get(f"/api/v1/projects/{sample_project.id}/plan/latest")
    assert response.status_code == 404

def test_generate_plan_invalid_project(client: TestClient):
    """Test generating plan for non-existent project."""
    non_existent_id = uuid.uuid4()
    response = client.post(
        f"/api/v1/projects/{non_existent_id}/plan",
        json={"source": "requirements"}
    )
    assert response.status_code == 404

def test_generate_plan_exception_handling(client: TestClient, sample_project: Project):
    """Test plan generation with invalid request."""
    response = client.post(
        f"/api/v1/projects/{sample_project.id}/plan",
        json={"source": "invalid_source"}
    )
    assert response.status_code == 422

def test_get_plan_by_id_invalid_project(client: TestClient):
    """Test getting plan by ID for non-existent project."""
    non_existent_project_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    response = client.get(f"/api/v1/projects/{non_existent_project_id}/plan/{plan_id}")
    assert response.status_code == 404