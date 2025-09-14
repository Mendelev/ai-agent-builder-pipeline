# backend/app/schemas/orchestration.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum

class ProjectStateEnum(str, Enum):
    DRAFT = "DRAFT"
    REQS_REFINING = "REQS_REFINING"
    REQS_READY = "REQS_READY"
    CODE_VALIDATED = "CODE_VALIDATED"
    PLAN_READY = "PLAN_READY"
    PROMPTS_READY = "PROMPTS_READY"
    DONE = "DONE"
    BLOCKED = "BLOCKED"

class AgentTypeEnum(str, Enum):
    REQUIREMENTS = "REQUIREMENTS"
    REFINE = "REFINE"
    PLAN = "PLAN"
    PROMPTS = "PROMPTS"
    VALIDATION = "VALIDATION"

class ProjectStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    state: ProjectStateEnum
    created_at: datetime
    updated_at: datetime
    recent_events: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class StateTransition(BaseModel):
    from_state: Optional[ProjectStateEnum]
    to_state: ProjectStateEnum
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    project_id: UUID
    correlation_id: Optional[str]
    event_type: str
    agent_type: Optional[str]
    action: str
    details: Dict[str, Any]
    user_id: Optional[str]
    duration_ms: Optional[float]
    success: bool
    error_message: Optional[str]
    created_at: datetime

class AuditLogPage(BaseModel):
    items: List[AuditLogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int

class RetryRequest(BaseModel):
    agent: AgentTypeEnum
    force: bool = False
    metadata: Optional[Dict[str, Any]] = None

class RetryResponse(BaseModel):
    task_id: str
    agent: str
    status: Literal["queued", "running", "cached"]
    message: str