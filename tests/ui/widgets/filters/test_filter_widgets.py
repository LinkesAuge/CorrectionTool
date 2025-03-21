"""
test_filter_widgets.py

Description: Tests for filter UI widgets
"""

import pytest
from unittest.mock import MagicMock, patch

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow

from src.services.filters import ValidationListFilter, TextFilter, FilterManager
from src.ui.widgets.filters import (
    FilterDropdown,
    FilterSearchBar,
    FilterStatusIndicator,
    FilterPanel,
)


@pytest.fixture
def app():
    """Create a Qt application for testing."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def filter_manager():
    """Create a filter manager for testing."""
    return FilterManager()


@pytest.fixture
def data_store():
    """Create a mock data store for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
def validation_filter():
    """Create a validation list filter for testing."""
    return ValidationListFilter("player", "Player Filter", "player")


@pytest.fixture
def text_filter():
    """Create a text filter for testing."""
    return TextFilter("text_search", "Text Search")


@pytest.fixture
def sample_values():
    """Create sample values for testing."""
    return ["Player1", "Player2", "Player3", "PlayerOne", "Player Two"]


class TestFilterDropdown:
    """Tests for FilterDropdown widget."""

    def test_initialization(self, app, validation_filter):
        """Test initialization of FilterDropdown."""
        widget = FilterDropdown(validation_filter, "Test Filter")
        assert widget._filter is validation_filter
        assert widget._title == "Test Filter"
        assert widget._selected_items == set()
        assert widget._expanded is False

        # Verify clear search button is disabled and not visible
        assert hasattr(widget, "_clear_search_button")
        assert widget._clear_search_button is not None
        assert widget._clear_search_button.isEnabled() is False

    def test_set_items(self, app, validation_filter, sample_values):
        """Test setting items in the dropdown."""
        widget = FilterDropdown(validation_filter, "Test Filter")
        widget.set_items(sample_values)

        # Check that all items were added
        assert widget._list_widget.count() == len(sample_values)
        assert widget._all_items == sample_values

    def test_selection(self, app, validation_filter, sample_values):
        """Test selecting items in the dropdown."""
        widget = FilterDropdown(validation_filter, "Test Filter")
        widget.set_items(sample_values)

        # Test programmatic selection
        selected = ["Player1", "Player3"]
        widget.set_selected_values(selected)

        # Check that values were selected
        assert set(widget.get_selected_values()) == set(selected)

        # Check filter was updated
        assert set(validation_filter.selected_values) == set(selected)

    def test_search_functionality(self, app, validation_filter, sample_values):
        """Test the search functionality of FilterDropdown."""
        widget = FilterDropdown(validation_filter, "Test Filter")
        widget.set_items(sample_values)

        # Initially clear button should be disabled
        assert widget._clear_search_button.isEnabled() is False

        # Add search text
        widget._search_edit.setText("Player1")

        # Clear button should be enabled
        assert widget._clear_search_button.isEnabled() is True

        # Filtered items should be correct
        visible_count = 0
        for i in range(widget._list_widget.count()):
            if not widget._list_widget.item(i).isHidden():
                visible_count += 1
                assert "player1" in widget._list_widget.item(i).text().lower()

        assert visible_count > 0

        # Clear search
        widget._clear_search()

        # Clear button should be disabled again
        assert widget._clear_search_button.isEnabled() is False

        # All items should be visible again
        visible_count = 0
        for i in range(widget._list_widget.count()):
            if not widget._list_widget.item(i).isHidden():
                visible_count += 1

        assert visible_count == len(sample_values)


class TestFilterSearchBar:
    """Tests for FilterSearchBar widget."""

    def test_initialization(self, app, text_filter):
        """Test initialization of FilterSearchBar."""
        widget = FilterSearchBar(text_filter)
        assert widget._filter is text_filter
        assert widget._search_edit.text() == ""
        assert hasattr(widget, "_clear_button")
        assert widget._clear_button is not None
        assert widget._clear_button.isEnabled() is False

    def test_search_text(self, app, text_filter):
        """Test setting and getting search text."""
        widget = FilterSearchBar(text_filter)

        # Test setting text
        search_text = "test search"
        widget.set_search_text(search_text)

        # Check that text was set
        assert widget.get_search_text() == search_text
        assert text_filter.search_text == search_text
        assert widget._clear_button.isEnabled() is True

    def test_column_selection(self, app, text_filter):
        """Test column selection functionality."""
        columns = ["Column1", "Column2", "Column3"]
        widget = FilterSearchBar(text_filter, columns)

        # Check that columns were added
        assert widget._column_combo.count() == len(columns) + 1  # +1 for "All Columns"
        assert widget._column_combo is not None
        assert widget._column_combo.isEnabled() is True


class TestFilterStatusIndicator:
    """Tests for FilterStatusIndicator widget."""

    def test_initialization(self, app, filter_manager):
        """Test initialization of FilterStatusIndicator."""
        widget = FilterStatusIndicator(filter_manager)
        assert widget._filter_manager is filter_manager
        assert widget._status_label.text() == "No active filters"
        assert hasattr(widget, "_clear_button")
        assert widget._clear_button is not None
        assert widget._clear_button.isEnabled() is False

    def test_status_update(self, app, filter_manager, text_filter):
        """Test status updates based on active filters."""
        widget = FilterStatusIndicator(filter_manager)

        # Register and activate a filter
        filter_manager.register_filter("text_search", text_filter)
        text_filter.set_search_text("search text")

        # Update status
        widget.update_status()

        # Check that status was updated
        assert widget._status_label.text() == "1 active filter"
        assert widget._clear_button.isEnabled() is True

        # Clear the filter
        text_filter.clear()
        widget.update_status()

        # Check that status was updated
        assert widget._status_label.text() == "No active filters"
        assert widget._clear_button.isEnabled() is False


class TestFilterPanel:
    """Tests for FilterPanel widget."""

    def test_initialization(self, app, filter_manager, data_store):
        """Test initialization of FilterPanel."""
        widget = FilterPanel(filter_manager, data_store)
        assert widget._filter_manager is filter_manager
        assert widget._data_store is data_store
        assert widget._dropdown_filters == {}
        assert widget._date_filters == {}

    def test_add_validation_filter(self, app, filter_manager, data_store, sample_values):
        """Test adding a validation filter to the panel."""
        widget = FilterPanel(filter_manager, data_store)

        # Create filter object
        filter_obj = ValidationListFilter("player", "Player Filter", "player")

        # Add a validation filter
        widget.add_validation_filter("player_filter", filter_obj, "Player")

        # Check that filter was added
        assert "player_filter" in widget._dropdown_filters
        assert filter_manager.get_filter("player_filter") is filter_obj

    def test_update_filter_values(self, app, filter_manager, data_store, sample_values):
        """Test updating filter values."""
        widget = FilterPanel(filter_manager, data_store)

        # Create and add filter
        filter_obj = ValidationListFilter("player", "Player Filter", "player")
        widget.add_validation_filter("player_filter", filter_obj, "Player")

        # Update filter values
        widget.update_filter_values("player_filter", sample_values)

        # Check that values were updated
        dropdown = widget._dropdown_filters["player_filter"]
        assert dropdown.get_items() == sample_values

    def test_clear_all_filters(self, app, filter_manager, data_store, sample_values):
        """Test clearing all filters."""
        widget = FilterPanel(filter_manager, data_store)

        # Create and add filters
        filter_obj = ValidationListFilter("player", "Player Filter", "player")
        widget.add_validation_filter("player_filter", filter_obj, "Player")

        # Set filter value
        dropdown = widget._dropdown_filters["player_filter"]
        dropdown.set_selected_item(sample_values[0])

        # Verify filter is active
        assert filter_obj.is_active() is True

        # Clear all filters
        widget.clear_all_filters()

        # Verify filter is cleared
        assert filter_obj.is_active() is False
