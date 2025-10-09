"""
QA Session model for requirement refinement
"""
from sqlalchemy import Column, Text, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from app.core.types import UUID, JSONB


class QASession(Base):
    """
    Stores Q&A sessions for requirement refinement.
    Each session represents one round of questions/answers.
    """
    __tablename__ = "qa_sessions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    request_id = Column(String(36), nullable=False, unique=True, index=True)
    round = Column(Integer, nullable=False, default=1)
    questions = Column(JSONB, nullable=False)  # List of question objects
    answers = Column(JSONB, nullable=True)  # List of answer objects (null until answered)
    quality_flags = Column(JSONB, nullable=True)  # Quality metrics for questions
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="qa_sessions")
