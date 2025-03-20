"""
test_event_system_standardization.py

Description: Tests for the standardized event system implementation
Usage:
    python -m pytest tests/test_event_system_standardization.py
"""

import pytest
import logging
from typing import Dict, Any

# Import standardized event types
from src.interfaces.events import EventType, EventHandler, EventData
from src.interfaces.i_data_store import IDataStore

# Import concrete implementations
from src.services.dataframe_store import DataFrameStore
from src.services.service_factory import ServiceFactory
from src.app_bootstrapper import AppBootstrapper

# Setup logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_event_type_standardization():
    """Test that EventType is standardized and consistent."""
    # Verify that all expected event types are present
    assert hasattr(EventType, "ENTRIES_UPDATED")
    assert hasattr(EventType, "CORRECTION_RULES_UPDATED")
    assert hasattr(EventType, "VALIDATION_LISTS_UPDATED")
    assert hasattr(EventType, "VALIDATION_COMPLETED")
    assert hasattr(EventType, "CORRECTION_APPLIED")
    assert hasattr(EventType, "ERROR_OCCURRED")


def test_dataframe_store_implements_idatastore():
    """Test that DataFrameStore properly implements IDataStore."""
    # Check if DataFrameStore is an instance of IDataStore
    data_store = DataFrameStore()
    assert isinstance(data_store, IDataStore)

    # Verify that all required methods are implemented
    assert hasattr(data_store, "get_entries")
    assert hasattr(data_store, "set_entries")
    assert hasattr(data_store, "get_validation_list")
    assert hasattr(data_store, "set_validation_list")
    assert hasattr(data_store, "add_validation_entry")
    assert hasattr(data_store, "remove_validation_entry")
    assert hasattr(data_store, "get_correction_rules")
    assert hasattr(data_store, "set_correction_rules")
    assert hasattr(data_store, "begin_transaction")
    assert hasattr(data_store, "commit_transaction")
    assert hasattr(data_store, "rollback_transaction")
    assert hasattr(data_store, "subscribe")
    assert hasattr(data_store, "unsubscribe")


def test_event_subscription_and_emission():
    """Test that event subscription and emission works correctly."""
    data_store = DataFrameStore()

    # Create a flag to track event emission
    event_received = False
    received_data = {}

    # Create an event handler
    def test_handler(data: EventData) -> None:
        nonlocal event_received, received_data
        event_received = True
        received_data = data

    # Subscribe to an event
    data_store.subscribe(EventType.ENTRIES_UPDATED, test_handler)

    # Emit the event through internal method (simulating a real update)
    test_data = {"count": 5, "source": "test"}
    data_store._emit_event(EventType.ENTRIES_UPDATED, test_data)

    # Verify the event was received
    assert event_received is True
    assert received_data == test_data

    # Unsubscribe and emit again
    data_store.unsubscribe(EventType.ENTRIES_UPDATED, test_handler)

    # Reset flags
    event_received = False
    received_data = {}

    # Emit again
    data_store._emit_event(EventType.ENTRIES_UPDATED, {"count": 10})

    # Verify the event was not received after unsubscribing
    assert event_received is False
    assert received_data == {}


def test_app_bootstrapper_with_standardized_events():
    """Test that AppBootstrapper works with standardized events."""
    # Initialize app bootstrapper
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()

    # Get the IDataStore from the service factory
    service_factory = bootstrapper.service_factory
    data_store = service_factory.get_service(IDataStore)

    # Verify it's a valid implementation
    assert isinstance(data_store, IDataStore)

    # Test event subscription
    event_received = False

    def test_handler(data: EventData) -> None:
        nonlocal event_received
        event_received = True

    # Subscribe and emit
    data_store.subscribe(EventType.INFO_MESSAGE, test_handler)
    data_store._emit_event(EventType.INFO_MESSAGE, {"message": "Test message"})

    # Verify the event was received
    assert event_received is True
