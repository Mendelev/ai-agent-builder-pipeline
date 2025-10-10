from sqlalchemy import Column, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from app.core.types import UUID, JSONB


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="DRAFT")
    requirements_version = Column(Integer, nullable=False, default=1)
    created_by = Column(UUID, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    qa_sessions = relationship("QASession", back_populates="project", cascade="all, delete-orphan")


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code = Column(Text, nullable=False)
    version = Column(JSONB, nullable=False, default=1)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="requirements")
    versions = relationship("RequirementVersion", back_populates="requirement", cascade="all, delete-orphan")


class RequirementVersion(Base):
    __tablename__ = "requirements_versions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    version = Column(JSONB, nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    requirement = relationship("Requirement", back_populates="versions")


class RequirementsGatewayAudit(Base):
    __tablename__ = "requirements_gateway_audit"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    correlation_id = Column(UUID, nullable=False)
    request_id = Column(UUID, nullable=False, unique=True)
    action = Column(Text, nullable=False)
    from_state = Column(Text, nullable=False)
    to_state = Column(Text, nullable=False)
    user_id = Column(UUID, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    project = relationship("Project")
