"""
test_drag_drop_manager.py

Description: Tests for the DragDropManager class
Usage:
    pytest tests/test_drag_drop_manager.py
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
import pandas as pd
from typing import Dict, List, Any

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QWidget, QTableView

from src.ui.helpers.drag_drop_manager import DragDropManager
from src.interfaces.i_data_store import IDataStore
from src.interfaces.events import EventType, EventHandler
from src.ui.validation_list_widget import ValidationListWidget
from src.ui.correction_rules_table import CorrectionRulesTable


class MockDataStore(IDataStore):
    """Mock implementation of IDataStore for testing."""

    def __init__(self):
        self.entries = pd.DataFrame(columns=["chest_type", "player", "source"])
        self.correction_rules = []
        self.validation_lists = {
            "player": ["Player1", "Player2"],
            "chest_type": ["Chest1", "Chest2"],
            "source": ["Source1", "Source2"],
        }
        self.subscribers = {}

    def get_entries(self) -> pd.DataFrame:
        return self.entries

    def set_entries(self, entries_df: pd.DataFrame, source: str = "") -> bool:
        self.entries = entries_df
        return True

    def get_validation_list(self, list_type: str) -> pd.DataFrame:
        items = self.validation_lists.get(list_type, [])
        return pd.DataFrame(items, columns=["name"])

    def set_validation_list(self, list_type: str, entries_df: pd.DataFrame) -> bool:
        self.validation_lists[list_type] = entries_df["name"].tolist()
        return True

    def add_validation_entry(self, list_type: str, entry: str) -> bool:
        if list_type not in self.validation_lists:
            self.validation_lists[list_type] = []
        if entry not in self.validation_lists[list_type]:
            self.validation_lists[list_type].append(entry)
            return True
        return False

    def remove_validation_entry(self, list_type: str, entry: str) -> bool:
        if list_type in self.validation_lists and entry in self.validation_lists[list_type]:
            self.validation_lists[list_type].remove(entry)
            return True
        return False

    def get_correction_rules(self) -> pd.DataFrame:
        return pd.DataFrame(self.correction_rules)

    def set_correction_rules(self, rules_df: pd.DataFrame) -> bool:
        self.correction_rules = rules_df.to_dict("records") if not rules_df.empty else []
        return True

    def begin_transaction(self) -> bool:
        return True

    def commit_transaction(self) -> bool:
        return True

    def rollback_transaction(self) -> bool:
        return True

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type in self.subscribers and handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)


@pytest.fixture
def app():
    """QApplication instance needed for Qt widgets."""
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    return app


@pytest.fixture
def mock_data_store():
    """Fixture that provides a mock data store."""
    return MockDataStore()


@pytest.fixture
def drag_drop_manager(app, mock_data_store):
    """Fixture that provides a DragDropManager instance."""
    return DragDropManager(mock_data_store)


class TestDragDropManager:
    """Tests for the DragDropManager class."""

    def test_initialization(self, drag_drop_manager, mock_data_store):
        """Test that the manager initializes correctly."""
        assert drag_drop_manager._data_store == mock_data_store
        assert isinstance(drag_drop_manager._adapters, list)
        assert len(drag_drop_manager._adapters) == 0

    def test_setup_drag_drop(self, drag_drop_manager):
        """Test setting up drag and drop with validation lists and correction rules."""
        # Create mock widgets
        validation_lists = {}
        for list_type in ["player", "chest_type", "source"]:
            mock_list_widget = MagicMock(spec=ValidationListWidget)
            mock_list_widget._table_view = MagicMock(spec=QTableView)
            validation_lists[list_type] = mock_list_widget

        correction_rules_table = MagicMock(spec=CorrectionRulesTable)
        correction_rules_table._table_view = MagicMock(spec=QTableView)

        # Call the method
        drag_drop_manager.setup_drag_drop(validation_lists, correction_rules_table)

        # Verify that adapters were created for each widget
        assert (
            len(drag_drop_manager._adapters) >= len(validation_lists) + 1
        )  # +1 for correction rules

        # Check for cleanup on re-setup
        drag_drop_manager.setup_drag_drop(validation_lists, correction_rules_table)
        assert len(drag_drop_manager._adapters) >= len(validation_lists) + 1

    def test_cleanup(self, drag_drop_manager):
        """Test cleanup method."""
        # Setup adapters
        mock_adapter1 = MagicMock()
        mock_adapter2 = MagicMock()
        drag_drop_manager._adapters = [mock_adapter1, mock_adapter2]

        # Call the method
        drag_drop_manager.cleanup()

        # Verify adapters were cleaned up
        mock_adapter1.disconnect.assert_called_once()
        mock_adapter2.disconnect.assert_called_once()
        assert len(drag_drop_manager._adapters) == 0


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
