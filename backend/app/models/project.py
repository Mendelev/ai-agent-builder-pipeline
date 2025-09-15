# backend/app/models/project.py
import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

from .enums import ProjectState


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(ProjectState), default=ProjectState.DRAFT, nullable=False)
    context = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="project", cascade="all, delete-orphan")
    prompt_bundles = relationship("PromptBundle", back_populates="project", cascade="all, delete-orphan")
