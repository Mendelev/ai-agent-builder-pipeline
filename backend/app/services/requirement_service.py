from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from app.models.project import Project, Requirement, RequirementVersion
from app.schemas.project import RequirementUpsert, RequirementData


class RequirementService:
    @staticmethod
    def bulk_upsert_requirements(
        db: Session, 
        project_id: UUID, 
        requirements: List[RequirementUpsert]
    ) -> List[Requirement]:
        """Bulk upsert requirements with version bumping"""
        # Validate project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        result_requirements = []
        
        for req_data in requirements:
            # Check if requirement exists
            existing_req = db.query(Requirement).filter(
                Requirement.project_id == project_id,
                Requirement.code == req_data.code
            ).first()

            requirement_dict = req_data.dict()
            
            if existing_req:
                # Archive current version
                version_record = RequirementVersion(
                    requirement_id=existing_req.id,
                    version=existing_req.version,
                    data=existing_req.data
                )
                db.add(version_record)
                
                # Update requirement with version bump
                existing_req.version += 1
                existing_req.data = requirement_dict
                db.add(existing_req)
                result_requirements.append(existing_req)
            else:
                # Create new requirement
                new_req = Requirement(
                    project_id=project_id,
                    code=req_data.code,
                    version=1,
                    data=requirement_dict
                )
                db.add(new_req)
                result_requirements.append(new_req)

        try:
            db.commit()
            for req in result_requirements:
                db.refresh(req)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=422, detail=f"Integrity error: {str(e)}")

        return result_requirements

    @staticmethod
    def update_requirement(
        db: Session,
        requirement_id: UUID,
        update_data: RequirementUpsert
    ) -> Requirement:
        """Update requirement and create version history"""
        requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
        if not requirement:
            raise HTTPException(status_code=404, detail="Requirement not found")

        # Archive current version
        version_record = RequirementVersion(
            requirement_id=requirement.id,
            version=requirement.version,
            data=requirement.data
        )
        db.add(version_record)

        # Update with version bump
        requirement.version += 1
        requirement.data = update_data.dict()
        requirement.code = update_data.code

        try:
            db.commit()
            db.refresh(requirement)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=422, detail=f"Integrity error: {str(e)}")

        return requirement

    @staticmethod
    def get_requirements_by_version(
        db: Session,
        project_id: UUID,
        version: Optional[int] = None
    ) -> List[Requirement]:
        """Get requirements at specific version or latest"""
        query = db.query(Requirement).filter(Requirement.project_id == project_id)
        
        if version:
            query = query.filter(Requirement.version == version)
        
        return query.all()

    @staticmethod
    def get_requirement_versions(
        db: Session,
        requirement_id: UUID
    ) -> List[RequirementVersion]:
        """Get all versions of a requirement"""
        return db.query(RequirementVersion).filter(
            RequirementVersion.requirement_id == requirement_id
        ).order_by(RequirementVersion.version.desc()).all()

    @staticmethod
    def get_requirement_version(
        db: Session,
        requirement_id: UUID,
        version: int
    ) -> Optional[RequirementVersion]:
        """Get specific version of a requirement"""
        return db.query(RequirementVersion).filter(
            RequirementVersion.requirement_id == requirement_id,
            RequirementVersion.version == version
        ).first()
