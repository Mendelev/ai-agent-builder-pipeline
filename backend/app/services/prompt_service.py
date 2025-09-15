# backend/app/services/prompt_service.py
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import Project, Plan, PlanPhase, Requirement, PromptBundle, PromptItem
from app.schemas.prompt import PromptGenerateRequest
from app.utils.security import sanitize_content, generate_placeholder_config
from app.core.observability import get_logger
from datetime import datetime, UTC
import json
import zipfile
import io

logger = get_logger(__name__)

class PromptService:
    @staticmethod
    def generate_prompts(
        db: Session,
        project_id: UUID,
        request: PromptGenerateRequest
    ) -> PromptBundle:
        """Generate prompts for a project plan"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Get plan
        if request.plan_id:
            plan = db.query(Plan).filter(
                Plan.id == request.plan_id,
                Plan.project_id == project_id
            ).first()
        else:
            plan = db.query(Plan).filter(
                Plan.project_id == project_id
            ).order_by(desc(Plan.version)).first()
        
        if not plan:
            raise ValueError("No plan found for project")
        
        # Get requirements
        requirements = db.query(Requirement).filter(
            Requirement.project_id == project_id
        ).all()
        
        # Check for existing bundle version
        last_bundle = db.query(PromptBundle).filter(
            PromptBundle.project_id == project_id
        ).order_by(desc(PromptBundle.version)).first()
        
        new_version = (last_bundle.version + 1) if last_bundle else 1
        
        # Generate context
        context_md = PromptService._generate_context(
            project, plan, requirements, request.include_code
        )
        
        # Sanitize context
        context_md = sanitize_content(context_md)
        
        # Create bundle
        bundle = PromptBundle(
            project_id=project_id,
            plan_id=plan.id,
            version=new_version,
            include_code=request.include_code,
            context_md=context_md,
            metadata={
                "project_name": project.name,
                "plan_version": plan.version,
                "requirements_count": len(requirements),
                "generated_at": datetime.now(UTC).isoformat()
            }
        )
        
        db.add(bundle)
        db.flush()
        
        # Generate prompts for each phase
        prompt_count = 0
        for sequence, phase in enumerate(plan.phases, 1):
            prompt_content = PromptService._generate_phase_prompt(
                phase, requirements, project, request.include_code
            )
            
            # Sanitize prompt
            prompt_content = sanitize_content(prompt_content)
            
            prompt_item = PromptItem(
                bundle_id=bundle.id,
                phase_id=phase.phase_id,
                sequence=sequence,
                title=f"Phase {phase.phase_id}: {phase.title}",
                content_md=prompt_content,
                metadata={
                    "requirements": phase.requirements_covered,
                    "estimated_tokens": len(prompt_content.split()) * 1.3,  # Rough estimate
                    "dependencies": phase.dependencies
                }
            )
            db.add(prompt_item)
            prompt_count += 1
        
        bundle.total_prompts = prompt_count
        
        db.commit()
        db.refresh(bundle)
        
        logger.info(f"Generated prompt bundle v{new_version} for project {project_id}")
        return bundle
    
    @staticmethod
    def _generate_context(
        project: Project,
        plan: Plan,
        requirements: List[Requirement],
        include_code: bool
    ) -> str:
        """Generate general context markdown"""
        context = []
        
        # Header
        context.append(f"# Project Context: {project.name}\n")
        context.append(f"**Generated**: {datetime.now(UTC).isoformat()}\n")
        context.append(f"**Plan Version**: {plan.version}\n")
        
        # Domain & Objectives
        context.append("## Domain & Objectives\n")
        if project.description:
            context.append(f"{project.description}\n")
        if project.context:
            context.append(f"\n### Additional Context\n{project.context}\n")
        
        # NFRs (Non-Functional Requirements)
        context.append("\n## Non-Functional Requirements (NFRs)\n")
        nfrs = []
        if plan.constraints:
            if "nfrs" in plan.constraints:
                nfrs.extend(plan.constraints["nfrs"])
            if "deadline_days" in plan.constraints:
                nfrs.append(f"Project deadline: {plan.constraints['deadline_days']} days")
            if "team_size" in plan.constraints:
                nfrs.append(f"Team size: {plan.constraints['team_size']} members")
        
        if nfrs:
            for nfr in nfrs:
                context.append(f"- {nfr}")
            context.append("")
        else:
            context.append("- Performance: Response time < 200ms for 95% of requests")
            context.append("- Scalability: Support 10,000 concurrent users")
            context.append("- Security: OWASP Top 10 compliance")
            context.append("- Availability: 99.9% uptime SLA\n")
        
        # Conventions
        context.append("\n## Conventions & Standards\n")
        context.append("### Naming Conventions")
        context.append("- Requirements: `REQ-###` (e.g., REQ-001)")
        context.append("- Phases: `PH-##` (e.g., PH-01)")
        context.append("- APIs: RESTful, kebab-case endpoints")
        context.append("- Database: snake_case for tables and columns")
        context.append("- Code: Follow language-specific conventions (PEP8 for Python, ESLint for JS)\n")
        
        if include_code:
            context.append("\n### Code Generation Guidelines")
            context.append("- Generate production-ready, well-documented code")
            context.append("- Include comprehensive error handling")
            context.append("- Add unit tests with >80% coverage")
            context.append("- Follow SOLID principles and design patterns")
            context.append("- Include logging and monitoring hooks")
            context.append("- Use dependency injection where appropriate\n")
        
        # Technical Stack (if available)
        context.append("\n## Technical Stack\n")
        tech_stack = PromptService._detect_tech_stack(requirements)
        for tech in tech_stack:
            context.append(f"- {tech}")
        context.append("")
        
        # Requirements Summary
        context.append("\n## Requirements Overview\n")
        context.append(f"**Total Requirements**: {len(requirements)}\n")
        
        # Group by priority
        priority_counts = {}
        for req in requirements:
            priority_counts[req.priority] = priority_counts.get(req.priority, 0) + 1
        
        context.append("### Priority Distribution")
        for priority in ["critical", "high", "medium", "low"]:
            if priority in priority_counts:
                context.append(f"- {priority.capitalize()}: {priority_counts[priority]} requirements")
        context.append("")
        
        # Key Requirements
        context.append("### Key Requirements")
        critical_reqs = [r for r in requirements if r.priority == "critical"][:5]
        high_reqs = [r for r in requirements if r.priority == "high"][:5]
        
        if critical_reqs:
            context.append("\n**Critical:**")
            for req in critical_reqs:
                context.append(f"- [{req.key}] {req.title}")
        
        if high_reqs:
            context.append("\n**High Priority:**")
            for req in high_reqs:
                context.append(f"- [{req.key}] {req.title}")
        context.append("")
        
        # Plan Summary
        context.append("\n## Execution Plan Summary\n")
        context.append(f"**Total Phases**: {len(plan.phases)}")
        context.append(f"**Estimated Duration**: {plan.total_duration_days} days")
        context.append(f"**Coverage**: {plan.coverage_percentage:.1f}%")
        context.append(f"**Risk Score**: {plan.risk_score:.2f}\n")
        
        # Configuration Placeholders
        context.append("\n## Configuration Placeholders\n")
        context.append("```yaml")
        placeholders = generate_placeholder_config()
        for key, value in placeholders.items():
            context.append(f"{key}: {value}")
        context.append("```\n")
        
        return "\n".join(context)
    
    @staticmethod
    def _generate_phase_prompt(
        phase: PlanPhase,
        requirements: List[Requirement],
        project: Project,
        include_code: bool
    ) -> str:
        """Generate prompt for a specific phase"""
        prompt = []
        
        # Header
        prompt.append(f"# {phase.phase_id}: {phase.title}\n")
        
        # Objective
        prompt.append("## Objective\n")
        prompt.append(f"{phase.objective}\n")
        
        # Inputs
        prompt.append("## Inputs\n")
        
        # Requirements for this phase
        requirements_covered = phase.requirements_covered or []
        phase_reqs = [r for r in requirements if r.key in requirements_covered]
        if phase_reqs:
            prompt.append("### Requirements to Implement")
            for req in phase_reqs:
                prompt.append(f"\n**[{req.key}] {req.title}**")
                if req.description:
                    prompt.append(f"- Description: {req.description}")
                if req.acceptance_criteria:
                    prompt.append("- Acceptance Criteria:")
                    for ac in req.acceptance_criteria:
                        prompt.append(f"  - {ac}")
                if req.dependencies:
                    prompt.append(f"- Dependencies: {', '.join(req.dependencies)}")
        prompt.append("")
        
        # Dependencies from other phases
        if phase.dependencies:
            prompt.append("### Phase Dependencies")
            for dep in phase.dependencies:
                prompt.append(f"- {dep} must be completed")
            prompt.append("")
        
        # Resources
        if phase.resources_required:
            prompt.append("### Resources Required")
            for role, count in phase.resources_required.items():
                prompt.append(f"- {role.capitalize()}: {count}")
            prompt.append("")
        
        # Tasks
        prompt.append("## Tasks\n")
        for i, activity in enumerate(phase.activities, 1):
            prompt.append(f"{i}. {activity}")
        prompt.append("")
        
        # Deliverables
        prompt.append("## Expected Deliverables\n")
        for deliverable in phase.deliverables[:10]:  # Limit to 10
            prompt.append(f"- {deliverable}")
        prompt.append("")
        
        # Output Format
        prompt.append("## Output Format\n")
        if include_code:
            prompt.append("### Code Structure")
            prompt.append("```")
            prompt.append("project/")
            prompt.append("├── src/")
            prompt.append("│   ├── features/")
            prompt.append("│   ├── services/")
            prompt.append("│   └── tests/")
            prompt.append("├── docs/")
            prompt.append("└── README.md")
            prompt.append("```\n")
            
            prompt.append("### Code Requirements")
            prompt.append("- Include comprehensive inline documentation")
            prompt.append("- Add type hints/annotations")
            prompt.append("- Follow project coding standards")
            prompt.append("- Include unit and integration tests")
            prompt.append("- Add error handling and logging\n")
        else:
            prompt.append("### Documentation")
            prompt.append("- Technical design document")
            prompt.append("- API specifications (OpenAPI/Swagger)")
            prompt.append("- Database schema and ERD")
            prompt.append("- Sequence diagrams for key flows")
            prompt.append("- Test cases and test plans\n")
        
        # Definition of Done
        prompt.append("## Definition of Done\n")
        for dod_item in phase.definition_of_done:
            prompt.append(f"- [ ] {dod_item}")
        prompt.append("")
        
        # Risks & Mitigations
        if phase.risks:
            prompt.append("## Risks & Mitigations\n")
            prompt.append(f"**Risk Level**: {phase.risk_level.upper()}\n")
            for risk in phase.risks:
                prompt.append(f"- ⚠️ {risk}")
            prompt.append("")
        
        # Common Errors to Avoid
        prompt.append("## Common Errors to Avoid\n")
        errors = PromptService._get_common_errors(phase, phase_reqs)
        for error in errors:
            prompt.append(f"- {error}")
        prompt.append("")
        
        # Validation Checklist
        prompt.append("## Validation Checklist\n")
        prompt.append("- [ ] All requirements covered and tested")
        prompt.append("- [ ] Code review completed")
        prompt.append("- [ ] Documentation updated")
        prompt.append("- [ ] No critical security vulnerabilities")
        prompt.append("- [ ] Performance benchmarks met")
        prompt.append("- [ ] Integration tests passing\n")
        
        # Notes
        prompt.append("## Notes\n")
        prompt.append(f"- Estimated Duration: {phase.estimated_days} days")
        prompt.append(f"- Requirements Coverage: {len(phase.requirements_covered)} requirements")
        # Note: PlanPhase doesn't have extra_metadata field - could be added later if needed
        
        return "\n".join(prompt)
    
    @staticmethod
    def _detect_tech_stack(requirements: List[Requirement]) -> List[str]:
        """Detect technology stack from requirements"""
        tech_stack = []
        
        # Check requirement content for technology mentions
        all_text = " ".join([
            f"{r.title} {r.description or ''}" 
            for r in requirements
        ]).lower()
        
        # Common technologies
        tech_patterns = {
            "Backend: Python/FastAPI": ["fastapi", "python", "pydantic"],
            "Backend: Node.js/Express": ["node", "express", "nodejs"],
            "Frontend: React": ["react", "jsx", "component"],
            "Frontend: Vue.js": ["vue", "vuex", "nuxt"],
            "Database: PostgreSQL": ["postgres", "postgresql", "pg"],
            "Database: MongoDB": ["mongodb", "mongo", "nosql"],
            "Cache: Redis": ["redis", "cache", "session"],
            "Message Queue: RabbitMQ": ["rabbitmq", "amqp", "queue"],
            "Container: Docker": ["docker", "container", "kubernetes"],
        }
        
        for tech, patterns in tech_patterns.items():
            if any(pattern in all_text for pattern in patterns):
                tech_stack.append(tech)
        
        if not tech_stack:
            # Default stack
            tech_stack = [
                "Backend: Python/FastAPI",
                "Database: PostgreSQL",
                "Cache: Redis",
                "Container: Docker"
            ]
        
        return tech_stack
    
    @staticmethod
    def _get_common_errors(phase: PlanPhase, requirements: List[Requirement]) -> List[str]:
        """Get common errors for a phase"""
        errors = []
        
        # General errors
        errors.append("Not validating input data properly")
        errors.append("Missing error handling for edge cases")
        errors.append("Ignoring performance implications")
        
        # Phase-specific errors
        if "security" in phase.title.lower() or any("security" in r.title.lower() for r in requirements):
            errors.append("Storing passwords in plain text")
            errors.append("Not using parameterized queries (SQL injection risk)")
            errors.append("Missing authentication/authorization checks")
        
        if "api" in phase.title.lower():
            errors.append("Not following RESTful conventions")
            errors.append("Missing API versioning")
            errors.append("Inadequate rate limiting")
        
        if "database" in phase.title.lower():
            errors.append("Missing database indexes")
            errors.append("Not handling transaction rollbacks")
            errors.append("N+1 query problems")
        
        if phase.risk_level in ["high", "critical"]:
            errors.append("Insufficient testing coverage")
            errors.append("Not planning for failure scenarios")
            errors.append("Missing monitoring and alerting")
        
        return errors[:7]  # Limit to 7 errors
    
    @staticmethod
    def get_latest_bundle(db: Session, project_id: UUID) -> Optional[PromptBundle]:
        """Get the latest prompt bundle for a project"""
        return db.query(PromptBundle).filter(
            PromptBundle.project_id == project_id
        ).order_by(desc(PromptBundle.version)).first()
    
    @staticmethod
    def create_bundle_zip(db: Session, bundle_id: UUID) -> bytes:
        """Create a ZIP file containing the prompt bundle"""
        bundle = db.query(PromptBundle).filter(
            PromptBundle.id == bundle_id
        ).first()
        
        if not bundle:
            raise ValueError(f"Bundle {bundle_id} not found")
        
        # Create in-memory ZIP
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add context file
            zip_file.writestr(
                "context.md",
                bundle.context_md
            )
            
            # Add individual prompts
            for prompt in bundle.prompts:
                filename = f"prompts/{prompt.phase_id}_{prompt.title.replace(':', '').replace(' ', '_')}.md"
                zip_file.writestr(filename, prompt.content_md)
            
            # Add metadata JSON
            metadata = {
                "bundle_id": str(bundle.id),
                "project_id": str(bundle.project_id),
                "plan_id": str(bundle.plan_id),
                "version": bundle.version,
                "total_prompts": bundle.total_prompts,
                "created_at": bundle.created_at.isoformat(),
                "prompts": [
                    {
                        "phase_id": p.phase_id,
                        "title": p.title,
                        "sequence": p.sequence,
                        "metadata": p.extra_metadata
                    }
                    for p in bundle.prompts
                ]
            }
            
            zip_file.writestr(
                "metadata.json",
                json.dumps(metadata, indent=2)
            )
            
            # Add README
            readme = f"""# Prompt Bundle

Generated: {bundle.created_at.isoformat()}
Version: {bundle.version}
Total Prompts: {bundle.total_prompts}

## Contents

- `context.md`: General project context and conventions
- `prompts/`: Individual phase prompts
- `metadata.json`: Bundle metadata
- `README.md`: This file

## Usage

1. Review the context.md file for project overview
2. Execute prompts in sequence (by phase number)
3. Validate outputs against Definition of Done in each prompt
"""
            zip_file.writestr("README.md", readme)
        
        zip_buffer.seek(0)
        return zip_buffer.read()