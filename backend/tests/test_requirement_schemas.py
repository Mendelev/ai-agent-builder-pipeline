# backend/tests/test_requirement_schemas.py
import pytest
from pydantic import ValidationError

from app.schemas.requirement import (
    ExportFormat,
    RequirementBase,
    RequirementBulkCreate,
    RequirementCreate,
    RequirementUpdate,
)


def test_requirement_base_validation():
    """Test RequirementBase validation."""
    # Valid requirement
    req = RequirementBase(
        key="REQ-001", title="Test Requirement", priority="high", acceptance_criteria=["Criterion 1", "Criterion 2"]
    )
    assert req.key == "REQ-001"
    assert req.title == "Test Requirement"
    assert req.priority == "high"


def test_requirement_base_invalid_key():
    """Test RequirementBase with invalid key pattern."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementBase(key="invalid key", title="Test")  # Contains space, should fail
    assert "String should match pattern" in str(exc_info.value)


def test_requirement_base_critical_without_acceptance_criteria():
    """Test critical priority requirement without acceptance criteria."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementBase(
            key="REQ-001",
            title="Critical Requirement",
            priority="critical",
            acceptance_criteria=[],  # Empty, should fail for critical
        )
    assert "High/critical priority requirements must have acceptance criteria" in str(exc_info.value)


def test_requirement_base_high_without_acceptance_criteria():
    """Test high priority requirement without acceptance criteria."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementBase(
            key="REQ-001",
            title="High Priority Requirement",
            priority="high",
            acceptance_criteria=[],  # Empty, should fail for high
        )
    assert "High/critical priority requirements must have acceptance criteria" in str(exc_info.value)


def test_requirement_base_medium_without_acceptance_criteria():
    """Test medium priority requirement without acceptance criteria (should pass)."""
    req = RequirementBase(
        key="REQ-001",
        title="Medium Priority Requirement",
        priority="medium",
        acceptance_criteria=[],  # Empty is OK for medium/low priority
    )
    assert req.priority == "medium"
    assert req.acceptance_criteria == []


def test_requirement_create_defaults():
    """Test RequirementCreate default values."""
    req = RequirementCreate(key="REQ-001", title="Test Requirement")
    assert req.is_coherent is True
    assert req.priority == "medium"
    assert req.acceptance_criteria == []
    assert req.dependencies == []
    assert req.metadata == {}


def test_requirement_update_partial():
    """Test RequirementUpdate with partial data."""
    req = RequirementUpdate(title="Updated Title", priority="high")
    assert req.title == "Updated Title"
    assert req.priority == "high"
    assert req.description is None


def test_requirement_update_empty():
    """Test RequirementUpdate with no data."""
    req = RequirementUpdate()
    assert req.title is None
    assert req.description is None
    assert req.priority is None


def test_export_format_enum():
    """Test ExportFormat enum values."""
    export = ExportFormat(format="json")
    assert export.format == "json"

    export = ExportFormat(format="md")
    assert export.format == "md"


def test_requirement_bulk_create_empty():
    """Test RequirementBulkCreate with empty requirements."""
    # Empty list is allowed, this test should not expect failure
    bulk = RequirementBulkCreate(requirements=[])
    assert bulk.requirements == []


def test_requirement_bulk_create_too_many():
    """Test RequirementBulkCreate with too many requirements."""
    requirements = []
    for i in range(101):  # More than max allowed (100)
        requirements.append(RequirementCreate(key=f"REQ-{i:03d}", title=f"Requirement {i}"))

    with pytest.raises(ValidationError) as exc_info:
        RequirementBulkCreate(requirements=requirements)
    assert "Maximum 100 requirements per bulk operation" in str(exc_info.value)
