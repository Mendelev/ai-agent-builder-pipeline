from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class PriorityEnum(str, Enum):
    must = "must"
    should = "should"
    could = "could"
    wont = "wont"


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    created_by: Optional[UUID] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['DRAFT', 'REQS_REFINING', 'REQS_READY', 'CODE_VALIDATION_REQUESTED', 
                         'CODE_VALIDATED', 'PLAN_READY', 'PROMPTS_READY', 'DONE', 'BLOCKED']
        if v and v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    status: str
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class RequirementData(BaseModel):
    code: str = Field(..., min_length=1)
    descricao: str = Field(..., min_length=1)
    criterios_aceitacao: List[str] = Field(default_factory=list)
    prioridade: str = Field(default="should")
    dependencias: List[str] = Field(default_factory=list)
    testabilidade: Optional[str] = None
    waiver_reason: Optional[str] = None

    @field_validator('prioridade')
    @classmethod
    def validate_prioridade(cls, v):
        valid = ['must', 'should', 'could', 'wont']
        if v not in valid:
            raise ValueError(f'Invalid priority. Must be one of: {valid}')
        return v


class RequirementUpsert(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    descricao: str = Field(..., min_length=1, max_length=2000)
    criterios_aceitacao: List[str] = Field(...)
    prioridade: PriorityEnum = Field(default=PriorityEnum.should)
    dependencias: List[str] = Field(default_factory=list)
    testabilidade: Optional[str] = Field(None, max_length=500)
    waiver_reason: Optional[str] = Field(None, max_length=1000)

    @field_validator('criterios_aceitacao')
    @classmethod
    def validate_criterios(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one acceptance criterion is required')
        
        # Remove empty strings
        cleaned = [c.strip() for c in v if c.strip()]
        if not cleaned:
            raise ValueError('At least one non-empty acceptance criterion is required')
        
        return cleaned

    @field_validator('testabilidade')
    @classmethod
    def validate_testabilidade(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None

    @model_validator(mode='after')
    def validate_waiver(self):
        # If waiver_reason is provided, log a warning (handled in service layer)
        if self.waiver_reason and len(self.waiver_reason.strip()) > 0:
            # Add a marker for service layer if needed
            pass
        
        return self


class RequirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    project_id: UUID
    code: str
    version: int
    data: RequirementData
    created_at: datetime
    updated_at: datetime


class RequirementVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    requirement_id: UUID
    version: int
    data: RequirementData
    created_at: datetime


class RequirementsBulkUpsert(BaseModel):
    requirements: List[RequirementUpsert]


class ValidationResult(BaseModel):
    """Validation result with errors and warnings"""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)


class RequirementUpdateResponse(BaseModel):
    """Response for requirement update with validation info"""
    requirement: RequirementRead
    validation: ValidationResult
