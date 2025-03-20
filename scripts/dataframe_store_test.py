"""
dataframe_store_test.py

Description: Test script for DataFrameStore class
Usage: python dataframe_store_test.py
"""

import threading
import logging
import pandas as pd
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for DataFrameStore."""

    ENTRIES_UPDATED = auto()
    CORRECTION_RULES_UPDATED = auto()
    VALIDATION_LISTS_UPDATED = auto()
    IMPORT_COMPLETED = auto()
    EXPORT_COMPLETED = auto()
    CORRECTION_APPLIED = auto()
    VALIDATION_COMPLETED = auto()
    ERROR_OCCURRED = auto()


class DataFrameStore:
    """
    Singleton class for centralized data management using pandas DataFrames.
    """

    _instance = None
    _instance_lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = DataFrameStore()
        return cls._instance

    def __init__(self):
        """Initialize the DataFrameStore."""
        # Initialize data structures
        self._entries_df = pd.DataFrame()
        self._correction_rules_df = pd.DataFrame()
        self._validation_lists = {}

        # Initialize event handlers
        self._event_handlers = {event_type: [] for event_type in EventType}

        # Initialize transaction state
        self._transaction_active = False
        self._transaction_backup = {}

        # Initialize caches
        self._caches = {}

        # Set up logging
        self._logger = logger
        self._logger.info("DataFrameStore initialized")

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        self._logger.info(f"Handler subscribed to {event_type.name}")

    def _emit_event(self, event_type: EventType, data: Any = None):
        """Emit an event to all subscribers."""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self._logger.error(f"Error in event handler: {e}")
            self._logger.info(
                f"Event {event_type.name} emitted with {len(self._event_handlers[event_type])} subscribers"
            )

    def begin_transaction(self):
        """Begin a transaction."""
        if self._transaction_active:
            self._logger.warning("Transaction already active, ignoring begin_transaction")
            return False

        self._transaction_active = True
        self._transaction_backup = {
            "entries": self._entries_df.copy(),
            "correction_rules": self._correction_rules_df.copy(),
            "validation_lists": {k: v.copy() for k, v in self._validation_lists.items()},
        }
        self._logger.info("Transaction started")
        return True

    def commit_transaction(self):
        """Commit a transaction."""
        if not self._transaction_active:
            self._logger.warning("No active transaction, ignoring commit_transaction")
            return False

        self._transaction_active = False
        self._transaction_backup = {}
        self._logger.info("Transaction committed")
        return True

    def rollback_transaction(self):
        """Roll back a transaction."""
        if not self._transaction_active:
            self._logger.warning("No active transaction, ignoring rollback_transaction")
            return False

        self._entries_df = self._transaction_backup["entries"]
        self._correction_rules_df = self._transaction_backup["correction_rules"]
        self._validation_lists = self._transaction_backup["validation_lists"]

        self._transaction_active = False
        self._transaction_backup = {}
        self._logger.info("Transaction rolled back")
        return True

    def get_entries(self) -> pd.DataFrame:
        """Get the entries DataFrame."""
        return self._entries_df.copy()

    def set_entries(self, df: pd.DataFrame, source: str = None):
        """Set the entries DataFrame."""
        self._entries_df = df.copy()
        self._emit_event(EventType.ENTRIES_UPDATED, {"source": source})
        self._logger.info(f"Set {len(df)} entries")

    def get_correction_rules(self) -> pd.DataFrame:
        """Get the correction rules DataFrame."""
        return self._correction_rules_df.copy()

    def set_correction_rules(self, df: pd.DataFrame):
        """Set the correction rules DataFrame."""
        self._correction_rules_df = df.copy()
        self._emit_event(EventType.CORRECTION_RULES_UPDATED, {})
        self._logger.info(f"Set {len(df)} correction rules")

    def get_validation_list(self, list_type: str) -> pd.DataFrame:
        """Get a validation list DataFrame."""
        if list_type in self._validation_lists:
            return self._validation_lists[list_type].copy()
        return pd.DataFrame({"value": []})

    def set_validation_list(self, list_type: str, df: pd.DataFrame):
        """Set a validation list DataFrame."""
        self._validation_lists[list_type] = df.copy()
        self._emit_event(EventType.VALIDATION_LISTS_UPDATED, {"list_type": list_type})
        self._logger.info(f"Set validation list '{list_type}' with {len(df)} items")

    def get_entry_statistics(self) -> Dict[str, Any]:
        """Get statistics about the entries."""
        stats = {"total": len(self._entries_df), "valid": 0, "invalid": 0, "pending": 0}

        if not self._entries_df.empty and "status" in self._entries_df.columns:
            status_counts = self._entries_df["status"].value_counts().to_dict()
            stats["valid"] = status_counts.get("Valid", 0)
            stats["invalid"] = status_counts.get("Invalid", 0)
            stats["pending"] = status_counts.get("Pending", 0)

        return stats

    def clear_cache(self, cache_name: Optional[str] = None):
        """Clear the cache."""
        if cache_name:
            if cache_name in self._caches:
                del self._caches[cache_name]
                self._logger.info(f"Cache '{cache_name}' cleared")
        else:
            self._caches.clear()
            self._logger.info("All caches cleared")


def test_dataframe_store():
    """Test the DataFrameStore class."""
    logger.info("Starting DataFrameStore test")

    # Get the singleton instance
    store = DataFrameStore.get_instance()

    # Subscribe to events
    events_received = []

    def handle_entries_updated(data):
        events_received.append(("ENTRIES_UPDATED", data))
        logger.info(f"Entries updated event received: {data}")

    def handle_correction_rules_updated(data):
        events_received.append(("CORRECTION_RULES_UPDATED", data))
        logger.info("Correction rules updated event received")

    def handle_validation_lists_updated(data):
        events_received.append(("VALIDATION_LISTS_UPDATED", data))
        logger.info(f"Validation list updated event received: {data}")

    # Subscribe to events
    store.subscribe(EventType.ENTRIES_UPDATED, handle_entries_updated)
    store.subscribe(EventType.CORRECTION_RULES_UPDATED, handle_correction_rules_updated)
    store.subscribe(EventType.VALIDATION_LISTS_UPDATED, handle_validation_lists_updated)

    # Test set_entries
    entries_data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "chest_type": ["Gold", "Silver", "Bronze"],
        "player": ["Player1", "Player2", "Player3"],
        "source": ["Source1", "Source2", "Source3"],
        "status": ["Pending", "Pending", "Pending"],
    }
    entries_df = pd.DataFrame(entries_data)

    store.set_entries(entries_df, "test")

    # Test get_entries
    retrieved_entries = store.get_entries()
    assert len(retrieved_entries) == 3, "Retrieved entries count mismatch"
    logger.info("get_entries test passed")

    # Test set_correction_rules
    rules_data = {
        "from_text": ["Silver", "Gold"],
        "to_text": ["Silver Chest", "Gold Chest"],
        "category": ["chest_type", "chest_type"],
        "enabled": [True, True],
    }
    rules_df = pd.DataFrame(rules_data)

    store.set_correction_rules(rules_df)

    # Test get_correction_rules
    retrieved_rules = store.get_correction_rules()
    assert len(retrieved_rules) == 2, "Retrieved rules count mismatch"
    logger.info("get_correction_rules test passed")

    # Test set_validation_list
    chest_types_data = {"value": ["Gold", "Silver", "Bronze", "Platinum"]}
    chest_types_df = pd.DataFrame(chest_types_data)

    store.set_validation_list("chest_types", chest_types_df)

    # Test get_validation_list
    retrieved_list = store.get_validation_list("chest_types")
    assert len(retrieved_list) == 4, "Retrieved validation list count mismatch"
    logger.info("get_validation_list test passed")

    # Test transaction support
    store.begin_transaction()

    # Modify data within transaction
    new_entries_data = {
        "date": ["2023-01-04", "2023-01-05"],
        "chest_type": ["Diamond", "Emerald"],
        "player": ["Player4", "Player5"],
        "source": ["Source4", "Source5"],
        "status": ["Pending", "Pending"],
    }
    new_entries_df = pd.DataFrame(new_entries_data)

    store.set_entries(new_entries_df, "transaction_test")

    # Check that changes are reflected
    assert len(store.get_entries()) == 2, "Transaction entries count mismatch"

    # Rollback the transaction
    store.rollback_transaction()

    # Check that changes were reverted
    assert len(store.get_entries()) == 3, "Rolled back entries count mismatch"
    logger.info("Transaction rollback test passed")

    # Begin a new transaction
    store.begin_transaction()

    # Modify data again
    store.set_entries(new_entries_df, "transaction_test_2")

    # Commit the transaction
    store.commit_transaction()

    # Check that changes were committed
    assert len(store.get_entries()) == 2, "Committed entries count mismatch"
    logger.info("Transaction commit test passed")

    # Test get_entry_statistics
    stats = store.get_entry_statistics()
    assert stats["total"] == 2, "Statistics total count mismatch"
    assert stats["pending"] == 2, "Statistics pending count mismatch"
    logger.info("get_entry_statistics test passed")

    # Check that events were received
    assert len(events_received) >= 5, "Events received count mismatch"
    logger.info(f"Received {len(events_received)} events as expected")

    logger.info("All DataFrameStore tests passed!")


if __name__ == "__main__":
    test_dataframe_store()
