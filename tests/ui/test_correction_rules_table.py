"""
test_correction_rules_table.py

Description: Tests for the CorrectionRulesTable widget
Usage:
    pytest tests/ui/test_correction_rules_table.py
"""

import pytest
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTableWidgetItem, QWidget

from tests.ui.helpers.mock_services import MockCorrectionRulesTable as CorrectionRulesTable
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
        "source": MockValidationListWidget("source", ["Source1", "Source2", "Source3"]),
    }


@pytest.fixture
def sample_rules():
    """Create sample rules for testing."""
    return [
        {
            "player": "Player1",
            "chest_type": "",
            "source": "",
            "replace_player": "Player2",
            "replace_chest_type": "",
            "replace_source": "",
            "enabled": True,
        },
        {
            "player": "",
            "chest_type": "Chest1",
            "source": "",
            "replace_player": "",
            "replace_chest_type": "Chest2",
            "replace_source": "",
            "enabled": True,
        },
        {
            "player": "",
            "chest_type": "",
            "source": "Source1",
            "replace_player": "",
            "replace_chest_type": "",
            "replace_source": "Source2",
            "enabled": False,
        },
    ]


def test_table_initialization(qtbot, validation_lists):
    """Test that the table initializes correctly."""
    table = CorrectionRulesTable(validation_lists=validation_lists)
    qtbot.addWidget(table)

    # Check table structure
    assert table.columnCount() == 9
    assert table.rowCount() == 0  # Empty by default

    # Check headers
    header_labels = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
    expected_headers = [
        "Player",
        "Chest Type",
        "Source",
        "→ Player",
        "→ Chest Type",
        "→ Source",
        "Enabled",
        "Edit",
        "Delete",
    ]
    assert header_labels == expected_headers


def test_set_rules(qtbot, validation_lists, sample_rules):
    """Test that rules are properly set and displayed in the table."""
    table = CorrectionRulesTable(validation_lists=validation_lists)
    qtbot.addWidget(table)

    # Set rules
    table.set_rules(sample_rules)

    # Check number of rows
    assert table.rowCount() == len(sample_rules)

    # Check contents of first rule
    assert table.item(0, 0).text() == "Player1"
    assert table.item(0, 3).text() == "Player2"
    assert table.item(0, 6).checkState() == Qt.Checked

    # Check contents of third rule (which is disabled)
    assert table.item(2, 2).text() == "Source1"
    assert table.item(2, 5).text() == "Source2"
    assert table.item(2, 6).checkState() == Qt.Unchecked


def test_get_rules(qtbot, validation_lists, sample_rules):
    """Test getting rules from the table."""
    table = CorrectionRulesTable(validation_lists=validation_lists)
    qtbot.addWidget(table)

    # Set rules
    table.set_rules(sample_rules)

    # Get rules
    rules = table.get_rules()

    # Check that rules match what was set
    assert len(rules) == len(sample_rules)
    assert rules[0]["player"] == "Player1"
    assert rules[0]["replace_player"] == "Player2"
    assert rules[0]["enabled"] is True
    assert rules[2]["source"] == "Source1"
    assert rules[2]["replace_source"] == "Source2"
    assert rules[2]["enabled"] is False


def test_rules_updated_signal(qtbot, validation_lists, sample_rules):
    """Test that the rules_updated signal is emitted when rules change."""
    table = CorrectionRulesTable(validation_lists=validation_lists)
    qtbot.addWidget(table)

    # Use qtbot to wait for the signal
    with qtbot.waitSignal(table.rules_updated, timeout=1000) as blocker:
        # Set rules
        table.set_rules(sample_rules)

    # Check signal was received with correct data
    assert blocker.args is not None
    assert len(blocker.args[0]) == len(sample_rules)


def test_set_all_enabled(qtbot, validation_lists, sample_rules):
    """Test setting all rules as enabled/disabled."""
    table = CorrectionRulesTable(validation_lists=validation_lists)
    qtbot.addWidget(table)

    # Set rules
    table.set_rules(sample_rules)

    # Wait for signal when disabling all rules
    with qtbot.waitSignal(table.rules_updated, timeout=1000) as blocker:
        table.set_all_enabled(False)

    # Check all rules are disabled in the signal data
    updated_rules = blocker.args[0]
    assert all(not rule["enabled"] for rule in updated_rules)

    # Check UI state - all checkboxes should be unchecked
    for i in range(table.rowCount()):
        assert table.item(i, 6).checkState() == Qt.Unchecked

    # Wait for signal when enabling all rules
    with qtbot.waitSignal(table.rules_updated, timeout=1000) as blocker:
        table.set_all_enabled(True)

    # Check all rules are enabled in the signal data
    updated_rules = blocker.args[0]
    assert all(rule["enabled"] for rule in updated_rules)

    # Check UI state - all checkboxes should be checked
    for i in range(table.rowCount()):
        assert table.item(i, 6).checkState() == Qt.Checked
