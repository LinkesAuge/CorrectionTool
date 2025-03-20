"""
test_drag_drop_adapters.py

Description: Tests for the drag and drop adapter classes
Usage:
    pytest tests/test_drag_drop_adapters.py
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from typing import List, Dict, Any

from PySide6.QtCore import QEvent, QMimeData, QPoint, Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QTableView, QApplication, QWidget

from src.ui.validation_list_widget import ValidationListWidget
from src.ui.correction_rules_table import CorrectionRulesTable
from src.ui.adapters.validation_list_drag_drop_adapter import (
    ValidationListDragDropAdapter,
    VALIDATION_ITEM_MIME_TYPE,
)
from src.ui.adapters.correction_rules_drag_drop_adapter import CorrectionRulesDragDropAdapter
from src.interfaces.i_data_store import IDataStore


class MockDataStore(IDataStore):
    """Mock implementation of IDataStore for testing."""

    def __init__(self):
        self.entries = pd.DataFrame(columns=["chest_type", "player", "source"])
        self.correction_rules = pd.DataFrame(
            columns=["from_text", "to_text", "category", "enabled"]
        )
        self.validation_lists = {
            "player": ["Player1", "Player2"],
            "chest_type": ["Chest1", "Chest2"],
            "source": ["Source1", "Source2"],
        }
        self.subscribers = {}

    # Implement required methods from IDataStore
    def set_entries(self, entries):
        self.entries = entries
        return True

    def get_entries(self):
        return self.entries

    def get_correction_rules(self):
        return self.correction_rules

    def update_correction_rules(self, rules):
        self.correction_rules = pd.DataFrame(rules)
        return True

    def get_validation_list(self, list_type):
        return self.validation_lists.get(list_type, [])

    def update_validation_list(self, list_type, items):
        self.validation_lists[list_type] = items
        return True

    def subscribe(self, event_type, handler):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        return True

    def unsubscribe(self, event_type, handler):
        if event_type in self.subscribers and handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
        return True

    def begin_transaction(self):
        return True

    def commit_transaction(self):
        return True

    def rollback_transaction(self):
        return True


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
def mock_data_store():
    """Fixture that provides a mock data store."""
    return MockDataStore()


@pytest.fixture
def mock_validation_list_widget():
    """Fixture that provides a mock validation list widget."""
    widget = MagicMock(spec=ValidationListWidget)
    widget._table_view = MagicMock(spec=QTableView)
    widget.get_items.return_value = ["Item1", "Item2"]
    widget.add_item = MagicMock()
    return widget


@pytest.fixture
def mock_correction_rules_table():
    """Fixture that provides a mock correction rules table."""
    table = MagicMock(spec=CorrectionRulesTable)
    table.add_rule = MagicMock()
    table.get_rules = MagicMock(return_value=[])
    return table


@pytest.fixture
def validation_list_adapter(mock_validation_list_widget, mock_data_store):
    """Fixture that provides a ValidationListDragDropAdapter instance."""
    adapter = ValidationListDragDropAdapter(mock_validation_list_widget, mock_data_store, "player")
    return adapter


@pytest.fixture
def correction_rules_adapter(mock_correction_rules_table, mock_data_store):
    """Fixture that provides a CorrectionRulesDragDropAdapter instance."""
    adapter = CorrectionRulesDragDropAdapter(mock_correction_rules_table, mock_data_store)
    return adapter


class TestValidationListDragDropAdapter:
    """Tests for the ValidationListDragDropAdapter class."""

    def test_initialization(self, validation_list_adapter, mock_validation_list_widget):
        """Test that the adapter initializes correctly."""
        assert validation_list_adapter._widget == mock_validation_list_widget
        assert validation_list_adapter._list_type == "player"
        assert validation_list_adapter._table_view == mock_validation_list_widget._table_view

    def test_connect(self, validation_list_adapter):
        """Test that connect method sets up the table view correctly."""
        validation_list_adapter.connect()

        # Verify that drag and drop is enabled
        validation_list_adapter._table_view.setDragEnabled.assert_called_once_with(True)
        validation_list_adapter._table_view.setAcceptDrops.assert_called_once_with(True)
        validation_list_adapter._table_view.setDragDropMode.assert_called_once()

        # Verify that event filter is installed
        validation_list_adapter._table_view.installEventFilter.assert_called_once_with(
            validation_list_adapter
        )

    def test_disconnect(self, validation_list_adapter):
        """Test that disconnect method cleans up the table view correctly."""
        validation_list_adapter.disconnect()

        # Verify that drag and drop is disabled
        validation_list_adapter._table_view.setDragEnabled.assert_called_once_with(False)
        validation_list_adapter._table_view.setAcceptDrops.assert_called_once_with(False)
        validation_list_adapter._table_view.setDragDropMode.assert_called_once()

        # Verify that event filter is removed
        validation_list_adapter._table_view.removeEventFilter.assert_called_once_with(
            validation_list_adapter
        )

    def test_event_filter_wrong_watched(self, validation_list_adapter):
        """Test that event filter returns False for events from other widgets."""
        other_widget = MagicMock(spec=QWidget)
        event = MockDragEnterEvent()

        result = validation_list_adapter.eventFilter(other_widget, event)

        assert result is False

    def test_handle_drag_enter_valid(self, validation_list_adapter):
        """Test handling a valid drag enter event."""
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"test_item")
        event = MockDragEnterEvent(mime_data)

        result = validation_list_adapter._handle_drag_enter(event)

        assert result is True
        assert event.accepted is True

    def test_handle_drag_enter_invalid(self, validation_list_adapter):
        """Test handling an invalid drag enter event."""
        mime_data = QMimeData()  # No data set
        event = MockDragEnterEvent(mime_data)

        result = validation_list_adapter._handle_drag_enter(event)

        assert result is False
        assert event.accepted is False

    def test_handle_drag_move_valid(self, validation_list_adapter):
        """Test handling a valid drag move event."""
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"test_item")
        event = MockDragMoveEvent(mime_data)

        result = validation_list_adapter._handle_drag_move(event)

        assert result is True
        assert event.accepted is True

    def test_handle_drag_move_invalid(self, validation_list_adapter):
        """Test handling an invalid drag move event."""
        mime_data = QMimeData()  # No data set
        event = MockDragMoveEvent(mime_data)

        result = validation_list_adapter._handle_drag_move(event)

        assert result is False
        assert event.accepted is False

    def test_handle_drop_new_item(self, validation_list_adapter, mock_data_store):
        """Test handling a drop event with a new item."""
        # Set up the mime data
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"NewItem")
        event = MockDropEvent(mime_data, QPoint(10, 10))

        # Set up the mock index at operation
        validation_list_adapter._table_view.indexAt.return_value = MagicMock()

        # Ensure the item is not in the current items
        mock_items = ["Item1", "Item2"]
        validation_list_adapter._widget.get_items.return_value = mock_items

        # Call the method
        result = validation_list_adapter._handle_drop(event)

        # Verify the results
        assert result is True
        assert event.accepted is True
        validation_list_adapter._widget.add_item.assert_called_once_with("NewItem")
        validation_list_adapter._widget.get_items.assert_called()
        mock_data_store.update_validation_list.assert_called_once()

    def test_handle_drop_existing_item(self, validation_list_adapter, mock_data_store):
        """Test handling a drop event with an existing item."""
        # Set up the mime data with an existing item
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"Item1")
        event = MockDropEvent(mime_data, QPoint(10, 10))

        # Set up the mock index at operation
        validation_list_adapter._table_view.indexAt.return_value = MagicMock()

        # The item is already in the current items
        validation_list_adapter._widget.get_items.return_value = ["Item1", "Item2"]

        # Call the method
        result = validation_list_adapter._handle_drop(event)

        # Verify the results
        assert result is True
        assert event.accepted is True
        validation_list_adapter._widget.add_item.assert_not_called()
        mock_data_store.update_validation_list.assert_not_called()

    def test_can_accept_drop(self, validation_list_adapter):
        """Test the can_accept_drop method."""
        # Valid mime data
        mime_data1 = QMimeData()
        mime_data1.setData(VALIDATION_ITEM_MIME_TYPE, b"test_item")
        assert validation_list_adapter.can_accept_drop(mime_data1) is True

        # Invalid mime data
        mime_data2 = QMimeData()
        assert validation_list_adapter.can_accept_drop(mime_data2) is False


class TestCorrectionRulesDragDropAdapter:
    """Tests for the CorrectionRulesDragDropAdapter class."""

    def test_initialization(self, correction_rules_adapter, mock_correction_rules_table):
        """Test that the adapter initializes correctly."""
        assert correction_rules_adapter._widget == mock_correction_rules_table
        assert correction_rules_adapter._table == mock_correction_rules_table

    def test_connect(self, correction_rules_adapter):
        """Test that connect method sets up the table correctly."""
        correction_rules_adapter.connect()

        # Verify that drag and drop is enabled
        correction_rules_adapter._table.setAcceptDrops.assert_called_once_with(True)
        correction_rules_adapter._table.setDragDropMode.assert_called_once()

        # Verify that event filter is installed
        correction_rules_adapter._table.installEventFilter.assert_called_once_with(
            correction_rules_adapter
        )

    def test_disconnect(self, correction_rules_adapter):
        """Test that disconnect method cleans up the table correctly."""
        correction_rules_adapter.disconnect()

        # Verify that drag and drop is disabled
        correction_rules_adapter._table.setAcceptDrops.assert_called_once_with(False)
        correction_rules_adapter._table.setDragDropMode.assert_called_once()

        # Verify that event filter is removed
        correction_rules_adapter._table.removeEventFilter.assert_called_once_with(
            correction_rules_adapter
        )

    def test_event_filter_wrong_watched(self, correction_rules_adapter):
        """Test that event filter returns False for events from other widgets."""
        other_widget = MagicMock(spec=QWidget)
        event = MockDragEnterEvent()

        result = correction_rules_adapter.eventFilter(other_widget, event)

        assert result is False

    def test_handle_drag_enter_valid(self, correction_rules_adapter):
        """Test handling a valid drag enter event."""
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"test_item")
        event = MockDragEnterEvent(mime_data)

        result = correction_rules_adapter._handle_drag_enter(event)

        assert result is True
        assert event.accepted is True

    def test_handle_drag_enter_invalid(self, correction_rules_adapter):
        """Test handling an invalid drag enter event."""
        mime_data = QMimeData()  # No data set
        event = MockDragEnterEvent(mime_data)

        result = correction_rules_adapter._handle_drag_enter(event)

        assert result is False
        assert event.accepted is False

    def test_handle_drag_move_valid(self, correction_rules_adapter):
        """Test handling a valid drag move event."""
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"test_item")
        event = MockDragMoveEvent(mime_data)

        result = correction_rules_adapter._handle_drag_move(event)

        assert result is True
        assert event.accepted is True

    def test_handle_drag_move_invalid(self, correction_rules_adapter):
        """Test handling an invalid drag move event."""
        mime_data = QMimeData()  # No data set
        event = MockDragMoveEvent(mime_data)

        result = correction_rules_adapter._handle_drag_move(event)

        assert result is False
        assert event.accepted is False

    def test_handle_drop_create_rule(self, correction_rules_adapter, mock_data_store):
        """Test handling a drop event to create a new rule."""
        # Set up the mime data
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"NewItem")
        event = MockDropEvent(mime_data)

        # Set up the mock return values
        correction_rules_adapter._widget.get_rules.return_value = []

        # Call the method
        result = correction_rules_adapter._handle_drop(event)

        # Verify the results
        assert result is True
        assert event.accepted is True

        # Verify that a new rule was created
        new_rule = {"from_text": "", "to_text": "NewItem", "enabled": True}
        correction_rules_adapter._widget.add_rule.assert_called_once_with(new_rule)
        correction_rules_adapter._widget.get_rules.assert_called_once()
        mock_data_store.update_correction_rules.assert_called_once()

    def test_can_accept_drop(self, correction_rules_adapter):
        """Test the can_accept_drop method."""
        # Valid mime data
        mime_data1 = QMimeData()
        mime_data1.setData(VALIDATION_ITEM_MIME_TYPE, b"test_item")
        assert correction_rules_adapter.can_accept_drop(mime_data1) is True

        # Invalid mime data
        mime_data2 = QMimeData()
        assert correction_rules_adapter.can_accept_drop(mime_data2) is False


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
