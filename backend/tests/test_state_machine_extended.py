# backend/tests/test_state_machine_extended.py
from unittest.mock import MagicMock, patch

from app.models.enums import ProjectState
from app.services.state_machine import StateMachine


def test_state_machine_init():
    """Test StateMachine initialization."""
    sm = StateMachine()
    assert sm.graph is not None
    assert hasattr(sm, "TRANSITIONS")


def test_state_machine_build_graph():
    """Test building state graph."""
    sm = StateMachine()
    graph = sm._build_graph()
    assert graph is not None


@patch("app.services.state_machine.StateGraph")
def test_state_machine_graph_construction(mock_state_graph):
    """Test state machine graph construction with mocks."""
    mock_workflow = MagicMock()
    mock_state_graph.return_value = mock_workflow
    mock_workflow.compile.return_value = "compiled_graph"

    sm = StateMachine()
    # Test individual graph building
    sm._build_graph()

    # Verify StateGraph was called
    assert mock_state_graph.call_count >= 1
    # Verify nodes were added for each state
    expected_calls = len(ProjectState)
    assert mock_workflow.add_node.call_count >= expected_calls

    # Verify entry point was set
    assert mock_workflow.set_entry_point.call_count >= 1

    # Verify compilation
    assert mock_workflow.compile.call_count >= 1


def test_state_handler():
    """Test state handler method."""
    sm = StateMachine()
    # Test with mock state
    test_state = {"current_state": "draft"}
    result = sm._state_handler(test_state)

    # Should return the same state (no-op handler)
    assert result == test_state


def test_transitions_completeness():
    """Test that all states have transition definitions."""
    sm = StateMachine()

    # Check that all non-terminal states have transitions defined
    for state in ProjectState:
        if state != ProjectState.DONE:  # DONE is terminal
            assert state in sm.TRANSITIONS
    # Check DONE state is terminal
    assert sm.TRANSITIONS[ProjectState.DONE] == []


def test_specific_state_transitions():
    """Test specific state transition rules."""
    sm = StateMachine()

    # Test some specific transitions based on actual TRANSITIONS
    assert ProjectState.REQS_REFINING in sm.TRANSITIONS[ProjectState.DRAFT]
    assert ProjectState.PLAN_READY in sm.TRANSITIONS[ProjectState.CODE_VALIDATED]
    assert ProjectState.PROMPTS_READY in sm.TRANSITIONS[ProjectState.PLAN_READY]
    assert ProjectState.DONE in sm.TRANSITIONS[ProjectState.PROMPTS_READY]


def test_blocked_state_transitions():
    """Test blocked state transition rules."""
    sm = StateMachine()

    blocked_transitions = sm.TRANSITIONS[ProjectState.BLOCKED]
    assert ProjectState.DRAFT in blocked_transitions
    assert ProjectState.REQS_REFINING in blocked_transitions
