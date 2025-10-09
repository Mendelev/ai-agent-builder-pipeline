"""
Pydantic schemas for QA Sessions (Requirement Refinement)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class QuestionCategory(str, Enum):
    """Category of question for requirement refinement"""
    TESTABILITY = "testability"
    AMBIGUITY = "ambiguity"
    DEPENDENCIES = "dependencies"
    SCOPE = "scope"
    CONSTRAINTS = "constraints"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"


class Question(BaseModel):
    """Individual question in a Q&A session"""
    id: str = Field(..., description="Unique identifier for the question")
    category: QuestionCategory = Field(..., description="Category of the question")
    text: str = Field(..., min_length=10, max_length=1000, description="Question text")
    context: Optional[str] = Field(None, description="Additional context for the question")
    priority: int = Field(default=1, ge=1, le=5, description="Priority (1=highest, 5=lowest)")


class Answer(BaseModel):
    """Individual answer to a question"""
    question_id: str = Field(..., description="ID of the question being answered")
    text: str = Field(..., min_length=1, max_length=2000, description="Answer text")
    confidence: Optional[int] = Field(None, ge=1, le=5, description="Confidence in answer (1=low, 5=high)")


class QualityFlags(BaseModel):
    """Quality metrics for generated questions"""
    has_low_quality: bool = Field(default=False, description="Whether low-quality questions were detected")
    ambiguous_count: int = Field(default=0, ge=0, description="Number of ambiguous questions")
    duplicate_count: int = Field(default=0, ge=0, description="Number of duplicate questions")
    total_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall quality score")
    notes: Optional[str] = Field(None, description="Additional quality notes")


class RefineRequest(BaseModel):
    """Request to refine project requirements"""
    project_id: str = Field(..., description="Project ID to refine (UUID)")
    max_rounds: int = Field(default=5, ge=1, le=10, description="Maximum refinement rounds")
    request_id: Optional[str] = Field(None, description="Optional idempotency key (UUID). Auto-generated if not provided.")
    answers: Optional[List[Answer]] = Field(None, description="Answers to previous questions")
    
    @field_validator('project_id')
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        """Validate project_id is a valid UUID"""
        try:
            UUID(v)
        except ValueError:
            raise ValueError("project_id must be a valid UUID")
        return v
    
    @field_validator('request_id')
    @classmethod
    def validate_request_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate request_id is a valid UUID if provided"""
        if v is None:
            return v
        try:
            UUID(v)
        except ValueError:
            raise ValueError("request_id must be a valid UUID")
        return v


class RefineResponse(BaseModel):
    """Response from refinement process"""
    status: str = Field(..., description="Project status: REQS_REFINING|REQS_READY|BLOCKED")
    open_questions: Optional[List[Question]] = Field(None, description="Unanswered questions")
    refined_requirements_version: Optional[int] = Field(None, description="New requirements version if refined")
    audit_ref: Dict[str, Any] = Field(..., description="Audit trail reference")
    current_round: int = Field(..., ge=1, description="Current refinement round")
    max_rounds: int = Field(..., ge=1, description="Maximum allowed rounds")
    quality_flags: Optional[QualityFlags] = Field(None, description="Quality metrics for questions")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of allowed values"""
        allowed = ["REQS_REFINING", "REQS_READY", "BLOCKED"]
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class QASessionResponse(BaseModel):
    """Q&A Session details"""
    id: UUID
    project_id: UUID
    request_id: str
    round: int
    questions: List[Question]
    answers: Optional[List[Answer]]
    quality_flags: Optional[QualityFlags]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QASessionListResponse(BaseModel):
    """List of Q&A sessions for a project"""
    project_id: UUID
    sessions: List[QASessionResponse]
    total: int
