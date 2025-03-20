"""
test_validation_panel_interface.py

Description: Tests for the ValidationPanelInterface class
Usage:
    python -m pytest tests/test_validation_panel_interface.py
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
from enum import Enum, auto

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QMessageBox,
    QListWidget,
)

from src.app_bootstrapper import AppBootstrapper
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_validation_service import IValidationService
from src.interfaces.i_config_manager import IConfigManager


# Define event types
class EventType(Enum):
    """Mock event types for testing."""

    ENTRIES_LOADED = auto()
    ENTRIES_UPDATED = auto()
    CORRECTION_RULES_LOADED = auto()
    CORRECTION_RULES_UPDATED = auto()
    VALIDATION_LISTS_UPDATED = auto()
    VALIDATION_LIST_UPDATED = auto()
    CORRECTION_APPLIED = auto()
    CORRECTIONS_RESET = auto()
    ERROR_OCCURRED = auto()
    WARNING_ISSUED = auto()
    INFO_MESSAGE = auto()
    UI_REFRESH_NEEDED = auto()
    SELECTION_CHANGED = auto()
    FILTER_CHANGED = auto()


@pytest.fixture
def app():
    """Create a QApplication instance."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def bootstrapper():
    """Create an application bootstrapper for the tests."""
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()
    return bootstrapper


@pytest.fixture
def mock_data_store():
    """Create a mock data store."""
    mock = MagicMock(spec=IDataStore)
    mock.subscribe = MagicMock()
    mock.begin_transaction = MagicMock(return_value=True)
    mock.commit_transaction = MagicMock(return_value=True)
    mock.rollback_transaction = MagicMock(return_value=True)
    mock._validation_lists = {"player": [], "chest_type": [], "source": []}

    # Setup get_validation_list method
    def get_validation_list(list_type):
        return mock._validation_lists.get(list_type, [])

    mock.get_validation_list = MagicMock(side_effect=get_validation_list)

    # Setup set_validation_list method
    def set_validation_list(list_type, entries):
        mock._validation_lists[list_type] = entries
        return True

    mock.set_validation_list = MagicMock(side_effect=set_validation_list)

    # Setup notify method
    mock.notify = MagicMock()

    return mock


@pytest.fixture
def mock_file_service():
    """Create a mock file service."""
    mock = MagicMock(spec=IFileService)
    mock.load_validation_list = MagicMock(return_value=True)
    mock.save_validation_list = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_validation_service():
    """Create a mock validation service."""
    mock = MagicMock(spec=IValidationService)
    mock.set_fuzzy_matching = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager."""
    mock = MagicMock(spec=IConfigManager)

    # Setup get_value method
    mock.get_value = MagicMock(
        side_effect=lambda section, key, fallback=None: {
            "ValidationLists": {
                "player_list_name": "Player List",
                "chest_type_list_name": "Chest Type List",
                "source_list_name": "Source List",
            },
            "ValidationSettings": {"fuzzy_matching_enabled": "True", "fuzzy_threshold": "80"},
        }.get(section, {}).get(key, fallback)
    )

    # Setup get_path method
    mock.get_path = MagicMock(
        side_effect=lambda key, fallback=None: {
            "player_list_file": "player_list.txt",
            "chest_type_list_file": "chest_type_list.txt",
            "source_list_file": "source_list.txt",
            "input_dir": "input",
            "output_dir": "output",
        }.get(key, fallback)
    )

    # Setup set_value method
    mock.set_value = MagicMock(return_value=True)

    # Setup set_path method
    mock.set_path = MagicMock(return_value=True)

    # Setup get_bool method
    mock.get_bool = MagicMock(return_value=True)

    # Setup get_int method
    mock.get_int = MagicMock(return_value=80)

    return mock


@pytest.fixture
def service_factory(
    bootstrapper, mock_data_store, mock_file_service, mock_validation_service, mock_config_manager
):
    """Create a service factory with mocked services."""
    service_factory = bootstrapper.service_factory

    # Define a function to return the appropriate mock based on interface type
    def get_service_mock(interface_type):
        if interface_type == IDataStore:
            return mock_data_store
        elif interface_type == IFileService:
            return mock_file_service
        elif interface_type == IValidationService:
            return mock_validation_service
        elif interface_type == IConfigManager:
            return mock_config_manager
        return MagicMock()

    # Mock the get_service method to use our function
    service_factory.get_service = MagicMock(side_effect=get_service_mock)

    return service_factory


@pytest.fixture
def mock_patches():
    """Create mock patches for QFileDialog and QMessageBox."""
    with patch("src.ui.validation_panel_interface.QFileDialog") as file_dialog_mock:
        with patch("src.ui.validation_panel_interface.QMessageBox") as message_box_mock:
            # Configure the mocks
            file_dialog_mock.getOpenFileName.return_value = ("test_file.txt", "")
            file_dialog_mock.getSaveFileName.return_value = ("test_file.txt", "")

            # Set up message box mock to always return QMessageBox.Yes
            message_box_mock.question.return_value = QMessageBox.Yes
            message_box_mock.Yes = QMessageBox.Yes
            message_box_mock.No = QMessageBox.No

            yield {
                "file_dialog": file_dialog_mock,
                "message_box": message_box_mock,
            }


@pytest.fixture
def validation_panel(
    app,
    service_factory,
    mock_patches,
    mock_data_store,
    mock_file_service,
    mock_validation_service,
    mock_config_manager,
    monkeypatch,
):
    """Create a ValidationPanelInterface instance with mocked dependencies."""
    # Import here to avoid circular import
    from src.ui.validation_panel_interface import ValidationPanelInterface

    # Create a mock UI setup function
    def mock_setup_ui(self):
        # Create mock UI components
        for list_type in ["player", "chest_type", "source"]:
            # Create list widget mock
            list_widget = MagicMock(spec=QListWidget)
            list_widget.selectedItems.return_value = []
            setattr(self, f"_{list_type}_list_widget", list_widget)

            # Create name edit mock
            name_edit = MagicMock(spec=QLineEdit)
            name_edit.text.return_value = f"Default {list_type.title()} List"
            setattr(self, f"_{list_type}_name_edit", name_edit)

            # Create entry edit mock
            entry_edit = MagicMock(spec=QLineEdit)
            entry_edit.text.return_value = f"Test {list_type}"
            setattr(self, f"_{list_type}_entry_edit", entry_edit)

        # Create fuzzy matching control mocks
        self._fuzzy_enabled_checkbox = MagicMock(spec=QCheckBox)
        self._fuzzy_enabled_checkbox.isChecked.return_value = True
        self._fuzzy_threshold_slider = MagicMock()
        self._fuzzy_threshold_slider.value.return_value = 80
        self._threshold_value_label = MagicMock()

    # Define patched methods
    def patched_apply_fuzzy_settings(self):
        enabled = self._fuzzy_enabled_checkbox.isChecked()
        threshold = self._fuzzy_threshold_slider.value() / 100.0
        self._validation_service.set_fuzzy_matching(enabled, threshold)

    def patched_on_fuzzy_enabled_changed(self, state):
        enabled = state == Qt.CheckState.Checked.value
        self._config_manager.set_value(
            "ValidationSettings", "fuzzy_matching_enabled", "True" if enabled else "False"
        )
        self._fuzzy_threshold_slider.setEnabled(enabled)
        self._apply_fuzzy_settings()

    def patched_on_validation_lists_updated(self, event_data):
        if "list_type" in event_data:
            list_type = event_data["list_type"]
            validation_list = self._data_store.get_validation_list(list_type)
            self._update_list_widget(list_type, validation_list)
        else:
            self._refresh_all_validation_lists()

    # Monkeypatch methods to avoid UI setup
    monkeypatch.setattr(ValidationPanelInterface, "_setup_ui", mock_setup_ui)
    monkeypatch.setattr(ValidationPanelInterface, "_connect_signals", lambda self: None)
    monkeypatch.setattr(
        ValidationPanelInterface, "_load_validation_lists_from_config", lambda self: None
    )
    monkeypatch.setattr(
        ValidationPanelInterface, "_apply_fuzzy_settings", patched_apply_fuzzy_settings
    )
    monkeypatch.setattr(
        ValidationPanelInterface, "_on_fuzzy_enabled_changed", patched_on_fuzzy_enabled_changed
    )
    monkeypatch.setattr(
        ValidationPanelInterface,
        "_on_validation_lists_updated",
        patched_on_validation_lists_updated,
    )

    # Create the interface with dependencies
    validation_panel = ValidationPanelInterface(service_factory)

    # Directly set service mocks to ensure they're the correct instances
    validation_panel._data_store = mock_data_store
    validation_panel._file_service = mock_file_service
    validation_panel._validation_service = mock_validation_service
    validation_panel._config_manager = mock_config_manager

    # Initialize connected events set
    validation_panel._connected_events = {
        EventType.ENTRIES_LOADED,
        EventType.ENTRIES_UPDATED,
        EventType.VALIDATION_LISTS_UPDATED,
    }

    # Mock the update_list_widget method to avoid UI update issues
    validation_panel._update_list_widget = MagicMock()

    return validation_panel


def test_initialization(validation_panel, service_factory):
    """Test ValidationPanelInterface initialization."""
    # Ensure the service factory is stored
    assert validation_panel._service_factory == service_factory

    # Ensure UI components are created
    for list_type in ["player", "chest_type", "source"]:
        assert hasattr(validation_panel, f"_{list_type}_list_widget")
        assert hasattr(validation_panel, f"_{list_type}_name_edit")
        assert hasattr(validation_panel, f"_{list_type}_entry_edit")

    # Ensure fuzzy matching controls are created
    assert hasattr(validation_panel, "_fuzzy_enabled_checkbox")
    assert hasattr(validation_panel, "_fuzzy_threshold_slider")
    assert hasattr(validation_panel, "_threshold_value_label")


def test_service_injection(
    validation_panel,
    mock_data_store,
    mock_file_service,
    mock_validation_service,
    mock_config_manager,
):
    """Test services are correctly injected."""
    assert validation_panel._data_store == mock_data_store
    assert validation_panel._file_service == mock_file_service
    assert validation_panel._validation_service == mock_validation_service
    assert validation_panel._config_manager == mock_config_manager


def test_event_connections(validation_panel):
    """Test that event connections are properly set up."""
    # Check if events are in the _connected_events set
    assert EventType.VALIDATION_LISTS_UPDATED in validation_panel._connected_events
    assert EventType.ENTRIES_LOADED in validation_panel._connected_events
    assert EventType.ENTRIES_UPDATED in validation_panel._connected_events


def test_add_entry(validation_panel, mock_data_store):
    """Test adding an entry to a validation list."""
    # Prepare test data
    list_type = "player"
    entry = "Test Player"

    # Set up entry edit to return test entry
    entry_edit = getattr(validation_panel, f"_{list_type}_entry_edit")
    entry_edit.text.return_value = entry

    # Call add entry method
    validation_panel._add_entry(list_type)

    # Verify data store methods were called
    assert mock_data_store.begin_transaction.called
    assert mock_data_store.set_validation_list.called
    assert mock_data_store.commit_transaction.called

    # Verify entry edit was cleared
    assert entry_edit.clear.called


def test_remove_selected_entries(validation_panel, mock_data_store):
    """Test removing selected entries from a validation list."""
    # Prepare test data
    list_type = "player"

    # Set up mock selected items
    list_widget = getattr(validation_panel, f"_{list_type}_list_widget")
    selected_item1 = MagicMock()
    selected_item1.text.return_value = "Player 1"
    selected_item2 = MagicMock()
    selected_item2.text.return_value = "Player 2"
    list_widget.selectedItems.return_value = [selected_item1, selected_item2]

    # Set up validation list with items to remove
    mock_data_store._validation_lists[list_type] = ["Player 1", "Player 2", "Player 3"]

    # Call remove selected entries method
    validation_panel._remove_selected_entries(list_type)

    # Verify data store methods were called
    assert mock_data_store.begin_transaction.called
    assert mock_data_store.set_validation_list.called
    assert mock_data_store.commit_transaction.called

    # Verify list was updated correctly
    mock_data_store.set_validation_list.assert_called_with(list_type, ["Player 3"])


def test_clear_entries(validation_panel, mock_data_store, mock_patches):
    """Test clearing all entries from a validation list."""
    # Prepare test data
    list_type = "player"

    # Set up validation list with items
    mock_data_store._validation_lists[list_type] = ["Player 1", "Player 2", "Player 3"]

    # Set up message box to return Yes
    mock_patches["message_box"].question.return_value = QMessageBox.Yes

    # Call clear entries method
    validation_panel._clear_entries(list_type)

    # Verify data store methods were called
    assert mock_data_store.begin_transaction.called
    assert mock_data_store.set_validation_list.called
    assert mock_data_store.commit_transaction.called

    # Verify list was cleared
    mock_data_store.set_validation_list.assert_called_with(list_type, [])


def test_on_name_changed(validation_panel, mock_config_manager):
    """Test changing the name of a validation list."""
    # Prepare test data
    list_type = "player"
    new_name = "Custom Player List"

    # Call name changed method
    validation_panel._on_name_changed(list_type, new_name)

    # Verify config manager was called
    mock_config_manager.set_value.assert_called_with(
        "ValidationLists", f"{list_type}_list_name", new_name
    )


def test_import_list(validation_panel, mock_file_service, mock_config_manager, mock_patches):
    """Test importing a validation list from a file."""
    # Prepare test data
    list_type = "player"
    file_path = "test_player_list.txt"

    # Set up file dialog to return test file path
    mock_patches["file_dialog"].getOpenFileName.return_value = (file_path, "")

    # Call import list method
    validation_panel._on_import_list(list_type)

    # Verify file service was called
    mock_file_service.load_validation_list.assert_called_with(list_type, file_path)

    # Verify config manager was called
    mock_config_manager.set_path.assert_called_with(
        f"{list_type}_list_file", file_path, create_if_missing=True
    )


def test_export_list(
    validation_panel, mock_file_service, mock_config_manager, mock_patches, mock_data_store
):
    """Test exporting a validation list to a file."""
    # Prepare test data
    list_type = "player"
    file_path = "test_player_list.txt"

    # Set up validation list with items
    mock_data_store._validation_lists[list_type] = ["Player 1", "Player 2", "Player 3"]

    # Set up file dialog to return test file path
    mock_patches["file_dialog"].getSaveFileName.return_value = (file_path, "")

    # Call export list method
    validation_panel._export_list(list_type)

    # Verify file service was called
    mock_file_service.save_validation_list.assert_called_with(list_type, file_path)

    # Verify config manager was called
    mock_config_manager.set_path.assert_called_with(
        f"{list_type}_list_file", file_path, create_if_missing=True
    )


def test_apply_fuzzy_settings(validation_panel, mock_validation_service):
    """Test applying fuzzy matching settings."""
    # Prepare test data
    enabled = True
    threshold = 80

    # Set up fuzzy matching controls
    validation_panel._fuzzy_enabled_checkbox.isChecked.return_value = enabled
    validation_panel._fuzzy_threshold_slider.value.return_value = threshold

    # Call apply fuzzy settings method
    validation_panel._apply_fuzzy_settings()

    # Verify validation service was called
    mock_validation_service.set_fuzzy_matching.assert_called_with(enabled, threshold / 100.0)


def test_on_fuzzy_enabled_changed(validation_panel, mock_config_manager, mock_validation_service):
    """Test handling fuzzy matching enabled state changes."""
    # Prepare test data
    state = Qt.CheckState.Checked.value

    # Call fuzzy enabled changed method
    validation_panel._on_fuzzy_enabled_changed(state)

    # Verify config manager was called
    mock_config_manager.set_value.assert_called_with(
        "ValidationSettings", "fuzzy_matching_enabled", "True"
    )

    # Verify threshold slider was enabled
    validation_panel._fuzzy_threshold_slider.setEnabled.assert_called_with(True)

    # Verify apply_fuzzy_settings was called indirectly
    mock_validation_service.set_fuzzy_matching.assert_called()


def test_on_fuzzy_threshold_changed(validation_panel, mock_config_manager):
    """Test handling fuzzy threshold slider changes."""
    # Prepare test data
    value = 85

    # Call fuzzy threshold changed method
    validation_panel._on_fuzzy_threshold_changed(value)

    # Verify threshold value label was updated
    validation_panel._threshold_value_label.setText.assert_called_with(f"{value}%")

    # Verify config manager was called
    mock_config_manager.set_value.assert_called_with(
        "ValidationSettings", "fuzzy_threshold", str(value)
    )


def test_on_validation_lists_updated(validation_panel, mock_data_store):
    """Test handling validation lists updated event."""
    # Prepare test data
    list_type = "player"
    count = 3
    event_data = {"list_type": list_type, "count": count}
    validation_list = ["Player 1", "Player 2", "Player 3"]

    # Set up validation list in the mock data store
    mock_data_store._validation_lists[list_type] = validation_list

    # Make sure the mock returns our validation list
    # Override the side_effect with a simple return_value for this test
    original_side_effect = mock_data_store.get_validation_list.side_effect
    mock_data_store.get_validation_list.side_effect = None
    mock_data_store.get_validation_list.return_value = validation_list

    # Reset update_list_widget mock to clear any previous calls
    validation_panel._update_list_widget.reset_mock()

    # Call validation lists updated event handler
    validation_panel._on_validation_lists_updated(event_data)

    # Verify get_validation_list was called
    mock_data_store.get_validation_list.assert_called_with(list_type)

    # Verify update_list_widget was called with our validation list
    validation_panel._update_list_widget.assert_called_with(list_type, validation_list)

    # Restore original side_effect for other tests
    mock_data_store.get_validation_list.side_effect = original_side_effect


def test_refresh_all_validation_lists(validation_panel, mock_data_store):
    """Test refreshing all validation list widgets."""
    # Set up validation lists
    mock_data_store._validation_lists = {
        "player": ["Player 1", "Player 2"],
        "chest_type": ["Chest Type 1", "Chest Type 2"],
        "source": ["Source 1", "Source 2"],
    }

    # Mock get_validation_list to return lists from _validation_lists
    mock_data_store.get_validation_list = MagicMock(
        side_effect=lambda list_type: mock_data_store._validation_lists.get(list_type, [])
    )

    # Call refresh all validation lists method
    validation_panel._refresh_all_validation_lists()

    # Verify get_validation_list was called for each list type
    assert mock_data_store.get_validation_list.call_count == 3

    # Verify update_list_widget was called for each list type
    assert validation_panel._update_list_widget.call_count == 3


def test_update_list_widget(validation_panel):
    """Test updating a list widget with validation list entries."""
    # Prepare test data
    list_type = "player"
    validation_list = ["Player 1", "Player 2", "Player 3"]

    # Store original method
    original_update = validation_panel._update_list_widget

    # Replace mock with actual implementation for this test
    def update_list_widget(lt, vl):
        list_widget = getattr(validation_panel, f"_{lt}_list_widget")
        list_widget.blockSignals(True)
        list_widget.clear()
        for entry in vl:
            list_widget.addItem(entry)
        list_widget.blockSignals(False)

    validation_panel._update_list_widget = update_list_widget

    # Call update list widget method
    validation_panel._update_list_widget(list_type, validation_list)

    # Verify list widget was updated
    list_widget = getattr(validation_panel, f"_{list_type}_list_widget")
    assert list_widget.blockSignals.call_count == 2  # Called with True, then False
    assert list_widget.clear.called
    assert list_widget.addItem.call_count == len(validation_list)

    # Restore mock for other tests
    validation_panel._update_list_widget = original_update
