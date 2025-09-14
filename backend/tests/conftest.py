# backend/tests/conftest.py
import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app
from app.models import Project, ProjectStatus
import uuid

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Create a test client with overridden dependencies."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def sample_project(db_session: Session) -> Project:
    """Create a sample project for testing."""
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project for requirements",
        status=ProjectStatus.DRAFT,
        context="Testing context"
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
            "description": "Implement user authentication system",
            "priority": "high",
            "acceptance_criteria": [
                "Users can register with email",
                "Users can login with credentials",
                "Password reset functionality"
            ],
            "dependencies": [],
            "metadata": {"category": "security"}
        },
        {
            "key": "REQ-002",
            "title": "Dashboard",
            "description": "Create user dashboard",
            "priority": "medium",
            "acceptance_criteria": [
                "Display user statistics",
                "Show recent activity"
            ],
            "dependencies": ["REQ-001"],
            "metadata": {"category": "ui"}
        }
    ]