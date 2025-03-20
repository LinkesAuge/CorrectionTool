"""
test_validation_lists_control_panel.py

Description: Tests for the ValidationListsControlPanel component
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QModelIndex
from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui.widgets.validation_lists_control_panel import ValidationListsControlPanel
from src.ui.validation_list_widget import ValidationListWidget
from src.models.validation_list import ValidationList
from src.interfaces import IConfigManager, IDataStore


@pytest.fixture
def app():
    """Create a QApplication instance for tests."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def validation_lists():
    """Create mock validation list widgets."""
    player_widget = MagicMock(spec=ValidationListWidget)
    player_list = ValidationList(name="player")
    player_list.entries = ["Player1", "Player2", "Player3"]
    player_widget.get_list.return_value = player_list

    chest_type_widget = MagicMock(spec=ValidationListWidget)
    chest_type_list = ValidationList(name="chest_type")
    chest_type_list.entries = ["Chest Type 1", "Chest Type 2"]
    chest_type_widget.get_list.return_value = chest_type_list

    source_widget = MagicMock(spec=ValidationListWidget)
    source_list = ValidationList(name="source")
    source_list.entries = ["Source 1", "Source 2", "Source 3", "Source 4"]
    source_widget.get_list.return_value = source_list

    return {"player": player_widget, "chest_type": chest_type_widget, "source": source_widget}


@pytest.fixture
def config_manager():
    """Create a mock config manager."""
    config_manager = MagicMock(spec=IConfigManager)
    config_manager.get_path = MagicMock(return_value=Path(str(Path.home())))
    config_manager.set_path = MagicMock()
    return config_manager


@pytest.fixture
def data_store():
    """Create a mock data store."""
    return MagicMock(spec=IDataStore)


@pytest.fixture
def control_panel(app, validation_lists, config_manager, data_store):
    """Create a ValidationListsControlPanel instance."""
    return ValidationListsControlPanel(
        validation_lists=validation_lists,
        config_manager=config_manager,
        data_store=data_store,
    )


def test_initialization(control_panel, validation_lists):
    """Test that the control panel initializes correctly."""
    assert control_panel._validation_lists == validation_lists
    assert control_panel._player_checkbox.isChecked()
    assert control_panel._chest_type_checkbox.isChecked()
    assert control_panel._source_checkbox.isChecked()


def test_get_selected_lists(control_panel, validation_lists):
    """Test that get_selected_lists returns the correct lists."""
    # All checkboxes are checked by default
    selected = control_panel._get_selected_lists()
    assert len(selected) == 3
    assert "player" in selected
    assert "chest_type" in selected
    assert "source" in selected

    # Uncheck player checkbox
    control_panel._player_checkbox.setChecked(False)
    selected = control_panel._get_selected_lists()
    assert len(selected) == 2
    assert "player" not in selected
    assert "chest_type" in selected
    assert "source" in selected

    # Uncheck all checkboxes
    control_panel._chest_type_checkbox.setChecked(False)
    control_panel._source_checkbox.setChecked(False)
    selected = control_panel._get_selected_lists()
    assert len(selected) == 0


def test_update_statistics(control_panel, validation_lists):
    """Test that update_statistics updates the count labels."""
    control_panel._update_statistics()

    assert control_panel._player_count_label.text() == "Players: 3"
    assert control_panel._chest_type_count_label.text() == "Chest Types: 2"
    assert control_panel._source_count_label.text() == "Sources: 4"
    assert control_panel._total_count_label.text() == "Total Items: 9"


@patch("src.ui.widgets.validation_lists_control_panel.QMessageBox")
def test_search_functionality(mock_message_box, control_panel):
    """Test the search functionality."""
    # Mock the search term and results
    control_panel._search_edit.setText("Player")

    # Call search method
    control_panel._on_search()

    # Verify message box was shown with results
    mock_message_box.information.assert_called_once()

    # Test search with no results
    mock_message_box.reset_mock()
    control_panel._search_edit.setText("NonExistentTerm")
    control_panel._on_search()
    mock_message_box.information.assert_called_once()


def test_clear_search(control_panel):
    """Test clearing the search field."""
    control_panel._search_edit.setText("Test")
    control_panel._on_clear_search()
    assert control_panel._search_edit.text() == ""


@patch("src.ui.widgets.validation_lists_control_panel.QFileDialog")
@patch("src.ui.widgets.validation_lists_control_panel.QMessageBox")
@patch("src.ui.widgets.validation_lists_control_panel.ValidationList")
@patch("os.path.exists")
def test_import_all(
    mock_exists, mock_validation_list, mock_message_box, mock_file_dialog, control_panel
):
    """Test importing all lists."""
    # Setup mocks
    mock_file_dialog.getExistingDirectory.return_value = "/test/dir"
    mock_exists.return_value = True

    # Setup mock ValidationList with entries
    mock_list = MagicMock()
    mock_list.entries = ["Item1", "Item2"]
    mock_validation_list.load_from_file.return_value = mock_list

    # Call import method
    control_panel._on_import_all()

    # Verify dialog was shown
    mock_file_dialog.getExistingDirectory.assert_called_once()

    # Verify import was attempted for each list
    assert mock_validation_list.load_from_file.call_count == 3

    # Verify set_list was called on each widget
    for widget in control_panel._validation_lists.values():
        widget.set_list.assert_called_once()

    # Verify results message was shown
    mock_message_box.information.assert_called_once()


@patch("src.ui.widgets.validation_lists_control_panel.QFileDialog")
@patch("src.ui.widgets.validation_lists_control_panel.QMessageBox")
def test_export_all(mock_message_box, mock_file_dialog, control_panel, tmp_path):
    """Test exporting all lists."""
    # Setup mocks
    export_dir = tmp_path / "export"
    export_dir.mkdir()
    mock_file_dialog.getExistingDirectory.return_value = str(export_dir)

    # Call export method
    with patch("builtins.open") as mock_open:
        control_panel._on_export_all()

        # Verify dialog was shown
        mock_file_dialog.getExistingDirectory.assert_called_once()

        # Verify files were opened for writing
        assert mock_open.call_count == 3

        # Verify results message was shown
        mock_message_box.information.assert_called_once()


@patch("src.ui.widgets.validation_lists_control_panel.QMessageBox")
def test_find_duplicates(mock_message_box, control_panel):
    """Test finding duplicate entries."""
    # Add duplicate entries to lists
    player_list = control_panel._validation_lists["player"].get_list()
    player_list.entries.append("Player1")  # Create duplicate

    # Add same entry to another list (cross-list duplicate)
    source_list = control_panel._validation_lists["source"].get_list()
    source_list.entries.append("Player1")

    # Call find duplicates method
    control_panel._on_find_duplicates()

    # Verify results message was shown
    mock_message_box.information.assert_called_once()


@patch("src.ui.widgets.validation_lists_control_panel.QMessageBox")
def test_normalize_case(mock_message_box, control_panel):
    """Test normalizing case of entries."""
    # Setup mock for QMessageBox.question to return Yes
    mock_message_box.question.return_value = QMessageBox.Yes

    # Add mixed case entries
    player_list = control_panel._validation_lists["player"].get_list()
    player_list.entries = ["player1", "PLAYER2", "Player3"]

    # Call normalize case method
    control_panel._on_normalize_case()

    # Verify confirmation dialog was shown
    mock_message_box.question.assert_called_once()

    # Verify each widget's set_list was called
    for widget in control_panel._validation_lists.values():
        widget.set_list.assert_called_once()

    # Verify results message was shown
    mock_message_box.information.assert_called_once()


def test_list_updated_signal(control_panel):
    """Test that list_updated signal is emitted."""
    # Setup signal spy
    signal_received = False
    lists_dict = None

    def slot(data):
        nonlocal signal_received, lists_dict
        signal_received = True
        lists_dict = data

    control_panel.lists_updated.connect(slot)

    # Trigger list update
    test_list = ValidationList(name="test")
    control_panel._on_list_updated(test_list)

    # Verify signal was emitted with correct data
    assert signal_received
    assert lists_dict is not None
    assert len(lists_dict) == 3
