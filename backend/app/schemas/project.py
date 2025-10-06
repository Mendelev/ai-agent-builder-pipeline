from pydantic import BaseModel, Field, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    created_by: Optional[UUID] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    status: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['DRAFT', 'REQS_REFINING', 'REQS_READY', 'CODE_VALIDATION_REQUESTED', 
                         'CODE_VALIDATED', 'PLAN_READY', 'PROMPTS_READY', 'DONE', 'BLOCKED']
        if v and v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v


class ProjectRead(BaseModel):
    id: UUID
    name: str
    status: str
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequirementData(BaseModel):
    code: str = Field(..., min_length=1)
    descricao: str = Field(..., min_length=1)
    criterios_aceitacao: List[str] = Field(default_factory=list)
    prioridade: str = Field(default="MEDIUM")
    dependencias: List[str] = Field(default_factory=list)
    testabilidade: Optional[str] = None
    waiver_reason: Optional[str] = None

    @validator('prioridade')
    def validate_prioridade(cls, v):
        valid = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if v not in valid:
            raise ValueError(f'Invalid priority. Must be one of: {valid}')
        return v


class RequirementUpsert(BaseModel):
    code: str
    descricao: str
    criterios_aceitacao: List[str] = Field(default_factory=list)
    prioridade: str = Field(default="MEDIUM")
    dependencias: List[str] = Field(default_factory=list)
    testabilidade: Optional[str] = None
    waiver_reason: Optional[str] = None


class RequirementRead(BaseModel):
    id: UUID
    project_id: UUID
    code: str
    version: int
    data: RequirementData
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequirementVersionRead(BaseModel):
    id: UUID
    requirement_id: UUID
    version: int
    data: RequirementData
    created_at: datetime

    class Config:
        from_attributes = True


class RequirementsBulkUpsert(BaseModel):
    requirements: List[RequirementUpsert]
