# backend/tests/test_requirement_service.py
import uuid

import pytest
from sqlalchemy.orm import Session

from app.models import Project, Requirement, RequirementIteration
from app.schemas.requirement import RequirementCreate
from app.services.requirement_service import RequirementService


def test_validate_dag_no_cycles():
    """Test DAG validation with valid dependencies."""
    requirements = [
        Requirement(key="A", dependencies=[]),
        Requirement(key="B", dependencies=["A"]),
        Requirement(key="C", dependencies=["A", "B"]),
        Requirement(key="D", dependencies=["B", "C"]),
    ]

    assert RequirementService.validate_dag(requirements) is True


def test_validate_dag_with_simple_cycle():
    """Test DAG validation detects simple cycle."""
    requirements = [Requirement(key="A", dependencies=["B"]), Requirement(key="B", dependencies=["A"])]

    assert RequirementService.validate_dag(requirements) is False


def test_validate_dag_with_complex_cycle():
    """Test DAG validation detects complex cycle."""
    requirements = [
        Requirement(key="A", dependencies=["C"]),
        # backend/tests/test_requirement_service.py (continued)
        Requirement(key="B", dependencies=["A"]),
        Requirement(key="C", dependencies=["D"]),
        Requirement(key="D", dependencies=["B"]),
    ]

    assert RequirementService.validate_dag(requirements) is False


def test_validate_dag_missing_dependency():
    """Test DAG validation with missing dependency."""
    requirements = [Requirement(key="A", dependencies=["B"]), Requirement(key="C", dependencies=["A"])]

    # B doesn't exist
    assert RequirementService.validate_dag(requirements) is False


def test_export_json_format():
    """Test JSON export format."""
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


def test_export_markdown_format():
    """Test Markdown export format."""
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
        Requirement(key="CRIT-001", title="Critical Task", priority="critical", is_coherent=True),
        Requirement(key="LOW-001", title="Low Priority Task", priority="low", is_coherent=False),
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


def test_create_bulk_creates_iterations(db_session: Session, sample_project: Project):
    """Test bulk create generates iteration records."""
    req_data = [RequirementCreate(key="ITER-001", title="Test Requirement", priority="medium")]

    # Create requirement
    requirements = RequirementService.create_bulk(db_session, sample_project.id, req_data)

    # Check iteration was created
    iteration = (
        db_session.query(RequirementIteration).filter(RequirementIteration.requirement_id == requirements[0].id).first()
    )

    assert iteration is not None
    assert iteration.version == 1
    assert iteration.changes["action"] == "created"


def test_create_bulk_update_increments_version(db_session: Session, sample_project: Project):
    """Test updating requirement increments iteration version."""
    req_data = RequirementCreate(key="UPDATE-001", title="Original Title", priority="low")

    # Create initial
    RequirementService.create_bulk(db_session, sample_project.id, [req_data])

    # Update
    updated_data = RequirementCreate(
        key="UPDATE-001", title="Updated Title", priority="high", acceptance_criteria=["New criterion"]
    )
    RequirementService.create_bulk(db_session, sample_project.id, [updated_data])

    # Check iterations
    iterations = (
        db_session.query(RequirementIteration)
        .filter(
            RequirementIteration.requirement_id.in_(
                db_session.query(Requirement.id).filter(Requirement.key == "UPDATE-001")
            )
        )
        .order_by(RequirementIteration.version)
        .all()
    )

    assert len(iterations) == 2
    assert iterations[0].version == 1
    assert iterations[1].version == 2
    assert "title" in iterations[1].changes
    assert iterations[1].changes["title"]["old"] == "Original Title"
    assert iterations[1].changes["title"]["new"] == "Updated Title"


def test_finalize_validates_acceptance_criteria(db_session: Session, sample_project: Project):
    """Test finalize checks high/critical requirements have acceptance criteria."""
    # Create high priority requirement without criteria
    req = Requirement(
        project_id=sample_project.id,
        key="HIGH-001",
        title="High Priority",
        priority="high",
        acceptance_criteria=[],
        is_coherent=True,
    )
    db_session.add(req)
    db_session.commit()

    with pytest.raises(ValueError) as exc:
        RequirementService.finalize_requirements(db_session, sample_project.id, force=False)

    assert "missing acceptance criteria" in str(exc.value).lower()
