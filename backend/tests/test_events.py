"""
Tests for Behavior Events

Validates event logging and validation.
"""

import pytest

from app.schemas import EventType, EventCreate


class TestEventSchemas:
    """Tests for event schema validation."""

    def test_event_create_valid(self):
        """Test valid event creation."""
        event = EventCreate(
            task_id="task_123",
            event_type=EventType.OPTION_SELECTED,
            payload={"option_id": "opt_1", "is_first_selection": True},
        )
        
        assert event.task_id == "task_123"
        assert event.event_type == EventType.OPTION_SELECTED
        assert event.payload["option_id"] == "opt_1"

    def test_event_types_coverage(self):
        """Ensure all expected event types exist."""
        expected_types = [
            "task_started",
            "option_viewed",
            "option_selected",
            "option_changed",
            "reasoning_started",
            "reasoning_updated",
            "reasoning_submitted",
            "task_completed",
            "idle_detected",
            "focus_lost",
            "focus_gained",
        ]
        
        for event_type in expected_types:
            assert hasattr(EventType, event_type.upper())


class TestEventValidation:
    """Tests for event validation rules."""

    def test_valid_state_transitions(self):
        """Test that valid state transitions are allowed."""
        from app.services.event_service import VALID_TRANSITIONS
        
        # task_started can come from None (beginning)
        assert EventType.TASK_STARTED in VALID_TRANSITIONS[None]
        
        # option_selected can follow task_started
        assert EventType.OPTION_SELECTED in VALID_TRANSITIONS[EventType.TASK_STARTED]
        
        # option_changed can follow option_selected
        assert EventType.OPTION_CHANGED in VALID_TRANSITIONS[EventType.OPTION_SELECTED]
        
        # task_completed can follow option_selected
        assert EventType.TASK_COMPLETED in VALID_TRANSITIONS[EventType.OPTION_SELECTED]
        
        # task_started can follow task_completed (next task)
        assert EventType.TASK_STARTED in VALID_TRANSITIONS[EventType.TASK_COMPLETED]

    def test_reasoning_flow(self):
        """Test reasoning event flow."""
        from app.services.event_service import VALID_TRANSITIONS
        
        # reasoning_started can follow option_selected
        assert EventType.REASONING_STARTED in VALID_TRANSITIONS[EventType.OPTION_SELECTED]
        
        # reasoning_updated can follow reasoning_started
        assert EventType.REASONING_UPDATED in VALID_TRANSITIONS[EventType.REASONING_STARTED]
        
        # reasoning_submitted can follow reasoning_updated
        assert EventType.REASONING_SUBMITTED in VALID_TRANSITIONS[EventType.REASONING_UPDATED]
        
        # task_completed can follow reasoning_submitted
        assert EventType.TASK_COMPLETED in VALID_TRANSITIONS[EventType.REASONING_SUBMITTED]

    def test_idle_and_focus_events(self):
        """Test idle and focus events can occur at various points."""
        from app.services.event_service import VALID_TRANSITIONS
        
        # idle_detected can occur after task_started
        assert EventType.IDLE_DETECTED in VALID_TRANSITIONS[EventType.TASK_STARTED]
        
        # focus_lost can occur after option_selected
        assert EventType.FOCUS_LOST in VALID_TRANSITIONS[EventType.OPTION_SELECTED]
        
        # focus_gained can follow focus_lost
        assert EventType.FOCUS_GAINED in VALID_TRANSITIONS[EventType.FOCUS_LOST]
