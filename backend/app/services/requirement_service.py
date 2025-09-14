# backend/app/services/requirement_service.py
from typing import List, Optional, Dict, Any, Set
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
        iteration_version_map = {}
        
        # Get current iteration versions
        existing_reqs = db.query(Requirement).filter(
            Requirement.project_id == project_id
        ).all()
        
        for req in existing_reqs:
            last_iteration = db.query(RequirementIteration).filter(
                RequirementIteration.requirement_id == req.id
            ).order_by(RequirementIteration.version.desc()).first()
            iteration_version_map[req.key] = (req, last_iteration.version if last_iteration else 0)
        
        for req_data in requirements_data:
            if req_data.key in iteration_version_map:
                # Update existing requirement
                existing, last_version = iteration_version_map[req_data.key]
                
                # Capture changes
                changes = {}
                for field, value in req_data.model_dump(exclude_unset=True).items():
                    old_value = getattr(existing, field)
                    if old_value != value:
                        changes[field] = {"old": old_value, "new": value}
                        setattr(existing, field, value)
                
                if changes:
                    # Create iteration record
                    iteration = RequirementIteration(
                        requirement_id=existing.id,
                        version=last_version + 1,
                        changes=changes,
                        created_by="system"
                    )
                    db.add(iteration)
                
                created_requirements.append(existing)
                logger.info(f"Updated requirement {req_data.key}")
            else:
                # Create new requirement
                new_req = Requirement(
                    project_id=project_id,
                    **req_data.model_dump()
                )
                db.add(new_req)
                db.flush()  # Get the ID
                
                # Create initial iteration
                iteration = RequirementIteration(
                    requirement_id=new_req.id,
                    version=1,
                    changes={"action": "created"},
                    created_by="system"
                )
                db.add(iteration)
                
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
        """Validate that dependencies form a DAG (no cycles) using DFS"""
        # Build adjacency list
        graph: Dict[str, List[str]] = {}
        for req in requirements:
            graph[req.key] = req.dependencies or []
        
        # Check all dependencies exist
        all_keys = set(graph.keys())
        for deps in graph.values():
            for dep in deps:
                if dep not in all_keys:
                    logger.warning(f"Dependency {dep} not found in requirements")
                    return False
        
        # DFS to detect cycles
        WHITE, GRAY, BLACK = 0, 1, 2
        colors: Dict[str, int] = {node: WHITE for node in graph}
        
        def has_cycle(node: str) -> bool:
            if colors[node] == GRAY:
                return True
            if colors[node] == BLACK:
                return False
            
            colors[node] = GRAY
            for neighbor in graph.get(node, []):
                if neighbor in colors and has_cycle(neighbor):
                    return True
            colors[node] = BLACK
            return False
        
        for node in graph:
            if colors[node] == WHITE:
                if has_cycle(node):
                    logger.error(f"Cycle detected starting from {node}")
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
            "total": len(requirements),
            "exported_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def export_markdown(requirements: List[Requirement]) -> str:
        """Export requirements as Markdown"""
        md_lines = ["# Requirements Export\n"]
        md_lines.append(f"**Generated:** {datetime.utcnow().isoformat()}\n")
        md_lines.append(f"**Total Requirements:** {len(requirements)}\n")
        
        # Group by priority
        priority_groups: Dict[str, List[Requirement]] = {}
        for req in requirements:
            if req.priority not in priority_groups:
                priority_groups[req.priority] = []
            priority_groups[req.priority].append(req)
        
        priority_order = ["critical", "high", "medium", "low"]
        
        for priority in priority_order:
            if priority not in priority_groups:
                continue
            
            md_lines.append(f"\n## {priority.capitalize()} Priority\n")
            
            for req in sorted(priority_groups[priority], key=lambda x: x.key):
                md_lines.append(f"\n### [{req.key}] {req.title}\n")
                
                if req.description:
                    md_lines.append(f"**Description:** {req.description}\n")
                
                if req.acceptance_criteria:
                    md_lines.append("\n**Acceptance Criteria:**")
                    for i, criterion in enumerate(req.acceptance_criteria, 1):
                        md_lines.append(f"  {i}. {criterion}")
                    md_lines.append("")
                
                if req.dependencies:
                    md_lines.append(f"**Dependencies:** `{', '.join(req.dependencies)}`\n")
                
                status = "✅ Validated" if req.is_coherent else "⚠️ Needs refinement"
                md_lines.append(f"**Status:** {status}\n")
        
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
            incoherent = [req.key for req in requirements if not req.is_coherent]
            if incoherent:
                raise ValueError(f"Requirements not coherent: {', '.join(incoherent)}. Use force=true to override.")
            
            # Check high/critical have acceptance criteria
            missing_criteria = []
            for req in requirements:
                if req.priority in ['high', 'critical'] and not req.acceptance_criteria:
                    missing_criteria.append(req.key)
            
            if missing_criteria:
                raise ValueError(f"High/critical requirements missing acceptance criteria: {', '.join(missing_criteria)}")
            
            # Validate DAG
            if not RequirementService.validate_dag(requirements):
                raise ValueError("Requirements have circular dependencies")
        
        project.status = ProjectStatus.REQS_READY
        db.commit()
        
        logger.info(f"Project {project_id} marked as REQS_READY")
        return True