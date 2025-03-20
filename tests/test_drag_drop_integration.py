"""
test_drag_drop_integration.py

Description: Integration tests for the drag and drop functionality
Usage:
    pytest tests/test_drag_drop_integration.py
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
import pandas as pd
from typing import Dict, List, Any

from PySide6.QtCore import QEvent, QMimeData, QPoint, Qt, QObject
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QApplication, QWidget, QTableView

from src.ui.helpers.drag_drop_manager import DragDropManager
from src.ui.validation_list_widget import ValidationListWidget
from src.ui.correction_rules_table import CorrectionRulesTable
from src.ui.adapters.validation_list_drag_drop_adapter import (
    ValidationListDragDropAdapter,
    VALIDATION_ITEM_MIME_TYPE,
)
from src.ui.adapters.correction_rules_drag_drop_adapter import CorrectionRulesDragDropAdapter
from src.services.dataframe_store import DataFrameStore
from src.interfaces.i_data_store import IDataStore
from src.interfaces.events import EventType, EventHandler


class MockDataStore(IDataStore):
    """Mock implementation of IDataStore for integration testing."""

    def __init__(self):
        self.entries = pd.DataFrame(columns=["chest_type", "player", "source"])
        self.correction_rules = []
        self.validation_lists = {
            "player": ["Player1", "Player2"],
            "chest_type": ["Chest1", "Chest2"],
            "source": ["Source1", "Source2"],
        }
        self.subscribers = {}
        self.updated_validation_list = None
        self.updated_validation_items = None
        self.updated_correction_rules = None

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
        self.updated_validation_list = list_type
        self.updated_validation_items = entries_df["name"].tolist()
        return True

    def add_validation_entry(self, list_type: str, entry: str) -> bool:
        if list_type not in self.validation_lists:
            self.validation_lists[list_type] = []
        if entry not in self.validation_lists[list_type]:
            self.validation_lists[list_type].append(entry)
            self.updated_validation_list = list_type
            self.updated_validation_items = self.validation_lists[list_type]
            return True
        return False

    def remove_validation_entry(self, list_type: str, entry: str) -> bool:
        if list_type in self.validation_lists and entry in self.validation_lists[list_type]:
            self.validation_lists[list_type].remove(entry)
            self.updated_validation_list = list_type
            self.updated_validation_items = self.validation_lists[list_type]
            return True
        return False

    def get_correction_rules(self) -> pd.DataFrame:
        return pd.DataFrame(self.correction_rules)

    def set_correction_rules(self, rules_df: pd.DataFrame) -> bool:
        self.correction_rules = rules_df.to_dict("records") if not rules_df.empty else []
        self.updated_correction_rules = self.correction_rules
        return True

    def update_correction_rules(self, rules: list) -> bool:
        """Update correction rules in the data store."""
        self.correction_rules = rules
        self.updated_correction_rules = rules
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
    """Mock ValidationListWidget for integration testing."""

    def __init__(self):
        super().__init__()
        self._table_view = MagicMock(spec=QTableView)
        self._items = ["Player1", "Player2", "Player3"]

    def get_items(self):
        return self._items.copy()

    def add_item(self, item):
        if item not in self._items:
            self._items.append(item)
            return True
        return False


class MockCorrectionRulesTable(QObject):
    """Mock CorrectionRulesTable for integration testing."""

    def __init__(self):
        super().__init__()
        self._table_view = MagicMock(spec=QTableView)
        self._rules = []

        # Add methods that are used directly on the table
        self.setAcceptDrops = MagicMock()
        self.setDragDropMode = MagicMock()
        self.installEventFilter = MagicMock()
        self.removeEventFilter = MagicMock()
        self.viewport = MagicMock(return_value=MagicMock())
        self.indexAt = MagicMock(return_value=MagicMock())

    def add_rule(self, rule):
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
def validation_list_widget():
    """Fixture that provides a mock validation list widget."""
    return MockValidationListWidget()


@pytest.fixture
def correction_rules_table():
    """Fixture that provides a mock correction rules table."""
    return MockCorrectionRulesTable()


@pytest.fixture
def drag_drop_manager(data_store):
    """Fixture that provides a DragDropManager instance."""
    return DragDropManager(data_store)


@pytest.fixture
def validation_list_adapter(validation_list_widget, data_store):
    """Fixture that provides a ValidationListDragDropAdapter instance."""
    adapter = ValidationListDragDropAdapter(validation_list_widget, data_store, "player")
    return adapter


@pytest.fixture
def correction_rules_adapter(correction_rules_table, data_store):
    """Fixture that provides a CorrectionRulesDragDropAdapter instance."""
    adapter = CorrectionRulesDragDropAdapter(correction_rules_table, data_store)
    return adapter


@pytest.fixture
def integrated_drag_drop_system(
    app, data_store, validation_list_widget, correction_rules_table, drag_drop_manager
):
    """Fixture that provides a fully integrated drag-drop system."""
    validation_lists = {"player": validation_list_widget}

    # Set up drag-drop system
    drag_drop_manager.setup_drag_drop(validation_lists, correction_rules_table)

    return {
        "manager": drag_drop_manager,
        "data_store": data_store,
        "validation_list_widget": validation_list_widget,
        "correction_rules_table": correction_rules_table,
    }


class TestDragDropIntegration:
    """Integration tests for the drag and drop functionality."""

    def test_drag_from_validation_list_to_correction_rules(self, integrated_drag_drop_system):
        """Test dragging an item from a validation list to the correction rules table."""
        system = integrated_drag_drop_system

        # Find the adapters in the system
        validation_adapter = None
        correction_adapter = None

        for adapter in system["manager"]._adapters:
            if isinstance(adapter, ValidationListDragDropAdapter):
                validation_adapter = adapter
            elif isinstance(adapter, CorrectionRulesDragDropAdapter):
                correction_adapter = adapter

        assert validation_adapter is not None, "ValidationListDragDropAdapter not found in system"
        assert correction_adapter is not None, "CorrectionRulesDragDropAdapter not found in system"

        # Create a mime data object with a validation item
        mime_data = QMimeData()
        test_item = "Player1"
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, test_item.encode())

        # Simulate a drop event on the correction rules table
        drop_event = MockDropEvent(mime_data, QPoint(10, 10))

        # Mock the indexAt method to return a valid index
        correction_adapter._table.indexAt = MagicMock(return_value=MagicMock())

        # Handle the drop event
        result = correction_adapter._handle_drop(drop_event)

        # Verify the results
        assert result is True, "Drop event handling failed"
        assert drop_event.accepted is True, "Drop event was not accepted"

        # Check that the correction rule was created correctly
        assert len(system["correction_rules_table"]._rules) == 1, "Rule was not added to the table"

        # Verify the rule data
        rule = system["correction_rules_table"]._rules[0]
        assert rule["from_text"] == "", "From text is not empty"
        assert rule["to_text"] == "Player1", "To text does not match dragged item"
        assert rule["enabled"] is True, "Rule is not enabled"

        # Verify the data store was updated
        assert system["data_store"].updated_correction_rules is not None, (
            "Data store was not updated"
        )
        assert len(system["data_store"].updated_correction_rules) == 1, (
            "Data store does not have the new rule"
        )

    def test_integration_cleanup(self, integrated_drag_drop_system):
        """Test that the drag-drop system cleans up properly."""
        system = integrated_drag_drop_system

        # Verify that adapters exist
        assert len(system["manager"]._adapters) > 0, "No adapters were created"

        # Clean up the system
        system["manager"].cleanup()

        # Verify that adapters were removed
        assert len(system["manager"]._adapters) == 0, "Adapters were not removed"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
