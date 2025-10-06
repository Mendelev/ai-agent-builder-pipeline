from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="DRAFT")
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    code = Column(Text, nullable=False)
    version = Column(JSONB, nullable=False, default=1)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="requirements")
    versions = relationship("RequirementVersion", back_populates="requirement", cascade="all, delete-orphan")


class RequirementVersion(Base):
    __tablename__ = "requirements_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False)
    version = Column(JSONB, nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    requirement = relationship("Requirement", back_populates="versions")
