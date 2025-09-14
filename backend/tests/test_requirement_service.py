# backend/tests/test_requirement_service.py
import pytest
from sqlalchemy.orm import Session
from app.services.requirement_service import RequirementService
from app.models import Project, Requirement, ProjectStatus
from app.schemas.requirement import RequirementCreate
import uuid

def test_validate_dag_no_cycles():
    """Test DAG validation with no cycles."""
    requirements = [
        Requirement(key="A", dependencies=[]),
        Requirement(key="B", dependencies=["A"]),
        Requirement(key="C", dependencies=["A", "B"]),
    ]
    
    assert RequirementService.validate_dag(requirements) is True

def test_validate_dag_with_cycle():
    """Test DAG validation with cycles."""
    requirements = [
        Requirement(key="A", dependencies=["C"]),
        Requirement(key="B", dependencies=["A"]),
        Requirement(key="C", dependencies=["B"]),
    ]
    
    assert RequirementService.validate_dag(requirements) is False

def test_export_json_format():
    """Test JSON export format."""
    req = Requirement(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        key="TEST-001",
        title="Test Requirement",
        description="Test description",
        priority="high",
        acceptance_criteria=["Criterion 1", "Criterion 2"],
        dependencies=["DEP-001"],
        is_coherent=True
    )
    
    result = RequirementService.export_json([req])
    
    assert "requirements" in result
    assert len(result["requirements"]) == 1
    assert result["requirements"][0]["key"] == "TEST-001"
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
            is_coherent=True
        ),
        Requirement(
            key="LOW-001",
            title="Low Priority Task",
            priority="low",
            is_coherent=False
        )
    ]
    
    result = RequirementService.export_markdown(reqs)
    
    assert "# Requirements" in result
    assert "## High Priority" in result
    assert "## Low Priority" in result
    assert "HIGH-001" in result
    assert "✅ **Validated**" in result
    assert "⚠️ **Needs refinement**" in result

def test_create_bulk_update_existing(db_session: Session, sample_project: Project):
    """Test bulk create updates existing requirements."""
    # Create initial requirement
    req_data = RequirementCreate(
        key="UPDATE-001",
        title="Original Title",
        priority="low"
    )
    RequirementService.create_bulk(db_session, sample_project.id, [req_data])
    
    # Update with new data
    updated_data = RequirementCreate(
        key="UPDATE-001",
        title="Updated Title",
        priority="high",
        acceptance_criteria=["New criterion"]
    )
    result = RequirementService.create_bulk(db_session, sample_project.id, [updated_data])
    
    assert len(result) == 1
    assert result[0].title == "Updated Title"
    assert result[0].priority == "high"
    assert len(result[0].acceptance_criteria) == 1