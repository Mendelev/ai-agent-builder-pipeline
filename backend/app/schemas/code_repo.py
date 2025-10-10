from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import re


class CodeRepositoryConnect(BaseModel):
    """Schema for connecting a Git repository"""
    git_url: str = Field(..., min_length=1, max_length=2048)
    access_token: str = Field(..., min_length=1, max_length=1024)
    project_id: UUID
    
    @field_validator('git_url')
    @classmethod
    def validate_git_url(cls, v):
        # Basic Git URL validation
        git_patterns = [
            r'^https://github\.com/[\w\-\.]+/[\w\-\.]+(\.git)?/?$',
            r'^https://gitlab\.com/[\w\-\.]+/[\w\-\.]+(\.git)?/?$',
            r'^https://bitbucket\.org/[\w\-\.]+/[\w\-\.]+(\.git)?/?$',
            r'^https://[\w\-\.]+/[\w\-\./]+(\.git)?/?$'  # Generic Git hosting
        ]
        
        if not any(re.match(pattern, v) for pattern in git_patterns):
            raise ValueError('Invalid Git repository URL format')
        return v
    
    @field_validator('access_token')
    @classmethod
    def validate_access_token(cls, v):
        # Ensure token looks valid (not empty, has reasonable length)
        if len(v.strip()) < 10:
            raise ValueError('Access token appears to be invalid')
        return v.strip()


class CodeRepositoryResponse(BaseModel):
    """Schema for repository connection response"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    repo_id: UUID = Field(alias="id")
    git_url: str
    connected: bool = True
    task_id: Optional[UUID] = None
    estimated_size_mb: Optional[Decimal] = Field(alias="repository_size_mb")
    clone_status: str
    created_at: datetime


class CodeRepositoryRead(BaseModel):
    """Schema for reading repository information"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    project_id: UUID
    git_url: str
    repository_size_mb: Optional[Decimal]
    clone_status: str
    sandbox_path: Optional[str]
    created_at: datetime
    updated_at: datetime


class CodeRepositoryStatus(BaseModel):
    """Schema for repository status response"""
    repo_id: UUID
    clone_status: str
    repository_size_mb: Optional[Decimal]
    sandbox_path: Optional[str]
    progress_message: Optional[str] = None
    error_message: Optional[str] = None


class RepositoryTooLargeError(BaseModel):
    """Schema for repository size error response"""
    error: str = "repository_too_large"
    message: str
    estimated_size_mb: Decimal
    limit_mb: int = 100
