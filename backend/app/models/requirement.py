# backend/app/models/requirement.py
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DateTime, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid
from app.core.database import Base
from app.models.types import JsonType

class Requirement(Base):
    __tablename__ = "requirements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    key = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(20), nullable=False, default="medium")
    acceptance_criteria = Column(JsonType, default=list)
    dependencies = Column(JsonType, default=list)
    extra_metadata = Column('metadata', JsonType, default=dict)
    is_coherent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="requirements")
    iterations = relationship("RequirementIteration", back_populates="requirement", cascade="all, delete-orphan")
    questions = relationship("RequirementQuestion", back_populates="requirement", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_project_key', 'project_id', 'key', unique=True),
        Index('idx_acceptance_criteria_gin', 'acceptance_criteria', postgresql_using='gin'),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name="check_priority"),
    )

class RequirementIteration(Base):
    __tablename__ = "requirement_iterations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False)
    version = Column(Integer, nullable=False)
    changes = Column(JsonType, default=dict)
    created_by = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    
    # Relationships
    requirement = relationship("Requirement", back_populates="iterations")
    
    __table_args__ = (
        Index('idx_requirement_version', 'requirement_id', 'version', unique=True),
    )

class RequirementQuestion(Base):
    __tablename__ = "requirement_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    answered_at = Column(DateTime)
    
    # Relationships
    requirement = relationship("Requirement", back_populates="questions")