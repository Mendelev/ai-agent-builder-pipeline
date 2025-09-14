# backend/tests/test_plan_service.py
import pytest
from sqlalchemy.orm import Session
from app.services.plan_service import PlanService
from app.models import Project, Requirement, Plan, PlanPhase
from app.schemas.plan import PlanGenerateRequest, PlanConstraints
import uuid

def test_topological_sort_simple():
    """Test topological sort with simple dependencies."""
    graph = {
        "A": [],
        "B": ["A"],
        "C": ["B"],
        "D": ["A", "B"]
    }
    
    result = PlanService._topological_sort(graph)
    
    # A should come before B and D
    assert result.index("A") < result.index("B")
    assert result.index("A") < result.index("D")
    # B should come before C and D
    assert result.index("B") < result.index("C")
    assert result.index("B") < result.index("D")

def test_topological_sort_with_cycle():
    """Test topological sort detects cycles."""
    graph = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"]  # Cycle
    }
    
    result = PlanService._topological_sort(graph)
    
    # Should detect cycle and return partial result
    assert len(result) < 3

def test_group_into_phases():
    """Test grouping requirements into phases."""
    req_map = {
        "REQ-001": Requirement(key="REQ-001", priority="critical"),
        "REQ-002": Requirement(key="REQ-002", priority="high"),
        "REQ-003": Requirement(key="REQ-003", priority="medium"),
        "REQ-004": Requirement(key="REQ-004", priority="low"),
        "REQ-005": Requirement(key="REQ-005", priority="medium")
    }
    
    execution_order = ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005"]
    
    phases = PlanService._group_into_phases(execution_order, req_map, None)
    
    assert len(phases) >= 1
    assert len(phases) <= 5
    # Critical requirement should be in early phase
    assert "REQ-001" in phases[0]

def test_calculate_complexity():
    """Test complexity calculation."""
    group = ["REQ-001", "REQ-002"]
    req_map = {
        "REQ-001": Requirement(
            key="REQ-001",
            priority="critical",
            acceptance_criteria=["AC1", "AC2", "AC3"]
        ),
        "REQ-002": Requirement(
            key="REQ-002",
            priority="medium",
            acceptance_criteria=["AC1"]
        )
    }
    
    complexity = PlanService._calculate_complexity(group, req_map)
    
    # Critical (4) + 3 criteria (1.5) + Medium (2) + 1 criterion (0.5) = 8
    assert complexity == 8.0

def test_assess_risk():
    """Test risk assessment."""
    # Test with critical priority
    group = ["REQ-001"]
    req_map = {"REQ-001": Requirement(key="REQ-001", priority="critical")}
    assert PlanService._assess_risk(group, req_map) == "critical"
    
    # Test with high priority
    req_map = {"REQ-001": Requirement(key="REQ-001", priority="high")}
    assert PlanService._assess_risk(group, req_map) == "high"
    
    # Test with many requirements
    group = ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005", "REQ-006"]
    req_map = {f"REQ-{i:03d}": Requirement(key=f"REQ-{i:03d}", priority="low") for i in range(1, 7)}
    assert PlanService._assess_risk(group, req_map) == "high"

def test_estimate_duration():
    """Test duration estimation."""
    group = ["REQ-001"]
    req_map = {
        "REQ-001": Requirement(
            key="REQ-001",
            priority="high",
            dependencies=["DEP-001", "DEP-002"]
        )
    }
    
    complexity = 5.0
    duration = PlanService._estimate_duration(group, req_map, complexity)
    
    # Base (5*2) + dependency factor (1 + 2*0.1) = 10 * 1.2 = 12
    assert duration == 12.0

def test_generate_plan_with_high_priority_uncovered(db_session: Session, sample_project: Project):
    """Test plan generation with high priority requirements needing remediation."""
    # Create requirements with circular dependency
    reqs = [
        Requirement(
            project_id=sample_project.id,
            key="HIGH-001",
            title="High Priority",
            priority="high",
            dependencies=["HIGH-002"],
            is_coherent=True
        ),
        Requirement(
            project_id=sample_project.id,
            key="HIGH-002",
            title="Another High",
            priority="high",
            dependencies=["HIGH-001"],  # Circular
            is_coherent=True
        ),
        Requirement(
            project_id=sample_project.id,
            key="NORMAL-001",
            title="Normal Priority",
            priority="medium",
            is_coherent=True
        )
    ]
    
    for req in reqs:
        db_session.add(req)
    db_session.commit()
    
    # Generate plan
    request = PlanGenerateRequest(source="requirements")
    plan = PlanService.generate_plan(db_session, sample_project.id, request)
    
    assert plan is not None
    
    # Should have remediation phase
    remediation_phase = next((p for p in plan.phases if p.phase_id == "PH-00"), None)
    assert remediation_phase is not None
    assert "Remediation" in remediation_phase.title

def test_generate_plan_coverage(db_session: Session, sample_project: Project):
    """Test plan coverage calculation."""
    # Create requirements
    reqs = [
        Requirement(
            project_id=sample_project.id,
            key=f"REQ-{i:03d}",
            title=f"Requirement {i}",
            priority="medium",
            is_coherent=True
        )
        for i in range(1, 6)
    ]
    
    for req in reqs:
        db_session.add(req)
    db_session.commit()
    
    # Generate plan
    request = PlanGenerateRequest(source="requirements")
    plan = PlanService.generate_plan(db_session, sample_project.id, request)
    
    # Check coverage
    assert plan.coverage_percentage == 100.0  # All requirements should be covered
    
    # Verify all requirements are in phases
    all_covered = set()
    for phase in plan.phases:
        all_covered.update(phase.requirements_covered)
    
    assert len(all_covered) == 5

def test_generate_checklist_phases():
    """Test checklist phase generation."""
    checklist_phases = PlanService._generate_checklist_phases(2)
    
    assert len(checklist_phases) == 2
    assert checklist_phases[0]["phase_id"] == "PH-03"
    assert "Quality Assurance" in checklist_phases[0]["title"]
    assert checklist_phases[1]["phase_id"] == "PH-04"
    assert "Deployment" in checklist_phases[1]["title"]
    
    # Check dependencies
    assert checklist_phases[0]["dependencies"] == ["PH-02"]
    assert checklist_phases[1]["dependencies"] == ["PH-03"]

def test_plan_versioning(db_session: Session, sample_project: Project):
    """Test plan version incrementing."""
    # Create requirement
    req = Requirement(
        project_id=sample_project.id,
        key="REQ-001",
        title="Test",
        priority="medium",
        is_coherent=True
    )
    db_session.add(req)
    db_session.commit()
    
    request = PlanGenerateRequest(source="requirements")
    
    # Generate first plan
    plan1 = PlanService.generate_plan(db_session, sample_project.id, request)
    assert plan1.version == 1
    
    # Generate second plan
    plan2 = PlanService.generate_plan(db_session, sample_project.id, request)
    assert plan2.version == 2
    
    # Get latest should return v2
    latest = PlanService.get_latest_plan(db_session, sample_project.id)
    assert latest.id == plan2.id
    assert latest.version == 2