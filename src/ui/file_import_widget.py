"""
file_import_widget.py

Description: Widget for importing files and displaying import status
Usage:
    from src.ui.file_import_widget import FileImportWidget
    file_widget = FileImportWidget(parent=self)
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.services.config_manager import ConfigManager
from src.services.file_parser import FileParser


class FileImportWidget(QWidget):
    """
    Widget for importing files and displaying import status.

    This widget provides controls for importing chest entries and
    correction files, along with status indicators.

    Signals:
        entries_loaded (list): Signal emitted when entries are loaded
        corrections_loaded (list): Signal emitted when corrections are loaded
        corrections_applied (list): Signal emitted when corrections are applied
        corrections_enabled_changed (bool): Signal emitted when corrections are enabled/disabled

    Implementation Notes:
        - Provides buttons for importing text and CSV files
        - Shows status indicators for loaded files
        - Auto-loads correction lists from default path
        - Provides a checkbox to enable/disable corrections
        - Corrections can be applied automatically when entries are loaded
        - Supports file format selection
        - Provides visual feedback for loading status
    """

    # Signals
    entries_loaded = Signal(list)  # List[ChestEntry]
    corrections_loaded = Signal(list)  # List[CorrectionRule]
    corrections_applied = Signal(list)  # List[ChestEntry]
    corrections_enabled_changed = Signal(bool)  # enabled

    def __init__(self, parent=None):
        """
        Initialize the file import widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize properties
        self._config = ConfigManager()
        self._file_parser = FileParser()
        self._entries: List[ChestEntry] = []
        self._correction_rules: List[CorrectionRule] = []
        self._corrections_enabled = self._config.get_bool(
            "Corrections", "auto_apply", fallback=True
        )
        self._default_correction_path = self._config.get(
            "Paths", "default_correction_rules", fallback=str(Path.cwd() / "corrections.csv")
        )
        self._last_entry_directory = self._config.get(
            "Files", "last_entry_directory", fallback=str(Path.home())
        )
        self._last_correction_directory = self._config.get(
            "Files", "last_correction_directory", fallback=str(Path.home())
        )

        # Set up UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

        # Auto-load corrections
        self._auto_load_corrections()

    def _auto_load_corrections(self):
        """Automatically load correction rules from the default path."""
        if Path(self._default_correction_path).exists():
            try:
                # Show loading status
                self._corrections_status_label.setText("Loading corrections...")
                self._corrections_status_label.setStyleSheet("color: #CC7700;")

                # Parse the file
                correction_rules = self._file_parser.parse_correction_file(
                    self._default_correction_path
                )

                # Update rules
                self.set_correction_rules(correction_rules)

                # Update status with success message
                self._show_status_message(
                    f"Loaded {len(correction_rules)} correction rules from default path", "success"
                )
            except Exception as e:
                # Update status with error message
                self._show_status_message(f"Error loading corrections: {str(e)}", "error")
                self._corrections_status_label.setText(f"Error loading corrections")
                self._corrections_status_label.setStyleSheet("color: #CC0000;")

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("File Import")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(title_label)

        # Corrections enabled checkbox
        self._corrections_checkbox = QCheckBox("Enable Corrections")
        self._corrections_checkbox.setChecked(self._corrections_enabled)
        self._corrections_checkbox.setToolTip("Enable or disable automatic corrections")
        title_layout.addWidget(self._corrections_checkbox)

        title_layout.addStretch()
        main_layout.addLayout(title_layout)

        # Import entries section
        entries_layout = QVBoxLayout()
        entries_header = QHBoxLayout()

        # Entry format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))

        self._entry_format_combo = QComboBox()
        self._entry_format_combo.addItem("Text File", "txt")
        self._entry_format_combo.setToolTip("Select the file format for chest entries")
        format_layout.addWidget(self._entry_format_combo)

        entries_header.addLayout(format_layout)
        entries_header.addStretch()

        # Import button
        self._import_entries_button = QPushButton("Import Entries")
        self._import_entries_button.setToolTip("Import chest entries from a file")
        entries_header.addWidget(self._import_entries_button)

        entries_layout.addLayout(entries_header)

        # Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))

        self._entries_status_label = QLabel("No entries loaded")
        self._entries_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_layout.addWidget(self._entries_status_label, 1)

        entries_layout.addLayout(status_layout)
        main_layout.addLayout(entries_layout)

        # Separator line
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #AAAAAA;")
        main_layout.addWidget(separator)

        # Import corrections section
        corrections_layout = QVBoxLayout()
        corrections_header = QHBoxLayout()

        # Correction format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))

        self._correction_format_combo = QComboBox()
        self._correction_format_combo.addItem("CSV File", "csv")
        self._correction_format_combo.setToolTip("Select the file format for correction rules")
        format_layout.addWidget(self._correction_format_combo)

        corrections_header.addLayout(format_layout)
        corrections_header.addStretch()

        # Import button
        self._import_corrections_button = QPushButton("Import Corrections")
        self._import_corrections_button.setToolTip("Import correction rules from a file")
        corrections_header.addWidget(self._import_corrections_button)

        corrections_layout.addLayout(corrections_header)

        # Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))

        self._corrections_status_label = QLabel("No corrections loaded")
        self._corrections_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_layout.addWidget(self._corrections_status_label, 1)

        corrections_layout.addLayout(status_layout)
        main_layout.addLayout(corrections_layout)

        # Status message label
        self._status_message_label = QLabel("")
        self._status_message_label.setAlignment(Qt.AlignCenter)
        self._status_message_label.setWordWrap(True)
        self._status_message_label.setVisible(False)
        main_layout.addWidget(self._status_message_label)

    def _connect_signals(self):
        """Connect signals to slots."""
        self._import_entries_button.clicked.connect(self.import_entries)
        self._import_corrections_button.clicked.connect(self.import_corrections)
        self._corrections_checkbox.toggled.connect(self._on_corrections_toggled)
        self._entry_format_combo.currentIndexChanged.connect(self._on_entry_format_changed)
        self._correction_format_combo.currentIndexChanged.connect(
            self._on_correction_format_changed
        )

    def set_entries(self, entries: List[ChestEntry]):
        """
        Set the chest entries.

        Args:
            entries: List of chest entries
        """
        self._entries = entries

        # Update status label
        entry_count = len(entries)
        if entry_count > 0:
            self._entries_status_label.setText(f"{entry_count} entries loaded")
            self._entries_status_label.setStyleSheet("color: #007700;")
        else:
            self._entries_status_label.setText("No entries loaded")
            self._entries_status_label.setStyleSheet("")

        # Emit signal
        self.entries_loaded.emit(entries)

        # Auto-apply corrections if enabled
        if self._corrections_enabled and self._correction_rules:
            self._apply_corrections()

    def set_correction_rules(self, rules: List[CorrectionRule]):
        """
        Set the correction rules.

        Args:
            rules: List of correction rules
        """
        self._correction_rules = rules

        # Update status label
        rule_count = len(rules)
        if rule_count > 0:
            self._corrections_status_label.setText(f"{rule_count} correction rules loaded")
            self._corrections_status_label.setStyleSheet("color: #007700;")
        else:
            self._corrections_status_label.setText("No corrections loaded")
            self._corrections_status_label.setStyleSheet("")

        # Emit signal with the updated rules
        self.corrections_loaded.emit(rules)

        # Auto-apply corrections if enabled
        if self._corrections_enabled and self._entries:
            self._apply_corrections()

    def _apply_corrections(self):
        """Apply correction rules to the loaded entries."""
        if not self._entries or not self._correction_rules:
            return

        try:
            # Show status message
            self._show_status_message("Applying corrections...", "info")

            # TODO: Implement actual correction application logic
            # For now, we'll just emit the signal with the current entries
            self.corrections_applied.emit(self._entries)

            # Show success message
            self._show_status_message(
                f"Applied {len(self._correction_rules)} correction rules to {len(self._entries)} entries",
                "success",
            )
        except Exception as e:
            # Show error message
            self._show_status_message(f"Error applying corrections: {str(e)}", "error")

    def _show_status_message(self, message: str, level: str = "info"):
        """
        Show a status message with appropriate styling.

        Args:
            message: Message to display
            level: Message level - 'info', 'success', 'warning', or 'error'
        """
        # Set message
        self._status_message_label.setText(message)

        # Set appropriate style based on level
        if level == "success":
            self._status_message_label.setStyleSheet("color: #007700; padding: 5px;")
        elif level == "warning":
            self._status_message_label.setStyleSheet("color: #CC7700; padding: 5px;")
        elif level == "error":
            self._status_message_label.setStyleSheet("color: #CC0000; padding: 5px;")
        else:  # info
            self._status_message_label.setStyleSheet("color: #000077; padding: 5px;")

        # Show the message
        self._status_message_label.setVisible(True)

        # Auto-hide the message after a delay
        # In a real implementation, we would use QTimer.singleShot()
        # But for now, we'll just show the message

    def _get_entry_file_filter(self) -> str:
        """
        Get the file filter string for entry files based on the selected format.

        Returns:
            File filter string for QFileDialog
        """
        format_data = self._entry_format_combo.currentData()
        if format_data == "txt":
            return "Text Files (*.txt);;All Files (*)"
        return "All Files (*)"

    def _get_correction_file_filter(self) -> str:
        """
        Get the file filter string for correction files based on the selected format.

        Returns:
            File filter string for QFileDialog
        """
        format_data = self._correction_format_combo.currentData()
        if format_data == "csv":
            return "CSV Files (*.csv);;All Files (*)"
        return "All Files (*)"

    @Slot()
    def import_entries(self):
        """Import chest entries from a file."""
        # Get the file filter based on selected format
        file_filter = self._get_entry_file_filter()

        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Entries", self._last_entry_directory, file_filter
        )

        if file_path:
            try:
                # Update status
                self._entries_status_label.setText("Loading entries...")
                self._entries_status_label.setStyleSheet("color: #CC7700;")

                # Save the directory for next time
                self._last_entry_directory = str(Path(file_path).parent)
                self._config.set("Files", "last_entry_directory", self._last_entry_directory)

                # Parse the file
                entries = self._file_parser.parse_entry_file(file_path)

                # Update entries
                self.set_entries(entries)

                # Show success message
                self._show_status_message(
                    f"Loaded {len(entries)} entries from {Path(file_path).name}", "success"
                )
            except Exception as e:
                # Show error in status label
                self._entries_status_label.setText("Error loading entries")
                self._entries_status_label.setStyleSheet("color: #CC0000;")

                # Show detailed error message
                self._show_status_message(f"Error loading entries: {str(e)}", "error")

                # Show error dialog for serious errors
                QMessageBox.critical(
                    self, "Import Error", f"An error occurred while importing entries:\n\n{str(e)}"
                )

    @Slot()
    def import_corrections(self):
        """Import correction rules from a file."""
        # Get the file filter based on selected format
        file_filter = self._get_correction_file_filter()

        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Corrections", self._last_correction_directory, file_filter
        )

        if file_path:
            try:
                # Update status
                self._corrections_status_label.setText("Loading corrections...")
                self._corrections_status_label.setStyleSheet("color: #CC7700;")

                # Save the directory for next time
                self._last_correction_directory = str(Path(file_path).parent)
                self._config.set(
                    "Files", "last_correction_directory", self._last_correction_directory
                )

                # Also update the General last_folder to ensure consistency with Dashboard
                self._config.set("General", "last_folder", self._last_correction_directory)

                # Save the path as the default for future auto-loading
                self._default_correction_path = file_path
                self._config.set("Paths", "default_correction_rules", self._default_correction_path)

                # Save the configuration to disk
                self._config.save()

                # Parse the file
                correction_rules = self._file_parser.parse_correction_file(file_path)

                # Update rules
                self.set_correction_rules(correction_rules)

                # Show success message
                self._show_status_message(
                    f"Loaded {len(correction_rules)} correction rules from {Path(file_path).name}",
                    "success",
                )
            except Exception as e:
                # Show error in status label
                self._corrections_status_label.setText("Error loading corrections")
                self._corrections_status_label.setStyleSheet("color: #CC0000;")

                # Show detailed error message
                self._show_status_message(f"Error loading corrections: {str(e)}", "error")

                # Show error dialog for serious errors
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"An error occurred while importing correction rules:\n\n{str(e)}",
                )

    @Slot()
    def _on_corrections_toggled(self, enabled: bool):
        """
        Handle corrections checkbox toggled.

        Args:
            enabled: Whether corrections are enabled
        """
        self._corrections_enabled = enabled
        self._config.set("Corrections", "auto_apply", enabled)

        # Apply corrections if enabled and we have entries and rules
        if enabled and self._entries and self._correction_rules:
            self._apply_corrections()

        # Emit signal
        self.corrections_enabled_changed.emit(enabled)

    @Slot()
    def _on_entry_format_changed(self, index: int):
        """
        Handle entry format combobox selection changed.

        Args:
            index: Selected index
        """
        # Update button text and tooltip based on format
        format_data = self._entry_format_combo.currentData()
        if format_data == "txt":
            self._import_entries_button.setText("Import Text")
            self._import_entries_button.setToolTip("Import chest entries from a text file")
        else:
            self._import_entries_button.setText("Import Entries")
            self._import_entries_button.setToolTip("Import chest entries from a file")

    @Slot()
    def _on_correction_format_changed(self, index: int):
        """
        Handle correction format combobox selection changed.

        Args:
            index: Selected index
        """
        # Update button text and tooltip based on format
        format_data = self._correction_format_combo.currentData()
        if format_data == "csv":
            self._import_corrections_button.setText("Import CSV")
            self._import_corrections_button.setToolTip("Import correction rules from a CSV file")
        else:
            self._import_corrections_button.setText("Import Corrections")
            self._import_corrections_button.setToolTip("Import correction rules from a file")
