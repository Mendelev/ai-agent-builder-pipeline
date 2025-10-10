import pytest
import uuid
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project, Requirement, RequirementsGatewayAudit
from app.services.gateway_service import GatewayService
from app.schemas.gateway import RequirementsGatewayRequest, GatewayActionEnum


class TestGatewayService:
    """Unit tests for GatewayService"""
    
    def test_valid_transitions_configuration(self):
        """Test that valid transitions are correctly configured"""
        assert "REQS_REFINING" in GatewayService.VALID_TRANSITIONS
        transitions = GatewayService.VALID_TRANSITIONS["REQS_REFINING"]
        
        assert transitions["finalizar"] == "REQS_READY"
        assert transitions["planejar"] == "REQS_READY"
        assert transitions["validar_codigo"] == "CODE_VALIDATION_REQUESTED"
    
    def test_action_reasons_configuration(self):
        """Test that action reasons are correctly configured"""
        assert "finalizar" in GatewayService.ACTION_REASONS
        assert "planejar" in GatewayService.ACTION_REASONS
        assert "validar_codigo" in GatewayService.ACTION_REASONS
        
        assert "finalize" in GatewayService.ACTION_REASONS["finalizar"]
        assert "planning" in GatewayService.ACTION_REASONS["planejar"]
        assert "validation" in GatewayService.ACTION_REASONS["validar_codigo"]

    def test_validate_project_state_valid(self, db_session: Session):
        """Test successful project state validation"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.commit()
        
        # Should not raise exception
        GatewayService.validate_project_state(project, "finalizar")
        GatewayService.validate_project_state(project, "planejar")
        GatewayService.validate_project_state(project, "validar_codigo")

    def test_validate_project_state_invalid_state(self, db_session: Session):
        """Test project state validation with invalid state"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="DRAFT"
        )
        db_session.add(project)
        db_session.commit()
        
        with pytest.raises(Exception) as exc_info:
            GatewayService.validate_project_state(project, "finalizar")
        
        assert exc_info.value.status_code == 400
        assert "INVALID_STATE_TRANSITION" in str(exc_info.value.detail)

    def test_validate_project_state_invalid_action(self, db_session: Session):
        """Test project state validation with invalid action"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project", 
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.commit()
        
        with pytest.raises(Exception) as exc_info:
            GatewayService.validate_project_state(project, "invalid_action")
        
        assert exc_info.value.status_code == 400
        assert "INVALID_ACTION_FOR_STATE" in str(exc_info.value.detail)

    def test_validate_project_requirements_valid(self, db_session: Session):
        """Test successful project requirements validation"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.flush()
        
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ001",
            version=1,
            data={"descricao": "Test requirement"}
        )
        db_session.add(requirement)
        db_session.commit()
        db_session.refresh(project)
        
        # Should not raise exception
        GatewayService.validate_project_requirements(project)

    def test_validate_project_requirements_no_requirements(self, db_session: Session):
        """Test project requirements validation with no requirements"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        with pytest.raises(Exception) as exc_info:
            GatewayService.validate_project_requirements(project)
        
        assert exc_info.value.status_code == 400
        assert "NO_REQUIREMENTS" in str(exc_info.value.detail)

    def test_check_idempotency_existing(self, db_session: Session):
        """Test idempotency check with existing request"""
        # Create project first to satisfy foreign key constraint
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_READY"
        )
        db_session.add(project)
        db_session.flush()
        
        request_id = uuid.uuid4()
        
        audit = RequirementsGatewayAudit(
            id=uuid.uuid4(),
            project_id=project.id,
            correlation_id=uuid.uuid4(),
            request_id=request_id,
            action="finalizar",
            from_state="REQS_REFINING",
            to_state="REQS_READY"
        )
        db_session.add(audit)
        db_session.commit()
        
        result = GatewayService.check_idempotency(db_session, request_id)
        assert result is not None
        assert result.request_id == request_id

    def test_check_idempotency_new(self, db_session: Session):
        """Test idempotency check with new request"""
        request_id = uuid.uuid4()
        
        result = GatewayService.check_idempotency(db_session, request_id)
        assert result is None

    def test_execute_transition_success(self, db_session: Session):
        """Test successful transition execution"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.flush()
        
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ001",
            version=1,
            data={"descricao": "Test requirement"}
        )
        db_session.add(requirement)
        db_session.commit()
        db_session.refresh(project)
        
        request = RequirementsGatewayRequest(
            action=GatewayActionEnum.finalizar,
            correlation_id=uuid.uuid4(),
            request_id=uuid.uuid4()
        )
        
        response = GatewayService.execute_transition(db_session, project, request)
        
        assert response.from_state == "REQS_REFINING"
        assert response.to_state == "REQS_READY"
        assert response.reason == "User chose to finalize requirements"
        assert response.audit_ref.project_id == project.id
        assert response.audit_ref.action == "finalizar"
        
        # Check project state was updated
        db_session.refresh(project)
        assert project.status == "REQS_READY"
        
        # Check audit record was created
        audit = db_session.query(RequirementsGatewayAudit).filter(
            RequirementsGatewayAudit.request_id == request.request_id
        ).first()
        assert audit is not None
        assert audit.from_state == "REQS_REFINING"
        assert audit.to_state == "REQS_READY"

    def test_execute_transition_idempotent(self, db_session: Session):
        """Test idempotent transition execution"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.flush()
        
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ001",
            version=1,
            data={"descricao": "Test requirement"}
        )
        db_session.add(requirement)
        db_session.commit()
        db_session.refresh(project)
        
        request_id = uuid.uuid4()
        request = RequirementsGatewayRequest(
            action=GatewayActionEnum.finalizar,
            correlation_id=uuid.uuid4(),
            request_id=request_id
        )
        
        # First execution
        response1 = GatewayService.execute_transition(db_session, project, request)
        
        # Second execution with same request_id should return cached response
        response2 = GatewayService.execute_transition(db_session, project, request)
        
        assert response1.audit_ref.request_id == response2.audit_ref.request_id
        assert response1.from_state == response2.from_state
        assert response1.to_state == response2.to_state

    def test_get_project_gateway_history(self, db_session: Session):
        """Test getting project gateway history"""
        # Create project first to satisfy foreign key constraint
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_READY"
        )
        db_session.add(project)
        db_session.flush()
        
        # Create multiple audit records
        audit1 = RequirementsGatewayAudit(
            id=uuid.uuid4(),
            project_id=project.id,
            correlation_id=uuid.uuid4(),
            request_id=uuid.uuid4(),
            action="finalizar",
            from_state="REQS_REFINING",
            to_state="REQS_READY"
        )
        
        audit2 = RequirementsGatewayAudit(
            id=uuid.uuid4(),
            project_id=project.id,
            correlation_id=uuid.uuid4(),
            request_id=uuid.uuid4(),
            action="validar_codigo",
            from_state="REQS_READY",
            to_state="CODE_VALIDATION_REQUESTED"
        )
        
        db_session.add_all([audit1, audit2])
        db_session.commit()
        
        history = GatewayService.get_project_gateway_history(db_session, project.id)
        
        assert len(history) == 2
        # Should be ordered by created_at desc
        assert history[0].created_at >= history[1].created_at


class TestGatewayAPI:
    """Integration tests for Gateway API endpoints"""
    
    def test_requirements_gateway_success(self, client: TestClient, db_session: Session):
        """Test successful gateway transition via API"""
        # Create project with requirements
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.flush()
        
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ001",
            version=1,
            data={"descricao": "Test requirement"}
        )
        db_session.add(requirement)
        db_session.commit()
        
        # Make gateway request
        response = client.post(
            f"/api/v1/requirements/{project.id}/gateway",
            json={
                "action": "finalizar",
                "correlation_id": str(uuid.uuid4()),
                "request_id": str(uuid.uuid4())
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["from"] == "REQS_REFINING"
        assert data["to"] == "REQS_READY"
        assert "finalize" in data["reason"]
        assert "audit_ref" in data
        assert data["audit_ref"]["action"] == "finalizar"

    def test_requirements_gateway_project_not_found(self, client: TestClient):
        """Test gateway request for non-existent project"""
        non_existent_id = uuid.uuid4()
        
        response = client.post(
            f"/api/v1/requirements/{non_existent_id}/gateway",
            json={
                "action": "finalizar",
                "request_id": str(uuid.uuid4())
            }
        )
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    def test_requirements_gateway_invalid_state(self, client: TestClient, db_session: Session):
        """Test gateway request with invalid project state"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="DRAFT"  # Invalid state for gateway
        )
        db_session.add(project)
        db_session.commit()
        
        response = client.post(
            f"/api/v1/requirements/{project.id}/gateway",
            json={
                "action": "finalizar",
                "request_id": str(uuid.uuid4())
            }
        )
        
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_code"] == "INVALID_STATE_TRANSITION"
        assert detail["current_state"] == "DRAFT"

    def test_requirements_gateway_no_requirements(self, client: TestClient, db_session: Session):
        """Test gateway request for project with no requirements"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.commit()
        
        response = client.post(
            f"/api/v1/requirements/{project.id}/gateway",
            json={
                "action": "finalizar",
                "request_id": str(uuid.uuid4())
            }
        )
        
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_code"] == "NO_REQUIREMENTS"

    def test_requirements_gateway_all_actions(self, client: TestClient, db_session: Session):
        """Test all valid gateway actions"""
        actions_and_states = [
            ("finalizar", "REQS_READY"),
            ("planejar", "REQS_READY"),
            ("validar_codigo", "CODE_VALIDATION_REQUESTED")
        ]
        
        for action, expected_state in actions_and_states:
            # Create fresh project for each action
            project = Project(
                id=uuid.uuid4(),
                name=f"Test Project {action}",
                status="REQS_REFINING"
            )
            db_session.add(project)
            db_session.flush()
            
            requirement = Requirement(
                id=uuid.uuid4(),
                project_id=project.id,
                code="REQ001",
                version=1,
                data={"descricao": "Test requirement"}
            )
            db_session.add(requirement)
            db_session.commit()
            
            response = client.post(
                f"/api/v1/requirements/{project.id}/gateway",
                json={
                    "action": action,
                    "request_id": str(uuid.uuid4())
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["to"] == expected_state

    def test_get_gateway_history(self, client: TestClient, db_session: Session):
        """Test getting gateway history via API"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_READY"
        )
        db_session.add(project)
        db_session.commit()
        
        # Create audit records
        audit = RequirementsGatewayAudit(
            id=uuid.uuid4(),
            project_id=project.id,
            correlation_id=uuid.uuid4(),
            request_id=uuid.uuid4(),
            action="finalizar",
            from_state="REQS_REFINING",
            to_state="REQS_READY"
        )
        db_session.add(audit)
        db_session.commit()
        
        response = client.get(f"/api/v1/requirements/{project.id}/gateway/history")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["action"] == "finalizar"
        assert data[0]["project_id"] == str(project.id)

    def test_get_gateway_history_project_not_found(self, client: TestClient):
        """Test getting history for non-existent project"""
        non_existent_id = uuid.uuid4()
        
        response = client.get(f"/api/v1/requirements/{non_existent_id}/gateway/history")
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    def test_requirements_gateway_idempotency(self, client: TestClient, db_session: Session):
        """Test idempotency of gateway requests"""
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="REQS_REFINING"
        )
        db_session.add(project)
        db_session.flush()
        
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ001",
            version=1,
            data={"descricao": "Test requirement"}
        )
        db_session.add(requirement)
        db_session.commit()
        
        request_id = str(uuid.uuid4())
        request_data = {
            "action": "finalizar",
            "request_id": request_id
        }
        
        # First request
        response1 = client.post(
            f"/api/v1/requirements/{project.id}/gateway",
            json=request_data
        )
        
        # Second request with same request_id
        response2 = client.post(
            f"/api/v1/requirements/{project.id}/gateway",
            json=request_data
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["audit_ref"]["request_id"] == data2["audit_ref"]["request_id"]
        assert data1["from"] == data2["from"]
        assert data1["to"] == data2["to"]


class TestGatewaySchemas:
    """Unit tests for Gateway schemas"""
    
    def test_gateway_action_enum_values(self):
        """Test that gateway action enum has correct values"""
        assert GatewayActionEnum.finalizar == "finalizar"
        assert GatewayActionEnum.planejar == "planejar"
        assert GatewayActionEnum.validar_codigo == "validar_codigo"
    
    def test_requirements_gateway_request_validation(self):
        """Test validation of gateway request schema"""
        # Valid request
        request = RequirementsGatewayRequest(
            action=GatewayActionEnum.finalizar,
            correlation_id=uuid.uuid4()
        )
        assert request.action == "finalizar"
        assert request.request_id is not None  # Should be auto-generated
        
        # Invalid action should raise validation error
        with pytest.raises(ValueError):
            RequirementsGatewayRequest(action="invalid_action")