# backend/app/schemas/project.py
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import ProjectState


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    context: Optional[str] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: ProjectState
    context: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True