# backend/app/schemas/requirement.py
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
import sys

class RequirementBase(BaseModel):
    key: str = Field(..., max_length=50, pattern=r'^[A-Z0-9_-]+$')
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    acceptance_criteria: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('acceptance_criteria')
    @classmethod
    def validate_acceptance_criteria(cls, v, info):
        if info.data.get('priority') in ['high', 'critical'] and not v:
            raise ValueError('High/critical priority requirements must have acceptance criteria')
        return v

class RequirementCreate(RequirementBase):
    pass

class RequirementUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    acceptance_criteria: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class RequirementResponse(RequirementBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    project_id: UUID
    is_coherent: bool
    created_at: datetime
    updated_at: datetime

class RequirementBulkCreate(BaseModel):
    requirements: List[RequirementCreate] = Field(..., max_length=1000)
    
    @model_validator(mode='after')
    def validate_payload_size(self):
        # Rough estimation of payload size
        total_size = sys.getsizeof(self.model_dump_json())
        if total_size > 100 * 1024 * 1024:  # 100MB
            raise ValueError('Payload exceeds 100MB limit')
        if len(self.requirements) > 100:
            raise ValueError('Maximum 100 requirements per bulk operation')
        return self

class RequirementQuestionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    requirement_id: UUID
    question: str
    answer: Optional[str] = None
    is_resolved: bool
    created_at: datetime
    answered_at: Optional[datetime] = None

class RequirementIterationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    requirement_id: UUID
    version: int
    changes: Dict[str, Any]
    created_by: Optional[str]
    created_at: datetime

class RefineRequest(BaseModel):
    context: Optional[str] = None

class FinalizeRequest(BaseModel):
    force: bool = False

class ExportFormat(BaseModel):
    format: Literal["json", "md"] = "json"