"""
test_enhanced_table_view.py

Description: Tests for the EnhancedTableView component
Usage:
    pytest tests/ui/widgets/test_enhanced_table_view.py -v
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os
from typing import List, Dict, Any

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog, QApplication

from tests.ui.helpers.ui_test_helper import UITestHelper
from tests.ui.helpers.mock_services import (
    MockDataStore,
    MockConfigManager,
    MockCorrectionService,
    MockValidationService,
    MockFileService,
    MockServiceFactory,
)

from src.ui.enhanced_table_view import EnhancedTableView, ChestEntryTableModel
from src.models.chest_entry import ChestEntry


@pytest.fixture
def ui_helper(qtbot):
    """
    Create a UITestHelper fixture for tests.

    Args:
        qtbot: The pytest-qt bot for UI interaction

    Returns:
        UITestHelper: Configured UITestHelper instance
    """
    return UITestHelper(qtbot)


@pytest.fixture
def mock_services(ui_helper):
    """
    Create a dictionary of mock services for tests.

    Args:
        ui_helper: The UITestHelper instance

    Returns:
        Dict: Dictionary of mock services
    """
    return ui_helper._create_default_mock_services()


@pytest.fixture
def sample_entries() -> List[Dict[str, Any]]:
    """
    Create sample entries for testing.

    Returns:
        List[Dict[str, Any]]: List of sample entries
    """
    return [
        {
            "id": 1,
            "chest_type": "Gold Chest",
            "player": "Player1",
            "source": "Source1",
            "status": "Valid",
        },
        {
            "id": 2,
            "chest_type": "Silver Chest",
            "player": "Player2",
            "source": "Source2",
            "status": "Invalid",
        },
        {
            "id": 3,
            "chest_type": "Bronze Chest",
            "player": "Player3",
            "source": "Source1",
            "status": "Valid",
        },
        {
            "id": 4,
            "chest_type": "Gold Chest",
            "player": "Player4",
            "source": "Source3",
            "status": "Valid",
        },
        {
            "id": 5,
            "chest_type": "Diamond Chest",
            "player": "Player5",
            "source": "Source2",
            "status": "Invalid",
        },
    ]


@pytest.fixture
def enhanced_table_view(qtbot, mock_services):
    """
    Create an EnhancedTableView fixture for tests.

    Args:
        qtbot: The pytest-qt bot for UI interaction
        mock_services: Dictionary of mock services

    Returns:
        EnhancedTableView: Configured EnhancedTableView instance
    """
    # Create a table view with test_mode enabled
    view = EnhancedTableView(test_mode=True)
    qtbot.addWidget(view)
    return view


@pytest.fixture
def enhanced_table_view_with_data(enhanced_table_view, sample_entries):
    """
    Create an EnhancedTableView with sample data.

    Args:
        enhanced_table_view: EnhancedTableView instance
        sample_entries: Sample entries data

    Returns:
        EnhancedTableView: Configured EnhancedTableView with data
    """
    enhanced_table_view.set_entries(sample_entries)
    return enhanced_table_view


class TestEnhancedTableView:
    """
    Tests for the EnhancedTableView component.
    """

    def test_initialization(self, enhanced_table_view):
        """Test that the view initializes correctly."""
        # Verify the view was created successfully
        assert enhanced_table_view is not None

        # Verify it starts with test mode enabled
        assert enhanced_table_view.is_test_mode() is True

        # Verify it starts with an empty model
        assert enhanced_table_view._entries == []

        # Verify proxy model and selection model exist
        assert enhanced_table_view._proxy_model is not None
        assert enhanced_table_view.selectionModel() is not None

    def test_toggle_test_mode(self, enhanced_table_view):
        """Test setting and getting test mode."""
        # Initially test mode should be enabled (from the fixture)
        assert enhanced_table_view.is_test_mode() is True

        # Disable test mode
        enhanced_table_view.set_test_mode(False)
        assert enhanced_table_view.is_test_mode() is False

        # Re-enable test mode
        enhanced_table_view.set_test_mode(True)
        assert enhanced_table_view.is_test_mode() is True

    def test_set_entries(self, enhanced_table_view, sample_entries):
        """Test setting entries in the table view."""
        # Set entries
        enhanced_table_view.set_entries(sample_entries)

        # Verify entries were set
        assert len(enhanced_table_view._entries) == len(sample_entries)

        # Verify rows in the view
        assert enhanced_table_view._proxy_model.rowCount() == len(sample_entries)

        # Verify data in the first row
        index = enhanced_table_view._proxy_model.index(0, 1)  # Chest Type column
        chest_type = enhanced_table_view._proxy_model.data(index, Qt.DisplayRole)
        assert chest_type == sample_entries[0]["chest_type"]

        # Get model data for verification
        model_data = enhanced_table_view.get_model_data()
        assert len(model_data) == len(sample_entries)
        assert model_data[0]["chest_type"] == sample_entries[0]["chest_type"]

    def test_select_row(self, enhanced_table_view_with_data, sample_entries):
        """Test programmatically selecting a row."""
        # Select row 2
        result = enhanced_table_view_with_data.select_row(2)
        assert result is True

        # Verify selection
        selected_entry = enhanced_table_view_with_data.get_selected_entry()
        assert selected_entry is not None
        assert selected_entry["id"] == sample_entries[2]["id"]

        # Verify signal was emitted
        last_selected = enhanced_table_view_with_data.get_last_selected_entry()
        assert last_selected is not None
        assert last_selected["id"] == sample_entries[2]["id"]

        # Try selecting invalid row
        result = enhanced_table_view_with_data.select_row(10)  # Out of range
        assert result is False

    def test_select_entry_by_id(self, enhanced_table_view_with_data, sample_entries):
        """Test selecting a row by entry ID."""
        # Select entry with ID 3
        result = enhanced_table_view_with_data.select_entry_by_id(3)
        assert result is True

        # Verify selection
        selected_entry = enhanced_table_view_with_data.get_selected_entry()
        assert selected_entry is not None
        assert selected_entry["id"] == 3

        # Try selecting non-existent ID
        result = enhanced_table_view_with_data.select_entry_by_id(100)  # Non-existent
        assert result is False

    def test_filter_entries(self, enhanced_table_view_with_data):
        """Test filtering entries."""
        # Initially all rows should be visible
        assert enhanced_table_view_with_data.get_visible_rows_count() == 5

        # Filter for "Gold"
        enhanced_table_view_with_data.filter_entries("Gold")

        # Verify filtered results
        assert enhanced_table_view_with_data.get_visible_rows_count() == 2  # 2 Gold Chests

        # Filter for a specific player
        enhanced_table_view_with_data.filter_entries("Player1")
        assert enhanced_table_view_with_data.get_visible_rows_count() == 1

        # Clear filter
        enhanced_table_view_with_data.filter_entries("")
        assert enhanced_table_view_with_data.get_visible_rows_count() == 5

    def test_programmatic_actions(self, enhanced_table_view_with_data, qtbot, monkeypatch):
        """Test programmatically triggering context menu actions."""
        # Mock the _edit_entry method to track calls
        edit_called = False
        original_edit = enhanced_table_view_with_data._edit_entry

        def mock_edit_entry(entry):
            nonlocal edit_called
            edit_called = True
            # Call original to ensure signal is emitted
            original_edit(entry)

        monkeypatch.setattr(enhanced_table_view_with_data, "_edit_entry", mock_edit_entry)

        # Mock the _create_rule_from_entry method
        rule_created = False

        def mock_create_rule(entry):
            nonlocal rule_created
            rule_created = True
            # Emit a signal that would normally be emitted
            enhanced_table_view_with_data.entry_edited.emit(entry)

        monkeypatch.setattr(
            enhanced_table_view_with_data, "_create_rule_from_entry", mock_create_rule
        )

        # Mock the _reset_entry method
        reset_called = False

        def mock_reset_entry(entry):
            nonlocal reset_called
            reset_called = True
            # Emit a signal that would normally be emitted
            enhanced_table_view_with_data.entry_edited.emit(entry)

        monkeypatch.setattr(enhanced_table_view_with_data, "_reset_entry", mock_reset_entry)

        # Test edit action
        result = enhanced_table_view_with_data.test_edit_entry_at_row(1)
        assert result is True
        assert edit_called is True

        # Test create rule action
        result = enhanced_table_view_with_data.test_create_rule_from_row(2)
        assert result is True
        assert rule_created is True

        # Test reset entry action
        result = enhanced_table_view_with_data.test_reset_entry_at_row(3)
        assert result is True
        assert reset_called is True

        # Verify signal history
        signal_history = enhanced_table_view_with_data._signal_history
        assert len(signal_history["entry_edited"]) == 2  # From create rule and reset

        # Clear signal history and verify
        enhanced_table_view_with_data.clear_signal_history()
        assert len(enhanced_table_view_with_data._signal_history["entry_edited"]) == 0
        assert len(enhanced_table_view_with_data._signal_history["entry_selected"]) == 0

    def test_highlight_validation_errors(self, enhanced_table_view_with_data, monkeypatch):
        """Test highlighting validation errors."""
        # Mock the setItemDelegate method to verify it's called correctly
        delegate_set = False
        original_set_delegate = enhanced_table_view_with_data.setItemDelegate

        def mock_set_delegate(delegate):
            nonlocal delegate_set
            delegate_set = True
            original_set_delegate(delegate)

        monkeypatch.setattr(enhanced_table_view_with_data, "setItemDelegate", mock_set_delegate)

        # Call highlight_validation_errors in test mode
        enhanced_table_view_with_data.highlight_validation_errors()

        # In test mode, the delegate should not be set
        assert delegate_set is False

        # Disable test mode and try again
        enhanced_table_view_with_data.set_test_mode(False)
        enhanced_table_view_with_data.highlight_validation_errors()

        # Now the delegate should be set
        assert delegate_set is True

    def test_get_visible_rows_count(self, enhanced_table_view_with_data):
        """Test getting the number of visible rows."""
        # Initially all rows should be visible
        assert enhanced_table_view_with_data.get_visible_rows_count() == 5

        # Filter to reduce visible rows
        enhanced_table_view_with_data.filter_entries("Silver")
        assert enhanced_table_view_with_data.get_visible_rows_count() == 1

        # Filter with no matches
        enhanced_table_view_with_data.filter_entries("NonExistentValue")
        assert enhanced_table_view_with_data.get_visible_rows_count() == 0

    def test_model_data_access(self, enhanced_table_view_with_data, sample_entries):
        """Test accessing model data for verification."""
        # Get model data
        model_data = enhanced_table_view_with_data.get_model_data()

        # Verify data matches sample entries
        assert len(model_data) == len(sample_entries)
        for i, entry in enumerate(sample_entries):
            assert model_data[i]["id"] == entry["id"]
            assert model_data[i]["chest_type"] == entry["chest_type"]
            assert model_data[i]["player"] == entry["player"]
            assert model_data[i]["source"] == entry["source"]
            assert model_data[i]["status"] == entry["status"]

    def test_edge_cases(self, enhanced_table_view):
        """Test edge cases and error handling."""
        # Test with empty entries
        enhanced_table_view.set_entries([])
        assert enhanced_table_view.get_visible_rows_count() == 0

        # Test selection on empty table
        result = enhanced_table_view.select_row(0)
        assert result is False

        # Test getting selected entry with no selection
        selected_entry = enhanced_table_view.get_selected_entry()
        assert selected_entry is None

        # Test filter on empty table
        enhanced_table_view.filter_entries("test")
        assert enhanced_table_view.get_visible_rows_count() == 0

        # Test with None as entries
        enhanced_table_view.set_entries(None)
        assert enhanced_table_view._entries == []
