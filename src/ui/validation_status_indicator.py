"""
validation_status_indicator.py

Description: Widget that indicates validation status visually
Usage:
    from src.ui.validation_status_indicator import ValidationStatusIndicator
    status_indicator = ValidationStatusIndicator(parent=self)
"""

from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from src.models.chest_entry import ChestEntry


class ValidationStatusIndicator(QWidget):
    """
    Widget that indicates validation status visually.

    Provides a visual indicator of the validation status of the entries,
    showing the percentage of valid entries and any validation errors.

    Implementation Notes:
        - Color-coded status indicator (green/yellow/red)
        - Shows percentage of valid entries
        - Displays count of validation errors
        - Updates in real-time as validation status changes
    """

    # Status levels
    STATUS_NONE = 0  # No entries loaded
    STATUS_VALID = 1  # All entries valid
    STATUS_WARNING = 2  # Some entries have warnings
    STATUS_ERROR = 3  # Some entries have errors

    def __init__(self, parent=None):
        """
        Initialize the validation status indicator.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize properties
        self._status_level = self.STATUS_NONE
        self._validation_percentage = 0
        self._error_count = 0
        self._warning_count = 0
        self._total_entries = 0

        # Set up UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)

        # Title
        title_label = QLabel("Validation Status")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(title_label)

        # Status indicator progress bar
        self._status_progress = QProgressBar()
        self._status_progress.setRange(0, 100)
        self._status_progress.setValue(0)
        self._status_progress.setTextVisible(True)
        self._status_progress.setFormat("%p% valid")
        main_layout.addWidget(self._status_progress)

        # Status details
        status_layout = QHBoxLayout()

        status_layout.addWidget(QLabel("Status:"))

        self._status_text = QLabel("No entries loaded")
        self._status_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_layout.addWidget(self._status_text, 1)

        main_layout.addLayout(status_layout)

        # Error count
        error_layout = QHBoxLayout()

        error_layout.addWidget(QLabel("Errors:"))

        self._error_text = QLabel("0")
        self._error_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        error_layout.addWidget(self._error_text, 1)

        main_layout.addLayout(error_layout)

        # Warning count
        warning_layout = QHBoxLayout()

        warning_layout.addWidget(QLabel("Warnings:"))

        self._warning_text = QLabel("0")
        self._warning_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        warning_layout.addWidget(self._warning_text, 1)

        main_layout.addLayout(warning_layout)

        # Add stretch to push everything to the top
        main_layout.addStretch()

        # Initialize status
        self._update_display()

    @Slot(list)
    def set_entries(self, entries: List[ChestEntry]):
        """
        Set the entries and update validation status.

        Args:
            entries: List of chest entries
        """
        if not entries:
            self._total_entries = 0
            self._error_count = 0
            self._warning_count = 0
            self._validation_percentage = 0
            self._status_level = self.STATUS_NONE
        else:
            self._total_entries = len(entries)

            # Count errors and warnings
            errors = 0
            warnings = 0

            for entry in entries:
                if entry.has_validation_errors():
                    validation_errors = entry.validation_errors
                    for error in validation_errors:
                        if "error" in error.lower():
                            errors += 1
                        else:
                            warnings += 1

            self._error_count = errors
            self._warning_count = warnings

            # Calculate percentage of valid entries
            invalid_entries = sum(1 for entry in entries if entry.has_validation_errors())
            valid_entries = self._total_entries - invalid_entries
            self._validation_percentage = int((valid_entries / self._total_entries) * 100)

            # Determine status level
            if errors > 0:
                self._status_level = self.STATUS_ERROR
            elif warnings > 0:
                self._status_level = self.STATUS_WARNING
            else:
                self._status_level = self.STATUS_VALID

        # Update display
        self._update_display()

    @Slot(int, int)
    def set_validation_status(self, errors: int, warnings: int):
        """
        Set the validation status directly.

        Args:
            errors: Number of error messages
            warnings: Number of warning messages
        """
        self._error_count = errors
        self._warning_count = warnings

        if self._total_entries > 0:
            # Determine status level
            if errors > 0:
                self._status_level = self.STATUS_ERROR
            elif warnings > 0:
                self._status_level = self.STATUS_WARNING
            else:
                self._status_level = self.STATUS_VALID

            # Calculate percentage (assuming one error/warning per entry at most)
            invalid_entries = min(self._total_entries, errors + warnings)
            valid_entries = self._total_entries - invalid_entries
            self._validation_percentage = int((valid_entries / self._total_entries) * 100)
        else:
            self._status_level = self.STATUS_NONE
            self._validation_percentage = 0

        # Update display
        self._update_display()

    @Slot(int)
    def set_validation_percentage(self, percentage: int):
        """
        Set the validation percentage directly.

        Args:
            percentage: Percentage of valid entries (0-100)
        """
        self._validation_percentage = percentage

        # Update display
        self._status_progress.setValue(percentage)

    def _update_display(self):
        """Update the display based on current status."""
        # Update progress bar
        self._status_progress.setValue(self._validation_percentage)

        # Update status color and text
        if self._status_level == self.STATUS_NONE:
            self._status_progress.setStyleSheet(
                "QProgressBar::chunk { background-color: #777777; }"
            )
            self._status_text.setText("No entries loaded")
            self._status_text.setStyleSheet("color: #000000;")

        elif self._status_level == self.STATUS_VALID:
            self._status_progress.setStyleSheet(
                "QProgressBar::chunk { background-color: #00CC00; }"
            )
            self._status_text.setText("All entries valid")
            self._status_text.setStyleSheet("color: #007700;")

        elif self._status_level == self.STATUS_WARNING:
            self._status_progress.setStyleSheet(
                "QProgressBar::chunk { background-color: #CCCC00; }"
            )
            self._status_text.setText("Some entries have warnings")
            self._status_text.setStyleSheet("color: #CC7700;")

        elif self._status_level == self.STATUS_ERROR:
            self._status_progress.setStyleSheet(
                "QProgressBar::chunk { background-color: #CC0000; }"
            )
            self._status_text.setText("Some entries have errors")
            self._status_text.setStyleSheet("color: #CC0000;")

        # Update error and warning counts
        self._error_text.setText(str(self._error_count))
        if self._error_count > 0:
            self._error_text.setStyleSheet("color: #CC0000;")
        else:
            self._error_text.setStyleSheet("color: #000000;")

        self._warning_text.setText(str(self._warning_count))
        if self._warning_count > 0:
            self._warning_text.setStyleSheet("color: #CC7700;")
        else:
            self._warning_text.setStyleSheet("color: #000000;")
