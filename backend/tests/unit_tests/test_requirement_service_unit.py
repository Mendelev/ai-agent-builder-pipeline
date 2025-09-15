# Unit tests for RequirementService using only in-memory objects and mocks
import uuid
from app.services.requirement_service import RequirementService
from app.models import Requirement


def test_validate_dag_no_cycles_unit():
    requirements = [
        Requirement(key="A", dependencies=[]),
        Requirement(key="B", dependencies=["A"]),
        Requirement(key="C", dependencies=["A", "B"]),
        Requirement(key="D", dependencies=["B", "C"]),
    ]
    assert RequirementService.validate_dag(requirements) is True


def test_validate_dag_with_simple_cycle_unit():
    requirements = [
        Requirement(key="A", dependencies=["B"]),
        Requirement(key="B", dependencies=["A"]),
    ]
    assert RequirementService.validate_dag(requirements) is False


def test_validate_dag_with_complex_cycle_unit():
    requirements = [
        Requirement(key="A", dependencies=["C"]),
        Requirement(key="B", dependencies=["A"]),
        Requirement(key="C", dependencies=["D"]),
        Requirement(key="D", dependencies=["B"]),
    ]
    assert RequirementService.validate_dag(requirements) is False


def test_validate_dag_missing_dependency_unit():
    requirements = [
        Requirement(key="A", dependencies=["B"]),
        Requirement(key="C", dependencies=["A"]),
    ]
    assert RequirementService.validate_dag(requirements) is False


def test_export_json_format_unit():
    req1 = Requirement(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        key="TEST-001",
        title="Test Requirement",
        description="Test description",
        priority="high",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        dependencies=["DEP-001"],
        is_coherent=True,
    )
    req2 = Requirement(
        id=uuid.uuid4(),
        project_id=req1.project_id,
        key="TEST-002",
        title="Another Requirement",
        priority="low",
        is_coherent=False,
    )

    result = RequirementService.export_json([req1, req2])
    assert "requirements" in result
    assert len(result["requirements"]) == 2
    assert result["total"] == 2
    assert result["requirements"][0]["key"] == "TEST-001"
    assert result["requirements"][0]["is_coherent"] is True
    assert result["requirements"][1]["is_coherent"] is False
    assert "exported_at" in result


def test_export_markdown_format_unit():
    reqs = [
        Requirement(
            key="HIGH-001",
            title="High Priority Task",
            description="Important task",
            priority="high",
            acceptance_criteria=["Must do X", "Must do Y"],
            dependencies=["REQ-001"],
            is_coherent=True,
        ),
        Requirement(
            key="CRIT-001",
            title="Critical Task",
            priority="critical",
            is_coherent=True,
        ),
        Requirement(
            key="LOW-001",
            title="Low Priority Task",
            priority="low",
            is_coherent=False,
        ),
    ]

    result = RequirementService.export_markdown(reqs)
    assert "# Requirements Export" in result
    assert "## Critical Priority" in result
    assert "## High Priority" in result
    assert "## Low Priority" in result
    assert "[HIGH-001]" in result
    assert "[CRIT-001]" in result
    assert "✅ Validated" in result
    assert "⚠️ Needs refinement" in result
    assert "**Dependencies:** `REQ-001`" in result

