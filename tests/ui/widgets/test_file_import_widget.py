"""
test_file_import_widget.py

Description: Tests for FileImportWidget
"""

import pytest
from unittest.mock import MagicMock, patch
import tempfile
import os
from pathlib import Path
import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog

from src.ui.file_import_widget import FileImportWidget
from src.models.chest_entry import ChestEntry
from tests.ui.helpers.ui_test_helper import UITestHelper
from tests.ui.helpers.mock_services import MockFileService, MockConfigManager


@pytest.fixture
def app():
    """Create a Qt application for testing."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def ui_helper(qtbot):
    """Create a UI test helper."""
    return UITestHelper(qtbot)


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    return {
        "file_service": MockFileService(),
        "config_manager": MockConfigManager(),
    }


@pytest.fixture
def file_import_widget(app, ui_helper, mock_services):
    """Create a FileImportWidget for testing."""
    # Create the widget
    widget = ui_helper.create_widget(FileImportWidget)

    # Return the configured widget
    return widget


@pytest.fixture
def sample_entries():
    """Create sample entries for testing."""
    return [
        {"player": "Player1", "chest_type": "Gold", "source": "Dungeon"},
        {"player": "Player2", "chest_type": "Silver", "source": "Quest"},
        {"player": "Player3", "chest_type": "Bronze", "source": "Daily"},
    ]


@pytest.fixture
def sample_correction_rules():
    """Create sample correction rules for testing."""
    return [
        {"from": "Player1", "to": "CorrectedPlayer1"},
        {"from": "Gold", "to": "Golden"},
        {"from": "Dungeon", "to": "Deep Dungeon"},
    ]


class TestFileImportWidget:
    """Tests for FileImportWidget."""

    def test_initialization(self, file_import_widget):
        """Test the initialization of FileImportWidget."""
        widget = file_import_widget

        # Verify initialization
        assert widget is not None
        assert hasattr(widget, "_entries")
        assert hasattr(widget, "_correction_rules")
        assert hasattr(widget, "_corrections_enabled")

        # Verify test mode attributes
        assert hasattr(widget, "_test_mode")
        assert widget._test_mode is False
        assert widget._test_entries_file is None
        assert widget._test_corrections_file is None

    def test_test_mode_setup(self, file_import_widget):
        """Test setting up test mode."""
        widget = file_import_widget

        # Set test mode
        widget.set_test_mode(True)
        assert widget._test_mode is True

        # Set test files
        test_entries_file = "/path/to/test/entries.csv"
        test_corrections_file = "/path/to/test/corrections.csv"

        widget.set_test_entries_file(test_entries_file)
        widget.set_test_corrections_file(test_corrections_file)

        assert widget._test_entries_file == test_entries_file
        assert widget._test_corrections_file == test_corrections_file

    def test_import_entries_in_test_mode(self, file_import_widget, sample_entries, qtbot):
        """Test importing entries in test mode."""
        widget = file_import_widget

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Set up test mode
            widget.set_test_mode(True)
            widget.set_test_entries_file(temp_path)

            # Create sample entries DataFrame and save to CSV
            entries_df = pd.DataFrame(sample_entries)
            entries_df.to_csv(temp_path, index=False)

            # Set up signal capture
            with qtbot.waitSignal(widget.entries_loaded, timeout=1000) as signal:
                # Import entries
                widget.import_entries()

            # Verify entries were loaded
            assert len(widget._entries) > 0
            assert signal.signal_triggered

            # Check status message - use the new accessor methods for headless testing
            assert "Loaded" in widget.get_last_status_message()
            assert str(len(sample_entries)) in widget._entries_status_label.text()

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_import_corrections_in_test_mode(
        self, file_import_widget, sample_correction_rules, qtbot
    ):
        """Test importing correction rules in test mode."""
        widget = file_import_widget

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Set up test mode
            widget.set_test_mode(True)
            widget.set_test_corrections_file(temp_path)

            # Create sample correction rules DataFrame and save to CSV
            corrections_df = pd.DataFrame(sample_correction_rules)
            corrections_df.to_csv(temp_path, index=False)

            # Set up signal capture
            with qtbot.waitSignal(widget.corrections_loaded, timeout=1000) as signal:
                # Import correction rules
                widget.import_corrections()

            # Verify correction rules were loaded
            assert len(widget._correction_rules) > 0
            assert signal.signal_triggered

            # Check status message - use the new accessor methods for headless testing
            assert "Loaded" in widget.get_last_status_message()
            assert str(len(sample_correction_rules)) in widget._corrections_status_label.text()

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_import_entries_with_monkeypatch(
        self, file_import_widget, sample_entries, qtbot, monkeypatch, tmp_path
    ):
        """Test importing entries using monkeypatch approach."""
        widget = file_import_widget

        # Create a temporary CSV file with entries
        temp_file = tmp_path / "test_entries.csv"
        entries_df = pd.DataFrame(sample_entries)
        entries_df.to_csv(temp_file, index=False)

        # Mock the QFileDialog.getOpenFileName method
        def mock_get_open_filename(*args, **kwargs):
            return str(temp_file), "CSV Files (*.csv)"

        monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_get_open_filename)

        # Set up signal capture
        with qtbot.waitSignal(widget.entries_loaded, timeout=1000) as signal:
            # Import entries
            widget.import_entries()

        # Verify entries were loaded
        assert len(widget._entries) > 0
        assert signal.signal_triggered

        # Check status message - use the new accessor methods for headless testing
        assert "Loaded" in widget.get_last_status_message()
        assert str(len(sample_entries)) in widget._entries_status_label.text()

    def test_import_corrections_with_monkeypatch(
        self, file_import_widget, sample_correction_rules, qtbot, monkeypatch, tmp_path
    ):
        """Test importing correction rules using monkeypatch approach."""
        widget = file_import_widget

        # Create a temporary CSV file with correction rules
        temp_file = tmp_path / "test_corrections.csv"
        corrections_df = pd.DataFrame(sample_correction_rules)
        corrections_df.to_csv(temp_file, index=False)

        # Mock the QFileDialog.getOpenFileName method
        def mock_get_open_filename(*args, **kwargs):
            return str(temp_file), "CSV Files (*.csv)"

        monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_get_open_filename)

        # Set up signal capture
        with qtbot.waitSignal(widget.corrections_loaded, timeout=1000) as signal:
            # Import correction rules
            widget.import_corrections()

        # Verify correction rules were loaded
        assert len(widget._correction_rules) > 0
        assert signal.signal_triggered

        # Check status message - use the new accessor methods for headless testing
        assert "Loaded" in widget.get_last_status_message()
        assert str(len(sample_correction_rules)) in widget._corrections_status_label.text()

    def test_corrections_enabled_toggle(self, file_import_widget, qtbot):
        """Test toggling corrections enabled state."""
        widget = file_import_widget

        # Get initial state
        initial_state = widget._corrections_enabled

        # Set up signal capture
        with qtbot.waitSignal(widget.corrections_enabled_changed, timeout=1000) as signal:
            # Toggle corrections enabled
            widget._corrections_checkbox.setChecked(not initial_state)

        # Verify state changed
        assert widget._corrections_enabled != initial_state
        assert signal.signal_triggered
        assert signal.args == [(not initial_state)]

    def test_status_message_accessors(self, file_import_widget):
        """Test the status message accessor methods."""
        widget = file_import_widget
        
        # Initially, there should be no status message
        assert widget.get_last_status_message() == ""
        assert widget.get_last_status_level() == "info"
        
        # Show a status message
        widget._show_status_message("Test message", "warning")
        
        # Verify accessors return the correct values
        assert widget.get_last_status_message() == "Test message"
        assert widget.get_last_status_level() == "warning"
        
        # Show another status message
        widget._show_status_message("Another message", "error")
        
        # Verify accessors return the updated values
        assert widget.get_last_status_message() == "Another message"
        assert widget.get_last_status_level() == "error"
