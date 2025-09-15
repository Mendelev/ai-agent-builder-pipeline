# Unit tests for PromptService helper logic without DB/API
from app.services.prompt_service import PromptService
from app.utils.security import remove_secrets, sanitize_content
from app.models import PlanPhase, Requirement


def test_remove_secrets_unit():
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


def test_sanitize_nested_content_unit():
    data = {
        "config": {
            "api_key": "secret123",
            "database": "postgresql://user:password@host/db",
        },
        "tokens": ["Bearer abc123", "token=xyz789"],
    }
    sanitized = sanitize_content(data)
    s = str(sanitized)
    assert "secret123" not in s
    assert "password" not in s
    assert "abc123" not in s
    assert "xyz789" not in s


def test_generate_phase_prompt_unit():
    phase = PlanPhase(
        phase_id="PH-01",
        sequence=1,
        title="Implementation Phase",
        objective="Implement core features",
        estimated_days=15.0,
        activities=["Design", "Implement", "Test"],
        deliverables=["Feature A", "Feature B"],
        definition_of_done=["All tests pass", "Meets requirements"],
        risk_level="HIGH",
    )
    requirements = [
        Requirement(
            key="REQ-001",
            title="Feature A",
            description="Implement feature A",
            acceptance_criteria=["AC1", "AC2"],
        ),
        Requirement(
            key="REQ-002",
            title="Feature B",
            description="Implement feature B",
            acceptance_criteria=["Performance < 100ms"],
            dependencies=["REQ-001"],
        ),
    ]
    project = type("Project", (), {"name": "Demo Project"})()
    prompt = PromptService._generate_phase_prompt(phase, requirements, project, include_code=True)
    assert "# PH-01: Implementation Phase" in prompt
    assert "## Objective" in prompt
    assert "## Inputs" in prompt
    assert "[REQ-001] Feature A" in prompt
    assert "## Tasks" in prompt
    assert "## Expected Deliverables" in prompt
    assert "## Output Format" in prompt
    assert "### Code Structure" in prompt
    assert "## Definition of Done" in prompt
    assert "## Risks & Mitigations" in prompt
    assert "HIGH" in prompt
    assert "## Common Errors to Avoid" in prompt
    assert "## Validation Checklist" in prompt
    assert "## Notes" in prompt
    assert "15.0 days" in prompt


def test_detect_tech_stack_unit():
    requirements = [
        Requirement(title="FastAPI REST API", description="Build REST API using FastAPI framework"),
        Requirement(title="PostgreSQL Database", description="Use PostgreSQL for data persistence"),
        Requirement(title="Redis Caching", description="Implement Redis cache layer"),
    ]
    tech_stack = PromptService._detect_tech_stack(requirements)
    assert "Backend: Python/FastAPI" in tech_stack
    assert "Database: PostgreSQL" in tech_stack
    assert "Cache: Redis" in tech_stack


def test_common_errors_generation_unit():
    security_phase = PlanPhase(phase_id="PH-01", title="Security Implementation", objective="Implement security features")
    errors = PromptService._get_common_errors(security_phase, [])
    assert any("password" in e.lower() for e in errors)
    assert any("sql injection" in e.lower() for e in errors)

    api_phase = PlanPhase(phase_id="PH-02", title="API Development", objective="Build REST API")
    errors = PromptService._get_common_errors(api_phase, [])
    assert any("restful" in e.lower() for e in errors)
    assert any("versioning" in e.lower() for e in errors)
