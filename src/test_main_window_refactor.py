"""
test_main_window_refactor.py

Description: Test script for the refactored MainWindow
Usage:
    python -m src.test_main_window_refactor
"""

import sys
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import PySide6
from PySide6.QtWidgets import QApplication

# Import pandas and needed modules directly to avoid circular imports
import pandas as pd
import threading
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
import functools


# Recreate minimal versions of needed classes to avoid import errors
class EventType(Enum):
    """Event types for the DataFrameStore event system."""

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

    This is a standalone test version to avoid circular imports.
    """

    # Singleton instance
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
        self._validation_lists = {
            "chest_types": pd.DataFrame({"value": []}),
            "players": pd.DataFrame({"value": []}),
            "sources": pd.DataFrame({"value": []}),
        }

        # Initialize event handlers
        self._event_handlers = {event_type: [] for event_type in EventType}

        # Initialize transaction state
        self._transaction_active = False
        self._transaction_backup = {}

        # Initialize caches
        self._caches = {}

        # Set up logging
        self._logger = logging.getLogger(__name__ + ".DataFrameStore")
        self._logger.info("DataFrameStore initialized")

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def _emit_event(self, event_type: EventType, data: Any = None):
        """Emit an event to all subscribers."""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self._logger.error(f"Error in event handler: {e}")

    def get_entries(self) -> pd.DataFrame:
        """Get the entries DataFrame."""
        return self._entries_df.copy()

    def set_entries(self, df: pd.DataFrame, source: str = None):
        """Set the entries DataFrame."""
        self._entries_df = df.copy()
        self._emit_event(EventType.ENTRIES_UPDATED, {"source": source})

    def get_correction_rules(self) -> pd.DataFrame:
        """Get the correction rules DataFrame."""
        return self._correction_rules_df.copy()

    def set_correction_rules(self, df: pd.DataFrame):
        """Set the correction rules DataFrame."""
        self._correction_rules_df = df.copy()
        self._emit_event(EventType.CORRECTION_RULES_UPDATED, {})

    def get_validation_list(self, list_type: str) -> pd.DataFrame:
        """Get a validation list DataFrame."""
        if list_type in self._validation_lists:
            return self._validation_lists[list_type].copy()
        return pd.DataFrame({"value": []})

    def set_validation_list(self, list_type: str, df: pd.DataFrame):
        """Set a validation list DataFrame."""
        self._validation_lists[list_type] = df.copy()
        self._emit_event(EventType.VALIDATION_LISTS_UPDATED, {"list_type": list_type})

    def get_entry_statistics(self) -> Dict[str, Any]:
        """Get statistics about the entries."""
        return {
            "total": len(self._entries_df),
            "valid": len(self._entries_df[self._entries_df["status"] == "Valid"]),
            "invalid": len(self._entries_df[self._entries_df["status"] == "Invalid"]),
            "pending": len(self._entries_df[self._entries_df["status"] == "Pending"]),
        }


class ServiceFactory:
    """Factory for creating and accessing services."""

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = ServiceFactory()
        return cls._instance

    def __init__(self):
        """Initialize the ServiceFactory."""
        self._services = {}
        self._logger = logging.getLogger(__name__ + ".ServiceFactory")

    def get_dataframe_store(self):
        """Get the DataFrameStore instance."""
        return DataFrameStore.get_instance()

    def get_file_service(self):
        """Get the FileService instance."""
        # For testing purposes, return a mock service
        return MockFileService()

    def get_correction_service(self):
        """Get the CorrectionService instance."""
        # For testing purposes, return a mock service
        return MockCorrectionService()

    def get_validation_service(self):
        """Get the ValidationService instance."""
        # For testing purposes, return a mock service
        return MockValidationService()

    def initialize_all_services(self):
        """Initialize all services."""
        self.get_dataframe_store()
        self.get_file_service()
        self.get_correction_service()
        self.get_validation_service()
        self._logger.info("All services initialized")

    def get_entry_table_adapter(self, table_view):
        """Get an EntryTableAdapter for a table view."""
        # For testing purposes, return a mock adapter
        return MockEntryTableAdapter(table_view)

    def get_correction_rule_table_adapter(self, table_widget):
        """Get a CorrectionRuleTableAdapter for a table widget."""
        # For testing purposes, return a mock adapter
        return MockCorrectionRuleTableAdapter(table_widget)

    def get_validation_list_combo_adapter(self, combo_box, list_type):
        """Get a ValidationListComboAdapter for a combo box."""
        # For testing purposes, return a mock adapter
        return MockValidationListComboAdapter(combo_box, list_type)


# Mock service classes for testing
class MockFileService:
    """Mock FileService for testing."""

    def load_entries_from_file(self, file_path):
        logger.info(f"Mock FileService: Loading entries from {file_path}")
        return 3

    def save_entries_to_file(self, file_path):
        logger.info(f"Mock FileService: Saving entries to {file_path}")
        return 3


class MockCorrectionService:
    """Mock CorrectionService for testing."""

    def apply_corrections(self, specific_entries=None):
        logger.info("Mock CorrectionService: Applying corrections")
        return 2

    def add_correction_rule(self, from_text, to_text, category="general"):
        logger.info(f"Mock CorrectionService: Adding rule {from_text} -> {to_text}")
        return 1


class MockValidationService:
    """Mock ValidationService for testing."""

    def validate_entries(self, specific_entries=None):
        logger.info("Mock ValidationService: Validating entries")
        return {"valid": 2, "invalid": 1, "total": 3}

    def add_to_validation_list(self, list_type, value):
        logger.info(f"Mock ValidationService: Adding {value} to {list_type}")
        return True


# Mock adapter classes for testing
class MockEntryTableAdapter:
    """Mock EntryTableAdapter for testing."""

    def __init__(self, table_view):
        self.table_view = table_view
        logger.info("Mock EntryTableAdapter: Created")

    def connect(self):
        logger.info("Mock EntryTableAdapter: Connected")

    def refresh(self):
        logger.info("Mock EntryTableAdapter: Refreshed")


class MockCorrectionRuleTableAdapter:
    """Mock CorrectionRuleTableAdapter for testing."""

    def __init__(self, table_widget):
        self.table_widget = table_widget
        logger.info("Mock CorrectionRuleTableAdapter: Created")

    def connect(self):
        logger.info("Mock CorrectionRuleTableAdapter: Connected")

    def refresh(self):
        logger.info("Mock CorrectionRuleTableAdapter: Refreshed")


class MockValidationListComboAdapter:
    """Mock ValidationListComboAdapter for testing."""

    def __init__(self, combo_box, list_type):
        self.combo_box = combo_box
        self.list_type = list_type
        logger.info(f"Mock ValidationListComboAdapter: Created for {list_type}")

    def connect(self):
        logger.info("Mock ValidationListComboAdapter: Connected")

    def refresh(self):
        logger.info("Mock ValidationListComboAdapter: Refreshed")


def setup_test_data():
    """Set up test data in the DataFrameStore."""
    logger.info("Setting up test data in DataFrameStore")

    # Get the DataFrameStore instance
    store = DataFrameStore.get_instance()

    # Create some test entries
    entries_data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "chest_type": ["Gold", "Silver", "Bronze"],
        "player": ["Player1", "Player2", "Player3"],
        "source": ["Source1", "Source2", "Source3"],
        "status": ["Pending", "Pending", "Pending"],
        "validation_errors": [[], [], []],
        "original_values": [{}, {}, {}],
    }

    entries_df = pd.DataFrame(entries_data)

    # Create validation lists
    chest_types_data = {"value": ["Gold", "Silver", "Bronze", "Platinum"]}
    player_names_data = {"value": ["Player1", "Player2", "Player3", "Player4"]}
    sources_data = {"value": ["Source1", "Source2", "Source3", "Source4"]}

    # Create DataFrames with the correct column name
    chest_types_df = pd.DataFrame(chest_types_data)
    player_names_df = pd.DataFrame(player_names_data)
    sources_df = pd.DataFrame(sources_data)

    # Create correction rules
    rules_data = {
        "from_text": ["Silver", "Gold"],
        "to_text": ["Silver Chest", "Gold Chest"],
        "category": ["chest_type", "chest_type"],
        "enabled": [True, True],
        "timestamp": [pd.Timestamp.now(), pd.Timestamp.now()],
    }

    rules_df = pd.DataFrame(rules_data)

    # Set data in the DataFrameStore
    store.set_entries(entries_df)
    store.set_validation_list("chest_types", chest_types_df)
    store.set_validation_list("players", player_names_df)
    store.set_validation_list("sources", sources_df)
    store.set_correction_rules(rules_df)

    logger.info("Test data setup completed")


# Now we can directly import our refactored MainWindow class
# without risking circular imports
from src.ui.main_window_refactor import MainWindow


def main():
    """Main test function."""
    # Create the application
    app = QApplication(sys.argv)

    # Setup data first
    setup_test_data()

    # Create and show the main window
    main_window = MainWindow()
    main_window.show()

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
