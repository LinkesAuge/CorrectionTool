"""
test_i_filter.py

Description: Tests for IFilter and IFilterManager interfaces
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from src.interfaces.i_filter import IFilter, IFilterManager
from src.services.filters.validation_list_filter import ValidationListFilter
from src.services.filters.text_filter import TextFilter
from src.services.filters.filter_manager import FilterManager


class TestIFilterInterface:
    """Tests for IFilter interface implementation."""

    def test_validation_list_filter_implements_interface(self):
        """Test that ValidationListFilter implements IFilter interface."""
        filter_obj = ValidationListFilter("test", "Test Filter", "column")

        # Check that the object is an instance of IFilter
        assert isinstance(filter_obj, IFilter)

        # Verify required methods and properties
        assert hasattr(filter_obj, "filter_id")
        assert hasattr(filter_obj, "display_name")
        assert hasattr(filter_obj, "apply")
        assert hasattr(filter_obj, "is_active")
        assert hasattr(filter_obj, "clear")
        assert hasattr(filter_obj, "save_state")
        assert hasattr(filter_obj, "load_state")

    def test_text_filter_implements_interface(self):
        """Test that TextFilter implements IFilter interface."""
        filter_obj = TextFilter("test", "Test Filter")

        # Check that the object is an instance of IFilter
        assert isinstance(filter_obj, IFilter)

        # Verify required methods and properties
        assert hasattr(filter_obj, "filter_id")
        assert hasattr(filter_obj, "display_name")
        assert hasattr(filter_obj, "apply")
        assert hasattr(filter_obj, "is_active")
        assert hasattr(filter_obj, "clear")
        assert hasattr(filter_obj, "save_state")
        assert hasattr(filter_obj, "load_state")


class TestIFilterManagerInterface:
    """Tests for IFilterManager interface implementation."""

    def test_filter_manager_implements_interface(self):
        """Test that FilterManager implements IFilterManager interface."""
        manager = FilterManager()

        # Check that the object is an instance of IFilterManager
        assert isinstance(manager, IFilterManager)

        # Verify required methods
        assert hasattr(manager, "register_filter")
        assert hasattr(manager, "unregister_filter")
        assert hasattr(manager, "get_filter")
        assert hasattr(manager, "get_all_filters")
        assert hasattr(manager, "apply_filters")
        assert hasattr(manager, "clear_all_filters")
        assert hasattr(manager, "save_filter_state")
        assert hasattr(manager, "load_filter_state")
        assert hasattr(manager, "get_active_filter_count")

    def test_interface_methods_signature(self):
        """Test that interface methods have the correct signature."""
        df = pd.DataFrame({"column": ["value"]})

        # Create a real FilterManager
        manager = FilterManager()

        # Create a mock filter that returns a DataFrame from apply
        mock_filter = MagicMock(spec=IFilter)
        mock_filter.filter_id = "mock_filter"
        mock_filter.is_active.return_value = True
        mock_filter.apply.return_value = df.copy()  # Return a DataFrame copy

        # Test register_filter
        manager.register_filter(mock_filter)

        # Test get_filter and verify return type
        result = manager.get_filter("mock_filter")
        assert result is mock_filter

        # Test get_all_filters and verify return type
        all_filters = manager.get_all_filters()
        assert isinstance(all_filters, list)
        assert len(all_filters) == 1
        assert all_filters[0] is mock_filter

        # Test apply_filters signature
        result_df = manager.apply_filters(df)
        assert isinstance(result_df, pd.DataFrame)

        # Test get_active_filter_count signature
        count = manager.get_active_filter_count()
        assert isinstance(count, int)
