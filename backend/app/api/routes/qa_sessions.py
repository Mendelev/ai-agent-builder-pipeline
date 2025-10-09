"""
QA Sessions API Routes - Requirement Refinement (R3)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid as uuid_lib
import logging

from app.core.database import get_db
from app.models.project import Project
from app.models.qa_session import QASession
from app.schemas.qa_session import (
    RefineRequest,
    RefineResponse,
    QASessionResponse,
    QASessionListResponse
)
from app.tasks.analyst import refine_requirements

logger = logging.getLogger(__name__)

# Router for refinement endpoint (no project_id in path)
router = APIRouter(prefix="/refine", tags=["qa_sessions"])

# Router for Q&A sessions listing (with project_id in path)
projects_router = APIRouter(prefix="/projects", tags=["qa_sessions"])


@router.post(
    "",
    response_model=RefineResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Refine project requirements (R3)",
    description="""
    Initiate asynchronous requirement refinement process for a project.
    
    **Process:**
    1. Analyzes current requirements for ambiguity, testability issues, and missing criteria
    2. Generates clarifying questions using heuristics
    3. If answers provided, refines requirements and increments version
    4. Returns status and open questions (if any)
    
    **Idempotency:** 
    - `request_id` is optional. If not provided, a UUID will be auto-generated.
    - If provided, use same `request_id` to prevent duplicate processing.
    
    **Guard-rails:**
    - Respects `max_rounds` to prevent infinite loops
    - Evaluates question quality and flags low-quality outputs
    
    **Status transitions:**
    - `DRAFT` → `REQS_REFINING` (first round with questions)
    - `REQS_REFINING` → `REQS_READY` (no more questions)
    - `REQS_REFINING` → `BLOCKED` (max_rounds exceeded or error)
    """
)
async def refine_project_requirements(
    request: RefineRequest,
    db: Session = Depends(get_db)
):
    """
    Start requirement refinement for a project.
    Returns immediately with task reference (async execution).
    """
    # Extract project_id from request body
    try:
        project_id = uuid_lib.UUID(request.project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project_id format. Must be a valid UUID."
        )
    
    # Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    # Check if project is in a valid state for refinement
    valid_states = ["DRAFT", "REQS_REFINING", "REQS_READY"]
    if project.status not in valid_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project must be in {valid_states} state. Current: {project.status}"
        )
    
    # Generate request_id if not provided
    if request.request_id is None:
        request.request_id = str(uuid_lib.uuid4())
        logger.info(f"Auto-generated request_id: {request.request_id}")
    
    # Prepare answers for task
    answers_data = None
    if request.answers:
        answers_data = [answer.model_dump() for answer in request.answers]
    
    logger.info(
        f"Enqueuing refinement task for project {project_id}, "
        f"request_id={request.request_id}, max_rounds={request.max_rounds}"
    )
    
    # Enqueue async task
    task = refine_requirements.apply_async(
        kwargs={
            "project_id": str(project_id),
            "max_rounds": request.max_rounds,
            "request_id": request.request_id,
            "answers": answers_data
        },
        task_id=request.request_id  # Use request_id as task_id for idempotency
    )
    
    # Return immediate response (task is running asynchronously)
    # In production, client would poll /tasks/{task_id} for results
    return RefineResponse(
        status="REQS_REFINING",
        open_questions=None,  # Will be available when task completes
        refined_requirements_version=None,
        audit_ref={
            "task_id": task.id,
            "request_id": request.request_id,
            "project_id": str(project_id),
            "enqueued_at": "UTC_NOW",  # Would use actual timestamp
            "state": "PENDING"
        },
        current_round=1,  # Task will determine actual round
        max_rounds=request.max_rounds,
        quality_flags=None
    )


# ============================================================================
# Q&A Sessions Listing Routes (with project_id in path)
# ============================================================================

@projects_router.get(
    "/{project_id}/qa-sessions",
    response_model=QASessionListResponse,
    summary="Get Q&A sessions for a project",
    description="Retrieve all Q&A refinement sessions for a project, ordered by round."
)
async def get_project_qa_sessions(
    project_id: uuid_lib.UUID,
    db: Session = Depends(get_db)
):
    """Get all Q&A sessions for a project"""
    # Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )
    
    # Get all sessions
    sessions = db.query(QASession).filter(
        QASession.project_id == project_id
    ).order_by(QASession.round.asc()).all()
    
    return QASessionListResponse(
        project_id=project_id,
        sessions=[QASessionResponse.model_validate(session) for session in sessions],
        total=len(sessions)
    )


@projects_router.get(
    "/{project_id}/qa-sessions/{session_id}",
    response_model=QASessionResponse,
    summary="Get specific Q&A session",
    description="Retrieve details of a specific Q&A session."
)
async def get_qa_session(
    project_id: uuid_lib.UUID,
    session_id: uuid_lib.UUID,
    db: Session = Depends(get_db)
):
    """Get a specific Q&A session"""
    session = db.query(QASession).filter(
        QASession.id == session_id,
        QASession.project_id == project_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QA Session {session_id} not found for project {project_id}"
        )
    
    return QASessionResponse.model_validate(session)
