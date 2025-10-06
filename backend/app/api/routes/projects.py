from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.models.project import Project, Requirement, RequirementVersion
from app.schemas.project import (
    ProjectCreate, ProjectRead, ProjectUpdate,
    RequirementsBulkUpsert, RequirementRead, RequirementUpsert,
    RequirementVersionRead
)
from app.services.requirement_service import RequirementService
from app.core.logging_config import get_logger

router = APIRouter(prefix="/projects", tags=["projects"])
logger = get_logger(__name__)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new project"""
    logger.info(f"Creating project: {project.name}")
    
    db_project = Project(
        name=project.name,
        created_by=project.created_by
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    logger.info(f"Project created: {db_project.id}")
    return db_project


@router.get("", response_model=List[ProjectRead])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all projects"""
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Get project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    logger.info(f"Project updated: {project_id}")
    return project


@router.post("/{project_id}/requirements", response_model=List[RequirementRead])
def bulk_upsert_requirements(
    project_id: UUID,
    bulk_data: RequirementsBulkUpsert,
    db: Session = Depends(get_db)
):
    """Bulk upsert requirements with version bumping"""
    logger.info(f"Bulk upserting {len(bulk_data.requirements)} requirements for project {project_id}")
    
    requirements = RequirementService.bulk_upsert_requirements(
        db=db,
        project_id=project_id,
        requirements=bulk_data.requirements
    )
    
    logger.info(f"Successfully upserted {len(requirements)} requirements")
    return requirements


@router.get("/{project_id}/requirements", response_model=List[RequirementRead])
def get_project_requirements(
    project_id: UUID,
    version: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get project requirements (optionally at specific version)"""
    requirements = RequirementService.get_requirements_by_version(
        db=db,
        project_id=project_id,
        version=version
    )
    return requirements


@router.put("/requirements/{requirement_id}", response_model=RequirementRead)
def update_requirement_put(
    requirement_id: UUID,
    requirement_data: RequirementUpsert,
    db: Session = Depends(get_db)
):
    """Update requirement (always creates new version)"""
    logger.info(f"Updating requirement: {requirement_id}")
    
    requirement = RequirementService.update_requirement(
        db=db,
        requirement_id=requirement_id,
        update_data=requirement_data
    )
    
    logger.info(f"Requirement updated to version {requirement.version}")
    return requirement


@router.patch("/requirements/{requirement_id}", response_model=RequirementRead)
def update_requirement_patch(
    requirement_id: UUID,
    requirement_data: RequirementUpsert,
    db: Session = Depends(get_db)
):
    """Update requirement (always creates new version)"""
    return update_requirement_put(requirement_id, requirement_data, db)


@router.get("/requirements/{requirement_id}/versions", response_model=List[RequirementVersionRead])
def get_requirement_versions(
    requirement_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all versions of a requirement"""
    versions = RequirementService.get_requirement_versions(
        db=db,
        requirement_id=requirement_id
    )
    
    if not versions:
        # Check if requirement exists
        req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
        if not req:
            raise HTTPException(status_code=404, detail="Requirement not found")
    
    return versions


@router.get("/requirements/{requirement_id}/versions/{version}", response_model=RequirementVersionRead)
def get_requirement_version(
    requirement_id: UUID,
    version: int,
    db: Session = Depends(get_db)
):
    """Get specific version of a requirement"""
    req_version = RequirementService.get_requirement_version(
        db=db,
        requirement_id=requirement_id,
        version=version
    )
    
    if not req_version:
        raise HTTPException(status_code=404, detail="Requirement version not found")
    
    return req_version
