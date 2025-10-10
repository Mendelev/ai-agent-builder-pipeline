import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
from unittest.mock import Mock, patch
from decimal import Decimal
from app.models.code_repo import CodeRepository, CloneStatus
from app.services.code_repo_service import CodeRepositoryService
from app.schemas.code_repo import CodeRepositoryConnect


class TestCodeRepositoryAPI:
    """Test cases for code repository API endpoints"""
    
    @patch('app.services.git_service.GitService.check_repository_size')
    @patch('app.services.encryption_service.EncryptionService.encrypt_token')
    @patch('app.tasks.git_clone.clone_repository_task.delay')
    def test_connect_repository_success(self, mock_task, mock_encrypt, mock_size_check, client, db):
        """Test successful repository connection"""
        # Setup mocks
        mock_size_check.return_value = Mock(
            size_mb=Decimal('25.5'),
            is_valid=True,
            error_message=None
        )
        mock_encrypt.return_value = (b'encrypted_data', 'key-123')
        mock_task.return_value = Mock(id='task-456')
        
        # Create test project first
        from app.models.project import Project
        project = Project(name="Test Project", status="DRAFT")
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Make request
        response = client.post(
            "/api/v1/code/connect",
            json={
                "git_url": "https://github.com/user/repo.git",
                "access_token": "ghp_test_token_123",
                "project_id": str(project.id)
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["connected"] is True
        assert data["git_url"] == "https://github.com/user/repo.git"
        assert "repo_id" in data
        assert "task_id" in data
    
    @patch('app.services.git_service.GitService.check_repository_size')
    def test_connect_repository_too_large(self, mock_size_check, client, db):
        """Test repository rejection due to size"""
        # Setup mock to return oversized repository
        mock_size_check.return_value = Mock(
            size_mb=Decimal('150.0'),
            is_valid=False,
            error_message="Repository size 150.0MB exceeds limit of 100MB"
        )
        
        # Create test project
        from app.models.project import Project
        project = Project(name="Test Project", status="DRAFT")
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.post(
            "/api/v1/code/connect",
            json={
                "git_url": "https://github.com/user/large-repo.git",
                "access_token": "ghp_test_token_123",
                "project_id": str(project.id)
            }
        )
        
        assert response.status_code == 413
        data = response.json()
        assert data["detail"]["error"] == "repository_too_large"
        assert data["detail"]["estimated_size_mb"] == 150.0
        assert data["detail"]["limit_mb"] == 100
    
    def test_connect_repository_invalid_url(self, client, db):
        """Test repository connection with invalid URL"""
        from app.models.project import Project
        project = Project(name="Test Project", status="DRAFT")
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.post(
            "/api/v1/code/connect",
            json={
                "git_url": "not-a-valid-url",
                "access_token": "ghp_test_token_123",
                "project_id": str(project.id)
            }
        )
        
        assert response.status_code == 422
        assert "Invalid Git repository URL format" in str(response.json())
    
    def test_connect_repository_invalid_token(self, client, db):
        """Test repository connection with invalid token"""
        from app.models.project import Project
        project = Project(name="Test Project", status="DRAFT")
        db.add(project)
        db.commit()
        db.refresh(project)
        
        response = client.post(
            "/api/v1/code/connect",
            json={
                "git_url": "https://github.com/user/repo.git",
                "access_token": "short",  # Too short
                "project_id": str(project.id)
            }
        )
        
        assert response.status_code == 422
        assert "Access token appears to be invalid" in str(response.json())
    
    def test_get_repository_success(self, client, db):
        """Test getting repository details"""
        # Create test project and repository
        from app.models.project import Project
        project = Project(name="Test Project", status="DRAFT")
        db.add(project)
        db.commit()
        
        repo = CodeRepository(
            project_id=project.id,
            git_url="https://github.com/user/repo.git",
            token_ciphertext=b"encrypted_token",
            token_kid="key-123",
            repository_size_mb=Decimal('25.5'),
            clone_status=CloneStatus.COMPLETED,
            sandbox_path="/tmp/repos/proj/repo"
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        
        response = client.get(f"/api/v1/code/repos/{repo.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(repo.id)
        assert data["git_url"] == "https://github.com/user/repo.git"
        assert data["clone_status"] == CloneStatus.COMPLETED
    
    def test_get_repository_not_found(self, client, db):
        """Test getting non-existent repository"""
        fake_id = uuid4()
        response = client.get(f"/api/v1/code/repos/{fake_id}")
        
        assert response.status_code == 404
        assert "Repository not found" in response.json()["detail"]
    
    def test_get_repository_status(self, client, db):
        """Test getting repository status"""
        # Create test project and repository
        from app.models.project import Project
        project = Project(name="Test Project", status="DRAFT")
        db.add(project)
        db.commit()
        
        repo = CodeRepository(
            project_id=project.id,
            git_url="https://github.com/user/repo.git",
            token_ciphertext=b"encrypted_token",
            token_kid="key-123",
            repository_size_mb=Decimal('25.5'),
            clone_status=CloneStatus.COMPLETED,
            sandbox_path="/tmp/repos/proj/repo"
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        
        response = client.get(f"/api/v1/code/repos/{repo.id}/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["repo_id"] == str(repo.id)
        assert data["clone_status"] == CloneStatus.COMPLETED
        assert data["repository_size_mb"] == 25.5
        assert data["sandbox_path"] == "/tmp/repos/proj/repo"
        assert "Repository successfully cloned" in data["progress_message"]
    
    def test_get_project_repositories(self, client, db):
        """Test getting all repositories for a project"""
        # Create test project
        from app.models.project import Project
        project = Project(name="Test Project", status="DRAFT")
        db.add(project)
        db.commit()
        
        # Create multiple repositories
        repo1 = CodeRepository(
            project_id=project.id,
            git_url="https://github.com/user/repo1.git",
            token_ciphertext=b"encrypted_token_1",
            token_kid="key-123",
            repository_size_mb=Decimal('10.0'),
            clone_status=CloneStatus.COMPLETED
        )
        repo2 = CodeRepository(
            project_id=project.id,
            git_url="https://github.com/user/repo2.git",
            token_ciphertext=b"encrypted_token_2",
            token_kid="key-456",
            repository_size_mb=Decimal('20.0'),
            clone_status=CloneStatus.PENDING
        )
        db.add_all([repo1, repo2])
        db.commit()
        
        response = client.get(f"/api/v1/code/projects/{project.id}/repos")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(r["git_url"] == "https://github.com/user/repo1.git" for r in data)
        assert any(r["git_url"] == "https://github.com/user/repo2.git" for r in data)
    
    def test_get_project_repositories_empty(self, client, db):
        """Test getting repositories for project with no repositories"""
        # Create test project
        from app.models.project import Project
        project = Project(name="Test Project", status="DRAFT")
        db.add(project)
        db.commit()
        
        response = client.get(f"/api/v1/code/projects/{project.id}/repos")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestCodeRepositoryService:
    """Test cases for code repository service"""
    
    def test_get_repository(self, db):
        """Test getting repository by ID"""
        # Create test project and repository
        from app.models.project import Project
        project = Project(name="Test Project", status="DRAFT")
        db.add(project)
        db.commit()
        
        repo = CodeRepository(
            project_id=project.id,
            git_url="https://github.com/user/repo.git",
            token_ciphertext=b"encrypted_token",
            token_kid="key-123"
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        
        service = CodeRepositoryService(db)
        result = service.get_repository(repo.id)
        
        assert result is not None
        assert result.id == repo.id
        assert result.git_url == "https://github.com/user/repo.git"
    
    def test_get_repository_not_found(self, db):
        """Test getting non-existent repository"""
        service = CodeRepositoryService(db)
        result = service.get_repository(uuid4())
        
        assert result is None
    
    def test_update_clone_status(self, db):
        """Test updating repository clone status"""
        # Create test project and repository
        from app.models.project import Project
        project = Project(name="Test Project", status="DRAFT")
        db.add(project)
        db.commit()
        
        repo = CodeRepository(
            project_id=project.id,
            git_url="https://github.com/user/repo.git",
            token_ciphertext=b"encrypted_token",
            token_kid="key-123",
            clone_status=CloneStatus.PENDING
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        
        service = CodeRepositoryService(db)
        success = service.update_clone_status(
            repo.id,
            CloneStatus.COMPLETED,
            sandbox_path="/tmp/repos/test",
            actual_size_mb=30.5
        )
        
        assert success is True
        
        # Verify update
        updated_repo = service.get_repository(repo.id)
        assert updated_repo.clone_status == CloneStatus.COMPLETED
        assert updated_repo.sandbox_path == "/tmp/repos/test"
        assert float(updated_repo.repository_size_mb) == 30.5
