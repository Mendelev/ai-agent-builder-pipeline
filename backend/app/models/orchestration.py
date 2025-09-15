# backend/app/models/orchestration.py
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.types import JsonType

from .enums import AgentType, EventType, ProjectState


class StateHistory(Base):
    __tablename__ = "state_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    from_state = Column(Enum(ProjectState), nullable=True)
    to_state = Column(Enum(ProjectState), nullable=False)
    transition_reason = Column(Text)
    triggered_by = Column(String(100))  # user_id, agent, system
    extra_metadata = Column("metadata", JsonType, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    project = relationship("Project")

    __table_args__ = (Index("idx_state_history_project", "project_id", "created_at"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    correlation_id = Column(String(100), nullable=True)
    event_type = Column(Enum(EventType), nullable=False)
    agent_type = Column(Enum(AgentType), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(JsonType, default=dict)
    user_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    duration_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    project = relationship("Project")

    __table_args__ = (
        Index("idx_audit_project", "project_id", "created_at"),
        Index("idx_audit_correlation", "correlation_id"),
        Index("idx_audit_event_type", "event_type", "created_at"),
    )


class DomainEvent(Base):
    __tablename__ = "domain_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)  # project_id usually
    aggregate_type = Column(String(50), nullable=False)  # 'project'
    event_name = Column(String(100), nullable=False)
    event_version = Column(Integer, default=1)
    event_data = Column(JsonType, nullable=False)
    extra_metadata = Column("metadata", JsonType, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    processed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_domain_event_aggregate", "aggregate_id", "created_at"),
        Index("idx_domain_event_name", "event_name", "created_at"),
        Index("idx_domain_event_unprocessed", "processed_at", "created_at"),
    )


class DedupKey(Base):
    __tablename__ = "dedup_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    agent_type = Column(Enum(AgentType), nullable=False)
    input_hash = Column(String(64), nullable=False)  # SHA256 hash
    task_id = Column(String(100), nullable=True)  # Celery task ID
    result = Column(JsonType, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    project = relationship("Project")

    __table_args__ = (
        Index("idx_dedup_key", "project_id", "agent_type", "input_hash", unique=True),
        Index("idx_dedup_expires", "expires_at"),
    )
