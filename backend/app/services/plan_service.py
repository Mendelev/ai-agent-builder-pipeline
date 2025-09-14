# backend/app/services/plan_service.py
from typing import List, Optional, Dict, Any, Set, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import Project, Requirement, Plan, PlanPhase, PlanStatus
from app.schemas.plan import PlanGenerateRequest, PlanConstraints
from app.core.observability import get_logger
from collections import defaultdict, deque
import math

logger = get_logger(__name__)

class PlanService:
    @staticmethod
    def generate_plan(
        db: Session, 
        project_id: UUID, 
        options: PlanGenerateRequest
    ) -> Plan:
        """Generate execution plan from requirements"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        requirements = db.query(Requirement).filter(
            Requirement.project_id == project_id
        ).all()
        
        if not requirements:
            raise ValueError("No requirements found for project")
        
        # Check previous versions
        last_plan = db.query(Plan).filter(
            Plan.project_id == project_id
        ).order_by(desc(Plan.version)).first()
        
        new_version = (last_plan.version + 1) if last_plan else 1
        
        # Create new plan
        plan = Plan(
            project_id=project_id,
            version=new_version,
            status=PlanStatus.DRAFT,
            source=options.source,
            use_code=options.use_code,
            include_checklist=options.include_checklist,
            constraints=options.constraints.model_dump() if options.constraints else {}
        )
        
        # Generate phases
        phases = PlanService._generate_phases(
            requirements, 
            options,
            project.context
        )
        
        # Calculate metrics
        total_duration = sum(p["estimated_days"] for p in phases)
        covered_reqs = set()
        for phase in phases:
            covered_reqs.update(phase["requirements_covered"])
        
        coverage = (len(covered_reqs) / len(requirements)) * 100 if requirements else 0
        
        # Calculate risk score (weighted average)
        risk_weights = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
        total_risk = sum(
            risk_weights.get(p["risk_level"], 0.5) * p["estimated_days"] 
            for p in phases
        )
        avg_risk = (total_risk / total_duration) if total_duration > 0 else 0
        
        plan.total_duration_days = total_duration
        plan.coverage_percentage = coverage
        plan.risk_score = avg_risk
        
        db.add(plan)
        db.flush()
        
        # Create phase records
        for seq, phase_data in enumerate(phases, 1):
            phase = PlanPhase(
                plan_id=plan.id,
                phase_id=phase_data["phase_id"],
                sequence=seq,
                title=phase_data["title"],
                objective=phase_data["objective"],
                deliverables=phase_data["deliverables"],
                activities=phase_data["activities"],
                dependencies=phase_data["dependencies"],
                estimated_days=phase_data["estimated_days"],
                risk_level=phase_data["risk_level"],
                risks=phase_data["risks"],
                requirements_covered=phase_data["requirements_covered"],
                definition_of_done=phase_data["definition_of_done"],
                resources_required=phase_data["resources_required"]
            )
            db.add(phase)
        
        db.commit()
        db.refresh(plan)
        
        logger.info(f"Generated plan v{new_version} for project {project_id}")
        return plan
    
    @staticmethod
    def _generate_phases(
        requirements: List[Requirement],
        options: PlanGenerateRequest,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate phases using heuristic algorithm"""
        phases = []
        
        # Group requirements by priority and dependencies
        req_map = {req.key: req for req in requirements}
        
        # Build dependency graph
        graph = PlanService._build_dependency_graph(requirements)
        
        # Topological sort to determine execution order
        execution_order = PlanService._topological_sort(graph)
        
        # Check for high priority requirements
        high_priority_reqs = [
            req for req in requirements 
            if req.priority in ["high", "critical"]
        ]
        
        # Phase 0: Remediation phase if needed
        uncovered_high = []
        for req in high_priority_reqs:
            if req.key not in execution_order:
                uncovered_high.append(req.key)
        
        if uncovered_high:
            phases.append({
                "phase_id": "PH-00",
                "title": "Critical Requirements Remediation",
                "objective": "Address high-priority requirements with dependency issues",
                "deliverables": ["Resolved dependency conflicts", "Risk mitigation plan"],
                "activities": ["Analyze blocked requirements", "Create workarounds"],
                "dependencies": [],
                "estimated_days": 5.0,
                "risk_level": "high",
                "risks": ["Dependency conflicts may delay project"],
                "requirements_covered": uncovered_high,
                "definition_of_done": ["All high-priority requirements addressable"],
                "resources_required": {"developers": 2, "architects": 1}
            })
        
        # Group requirements into logical phases
        phase_groups = PlanService._group_into_phases(
            execution_order, 
            req_map,
            options.constraints
        )
        
        # Generate phase details
        for i, group in enumerate(phase_groups, 1):
            if not group:
                continue
            
            # Calculate phase metrics
            complexity = PlanService._calculate_complexity(group, req_map)
            risk_level = PlanService._assess_risk(group, req_map)
            duration = PlanService._estimate_duration(group, req_map, complexity)
            
            # Determine dependencies
            phase_deps = []
            for req_key in group:
                req = req_map[req_key]
                for dep in req.dependencies or []:
                    # Find which phase contains this dependency
                    for j, prev_group in enumerate(phase_groups[:i-1], 1):
                        if dep in prev_group:
                            phase_dep = f"PH-{j:02d}"
                            if phase_dep not in phase_deps:
                                phase_deps.append(phase_dep)
            
            # Generate phase
            phase = {
                "phase_id": f"PH-{i:02d}",
                "title": PlanService._generate_phase_title(group, req_map),
                "objective": PlanService._generate_phase_objective(group, req_map),
                "deliverables": PlanService._generate_deliverables(group, req_map),
                "activities": PlanService._generate_activities(group, req_map),
                "dependencies": phase_deps,
                "estimated_days": duration,
                "risk_level": risk_level,
                "risks": PlanService._identify_risks(group, req_map),
                "requirements_covered": group,
                "definition_of_done": PlanService._generate_dod(group, req_map),
                "resources_required": PlanService._estimate_resources(group, req_map, complexity)
            }
            phases.append(phase)
        
        # Add checklist phases if requested
        if options.include_checklist:
            phases.extend(PlanService._generate_checklist_phases(len(phases)))
        
        return phases
    
    @staticmethod
    def _build_dependency_graph(requirements: List[Requirement]) -> Dict[str, List[str]]:
        """Build adjacency list from requirements"""
        graph = {}
        for req in requirements:
            graph[req.key] = req.dependencies or []
        return graph
    
    @staticmethod
    def _topological_sort(graph: Dict[str, List[str]]) -> List[str]:
        """Kahn's algorithm for topological sorting"""
        # Calculate in-degrees
        in_degree = defaultdict(int)
        all_nodes = set(graph.keys())
        
        for node in graph:
            for neighbor in graph[node]:
                if neighbor in all_nodes:
                    in_degree[neighbor] += 1
        
        # Find nodes with no dependencies
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in all_nodes:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(all_nodes):
            logger.warning(f"Cycle detected! Only {len(result)}/{len(all_nodes)} nodes sorted")
        
        return result
    
    @staticmethod
    def _group_into_phases(
        execution_order: List[str],
        req_map: Dict[str, Requirement],
        constraints: Optional[Dict[str, Any]]
    ) -> List[List[str]]:
        """Group requirements into logical phases"""
        if not execution_order:
            return []
        
        max_phases = 10
        if constraints and "max_parallel_phases" in constraints:
            max_phases = min(constraints["max_parallel_phases"], 10)
        
        # Simple grouping by levels in dependency graph
        phases = []
        current_phase = []
        phase_complexity = 0
        max_complexity_per_phase = 10
        
        for req_key in execution_order:
            req = req_map[req_key]
            
            # Estimate requirement complexity
            req_complexity = 1
            if req.priority == "critical":
                req_complexity = 4
            elif req.priority == "high":
                req_complexity = 3
            elif req.priority == "medium":
                req_complexity = 2
            
            # Check if adding to current phase exceeds complexity
            if phase_complexity + req_complexity > max_complexity_per_phase and current_phase:
                phases.append(current_phase)
                current_phase = [req_key]
                phase_complexity = req_complexity
            else:
                current_phase.append(req_key)
                phase_complexity += req_complexity
        
        if current_phase:
            phases.append(current_phase)
        
        # Limit number of phases
        if len(phases) > max_phases:
            # Merge smaller phases
            merged_phases = phases[:max_phases-1]
            merged_phases.append([req for phase in phases[max_phases-1:] for req in phase])
            phases = merged_phases
        
        return phases
    
    @staticmethod
    def _calculate_complexity(group: List[str], req_map: Dict[str, Requirement]) -> float:
        """Calculate phase complexity score"""
        complexity = 0.0
        for req_key in group:
            req = req_map[req_key]
            if req.priority == "critical":
                complexity += 4
            elif req.priority == "high":
                complexity += 3
            elif req.priority == "medium":
                complexity += 2
            else:
                complexity += 1
            
            # Add complexity for acceptance criteria
            complexity += len(req.acceptance_criteria) * 0.5
        
        return complexity
    
    @staticmethod
    def _assess_risk(group: List[str], req_map: Dict[str, Requirement]) -> str:
        """Assess risk level for phase"""
        has_critical = any(req_map[k].priority == "critical" for k in group)
        has_high = any(req_map[k].priority == "high" for k in group)
        
        if has_critical:
            return "critical"
        elif has_high:
            return "high"
        elif len(group) > 5:
            return "high"
        elif len(group) > 3:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _estimate_duration(
        group: List[str], 
        req_map: Dict[str, Requirement],
        complexity: float
    ) -> float:
        """Estimate phase duration in days"""
        # Base duration from complexity
        base_days = complexity * 2
        
        # Adjust for dependencies
        max_deps = max(
            len(req_map[k].dependencies or []) 
            for k in group
        )
        dependency_factor = 1 + (max_deps * 0.1)
        
        # Round to nearest 0.5
        duration = math.ceil(base_days * dependency_factor * 2) / 2
        
        return min(duration, 30)  # Cap at 30 days per phase
    
    @staticmethod
    def _generate_phase_title(group: List[str], req_map: Dict[str, Requirement]) -> str:
        """Generate descriptive phase title"""
        # Find common theme
        categories = defaultdict(int)
        for req_key in group:
            req = req_map[req_key]
            if req.metadata and "category" in req.metadata:
                categories[req.metadata["category"]] += 1
        
        if categories:
            main_category = max(categories, key=categories.get)
            return f"{main_category.title()} Implementation"
        
        # Fallback to priority-based title
        priorities = [req_map[k].priority for k in group]
        if "critical" in priorities:
            return "Critical Features Implementation"
        elif "high" in priorities:
            return "Core Features Development"
        else:
            return "Feature Development"
    
    @staticmethod
    def _generate_phase_objective(group: List[str], req_map: Dict[str, Requirement]) -> str:
        """Generate phase objective"""
        req_titles = [req_map[k].title for k in group[:3]]  # First 3
        if len(group) > 3:
            req_titles.append(f"and {len(group)-3} more")
        
        return f"Implement and deliver: {', '.join(req_titles)}"
    
    @staticmethod
    def _generate_deliverables(group: List[str], req_map: Dict[str, Requirement]) -> List[str]:
        """Generate phase deliverables"""
        deliverables = []
        
        for req_key in group:
            req = req_map[req_key]
            deliverables.append(f"{req.title} - fully implemented and tested")
        
        deliverables.append("Updated documentation")
        deliverables.append("Test coverage report")
        
        return deliverables[:10]  # Limit to 10
    
    @staticmethod
    def _generate_activities(group: List[str], req_map: Dict[str, Requirement]) -> List[str]:
        """Generate phase activities"""
        activities = [
            "Requirements analysis and design",
            "Implementation",
            "Unit testing",
            "Integration testing",
            "Code review",
            "Documentation update"
        ]
        
        if any(req_map[k].priority in ["high", "critical"] for k in group):
            activities.insert(2, "Security review")
            activities.append("Performance testing")
        
        return activities
    
    @staticmethod
    def _identify_risks(group: List[str], req_map: Dict[str, Requirement]) -> List[str]:
        """Identify phase risks"""
        risks = []
        
        # Check for complex dependencies
        total_deps = sum(len(req_map[k].dependencies or []) for k in group)
        if total_deps > 5:
            risks.append("Complex dependency chain may cause delays")
        
        # Check for missing acceptance criteria
        missing_criteria = [k for k in group if not req_map[k].acceptance_criteria]
        if missing_criteria:
            risks.append(f"Incomplete acceptance criteria for {len(missing_criteria)} requirements")
        
        # Check priority
        if any(req_map[k].priority == "critical" for k in group):
            risks.append("Critical requirements - failure impacts entire project")
        
        if not risks:
            risks.append("Standard implementation risks")
        
        return risks
    
    @staticmethod
    def _generate_dod(group: List[str], req_map: Dict[str, Requirement]) -> List[str]:
        """Generate Definition of Done"""
        dod = [
            "All requirements implemented",
            "Unit tests passing (>80% coverage)",
            "Integration tests passing",
            "Code reviewed and approved",
            "Documentation updated"
        ]
        
        if any(req_map[k].priority in ["high", "critical"] for k in group):
            dod.append("Security review completed")
            dod.append("Performance benchmarks met")
        
        # Add specific acceptance criteria
        for req_key in group[:2]:  # First 2 requirements
            req = req_map[req_key]
            if req.acceptance_criteria:
                dod.append(f"{req.key}: {req.acceptance_criteria[0]}")
        
        return dod
    
    @staticmethod
    def _estimate_resources(
        group: List[str], 
        req_map: Dict[str, Requirement],
        complexity: float
    ) -> Dict[str, int]:
        """Estimate required resources"""
        resources = {
            "developers": max(1, min(int(complexity / 3), 5)),
            "qa": max(1, int(len(group) / 3))
        }
        
        if any(req_map[k].priority == "critical" for k in group):
            resources["architects"] = 1
            resources["security"] = 1
        
        return resources
    
    @staticmethod
    def _generate_checklist_phases(existing_phases: int) -> List[Dict[str, Any]]:
        """Generate standard checklist phases"""
        checklist_phases = []
        
        # Testing phase
        checklist_phases.append({
            "phase_id": f"PH-{existing_phases + 1:02d}",
            "title": "Quality Assurance & Testing",
            "objective": "Comprehensive testing and quality validation",
            "deliverables": ["Test reports", "Bug fixes", "Performance metrics"],
            "activities": ["System testing", "UAT", "Performance testing", "Security testing"],
            "dependencies": [f"PH-{existing_phases:02d}"],
            "estimated_days": 10.0,
            "risk_level": "medium",
            "risks": ["Potential critical bugs discovery", "Performance issues"],
            "requirements_covered": [],
            "definition_of_done": ["All tests passing", "No critical bugs", "Performance SLA met"],
            "resources_required": {"qa": 3, "developers": 2}
        })
        
        # Deployment phase  
        checklist_phases.append({
            "phase_id": f"PH-{existing_phases + 2:02d}",
            "title": "Deployment & Go-Live",
            "objective": "Production deployment and monitoring setup",
            "deliverables": ["Deployed application", "Monitoring dashboards", "Runbooks"],
            "activities": ["Environment setup", "Deployment", "Monitoring setup", "Knowledge transfer"],
            "dependencies": [f"PH-{existing_phases + 1:02d}"],
            "estimated_days": 5.0,
            "risk_level": "high",
            "risks": ["Deployment failures", "Production issues"],
            "requirements_covered": [],
            "definition_of_done": ["Successfully deployed", "Monitoring active", "Team trained"],
            "resources_required": {"devops": 2, "developers": 1}
        })
        
        return checklist_phases
    
    @staticmethod
    def get_latest_plan(db: Session, project_id: UUID) -> Optional[Plan]:
        """Get the latest plan for a project"""
        return db.query(Plan).filter(
            Plan.project_id == project_id
        ).order_by(desc(Plan.version)).first()
    
    @staticmethod
    def get_plan_by_id(db: Session, project_id: UUID, plan_id: UUID) -> Optional[Plan]:
        """Get specific plan by ID"""
        return db.query(Plan).filter(
            Plan.id == plan_id,
            Plan.project_id == project_id
        ).first()