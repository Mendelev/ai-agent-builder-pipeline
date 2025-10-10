from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.schemas.code_repo import (
    CodeRepositoryConnect, CodeRepositoryResponse, 
    CodeRepositoryRead, CodeRepositoryStatus, RepositoryTooLargeError
)
from app.services.code_repo_service import CodeRepositoryService
from app.core.logging_config import get_logger

router = APIRouter(prefix="/code", tags=["code-repositories"])
logger = get_logger(__name__)


@router.post(
    "/connect", 
    response_model=CodeRepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        413: {"model": RepositoryTooLargeError, "description": "Repository too large"},
        401: {"description": "Invalid Git credentials"},
        422: {"description": "Validation error"}
    }
)
def connect_repository(
    request: CodeRepositoryConnect,
    db: Session = Depends(get_db)
):
    """Connect a Git repository with security validation and size limits"""
    service = CodeRepositoryService(db)
    return service.connect_repository(request)


@router.get(
    "/repos/{repo_id}",
    response_model=CodeRepositoryRead
)
def get_repository(
    repo_id: UUID,
    db: Session = Depends(get_db)
):
    """Get repository information by ID"""
    service = CodeRepositoryService(db)
    repo = service.get_repository(repo_id)
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    return repo


@router.get(
    "/repos/{repo_id}/status",
    response_model=CodeRepositoryStatus
)
def get_repository_status(
    repo_id: UUID,
    db: Session = Depends(get_db)
):
    """Get repository clone status"""
    service = CodeRepositoryService(db)
    repo = service.get_repository(repo_id)
    
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Determine progress message based on status
    progress_messages = {
        "PENDING": "Clone operation queued",
        "CLONING": "Repository clone in progress",
        "COMPLETED": "Repository successfully cloned",
        "FAILED": "Clone operation failed",
        "CLEANING": "Cleanup in progress",
        "CLEANED": "Repository cleaned up"
    }
    
    return CodeRepositoryStatus(
        repo_id=repo.id,
        clone_status=repo.clone_status,
        repository_size_mb=repo.repository_size_mb,
        sandbox_path=repo.sandbox_path,
        progress_message=progress_messages.get(repo.clone_status),
        error_message=None  # Would be populated from task result in full implementation
    )


@router.get(
    "/projects/{project_id}/repos",
    response_model=List[CodeRepositoryRead]
)
def get_project_repositories(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all repositories for a project"""
    service = CodeRepositoryService(db)
    return service.get_repositories_by_project(project_id)
