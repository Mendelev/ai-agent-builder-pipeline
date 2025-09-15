# Unit tests for PlanService with no DB interactions
from app.services.plan_service import PlanService
from app.models import Requirement


def test_topological_sort_simple_unit():
    graph = {
        "A": [],
        "B": ["A"],
        "C": ["B"],
        "D": ["A", "B"],
    }
    result = PlanService._topological_sort(graph)
    assert result.index("A") < result.index("B")
    assert result.index("A") < result.index("D")
    assert result.index("B") < result.index("C")
    assert result.index("B") < result.index("D")


def test_topological_sort_with_cycle_unit():
    graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
    result = PlanService._topological_sort(graph)
    assert len(result) < 3


def test_group_into_phases_unit():
    req_map = {
        "REQ-001": Requirement(key="REQ-001", priority="critical"),
        "REQ-002": Requirement(key="REQ-002", priority="high"),
        "REQ-003": Requirement(key="REQ-003", priority="medium"),
        "REQ-004": Requirement(key="REQ-004", priority="low"),
        "REQ-005": Requirement(key="REQ-005", priority="medium"),
    }
    execution_order = ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005"]
    phases = PlanService._group_into_phases(execution_order, req_map, None)
    assert len(phases) >= 1
    assert len(phases) <= 5
    assert "REQ-001" in phases[0]


def test_calculate_complexity_unit():
    group = ["REQ-001", "REQ-002"]
    req_map = {
        "REQ-001": Requirement(
            key="REQ-001",
            priority="critical",
            acceptance_criteria=["AC1", "AC2", "AC3"],
        ),
        "REQ-002": Requirement(
            key="REQ-002",
            priority="medium",
            acceptance_criteria=["AC1"],
        ),
    }
    complexity = PlanService._calculate_complexity(group, req_map)
    assert complexity == 8.0


def test_assess_risk_unit():
    group = ["REQ-001"]
    req_map = {"REQ-001": Requirement(key="REQ-001", priority="critical")}
    assert PlanService._assess_risk(group, req_map) == "critical"

    req_map = {"REQ-001": Requirement(key="REQ-001", priority="high")}
    assert PlanService._assess_risk(group, req_map) == "high"

    group = ["REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005", "REQ-006"]
    req_map = {f"REQ-{i:03d}": Requirement(key=f"REQ-{i:03d}", priority="low") for i in range(1, 7)}
    assert PlanService._assess_risk(group, req_map) == "high"


def test_estimate_duration_unit():
    group = ["REQ-001"]
    req_map = {
        "REQ-001": Requirement(
            key="REQ-001",
            priority="high",
            dependencies=["DEP-001", "DEP-002"],
        )
    }
    complexity = 5.0
    duration = PlanService._estimate_duration(group, req_map, complexity)
    assert duration == 12.0


def test_generate_checklist_phases_unit():
    checklist_phases = PlanService._generate_checklist_phases(2)
    assert len(checklist_phases) == 2
    assert checklist_phases[0]["phase_id"] == "PH-03"
    assert "Quality Assurance" in checklist_phases[0]["title"]
    assert checklist_phases[1]["phase_id"] == "PH-04"
    assert "Deployment" in checklist_phases[1]["title"]
    assert checklist_phases[0]["dependencies"] == ["PH-02"]
    assert checklist_phases[1]["dependencies"] == ["PH-03"]

