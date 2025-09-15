# backend/app/schemas/prompt.py
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PromptGenerateRequest(BaseModel):
    include_code: bool = Field(default=False, description="Include code generation instructions")
    plan_id: Optional[UUID] = Field(None, description="Specific plan ID to use")


class PromptItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phase_id: str
    sequence: int
    title: str
    content_md: str
    metadata: Dict[str, Any] = Field(alias="extra_metadata")
    created_at: datetime


class PromptBundleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    plan_id: UUID
    version: int
    include_code: bool
    context_md: str
    metadata: Dict[str, Any] = Field(alias="extra_metadata")
    total_prompts: int
    prompts: List[PromptItemResponse]
    created_at: datetime
    updated_at: datetime


class PromptBundleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    plan_id: UUID
    version: int
    total_prompts: int
    include_code: bool
    created_at: datetime


class PromptExport(BaseModel):
    bundle_id: UUID
    project_name: str
    generated_at: datetime
    context: str
    prompts: List[Dict[str, Any]]


class TaskPendingResponse(BaseModel):
    """Response when a task is still in progress"""

    message: str
    task_id: str
    project_id: str
    status: str = "pending"
