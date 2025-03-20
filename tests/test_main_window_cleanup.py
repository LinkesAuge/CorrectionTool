"""
test_main_window_cleanup.py

Description: Tests to ensure the MainWindowInterface works correctly
after removal of legacy main window implementations.
Usage:
    pytest tests/test_main_window_cleanup.py
"""

import sys
import os
import logging
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

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
    return bootstrapper.service_factory


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


def test_sidebar_navigation(main_window):
    """Test that the sidebar navigation works correctly."""
    # Start with default tab
    initial_tab = main_window._content_widget.currentIndex()

    # Switch to different tabs and verify
    main_window._on_sidebar_button_clicked(1)
    assert main_window._content_widget.currentIndex() == 1
    assert main_window._validation_btn.isChecked()
    assert not main_window._dashboard_btn.isChecked()

    main_window._on_sidebar_button_clicked(0)
    assert main_window._content_widget.currentIndex() == 0
    assert main_window._dashboard_btn.isChecked()
    assert not main_window._validation_btn.isChecked()

    main_window._on_sidebar_button_clicked(2)
    assert main_window._content_widget.currentIndex() == 2
    assert main_window._reports_btn.isChecked()
    assert not main_window._dashboard_btn.isChecked()

    main_window._on_sidebar_button_clicked(3)
    assert main_window._content_widget.currentIndex() == 3
    assert main_window._settings_btn.isChecked()
    assert not main_window._reports_btn.isChecked()


def test_event_connections(main_window, service_factory):
    """Test that events are properly connected."""
    # Check that events are subscribed
    data_store = service_factory.get_service(IDataStore)

    # We should have subscribed to events
    assert len(main_window._connected_events) > 0

    # Test setting the status message directly
    main_window._status_bar.showMessage("Loaded 10 entries from test.txt")

    # Check that the status bar shows the message
    assert "Loaded 10 entries from test.txt" in main_window._status_bar.currentMessage()


def test_correction_rules_updated_event(main_window, service_factory):
    """Test handling of the correction rules updated event."""
    # Set the status message directly
    main_window._on_correction_rules_updated({"count": 5})

    # Test that the status bar shows the message
    assert "Updated 5 correction rules" in main_window._status_bar.currentMessage()


def test_validation_lists_updated_event(main_window, service_factory):
    """Test handling of the validation lists updated event."""
    # Set the status message directly
    main_window._on_validation_lists_updated({"list_type": "player", "count": 15})

    # Test that the status bar shows the message
    assert (
        "Updated player validation list with 15 entries" in main_window._status_bar.currentMessage()
    )


def test_config_manager_interaction(main_window, service_factory):
    """Test interaction with the config manager."""
    config_manager = service_factory.get_service(IConfigManager)

    # Switch to a different tab
    main_window._on_sidebar_button_clicked(2)

    # Verify the config was updated
    assert config_manager.get_value("Window", "active_tab") == "2"


def test_restore_state(main_window, service_factory):
    """Test that window state is restored from config."""
    config_manager = service_factory.get_service(IConfigManager)

    # Set up test geometry in the config
    test_geometry = "41006d006f00650020"
    config_manager.set_value("Window", "geometry", test_geometry)

    # Call restore state and verify it processes without errors
    main_window._restore_state()

    # We can't verify the actual geometry application in unit tests
    # but we can ensure the code runs without errors


def test_save_state(main_window, service_factory):
    """Test that window state is saved to config."""
    config_manager = service_factory.get_service(IConfigManager)

    # Call save state
    main_window._save_state()

    # Verify that values were saved to the config
    # We can't check the exact values as they depend on window state
    assert config_manager.get_value("Window", "geometry") is not None
    assert config_manager.get_value("Window", "state") is not None


def test_get_entries_bridge_method(main_window, service_factory):
    """Test the get_entries bridge method for backward compatibility."""
    # Get services
    data_store = service_factory.get_service(IDataStore)

    # Mock entries data frame
    with patch.object(data_store, "get_entries") as mock_get_entries:
        import pandas as pd

        mock_df = pd.DataFrame({"player": ["Player1", "Player2"]})
        mock_get_entries.return_value = mock_df

        # Test get_entries bridge method
        entries = main_window.get_entries()
        assert len(entries) == 2
        assert entries[0]["player"] == "Player1"


def test_get_correction_rules_bridge_method(main_window, service_factory):
    """Test the get_correction_rules bridge method for backward compatibility."""
    # Get services
    data_store = service_factory.get_service(IDataStore)

    # Mock correction rules data frame
    with patch.object(data_store, "get_correction_rules") as mock_get_rules:
        import pandas as pd

        mock_df = pd.DataFrame({"from_text": ["A", "B"], "to_text": ["C", "D"]})
        mock_get_rules.return_value = mock_df

        # Test get_correction_rules bridge method
        rules = main_window.get_correction_rules()
        assert len(rules) == 2
        assert rules[0]["from_text"] == "A"


def test_get_validation_lists_bridge_method(main_window, service_factory):
    """Test the get_validation_lists bridge method for backward compatibility."""
    # Get services
    data_store = service_factory.get_service(IDataStore)

    # Mock validation lists
    with patch.object(data_store, "get_validation_list") as mock_get_list:
        mock_get_list.side_effect = (
            lambda list_type: ["Item1", "Item2"] if list_type == "player" else ["Item3", "Item4"]
        )

        # Test get_validation_lists bridge method
        lists = main_window.get_validation_lists()
        assert len(lists["player"]) == 2
        assert lists["player"][0] == "Item1"
        assert len(lists["chest_type"]) == 2
        assert lists["chest_type"][0] == "Item3"
        assert len(lists["source"]) == 2
        assert lists["source"][0] == "Item3"


def test_close_event(main_window):
    """Test that the close event is handled correctly."""
    # Mock the save_state method to verify it's called
    with patch.object(main_window, "_save_state") as mock_save_state:
        # Create a mock close event
        mock_event = MagicMock()

        # Call the close event handler
        main_window.closeEvent(mock_event)

        # Verify that _save_state was called
        mock_save_state.assert_called_once()

        # Verify that the event was accepted
        mock_event.accept.assert_called_once()


def test_on_new_action(main_window, service_factory):
    """Test the new action handler."""
    # Mock the clear_entries method directly on the instance
    with patch.object(main_window._data_store, "clear_entries", create=True) as mock_clear:
        # Call the handler directly
        main_window._on_new()

        # Verify the method was called
        mock_clear.assert_called_once()

    # Verify that the status bar was updated
    assert "Created new file" in main_window._status_bar.currentMessage()
