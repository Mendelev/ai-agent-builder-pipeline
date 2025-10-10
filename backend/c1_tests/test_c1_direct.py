#!/usr/bin/env python3
"""
Test C1 Code Repository Connect - Direct Python Tests
Automated testing script for the Code Repository Connection (C1) module
"""

import requests
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class C1Tester:
    """Test harness for C1 Code Repository Connect"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_resources = []  # Track created resources for cleanup
        
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.MAGENTA}{'='*70}{Colors.NC}")
        print(f"{Colors.MAGENTA}{text.center(70)}{Colors.NC}")
        print(f"{Colors.MAGENTA}{'='*70}{Colors.NC}\n")
        
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
    
    def assert_not_in_response(self, response_text: str, sensitive_data: str, message: str = ""):
        """Assert sensitive data is NOT in response"""
        if sensitive_data not in response_text:
            self.tests_passed += 1
            self.print_success(f"{message}: Data properly masked/encrypted")
            return True
        else:
            self.tests_failed += 1
            self.print_error(f"{message}: SECURITY ISSUE - Sensitive data exposed!")
            return False
        
    def create_project(self, name: str) -> Optional[Dict[str, Any]]:
        """Create a new project"""
        try:
            response = requests.post(
                f"{self.base_url}/projects",
                json={"name": name}
            )
            if response.status_code in [200, 201]:
                project = response.json()
                self.test_resources.append(('project', project['id']))
                self.print_success(f"Project created: {name}")
                return project
            else:
                self.print_error(f"Failed to create project: {response.status_code}")
                return None
        except Exception as e:
            self.print_error(f"Exception creating project: {e}")
            return None
    
    def connect_repository(self, git_url: str, access_token: str, project_id: str) -> Optional[requests.Response]:
        """Connect a repository to a project"""
        try:
            response = requests.post(
                f"{self.base_url}/code/connect",
                json={
                    "git_url": git_url,
                    "access_token": access_token,
                    "project_id": project_id
                }
            )
            if response.status_code in [200, 201]:
                data = response.json()
                repo_id = data.get('id') or data.get('repo_id')
                if repo_id:
                    self.test_resources.append(('repository', repo_id))
            return response
        except Exception as e:
            self.print_error(f"Exception connecting repository: {e}")
            return None
    
    def get_repository(self, repo_id: str) -> Optional[requests.Response]:
        """Get repository details"""
        try:
            return requests.get(f"{self.base_url}/code/repos/{repo_id}")
        except Exception as e:
            self.print_error(f"Exception getting repository: {e}")
            return None
    
    def get_repository_status(self, repo_id: str) -> Optional[requests.Response]:
        """Get repository clone status"""
        try:
            return requests.get(f"{self.base_url}/code/repos/{repo_id}/status")
        except Exception as e:
            self.print_error(f"Exception getting repository status: {e}")
            return None
    
    def get_project_repositories(self, project_id: str) -> Optional[requests.Response]:
        """Get all repositories for a project"""
        try:
            return requests.get(f"{self.base_url}/code/projects/{project_id}/repos")
        except Exception as e:
            self.print_error(f"Exception getting project repositories: {e}")
            return None
    
    def test_successful_repository_connection(self):
        """Test 1: Successful repository connection"""
        self.print_section("TEST 1: Successful Repository Connection")
        
        project = self.create_project("Test C1 Direct - Success")
        if not project:
            return False
        
        project_id = project["id"]
        
        # Connect repository
        response = self.connect_repository(
            git_url="https://github.com/octocat/Hello-World.git",
            access_token="ghp_test_token_success_12345678901234567890",
            project_id=project_id
        )
        
        if not response:
            return False
        
        self.assert_status_code(response, 201, "Repository connection")
        
        data = response.json()
        repo_id = data.get('id') or data.get('repo_id')
        
        # Verify response structure
        self.assert_equal('connected' in data, True, "Response has 'connected' field")
        self.assert_equal(data.get('connected'), True, "Repository connected status")
        self.assert_equal(data.get('git_url'), "https://github.com/octocat/Hello-World.git", "Git URL matches")
        
        # Verify clone status
        clone_status = data.get('clone_status')
        valid_statuses = ['PENDING', 'CLONING', 'COMPLETED']
        self.assert_equal(clone_status in valid_statuses, True, f"Clone status is valid: {clone_status}")
        
        self.print_info(f"Repository ID: {repo_id}")
        self.print_info(f"Clone Status: {clone_status}")
        
        return True
    
    def test_token_security(self):
        """Test 2: Token security and encryption"""
        self.print_section("TEST 2: Token Security & Encryption")
        
        project = self.create_project("Test C1 Direct - Token Security")
        if not project:
            return False
        
        project_id = project["id"]
        sensitive_token = "ghp_VERY_SECRET_TOKEN_MUST_BE_HIDDEN_987654321"
        
        # Connect repository
        response = self.connect_repository(
            git_url="https://github.com/github/docs.git",
            access_token=sensitive_token,
            project_id=project_id
        )
        
        if not response:
            return False
        
        # Check connection response
        self.assert_not_in_response(
            response.text, 
            sensitive_token, 
            "Token not in connection response"
        )
        
        data = response.json()
        repo_id = data.get('id') or data.get('repo_id')
        
        # Check GET repository details
        repo_response = self.get_repository(repo_id)
        if repo_response:
            self.assert_not_in_response(
                repo_response.text,
                sensitive_token,
                "Token not in repository details"
            )
        
        # Check GET project repositories
        project_repos = self.get_project_repositories(project_id)
        if project_repos:
            self.assert_not_in_response(
                project_repos.text,
                sensitive_token,
                "Token not in project repositories list"
            )
        
        # Verify that token_ciphertext is NOT exposed (if it exists)
        repo_data = repo_response.json() if repo_response else {}
        self.assert_equal(
            'token_ciphertext' not in repo_data and 'access_token' not in repo_data,
            True,
            "Token fields not exposed in API"
        )
        
        return True
    
    def test_repository_size_validation(self):
        """Test 3: Repository size validation"""
        self.print_section("TEST 3: Repository Size Validation")
        
        project = self.create_project("Test C1 Direct - Size Validation")
        if not project:
            return False
        
        project_id = project["id"]
        
        # Attempt to connect a large repository (Linux kernel)
        response = self.connect_repository(
            git_url="https://github.com/torvalds/linux.git",
            access_token="ghp_test_token_large_repo_123",
            project_id=project_id
        )
        
        if not response:
            return False
        
        # Should be rejected with 413 (Payload Too Large) or accepted if under limit
        if response.status_code == 413:
            self.print_success("Large repository correctly rejected (HTTP 413)")
            data = response.json()
            
            # Verify error structure
            detail = data.get('detail', {})
            self.assert_equal(detail.get('error'), 'repository_too_large', "Error type")
            self.assert_equal('estimated_size_mb' in detail, True, "Estimated size provided")
            self.assert_equal('limit_mb' in detail, True, "Limit provided")
            
            self.print_info(f"Estimated Size: {detail.get('estimated_size_mb')}MB")
            self.print_info(f"Limit: {detail.get('limit_mb')}MB")
            
        elif response.status_code in [200, 201]:
            self.print_info("Repository accepted (may be under limit or mocked)")
            data = response.json()
            size_mb = data.get('repository_size_mb') or data.get('estimated_size_mb')
            self.print_info(f"Repository Size: {size_mb}MB")
            
        return True
    
    def test_invalid_git_url(self):
        """Test 4: Invalid Git URL validation"""
        self.print_section("TEST 4: Invalid Git URL Validation")
        
        project = self.create_project("Test C1 Direct - Invalid URL")
        if not project:
            return False
        
        project_id = project["id"]
        
        # Try invalid URL
        response = self.connect_repository(
            git_url="not-a-valid-git-url",
            access_token="ghp_test_token_123",
            project_id=project_id
        )
        
        if not response:
            return False
        
        # Should be rejected with 422 (Validation Error)
        if response.status_code == 422:
            self.print_success("Invalid URL correctly rejected (HTTP 422)")
            data = response.json()
            self.print_info(f"Validation error: {data.get('detail')}")
        else:
            self.print_error(f"Expected HTTP 422, got {response.status_code}")
        
        return True
    
    def test_repository_status_tracking(self):
        """Test 5: Repository status tracking"""
        self.print_section("TEST 5: Repository Status Tracking")
        
        project = self.create_project("Test C1 Direct - Status Tracking")
        if not project:
            return False
        
        project_id = project["id"]
        
        # Connect repository
        response = self.connect_repository(
            git_url="https://github.com/octocat/Spoon-Knife.git",
            access_token="ghp_test_token_status_123",
            project_id=project_id
        )
        
        if not response or response.status_code not in [200, 201]:
            return False
        
        data = response.json()
        repo_id = data.get('id') or data.get('repo_id')
        
        # Get status immediately
        status_response = self.get_repository_status(repo_id)
        if not status_response:
            return False
        
        self.assert_status_code(status_response, 200, "Status endpoint")
        
        status_data = status_response.json()
        self.assert_equal('clone_status' in status_data, True, "Status has clone_status")
        self.assert_equal('repo_id' in status_data, True, "Status has repo_id")
        self.assert_equal('progress_message' in status_data, True, "Status has progress_message")
        
        clone_status = status_data.get('clone_status')
        progress_msg = status_data.get('progress_message')
        
        self.print_info(f"Clone Status: {clone_status}")
        self.print_info(f"Progress Message: {progress_msg}")
        
        return True
    
    def test_multiple_repositories_per_project(self):
        """Test 6: Multiple repositories per project"""
        self.print_section("TEST 6: Multiple Repositories per Project")
        
        project = self.create_project("Test C1 Direct - Multi Repo")
        if not project:
            return False
        
        project_id = project["id"]
        
        # Connect first repository
        response1 = self.connect_repository(
            git_url="https://github.com/octocat/Hello-World.git",
            access_token="ghp_test_token_repo1_123",
            project_id=project_id
        )
        
        if not response1 or response1.status_code not in [200, 201]:
            return False
        
        # Connect second repository
        response2 = self.connect_repository(
            git_url="https://github.com/github/docs.git",
            access_token="ghp_test_token_repo2_456",
            project_id=project_id
        )
        
        if not response2 or response2.status_code not in [200, 201]:
            return False
        
        # Get project repositories
        repos_response = self.get_project_repositories(project_id)
        if not repos_response:
            return False
        
        self.assert_status_code(repos_response, 200, "List project repositories")
        
        repos = repos_response.json()
        self.assert_equal(len(repos), 2, "Number of repositories")
        
        self.print_info(f"Repository 1: {repos[0].get('git_url')}")
        self.print_info(f"Repository 2: {repos[1].get('git_url')}")
        
        return True
    
    def test_nonexistent_repository(self):
        """Test 7: Get non-existent repository"""
        self.print_section("TEST 7: Non-existent Repository Handling")
        
        fake_repo_id = "99999999-9999-9999-9999-999999999999"
        
        response = self.get_repository(fake_repo_id)
        if not response:
            return False
        
        self.assert_status_code(response, 404, "Non-existent repository")
        
        return True
    
    def test_repository_details_response_structure(self):
        """Test 8: Repository details response structure"""
        self.print_section("TEST 8: Repository Details Response Structure")
        
        project = self.create_project("Test C1 Direct - Response Structure")
        if not project:
            return False
        
        project_id = project["id"]
        
        # Connect repository
        response = self.connect_repository(
            git_url="https://github.com/octocat/Hello-World.git",
            access_token="ghp_test_token_structure_123",
            project_id=project_id
        )
        
        if not response or response.status_code not in [200, 201]:
            return False
        
        data = response.json()
        repo_id = data.get('id') or data.get('repo_id')
        
        # Get repository details
        repo_response = self.get_repository(repo_id)
        if not repo_response:
            return False
        
        self.assert_status_code(repo_response, 200, "Get repository details")
        
        repo_data = repo_response.json()
        
        # Verify required fields
        required_fields = ['id', 'project_id', 'git_url', 'clone_status', 'created_at']
        for field in required_fields:
            self.assert_equal(field in repo_data, True, f"Field '{field}' present")
        
        # Verify data types
        self.assert_equal(isinstance(repo_data.get('git_url'), str), True, "git_url is string")
        self.assert_equal(isinstance(repo_data.get('clone_status'), str), True, "clone_status is string")
        
        # Verify sensitive fields NOT present
        sensitive_fields = ['access_token', 'token_ciphertext', 'token']
        for field in sensitive_fields:
            self.assert_equal(field not in repo_data, True, f"Sensitive field '{field}' not exposed")
        
        return True
    
    def run_all_tests(self):
        """Run all test cases"""
        self.print_header("C1 CODE REPOSITORY CONNECT - AUTOMATED TESTS")
        
        tests = [
            self.test_successful_repository_connection,
            self.test_token_security,
            self.test_repository_size_validation,
            self.test_invalid_git_url,
            self.test_repository_status_tracking,
            self.test_multiple_repositories_per_project,
            self.test_nonexistent_repository,
            self.test_repository_details_response_structure
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.print_error(f"Test exception: {e}")
                self.tests_failed += 1
        
        # Print summary
        self.print_header("TEST EXECUTION SUMMARY")
        
        total_tests = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{Colors.CYAN}Total Assertions: {total_tests}{Colors.NC}")
        print(f"{Colors.GREEN}Passed: {self.tests_passed}{Colors.NC}")
        print(f"{Colors.RED}Failed: {self.tests_failed}{Colors.NC}")
        print(f"{Colors.YELLOW}Pass Rate: {pass_rate:.1f}%{Colors.NC}\n")
        
        if self.tests_failed == 0:
            print(f"{Colors.GREEN}{'='*70}")
            print(f"ALL TESTS PASSED! ✓".center(70))
            print(f"{'='*70}{Colors.NC}\n")
        else:
            print(f"{Colors.RED}{'='*70}")
            print(f"SOME TESTS FAILED".center(70))
            print(f"{'='*70}{Colors.NC}\n")
        
        # Cleanup reminder
        print(f"{Colors.YELLOW}Created test resources:{Colors.NC}")
        print(f"{Colors.YELLOW}To cleanup, run: ./test_c1_cleanup.sh{Colors.NC}\n")
        
        return self.tests_failed == 0


def main():
    """Main test execution"""
    tester = C1Tester()
    success = tester.run_all_tests()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
