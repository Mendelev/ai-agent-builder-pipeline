import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
import subprocess
from app.services.git_service import GitService, GitSizeCheckResult


class TestGitService:
    """Test cases for Git service"""
    
    @patch('subprocess.run')
    @patch('os.walk')
    @patch('os.path.getsize')
    def test_check_repository_size_valid(self, mock_getsize, mock_walk, mock_subprocess):
        """Test repository size check for valid repository"""
        # Mock successful git clone
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Mock directory with 10MB of files
        mock_walk.return_value = [
            ('/tmp/repo', [], ['file1.txt', 'file2.txt']),
        ]
        
        # 5MB per file = 10MB total, estimated 35MB (3.5x multiplier)
        mock_getsize.return_value = 5 * 1024 * 1024
        
        service = GitService()
        result = service.check_repository_size(
            "https://github.com/user/repo.git",
            "test_token"
        )
        
        assert result.is_valid is True
        assert result.size_mb > 0
        assert result.size_mb < 100  # Within default limit
        assert result.error_message is None
    
    @patch('subprocess.run')
    @patch('os.walk')
    @patch('os.path.getsize')
    def test_check_repository_size_too_large(self, mock_getsize, mock_walk, mock_subprocess):
        """Test repository size check for oversized repository"""
        # Mock successful git clone
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Mock directory with 150MB of files (estimated)
        mock_walk.return_value = [
            ('/tmp/repo', [], ['large_file.bin']),
        ]
        
        # 50MB file will be estimated as 175MB (50 * 3.5)
        mock_getsize.return_value = 50 * 1024 * 1024
        
        service = GitService()
        result = service.check_repository_size(
            "https://github.com/user/large-repo.git",
            "test_token"
        )
        
        assert result.is_valid is False
        assert result.size_mb > 100
        assert "exceeds limit" in result.error_message
    
    @patch('subprocess.run')
    def test_check_repository_size_git_failure(self, mock_subprocess):
        """Test repository size check when git command fails"""
        # Mock git clone failure
        error = subprocess.CalledProcessError(
            returncode=128,
            cmd=['git', 'clone']
        )
        error.stderr = b"Repository not found"
        mock_subprocess.side_effect = error
        
        service = GitService()
        result = service.check_repository_size(
            "https://github.com/user/nonexistent.git",
            "test_token"
        )
        
        assert result.is_valid is False
        assert result.size_mb == Decimal('0')
        assert result.error_message is not None
        assert "Git operation failed" in result.error_message
    
    @patch('subprocess.run')
    def test_check_repository_size_timeout(self, mock_subprocess):
        """Test repository size check timeout"""
        # Mock timeout
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=['git', 'clone'],
            timeout=300
        )
        
        service = GitService()
        result = service.check_repository_size(
            "https://github.com/user/repo.git",
            "test_token"
        )
        
        assert result.is_valid is False
        assert result.size_mb == Decimal('0')
        assert "timed out" in result.error_message
    
    @patch('os.makedirs')
    def test_create_sandbox_directory(self, mock_makedirs):
        """Test sandbox directory creation"""
        service = GitService()
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        repo_id = "660e8400-e29b-41d4-a716-446655440001"
        
        sandbox_path = service.create_sandbox_directory(project_id, repo_id)
        
        assert project_id in sandbox_path
        assert repo_id in sandbox_path
        mock_makedirs.assert_called_once()
    
    @patch('os.path.exists')
    @patch('shutil.rmtree')
    def test_cleanup_sandbox_directory_success(self, mock_rmtree, mock_exists):
        """Test successful sandbox cleanup"""
        mock_exists.return_value = True
        
        service = GitService()
        result = service.cleanup_sandbox_directory("/tmp/repos/proj/repo")
        
        assert result is True
        mock_rmtree.assert_called_once_with("/tmp/repos/proj/repo")
    
    @patch('os.path.exists')
    def test_cleanup_sandbox_directory_not_exists(self, mock_exists):
        """Test cleanup when directory doesn't exist"""
        mock_exists.return_value = False
        
        service = GitService()
        result = service.cleanup_sandbox_directory("/tmp/repos/proj/repo")
        
        assert result is True  # Already clean
    
    @patch('os.path.exists')
    @patch('shutil.rmtree')
    def test_cleanup_sandbox_directory_failure(self, mock_rmtree, mock_exists):
        """Test cleanup failure"""
        mock_exists.return_value = True
        mock_rmtree.side_effect = Exception("Permission denied")
        
        service = GitService()
        result = service.cleanup_sandbox_directory("/tmp/repos/proj/repo")
        
        assert result is False
    
    def test_prepare_authenticated_url_github(self):
        """Test authenticated URL preparation for GitHub"""
        service = GitService()
        
        git_url = "https://github.com/user/repo.git"
        token = "ghp_test_token_123"
        
        auth_url = service._prepare_authenticated_url(git_url, token)
        
        assert "ghp_test_token_123@github.com" in auth_url
        assert auth_url.startswith("https://")
    
    def test_prepare_authenticated_url_gitlab(self):
        """Test authenticated URL preparation for GitLab"""
        service = GitService()
        
        git_url = "https://gitlab.com/user/repo.git"
        token = "glpat_test_token_123"
        
        auth_url = service._prepare_authenticated_url(git_url, token)
        
        assert "oauth2:glpat_test_token_123@gitlab.com" in auth_url
        assert auth_url.startswith("https://")
    
    def test_prepare_authenticated_url_bitbucket(self):
        """Test authenticated URL preparation for Bitbucket"""
        service = GitService()
        
        git_url = "https://bitbucket.org/user/repo.git"
        token = "test_token_123"
        
        auth_url = service._prepare_authenticated_url(git_url, token)
        
        assert "x-token-auth:test_token_123@bitbucket.org" in auth_url
        assert auth_url.startswith("https://")
    
    @patch('os.path.exists')
    @patch('shutil.rmtree')
    @patch('tempfile.mkdtemp')
    @patch('subprocess.run')
    @patch('os.walk')
    @patch('os.path.getsize')
    def test_estimate_size_cleanup_on_success(self, mock_getsize, mock_walk, 
                                              mock_subprocess, mock_mkdtemp, 
                                              mock_rmtree, mock_exists):
        """Test that temp directory is cleaned up after successful size check"""
        mock_mkdtemp.return_value = "/tmp/git_size_check_123"
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        mock_walk.return_value = [('/tmp/repo', [], ['file.txt'])]
        mock_getsize.return_value = 1024 * 1024  # 1MB
        mock_exists.return_value = True  # Directory exists for cleanup
        
        service = GitService()
        result = service.check_repository_size(
            "https://github.com/user/repo.git",
            "test_token"
        )
        
        # Verify cleanup was called
        mock_rmtree.assert_called_once_with("/tmp/git_size_check_123")
    
    @patch('os.path.exists')
    @patch('shutil.rmtree')
    @patch('tempfile.mkdtemp')
    @patch('subprocess.run')
    def test_estimate_size_cleanup_on_failure(self, mock_subprocess, mock_mkdtemp, 
                                              mock_rmtree, mock_exists):
        """Test that temp directory is cleaned up even on failure"""
        mock_mkdtemp.return_value = "/tmp/git_size_check_123"
        mock_subprocess.side_effect = Exception("Test error")
        mock_exists.return_value = True  # Directory exists for cleanup
        
        service = GitService()
        result = service.check_repository_size(
            "https://github.com/user/repo.git",
            "test_token"
        )
        
        # Verify cleanup was attempted
        mock_rmtree.assert_called_once_with("/tmp/git_size_check_123")
