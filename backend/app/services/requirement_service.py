# backend/app/services/requirement_service.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import Project, Requirement, RequirementIteration, RequirementQuestion, ProjectStatus
from app.schemas.requirement import RequirementCreate, RequirementUpdate
from app.core.observability import get_logger
import json
from datetime import datetime

logger = get_logger(__name__)

class RequirementService:
    @staticmethod
    def create_bulk(db: Session, project_id: UUID, requirements_data: List[RequirementCreate]) -> List[Requirement]:
        """Bulk create or update requirements"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        created_requirements = []
        for req_data in requirements_data:
            existing = db.query(Requirement).filter(
                Requirement.project_id == project_id,
                Requirement.key == req_data.key
            ).first()
            
            if existing:
                # Update existing requirement
                for field, value in req_data.model_dump(exclude_unset=True).items():
                    setattr(existing, field, value)
                created_requirements.append(existing)
                logger.info(f"Updated requirement {req_data.key}")
            else:
                # Create new requirement
                new_req = Requirement(
                    project_id=project_id,
                    **req_data.model_dump()
                )
                db.add(new_req)
                created_requirements.append(new_req)
                logger.info(f"Created requirement {req_data.key}")
        
        try:
            db.commit()
            for req in created_requirements:
                db.refresh(req)
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Failed to save requirements: {e}")
            raise ValueError("Failed to save requirements: duplicate keys or invalid data")
        
        return created_requirements
    
    @staticmethod
    def list_requirements(db: Session, project_id: UUID) -> List[Requirement]:
        """List all requirements for a project"""
        return db.query(Requirement).filter(Requirement.project_id == project_id).all()
    
    @staticmethod
    def validate_dag(requirements: List[Requirement]) -> bool:
        """Validate that dependencies form a DAG (no cycles)"""
        # Build adjacency list
        graph = {}
        for req in requirements:
            graph[req.key] = req.dependencies or []
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return False
        
        return True
    
    @staticmethod
    def export_json(requirements: List[Requirement]) -> Dict[str, Any]:
        """Export requirements as JSON"""
        return {
            "requirements": [
                {
                    "key": req.key,
                    "title": req.title,
                    "description": req.description,
                    "priority": req.priority,
                    "acceptance_criteria": req.acceptance_criteria,
                    "dependencies": req.dependencies,
                    "metadata": req.metadata,
                    "is_coherent": req.is_coherent,
                    "created_at": req.created_at.isoformat(),
                    "updated_at": req.updated_at.isoformat()
                }
                for req in requirements
            ],
            "exported_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def export_markdown(requirements: List[Requirement]) -> str:
        """Export requirements as Markdown"""
        md_lines = ["# Requirements\n"]
        
        # Group by priority
        priority_groups = {}
        for req in requirements:
            if req.priority not in priority_groups:
                priority_groups[req.priority] = []
            priority_groups[req.priority].append(req)
        
        priority_order = ["critical", "high", "medium", "low"]
        
        for priority in priority_order:
            if priority not in priority_groups:
                continue
            
            md_lines.append(f"\n## {priority.capitalize()} Priority\n")
            
            for req in priority_groups[priority]:
                md_lines.append(f"\n### {req.key}: {req.title}\n")
                
                if req.description:
                    md_lines.append(f"{req.description}\n")
                
                if req.acceptance_criteria:
                    md_lines.append("\n**Acceptance Criteria:**")
                    for criterion in req.acceptance_criteria:
                        md_lines.append(f"- {criterion}")
                
                if req.dependencies:
                    md_lines.append(f"\n**Dependencies:** {', '.join(req.dependencies)}")
                
                if req.is_coherent:
                    md_lines.append("\n✅ **Validated**")
                else:
                    md_lines.append("\n⚠️ **Needs refinement**")
        
        return "\n".join(md_lines)
    
    @staticmethod
    def finalize_requirements(db: Session, project_id: UUID, force: bool = False) -> bool:
        """Mark project as REQS_READY if all requirements are coherent"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        requirements = db.query(Requirement).filter(Requirement.project_id == project_id).all()
        
        if not requirements:
            raise ValueError("No requirements found for project")
        
        if not force:
            # Check if all requirements are coherent
            if not all(req.is_coherent for req in requirements):
                raise ValueError("Not all requirements are coherent. Use force=true to override.")
            
            # Validate DAG
            if not RequirementService.validate_dag(requirements):
                raise ValueError("Requirements have circular dependencies")
        
        project.status = ProjectStatus.REQS_READY
        db.commit()
        
        logger.info(f"Project {project_id} marked as REQS_READY")
        return True