# backend/tests/test_state_machine.py
import pytest
from app.services.state_machine import StateMachine
from app.models.orchestration import ProjectState

def test_validate_transition_valid():
    """Test valid state transitions."""
    # Valid transitions
    valid, error = StateMachine.validate_transition(
        ProjectState.DRAFT,
        ProjectState.REQS_REFINING
    )
    assert valid is True
    assert error is None
    
    valid, error = StateMachine.validate_transition(
        ProjectState.REQS_READY,
        ProjectState.PLAN_READY
    )
    assert valid is True

def test_validate_transition_invalid():
    """Test invalid state transitions."""
    # Invalid transition
    valid, error = StateMachine.validate_transition(
        ProjectState.DRAFT,
        ProjectState.DONE
    )
    assert valid is False
    assert "Invalid transition" in error
    
    # From terminal state
    valid, error = StateMachine.validate_transition(
        ProjectState.DONE,
        ProjectState.DRAFT
    )
    assert valid is False

def test_get_next_states():
    """Test getting valid next states."""
    next_states = StateMachine.get_next_states(ProjectState.DRAFT)
    assert ProjectState.REQS_REFINING in next_states

def test_is_terminal_state():
    """Test checking if state is terminal."""
    assert StateMachine.is_terminal_state(ProjectState.DONE) is True
    assert StateMachine.is_terminal_state(ProjectState.DRAFT) is False

def test_can_retry_in_state():  
    """Test if retries are allowed in certain states."""
    assert StateMachine.can_retry_in_state(ProjectState.REFINE) is True
    assert StateMachine.can_retry_in_state(ProjectState.DONE) is False

def test_compute_input_hash():
    """Test computing input hash."""
    input_data = {"key": "value"}
    hash1 = StateMachine.compute_input_hash(input_data)
    hash2 = StateMachine.compute_input_hash(input_data)
    assert hash1 == hash2
    
    different_input = {"key": "different_value"}
    hash3 = StateMachine.compute_input_hash(different_input)
    assert hash1 != hash3