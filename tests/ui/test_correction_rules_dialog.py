"""
test_correction_rules_dialog.py

Description: Tests for the RuleEditDialog in the correction_rules_table module
Usage:
    pytest tests/ui/test_correction_rules_dialog.py
"""

import pytest
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QDialog, QWidget

from src.models.validation_list import ValidationList
from src.ui.correction_rules_table import RuleEditDialog
from src.ui.validation_list_widget import ValidationListWidget


class MockValidationListWidget(QWidget):
    """Mock validation list widget for testing."""

    items_changed = Signal(list)

    def __init__(self, list_type: str, items: list = None):
        """Initialize with list type and optional items."""
        super().__init__()
        self._list_type = list_type
        self._items = items or []

    def get_items(self):
        """Return the list items."""
        return self._items


@pytest.fixture
def validation_lists():
    """Create mock validation lists for testing."""
    return {
        "player": MockValidationListWidget("player", ["Player1", "Player2", "Player3"]),
        "chest_type": MockValidationListWidget("chest_type", ["Chest1", "Chest2"]),
        "source": MockValidationListWidget("source", ["Source1", "Source2", "Source3", "Source4"]),
    }


@pytest.fixture
def empty_validation_lists():
    """Create empty validation lists for testing."""
    return {
        "player": MockValidationListWidget("player", []),
        "chest_type": MockValidationListWidget("chest_type", []),
        "source": MockValidationListWidget("source", []),
    }


@pytest.fixture
def example_rule():
    """Create an example rule for testing."""
    return {
        "player": "Player1",
        "chest_type": "Chest1",
        "source": "Source1",
        "replace_player": "Player2",
        "replace_chest_type": "Chest2",
        "replace_source": "Source2",
        "enabled": True,
    }


def test_dialog_initialization(qtbot, validation_lists):
    """Test that the dialog initializes correctly."""
    dialog = RuleEditDialog(validation_lists=validation_lists)
    qtbot.addWidget(dialog)

    # Check window title
    assert dialog.windowTitle() == "Edit Correction Rule"

    # Check dropdowns have the correct items
    assert dialog.player_dropdown.count() == 4  # "-- Select --" + 3 items
    assert dialog.chest_type_dropdown.count() == 3  # "-- Select --" + 2 items
    assert dialog.source_dropdown.count() == 5  # "-- Select --" + 4 items

    # Check replace dropdowns have the correct items
    assert dialog.replace_player_dropdown.count() == 4  # "-- Select --" + 3 items
    assert dialog.replace_chest_type_dropdown.count() == 3  # "-- Select --" + 2 items
    assert dialog.replace_source_dropdown.count() == 5  # "-- Select --" + 4 items

    # Check that the enabled checkbox is checked by default
    assert dialog.enabled_checkbox.isChecked()


def test_dialog_populate_form(qtbot, validation_lists, example_rule):
    """Test that the form is correctly populated with rule data."""
    dialog = RuleEditDialog(rule=example_rule, validation_lists=validation_lists)
    qtbot.addWidget(dialog)

    # Check that the fields have the correct values
    assert dialog.player_field.text() == "Player1"
    assert dialog.chest_type_field.text() == "Chest1"
    assert dialog.source_field.text() == "Source1"
    assert dialog.replace_player_field.text() == "Player2"
    assert dialog.replace_chest_type_field.text() == "Chest2"
    assert dialog.replace_source_field.text() == "Source2"
    assert dialog.enabled_checkbox.isChecked()


def test_dialog_dropdown_selection(qtbot, validation_lists):
    """Test that selecting an item from a dropdown updates the text field."""
    dialog = RuleEditDialog(validation_lists=validation_lists)
    qtbot.addWidget(dialog)

    # Select an item from each dropdown
    dialog.player_dropdown.setCurrentText("Player2")
    dialog.chest_type_dropdown.setCurrentText("Chest2")
    dialog.source_dropdown.setCurrentText("Source3")
    dialog.replace_player_dropdown.setCurrentText("Player3")
    dialog.replace_chest_type_dropdown.setCurrentText("Chest1")
    dialog.replace_source_dropdown.setCurrentText("Source4")

    # Check that the text fields have been updated
    assert dialog.player_field.text() == "Player2"
    assert dialog.chest_type_field.text() == "Chest2"
    assert dialog.source_field.text() == "Source3"
    assert dialog.replace_player_field.text() == "Player3"
    assert dialog.replace_chest_type_field.text() == "Chest1"
    assert dialog.replace_source_field.text() == "Source4"


def test_dialog_validation(qtbot, validation_lists):
    """Test dialog validation for empty match and replacement fields."""
    dialog = RuleEditDialog(validation_lists=validation_lists)
    qtbot.addWidget(dialog)

    # Test with no fields filled
    assert not dialog.validate()

    # Test with only match fields filled
    dialog.player_field.setText("Test")
    assert not dialog.validate()

    # Test with only replacement fields filled
    dialog.player_field.setText("")
    dialog.replace_player_field.setText("Test")
    assert not dialog.validate()

    # Test with both match and replacement fields filled
    dialog.player_field.setText("Test")
    dialog.replace_player_field.setText("Test")
    assert dialog.validate()


def test_dialog_accept_reject(qtbot, validation_lists):
    """Test dialog accept and reject functionality."""
    dialog = RuleEditDialog(validation_lists=validation_lists)
    qtbot.addWidget(dialog)

    # Fill in the fields
    dialog.player_field.setText("Test")
    dialog.replace_player_field.setText("Test")

    # Test accept
    qtbot.mouseClick(dialog.ok_button, Qt.LeftButton)
    assert dialog.result() == QDialog.Accepted

    # Create a new dialog for testing reject
    dialog = RuleEditDialog(validation_lists=validation_lists)
    qtbot.addWidget(dialog)

    # Test reject
    qtbot.mouseClick(dialog.cancel_button, Qt.LeftButton)
    assert dialog.result() == QDialog.Rejected


def test_dialog_get_rule_data(qtbot, validation_lists):
    """Test getting rule data from the dialog."""
    dialog = RuleEditDialog(validation_lists=validation_lists)
    qtbot.addWidget(dialog)

    # Fill in the fields
    dialog.player_field.setText("Player")
    dialog.chest_type_field.setText("Chest")
    dialog.source_field.setText("Source")
    dialog.replace_player_field.setText("ReplacePlayer")
    dialog.replace_chest_type_field.setText("ReplaceChest")
    dialog.replace_source_field.setText("ReplaceSource")
    dialog.enabled_checkbox.setChecked(False)

    # Get the rule data
    rule_data = dialog.get_rule_data()

    # Check the rule data
    assert rule_data["player"] == "Player"
    assert rule_data["chest_type"] == "Chest"
    assert rule_data["source"] == "Source"
    assert rule_data["replace_player"] == "ReplacePlayer"
    assert rule_data["replace_chest_type"] == "ReplaceChest"
    assert rule_data["replace_source"] == "ReplaceSource"
    assert rule_data["enabled"] is False


def test_dialog_handles_empty_validation_lists(qtbot, empty_validation_lists):
    """Test that the dialog handles empty validation lists correctly."""
    dialog = RuleEditDialog(validation_lists=empty_validation_lists)
    qtbot.addWidget(dialog)

    # Check that the dropdowns have only the placeholder item
    assert dialog.player_dropdown.count() == 1
    assert dialog.chest_type_dropdown.count() == 1
    assert dialog.source_dropdown.count() == 1
    assert dialog.replace_player_dropdown.count() == 1
    assert dialog.replace_chest_type_dropdown.count() == 1
    assert dialog.replace_source_dropdown.count() == 1

    # Check that the placeholder item is correct
    assert dialog.player_dropdown.itemText(0) == "-- Select --"

    # Fill in the fields manually and validate
    dialog.player_field.setText("Test")
    dialog.replace_player_field.setText("Test")
    assert dialog.validate()


def test_dialog_handles_missing_validation_lists(qtbot):
    """Test that the dialog handles missing validation lists correctly."""
    dialog = RuleEditDialog()  # No validation lists provided
    qtbot.addWidget(dialog)

    # Check that the dropdowns have only the placeholder item
    assert dialog.player_dropdown.count() == 1
    assert dialog.chest_type_dropdown.count() == 1
    assert dialog.source_dropdown.count() == 1

    # Fill in the fields manually and validate
    dialog.player_field.setText("Test")
    dialog.replace_player_field.setText("Test")
    assert dialog.validate()
