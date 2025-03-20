"""
test_validation_list_drag_drop_adapter.py

Description: Tests for the ValidationListDragDropAdapter class
Usage:
    pytest tests/test_validation_list_drag_drop_adapter.py
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
import pandas as pd
from typing import Dict, List, Any

from PySide6.QtCore import QEvent, QMimeData, QPoint, Qt, QObject, QPointF
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QWidget, QTableView, QAbstractItemView

from src.ui.adapters.validation_list_drag_drop_adapter import (
    ValidationListDragDropAdapter,
    VALIDATION_ITEM_MIME_TYPE,
)
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
        self.updated_list_type = None
        self.updated_items = None
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
        self.updated_list_type = list_type
        self.updated_items = entries_df["name"].tolist()
        return True

    def add_validation_entry(self, list_type: str, entry: str) -> bool:
        if list_type not in self.validation_lists:
            self.validation_lists[list_type] = []
        if entry not in self.validation_lists[list_type]:
            self.validation_lists[list_type].append(entry)
            self.updated_list_type = list_type
            self.updated_items = self.validation_lists[list_type]
            return True
        return False

    def remove_validation_entry(self, list_type: str, entry: str) -> bool:
        if list_type in self.validation_lists and entry in self.validation_lists[list_type]:
            self.validation_lists[list_type].remove(entry)
            self.updated_list_type = list_type
            self.updated_items = self.validation_lists[list_type]
            return True
        return False

    def update_validation_list(self, list_type: str, items: list) -> bool:
        """Update a validation list with new items."""
        self.validation_lists[list_type] = items
        self.updated_list_type = list_type
        self.updated_items = items
        return True

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


class MockValidationListWidget(QObject):
    """Mock ValidationListWidget for testing."""

    def __init__(self):
        super().__init__()
        # Create a mock table view with the necessary methods
        self._table_view = MagicMock(spec=QTableView)

        # Set up viewport
        viewport_mock = MagicMock()
        self._table_view.viewport.return_value = viewport_mock

        self._items = ["Player1", "Player2", "Player3"]

        # Set up the model mock
        model_mock = MagicMock()
        model_mock.index = MagicMock(return_value=MagicMock())
        model_mock.data = MagicMock(return_value="Player1")
        self._table_view.model = MagicMock(return_value=model_mock)

        # Set up selection model
        selection_model_mock = MagicMock()
        selection_model_mock.selectedIndexes = MagicMock(return_value=[MagicMock()])
        self._table_view.selectionModel = MagicMock(return_value=selection_model_mock)

    def get_items(self):
        return self._items.copy()

    def add_item(self, item):
        if item not in self._items:
            self._items.append(item)
            return True
        return False


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
        # Return a QPointF that can be converted to a QPoint
        return QPointF(self.pos.x(), self.pos.y())


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
def validation_list_widget():
    """Fixture that provides a mock validation list widget."""
    return MockValidationListWidget()


@pytest.fixture
def adapter(app, validation_list_widget, data_store):
    """Fixture that provides a ValidationListDragDropAdapter instance."""
    adapter = ValidationListDragDropAdapter(validation_list_widget, data_store, "player")
    adapter.connect()
    return adapter


class TestValidationListDragDropAdapter:
    """Tests for the ValidationListDragDropAdapter class."""

    def test_initialization(self, adapter, validation_list_widget):
        """Test that the adapter initializes correctly."""
        assert adapter._widget == validation_list_widget
        assert adapter._list_type == "player"
        assert adapter._table_view == validation_list_widget._table_view

    def test_connect(self, adapter, validation_list_widget):
        """Test that the adapter connects correctly."""
        # Re-connect to ensure the method is called
        adapter.connect()

        # Verify that the table view was configured correctly
        validation_list_widget._table_view.setDragEnabled.assert_called_with(True)
        validation_list_widget._table_view.setDragDropMode.assert_called_with(
            QAbstractItemView.DragDrop
        )
        validation_list_widget._table_view.setAcceptDrops.assert_called_with(True)

    def test_handle_dragenter_valid(self, adapter):
        """Test that the adapter handles drag enter events correctly with valid mime data."""
        # Create a mime data object with the correct format
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"Player4")

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

    def test_handle_drop_valid(self, adapter, data_store):
        """Test that the adapter handles drop events correctly with valid mime data."""
        # Create a mime data object with the correct format
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"Player4")

        # Create a drop event
        event = MockDropEvent(mime_data)

        # Add indexAt method to the table
        adapter._table_view.indexAt = MagicMock(return_value=MagicMock())

        # Call the method
        result = adapter._handle_drop(event)

        # Verify the results
        assert result is True
        assert event.accepted is True

        # Verify that the item was added to the validation list
        assert "Player4" in data_store.validation_lists["player"]
        assert data_store.updated_list_type == "player"
        assert "Player4" in data_store.updated_items

    def test_handle_drop_duplicate(self, adapter, data_store):
        """Test that the adapter handles drop events with duplicate items correctly."""
        # Create a mime data object with an existing item
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, b"Player1")  # Player1 already exists

        # Create a drop event
        event = MockDropEvent(mime_data)

        # Call the method
        result = adapter._handle_drop(event)

        # Verify the results
        assert result is True
        assert event.accepted is True

        # Verify that the item wasn't added again (no duplicates)
        assert data_store.validation_lists["player"].count("Player1") == 1

    def test_disconnect(self, adapter, validation_list_widget):
        """Test that the adapter disconnects correctly."""
        # Record initial event filter state
        viewport = validation_list_widget._table_view.viewport()

        # Call disconnect method
        adapter.disconnect()

        # Verify that the table view was configured correctly
        validation_list_widget._table_view.setDragEnabled.assert_called_with(False)
        validation_list_widget._table_view.setDragDropMode.assert_called_with(
            QAbstractItemView.NoDragDrop
        )
        validation_list_widget._table_view.setAcceptDrops.assert_called_with(False)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
