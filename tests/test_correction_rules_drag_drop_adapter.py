"""
test_correction_rules_drag_drop_adapter.py

Description: Tests for the CorrectionRulesDragDropAdapter class
Usage:
    pytest tests/test_correction_rules_drag_drop_adapter.py
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
import pandas as pd
from typing import Dict, List, Any

from PySide6.QtCore import QEvent, QMimeData, QPoint, Qt, QObject, QModelIndex
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QWidget, QTableView, QAbstractItemView

from src.ui.adapters.correction_rules_drag_drop_adapter import CorrectionRulesDragDropAdapter
from src.ui.adapters.validation_list_drag_drop_adapter import VALIDATION_ITEM_MIME_TYPE
from src.interfaces.i_data_store import IDataStore
from src.interfaces.events import EventType, EventHandler


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
        self.updated_rules = None
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
        self.updated_rules = self.correction_rules
        return True

    def update_correction_rules(self, rules: list) -> bool:
        """Update correction rules in the data store."""
        self.correction_rules = rules
        self.updated_rules = rules
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


class MockCorrectionRulesTable(QObject):
    """Mock CorrectionRulesTable for testing."""

    def __init__(self):
        super().__init__()
        self._table_view = MagicMock(spec=QTableView)
        self._table_view.setAcceptDrops = MagicMock()
        self._table_view.setDragDropMode = MagicMock()
        self._table_view.installEventFilter = MagicMock()
        self._table_view.removeEventFilter = MagicMock()
        self._table_view.viewport = MagicMock(return_value=MagicMock())
        self._table_view.indexAt = MagicMock(return_value=QModelIndex())

        # Add methods that are used directly on the table
        self.setAcceptDrops = self._table_view.setAcceptDrops
        self.setDragDropMode = self._table_view.setDragDropMode
        self.installEventFilter = self._table_view.installEventFilter
        self.removeEventFilter = self._table_view.removeEventFilter
        self.indexAt = MagicMock(return_value=MagicMock())

        self._rules = []
        self.add_rule_called = False
        self.add_rule_args = None

    def add_rule(self, rule):
        self.add_rule_called = True
        self.add_rule_args = rule
        self._rules.append(rule)
        return True

    def get_rules(self):
        return self._rules.copy()


class MockEvent:
    """Base class for mock drag and drop events."""

    def __init__(self, mime_data=None):
        self.accepted = False
        self._mime_data = mime_data or QMimeData()

    def mimeData(self):
        return self._mime_data

    def acceptProposedAction(self):
        self.accepted = True


class MockDragEnterEvent(MockEvent):
    def type(self):
        return QEvent.DragEnter


class MockDragMoveEvent(MockEvent):
    def type(self):
        return QEvent.DragMove


class MockDropEvent(MockEvent):
    def __init__(self, mime_data=None, pos=None):
        super().__init__(mime_data)
        self.pos = pos or QPoint(0, 0)

    def type(self):
        return QEvent.Drop

    def position(self):
        return self.pos


@pytest.fixture
def app():
    """QApplication instance needed for Qt widgets."""
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    return app


@pytest.fixture
def data_store():
    """Fixture that provides a mock data store."""
    return MockDataStore()


@pytest.fixture
def correction_rules_table():
    """Fixture that provides a mock correction rules table."""
    return MockCorrectionRulesTable()


@pytest.fixture
def adapter(app, correction_rules_table, data_store):
    """Fixture that provides a CorrectionRulesDragDropAdapter instance."""
    return CorrectionRulesDragDropAdapter(correction_rules_table, data_store)


class TestCorrectionRulesDragDropAdapter:
    """Tests for the CorrectionRulesDragDropAdapter class."""

    def test_initialization(self, adapter, correction_rules_table):
        """Test that the adapter initializes correctly."""
        assert adapter._widget == correction_rules_table
        assert adapter._table == correction_rules_table

        # Verify that the table view was configured correctly when connect() is called
        adapter.connect()
        correction_rules_table._table_view.setAcceptDrops.assert_called_once_with(True)

    def test_handle_dragenter_valid(self, adapter):
        """Test that the adapter handles drag enter events correctly with valid mime data."""
        # Create a mime data object with the correct format
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"Player1")

        # Create a drag enter event
        event = MockDragEnterEvent(mime_data)

        # Call the method
        result = adapter._handle_drag_enter(event)

        # Verify the results
        assert result is True
        assert event.accepted is True

    def test_handle_dragenter_invalid(self, adapter):
        """Test that the adapter rejects drag enter events with invalid mime data."""
        # Create a mime data object with an incorrect format
        mime_data = QMimeData()
        mime_data.setText("This is not a validation item")

        # Create a drag enter event
        event = MockDragEnterEvent(mime_data)

        # Call the method
        result = adapter._handle_drag_enter(event)

        # Verify the results
        assert result is False
        assert event.accepted is False

    def test_handle_drop_valid(self, adapter, correction_rules_table, data_store):
        """Test that the adapter handles drop events correctly with valid mime data."""
        # Create a mime data object with the correct format
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"Player1")

        # Create a drop event
        event = MockDropEvent(mime_data)

        # Call the method
        result = adapter._handle_drop(event)

        # Verify the results
        assert result is True
        assert event.accepted is True

        # Verify that a new rule was added
        assert correction_rules_table.add_rule_called is True

        # Verify the rule data
        rule = correction_rules_table.add_rule_args
        assert rule is not None
        assert rule.get("to_text") == "Player1"
        assert rule.get("from_text") == ""
        assert rule.get("enabled") is True

        # Verify the data store was updated
        assert data_store.updated_rules is not None

    def test_handle_drop_to_existing_rule(self, adapter, correction_rules_table, data_store):
        """Test that the adapter handles drop events correctly when dropping onto an existing rule."""
        # Setup an existing rule
        existing_rule = {"id": 1, "from_text": "Old", "to_text": "Player1", "enabled": True}
        correction_rules_table._rules = [existing_rule]
        data_store.correction_rules = [existing_rule]

        # Setup the adapter to find a valid index
        adapter._table.indexAt = MagicMock(return_value=MagicMock())
        adapter._table.indexAt.return_value.row.return_value = 0

        # Create a mime data object with the correct format
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"Player2")

        # Create a drop event
        event = MockDropEvent(mime_data)

        # Call the method
        result = adapter._handle_drop(event)

        # Verify the results
        assert result is True
        assert event.accepted is True

        # Verify that the rule was updated or a new one added
        assert correction_rules_table.add_rule_called is True

    def test_disconnect(self, adapter, correction_rules_table):
        """Test that the adapter disconnects correctly."""
        # Connect first
        adapter.connect()

        # Then disconnect
        adapter.disconnect()

        # Verify that the table view was configured correctly
        correction_rules_table._table_view.setAcceptDrops.assert_called_with(False)
        correction_rules_table._table_view.setDragDropMode.assert_called_with(
            QAbstractItemView.NoDragDrop
        )


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
