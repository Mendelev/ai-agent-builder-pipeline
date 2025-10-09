"""
Analyst Service - Requirement Refinement Logic
Implements heuristics for generating questions about requirements
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import re
from app.schemas.qa_session import Question, QuestionCategory, QualityFlags
from app.models.project import Requirement


class AnalystService:
    """
    Service for analyzing requirements and generating refinement questions.
    Uses heuristics to detect ambiguity, testability issues, and dependency conflicts.
    """
    
    # Keywords that indicate ambiguity
    AMBIGUOUS_WORDS = {
        "should", "might", "could", "maybe", "possibly", "probably",
        "some", "few", "many", "several", "various", "appropriate",
        "reasonable", "suitable", "adequate", "etc", "and so on"
    }
    
    # Keywords indicating untestable requirements
    UNTESTABLE_WORDS = {
        "user-friendly", "intuitive", "easy", "simple", "fast", "slow",
        "good", "bad", "nice", "beautiful", "clean", "elegant"
    }
    
    # Keywords for dependency detection
    DEPENDENCY_KEYWORDS = {
        "depends on", "requires", "needs", "uses", "integrates with",
        "calls", "connects to", "relies on", "based on"
    }
    
    def __init__(self):
        self.questions_cache: Dict[str, List[Question]] = {}
    
    def analyze_requirements(
        self,
        requirements: List[Requirement],
        max_questions: int = 10
    ) -> Tuple[List[Question], QualityFlags]:
        """
        Analyze requirements and generate refinement questions.
        
        Args:
            requirements: List of project requirements
            max_questions: Maximum number of questions to generate
            
        Returns:
            Tuple of (questions, quality_flags)
        """
        all_questions: List[Question] = []
        
        for req in requirements:
            req_text = self._extract_requirement_text(req.data)
            
            # Apply different heuristics
            all_questions.extend(self._check_testability(req_text, req.code))
            all_questions.extend(self._check_ambiguity(req_text, req.code))
            all_questions.extend(self._check_dependencies(req_text, req.code))
            all_questions.extend(self._check_acceptance_criteria(req_text, req.code))
            all_questions.extend(self._check_constraints(req_text, req.code))
        
        # Remove duplicates and prioritize
        unique_questions = self._deduplicate_questions(all_questions)
        prioritized_questions = self._prioritize_questions(unique_questions)[:max_questions]
        
        # Generate quality flags
        quality_flags = self._evaluate_question_quality(prioritized_questions, all_questions)
        
        return prioritized_questions, quality_flags
    
    def _extract_requirement_text(self, data: Dict[str, Any]) -> str:
        """Extract text content from requirement data (JSONB)"""
        if isinstance(data, dict):
            # Try common keys
            for key in ["description", "text", "content", "requirement"]:
                if key in data and isinstance(data[key], str):
                    return data[key]
            # Fallback: concatenate all string values
            return " ".join(str(v) for v in data.values() if isinstance(v, str))
        return str(data)
    
    def _check_testability(self, req_text: str, req_code: str) -> List[Question]:
        """Check for untestable or vague requirements"""
        questions = []
        req_lower = req_text.lower()
        
        # Check for untestable words
        found_untestable = [word for word in self.UNTESTABLE_WORDS if word in req_lower]
        
        if found_untestable:
            questions.append(Question(
                id=str(uuid4()),
                category=QuestionCategory.TESTABILITY,
                text=f"The requirement '{req_code}' uses subjective terms ({', '.join(found_untestable[:3])}). "
                     f"Can you provide measurable criteria? (e.g., response time < 2s, error rate < 0.1%)",
                context=f"Requirement: {req_text[:200]}...",
                priority=1  # High priority
            ))
        
        # Check for missing quantitative metrics
        has_numbers = bool(re.search(r'\d+', req_text))
        has_units = bool(re.search(r'\d+\s*(ms|s|min|hour|MB|GB|%|users?)', req_text, re.IGNORECASE))
        
        if not has_numbers and len(req_text) > 50:
            questions.append(Question(
                id=str(uuid4()),
                category=QuestionCategory.TESTABILITY,
                text=f"Requirement '{req_code}' lacks quantitative metrics. "
                     f"What are the measurable success criteria?",
                context=f"Requirement: {req_text[:200]}...",
                priority=2
            ))
        
        # Check for acceptance criteria
        if "acceptance" not in req_lower and "criteria" not in req_lower:
            questions.append(Question(
                id=str(uuid4()),
                category=QuestionCategory.ACCEPTANCE_CRITERIA,
                text=f"What are the acceptance criteria for requirement '{req_code}'?",
                context=f"Requirement: {req_text[:200]}...",
                priority=2
            ))
        
        return questions
    
    def _check_ambiguity(self, req_text: str, req_code: str) -> List[Question]:
        """Check for ambiguous language"""
        questions = []
        req_lower = req_text.lower()
        
        # Find ambiguous words
        found_ambiguous = [word for word in self.AMBIGUOUS_WORDS if word in req_lower]
        
        if found_ambiguous:
            questions.append(Question(
                id=str(uuid4()),
                category=QuestionCategory.AMBIGUITY,
                text=f"Requirement '{req_code}' contains ambiguous terms ({', '.join(found_ambiguous[:3])}). "
                     f"Can you clarify with specific values or conditions?",
                context=f"Requirement: {req_text[:200]}...",
                priority=1
            ))
        
        # Check for undefined pronouns
        if re.search(r'\b(it|this|that|these|those)\b', req_lower):
            if not re.search(r'(the\s+\w+|said\s+\w+|aforementioned)', req_lower):
                questions.append(Question(
                    id=str(uuid4()),
                    category=QuestionCategory.AMBIGUITY,
                    text=f"Requirement '{req_code}' uses pronouns (it/this/that). "
                         f"What do these pronouns refer to exactly?",
                    context=f"Requirement: {req_text[:200]}...",
                    priority=3
                ))
        
        return questions
    
    def _check_dependencies(self, req_text: str, req_code: str) -> List[Question]:
        """Check for dependency-related issues"""
        questions = []
        req_lower = req_text.lower()
        
        # Check for dependency keywords
        found_deps = [kw for kw in self.DEPENDENCY_KEYWORDS if kw in req_lower]
        
        if found_deps:
            questions.append(Question(
                id=str(uuid4()),
                category=QuestionCategory.DEPENDENCIES,
                text=f"Requirement '{req_code}' mentions dependencies ({found_deps[0]}). "
                     f"What are the specific external systems, libraries, or services required?",
                context=f"Requirement: {req_text[:200]}...",
                priority=2
            ))
            
            # Ask about version constraints
            questions.append(Question(
                id=str(uuid4()),
                category=QuestionCategory.DEPENDENCIES,
                text=f"For requirement '{req_code}', are there version constraints or compatibility requirements "
                     f"for the dependencies?",
                context=f"Requirement: {req_text[:200]}...",
                priority=3
            ))
        
        return questions
    
    def _check_acceptance_criteria(self, req_text: str, req_code: str) -> List[Question]:
        """Check for missing acceptance criteria"""
        questions = []
        req_lower = req_text.lower()
        
        # Check if acceptance criteria are defined
        has_given_when_then = all(kw in req_lower for kw in ["given", "when", "then"])
        has_acceptance = "acceptance" in req_lower or "criteria" in req_lower
        
        if not has_given_when_then and not has_acceptance and len(req_text) > 100:
            questions.append(Question(
                id=str(uuid4()),
                category=QuestionCategory.ACCEPTANCE_CRITERIA,
                text=f"Can you define acceptance criteria for requirement '{req_code}' "
                     f"in Given/When/Then format?",
                context=f"Requirement: {req_text[:200]}...",
                priority=2
            ))
        
        return questions
    
    def _check_constraints(self, req_text: str, req_code: str) -> List[Question]:
        """Check for constraints and edge cases"""
        questions = []
        req_lower = req_text.lower()
        
        # Check for error handling
        if "error" not in req_lower and "exception" not in req_lower and "fail" not in req_lower:
            questions.append(Question(
                id=str(uuid4()),
                category=QuestionCategory.CONSTRAINTS,
                text=f"How should the system handle errors or exceptions for requirement '{req_code}'?",
                context=f"Requirement: {req_text[:200]}...",
                priority=3
            ))
        
        # Check for boundaries and limits
        if re.search(r'\b(input|data|file|upload|request)\b', req_lower):
            if not re.search(r'\b(max|min|limit|size|length)\b', req_lower):
                questions.append(Question(
                    id=str(uuid4()),
                    category=QuestionCategory.CONSTRAINTS,
                    text=f"What are the size/length limits and boundaries for requirement '{req_code}'?",
                    context=f"Requirement: {req_text[:200]}...",
                    priority=3
                ))
        
        return questions
    
    def _deduplicate_questions(self, questions: List[Question]) -> List[Question]:
        """Remove duplicate or very similar questions"""
        seen_texts = set()
        unique_questions = []
        
        for q in questions:
            # Normalize text for comparison
            normalized = q.text.lower().strip()
            normalized = re.sub(r'\s+', ' ', normalized)
            
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                unique_questions.append(q)
        
        return unique_questions
    
    def _prioritize_questions(self, questions: List[Question]) -> List[Question]:
        """Sort questions by priority (1=highest)"""
        return sorted(questions, key=lambda q: (q.priority, q.category.value))
    
    def _evaluate_question_quality(
        self,
        selected_questions: List[Question],
        all_questions: List[Question]
    ) -> QualityFlags:
        """Evaluate the quality of generated questions"""
        duplicate_count = len(all_questions) - len(selected_questions)
        
        # Count questions by category
        category_counts = {}
        for q in selected_questions:
            category_counts[q.category] = category_counts.get(q.category, 0) + 1
        
        # Check for low quality (e.g., too generic)
        generic_count = sum(1 for q in selected_questions if len(q.text) < 50)
        has_low_quality = generic_count > len(selected_questions) * 0.3
        
        # Calculate quality score (0.0 - 1.0)
        diversity = len(category_counts) / len(QuestionCategory)
        specificity = 1.0 - (generic_count / max(len(selected_questions), 1))
        total_score = (diversity + specificity) / 2
        
        return QualityFlags(
            has_low_quality=has_low_quality,
            ambiguous_count=category_counts.get(QuestionCategory.AMBIGUITY, 0),
            duplicate_count=duplicate_count,
            total_score=round(total_score, 2),
            notes=f"Generated {len(selected_questions)} questions across {len(category_counts)} categories"
        )
    
    def refine_requirements_with_answers(
        self,
        requirements: List[Requirement],
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Refine requirements based on provided answers.
        Returns updated requirement data and change diffs.
        """
        refinements = []
        
        for answer in answers:
            question_id = answer.get("question_id")
            answer_text = answer.get("text", "")
            
            # TODO: Implement actual requirement refinement logic
            # This would involve:
            # 1. Finding which requirement the question relates to
            # 2. Updating the requirement text based on the answer
            # 3. Creating a diff of the changes
            # 4. Validating the refined requirement
            
            refinements.append({
                "question_id": question_id,
                "applied": True,
                "changes": f"Applied answer: {answer_text[:100]}..."
            })
        
        return {
            "refinements": refinements,
            "total_changes": len(refinements)
        }
