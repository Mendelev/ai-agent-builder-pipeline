from sqlalchemy import Column, Text, DateTime, ForeignKey, LargeBinary, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
from app.core.types import UUID


class CodeRepository(Base):
    __tablename__ = "code_repos"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    git_url = Column(Text, nullable=False)
    token_ciphertext = Column(LargeBinary, nullable=False)
    token_kid = Column(Text, nullable=False)  # KMS Key ID
    repository_size_mb = Column(Numeric(10, 2), nullable=True)
    clone_status = Column(Text, nullable=False, default="PENDING")
    sandbox_path = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="code_repositories")


# Status constants
class CloneStatus:
    PENDING = "PENDING"
    CLONING = "CLONING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CLEANING = "CLEANING"
    CLEANED = "CLEANED"
