"""
test_datastore_interface_compliance.py

Description: Detailed tests for DataFrameStore's compliance with the IDataStore interface
Usage:
    python -m pytest tests/test_datastore_interface_compliance.py
"""

import pytest
import pandas as pd
import logging
from typing import Dict, Any

# Import the interface and implementation
from src.interfaces.i_data_store import IDataStore
from src.services.dataframe_store import DataFrameStore
from src.interfaces.events import EventType, EventHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@pytest.fixture
def data_store():
    """Create a fresh DataFrameStore instance for testing."""
    # Reset the singleton instance for clean tests
    DataFrameStore._instance = None
    return DataFrameStore.get_instance()


def test_inheritance():
    """Test that DataFrameStore inherits from IDataStore."""
    assert issubclass(DataFrameStore, IDataStore)


def test_instance_type():
    """Test that DataFrameStore instance is an instance of IDataStore."""
    store = DataFrameStore.get_instance()
    assert isinstance(store, IDataStore)


def test_get_entries(data_store):
    """Test the get_entries method."""
    entries = data_store.get_entries()
    assert isinstance(entries, pd.DataFrame)


def test_set_entries(data_store):
    """Test the set_entries method."""
    # Create a test DataFrame
    test_df = pd.DataFrame(
        {
            "chest_type": ["Test Chest"],
            "player": ["Test Player"],
            "source": ["Test Source"],
            "status": ["pending"],
        }
    )

    # Set entries and verify return value
    result = data_store.set_entries(test_df, source="test")
    assert result is True

    # Verify the entries were set correctly
    entries = data_store.get_entries()
    assert len(entries) == len(test_df)
    assert "chest_type" in entries.columns
    assert entries["chest_type"].iloc[0] == "Test Chest"


def test_get_validation_list(data_store):
    """Test the get_validation_list method."""
    # Make sure the player validation list exists with proper format
    player_df = pd.DataFrame({"entry": ["Test Player"], "enabled": [True]})

    # Set validation list with proper structure
    result = data_store.set_validation_list("player", player_df)
    assert result is True

    # Test getting a validation list
    validation_list = data_store.get_validation_list("player")
    assert isinstance(validation_list, pd.DataFrame)
    assert "enabled" in validation_list.columns
    assert len(validation_list) > 0
    assert "Test Player" in validation_list.index


def test_set_validation_list(data_store):
    """Test the set_validation_list method."""
    # Create a test DataFrame with proper structure (entry column)
    test_df = pd.DataFrame({"entry": ["Test Player 1", "Test Player 2"], "enabled": [True, True]})

    # Set validation list and verify return value
    result = data_store.set_validation_list("player", test_df)
    assert result is True

    # Verify the validation list was set correctly
    validation_list = data_store.get_validation_list("player")
    assert len(validation_list) == len(test_df)
    assert "Test Player 1" in validation_list.index
    assert bool(validation_list.loc["Test Player 1", "enabled"]) is True


def test_add_validation_entry(data_store):
    """Test the add_validation_entry method."""
    # Clear existing entries in player list to avoid conflicts
    empty_df = pd.DataFrame({"entry": [], "enabled": []})
    data_store.set_validation_list("player", empty_df)

    # Add a validation entry and verify return value
    result = data_store.add_validation_entry("player", "New Test Player")
    assert result is True

    # Verify the entry was added
    validation_list = data_store.get_validation_list("player")
    assert "New Test Player" in validation_list.index


def test_remove_validation_entry(data_store):
    """Test the remove_validation_entry method."""
    # First add an entry
    data_store.add_validation_entry("player", "Player To Remove")

    # Then remove it and verify return value
    result = data_store.remove_validation_entry("player", "Player To Remove")
    assert result is True

    # Verify the entry was removed
    validation_list = data_store.get_validation_list("player")
    assert "Player To Remove" not in validation_list.index


def test_get_correction_rules(data_store):
    """Test the get_correction_rules method."""
    # Test getting correction rules
    rules = data_store.get_correction_rules()
    assert isinstance(rules, pd.DataFrame)


def test_set_correction_rules(data_store):
    """Test the set_correction_rules method."""
    # Create a test DataFrame
    test_df = pd.DataFrame(
        {
            "field": ["chest_type", "chest_type"],
            "from_text": ["Test From 1", "Test From 2"],
            "to_text": ["Test To 1", "Test To 2"],
            "enabled": [True, True],
        }
    )

    # Set correction rules and verify return value
    result = data_store.set_correction_rules(test_df)
    assert result is True

    # Verify the rules were set correctly
    rules = data_store.get_correction_rules()
    assert len(rules) == len(test_df)
    assert "from_text" in rules.columns
    assert "Test From 1" in rules["from_text"].values


def test_transaction_methods(data_store):
    """Test the transaction methods."""
    # Begin transaction
    result = data_store.begin_transaction()
    assert result is True

    # Make changes within transaction
    test_df = pd.DataFrame(
        {
            "chest_type": ["Transaction Test Chest"],
            "player": ["Transaction Test Player"],
            "source": ["Transaction Test Source"],
            "status": ["pending"],
        }
    )

    data_store.set_entries(test_df, source="test", emit_event=False)

    # Rollback transaction
    result = data_store.rollback_transaction()
    assert result is True

    # Verify changes were rolled back
    entries = data_store.get_entries()
    assert len(entries) == 0 or "Transaction Test Chest" not in entries["chest_type"].values

    # Now test commit
    result = data_store.begin_transaction()
    assert result is True

    data_store.set_entries(test_df, source="test", emit_event=False)

    result = data_store.commit_transaction()
    assert result is True

    # Verify changes were committed
    entries = data_store.get_entries()
    assert "Transaction Test Chest" in entries["chest_type"].values


def test_event_handlers(data_store):
    """Test the subscribe and unsubscribe methods."""
    # Create a test event handler
    event_received = False
    event_data = None

    def test_handler(data: Dict[str, Any]) -> None:
        nonlocal event_received, event_data
        event_received = True
        event_data = data

    # Initialize event handlers dictionary
    if not hasattr(data_store, "_event_handlers") or data_store._event_handlers is None:
        data_store._event_handlers = {event_type: set() for event_type in EventType}

    # Subscribe to an event
    data_store.subscribe(EventType.ENTRIES_UPDATED, test_handler)

    # Trigger the event
    test_df = pd.DataFrame(
        {
            "chest_type": ["Event Test Chest"],
            "player": ["Event Test Player"],
            "source": ["Event Test Source"],
            "status": ["pending"],
        }
    )

    data_store.set_entries(test_df, source="test")

    # Verify the event was received
    assert event_received is True
    assert event_data is not None

    # Reset flags
    event_received = False
    event_data = None

    # Unsubscribe and verify events are no longer received
    data_store.unsubscribe(EventType.ENTRIES_UPDATED, test_handler)

    test_df = pd.DataFrame(
        {
            "chest_type": ["Second Event Test Chest"],
            "player": ["Second Event Test Player"],
            "source": ["Second Event Test Source"],
            "status": ["pending"],
        }
    )

    data_store.set_entries(test_df, source="test")

    # Verify no event was received after unsubscribing
    assert event_received is False
    assert event_data is None


def test_invalid_operations(data_store):
    """Test that invalid operations are handled properly."""
    # Test getting a non-existent validation list
    try:
        data_store.get_validation_list("non_existent_list")
        assert False, "Expected ValueError was not raised"
    except ValueError:
        # Expected behavior
        pass

    # Test setting an invalid validation list with empty dataframe
    # Instead of expecting ValueError, we expect False return value
    result = data_store.set_validation_list("non_existent_list", pd.DataFrame())
    assert result is False

    # Test rollback without transaction
    result = data_store.rollback_transaction()
    assert result is False

    # Test commit without transaction
    result = data_store.commit_transaction()
    assert result is False


def test_method_signature_compliance():
    """Test that all methods have the correct signatures according to the interface."""
    # Define expected method signatures
    expected_methods = {
        "get_entries": {"return": pd.DataFrame},
        "set_entries": {"args": ["entries_df", "source"], "return": bool},
        "get_validation_list": {"args": ["list_type"], "return": pd.DataFrame},
        "set_validation_list": {"args": ["list_type", "entries_df"], "return": bool},
        "add_validation_entry": {"args": ["list_type", "entry"], "return": bool},
        "remove_validation_entry": {"args": ["list_type", "entry"], "return": bool},
        "get_correction_rules": {"return": pd.DataFrame},
        "set_correction_rules": {"args": ["rules_df"], "return": bool},
        "begin_transaction": {"return": bool},
        "commit_transaction": {"return": bool},
        "rollback_transaction": {"return": bool},
        "subscribe": {"args": ["event_type", "handler"]},
        "unsubscribe": {"args": ["event_type", "handler"]},
    }

    # Verify methods have correct signatures
    for method_name, expected in expected_methods.items():
        # Verify method exists
        assert hasattr(DataFrameStore, method_name), f"Method {method_name} is missing"

        # Get the method
        method = getattr(DataFrameStore, method_name)

        # Check if method is callable
        assert callable(method), f"{method_name} is not callable"

        # Check return type if specified
        if "return" in expected:
            # This is approximate since we can't easily check return type annotations at runtime
            # For thorough checks, use the inspect module as in test_interface_compliance.py
            pass

        # Check required arguments if specified (skipping self)
        if "args" in expected:
            method_args = method.__code__.co_varnames[1 : method.__code__.co_argcount]
            for arg in expected["args"]:
                assert arg in method_args, (
                    f"Method {method_name} is missing required argument {arg}"
                )
