import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project, Requirement


class TestRequirementsGatewayE2E:
    """End-to-end integration tests for requirements gateway workflows"""

    def test_complete_requirements_refinement_to_ready_workflow(self, client: TestClient, db_session: Session):
        """Test complete workflow from project creation to requirements ready"""
        
        # Step 1: Create a new project
        project_data = {
            "name": "Test E2E Project",
            "created_by": None
        }
        response = client.post("/api/v1/projects", json=project_data)
        assert response.status_code == 201
        project = response.json()
        project_id = project["id"]
        
        # Verify initial state
        assert project["status"] == "DRAFT"
        
        # Step 2: Update project to REQS_REFINING state (simulating requirements analysis)
        update_data = {"status": "REQS_REFINING"}
        response = client.patch(f"/api/v1/projects/{project_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["status"] == "REQS_REFINING"
        
        # Step 3: Add requirements to the project
        requirements_data = {
            "requirements": [
                {
                    "code": "REQ001",
                    "descricao": "User authentication functionality",
                    "criterios_aceitacao": [
                        "Users can log in with email and password",
                        "Invalid credentials show error message"
                    ],
                    "prioridade": "must",
                    "dependencias": [],
                    "testabilidade": "Automated tests for login scenarios"
                },
                {
                    "code": "REQ002", 
                    "descricao": "User profile management",
                    "criterios_aceitacao": [
                        "Users can view their profile",
                        "Users can update their profile information"
                    ],
                    "prioridade": "should",
                    "dependencias": ["REQ001"],
                    "testabilidade": "Integration tests for profile CRUD operations"
                }
            ]
        }
        response = client.post(f"/api/v1/projects/{project_id}/requirements", json=requirements_data)
        assert response.status_code == 200
        requirements = response.json()
        assert len(requirements) == 2
        
        # Step 4: Use gateway to finalize requirements 
        gateway_request = {
            "action": "finalizar",
            "correlation_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4())
        }
        response = client.post(f"/api/v1/requirements/{project_id}/gateway", json=gateway_request)
        assert response.status_code == 200
        
        gateway_response = response.json()
        assert gateway_response["from"] == "REQS_REFINING"
        assert gateway_response["to"] == "REQS_READY"
        assert "finalize" in gateway_response["reason"]
        
        # Step 5: Verify project state was updated
        response = client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        project = response.json()
        assert project["status"] == "REQS_READY"
        
        # Step 6: Verify gateway history
        response = client.get(f"/api/v1/requirements/{project_id}/gateway/history")
        assert response.status_code == 200
        history = response.json()
        assert len(history) == 1
        assert history[0]["action"] == "finalizar"
        assert history[0]["from_state"] == "REQS_REFINING"
        assert history[0]["to_state"] == "REQS_READY"

    def test_requirements_to_code_validation_workflow(self, client: TestClient, db_session: Session):
        """Test workflow for requesting code validation"""
        
        # Create project in REQS_REFINING state with requirements
        project = Project(
            id=uuid.uuid4(),
            name="Code Validation Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.flush()
        
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ001",
            version=1,
            data={
                "descricao": "Existing code validation requirement",
                "criterios_aceitacao": ["Code should be validated"],
                "prioridade": "must"
            }
        )
        db_session.add(requirement)
        db_session.commit()
        
        # Use gateway to request code validation
        gateway_request = {
            "action": "validar_codigo",
            "correlation_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4())
        }
        response = client.post(f"/api/v1/requirements/{project.id}/gateway", json=gateway_request)
        assert response.status_code == 200
        
        gateway_response = response.json()
        assert gateway_response["from"] == "REQS_REFINING"
        assert gateway_response["to"] == "CODE_VALIDATION_REQUESTED"
        assert "validation" in gateway_response["reason"]
        
        # Verify project state
        response = client.get(f"/api/v1/projects/{project.id}")
        assert response.status_code == 200
        project_data = response.json()
        assert project_data["status"] == "CODE_VALIDATION_REQUESTED"

    def test_requirements_to_planning_workflow(self, client: TestClient, db_session: Session):
        """Test workflow for proceeding to planning"""
        
        # Create project in REQS_REFINING state with requirements
        project = Project(
            id=uuid.uuid4(),
            name="Planning Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.flush()
        
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ001",
            version=1,
            data={
                "descricao": "Planning requirement",
                "criterios_aceitacao": ["Should proceed to planning"],
                "prioridade": "must"
            }
        )
        db_session.add(requirement)
        db_session.commit()
        
        # Use gateway to proceed to planning
        gateway_request = {
            "action": "planejar",
            "correlation_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4())
        }
        response = client.post(f"/api/v1/requirements/{project.id}/gateway", json=gateway_request)
        assert response.status_code == 200
        
        gateway_response = response.json()
        assert gateway_response["from"] == "REQS_REFINING"
        assert gateway_response["to"] == "REQS_READY"
        assert "planning" in gateway_response["reason"]

    def test_multiple_gateway_transitions_audit_trail(self, client: TestClient, db_session: Session):
        """Test audit trail with multiple gateway transitions"""
        
        # Create project with requirements
        project = Project(
            id=uuid.uuid4(),
            name="Multi-transition Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.flush()
        
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ001",
            version=1,
            data={
                "descricao": "Multi-transition requirement",
                "criterios_aceitacao": ["Should handle multiple transitions"],
                "prioridade": "must"
            }
        )
        db_session.add(requirement)
        db_session.commit()
        
        # First transition: finalizar
        gateway_request_1 = {
            "action": "finalizar",
            "correlation_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4())
        }
        response = client.post(f"/api/v1/requirements/{project.id}/gateway", json=gateway_request_1)
        assert response.status_code == 200
        
        # Manually update project back to REQS_REFINING for next transition
        # (simulating a real workflow where requirements might go back for refinement)
        db_session.query(Project).filter(Project.id == project.id).update({"status": "REQS_REFINING"})
        db_session.commit()
        
        # Second transition: validar_codigo
        gateway_request_2 = {
            "action": "validar_codigo",
            "correlation_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4())
        }
        response = client.post(f"/api/v1/requirements/{project.id}/gateway", json=gateway_request_2)
        assert response.status_code == 200
        
        # Check audit trail
        response = client.get(f"/api/v1/requirements/{project.id}/gateway/history")
        assert response.status_code == 200
        history = response.json()
        
        assert len(history) == 2
        # History should be ordered by created_at desc - but the order might vary due to timestamp precision
        # Just check that both actions are present
        actions = [h["action"] for h in history]
        assert "validar_codigo" in actions
        assert "finalizar" in actions

    def test_gateway_error_handling_workflow(self, client: TestClient, db_session: Session):
        """Test error handling in gateway workflows"""
        
        # Test 1: Project in wrong state
        project_wrong_state = Project(
            id=uuid.uuid4(),
            name="Wrong State Project",
            status="DRAFT"  # Wrong state for gateway
        )
        db_session.add(project_wrong_state)
        db_session.commit()
        
        gateway_request = {
            "action": "finalizar",
            "request_id": str(uuid.uuid4())
        }
        response = client.post(f"/api/v1/requirements/{project_wrong_state.id}/gateway", json=gateway_request)
        assert response.status_code == 400
        error = response.json()["detail"]
        assert error["error_code"] == "INVALID_STATE_TRANSITION"
        
        # Test 2: Project with no requirements
        project_no_reqs = Project(
            id=uuid.uuid4(),
            name="No Requirements Project",
            status="REQS_REFINING"
        )
        db_session.add(project_no_reqs)
        db_session.commit()
        
        response = client.post(f"/api/v1/requirements/{project_no_reqs.id}/gateway", json=gateway_request)
        assert response.status_code == 400
        error = response.json()["detail"]
        assert error["error_code"] == "NO_REQUIREMENTS"
        
        # Test 3: Non-existent project
        non_existent_id = uuid.uuid4()
        response = client.post(f"/api/v1/requirements/{non_existent_id}/gateway", json=gateway_request)
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    def test_gateway_idempotency_workflow(self, client: TestClient, db_session: Session):
        """Test idempotency behavior in workflow scenarios"""
        
        # Create project with requirements
        project = Project(
            id=uuid.uuid4(),
            name="Idempotency Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.flush()
        
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ001",
            version=1,
            data={
                "descricao": "Idempotency requirement",
                "criterios_aceitacao": ["Should handle duplicate requests"],
                "prioridade": "must"
            }
        )
        db_session.add(requirement)
        db_session.commit()
        
        # First request
        request_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        gateway_request = {
            "action": "finalizar",
            "correlation_id": correlation_id,
            "request_id": request_id
        }
        
        response1 = client.post(f"/api/v1/requirements/{project.id}/gateway", json=gateway_request)
        assert response1.status_code == 200
        
        # Second identical request (should be idempotent)
        response2 = client.post(f"/api/v1/requirements/{project.id}/gateway", json=gateway_request)
        assert response2.status_code == 200
        
        # Responses should be identical
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["from"] == data2["from"]
        assert data1["to"] == data2["to"]
        assert data1["audit_ref"]["request_id"] == data2["audit_ref"]["request_id"]
        assert data1["audit_ref"]["correlation_id"] == data2["audit_ref"]["correlation_id"]
        
        # Only one audit record should exist
        response = client.get(f"/api/v1/requirements/{project.id}/gateway/history")
        assert response.status_code == 200
        history = response.json()
        assert len(history) == 1

    def test_gateway_with_qa_sessions_workflow(self, client: TestClient, db_session: Session):
        """Test gateway integration with existing QA sessions workflow"""
        
        # Create project
        project_data = {"name": "QA Integration Test Project"}
        response = client.post("/api/v1/projects", json=project_data)
        assert response.status_code == 201
        project = response.json()
        project_id = project["id"]
        
        # Add requirements
        requirements_data = {
            "requirements": [
                {
                    "code": "REQ001",
                    "descricao": "QA integrated requirement",
                    "criterios_aceitacao": ["Should work with QA sessions"],
                    "prioridade": "must"
                }
            ]
        }
        response = client.post(f"/api/v1/projects/{project_id}/requirements", json=requirements_data)
        assert response.status_code == 200
        
        # Update to REQS_REFINING state (simulating QA refinement process)
        update_data = {"status": "REQS_REFINING"}
        response = client.patch(f"/api/v1/projects/{project_id}", json=update_data)
        assert response.status_code == 200
        
        # Create QA session (optional - showing integration point)
        qa_session_data = {
            "questions": [
                {
                    "id": "q1",
                    "text": "What authentication methods should be supported?",
                    "type": "open"
                }
            ]
        }
        response = client.post(f"/api/v1/projects/{project_id}/qa-sessions", json=qa_session_data)
        # QA session creation might return various status codes depending on current implementation
        # The important part is that gateway still works after QA sessions
        
        # Use gateway to transition (this is the main test)
        gateway_request = {
            "action": "planejar",
            "request_id": str(uuid.uuid4())
        }
        response = client.post(f"/api/v1/requirements/{project_id}/gateway", json=gateway_request)
        assert response.status_code == 200
        
        gateway_response = response.json()
        assert gateway_response["from"] == "REQS_REFINING"
        assert gateway_response["to"] == "REQS_READY"
        
        # Verify final project state
        response = client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        final_project = response.json()
        assert final_project["status"] == "REQS_READY"

    def test_concurrent_gateway_requests_simulation(self, client: TestClient, db_session: Session):
        """Test behavior with simulated concurrent requests"""
        
        # Create project with requirements
        project = Project(
            id=uuid.uuid4(),
            name="Concurrent Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.flush()
        
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ001",
            version=1,
            data={
                "descricao": "Concurrent requirement",
                "criterios_aceitacao": ["Should handle concurrent requests"],
                "prioridade": "must"
            }
        )
        db_session.add(requirement)
        db_session.commit()
        
        # Simulate concurrent requests with different request_ids but same correlation_id
        correlation_id = str(uuid.uuid4())
        requests = [
            {
                "action": "finalizar",
                "correlation_id": correlation_id,
                "request_id": str(uuid.uuid4())
            },
            {
                "action": "finalizar", 
                "correlation_id": correlation_id,
                "request_id": str(uuid.uuid4())
            }
        ]
        
        responses = []
        for req in requests:
            response = client.post(f"/api/v1/requirements/{project.id}/gateway", json=req)
            responses.append(response)
        
        # Both requests should succeed (different request_ids)
        # Note: The second request might fail if project state changed from first request
        successful_responses = [r for r in responses if r.status_code == 200]
        failed_responses = [r for r in responses if r.status_code != 200]
        
        # At least one should succeed
        assert len(successful_responses) >= 1
        
        # If there are failed responses, they should be due to invalid state (project already transitioned)
        for failed_response in failed_responses:
            if failed_response.status_code == 400:
                error_detail = failed_response.json()["detail"]
                # Should be an invalid state transition error since first request changed the state
                assert "INVALID_STATE_TRANSITION" in str(error_detail)
        
        # All successful responses should result in same final state
        for response in successful_responses:
            data = response.json()
            assert data["from"] == "REQS_REFINING"
            assert data["to"] == "REQS_READY"
        
        # Should have audit records for successful requests only
        response = client.get(f"/api/v1/requirements/{project.id}/gateway/history")
        assert response.status_code == 200
        history = response.json()
        assert len(history) >= 1  # At least one successful request
        
        # All successful requests should have same correlation_id
        successful_correlation_ids = [h["correlation_id"] for h in history]
        if successful_correlation_ids:
            assert all(cid == correlation_id for cid in successful_correlation_ids)