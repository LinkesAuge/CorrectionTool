"""
test_main_window_interface.py

Description: Tests for the interface-based MainWindowInterface implementation
Usage:
    pytest tests/test_main_window_interface.py
"""

import sys
import os
import logging
from pathlib import Path
import pytest

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Add the source directory to the path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app_bootstrapper import AppBootstrapper
from src.ui.main_window_interface import MainWindowInterface
from src.interfaces import (
    IServiceFactory,
    IDataStore,
    IFileService,
    ICorrectionService,
    IValidationService,
    IConfigManager,
)


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
def bootstrapper():
    """Fixture for initializing the AppBootstrapper."""
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()
    yield bootstrapper


@pytest.fixture
def service_factory(bootstrapper):
    """Fixture for getting the service factory."""
    return bootstrapper.get_service_factory()


@pytest.fixture
def main_window(app, service_factory):
    """Fixture for creating the MainWindowInterface instance."""
    window = MainWindowInterface(service_factory)
    yield window
    # Clean up the window
    window.close()


def test_main_window_initialization(main_window):
    """Test that the MainWindowInterface initializes correctly."""
    assert main_window is not None
    assert main_window.windowTitle() == "Chest Tracker Correction Tool"


def test_service_injection(main_window, service_factory):
    """Test that services are properly injected into MainWindowInterface."""
    # Check private attributes for service injection
    assert main_window._service_factory is service_factory
    assert main_window._config_manager is service_factory.get_service(IConfigManager)
    assert main_window._data_store is service_factory.get_service(IDataStore)
    assert main_window._file_service is service_factory.get_service(IFileService)
    assert main_window._correction_service is service_factory.get_service(ICorrectionService)
    assert main_window._validation_service is service_factory.get_service(IValidationService)


def test_ui_setup(main_window):
    """Test that the UI is properly set up."""
    # Check that basic UI components are created
    assert main_window._sidebar is not None
    assert main_window._content_widget is not None
    assert main_window._status_bar is not None

    # Check that navigation buttons are created
    assert main_window._dashboard_btn is not None
    assert main_window._validation_btn is not None
    assert main_window._reports_btn is not None
    assert main_window._settings_btn is not None

    # Check that content pages are created
    assert main_window._dashboard is not None
    assert main_window._correction_manager is not None
    assert main_window._report_panel is not None
    assert main_window._settings_panel is not None


def test_event_connections(main_window, service_factory):
    """Test that events are properly connected."""
    # Check that events are subscribed
    data_store = service_factory.get_service(IDataStore)

    # We should have subscribed to events
    assert len(main_window._connected_events) > 0

    # Test an event - this should not raise exceptions
    data_store.notify_subscribers("ENTRIES_LOADED", {"count": 10, "file_path": "test.txt"})

    # Test that the status bar shows the message
    assert "Loaded 10 entries from test.txt" in main_window._status_bar.currentMessage()


def test_new_action(main_window, service_factory):
    """Test that the new action works."""
    # Get services
    data_store = service_factory.get_service(IDataStore)

    # Set up a mock data frame
    import pandas as pd

    mock_entries = pd.DataFrame({"player": ["Player1", "Player2"]})
    data_store._entries_df = mock_entries

    # Trigger the new action
    main_window._on_new()

    # Check that entries are cleared
    assert data_store.get_entries().empty


def test_bridge_methods(main_window, service_factory):
    """Test that bridge methods for backward compatibility work."""
    # Get services
    data_store = service_factory.get_service(IDataStore)

    # Set up a mock data frame
    import pandas as pd

    mock_entries = pd.DataFrame({"player": ["Player1", "Player2"]})
    data_store._entries_df = mock_entries

    # Test get_entries bridge method
    entries = main_window.get_entries()
    assert len(entries) == 2
    assert entries[0]["player"] == "Player1"

    # Set up a mock data frame for correction rules
    mock_rules = pd.DataFrame({"from_text": ["A", "B"], "to_text": ["C", "D"]})
    data_store._correction_rules_df = mock_rules

    # Test get_correction_rules bridge method
    rules = main_window.get_correction_rules()
    assert len(rules) == 2
    assert rules[0]["from_text"] == "A"
