"""
test_report_panel_interface.py

Description: Tests for the ReportPanelInterface class
"""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.ui.report_panel_interface import ReportPanelInterface
from src.interfaces import IServiceFactory, IConfigManager, IDataStore


@pytest.fixture
def app():
    """Create a Qt application for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def service_factory():
    """Create a mock service factory."""
    mock_factory = MagicMock()

    # Create mock services
    mock_config = MagicMock()
    mock_config.get_path = MagicMock(return_value=Path.cwd())
    mock_config.set_path = MagicMock()

    mock_data_store = MagicMock()
    mock_data_store.entries_changed = MagicMock()
    mock_data_store.entries_changed.connect = MagicMock()

    # Configure get_service method to return appropriate mocks
    def get_service(service_type):
        if service_type == IConfigManager:
            return mock_config
        elif service_type == IDataStore:
            return mock_data_store
        return MagicMock()

    mock_factory.get_service = MagicMock(side_effect=get_service)

    # Add get_service_or_none method
    mock_factory.get_service_or_none = MagicMock(return_value=None)

    return mock_factory


@pytest.fixture
def mock_entries_df():
    """Create a mock DataFrame for entries."""
    data = {
        "chest_type": ["Elegant Chest", "Cobra Chest", "Merchant's Chest"],
        "player": ["Player1", "Player2", "Player1"],
        "source": ["Level 20 epic Crypt", "Level 15 Crypt", "Mercenary Exchange"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def report_panel(app, service_factory):
    """Create a ReportPanelInterface for testing."""
    return ReportPanelInterface(service_factory)


def test_initialization(report_panel):
    """Test that ReportPanelInterface initializes correctly."""
    assert report_panel is not None
    assert hasattr(report_panel, "_service_factory")
    assert hasattr(report_panel, "_config_manager")
    assert hasattr(report_panel, "_data_store")


def test_service_injection(report_panel, service_factory):
    """Test that services are properly injected."""
    assert report_panel._service_factory == service_factory
    assert report_panel._config_manager == service_factory.get_service(IConfigManager)
    assert report_panel._data_store == service_factory.get_service(IDataStore)


def test_ui_setup(report_panel):
    """Test that UI components are set up correctly."""
    assert hasattr(report_panel, "_report_type_combo")
    assert hasattr(report_panel, "_from_date")
    assert hasattr(report_panel, "_to_date")
    assert hasattr(report_panel, "_include_corrections_checkbox")
    assert hasattr(report_panel, "_include_validation_checkbox")
    assert hasattr(report_panel, "_export_format_combo")
    assert hasattr(report_panel, "_generate_button")
    assert hasattr(report_panel, "_export_button")
    assert hasattr(report_panel, "_text_report")
    assert hasattr(report_panel, "_table_report")

    # Check that report types are populated
    assert report_panel._report_type_combo.count() > 0

    # Check that export formats are populated
    assert report_panel._export_format_combo.count() > 0


def test_event_connections(report_panel):
    """Test that event connections are set up correctly."""
    # Test connection to data store
    assert report_panel._data_store.entries_changed.connect.called


def test_on_entries_changed(report_panel, mock_entries_df):
    """Test handling of entries changed event."""
    # Call the event handler
    report_panel._on_entries_changed(mock_entries_df)

    # Check that entries were stored
    assert hasattr(report_panel, "_entries_df")
    assert report_panel._entries_df is mock_entries_df


def test_generate_summary_report(report_panel, mock_entries_df):
    """Test generation of summary report."""
    # Set up entries
    report_panel._entries_df = mock_entries_df

    # Generate report
    report_panel._generate_summary_report()

    # Check that text report was populated
    assert report_panel._text_report.toPlainText() != ""
    assert "Total entries: 3" in report_panel._text_report.toPlainText()
    assert "Unique players: 2" in report_panel._text_report.toPlainText()
    assert "Unique chest types: 3" in report_panel._text_report.toPlainText()

    # Check that table report was populated
    assert report_panel._table_report.rowCount() > 0
    assert report_panel._table_report.columnCount() == 3


def test_update_options(report_panel):
    """Test that options are updated when report type changes."""
    # Set up a spy on the enabled property of date controls
    with patch.object(report_panel._from_date, "setEnabled") as mock_set_enabled:
        # Trigger update for a report type that uses date range
        report_panel._report_type_combo.setCurrentText("Summary Report")
        report_panel._update_options()

        # Check that date range was enabled
        mock_set_enabled.assert_called_with(True)

        # Change to a type that doesn't use date range
        report_panel._report_type_combo.setCurrentText("Player Stats")
        report_panel._update_options()

        # Check that date range was disabled
        mock_set_enabled.assert_called_with(False)


def test_export_report_validation(report_panel):
    """Test validation when exporting report."""
    # Set up empty report
    report_panel._text_report.clear()

    # Mock QMessageBox.warning to avoid dialog
    with patch("src.ui.report_panel_interface.QMessageBox.warning") as mock_warning:
        # Try to export
        report_panel._export_report()

        # Check that warning was shown
        assert mock_warning.called


def test_generate_report_validation(report_panel):
    """Test validation when generating report."""
    # Set up empty entries
    report_panel._entries_df = None

    # Mock QMessageBox.warning to avoid dialog
    with patch("src.ui.report_panel_interface.QMessageBox.warning") as mock_warning:
        # Try to generate report
        report_panel._generate_report()

        # Check that warning was shown
        assert mock_warning.called
