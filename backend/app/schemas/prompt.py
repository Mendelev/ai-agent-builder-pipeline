# backend/app/schemas/prompt.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

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
    metadata: Dict[str, Any]
    created_at: datetime

class PromptBundleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    project_id: UUID
    plan_id: UUID
    version: int
    include_code: bool
    context_md: str
    metadata: Dict[str, Any]
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