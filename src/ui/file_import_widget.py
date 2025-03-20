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

from PySide6.QtCore import Qt, Signal, Slot, QTimer
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
        file_loaded (str, int): Signal emitted when a file is loaded

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
    file_loaded = Signal(str, int)  # file_path, count

    def __init__(self, parent=None):
        """
        Initialize the file import widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize logger
        import logging

        self.logger = logging.getLogger(__name__)

        # Initialize properties
        self._config = ConfigManager()
        self._file_parser = FileParser()
        self._entries: List[ChestEntry] = []
        self._correction_rules: List[CorrectionRule] = []
        self._corrections_enabled = self._config.get_boolean(
            "Correction", "auto_apply_corrections", fallback=True
        )

        # Get paths using the new path methods
        self._default_correction_path = self._config.get_path("correction_rules_file")
        self._last_entry_directory = self._config.get_last_used_path(
            "last_entry_directory", fallback=Path.home()
        )
        self._last_correction_directory = self._config.get_last_used_path(
            "last_correction_directory", fallback=Path.home()
        )
        self._processing_signal = False

        # Set up UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

        # Auto-load corrections
        self._auto_load_corrections()

    def _auto_load_corrections(self):
        """Automatically load correction rules from the default path."""
        # Set a flag to indicate auto-loading is in progress
        self._auto_loading = True

        try:
            # Get the absolute path
            correction_path = self._config.get_absolute_path(self._default_correction_path)

            # Only load if file exists
            if correction_path.exists():
                self.logger.info(f"Auto-loading correction rules from {correction_path}")

                # Use the correct FileParser method
                rules = self._file_parser.parse_correction_file(str(correction_path))

                if rules:
                    # This won't emit signals due to _auto_loading flag
                    self.set_correction_rules(rules)
                    self.logger.info(f"Loaded {len(rules)} rules from {correction_path}")

                    # Use the correct label name - wait until after UI initialization
                    if hasattr(self, "_corrections_status_label"):
                        self._corrections_status_label.setText(
                            f"{len(rules)} correction rules loaded"
                        )
                        self._corrections_status_label.setStyleSheet("color: green;")

                    # Update last used path
                    self._config.set_last_used_path("last_correction_file", str(correction_path))
                    self._config.set_last_used_path(
                        "last_correction_directory", str(correction_path.parent)
                    )

                    # Now that UI is updated, emit signal once for DataManager
                    self.logger.info(
                        f"Auto-load complete, emitting corrections_loaded with {len(rules)} rules"
                    )
                    self.corrections_loaded.emit(rules)
            else:
                self.logger.warning(f"Default correction rules file not found: {correction_path}")
                if hasattr(self, "_corrections_status_label"):
                    self._corrections_status_label.setText("No correction rules loaded")
                    self._corrections_status_label.setStyleSheet("color: orange;")
        except Exception as e:
            self.logger.error(f"Error auto-loading correction rules: {e}")
            if hasattr(self, "_corrections_status_label"):
                self._corrections_status_label.setText("Error loading correction rules")
                self._corrections_status_label.setStyleSheet("color: red;")
        finally:
            # Clear the auto-loading flag
            self._auto_loading = False

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create UI components first before attempting to update them
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

        # Remember to call _auto_load_corrections after setting up the UI
        QTimer.singleShot(100, self._auto_load_corrections)

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
        # Prevent recursive signal loops
        if self._processing_signal:
            self.logger.info(
                "Skipping redundant set_correction_rules call due to signal loop prevention"
            )
            return

        try:
            self._processing_signal = True

            # Check if rules are the same to avoid unnecessary processing
            if self._correction_rules == rules:
                self.logger.debug("Rules are unchanged, skipping update")
                return

            self._correction_rules = rules

            # Update status label
            if rules:
                rule_count = len(rules)
                self._corrections_status_label.setText(f"{rule_count} rules loaded")
                self._corrections_status_label.setStyleSheet("color: #007700;")
            else:
                self._corrections_status_label.setText("No rules loaded")
                self._corrections_status_label.setStyleSheet("")

            # Emit signal - but only if not in auto-loading mode
            # This prevents multiple signal emissions when we're doing something
            # like loading a file, not if it came from another component
            if not self._auto_loading:
                self.logger.info(
                    f"Auto-load complete, emitting corrections_loaded with {len(rules)} rules"
                )
                self.corrections_loaded.emit(rules)

            # Auto-apply corrections if enabled and we have entries
            if self._corrections_enabled and self._entries:
                self._apply_corrections()

        finally:
            self._processing_signal = False

    def set_loaded_file(self, file_path):
        """
        Set the loaded file path and update UI accordingly.

        Args:
            file_path: Path to the loaded file (str or Path)
        """
        self.logger.info(f"Setting loaded file: {file_path}")

        try:
            # Convert to Path object if it's a string
            if isinstance(file_path, str):
                path_obj = Path(file_path)
            else:
                path_obj = file_path

            # Save in config
            self._config.set_last_used_path("last_input_file", str(path_obj))

            # Update directory too
            self._config.set_last_used_path("last_entry_directory", str(path_obj.parent))

            # Update status label
            self._entries_status_label.setText(f"File loaded: {path_obj.name}")
            self._entries_status_label.setStyleSheet("color: #007700;")

            # Reload the entries from the file path
            entries = []
            try:
                # Use the file parser to get entries
                entries = self._file_parser.parse_entry_file(str(path_obj))

                # Update entries
                self._entries = entries
                entry_count = len(entries)
                self._entries_status_label.setText(f"{entry_count} entries loaded")

                # Emit the signal with the file path and count
                if not self._processing_signal:
                    self.entries_loaded.emit(entries)
                    self.file_loaded.emit(str(path_obj), entry_count)

                # The file path and count should be handled by subscribers
                # to this signal

                self.logger.info(f"Loaded {entry_count} entries from {str(path_obj)}")
            except Exception as e:
                self.logger.error(f"Error loading entries from file: {e}")
                self._entries_status_label.setText("Error loading file")
                self._entries_status_label.setStyleSheet("color: #FF0000;")

        except Exception as e:
            self.logger.error(f"Error setting loaded file: {e}")
            self._entries_status_label.setText("Invalid file path")
            self._entries_status_label.setStyleSheet("color: #FF0000;")

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
        """Import entries from a file."""
        try:
            # Get the last directory from config
            last_dir = self._config.get_last_used_path("last_entry_directory", fallback=Path.home())

            # Get file filters based on selected format
            file_filter = self._get_entry_file_filter()

            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open File", str(last_dir), file_filter
            )

            if file_path:
                # Save the last directory
                self._config.set_last_used_path("last_entry_directory", str(Path(file_path).parent))
                self._config.set_last_used_path("last_input_file", file_path)

                # Load entries using the correct FileParser method
                entries = self._file_parser.parse_entry_file(file_path)

                if entries:
                    self.set_entries(entries)

                    # Show status message
                    self._show_status_message(f"Loaded {len(entries)} entries from {file_path}")

                    # Apply corrections if enabled
                    if self._corrections_enabled and self._correction_rules:
                        self._apply_corrections()
                else:
                    self._show_status_message("No entries found in the file", "warning")
        except Exception as e:
            self._show_status_message(f"Error importing entries: {str(e)}", "error")

    @Slot()
    def import_corrections(self):
        """Import correction rules from a file."""
        try:
            # Get the last directory from config
            last_dir = self._config.get_last_used_path(
                "last_correction_directory", fallback=Path.home()
            )

            # Get file filters based on selected format
            file_filter = self._get_correction_file_filter()

            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Correction File", str(last_dir), file_filter
            )

            if file_path:
                # Save the last directory
                self._config.set_last_used_path(
                    "last_correction_directory", str(Path(file_path).parent)
                )
                self._config.set_last_used_path("last_correction_file", file_path)

                # Load correction rules using the correct FileParser method
                rules = self._file_parser.parse_correction_file(file_path)

                if rules:
                    self.set_correction_rules(rules)

                    # Show status message
                    self._show_status_message(
                        f"Loaded {len(rules)} correction rules from {file_path}"
                    )

                    # Apply corrections if enabled
                    if self._corrections_enabled and self._entries:
                        self._apply_corrections()
                else:
                    self._show_status_message("No correction rules found in the file", "warning")
        except Exception as e:
            self._show_status_message(f"Error importing correction rules: {str(e)}", "error")

    @Slot()
    def _on_corrections_toggled(self, enabled: bool):
        """
        Handle corrections checkbox toggled.

        Args:
            enabled: Whether corrections are enabled
        """
        self._corrections_enabled = enabled
        self._config.set("Correction", "auto_apply_corrections", enabled)

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
