"""
test_event_manager.py

Description: Tests for the EventManager class to verify event system functionality
Usage:
    python -m pytest tests/test_event_manager.py -v
"""

import pytest
import threading
import time
from typing import Dict, List, Any

# Import the classes to test
from src.interfaces.events import EventType, EventHandler, EventData
from src.services.event_manager import EventManager


@pytest.fixture
def reset_event_manager():
    """Reset the EventManager between tests."""
    # Clear all subscribers before each test
    EventManager.clear_subscribers()
    yield
    # Clear all subscribers after each test
    EventManager.clear_subscribers()


class TestEventManager:
    """Tests for the EventManager class."""

    def test_subscribe_and_unsubscribe(self, reset_event_manager):
        """Test subscribing and unsubscribing from events."""

        # Define a handler function
        def test_handler(event_data):
            pass

        # Subscribe to an event
        EventManager.subscribe(EventType.ENTRIES_UPDATED, test_handler)

        # Verify the subscription
        assert EventManager.get_subscriber_count(EventType.ENTRIES_UPDATED) == 1

        # Unsubscribe
        result = EventManager.unsubscribe(EventType.ENTRIES_UPDATED, test_handler)

        # Verify the unsubscription
        assert result is True
        assert EventManager.get_subscriber_count(EventType.ENTRIES_UPDATED) == 0

        # Try to unsubscribe again (should return False)
        result = EventManager.unsubscribe(EventType.ENTRIES_UPDATED, test_handler)
        assert result is False

    def test_emit_event(self, reset_event_manager):
        """Test emitting events to subscribed handlers."""
        # Create a mutable list to store results
        results = []

        # Define a handler function
        def test_handler(event_data):
            results.append(event_data)

        # Subscribe to an event
        EventManager.subscribe(EventType.ENTRIES_UPDATED, test_handler)

        # Emit an event
        event_data = {"source": "test", "value": 42}
        handler_count = EventManager.emit(EventType.ENTRIES_UPDATED, event_data)

        # Verify the event was received
        assert handler_count == 1
        assert len(results) == 1
        assert results[0]["source"] == "test"
        assert results[0]["value"] == 42
        assert results[0]["event_type"] == EventType.ENTRIES_UPDATED

        # Emit an event with no subscribers
        handler_count = EventManager.emit(EventType.CORRECTION_APPLIED, {"source": "test"})
        assert handler_count == 0
        assert len(results) == 1  # Still only the first event

    def test_multiple_subscribers(self, reset_event_manager):
        """Test multiple subscribers for the same event."""
        # Create mutable counters
        counter1 = {"count": 0}
        counter2 = {"count": 0}

        # Define handler functions
        def handler1(event_data):
            counter1["count"] += 1

        def handler2(event_data):
            counter2["count"] += 1

        # Subscribe both handlers
        EventManager.subscribe(EventType.ENTRIES_UPDATED, handler1)
        EventManager.subscribe(EventType.ENTRIES_UPDATED, handler2)

        # Verify the subscription count
        assert EventManager.get_subscriber_count(EventType.ENTRIES_UPDATED) == 2

        # Emit an event
        handler_count = EventManager.emit(EventType.ENTRIES_UPDATED, {"source": "test"})

        # Verify both handlers were called
        assert handler_count == 2
        assert counter1["count"] == 1
        assert counter2["count"] == 1

        # Unsubscribe one handler
        EventManager.unsubscribe(EventType.ENTRIES_UPDATED, handler1)

        # Emit another event
        handler_count = EventManager.emit(EventType.ENTRIES_UPDATED, {"source": "test"})

        # Verify only the second handler was called
        assert handler_count == 1
        assert counter1["count"] == 1  # Unchanged
        assert counter2["count"] == 2  # Incremented

    def test_clear_subscribers(self, reset_event_manager):
        """Test clearing subscribers."""

        # Define handler functions
        def handler1(event_data):
            pass

        def handler2(event_data):
            pass

        # Subscribe to different events
        EventManager.subscribe(EventType.ENTRIES_UPDATED, handler1)
        EventManager.subscribe(EventType.CORRECTION_APPLIED, handler2)

        # Verify the subscription counts
        assert EventManager.get_subscriber_count(EventType.ENTRIES_UPDATED) == 1
        assert EventManager.get_subscriber_count(EventType.CORRECTION_APPLIED) == 1

        # Clear subscribers for one event
        count = EventManager.clear_subscribers(EventType.ENTRIES_UPDATED)

        # Verify only that event's subscribers were cleared
        assert count == 1
        assert EventManager.get_subscriber_count(EventType.ENTRIES_UPDATED) == 0
        assert EventManager.get_subscriber_count(EventType.CORRECTION_APPLIED) == 1

        # Re-subscribe
        EventManager.subscribe(EventType.ENTRIES_UPDATED, handler1)

        # Clear all subscribers
        count = EventManager.clear_subscribers()

        # Verify all subscribers were cleared
        assert count == 2
        assert EventManager.get_subscriber_count(EventType.ENTRIES_UPDATED) == 0
        assert EventManager.get_subscriber_count(EventType.CORRECTION_APPLIED) == 0

    def test_exception_handling(self, reset_event_manager):
        """Test that exceptions in handlers don't stop event propagation."""
        # Create mutable counters
        counter1 = {"count": 0}
        counter2 = {"count": 0}

        # Define handler functions
        def handler1(event_data):
            counter1["count"] += 1
            raise Exception("Test exception")

        def handler2(event_data):
            counter2["count"] += 1

        # Subscribe both handlers
        EventManager.subscribe(EventType.ENTRIES_UPDATED, handler1)
        EventManager.subscribe(EventType.ENTRIES_UPDATED, handler2)

        # Emit an event
        handler_count = EventManager.emit(EventType.ENTRIES_UPDATED, {"source": "test"})

        # Verify both handlers were called, despite the exception in the first
        assert handler_count == 2
        assert counter1["count"] == 1
        assert counter2["count"] == 1

    def test_thread_safety(self, reset_event_manager):
        """Test thread safety of the EventManager."""
        # Create a shared counter
        counter = {"count": 0}
        lock = threading.Lock()

        # Define a handler function
        def handler(event_data):
            with lock:
                counter["count"] += 1
            time.sleep(0.001)  # Add a small delay to increase thread interleaving

        # Subscribe the handler
        EventManager.subscribe(EventType.ENTRIES_UPDATED, handler)

        # Create threads to emit events
        threads = []
        for i in range(10):
            thread = threading.Thread(
                target=EventManager.emit, args=(EventType.ENTRIES_UPDATED, {"thread_id": i})
            )
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        # Verify the handler was called for each emit
        assert counter["count"] == 10

    def test_valid_event_types(self, reset_event_manager):
        """Test that the EventManager only accepts valid EventType values."""

        # Define a handler function
        def handler(event_data):
            pass

        # Test with invalid event types
        with pytest.raises(ValueError):
            EventManager.subscribe("INVALID_EVENT", handler)

        with pytest.raises(ValueError):
            EventManager.unsubscribe("INVALID_EVENT", handler)

        with pytest.raises(ValueError):
            EventManager.emit("INVALID_EVENT", {"source": "test"})

        with pytest.raises(ValueError):
            EventManager.get_subscriber_count("INVALID_EVENT")

        with pytest.raises(ValueError):
            EventManager.clear_subscribers("INVALID_EVENT")

    def test_handler_must_be_callable(self, reset_event_manager):
        """Test that the EventManager only accepts callable handler functions."""
        # Test with non-callable handler
        with pytest.raises(ValueError):
            EventManager.subscribe(EventType.ENTRIES_UPDATED, "not_callable")

    def test_event_data_none(self, reset_event_manager):
        """Test that the EventManager handles None event data gracefully."""
        # Create a mutable list to store results
        results = []

        # Define a handler function
        def handler(event_data):
            results.append(event_data)

        # Subscribe the handler
        EventManager.subscribe(EventType.ENTRIES_UPDATED, handler)

        # Emit an event with None data
        EventManager.emit(EventType.ENTRIES_UPDATED)

        # Verify an empty dict was created and the event_type was added
        assert len(results) == 1
        assert "event_type" in results[0]
        assert results[0]["event_type"] == EventType.ENTRIES_UPDATED
