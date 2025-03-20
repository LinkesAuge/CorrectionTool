#!/usr/bin/env python3
"""
test_interface_architecture.py

Description: Tests for the interface-based architecture implementation
"""

import sys
import os
import unittest
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

import pytest
from PySide6.QtWidgets import QApplication, QTableWidget
from PySide6.QtCore import Qt

# Make sure we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import interfaces
from src.interfaces import (
    IServiceFactory,
    IDataStore,
    IFileService,
    ICorrectionService,
    IValidationService,
    IConfigManager,
    ITableAdapter,
    IComboBoxAdapter,
)

# Import implementations
from src.app_bootstrapper import AppBootstrapper
from src.services.dataframe_store import DataFrameStore
from src.ui.adapters.correction_rule_table_adapter import CorrectionRuleTableAdapter


class TestAppBootstrapper:
    """Test the AppBootstrapper functionality."""

    def test_initialization(self):
        """Test that the AppBootstrapper initializes services correctly."""
        # Create and initialize bootstrapper
        bootstrapper = AppBootstrapper()
        bootstrapper.initialize()

        # Get services and verify they're registered
        service_factory = bootstrapper.get_service_factory()

        # Check that all expected services are registered
        data_store = service_factory.get_service(IDataStore)
        assert data_store is not None, "DataStore should be registered"

        file_service = service_factory.get_service(IFileService)
        assert file_service is not None, "FileService should be registered"

        correction_service = service_factory.get_service(ICorrectionService)
        assert correction_service is not None, "CorrectionService should be registered"

        validation_service = service_factory.get_service(IValidationService)
        assert validation_service is not None, "ValidationService should be registered"

        config_manager = service_factory.get_service(IConfigManager)
        assert config_manager is not None, "ConfigManager should be registered"


class TestCorrectionRuleTableAdapter:
    """Test the CorrectionRuleTableAdapter implementation of ITableAdapter."""

    @pytest.fixture
    def table_widget(self):
        """Create a QTableWidget for testing."""
        # Need to create a QApplication if one doesn't already exist
        if not QApplication.instance():
            self.app = QApplication([])

        # Create a table widget
        table = QTableWidget()
        table.setColumnCount(4)
        table.setRowCount(0)

        return table

    @pytest.fixture
    def adapter(self, table_widget):
        """Create a CorrectionRuleTableAdapter for testing."""
        # Create the adapter
        adapter = CorrectionRuleTableAdapter(table_widget)

        # Create some sample data in the DataFrameStore
        data_store = DataFrameStore.get_instance()

        # Sample correction rules
        sample_rules = pd.DataFrame(
            {
                "from_text": ["Test1", "Test2", "Test3"],
                "to_text": ["Corrected1", "Corrected2", "Corrected3"],
                "category": ["Category1", "Category2", "Category1"],
                "enabled": [True, True, False],
            }
        )

        # Load the sample data
        data_store.set_correction_rules(sample_rules)

        # Connect the adapter
        adapter.connect()

        yield adapter

        # Disconnect after test
        adapter.disconnect()

    def test_interface_implementation(self, adapter):
        """Test that CorrectionRuleTableAdapter implements ITableAdapter."""
        assert isinstance(adapter, ITableAdapter), "Adapter should implement ITableAdapter"

    def test_get_selected_rows(self, adapter, table_widget):
        """Test the get_selected_rows method."""
        # Add some rows
        table_widget.setRowCount(3)
        for i in range(3):
            for j in range(4):
                table_widget.setItem(i, j, QTableWidget.QTableWidgetItem(f"Item {i},{j}"))

        # Select rows
        table_widget.selectRow(1)

        # Check selected rows
        selected_rows = adapter.get_selected_rows()
        assert selected_rows == [1], "Should return the selected row"

    def test_get_row_data(self, adapter, table_widget):
        """Test the get_row_data method."""
        # Refresh the adapter to populate the table
        adapter.refresh()

        # Get row data for row 0
        row_data = adapter.get_row_data(0)

        # Verify data
        assert "from_text" in row_data, "Row data should contain 'from_text'"
        assert "to_text" in row_data, "Row data should contain 'to_text'"
        assert "category" in row_data, "Row data should contain 'category'"
        assert "enabled" in row_data, "Row data should contain 'enabled'"

    def test_set_filter(self, adapter):
        """Test the set_filter method."""
        # Apply a filter
        adapter.set_filter("category", "Category1")

        # Verify filter was applied (should now show only 2 rows)
        assert adapter._table_widget.rowCount() == 2, "Filter should show only rows with Category1"

        # Clear filters
        adapter.clear_filters()

        # Verify all rows are shown
        assert adapter._table_widget.rowCount() == 3, (
            "All rows should be shown after clearing filters"
        )


if __name__ == "__main__":
    pytest.main(["-v", "test_interface_architecture.py"])
