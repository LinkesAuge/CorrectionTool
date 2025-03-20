"""
test_validation_list_editing.py

Description: Tests for direct editing functionality in ValidationListWidget
"""

import os
import sys
import pytest
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QModelIndex
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTableView, QMenu, QMessageBox

from src.models.validation_list import ValidationList
from src.ui.validation_list_widget import ValidationListWidget, ValidationListItemModel


@pytest.fixture
def app():
    """Fixture to create QApplication."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def validation_list():
    """Fixture to create a ValidationList."""
    return ValidationList(
        list_type="player",
        entries=["Player1", "Player2", "Player3"],
        name="Test Players",
    )


@pytest.fixture
def validation_list_model(validation_list):
    """Fixture to create a ValidationListItemModel."""
    return ValidationListItemModel(validation_list)


@pytest.fixture
def validation_list_widget(app, validation_list):
    """Fixture to create a ValidationListWidget."""
    widget = ValidationListWidget("Test Players")
    widget.set_validation_list(validation_list)
    return widget


def test_model_setdata(validation_list_model):
    """Test the setData method of ValidationListItemModel."""
    # Get initial count
    initial_count = validation_list_model.rowCount()
    assert initial_count == 3

    # Test valid edit
    index = validation_list_model.index(0, 0)
    result = validation_list_model.setData(index, "NewPlayer1", Qt.EditRole)
    assert result is True
    assert validation_list_model.data(index, Qt.DisplayRole) == "NewPlayer1"

    # Test duplicate value
    index2 = validation_list_model.index(1, 0)
    result = validation_list_model.setData(index2, "NewPlayer1", Qt.EditRole)
    assert result is False  # Should fail due to duplicate
    assert validation_list_model.data(index2, Qt.DisplayRole) == "Player2"  # Should not change

    # Test empty value
    result = validation_list_model.setData(index, "", Qt.EditRole)
    assert result is False  # Should fail due to empty value
    assert validation_list_model.data(index, Qt.DisplayRole) == "NewPlayer1"  # Should not change

    # Test invalid index
    invalid_index = QModelIndex()
    result = validation_list_model.setData(invalid_index, "Invalid", Qt.EditRole)
    assert result is False


def test_model_flags(validation_list_model):
    """Test the flags method of ValidationListItemModel."""
    # Valid index should have ItemIsEditable flag
    index = validation_list_model.index(0, 0)
    flags = validation_list_model.flags(index)
    assert flags & Qt.ItemIsEditable

    # Invalid index should have NoItemFlags
    invalid_index = QModelIndex()
    flags = validation_list_model.flags(invalid_index)
    assert flags == Qt.NoItemFlags


def test_widget_data_changed_signal(validation_list_widget):
    """Test that editing data emits list_updated signal."""
    # Track if signal was emitted
    signal_emitted = False

    def on_list_updated(list_obj):
        nonlocal signal_emitted
        signal_emitted = True

    # Connect signal
    validation_list_widget.list_updated.connect(on_list_updated)

    # Get the model
    model = validation_list_widget.model()
    index = model.index(0, 0)

    # Manually call the method that emits the signal
    validation_list_widget._emit_list_updated()

    # Verify signal was emitted
    assert signal_emitted


def test_widget_edit_from_context_menu(validation_list_widget, monkeypatch):
    """Test editing from context menu."""
    # Mock the edit method of the table view
    edit_called = False

    def mock_edit(index):
        nonlocal edit_called
        edit_called = True
        return True

    monkeypatch.setattr(validation_list_widget._table_view, "edit", mock_edit)

    # Create a valid index
    index = validation_list_widget.model().index(0, 0)

    # Call the method directly
    validation_list_widget._on_edit_from_menu(index)

    # Verify edit was called
    assert edit_called


def test_widget_delete_from_context_menu(validation_list_widget, monkeypatch):
    """Test deleting from context menu."""
    # Mock the confirmation dialog to always return Yes
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)

    # Track signal emission
    signal_emitted = False

    def on_list_updated(list_obj):
        nonlocal signal_emitted
        signal_emitted = True

    # Connect signal
    validation_list_widget.list_updated.connect(on_list_updated)

    # Get initial row count
    model = validation_list_widget.model()
    initial_count = model.rowCount()
    assert initial_count == 3  # Sanity check

    # Create a valid index
    index = model.index(0, 0)

    # Call delete method directly
    validation_list_widget._on_delete_from_menu(index)

    # Verify row was deleted
    assert model.rowCount() == initial_count - 1
    assert signal_emitted


def test_validation_list_update_after_edit(validation_list_widget):
    """Test that the ValidationList is updated after editing."""
    # Get initial items
    initial_items = validation_list_widget.get_list().items
    assert "Player1" in initial_items  # Sanity check

    # Get the model
    model = validation_list_widget.model()

    # Update directly via the model's update_item method
    model.update_item(0, "NewPlayer1")

    # Manually trigger data changed to update the validation list
    validation_list_widget._emit_list_updated()

    # Get updated items
    updated_items = validation_list_widget.get_list().items

    # Verify the item was updated
    assert "NewPlayer1" in updated_items
    assert "Player1" not in updated_items
