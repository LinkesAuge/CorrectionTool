"""
test_validation_list_widget.py

Description: Test cases for the ValidationListWidget component
Usage:
    pytest tests/ui/components/test_validation_list_widget.py
"""

import pytest
import pandas as pd
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from typing import List, Dict, Any

from src.ui.validation_list_widget import ValidationListWidget
from tests.ui.helpers.ui_test_helper import UITestHelper
from tests.ui.fixtures.base_test_fixtures import (
    qtbot_fixture,
    default_services,
    sample_validation_list_data,
    setup_validation_lists,
)


class TestValidationListWidget:
    """Test suite for ValidationListWidget."""

    def test_widget_creation(self, qtbot_fixture, default_services):
        """Test that the widget can be created successfully."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget
        widget = helper.create_validation_list_widget(default_services)

        # Check that the widget was created successfully
        assert widget is not None
        assert isinstance(widget, ValidationListWidget)

        # Check initial state
        assert widget.count() == 0  # No items initially
        assert not widget.isVisible()  # Not visible initially

    def test_populate_with_list(self, qtbot_fixture, default_services):
        """Test that the widget can be populated with a list."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget
        widget = helper.create_validation_list_widget(default_services)

        # Create a test list
        test_items = ["Item 1", "Item 2", "Item 3"]

        # Populate the widget
        helper.populate_widget_with_list(widget, test_items)

        # Check that items were added
        assert widget.count() == len(test_items)

        # Verify each item
        for i, item_text in enumerate(test_items):
            assert helper.get_list_item_text(widget, i) == item_text

    def test_set_validation_list(self, qtbot_fixture, default_services):
        """Test the set_validation_list method."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget
        widget = helper.create_validation_list_widget(default_services)

        # Create a test list object
        class TestValidationList:
            def __init__(self, items):
                self._items = items

            def items(self):
                return self._items

        test_list = TestValidationList(["List Item 1", "List Item 2", "List Item 3"])

        # Set the validation list
        widget.set_validation_list(test_list)

        # Check that items were added
        assert widget.count() == 3

        # Verify each item
        for i, item_text in enumerate(test_list.items()):
            assert helper.get_list_item_text(widget, i) == item_text

    def test_set_validation_list_dataframe(self, qtbot_fixture, default_services):
        """Test the set_validation_list method with a DataFrame."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget
        widget = helper.create_validation_list_widget(default_services)

        # Create a test DataFrame
        df = pd.DataFrame({"values": ["DF Item 1", "DF Item 2", "DF Item 3"]})

        # Set the validation list
        widget.set_validation_list(df)

        # Check that items were added
        assert widget.count() == 3

        # Verify each item
        for i, item_text in enumerate(df["values"]):
            assert helper.get_list_item_text(widget, i) == item_text

    def test_add_item(self, qtbot_fixture, default_services):
        """Test adding an item to the widget."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget with some initial items
        widget = helper.create_validation_list_widget(default_services)
        helper.populate_widget_with_list(widget, ["Item 1", "Item 2"])

        # Mock the add_action method to add an item
        def add_action():
            widget._add_item("New Item")

        # Call the add action
        qtbot_fixture.mouseClick(widget._add_button, Qt.LeftButton)
        add_action()

        # Check that the item was added
        assert widget.count() == 3
        assert helper.get_list_item_text(widget, 2) == "New Item"

    def test_edit_item(self, qtbot_fixture, default_services):
        """Test editing an item in the widget."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget with some initial items
        widget = helper.create_validation_list_widget(default_services)
        helper.populate_widget_with_list(widget, ["Item 1", "Item 2", "Item 3"])

        # Select the second item
        widget.setCurrentRow(1)

        # Mock the edit_action method to edit an item
        def edit_action():
            widget._edit_item("Edited Item")

        # Call the edit action
        qtbot_fixture.mouseClick(widget._edit_button, Qt.LeftButton)
        edit_action()

        # Check that the item was edited
        assert widget.count() == 3
        assert helper.get_list_item_text(widget, 1) == "Edited Item"

    def test_delete_item(self, qtbot_fixture, default_services):
        """Test deleting an item from the widget."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget with some initial items
        widget = helper.create_validation_list_widget(default_services)
        helper.populate_widget_with_list(widget, ["Item 1", "Item 2", "Item 3"])

        # Select the second item
        widget.setCurrentRow(1)

        # Mock the delete confirmation dialog
        widget._confirm_delete = lambda: True

        # Click the delete button
        qtbot_fixture.mouseClick(widget._delete_button, Qt.LeftButton)

        # Check that the item was deleted
        assert widget.count() == 2
        assert helper.get_list_item_text(widget, 0) == "Item 1"
        assert helper.get_list_item_text(widget, 1) == "Item 3"

    def test_filter_items(self, qtbot_fixture, default_services):
        """Test filtering items in the widget."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget with some initial items
        widget = helper.create_validation_list_widget(default_services)
        helper.populate_widget_with_list(widget, ["Apple", "Banana", "Cherry", "Date"])

        # Set the filter text
        helper.enter_text(widget._filter_input, "an")

        # Check that only matching items are visible
        visible_items = helper.get_visible_list_items(widget)
        assert len(visible_items) == 2
        assert "Banana" in visible_items
        assert "Date" not in visible_items

    def test_integration_with_data_store(self, qtbot_fixture, setup_validation_lists):
        """Test integration with the data store."""
        # Get services with validation lists set up
        services = setup_validation_lists
        data_store = services["data_store"]

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create widget
        widget = helper.create_validation_list_widget(services)

        # Get a validation list from the data store
        players_list = data_store.get_validation_list("players")

        # Set the validation list in the widget
        widget.set_validation_list(players_list)

        # Check that items were added
        assert widget.count() == len(players_list)

        # Verify each item
        for i, item_text in enumerate(players_list):
            assert helper.get_list_item_text(widget, i) == item_text

        # Add a new item to the widget
        widget.setCurrentRow(-1)  # Deselect any item
        widget._add_item("New Player")

        # Check that the item was added
        assert widget.count() == len(players_list) + 1
        assert helper.get_list_item_text(widget, widget.count() - 1) == "New Player"
