# backend/tests/test_state_machine.py
from app.models.orchestration import ProjectState
from app.services.state_machine import StateMachine


def test_validate_transition_valid():
    """Test valid state transitions."""
    # Valid transitions
    valid, error = StateMachine.validate_transition(ProjectState.DRAFT, ProjectState.REQS_REFINING)
    assert valid is True
    assert error is None

    valid, error = StateMachine.validate_transition(ProjectState.REQS_READY, ProjectState.PLAN_READY)
    assert valid is True


def test_validate_transition_invalid():
    """Test invalid state transitions."""
    # Invalid transition
    valid, error = StateMachine.validate_transition(ProjectState.DRAFT, ProjectState.DONE)
    assert valid is False
    assert "Invalid transition" in error

    # From terminal state
    valid, error = StateMachine.validate_transition(ProjectState.DONE, ProjectState.DRAFT)
    assert valid is False


def test_get_next_states():
    """Test getting valid next states."""
    next_states = StateMachine.get_next_states(ProjectState.DRAFT)
    assert ProjectState.REQS_REFINING in next_states
    assert len(next_states) == 1

    next_states = StateMachine.get_next_states(ProjectState.REQS_READY)
    assert ProjectState.CODE_VALIDATED in next_states
    assert ProjectState.PLAN_READY in next_states

    next_states = StateMachine.get_next_states(ProjectState.DONE)
    assert len(next_states) == 0


def test_is_terminal_state():
    """Test terminal state detection."""
    assert StateMachine.is_terminal_state(ProjectState.DONE) is True
    assert StateMachine.is_terminal_state(ProjectState.DRAFT) is False
    assert StateMachine.is_terminal_state(ProjectState.BLOCKED) is False


def test_can_retry_in_state():
    """Test agent retry permissions by state."""
    # Can retry REFINE in REQS_REFINING
    assert StateMachine.can_retry_in_state(ProjectState.REQS_REFINING, "REFINE") is True

    # Cannot retry PLAN in DRAFT
    assert StateMachine.can_retry_in_state(ProjectState.DRAFT, "PLAN") is False

    # Can retry PROMPTS in PLAN_READY
    assert StateMachine.can_retry_in_state(ProjectState.PLAN_READY, "PROMPTS") is True

    # Cannot retry anything in DONE
    assert StateMachine.can_retry_in_state(ProjectState.DONE, "REFINE") is False


def test_compute_input_hash():
    """Test deterministic hash computation."""
    data1 = {"key": "value", "number": 123}
    data2 = {"number": 123, "key": "value"}  # Different order

    hash1 = StateMachine.compute_input_hash("REFINE", data1)
    hash2 = StateMachine.compute_input_hash("REFINE", data2)

    # Should be the same despite different order
    assert hash1 == hash2

    # Different data should produce different hash
    data3 = {"key": "different"}
    hash3 = StateMachine.compute_input_hash("REFINE", data3)
    assert hash1 != hash3

    # Different agent should produce different hash
    hash4 = StateMachine.compute_input_hash("PLAN", data1)
    assert hash1 != hash4
