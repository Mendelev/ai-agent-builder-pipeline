# backend/app/models/orchestration.py
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, DateTime, Enum, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base

class ProjectState(str, enum.Enum):
    DRAFT = "DRAFT"
    REQS_REFINING = "REQS_REFINING"
    REQS_READY = "REQS_READY"
    CODE_VALIDATED = "CODE_VALIDATED"
    PLAN_READY = "PLAN_READY"
    PROMPTS_READY = "PROMPTS_READY"
    DONE = "DONE"
    BLOCKED = "BLOCKED"

class AgentType(str, enum.Enum):
    REQUIREMENTS = "REQUIREMENTS"
    REFINE = "REFINE"
    PLAN = "PLAN"
    PROMPTS = "PROMPTS"
    VALIDATION = "VALIDATION"

class EventType(str, enum.Enum):
    STATE_TRANSITION = "STATE_TRANSITION"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    RETRY_ATTEMPTED = "RETRY_ATTEMPTED"
    USER_ACTION = "USER_ACTION"
    SYSTEM_EVENT = "SYSTEM_EVENT"

class StateHistory(Base):
    __tablename__ = "state_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    from_state = Column(Enum(ProjectState), nullable=True)
    to_state = Column(Enum(ProjectState), nullable=False)
    transition_reason = Column(Text)
    triggered_by = Column(String(100))  # user_id, agent, system
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    project = relationship("Project")
    
    __table_args__ = (
        Index('idx_state_history_project', 'project_id', 'created_at'),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    correlation_id = Column(String(100), nullable=True)
    event_type = Column(Enum(EventType), nullable=False)
    agent_type = Column(Enum(AgentType), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(JSONB, default=dict)
    user_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    duration_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    project = relationship("Project")
    
    __table_args__ = (
        Index('idx_audit_project', 'project_id', 'created_at'),
        Index('idx_audit_correlation', 'correlation_id'),
        Index('idx_audit_event_type', 'event_type', 'created_at'),
    )

class DomainEvent(Base):
    __tablename__ = "domain_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)  # project_id usually
    aggregate_type = Column(String(50), nullable=False)  # 'project'
    event_name = Column(String(100), nullable=False)
    event_version = Column(Integer, default=1)
    event_data = Column(JSONB, nullable=False)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_domain_event_aggregate', 'aggregate_id', 'created_at'),
        Index('idx_domain_event_name', 'event_name', 'created_at'),
        Index('idx_domain_event_unprocessed', 'processed_at', 'created_at'),
    )

class DedupKey(Base):
    __tablename__ = "dedup_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    agent_type = Column(Enum(AgentType), nullable=False)
    input_hash = Column(String(64), nullable=False)  # SHA256 hash
    task_id = Column(String(100), nullable=True)  # Celery task ID
    result = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    project = relationship("Project")
    
    __table_args__ = (
        Index('idx_dedup_key', 'project_id', 'agent_type', 'input_hash', unique=True),
        Index('idx_dedup_expires', 'expires_at'),
    )