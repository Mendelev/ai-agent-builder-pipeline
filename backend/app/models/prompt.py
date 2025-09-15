# backend/app/models/prompt.py
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.types import JsonType


class PromptBundle(Base):
    __tablename__ = "prompt_bundles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    include_code = Column(Boolean, default=False)
    context_md = Column(Text, nullable=False)  # General context markdown
    extra_metadata = Column("metadata", JsonType, default=dict)
    total_prompts = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    project = relationship("Project")
    plan = relationship("Plan")
    prompts = relationship("PromptItem", back_populates="bundle", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_bundle_project", "project_id", "created_at"),
        Index("idx_bundle_plan", "plan_id"),
    )


class PromptItem(Base):
    __tablename__ = "prompt_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bundle_id = Column(UUID(as_uuid=True), ForeignKey("prompt_bundles.id"), nullable=False)
    phase_id = Column(String(20), nullable=False)  # PH-01, PH-02, etc
    sequence = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content_md = Column(Text, nullable=False)  # Prompt markdown content
    extra_metadata = Column("metadata", JsonType, default=dict)  # {requirements: [], estimated_tokens: 0}
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    bundle = relationship("PromptBundle", back_populates="prompts")

    __table_args__ = (
        Index("idx_prompt_bundle_phase", "bundle_id", "phase_id", unique=True),
        Index("idx_prompt_sequence", "bundle_id", "sequence"),
    )
