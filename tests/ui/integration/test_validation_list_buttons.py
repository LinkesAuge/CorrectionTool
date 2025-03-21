"""
test_validation_list_buttons.py

Description: Integration tests for ValidationListWidget button functionality
Usage:
    pytest tests/ui/integration/test_validation_list_buttons.py
"""

import pytest
import os
import tempfile
from pathlib import Path
import pandas as pd
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QInputDialog, QFileDialog
from PySide6.QtCore import Qt
from typing import List, Dict, Any, Callable

from src.ui.validation_list_widget import ValidationListWidget
from tests.ui.helpers.ui_test_helper import UITestHelper
from tests.ui.fixtures.base_test_fixtures import (
    qtbot_fixture,
    default_services,
    sample_validation_list_data,
    setup_validation_lists,
)


class TestValidationListButtons:
    """Integration test suite for ValidationListWidget buttons."""

    def test_add_button(self, qtbot_fixture, default_services, monkeypatch):
        """Test the add button functionality."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget
        widget = helper.create_validation_list_widget(default_services)

        # Mock the QInputDialog.getText method to return a new item
        def mock_get_text(*args, **kwargs):
            return "New Test Item", True

        monkeypatch.setattr(QInputDialog, "getText", mock_get_text)

        # Initial count
        initial_count = widget.count()

        # Click the add button
        qtbot_fixture.mouseClick(widget._add_button, Qt.LeftButton)

        # Verify item was added
        assert widget.count() == initial_count + 1
        assert helper.get_list_item_text(widget, widget.count() - 1) == "New Test Item"

    def test_edit_button(self, qtbot_fixture, default_services, monkeypatch):
        """Test the edit button functionality."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget with items
        widget = helper.create_validation_list_widget(default_services)
        helper.populate_widget_with_list(widget, ["Item 1", "Item to Edit", "Item 3"])

        # Select the item to edit
        widget.setCurrentRow(1)

        # Mock the QInputDialog.getText method to return the edited item
        def mock_get_text(*args, **kwargs):
            return "Edited Item", True

        monkeypatch.setattr(QInputDialog, "getText", mock_get_text)

        # Click the edit button
        qtbot_fixture.mouseClick(widget._edit_button, Qt.LeftButton)

        # Verify item was edited
        assert widget.count() == 3
        assert helper.get_list_item_text(widget, 1) == "Edited Item"

    def test_delete_button(self, qtbot_fixture, default_services, monkeypatch):
        """Test the delete button functionality."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget with items
        widget = helper.create_validation_list_widget(default_services)
        helper.populate_widget_with_list(widget, ["Item 1", "Item to Delete", "Item 3"])

        # Select the item to delete
        widget.setCurrentRow(1)

        # Mock the QMessageBox.question method to return QMessageBox.Yes
        def mock_question(*args, **kwargs):
            return QMessageBox.Yes

        monkeypatch.setattr(QMessageBox, "question", mock_question)

        # Click the delete button
        qtbot_fixture.mouseClick(widget._delete_button, Qt.LeftButton)

        # Verify item was deleted
        assert widget.count() == 2
        assert helper.get_list_item_text(widget, 0) == "Item 1"
        assert helper.get_list_item_text(widget, 1) == "Item 3"

    def test_import_button(self, qtbot_fixture, default_services, monkeypatch, tmp_path):
        """Test the import button functionality."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget
        widget = helper.create_validation_list_widget(default_services)

        # Create a temporary CSV file with items
        temp_file = tmp_path / "test_import.csv"
        test_data = pd.DataFrame(
            {"values": ["Imported Item 1", "Imported Item 2", "Imported Item 3"]}
        )
        test_data.to_csv(temp_file, index=False)

        # Mock the QFileDialog.getOpenFileName method to return the temp file
        def mock_get_open_filename(*args, **kwargs):
            return str(temp_file), "CSV Files (*.csv)"

        monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_get_open_filename)

        # Set the mock file in the file service
        file_service = default_services["file_service"]
        file_service.set_mock_file(str(temp_file), test_data)

        # Initial count
        initial_count = widget.count()

        # Click the import button
        qtbot_fixture.mouseClick(widget._import_button, Qt.LeftButton)

        # Verify items were imported
        assert widget.count() > initial_count
        assert file_service.get_imported_files()[-1] == str(temp_file)

    def test_export_button(self, qtbot_fixture, default_services, monkeypatch, tmp_path):
        """Test the export button functionality."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget with items
        widget = helper.create_validation_list_widget(default_services)
        helper.populate_widget_with_list(
            widget, ["Export Item 1", "Export Item 2", "Export Item 3"]
        )

        # Create a temporary file path for export
        temp_file = tmp_path / "test_export.csv"

        # Mock the QFileDialog.getSaveFileName method to return the temp file
        def mock_get_save_filename(*args, **kwargs):
            return str(temp_file), "CSV Files (*.csv)"

        monkeypatch.setattr(QFileDialog, "getSaveFileName", mock_get_save_filename)

        # Click the export button
        qtbot_fixture.mouseClick(widget._export_button, Qt.LeftButton)

        # Verify export was attempted
        file_service = default_services["file_service"]
        assert file_service.get_exported_files()[-1] == str(temp_file)

    def test_filter_functionality(self, qtbot_fixture, default_services):
        """Test the filter functionality."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget with items
        widget = helper.create_validation_list_widget(default_services)
        helper.populate_widget_with_list(
            widget, ["Alpha Item", "Beta Item", "Alpha Beta", "Gamma Item", "Delta Beta"]
        )

        # Initial count - all items visible
        assert helper.count_visible_items(widget) == 5

        # Set filter text
        helper.enter_text(widget._filter_input, "Beta")

        # Verify filtering
        visible_items = helper.get_visible_list_items(widget)
        assert len(visible_items) == 3
        assert "Beta Item" in visible_items
        assert "Alpha Beta" in visible_items
        assert "Delta Beta" in visible_items
        assert "Alpha Item" not in visible_items

        # Clear filter
        helper.enter_text(widget._filter_input, "")

        # Verify all items visible again
        assert helper.count_visible_items(widget) == 5

    def test_button_states(self, qtbot_fixture, default_services):
        """Test the button enable/disable states based on selection."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget with items
        widget = helper.create_validation_list_widget(default_services)
        helper.populate_widget_with_list(widget, ["Item 1", "Item 2", "Item 3"])

        # Initially no selection
        widget.setCurrentRow(-1)

        # Add button should be enabled regardless of selection
        assert widget._add_button.isEnabled()

        # Edit and delete buttons should be disabled without selection
        assert not widget._edit_button.isEnabled()
        assert not widget._delete_button.isEnabled()

        # Select an item
        widget.setCurrentRow(1)

        # Edit and delete buttons should now be enabled
        assert widget._edit_button.isEnabled()
        assert widget._delete_button.isEnabled()

    def test_integration_with_data_store(self, qtbot_fixture, setup_validation_lists, monkeypatch):
        """Test integration with the data store for button operations."""
        # Get services with validation lists set up
        services = setup_validation_lists
        data_store = services["data_store"]

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget
        widget = helper.create_validation_list_widget(services)

        # Get a validation list from the data store
        original_list = data_store.get_validation_list("players")

        # Set the validation list in the widget
        widget.set_validation_list(original_list)
        widget._list_name = "players"  # Set list name for update operations

        # Record initial event count
        initial_events = len(data_store.get_triggered_events())

        # Mock the QInputDialog.getText method to return a new item
        def mock_get_text(*args, **kwargs):
            return "New Player Via Button", True

        monkeypatch.setattr(QInputDialog, "getText", mock_get_text)

        # Click the add button
        qtbot_fixture.mouseClick(widget._add_button, Qt.LeftButton)

        # Verify the data store was updated
        updated_list = data_store.get_validation_list("players")
        assert "New Player Via Button" in updated_list

        # Verify an event was triggered
        triggered_events = data_store.get_triggered_events()
        assert len(triggered_events) > initial_events

        # Check for the VALIDATION_LIST_UPDATED event
        assert any(
            event_type.name == "VALIDATION_LIST_UPDATED" and data.get("list_name") == "players"
            for event_type, data in triggered_events[initial_events:]
        )
