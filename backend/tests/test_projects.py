import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app

# Test database
SQLALCHEMY_DATABASE_URL = "postgresql://test:test@localhost:5432/test_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_create_project():
    response = client.post(
        "/projects",
        json={"name": "Test Project"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["status"] == "DRAFT"
    assert "id" in data


def test_list_projects():
    # Create projects
    client.post("/projects", json={"name": "Project 1"})
    client.post("/projects", json={"name": "Project 2"})
    
    response = client.get("/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_project():
    create_response = client.post("/projects", json={"name": "Test Project"})
    project_id = create_response.json()["id"]
    
    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Project"


def test_get_project_not_found():
    response = client.get("/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_update_project():
    create_response = client.post("/projects", json={"name": "Old Name"})
    project_id = create_response.json()["id"]
    
    response = client.patch(
        f"/projects/{project_id}",
        json={"name": "New Name", "status": "REQS_REFINING"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["status"] == "REQS_REFINING"


def test_bulk_upsert_requirements():
    create_response = client.post("/projects", json={"name": "Test Project"})
    project_id = create_response.json()["id"]
    
    requirements_data = {
        "requirements": [
            {
                "code": "REQ-001",
                "descricao": "First requirement",
                "criterios_aceitacao": ["Criteria 1"],
                "prioridade": "HIGH",
                "dependencias": []
            },
            {
                "code": "REQ-002",
                "descricao": "Second requirement",
                "criterios_aceitacao": ["Criteria 1", "Criteria 2"],
                "prioridade": "MEDIUM",
                "dependencias": ["REQ-001"]
            }
        ]
    }
    
    response = client.post(
        f"/projects/{project_id}/requirements",
        json=requirements_data
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["version"] == 1
    assert data[1]["version"] == 1


def test_update_requirement_creates_version():
    # Create project and requirement
    create_response = client.post("/projects", json={"name": "Test Project"})
    project_id = create_response.json()["id"]
    
    req_response = client.post(
        f"/projects/{project_id}/requirements",
        json={
            "requirements": [{
                "code": "REQ-001",
                "descricao": "Original description",
                "criterios_aceitacao": [],
                "prioridade": "LOW",
                "dependencias": []
            }]
        }
    )
    requirement_id = req_response.json()[0]["id"]
    
    # Update requirement
    update_response = client.put(
        f"/projects/requirements/{requirement_id}",
        json={
            "code": "REQ-001",
            "descricao": "Updated description",
            "criterios_aceitacao": ["New criteria"],
            "prioridade": "HIGH",
            "dependencias": []
        }
    )
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["version"] == 2
    assert updated_data["data"]["descricao"] == "Updated description"


def test_get_requirement_versions():
    # Create and update requirement
    create_response = client.post("/projects", json={"name": "Test Project"})
    project_id = create_response.json()["id"]
    
    req_response = client.post(
        f"/projects/{project_id}/requirements",
        json={
            "requirements": [{
                "code": "REQ-001",
                "descricao": "Version 1",
                "criterios_aceitacao": [],
                "prioridade": "LOW",
                "dependencias": []
            }]
        }
    )
    requirement_id = req_response.json()[0]["id"]
    
    # Update to create version 2
    client.put(
        f"/projects/requirements/{requirement_id}",
        json={
            "code": "REQ-001",
            "descricao": "Version 2",
            "criterios_aceitacao": [],
            "prioridade": "MEDIUM",
            "dependencias": []
        }
    )
    
    # Get versions
    versions_response = client.get(f"/projects/requirements/{requirement_id}/versions")
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert len(versions) == 1  # Only archived versions
    assert versions[0]["version"] == 1


def test_invalid_priority_validation():
    create_response = client.post("/projects", json={"name": "Test Project"})
    project_id = create_response.json()["id"]
    
    response = client.post(
        f"/projects/{project_id}/requirements",
        json={
            "requirements": [{
                "code": "REQ-001",
                "descricao": "Test",
                "prioridade": "INVALID",
                "criterios_aceitacao": [],
                "dependencias": []
            }]
        }
    )
    assert response.status_code == 422
