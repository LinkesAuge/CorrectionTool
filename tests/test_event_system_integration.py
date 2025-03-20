"""
test_event_system_integration.py

Description: Integration test for the event system to demonstrate component communication
Usage:
    python -m pytest tests/test_event_system_integration.py -v
"""

import logging
from typing import Dict, Any, List
import pytest
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

# Import from the project
from src.interfaces.events import EventType
from src.services.event_manager import EventManager


class TestEventSystemIntegration:
    """Integration tests for the event system."""

    def setup_method(self):
        """Set up test environment."""
        # Clear all event subscriptions before each test
        EventManager.clear_subscribers()

    def teardown_method(self):
        """Clean up after each test."""
        # Clear all event subscriptions after each test
        EventManager.clear_subscribers()

    def test_basic_event_communication(self):
        """Test basic communication between components through events."""
        # Create tracking variables to verify event flow
        events_received = {
            "component_a_emitted": False,
            "component_b_received": False,
            "component_b_reacted": False,
            "component_c_refreshed": False,
        }

        event_data_received = {}

        # Define component A - emits events
        class ComponentA:
            def __init__(self):
                self.name = "ComponentA"

            def do_work(self):
                """Perform some work and emit an event."""
                # Log that we're doing work
                logging.info(f"{self.name} is doing work")

                # Emit an event
                data = {"source": self.name, "status": "completed"}
                logging.info(f"{self.name} emitting INFO_MESSAGE event: {data}")
                EventManager.emit(EventType.INFO_MESSAGE, data)

                # Record that we emitted an event
                events_received["component_a_emitted"] = True
                return True

        # Define component B - receives events
        class ComponentB:
            def __init__(self):
                self.name = "ComponentB"
                self.message_received = False

                # Subscribe to events
                EventManager.subscribe(EventType.INFO_MESSAGE, self._on_info_message)

            def _on_info_message(self, event_data):
                """Handle info message event."""
                # Log that we received an event
                logging.info(f"{self.name} received INFO_MESSAGE: {event_data}")

                # Store the event data
                event_data_received.update(event_data)
                self.message_received = True

                # Record that we received an event
                events_received["component_b_received"] = True

                # Do something in response
                self.react_to_message()

            def react_to_message(self):
                """React to the received message."""
                logging.info(f"{self.name} is reacting to message")

                # Record that we reacted
                events_received["component_b_reacted"] = True

                # Emit a different event
                data = {"source": self.name, "action": "processed"}
                logging.info(f"{self.name} emitting UI_REFRESH_NEEDED event: {data}")
                EventManager.emit(EventType.UI_REFRESH_NEEDED, data)

        # Define component C - receives the second event
        class ComponentC:
            def __init__(self):
                self.name = "ComponentC"
                self.refresh_triggered = False

                # Subscribe to events
                EventManager.subscribe(EventType.UI_REFRESH_NEEDED, self._on_refresh_needed)

            def _on_refresh_needed(self, event_data):
                """Handle refresh needed event."""
                # Log that we received an event
                logging.info(f"{self.name} received UI_REFRESH_NEEDED: {event_data}")

                # Store the event data
                event_data_received.update(event_data)
                self.refresh_triggered = True

                # Record that we received an event
                events_received["component_c_refreshed"] = True

        # Create instances of our components
        comp_a = ComponentA()
        comp_b = ComponentB()
        comp_c = ComponentC()

        # Execute the test
        logging.info("Starting event communication test")

        # Trigger the initial action
        comp_a.do_work()

        # Verify all events were received (regardless of order)
        for event_name, received in events_received.items():
            logging.info(f"Checking event {event_name}: {'✓' if received else '✗'}")
            assert received, f"Event {event_name} was not received"

        # Verify state changes
        assert comp_b.message_received is True, "ComponentB should have received the message"
        assert comp_c.refresh_triggered is True, "ComponentC should have been triggered to refresh"

        # Verify the data was passed correctly
        assert event_data_received["source"] == "ComponentB", (
            "Event data should contain source=ComponentB"
        )
        assert event_data_received["action"] == "processed", (
            "Event data should contain action=processed"
        )

        # Log success
        logging.info("All events were successfully processed")
