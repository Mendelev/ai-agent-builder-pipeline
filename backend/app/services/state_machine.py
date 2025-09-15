# backend/app/services/state_machine.py
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from langgraph.graph import END, StateGraph

from app.core.observability import get_logger
from app.models.orchestration import ProjectState

logger = get_logger(__name__)


class StateMachine:
    """Project state machine using LangGraph"""

    # Valid state transitions
    TRANSITIONS = {
        ProjectState.DRAFT: [ProjectState.REQS_REFINING],
        ProjectState.REQS_REFINING: [ProjectState.REQS_READY, ProjectState.BLOCKED],
        ProjectState.REQS_READY: [ProjectState.CODE_VALIDATED, ProjectState.PLAN_READY],
        ProjectState.CODE_VALIDATED: [ProjectState.PLAN_READY],
        ProjectState.PLAN_READY: [ProjectState.PROMPTS_READY],
        ProjectState.PROMPTS_READY: [ProjectState.DONE],
        ProjectState.BLOCKED: [ProjectState.DRAFT, ProjectState.REQS_REFINING],
        ProjectState.DONE: [],  # Terminal state
    }

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the state graph"""
        workflow = StateGraph(dict)

        # Add nodes for each state
        for state in ProjectState:
            workflow.add_node(state.value, self._state_handler)

        # Add edges based on transitions
        for from_state, to_states in self.TRANSITIONS.items():
            for to_state in to_states:
                workflow.add_edge(from_state.value, to_state.value)

        # Set entry point
        workflow.set_entry_point(ProjectState.DRAFT.value)

        # Add end conditions
        workflow.add_edge(ProjectState.DONE.value, END)

        return workflow.compile()

    def _state_handler(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle state node execution"""
        current_state = state.get("current_state")
        logger.info(f"Processing state: {current_state}", extra=state)
        return state

    @classmethod
    def validate_transition(cls, from_state: ProjectState, to_state: ProjectState) -> Tuple[bool, Optional[str]]:
        """Validate if a state transition is allowed"""
        if from_state == to_state:
            return True, None  # No-op transition

        valid_transitions = cls.TRANSITIONS.get(from_state, [])
        if to_state not in valid_transitions:
            return False, f"Invalid transition from {from_state.value} to {to_state.value}"

        return True, None

    @classmethod
    def get_next_states(cls, current_state: ProjectState) -> List[ProjectState]:
        """Get valid next states from current state"""
        return cls.TRANSITIONS.get(current_state, [])

    @classmethod
    def is_terminal_state(cls, state: ProjectState) -> bool:
        """Check if state is terminal"""
        return state == ProjectState.DONE

    @classmethod
    def can_retry_in_state(cls, state: ProjectState, agent: str) -> bool:
        """Check if an agent can be retried in current state"""
        retry_rules = {
            ProjectState.DRAFT: ["REQUIREMENTS"],
            ProjectState.REQS_REFINING: ["REFINE"],
            ProjectState.REQS_READY: ["PLAN", "VALIDATION"],
            ProjectState.CODE_VALIDATED: ["PLAN"],
            ProjectState.PLAN_READY: ["PROMPTS"],
            ProjectState.BLOCKED: ["REQUIREMENTS", "REFINE"],
        }

        allowed_agents = retry_rules.get(state, [])
        return agent in allowed_agents

    @staticmethod
    def compute_input_hash(agent: str, data: Dict[str, Any]) -> str:
        """Compute deterministic hash for deduplication"""
        # Sort keys for consistent hashing
        canonical = json.dumps({"agent": agent, "data": data}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()
