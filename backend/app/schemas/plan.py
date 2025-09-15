# backend/app/schemas/plan.py
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanConstraints(BaseModel):
    deadline_days: Optional[int] = Field(None, ge=1, le=365)
    team_size: Optional[int] = Field(None, ge=1, le=100)
    max_parallel_phases: Optional[int] = Field(None, ge=1, le=10)
    nfrs: Optional[List[str]] = Field(default_factory=list)
    budget: Optional[float] = Field(None, ge=0)


class PlanGenerateRequest(BaseModel):
    source: Literal["requirements", "checklist", "hybrid"] = "requirements"
    use_code: bool = False
    include_checklist: bool = False
    constraints: Optional[PlanConstraints] = None


class PlanPhaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phase_id: str
    sequence: int
    title: str
    objective: str
    deliverables: List[str]
    activities: List[str]
    dependencies: List[str]
    estimated_days: float
    risk_level: Literal["low", "medium", "high", "critical"]
    risks: List[str]
    requirements_covered: List[str]
    definition_of_done: List[str]
    resources_required: Dict[str, int]
    created_at: datetime


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    version: int
    status: str
    source: str
    use_code: bool
    include_checklist: bool
    constraints: Dict[str, Any]
    metadata: Dict[str, Any] = Field(alias="extra_metadata")
    total_duration_days: float
    risk_score: float
    coverage_percentage: float
    phases: List[PlanPhaseResponse]
    created_at: datetime
    updated_at: datetime


class PlanSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    version: int
    status: str
    total_phases: int
    total_duration_days: float
    coverage_percentage: float
    risk_score: float
    created_at: datetime


class TaskPendingResponse(BaseModel):
    """Response when a task is still in progress"""

    message: str
    task_id: str
    project_id: str
    status: str = "pending"
