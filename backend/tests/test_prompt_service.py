# backend/tests/test_prompt_service.py
import pytest
from sqlalchemy.orm import Session
from app.services.prompt_service import PromptService
from app.models import Project, Plan, PlanPhase, Requirement, PromptBundle
from app.schemas.prompt import PromptGenerateRequest
from app.utils.security import remove_secrets, sanitize_content
import uuid

def test_remove_secrets():
    """Test secret removal from content."""
    content = """
    API_KEY=sk-1234567890abcdef
    password: mysecretpass123
    AWS_SECRET=AKIAIOSFODNN7EXAMPLE
    Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
    mongodb://user:pass@localhost:27017/db
    """
    
    sanitized = remove_secrets(content)
    
    assert "sk-1234567890abcdef" not in sanitized
    assert "mysecretpass123" not in sanitized
    assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized
    assert "user:pass" not in sanitized
    
    assert "API_KEY=<REDACTED>" in sanitized
    assert "PASSWORD=<REDACTED>" in sanitized
    assert "Bearer <TOKEN>" in sanitized

def test_sanitize_nested_content():
    """Test sanitizing nested data structures."""
    data = {
        "config": {
            "api_key": "secret123",
            "database": "postgresql://user:password@host/db"
        },
        "tokens": ["Bearer abc123", "token=xyz789"]
    }
    
    sanitized = sanitize_content(data)
    
    assert "secret123" not in str(sanitized)
    assert "password" not in str(sanitized)
    assert "abc123" not in str(sanitized)
    assert "xyz789" not in str(sanitized)

def test_generate_context(db_session: Session, sample_project: Project):
    """Test context generation."""
    # Create plan and requirements
    plan = Plan(
        project_id=sample_project.id,
        version=1,
        source="requirements",
        total_duration_days=30.0,
        coverage_percentage=95.0,
        risk_score=0.5,
        constraints={
            "deadline_days": 90,
            "team_size": 5,
            "nfrs": ["Performance", "Security"]
        }
    )
    db_session.add(plan)
    db_session.flush()  # This assigns an ID to plan
    
    phase = PlanPhase(
        plan_id=plan.id,
        phase_id="PH-01",
        sequence=1,
        title="Phase 1",
        objective="Test",
        estimated_days=10.0
    )
    db_session.add(phase)
    
    requirements = [
        Requirement(
            project_id=sample_project.id,
            key="REQ-001",
            title="Critical Feature",
            priority="critical",
            is_coherent=True
        ),
        Requirement(
            project_id=sample_project.id,
            key="REQ-002",
            title="High Priority Feature",
            priority="high",
            is_coherent=True
        )
    ]
    for req in requirements:
        db_session.add(req)
    db_session.commit()
    
    # Generate context
    context = PromptService._generate_context(
        sample_project, plan, requirements, include_code=True
    )
    
    assert "# Project Context:" in context
    assert sample_project.name in context
    assert "## Domain & Objectives" in context
    assert "## Non-Functional Requirements" in context
    assert "Performance" in context
    assert "Security" in context
    assert "## Conventions & Standards" in context
    assert "REQ-###" in context
    assert "PH-##" in context
    assert "## Code Generation Guidelines" in context
    assert "## Technical Stack" in context
    assert "## Requirements Overview" in context
    assert "Critical: 1 requirements" in context
    assert "[REQ-001]" in context
    assert "## Execution Plan Summary" in context
    assert "30.0 days" in context
    assert "95.0%" in context
    assert "## Configuration Placeholders" in context

def test_generate_phase_prompt(db_session: Session, sample_project: Project):
    """Test phase prompt generation."""
    phase = PlanPhase(
        phase_id="PH-01",
        sequence=1,
        title="Implementation Phase",
        objective="Implement core features",
        deliverables=["Feature A", "Feature B"],
        activities=["Design", "Code", "Test"],
        dependencies=["PH-00"],
        estimated_days=15.0,
        risk_level="high",
        risks=["Complexity risk"],
        requirements_covered=["REQ-001", "REQ-002"],
        definition_of_done=["All tests pass", "Code reviewed"],
        resources_required={"developers": 3, "qa": 1}
    )
    
    requirements = [
        Requirement(
            key="REQ-001",
            title="Feature A",
            description="Implement feature A",
            acceptance_criteria=["Works as expected"],
            dependencies=[]
        ),
        Requirement(
            key="REQ-002",
            title="Feature B",
            description="Implement feature B",
            acceptance_criteria=["Performance < 100ms"],
            dependencies=["REQ-001"]
        )
    ]
    
    prompt = PromptService._generate_phase_prompt(
        phase, requirements, sample_project, include_code=True
    )
    
    assert "# PH-01: Implementation Phase" in prompt
    assert "## Objective" in prompt
    assert "Implement core features" in prompt
    assert "## Inputs" in prompt
    assert "[REQ-001] Feature A" in prompt
    assert "[REQ-002] Feature B" in prompt
    assert "## Tasks" in prompt
    assert "1. Design" in prompt
    assert "## Expected Deliverables" in prompt
    assert "Feature A" in prompt
    assert "## Output Format" in prompt
    assert "### Code Structure" in prompt
    assert "## Definition of Done" in prompt
    assert "[ ] All tests pass" in prompt
    assert "## Risks & Mitigations" in prompt
    assert "HIGH" in prompt
    assert "## Common Errors to Avoid" in prompt
    assert "## Validation Checklist" in prompt
    assert "## Notes" in prompt
    assert "15.0 days" in prompt

def test_detect_tech_stack():
    """Test technology stack detection."""
    requirements = [
        Requirement(
            title="FastAPI REST API",
            description="Build REST API using FastAPI framework"
        ),
        Requirement(
            title="PostgreSQL Database",
            description="Use PostgreSQL for data persistence"
        ),
        Requirement(
            title="Redis Caching",
            description="Implement Redis cache layer"
        )
    ]
    
    tech_stack = PromptService._detect_tech_stack(requirements)
    
    assert "Backend: Python/FastAPI" in tech_stack
    assert "Database: PostgreSQL" in tech_stack
    assert "Cache: Redis" in tech_stack

def test_common_errors_generation():
    """Test common errors generation for different phase types."""
    # Security phase
    security_phase = PlanPhase(
        phase_id="PH-01",
        title="Security Implementation",
        objective="Implement security features"
    )
    
    errors = PromptService._get_common_errors(security_phase, [])
    
    assert any("password" in e.lower() for e in errors)
    assert any("sql injection" in e.lower() for e in errors)
    
    # API phase
    api_phase = PlanPhase(
        phase_id="PH-02",
        title="API Development",
        objective="Build REST API"
    )
    
    errors = PromptService._get_common_errors(api_phase, [])
    
    assert any("restful" in e.lower() for e in errors)
    assert any("versioning" in e.lower() for e in errors)

def test_create_bundle_zip(db_session: Session, sample_project: Project):
    """Test ZIP bundle creation."""
    # Create bundle with prompts
    bundle = PromptBundle(
        project_id=sample_project.id,
        plan_id=uuid.uuid4(),
        version=1,
        context_md="# Context",
        total_prompts=1
    )
    db_session.add(bundle)
    db_session.flush()
    
    from app.models import PromptItem
    prompt = PromptItem(
        bundle_id=bundle.id,
        phase_id="PH-01",
        sequence=1,
        title="Phase 1",
        content_md="# Phase 1 Content"
    )
    db_session.add(prompt)
    db_session.commit()
    
    # Create ZIP
    zip_content = PromptService.create_bundle_zip(db_session, bundle.id)
    
    assert zip_content is not None
    assert len(zip_content) > 0
    
    # Verify ZIP structure
    import zipfile
    import io
    
    zip_data = io.BytesIO(zip_content)
    with zipfile.ZipFile(zip_data, 'r') as zip_file:
        files = zip_file.namelist()
        
        assert "context.md" in files
        assert "metadata.json" in files
        assert "README.md" in files
        assert any("prompts/" in f for f in files)
        
        # Check content
        context = zip_file.read("context.md").decode()
        assert "# Context" in context