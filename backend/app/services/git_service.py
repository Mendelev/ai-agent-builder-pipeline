import subprocess
import tempfile
import shutil
import os
from pathlib import Path
from typing import Tuple, Optional
from decimal import Decimal
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class GitSizeCheckResult:
    def __init__(self, size_mb: Decimal, is_valid: bool, error_message: Optional[str] = None):
        self.size_mb = size_mb
        self.is_valid = is_valid
        self.error_message = error_message


class GitService:
    """Service for Git operations with security and size validation"""
    
    def __init__(self):
        self.max_repo_size_mb = getattr(settings, 'MAX_REPO_SIZE_MB', 100)
        self.git_timeout = getattr(settings, 'GIT_CLONE_TIMEOUT', 300)
        self.sandbox_base = getattr(settings, 'SANDBOX_BASE_PATH', '/tmp/repos')
    
    def check_repository_size(self, git_url: str, access_token: str) -> GitSizeCheckResult:
        """
        Check repository size using shallow clone and pack analysis
        
        Args:
            git_url: Repository URL
            access_token: Git access token
            
        Returns:
            GitSizeCheckResult with size validation
        """
        temp_dir = None
        try:
            # Create temporary directory for size check
            temp_dir = tempfile.mkdtemp(prefix='git_size_check_')
            
            # Prepare authenticated URL
            auth_url = self._prepare_authenticated_url(git_url, access_token)
            
            logger.info(
                "Starting repository size check",
                extra={
                    "git_url": git_url,  # Log original URL without token
                    "temp_dir": temp_dir
                }
            )
            
            # Step 1: Try shallow clone to estimate size
            size_mb = self._estimate_size_with_shallow_clone(auth_url, temp_dir)
            
            # Step 2: Validate against limit
            is_valid = size_mb <= self.max_repo_size_mb
            
            logger.info(
                "Repository size check completed",
                extra={
                    "git_url": git_url,
                    "estimated_size_mb": float(size_mb),
                    "is_valid": is_valid,
                    "limit_mb": self.max_repo_size_mb
                }
            )
            
            return GitSizeCheckResult(
                size_mb=size_mb,
                is_valid=is_valid,
                error_message=None if is_valid else f"Repository size {size_mb}MB exceeds limit of {self.max_repo_size_mb}MB"
            )
            
        except subprocess.TimeoutExpired:
            error_msg = f"Repository size check timed out after {self.git_timeout} seconds"
            logger.error(
                "Git operation timeout",
                extra={"git_url": git_url, "timeout": self.git_timeout}
            )
            return GitSizeCheckResult(Decimal('0'), False, error_msg)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git operation failed: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(
                "Git command failed",
                extra={
                    "git_url": git_url,
                    "return_code": e.returncode,
                    "error": error_msg
                }
            )
            return GitSizeCheckResult(Decimal('0'), False, error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error during size check: {str(e)}"
            logger.error(
                "Unexpected error in size check",
                extra={"git_url": git_url, "error": str(e)}
            )
            return GitSizeCheckResult(Decimal('0'), False, error_msg)
            
        finally:
            # Always cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")
    
    def _estimate_size_with_shallow_clone(self, auth_url: str, temp_dir: str) -> Decimal:
        """Estimate repository size using shallow clone"""
        clone_path = os.path.join(temp_dir, 'repo')
        
        # Perform shallow clone with depth=1
        cmd = [
            'git', 'clone',
            '--depth=1',
            '--single-branch',
            '--no-tags',
            auth_url,
            clone_path
        ]
        
        result = subprocess.run(
            cmd,
            timeout=self.git_timeout,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, 
                stdout=result.stdout, stderr=result.stderr
            )
        
        # Calculate directory size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(clone_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError):
                    continue  # Skip files we can't access
        
        # Convert to MB and apply estimation multiplier
        # Shallow clone is typically 10-30% of full repo size
        size_mb = Decimal(total_size) / Decimal(1024 * 1024)
        estimated_full_size = size_mb * Decimal('3.5')  # Conservative estimate
        
        return estimated_full_size
    
    def create_sandbox_directory(self, project_id: str, repo_id: str) -> str:
        """Create isolated sandbox directory for repository"""
        sandbox_path = os.path.join(self.sandbox_base, project_id, repo_id)
        os.makedirs(sandbox_path, exist_ok=True, mode=0o755)
        
        logger.info(
            "Created sandbox directory",
            extra={
                "project_id": project_id,
                "repo_id": repo_id,
                "sandbox_path": sandbox_path
            }
        )
        
        return sandbox_path
    
    def cleanup_sandbox_directory(self, sandbox_path: str) -> bool:
        """Clean up sandbox directory"""
        try:
            if os.path.exists(sandbox_path):
                shutil.rmtree(sandbox_path)
                logger.info(f"Cleaned up sandbox directory: {sandbox_path}")
                return True
            return True  # Already clean
        except Exception as e:
            logger.error(
                "Failed to cleanup sandbox directory",
                extra={"sandbox_path": sandbox_path, "error": str(e)}
            )
            return False
    
    def _prepare_authenticated_url(self, git_url: str, access_token: str) -> str:
        """Prepare Git URL with authentication token"""
        if git_url.startswith('https://github.com/'):
            # GitHub: https://token@github.com/user/repo.git
            return git_url.replace('https://', f'https://{access_token}@')
        elif git_url.startswith('https://gitlab.com/'):
            # GitLab: https://oauth2:token@gitlab.com/user/repo.git
            return git_url.replace('https://', f'https://oauth2:{access_token}@')
        elif git_url.startswith('https://bitbucket.org/'):
            # Bitbucket: https://x-token-auth:token@bitbucket.org/user/repo.git
            return git_url.replace('https://', f'https://x-token-auth:{access_token}@')
        else:
            # Generic: try token-based auth
            return git_url.replace('https://', f'https://{access_token}@')
