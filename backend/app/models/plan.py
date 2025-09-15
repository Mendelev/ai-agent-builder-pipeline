# backend/app/models/plan.py
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, DateTime, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base
from app.models.types import JsonType

class PlanStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(Enum(PlanStatus), default=PlanStatus.DRAFT, nullable=False)
    source = Column(String(50), nullable=False)  # 'requirements', 'checklist', 'hybrid'
    use_code = Column(Boolean, default=False)
    include_checklist = Column(Boolean, default=False)
    constraints = Column(JsonType, default=dict)  # {deadline, team_size, nfrs}
    extra_metadata = Column('metadata', JsonType, default=dict)
    total_duration_days = Column(Float, default=0)
    risk_score = Column(Float, default=0)
    coverage_percentage = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project = relationship("Project")
    phases = relationship("PlanPhase", back_populates="plan", cascade="all, delete-orphan", order_by="PlanPhase.sequence")

class PlanPhase(Base):
    __tablename__ = "plan_phases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    phase_id = Column(String(20), nullable=False)  # PH-01, PH-02, etc
    sequence = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    objective = Column(Text, nullable=False)
    deliverables = Column(JsonType, default=list)
    activities = Column(JsonType, default=list)
    dependencies = Column(JsonType, default=list)  # Phase IDs this depends on
    estimated_days = Column(Float, nullable=False, default=0)
    risk_level = Column(String(20), default="medium")  # low, medium, high, critical
    risks = Column(JsonType, default=list)
    requirements_covered = Column(JsonType, default=list)  # Requirement keys
    definition_of_done = Column(JsonType, default=list)
    resources_required = Column(JsonType, default=dict)  # {developers: 2, qa: 1}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    plan = relationship("Plan", back_populates="phases")
    
    __table_args__ = (
        Index('idx_plan_phase', 'plan_id', 'phase_id', unique=True),
        Index('idx_phase_sequence', 'plan_id', 'sequence'),
    )