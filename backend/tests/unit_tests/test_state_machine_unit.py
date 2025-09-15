# Unit version of state machine tests (no external deps)
import pytest
from app.services.state_machine import StateMachine
from app.models.orchestration import ProjectState


def test_validate_transition_valid_unit():
    valid, error = StateMachine.validate_transition(
        ProjectState.DRAFT,
        ProjectState.REQS_REFINING,
    )
    assert valid is True
    assert error is None

    valid, error = StateMachine.validate_transition(
        ProjectState.REQS_READY,
        ProjectState.PLAN_READY,
    )
    assert valid is True


def test_validate_transition_invalid_unit():
    valid, error = StateMachine.validate_transition(
        ProjectState.DRAFT,
        ProjectState.DONE,
    )
    assert valid is False
    assert "Invalid transition" in error

    valid, error = StateMachine.validate_transition(
        ProjectState.DONE,
        ProjectState.DRAFT,
    )
    assert valid is False


def test_get_next_states_unit():
    next_states = StateMachine.get_next_states(ProjectState.DRAFT)
    assert ProjectState.REQS_REFINING in next_states
    assert len(next_states) == 1

    next_states = StateMachine.get_next_states(ProjectState.REQS_READY)
    assert ProjectState.CODE_VALIDATED in next_states
    assert ProjectState.PLAN_READY in next_states

    next_states = StateMachine.get_next_states(ProjectState.DONE)
    assert len(next_states) == 0


def test_is_terminal_state_unit():
    assert StateMachine.is_terminal_state(ProjectState.DONE) is True
    assert StateMachine.is_terminal_state(ProjectState.DRAFT) is False
    assert StateMachine.is_terminal_state(ProjectState.BLOCKED) is False


def test_can_retry_in_state_unit():
    assert StateMachine.can_retry_in_state(ProjectState.REQS_REFINING, "REFINE") is True
    assert StateMachine.can_retry_in_state(ProjectState.DRAFT, "PLAN") is False
    assert StateMachine.can_retry_in_state(ProjectState.PLAN_READY, "PROMPTS") is True
    assert StateMachine.can_retry_in_state(ProjectState.DONE, "REFINE") is False


def test_compute_input_hash_unit():
    data1 = {"key": "value", "number": 123}
    data2 = {"number": 123, "key": "value"}

    hash1 = StateMachine.compute_input_hash("REFINE", data1)
    hash2 = StateMachine.compute_input_hash("REFINE", data2)
    assert hash1 == hash2

    data3 = {"key": "different"}
    hash3 = StateMachine.compute_input_hash("REFINE", data3)
    assert hash1 != hash3

    hash4 = StateMachine.compute_input_hash("PLAN", data1)
    assert hash1 != hash4

