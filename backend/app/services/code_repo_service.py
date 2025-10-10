from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID, uuid4
from app.models.code_repo import CodeRepository, CloneStatus
from app.schemas.code_repo import CodeRepositoryConnect, CodeRepositoryResponse
from app.services.encryption_service import EncryptionService
from app.services.git_service import GitService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CodeRepositoryService:
    """Service for managing code repository connections"""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption_service = EncryptionService()
        self.git_service = GitService()
    
    def connect_repository(self, request: CodeRepositoryConnect) -> CodeRepositoryResponse:
        """Connect a Git repository with security validation"""
        try:
            # Log request (with masked token)
            logger.info(
                "Repository connection requested",
                extra={
                    "git_url": request.git_url,
                    "project_id": str(request.project_id),
                    "token_masked": EncryptionService.mask_token(request.access_token)
                }
            )
            
            # Step 1: Pre-check repository size
            size_result = self.git_service.check_repository_size(
                request.git_url, 
                request.access_token
            )
            
            if not size_result.is_valid:
                logger.warning(
                    "Repository rejected due to size",
                    extra={
                        "git_url": request.git_url,
                        "project_id": str(request.project_id),
                        "estimated_size_mb": float(size_result.size_mb),
                        "error": size_result.error_message
                    }
                )
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=413,
                    detail={
                        "error": "repository_too_large",
                        "message": size_result.error_message,
                        "estimated_size_mb": float(size_result.size_mb),
                        "limit_mb": self.git_service.max_repo_size_mb
                    }
                )
            
            # Step 2: Encrypt access token
            token_ciphertext, key_id = self.encryption_service.encrypt_token(
                request.access_token,
                str(request.project_id)
            )
            
            # Step 3: Create database record
            repo = CodeRepository(
                project_id=request.project_id,
                git_url=request.git_url,
                token_ciphertext=token_ciphertext,
                token_kid=key_id,
                repository_size_mb=size_result.size_mb,
                clone_status=CloneStatus.PENDING
            )
            
            self.db.add(repo)
            self.db.commit()
            self.db.refresh(repo)
            
            # Step 4: Queue clone task (import here to avoid circular dependency)
            from app.tasks.git_clone import clone_repository_task
            task = clone_repository_task.delay(
                repo_id=str(repo.id),
                project_id=str(request.project_id)
            )
            
            logger.info(
                "Repository connection created successfully",
                extra={
                    "repo_id": str(repo.id),
                    "project_id": str(request.project_id),
                    "task_id": str(task.id),
                    "estimated_size_mb": float(size_result.size_mb)
                }
            )
            
            # Return response (no sensitive data)
            return CodeRepositoryResponse(
                repo_id=repo.id,
                git_url=repo.git_url,
                connected=True,
                task_id=UUID(task.id),
                estimated_size_mb=repo.repository_size_mb,
                clone_status=repo.clone_status,
                created_at=repo.created_at
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Repository connection failed",
                extra={
                    "git_url": request.git_url,
                    "project_id": str(request.project_id),
                    "error": str(e)
                }
            )
            raise
    
    def get_repository(self, repo_id: UUID) -> Optional[CodeRepository]:
        """Get repository by ID"""
        return self.db.query(CodeRepository).filter(CodeRepository.id == repo_id).first()
    
    def get_repositories_by_project(self, project_id: UUID) -> List[CodeRepository]:
        """Get all repositories for a project"""
        return self.db.query(CodeRepository).filter(
            CodeRepository.project_id == project_id
        ).all()
    
    def update_clone_status(self, repo_id: UUID, status: str, 
                          sandbox_path: Optional[str] = None,
                          actual_size_mb: Optional[float] = None) -> bool:
        """Update repository clone status"""
        try:
            repo = self.get_repository(repo_id)
            if not repo:
                return False
            
            repo.clone_status = status
            if sandbox_path:
                repo.sandbox_path = sandbox_path
            if actual_size_mb:
                repo.repository_size_mb = actual_size_mb
            
            self.db.commit()
            
            logger.info(
                "Repository status updated",
                extra={
                    "repo_id": str(repo_id),
                    "status": status,
                    "sandbox_path": sandbox_path
                }
            )
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to update repository status",
                extra={"repo_id": str(repo_id), "error": str(e)}
            )
            return False
    
    def decrypt_repository_token(self, repo: CodeRepository) -> str:
        """Decrypt repository access token for use"""
        return self.encryption_service.decrypt_token(
            repo.token_ciphertext,
            repo.token_kid,
            str(repo.project_id)
        )
