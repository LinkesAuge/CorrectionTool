"""
test_validation_list_search.py

Description: Tests for search functionality in ValidationListWidget
"""

import sys
import pytest
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QItemSelectionModel
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.models.validation_list import ValidationList
from src.ui.validation_list_widget import ValidationListWidget


@pytest.fixture
def app():
    """Fixture to create QApplication."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def validation_list():
    """Fixture to create a ValidationList with sample data."""
    return ValidationList(
        list_type="player",
        entries=[
            "Player1",
            "Player2",
            "AnotherPlayer",
            "SomeOtherPlayer",
            "PlayerSpecial",
            "RandomEntry",
            "UniqueValue",
        ],
        name="Test Players",
    )


@pytest.fixture
def validation_list_widget(app, validation_list):
    """Fixture to create a ValidationListWidget with the test validation list."""
    widget = ValidationListWidget("Test Players")
    widget.set_validation_list(validation_list)
    return widget


def test_search_field_exists(validation_list_widget):
    """Test that the search field exists in the widget."""
    # This test will fail until we implement the search field
    assert hasattr(validation_list_widget, "_search_field")
    assert validation_list_widget._search_field is not None


def test_search_filters_items(validation_list_widget):
    """Test that searching filters the items in the list."""
    # Get the initial row count
    model = validation_list_widget.model()
    initial_count = model.rowCount()
    assert initial_count == 7  # Sanity check based on our test data

    # Enter a search term
    validation_list_widget._search_field.setText("Player")
    validation_list_widget._on_search_changed("Player")

    # Verify that only items containing "Player" are shown
    assert model.rowCount() == 5  # Player1, Player2, AnotherPlayer, SomeOtherPlayer, PlayerSpecial

    # Clear the search
    validation_list_widget._search_field.clear()
    validation_list_widget._on_search_changed("")

    # Verify that all items are shown again
    assert model.rowCount() == initial_count


def test_search_is_case_insensitive(validation_list_widget):
    """Test that the search is case insensitive."""
    model = validation_list_widget.model()

    # Search with lowercase
    validation_list_widget._search_field.setText("player")
    validation_list_widget._on_search_changed("player")

    # Should match all items containing "Player" regardless of case
    assert model.rowCount() == 5

    # Search with mixed case
    validation_list_widget._search_field.setText("pLaYeR")
    validation_list_widget._on_search_changed("pLaYeR")

    # Should still match the same items
    assert model.rowCount() == 5


def test_search_preserves_selection(validation_list_widget):
    """Test that the search preserves the selected item if possible."""
    # Select an item that will remain visible after the search
    model = validation_list_widget.model()
    table_view = validation_list_widget._table_view
    selection_model = table_view.selectionModel()

    # Select "Player1"
    index = model.index(0, 0)  # Assuming Player1 is at index 0
    selection_model.select(index, QItemSelectionModel.SelectCurrent)

    # Perform a search that includes the selected item
    validation_list_widget._search_field.setText("Player")
    validation_list_widget._on_search_changed("Player")

    # Verify the selection is preserved
    assert selection_model.isSelected(model.index(0, 0))

    # Now select an item that will be filtered out
    # Clear the search first
    validation_list_widget._search_field.clear()
    validation_list_widget._on_search_changed("")

    # Select "RandomEntry"
    for i in range(model.rowCount()):
        if model.data(model.index(i, 0)) == "RandomEntry":
            random_index = model.index(i, 0)
            break

    selection_model.select(random_index, QItemSelectionModel.SelectCurrent)

    # Perform a search that excludes the selected item
    validation_list_widget._search_field.setText("Player")
    validation_list_widget._on_search_changed("Player")

    # Verify no selection exists anymore (as the selected item was filtered out)
    assert not selection_model.hasSelection()


def test_search_clear_button(validation_list_widget):
    """Test that the clear button works."""
    # Enter a search term
    validation_list_widget._search_field.setText("Player")
    validation_list_widget._on_search_changed("Player")

    # Verify filtered items are showing
    model = validation_list_widget.model()
    assert model.rowCount() < 7  # Should be filtered (less than all items)

    # Click the clear button
    validation_list_widget._clear_button.click()

    # Verify all items are shown
    assert model.rowCount() == 7
    assert validation_list_widget._search_field.text() == ""
