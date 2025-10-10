import os
import subprocess
import shutil
from celery import Celery
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.code_repo_service import CodeRepositoryService
from app.services.git_service import GitService
from app.models.code_repo import CloneStatus
from app.core.logging_config import get_logger
from uuid import UUID
from decimal import Decimal

# Import Celery app
from app.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def clone_repository_task(self, repo_id: str, project_id: str):
    """
    Celery task to clone repository in isolated sandbox
    
    Args:
        repo_id: Repository UUID
        project_id: Project UUID
    """
    db: Session = SessionLocal()
    
    try:
        logger.info(
            "Starting repository clone task",
            extra={
                "task_id": self.request.id,
                "repo_id": repo_id,
                "project_id": project_id
            }
        )
        
        service = CodeRepositoryService(db)
        git_service = GitService()
        
        # Get repository record
        repo = service.get_repository(UUID(repo_id))
        if not repo:
            raise Exception(f"Repository {repo_id} not found")
        
        # Update status to CLONING
        service.update_clone_status(UUID(repo_id), CloneStatus.CLONING)
        
        # Create sandbox directory
        sandbox_path = git_service.create_sandbox_directory(project_id, repo_id)
        
        # Decrypt token for Git operations
        access_token = service.decrypt_repository_token(repo)
        
        # Perform full clone in sandbox
        clone_path = os.path.join(sandbox_path, 'repository')
        actual_size_mb = _perform_full_clone(
            repo.git_url, 
            access_token, 
            clone_path, 
            git_service.git_timeout
        )
        
        # Update status to COMPLETED with actual size
        service.update_clone_status(
            UUID(repo_id), 
            CloneStatus.COMPLETED,
            sandbox_path=sandbox_path,
            actual_size_mb=float(actual_size_mb)
        )
        
        logger.info(
            "Repository clone completed successfully",
            extra={
                "task_id": self.request.id,
                "repo_id": repo_id,
                "actual_size_mb": float(actual_size_mb),
                "sandbox_path": sandbox_path
            }
        )
        
        return {
            "status": "completed",
            "repo_id": repo_id,
            "sandbox_path": sandbox_path,
            "actual_size_mb": float(actual_size_mb)
        }
        
    except Exception as e:
        logger.error(
            "Repository clone failed",
            extra={
                "task_id": self.request.id,
                "repo_id": repo_id,
                "project_id": project_id,
                "error": str(e)
            }
        )
        
        # Update status to FAILED
        try:
            service = CodeRepositoryService(db)
            service.update_clone_status(UUID(repo_id), CloneStatus.FAILED)
        except Exception as update_error:
            logger.error(f"Failed to update status to FAILED: {update_error}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying clone task (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))  # Exponential backoff
        
        return {
            "status": "failed",
            "repo_id": repo_id,
            "error": str(e)
        }
        
    finally:
        db.close()


@celery_app.task
def cleanup_repository_task(repo_id: str):
    """
    Celery task to cleanup repository sandbox
    
    Args:
        repo_id: Repository UUID
    """
    db: Session = SessionLocal()
    
    try:
        logger.info(
            "Starting repository cleanup task",
            extra={"repo_id": repo_id}
        )
        
        service = CodeRepositoryService(db)
        git_service = GitService()
        
        # Get repository record
        repo = service.get_repository(UUID(repo_id))
        if not repo or not repo.sandbox_path:
            logger.warning(f"Repository {repo_id} not found or no sandbox path")
            return {"status": "skipped", "repo_id": repo_id}
        
        # Update status to CLEANING
        service.update_clone_status(UUID(repo_id), CloneStatus.CLEANING)
        
        # Cleanup sandbox directory
        success = git_service.cleanup_sandbox_directory(repo.sandbox_path)
        
        if success:
            # Update status to CLEANED and clear sandbox path
            service.update_clone_status(
                UUID(repo_id), 
                CloneStatus.CLEANED, 
                sandbox_path=None
            )
            
            logger.info(
                "Repository cleanup completed",
                extra={"repo_id": repo_id}
            )
            
            return {"status": "cleaned", "repo_id": repo_id}
        else:
            logger.error(
                "Repository cleanup failed",
                extra={"repo_id": repo_id}
            )
            return {"status": "cleanup_failed", "repo_id": repo_id}
        
    except Exception as e:
        logger.error(
            "Repository cleanup task failed",
            extra={"repo_id": repo_id, "error": str(e)}
        )
        return {"status": "error", "repo_id": repo_id, "error": str(e)}
        
    finally:
        db.close()


def _perform_full_clone(git_url: str, access_token: str, clone_path: str, timeout: int) -> Decimal:
    """
    Perform full Git clone and return actual repository size
    
    Args:
        git_url: Repository URL
        access_token: Git access token
        clone_path: Local path for clone
        timeout: Operation timeout in seconds
        
    Returns:
        Actual repository size in MB
    """
    # Prepare authenticated URL
    if git_url.startswith('https://github.com/'):
        auth_url = git_url.replace('https://', f'https://{access_token}@')
    elif git_url.startswith('https://gitlab.com/'):
        auth_url = git_url.replace('https://', f'https://oauth2:{access_token}@')
    else:
        auth_url = git_url.replace('https://', f'https://{access_token}@')
    
    # Perform full clone
    cmd = ['git', 'clone', auth_url, clone_path]
    
    result = subprocess.run(
        cmd,
        timeout=timeout,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd,
            stdout=result.stdout, stderr=result.stderr
        )
    
    # Calculate actual size
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(clone_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, IOError):
                continue
    
    # Convert to MB
    size_mb = Decimal(total_size) / Decimal(1024 * 1024)
    return size_mb
