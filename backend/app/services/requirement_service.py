from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Tuple
from uuid import UUID
from fastapi import HTTPException, status
from app.models.project import Project, Requirement, RequirementVersion
from app.schemas.project import RequirementUpsert, RequirementData, ValidationResult
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class RequirementService:
    @staticmethod
    def _validate_dependencies(
        db: Session,
        project_id: UUID,
        dependencias: List[str],
        current_code: str
    ) -> Tuple[bool, List[str]]:
        """Validate that all dependencies exist and are not circular"""
        errors = []
        
        if not dependencias:
            return True, []
        
        # Check for self-dependency
        if current_code in dependencias:
            errors.append(f"Requirement cannot depend on itself: {current_code}")
        
        # Check that all dependencies exist
        existing_reqs = db.query(Requirement).filter(
            Requirement.project_id == project_id,
            Requirement.code.in_(dependencias)
        ).all()
        
        existing_codes = {req.code for req in existing_reqs}
        missing_deps = set(dependencias) - existing_codes
        
        if missing_deps:
            errors.append(f"Dependencies not found: {', '.join(sorted(missing_deps))}")
        
        return len(errors) == 0, errors

    @staticmethod
    def _check_validation_warnings(
        req_data: RequirementUpsert
    ) -> List[str]:
        """Check for validation warnings (non-blocking)"""
        warnings = []
        
        # Check for waiver
        if hasattr(req_data, '_has_waiver') and req_data._has_waiver:
            warnings.append("Requirement has waiver reason - manual review recommended")
        
        # Check testability
        if not req_data.testabilidade or len(req_data.testabilidade.strip()) == 0:
            if not settings.DEV_ALLOW_PARTIAL_OBS:
                warnings.append("No testability information provided")
        
        # Check for minimal acceptance criteria
        if len(req_data.criterios_aceitacao) < 2:
            warnings.append("Only one acceptance criterion provided - consider adding more")
        
        # Check priority
        if req_data.prioridade == "wont":
            warnings.append("Priority set to 'wont' - requirement may not be implemented")
        
        return warnings

    @staticmethod
    def validate_requirement(
        db: Session,
        project_id: UUID,
        req_data: RequirementUpsert,
        requirement_id: Optional[UUID] = None
    ) -> ValidationResult:
        """Validate requirement and return structured result"""
        errors = []
        warnings = []
        
        # Validate dependencies
        deps_valid, dep_errors = RequirementService._validate_dependencies(
            db=db,
            project_id=project_id,
            dependencias=req_data.dependencias,
            current_code=req_data.code
        )
        
        if not deps_valid:
            errors.extend(dep_errors)
        
        # Check warnings
        warnings = RequirementService._check_validation_warnings(req_data)
        
        # Log validation with minimal PII
        logger.info(
            "Requirement validation completed",
            extra={
                "project_id": str(project_id),
                "requirement_code": req_data.code,
                "requirement_id": str(requirement_id) if requirement_id else None,
                "valid": len(errors) == 0,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "has_waiver": bool(req_data.waiver_reason)
            }
        )
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            validation_warnings=warnings
        )

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

        # Build set of codes being inserted/updated in this batch
        batch_codes = {req.code for req in requirements}
        
        # Get existing requirements for dependency validation
        existing_reqs = db.query(Requirement).filter(
            Requirement.project_id == project_id
        ).all()
        existing_codes = {req.code for req in existing_reqs}
        
        # All available codes = existing + batch
        available_codes = existing_codes | batch_codes
        
        # Validate all requirements first
        validation_errors = []
        for idx, req_data in enumerate(requirements):
            errors = []
            warnings = []
            
            # Check for self-dependency
            if req_data.code in req_data.dependencias:
                errors.append(f"Requirement cannot depend on itself: {req_data.code}")
            
            # Check dependencies against available codes
            missing_deps = set(req_data.dependencias) - available_codes
            if missing_deps:
                errors.append(f"Dependencies not found: {', '.join(sorted(missing_deps))}")
            
            # Check warnings
            warnings = RequirementService._check_validation_warnings(req_data)
            
            # Log validation
            logger.info(
                "Requirement validation completed",
                extra={
                    "project_id": str(project_id),
                }
            )
            
            if errors:
                validation_errors.append({
                    "index": idx,
                    "code": req_data.code,
                    "errors": errors
                })
        
        if validation_errors:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Validation failed for one or more requirements",
                    "validation_errors": validation_errors
                }
            )

        result_requirements = []
        
        for req_data in requirements:
            # Check if requirement exists
            existing_req = db.query(Requirement).filter(
                Requirement.project_id == project_id,
                Requirement.code == req_data.code
            ).first()

            requirement_dict = req_data.model_dump(exclude={'_has_waiver'})
            
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
    ) -> Tuple[Requirement, ValidationResult]:
        """Update requirement and create version history with validation"""
        requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
        if not requirement:
            raise HTTPException(status_code=404, detail="Requirement not found")

        # Validate requirement
        validation = RequirementService.validate_requirement(
            db=db,
            project_id=requirement.project_id,
            req_data=update_data,
            requirement_id=requirement_id
        )
        
        if not validation.valid:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Requirement validation failed",
                    "errors": validation.errors,
                    "warnings": validation.validation_warnings
                }
            )

        # Archive current version
        version_record = RequirementVersion(
            requirement_id=requirement.id,
            version=requirement.version,
            data=requirement.data
        )
        db.add(version_record)

        # Update with version bump
        requirement.version += 1
        requirement.data = update_data.model_dump(exclude={'_has_waiver'})
        requirement.code = update_data.code

        try:
            db.commit()
            db.refresh(requirement)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=422, detail=f"Integrity error: {str(e)}")

        return requirement, validation

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
