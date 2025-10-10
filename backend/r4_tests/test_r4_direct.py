#!/usr/bin/env python3
"""
Test R4 Requirements Gateway - Direct Python Tests
Automated testing script for the Requirements Gateway (R4) module
"""

import requests
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class R4Tester:
    """Test harness for R4 Requirements Gateway"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.tests_passed = 0
        self.tests_failed = 0
        self.current_test = ""
        
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.MAGENTA}{'='*60}{Colors.NC}")
        print(f"{Colors.MAGENTA}{text.center(60)}{Colors.NC}")
        print(f"{Colors.MAGENTA}{'='*60}{Colors.NC}\n")
        
    def print_section(self, text: str):
        """Print formatted section"""
        print(f"\n{Colors.YELLOW}▶ {text}{Colors.NC}")
        
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.NC}")
        
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.RED}✗ {text}{Colors.NC}")
        
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.CYAN}  {text}{Colors.NC}")
        
    def assert_equal(self, actual: Any, expected: Any, message: str = ""):
        """Assert equality with colored output"""
        if actual == expected:
            self.tests_passed += 1
            self.print_success(f"{message or 'Assertion passed'}: {actual} == {expected}")
            return True
        else:
            self.tests_failed += 1
            self.print_error(f"{message or 'Assertion failed'}: {actual} != {expected}")
            return False
            
    def assert_status_code(self, response: requests.Response, expected: int, message: str = ""):
        """Assert HTTP status code"""
        return self.assert_equal(
            response.status_code, 
            expected, 
            message or f"HTTP status code"
        )
        
    def create_project(self, name: str) -> Optional[Dict[str, Any]]:
        """Create a new project"""
        try:
            response = requests.post(
                f"{self.base_url}/projects",
                json={"name": name}
            )
            if response.status_code in [200, 201]:
                self.print_success(f"Project created: {name}")
                return response.json()
            else:
                self.print_error(f"Failed to create project: {response.status_code}")
                return None
        except Exception as e:
            self.print_error(f"Exception creating project: {e}")
            return None
            
    def add_requirements(self, project_id: str, requirements: list) -> bool:
        """Add requirements to a project"""
        try:
            response = requests.post(
                f"{self.base_url}/projects/{project_id}/requirements",
                json={"requirements": requirements}
            )
            if response.status_code == 200:
                self.print_success(f"Added {len(requirements)} requirement(s)")
                return True
            else:
                self.print_error(f"Failed to add requirements: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Exception adding requirements: {e}")
            return False
            
    def update_project_status(self, project_id: str, status: str) -> bool:
        """Update project status"""
        try:
            response = requests.patch(
                f"{self.base_url}/projects/{project_id}",
                json={"status": status}
            )
            if response.status_code == 200:
                self.print_success(f"Project status updated to: {status}")
                return True
            else:
                self.print_error(f"Failed to update status: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Exception updating status: {e}")
            return False
            
    def execute_gateway(
        self, 
        project_id: str, 
        action: str,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Optional[requests.Response]:
        """Execute gateway transition"""
        try:
            payload = {"action": action}
            if request_id:
                payload["request_id"] = request_id
            if correlation_id:
                payload["correlation_id"] = correlation_id
                
            response = requests.post(
                f"{self.base_url}/requirements/{project_id}/gateway",
                json=payload
            )
            return response
        except Exception as e:
            self.print_error(f"Exception executing gateway: {e}")
            return None
            
    def get_gateway_history(self, project_id: str) -> Optional[requests.Response]:
        """Get gateway history for a project"""
        try:
            response = requests.get(
                f"{self.base_url}/requirements/{project_id}/gateway/history"
            )
            return response
        except Exception as e:
            self.print_error(f"Exception getting history: {e}")
            return None
            
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        try:
            response = requests.get(f"{self.base_url}/projects/{project_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.print_error(f"Exception getting project: {e}")
            return None
            
    # ========================================================================
    # TEST CASES
    # ========================================================================
    
    def test_finalizar_transition(self):
        """Test gateway transition with 'finalizar' action"""
        self.print_section("TEST 1: Gateway Transition - FINALIZAR")
        
        # Create project
        project = self.create_project("Test R4 - Finalizar")
        if not project:
            return False
            
        project_id = project["id"]
        
        # Add requirement
        requirements = [{
            "code": "REQ-001",
            "descricao": "Sistema de autenticação completo",
            "criterios_aceitacao": [
                "Login com email e senha",
                "Logout funcional"
            ],
            "prioridade": "must",
            "dependencias": []
        }]
        
        if not self.add_requirements(project_id, requirements):
            return False
            
        # Update to REQS_REFINING
        if not self.update_project_status(project_id, "REQS_REFINING"):
            return False
            
        # Execute gateway
        response = self.execute_gateway(project_id, "finalizar")
        if not response:
            return False
            
        # Verify response
        self.assert_status_code(response, 200, "Gateway finalizar")
        
        data = response.json()
        self.assert_equal(data.get("from"), "REQS_REFINING", "From state")
        self.assert_equal(data.get("to"), "REQS_READY", "To state")
        self.assert_equal("finalize" in data.get("reason", "").lower(), True, "Reason contains 'finalize'")
        
        # Verify audit reference
        audit_ref = data.get("audit_ref", {})
        self.print_info(f"Correlation ID: {audit_ref.get('correlation_id')}")
        self.print_info(f"Request ID: {audit_ref.get('request_id')}")
        
        return True
        
    def test_planejar_transition(self):
        """Test gateway transition with 'planejar' action"""
        self.print_section("TEST 2: Gateway Transition - PLANEJAR")
        
        project = self.create_project("Test R4 - Planejar")
        if not project:
            return False
            
        project_id = project["id"]
        
        requirements = [{
            "code": "REQ-002",
            "descricao": "Dashboard analítico",
            "criterios_aceitacao": ["Gráficos interativos", "Exportar relatórios"],
            "prioridade": "should",
            "dependencias": []
        }]
        
        if not self.add_requirements(project_id, requirements):
            return False
            
        if not self.update_project_status(project_id, "REQS_REFINING"):
            return False
            
        response = self.execute_gateway(project_id, "planejar")
        if not response:
            return False
            
        self.assert_status_code(response, 200, "Gateway planejar")
        
        data = response.json()
        self.assert_equal(data.get("from"), "REQS_REFINING", "From state")
        self.assert_equal(data.get("to"), "REQS_READY", "To state")
        self.assert_equal("planning" in data.get("reason", "").lower(), True, "Reason contains 'planning'")
        
        return True
        
    def test_validar_codigo_transition(self):
        """Test gateway transition with 'validar_codigo' action"""
        self.print_section("TEST 3: Gateway Transition - VALIDAR_CODIGO")
        
        project = self.create_project("Test R4 - Validar Código")
        if not project:
            return False
            
        project_id = project["id"]
        
        requirements = [{
            "code": "REQ-003",
            "descricao": "API REST com testes",
            "criterios_aceitacao": ["Endpoints documentados", "Coverage > 80%"],
            "prioridade": "must",
            "dependencias": []
        }]
        
        if not self.add_requirements(project_id, requirements):
            return False
            
        if not self.update_project_status(project_id, "REQS_REFINING"):
            return False
            
        response = self.execute_gateway(project_id, "validar_codigo")
        if not response:
            return False
            
        self.assert_status_code(response, 200, "Gateway validar_codigo")
        
        data = response.json()
        self.assert_equal(data.get("from"), "REQS_REFINING", "From state")
        self.assert_equal(data.get("to"), "CODE_VALIDATION_REQUESTED", "To state")
        self.assert_equal("validation" in data.get("reason", "").lower(), True, "Reason contains 'validation'")
        
        return True
        
    def test_idempotency(self):
        """Test idempotency with same request_id"""
        self.print_section("TEST 4: Idempotency")
        
        project = self.create_project("Test R4 - Idempotency")
        if not project:
            return False
            
        project_id = project["id"]
        
        requirements = [{
            "code": "REQ-IDEMP-001",
            "descricao": "Test requirement",
            "criterios_aceitacao": ["Test criterion"],
            "prioridade": "must",
            "dependencias": []
        }]
        
        if not self.add_requirements(project_id, requirements):
            return False
            
        if not self.update_project_status(project_id, "REQS_REFINING"):
            return False
            
        # First request with specific request_id
        request_id = str(uuid.uuid4())
        self.print_info(f"Using request_id: {request_id}")
        
        response1 = self.execute_gateway(project_id, "finalizar", request_id=request_id)
        if not response1:
            return False
            
        self.assert_status_code(response1, 200, "First request")
        data1 = response1.json()
        
        # Second request with SAME request_id
        response2 = self.execute_gateway(project_id, "finalizar", request_id=request_id)
        if not response2:
            return False
            
        self.assert_status_code(response2, 200, "Second request (idempotent)")
        data2 = response2.json()
        
        # Verify same audit reference
        audit1 = data1.get("audit_ref", {})
        audit2 = data2.get("audit_ref", {})
        
        self.assert_equal(
            audit1.get("correlation_id"), 
            audit2.get("correlation_id"), 
            "Correlation IDs match (idempotent)"
        )
        
        return True
        
    def test_invalid_state_transition(self):
        """Test invalid state transition (DRAFT state)"""
        self.print_section("TEST 5: Invalid State Transition")
        
        project = self.create_project("Test R4 - Invalid State")
        if not project:
            return False
            
        project_id = project["id"]
        
        # Try gateway on DRAFT state (should fail with 400)
        response = self.execute_gateway(project_id, "finalizar")
        if not response:
            return False
            
        self.assert_status_code(response, 400, "Invalid state rejected")
        
        data = response.json()
        self.print_info(f"Error detail: {data.get('detail')}")
        
        return True
        
    def test_no_requirements_error(self):
        """Test error when project has no requirements"""
        self.print_section("TEST 6: No Requirements Error")
        
        project = self.create_project("Test R4 - No Requirements")
        if not project:
            return False
            
        project_id = project["id"]
        
        # Update to REQS_REFINING but don't add requirements
        if not self.update_project_status(project_id, "REQS_REFINING"):
            return False
            
        # Try gateway without requirements (should fail with 400)
        response = self.execute_gateway(project_id, "finalizar")
        if not response:
            return False
            
        self.assert_status_code(response, 400, "No requirements error")
        
        data = response.json()
        self.print_info(f"Error detail: {data.get('detail')}")
        
        return True
        
    def test_gateway_history(self):
        """Test gateway history retrieval"""
        self.print_section("TEST 7: Gateway History")
        
        project = self.create_project("Test R4 - History")
        if not project:
            return False
            
        project_id = project["id"]
        
        requirements = [{
            "code": "REQ-HIST-001",
            "descricao": "Test requirement",
            "criterios_aceitacao": ["Test criterion"],
            "prioridade": "must",
            "dependencias": []
        }]
        
        if not self.add_requirements(project_id, requirements):
            return False
            
        if not self.update_project_status(project_id, "REQS_REFINING"):
            return False
            
        # Execute gateway transition
        response = self.execute_gateway(project_id, "finalizar")
        if not response or response.status_code != 200:
            return False
            
        # Get history
        history_response = self.get_gateway_history(project_id)
        if not history_response:
            return False
            
        self.assert_status_code(history_response, 200, "Get history")
        
        history = history_response.json()
        self.assert_equal(len(history) >= 1, True, "History has at least 1 entry")
        
        if len(history) > 0:
            entry = history[0]
            self.print_info(f"Latest transition: {entry.get('action')} "
                          f"({entry.get('from_state')} → {entry.get('to_state')})")
            self.print_info(f"Timestamp: {entry.get('created_at')}")
            
        return True
        
    def test_correlation_id_tracking(self):
        """Test correlation ID tracking across requests"""
        self.print_section("TEST 8: Correlation ID Tracking")
        
        project = self.create_project("Test R4 - Correlation")
        if not project:
            return False
            
        project_id = project["id"]
        
        requirements = [{
            "code": "REQ-CORR-001",
            "descricao": "Test requirement",
            "criterios_aceitacao": ["Test criterion"],
            "prioridade": "must",
            "dependencias": []
        }]
        
        if not self.add_requirements(project_id, requirements):
            return False
            
        if not self.update_project_status(project_id, "REQS_REFINING"):
            return False
            
        # Execute with custom correlation ID
        correlation_id = str(uuid.uuid4())
        self.print_info(f"Using correlation_id: {correlation_id}")
        
        response = self.execute_gateway(
            project_id, 
            "finalizar", 
            correlation_id=correlation_id
        )
        if not response:
            return False
            
        self.assert_status_code(response, 200, "Gateway with correlation ID")
        
        data = response.json()
        returned_corr_id = data.get("audit_ref", {}).get("correlation_id")
        
        self.assert_equal(
            returned_corr_id, 
            correlation_id, 
            "Correlation ID preserved"
        )
        
        return True
        
    def run_all_tests(self):
        """Run all test cases"""
        self.print_header("R4 REQUIREMENTS GATEWAY - AUTOMATED TESTS")
        
        tests = [
            self.test_finalizar_transition,
            self.test_planejar_transition,
            self.test_validar_codigo_transition,
            self.test_idempotency,
            self.test_invalid_state_transition,
            self.test_no_requirements_error,
            self.test_gateway_history,
            self.test_correlation_id_tracking,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.print_error(f"Test failed with exception: {e}")
                self.tests_failed += 1
                
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        total = self.tests_passed + self.tests_failed
        
        print(f"\n{Colors.MAGENTA}{'='*60}{Colors.NC}")
        print(f"{Colors.CYAN}TEST SUMMARY{Colors.NC}")
        print(f"{Colors.MAGENTA}{'='*60}{Colors.NC}")
        print(f"{Colors.GREEN}Passed: {self.tests_passed}{Colors.NC}")
        print(f"{Colors.RED}Failed: {self.tests_failed}{Colors.NC}")
        print(f"{Colors.CYAN}Total:  {total}{Colors.NC}")
        
        if self.tests_failed == 0:
            print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED! 🎉{Colors.NC}\n")
        else:
            print(f"\n{Colors.RED}❌ SOME TESTS FAILED ❌{Colors.NC}\n")
            

if __name__ == "__main__":
    tester = R4Tester()
    tester.run_all_tests()
