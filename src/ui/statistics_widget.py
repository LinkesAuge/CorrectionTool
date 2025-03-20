"""
statistics_widget.py

Description: Widget for displaying statistics and status information
Usage:
    from src.ui.statistics_widget import StatisticsWidget
    stats_widget = StatisticsWidget(parent=self)
"""

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule


class StatisticsWidget(QWidget):
    """
    Widget for displaying statistics and status information.

    Displays information about loaded entries, validation errors,
    and correction statistics in a compact, readable format.

    Implementation Notes:
        - Shows counts for entries, errors, and corrections
        - Uses color-coded indicators for status
        - Updates in real-time as entries are processed
        - Provides visual feedback on validation progress
    """

    def __init__(self, parent=None):
        """
        Initialize the statistics widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize properties
        self._entries = []
        self._correction_rules = []
        self._corrections_applied = 0
        self._validation_errors = 0

        # Set up UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)

        # Title
        title_label = QLabel("Statistics")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title_label)

        # Entries section
        entries_layout = self._create_stat_row("Entries:", "0")
        self._entries_label = entries_layout.itemAt(1).widget()
        main_layout.addLayout(entries_layout)

        # Validation Errors section
        errors_layout = self._create_stat_row("Validation Errors:", "0")
        self._errors_label = errors_layout.itemAt(1).widget()
        main_layout.addLayout(errors_layout)

        # Correction Rules section
        rules_layout = self._create_stat_row("Correction Rules:", "0")
        self._rules_label = rules_layout.itemAt(1).widget()
        main_layout.addLayout(rules_layout)

        # Corrections Applied section
        corrections_layout = self._create_stat_row("Corrections Applied:", "0")
        self._corrections_label = corrections_layout.itemAt(1).widget()
        main_layout.addLayout(corrections_layout)

        # Validation Progress
        validation_layout = QHBoxLayout()
        validation_layout.addWidget(QLabel("Validation:"))

        self._validation_progress = QProgressBar()
        self._validation_progress.setRange(0, 100)
        self._validation_progress.setValue(0)
        self._validation_progress.setTextVisible(True)
        self._validation_progress.setFormat("%p% validated")
        validation_layout.addWidget(self._validation_progress)

        main_layout.addLayout(validation_layout)

        # Add stretch to push everything to the top
        main_layout.addStretch()

    def _create_stat_row(self, label_text: str, value_text: str) -> QHBoxLayout:
        """
        Create a row with a label and value for displaying statistics.

        Args:
            label_text: Text for the label
            value_text: Initial value text

        Returns:
            Layout containing the label and value
        """
        layout = QHBoxLayout()
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        value = QLabel(value_text)
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(label)
        layout.addWidget(value)

        return layout

    @Slot(list)
    def set_entries(self, entries: List[ChestEntry]):
        """
        Set the current entries and update statistics.

        Args:
            entries: List of chest entries
        """
        self._entries = entries
        self._update_statistics()

    @Slot(list)
    def set_correction_rules(self, rules: List[CorrectionRule]):
        """
        Set the correction rules and update statistics.

        Args:
            rules: List of correction rules
        """
        self._correction_rules = rules
        self._update_statistics()

    @Slot(int)
    def set_corrections_applied(self, count: int):
        """
        Set the number of corrections applied and update statistics.

        Args:
            count: Number of corrections applied
        """
        self._corrections_applied = count
        self._update_statistics()

    @Slot(int)
    def set_validation_errors(self, count: int):
        """
        Set the number of validation errors.

        Args:
            count: Number of validation errors
        """
        self._validation_errors = count
        self._errors_label.setText(str(count))

        # Update background color based on error count
        if count > 0:
            self._errors_label.setStyleSheet("color: #d9534f; font-weight: bold;")
        else:
            self._errors_label.setStyleSheet("color: #5cb85c; font-weight: bold;")

    @Slot(str, int)
    def set_validation_list_count(self, list_type: str, count: int):
        """
        Set the count for a validation list.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            count: Number of items in the list
        """
        # This is just for event handling from the DataFrameStore
        # We don't need to display this in the statistics widget
        # But we need to handle the signal to prevent errors
        pass

    @Slot(int)
    def set_validation_progress(self, percentage: int):
        """
        Set the validation progress percentage.

        Args:
            percentage: Progress percentage (0-100)
        """
        self._validation_progress.setValue(percentage)

        # Update color based on percentage
        if percentage < 33:
            self._validation_progress.setStyleSheet(
                "QProgressBar::chunk { background-color: #CC0000; }"
            )
        elif percentage < 66:
            self._validation_progress.setStyleSheet(
                "QProgressBar::chunk { background-color: #CCCC00; }"
            )
        else:
            self._validation_progress.setStyleSheet(
                "QProgressBar::chunk { background-color: #00CC00; }"
            )

    def _update_statistics(self, entries=None):
        """
        Update all statistics displays with current values.

        Args:
            entries (List[ChestEntry], optional): List of entries to update statistics with.
                If provided, will update the internal entries list. Defaults to None.
        """
        # Update entries if provided
        if entries is not None:
            self._entries = entries

        # Update entry count
        entry_count = len(self._entries)
        self._entries_label.setText(str(entry_count))

        if entry_count > 0:
            self._entries_label.setStyleSheet("color: #007700;")
        else:
            self._entries_label.setStyleSheet("color: #000000;")

        # Update validation errors
        self._errors_label.setText(str(self._validation_errors))

        if self._validation_errors > 0:
            self._errors_label.setStyleSheet("color: #CC0000;")
        else:
            self._errors_label.setStyleSheet("color: #007700;")

        # Update correction rules
        rule_count = len(self._correction_rules)
        self._rules_label.setText(str(rule_count))

        if rule_count > 0:
            self._rules_label.setStyleSheet("color: #007700;")
        else:
            self._rules_label.setStyleSheet("color: #000000;")

        # Update corrections applied
        self._corrections_label.setText(str(self._corrections_applied))

        if self._corrections_applied > 0:
            self._corrections_label.setStyleSheet("color: #007700;")
        else:
            self._corrections_label.setStyleSheet("color: #000000;")

        # Calculate and update validation progress
        if entry_count > 0:
            valid_entries = entry_count - self._validation_errors
            progress_percentage = int((valid_entries / entry_count) * 100)
            self.set_validation_progress(progress_percentage)
        else:
            self.set_validation_progress(0)
