"""
test_dashboard_interface.py

Description: Tests for the interface-based DashboardInterface implementation
Usage:
    pytest tests/test_dashboard_interface.py
"""

import sys
import os
import logging
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from enum import Enum, auto

from PySide6.QtWidgets import QApplication, QSplitter, QPushButton, QWidget
from PySide6.QtCore import Qt, Signal, QObject

# Add the source directory to the path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app_bootstrapper import AppBootstrapper
from src.interfaces import (
    IServiceFactory,
    IDataStore,
    IFileService,
    ICorrectionService,
    IValidationService,
    IConfigManager,
)


# Mock EventType for testing
class EventType(Enum):
    ENTRIES_LOADED = "ENTRIES_LOADED"
    ENTRIES_UPDATED = "ENTRIES_UPDATED"
    CORRECTION_RULES_LOADED = "CORRECTION_RULES_LOADED"
    CORRECTION_RULES_UPDATED = "CORRECTION_RULES_UPDATED"
    VALIDATION_LISTS_UPDATED = "VALIDATION_LISTS_UPDATED"
    IMPORT_COMPLETED = "IMPORT_COMPLETED"


# Create mocks
class MockFileImportWidget(QWidget):
    entries_loaded = Signal(list)
    corrections_loaded = Signal(list)
    corrections_applied = Signal(list)
    corrections_enabled_changed = Signal(bool)
    file_loaded = Signal(str, int)

    def __init__(self):
        super().__init__()
        self._import_entries_button = QPushButton()
        self._corrections_status_label = MagicMock()
        self._entries_status_label = MagicMock()
        self._correction_rules_loaded = False

    def set_correction_rules_loaded(self, loaded):
        self._correction_rules_loaded = loaded


class MockEnhancedTableView(QWidget):
    entry_selected = Signal(object)
    entry_edited = Signal(object)

    def __init__(self):
        super().__init__()
        self._entries = []

    def set_entries(self, entries):
        self._entries = entries

    def get_entries(self):
        return self._entries

    def highlight_validation_errors(self):
        pass


class MockActionButtonGroup(QWidget):
    apply_corrections = Signal()
    save_requested = Signal()
    export_requested = Signal()
    settings_requested = Signal()
    apply_corrections_requested = Signal()
    validate_requested = Signal()

    def __init__(self):
        super().__init__()


class MockStatisticsWidget(QWidget):
    def __init__(self):
        super().__init__()

    def set_entries_count(self, count):
        pass

    def set_correction_rules_count(self, count):
        pass

    def set_validation_list_count(self, list_type, count):
        pass

    def set_validation_errors_count(self, count):
        pass


class MockValidationStatusIndicator(QWidget):
    def __init__(self):
        super().__init__()

    def set_validation_status(self, count):
        pass


class MockDataStore(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._entries_df = pd.DataFrame()
        self._correction_rules_df = pd.DataFrame()
        self._validation_lists = {}
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def notify_subscribers(self, event_type, event_data):
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(event_data)

    def get_entries(self):
        return self._entries_df

    def get_correction_rules(self):
        return self._correction_rules_df

    def get_validation_list(self, list_type):
        return self._validation_lists.get(list_type, [])


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
    factory = bootstrapper.service_factory

    # Create mocks for different service types
    mock_data_store = MockDataStore()
    mock_file_service = MagicMock()
    mock_correction_service = MagicMock()
    mock_validation_service = MagicMock()
    mock_config_manager = MagicMock()

    # Set up return values for get_service based on interface type
    def get_service_mock(interface_type):
        if interface_type == IDataStore:
            return mock_data_store
        elif interface_type == IFileService:
            return mock_file_service
        elif interface_type == ICorrectionService:
            return mock_correction_service
        elif interface_type == IValidationService:
            return mock_validation_service
        elif interface_type == IConfigManager:
            return mock_config_manager
        else:
            return MagicMock()

    # Mock the get_service method
    factory.get_service = MagicMock(side_effect=get_service_mock)

    return factory


@pytest.fixture
def mock_patches():
    """Set up mock patches for UI widgets."""
    # Define the patches
    with (
        patch("src.ui.dashboard_interface.FileImportWidget", return_value=MockFileImportWidget()),
        patch("src.ui.dashboard_interface.EnhancedTableView", return_value=MockEnhancedTableView()),
        patch("src.ui.dashboard_interface.ActionButtonGroup", return_value=MockActionButtonGroup()),
        patch("src.ui.dashboard_interface.StatisticsWidget", return_value=MockStatisticsWidget()),
        patch(
            "src.ui.dashboard_interface.ValidationStatusIndicator",
            return_value=MockValidationStatusIndicator(),
        ),
        patch("src.ui.dashboard_interface.QSplitter", return_value=QSplitter()),
        patch("src.ui.dashboard_interface.EventType", EventType),
    ):
        yield


@pytest.fixture
def dashboard(app, service_factory, mock_patches):
    """Fixture for creating the DashboardInterface instance."""
    # Import here to get the mocked version
    from src.ui.dashboard_interface import DashboardInterface

    widget = DashboardInterface(service_factory)
    yield widget
    # Clean up the widget
    widget.close()


def test_dashboard_initialization(dashboard):
    """Test that the DashboardInterface initializes correctly."""
    assert dashboard is not None
    assert isinstance(dashboard._splitter, QSplitter)


def test_service_injection(dashboard, service_factory):
    """Test that services are properly injected into DashboardInterface."""
    # Check private attributes for service injection
    assert dashboard._service_factory is service_factory
    assert dashboard._config_manager is service_factory.get_service(IConfigManager)
    assert dashboard._data_store is service_factory.get_service(IDataStore)
    assert dashboard._file_service is service_factory.get_service(IFileService)
    assert dashboard._correction_service is service_factory.get_service(ICorrectionService)
    assert dashboard._validation_service is service_factory.get_service(IValidationService)


def test_ui_setup(dashboard):
    """Test that the UI is properly set up."""
    # Check that basic UI components are created
    assert dashboard._file_import_widget is not None
    assert dashboard._statistics_widget is not None
    assert dashboard._validation_status is not None
    assert dashboard._action_buttons is not None
    assert dashboard._table_view is not None


def test_event_connections(dashboard, service_factory):
    """Test that events are properly connected."""
    # Check that events are subscribed
    data_store = service_factory.get_service(IDataStore)

    # We should have subscribed to events
    assert len(dashboard._connected_events) > 0

    # Check that all required events are connected
    assert EventType.ENTRIES_LOADED in dashboard._connected_events
    assert EventType.ENTRIES_UPDATED in dashboard._connected_events
    assert EventType.CORRECTION_RULES_LOADED in dashboard._connected_events
    assert EventType.CORRECTION_RULES_UPDATED in dashboard._connected_events
    assert EventType.VALIDATION_LISTS_UPDATED in dashboard._connected_events


def test_entries_loaded_event(dashboard, service_factory):
    """Test that entries loaded event is handled correctly."""
    # Get services
    data_store = service_factory.get_service(IDataStore)

    # Create mock data
    mock_entries = pd.DataFrame(
        {
            "player": ["Player1", "Player2"],
            "chest_type": ["Gold", "Silver"],
            "source": ["Dungeon", "Quest"],
        }
    )

    # Set mock data in data store
    data_store._entries_df = mock_entries

    # Create a status bar mock
    dashboard._status_bar = MagicMock()
    dashboard._status_bar.showMessage = MagicMock()

    # Trigger entries loaded event
    data_store.notify_subscribers(EventType.ENTRIES_LOADED, {"count": 2, "file_path": "test.txt"})

    # Check that the status bar message was updated
    dashboard._status_bar.showMessage.assert_called_once()


def test_correction_rules_loaded_event(dashboard, service_factory):
    """Test that correction rules loaded event is handled correctly."""
    # Get services
    data_store = service_factory.get_service(IDataStore)

    # Create mock data
    mock_rules = pd.DataFrame({"from_text": ["A", "B"], "to_text": ["C", "D"]})

    # Set mock data in data store
    data_store._correction_rules_df = mock_rules

    # Create a status bar mock
    dashboard._status_bar = MagicMock()
    dashboard._status_bar.showMessage = MagicMock()

    # Trigger correction rules loaded event
    data_store.notify_subscribers(
        EventType.CORRECTION_RULES_LOADED, {"count": 2, "file_path": "rules.csv"}
    )

    # Check that the status bar message was updated
    dashboard._status_bar.showMessage.assert_called_once()


def test_apply_corrections(dashboard, service_factory, monkeypatch):
    """Test that apply corrections works correctly."""
    # Get services
    data_store = service_factory.get_service(IDataStore)
    correction_service = service_factory.get_service(ICorrectionService)

    # Create mock data
    mock_entries = pd.DataFrame(
        {
            "player": ["Player1", "Player2"],
            "chest_type": ["Gold", "Silver"],
            "source": ["Dungeon", "Quest"],
        }
    )

    # Set mock data in data store
    data_store._entries_df = mock_entries

    # Create a status bar mock
    dashboard._status_bar = MagicMock()
    dashboard._status_bar.showMessage = MagicMock()

    # Mock the correction service apply_corrections_to_entries method
    def mock_apply_corrections(*args, **kwargs):
        return {
            "total_corrections": 2,
            "entries_modified": 1,
            "corrections": [
                {"field": "player", "from": "Player1", "to": "Player One"},
                {"field": "chest_type", "from": "Gold", "to": "Golden"},
            ],
        }

    monkeypatch.setattr(correction_service, "apply_corrections_to_entries", mock_apply_corrections)

    # Apply corrections
    dashboard._apply_corrections()

    # Check that the status bar message was updated for corrections applied
    dashboard._status_bar.showMessage.assert_called_once()


def test_entries_display(dashboard, service_factory):
    """Test that entries are properly displayed in the table view."""
    # Get services
    data_store = service_factory.get_service(IDataStore)

    # Create mock data
    mock_entries = pd.DataFrame(
        {
            "chest_type": ["Gold Chest", "Silver Chest"],
            "player": ["Player1", "Player2"],
            "source": ["Dungeon", "Quest"],
            "status": ["Pending", "Pending"],
            "validation_errors": [[], []],
            "original_values": [{}, {}],
        }
    )

    # Set mock data in data store and trigger event
    data_store._entries_df = mock_entries
    data_store.notify_subscribers(EventType.ENTRIES_UPDATED, {"count": 2})

    # Mock the set_entries method to verify it was called
    dashboard._table_view.set_entries = MagicMock()

    # Trigger the method that should update the table
    dashboard._on_entries_updated({"count": 2})

    # Verify table was updated with entries - check that it was called at least once
    assert dashboard._table_view.set_entries.call_count >= 1

    # Check that the entries were passed correctly
    call_args = dashboard._table_view.set_entries.call_args_list[0][0][0]
    assert len(call_args) == 2
    assert call_args[0]["chest_type"] == "Gold Chest"
    assert call_args[1]["player"] == "Player2"
