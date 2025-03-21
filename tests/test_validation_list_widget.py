"""
test_validation_list_widget.py

Description: Tests for the ValidationListWidget class.
Usage:
    pytest tests/test_validation_list_widget.py
"""

import sys
import os
import logging
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication, QTableView, QMessageBox
from PySide6.QtCore import Qt

# Add the source directory to the path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.validation_list_widget import ValidationListWidget
from src.models.validation_list import ValidationList


@pytest.fixture
def app():
    """Fixture for the QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Clean up after tests
    app.quit()


@pytest.fixture
def validation_list_widget(app):
    """Fixture for creating a ValidationListWidget instance."""
    widget = ValidationListWidget("player")
    yield widget
    # Clean up
    widget.deleteLater()


def test_validation_list_widget_initialization(validation_list_widget):
    """Test that ValidationListWidget initializes correctly."""
    assert validation_list_widget is not None
    assert validation_list_widget._list_name == "player"
    assert validation_list_widget._validation_list is not None
    assert validation_list_widget._model is not None


def test_validation_list_widget_has_table_view(validation_list_widget):
    """Test that ValidationListWidget has a table view."""
    assert hasattr(validation_list_widget, "_table_view")
    assert isinstance(validation_list_widget._table_view, QTableView)


def test_validation_list_widget_set_validation_list(validation_list_widget):
    """Test that ValidationListWidget has a set_validation_list method that works properly."""
    # Create a test ValidationList
    test_list = ValidationList(name="player")
    test_list.items = ["Player1", "Player2", "Player3"]

    # Check that the method exists
    assert hasattr(validation_list_widget, "set_validation_list")

    # Use the method
    validation_list_widget.set_validation_list(test_list)

    # Verify the list was set
    model = validation_list_widget.model()
    assert model.rowCount() == 3


def test_validation_list_widget_set_list(validation_list_widget):
    """Test that ValidationListWidget has a set_list method that works properly."""
    # Create a test ValidationList
    test_list = ValidationList(name="player")
    test_list.items = ["Player1", "Player2", "Player3"]

    # Check that the method exists
    assert hasattr(validation_list_widget, "set_list")

    # Use the method
    result = validation_list_widget.set_list(test_list)

    # Verify method returns True
    assert result is True

    # Verify the list was set
    model = validation_list_widget._filtered_model
    assert model.rowCount() == 3
    assert model.data(model.index(0, 0)) == "Player1"
    assert model.data(model.index(1, 0)) == "Player2"
    assert model.data(model.index(2, 0)) == "Player3"

    # Verify the actual list object was stored
    assert validation_list_widget._list is test_list


def test_validation_list_widget_get_items(validation_list_widget):
    """Test that ValidationListWidget can return items."""
    # Set up some test items
    test_list = ValidationList(name="player")
    test_list.items = ["Player1", "Player2", "Player3"]
    validation_list_widget.set_list(test_list)

    # Check if get_items method exists and works
    assert hasattr(validation_list_widget, "get_items")
    items = validation_list_widget.get_items()
    assert len(items) == 3
    assert "Player1" in items
    assert "Player2" in items
    assert "Player3" in items


def test_validation_list_widget_add_item(validation_list_widget):
    """Test that ValidationListWidget can add items."""
    # Check if add_item method exists
    assert hasattr(validation_list_widget, "add_item")

    # Add some items
    validation_list_widget.add_item("Player1")
    validation_list_widget.add_item("Player2")

    # Verify items were added
    items = validation_list_widget.get_items()
    assert len(items) == 2
    assert "Player1" in items
    assert "Player2" in items


def test_validation_list_widget_delete_item(validation_list_widget):
    """Test that ValidationListWidget can delete items."""
    # Set up some test items
    validation_list_widget.add_item("Player1")
    validation_list_widget.add_item("Player2")
    validation_list_widget.add_item("Player3")

    # Check if delete_item or similar method exists
    has_delete_method = (
        hasattr(validation_list_widget, "delete_item")
        or hasattr(validation_list_widget, "remove_item")
        or hasattr(validation_list_widget, "_on_delete")
    )
    assert has_delete_method

    # Delete an item directly using delete_item
    if hasattr(validation_list_widget, "delete_item"):
        validation_list_widget.delete_item("Player1")

        # Verify item was deleted
        items = validation_list_widget.get_items()
        assert len(items) == 2
        assert "Player1" not in items
    # If _on_delete exists we can try to test that instead
    elif hasattr(validation_list_widget, "_on_delete"):
        # Mock the selection
        mock_selection = MagicMock()
        mock_selection.selectedIndexes.return_value = [validation_list_widget._model.index(0, 0)]
        mock_selection.hasSelection.return_value = True
        validation_list_widget._table_view.selectionModel = MagicMock(return_value=mock_selection)

        # Replace the QMessageBox with a mock
        original_qmessagebox = QMessageBox
        QMessageBox.question = MagicMock(return_value=QMessageBox.Yes)

        try:
            # Call the delete method
            validation_list_widget._on_delete()

            # Verify item was deleted
            items = validation_list_widget.get_items()
            assert len(items) == 2
            assert "Player1" not in items
        finally:
            # Restore original QMessageBox
            QMessageBox = original_qmessagebox


def test_validation_list_widget_has_required_attributes(validation_list_widget):
    """Test that ValidationListWidget has all required attributes for drag-drop adapters."""
    # Check for _table_view, which is used by the drag-drop adapter
    assert hasattr(validation_list_widget, "_table_view")

    # Check for methods used in the adapter
    assert hasattr(validation_list_widget, "get_items")
    assert hasattr(validation_list_widget, "add_item")

    # Check for the model method
    assert hasattr(validation_list_widget, "model")


def test_validation_list_widget_emits_signals(validation_list_widget):
    """Test that ValidationListWidget emits signals when changed."""
    # Check if the widget has the expected signal
    assert hasattr(validation_list_widget, "list_updated")

    # Create a signal spy
    signal_received = False

    def on_list_updated(data):
        nonlocal signal_received
        signal_received = True

    # Connect to the signal
    validation_list_widget.list_updated.connect(on_list_updated)

    # Modify the list
    validation_list_widget.add_item("TestPlayer")

    # Check if the signal was emitted
    assert signal_received
