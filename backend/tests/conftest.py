"""Test fixtures for integration-style tests.

Modified to lazily import application modules so that unit tests
in backend/tests/unit_tests can run without triggering external
connections during module import.
"""

import sys
import uuid
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure `backend` is on sys.path so `import app` works when running from repo root
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Test database (SQLite in-memory for speed)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a new database session for a test (SQLite in-memory).

    Lazy-import Base to avoid importing the app at module load time.
    """
    from app.core.database import Base  # lazy import

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Create a test client with overridden dependencies.

    Lazy-import FastAPI app and get_db to avoid side effects at module import.
    """
    from app.core.database import get_db  # lazy import
    from app.main import app  # lazy import

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project(db_session: Session):
    """Create a sample project for testing (lazy imports)."""
    from app.models import Project, ProjectState  # lazy import

    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project for requirements",
        status=ProjectState.DRAFT,
        context="Testing context for refinement",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def sample_requirements_data():
    """Sample requirements data for testing."""
    return [
        {
            "key": "REQ-001",
            "title": "User Authentication",
            "description": "Implement secure user authentication system with OAuth2 support",
            "priority": "high",
            "acceptance_criteria": [
                "Users can register with email",
                "Users can login with credentials",
                "Password reset functionality works",
                "OAuth2 integration with Google",
            ],
            "dependencies": [],
            "metadata": {"category": "security", "effort": "high"},
        },
        {
            "key": "REQ-002",
            "title": "Dashboard",
            "description": "Create comprehensive user dashboard",
            "priority": "medium",
            "acceptance_criteria": ["Display user statistics", "Show recent activity"],
            "dependencies": ["REQ-001"],
            "metadata": {"category": "ui", "effort": "medium"},
        },
        {
            "key": "REQ-003",
            "title": "API Rate Limiting",
            "description": "Implement rate limiting",
            "priority": "critical",
            "acceptance_criteria": ["Limit requests per IP", "Configurable limits"],
            "dependencies": [],
            "metadata": {"category": "security"},
        },
    ]
