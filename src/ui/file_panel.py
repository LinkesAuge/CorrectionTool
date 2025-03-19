"""
file_panel.py

Description: File management panel for the application
Usage:
    from src.ui.file_panel import FilePanel
    file_panel = FilePanel(parent=self)
"""

from pathlib import Path
from typing import List, Optional, Set, Tuple

from PySide6.QtCore import QDir, QSize, Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.services.config_manager import ConfigManager
from src.services.corrector import Corrector
from src.services.file_parser import CSVParser, TextParser


class FilePanel(QWidget):
    """
    File management panel for the application.

    Provides controls for loading input files and correction lists.

    Attributes:
        entries_loaded (Signal): Signal emitted when entries are loaded
        corrections_loaded (Signal): Signal emitted when corrections are loaded
        corrections_applied (Signal): Signal emitted when corrections are applied

    Implementation Notes:
        - Provides file selection controls
        - Handles loading and parsing of input files
        - Manages correction lists
    """

    entries_loaded = Signal(list)  # List[ChestEntry]
    corrections_loaded = Signal(list)  # List[CorrectionRule]
    corrections_applied = Signal(list, dict)  # List[ChestEntry], Dict[str, int]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the file panel.

        Args:
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)

        # Internal data
        self._config = ConfigManager()
        self._entries: List[ChestEntry] = []
        self._correction_rules: List[CorrectionRule] = []

        # Setup UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Input file group
        input_group = QGroupBox("Input File")
        input_layout = QVBoxLayout(input_group)

        # Input file controls
        input_file_layout = QHBoxLayout()
        self._input_file_edit = QLineEdit()
        self._input_file_edit.setPlaceholderText("Select input file...")
        self._input_file_edit.setReadOnly(True)

        self._browse_input_button = QPushButton("Browse...")
        self._browse_input_button.clicked.connect(self._open_input_file)

        input_file_layout.addWidget(self._input_file_edit)
        input_file_layout.addWidget(self._browse_input_button)

        # Add to input group
        input_layout.addLayout(input_file_layout)

        # Load button
        self._load_file_button = QPushButton("Load File")
        self._load_file_button.clicked.connect(self._load_input_file)
        self._load_file_button.setEnabled(False)

        input_layout.addWidget(self._load_file_button)

        # Add input group to main layout
        main_layout.addWidget(input_group)

        # Correction list group
        correction_group = QGroupBox("Correction List")
        correction_layout = QVBoxLayout(correction_group)

        # Correction file controls
        correction_file_layout = QHBoxLayout()
        self._correction_file_edit = QLineEdit()
        self._correction_file_edit.setPlaceholderText("Select correction list file...")
        self._correction_file_edit.setReadOnly(True)

        self._browse_correction_button = QPushButton("Browse...")
        self._browse_correction_button.clicked.connect(self._load_correction_list)

        correction_file_layout.addWidget(self._correction_file_edit)
        correction_file_layout.addWidget(self._browse_correction_button)

        # Add to correction group
        correction_layout.addLayout(correction_file_layout)

        # Load button
        self._load_correction_button = QPushButton("Load Corrections")
        self._load_correction_button.clicked.connect(self._load_correction_file)
        self._load_correction_button.setEnabled(False)

        correction_layout.addWidget(self._load_correction_button)

        # Add correction group to main layout
        main_layout.addWidget(correction_group)

        # Apply corrections group
        apply_group = QGroupBox("Apply Corrections")
        apply_layout = QVBoxLayout(apply_group)

        # Apply options
        self._apply_auto_checkbox = QCheckBox(
            "Apply corrections automatically when both files are loaded"
        )
        self._apply_auto_checkbox.setChecked(
            self._config.get_bool("Correction", "auto_save_corrections", fallback=True)
        )
        self._apply_auto_checkbox.stateChanged.connect(self._on_auto_apply_changed)

        apply_layout.addWidget(self._apply_auto_checkbox)

        # Apply button
        self._apply_button = QPushButton("Apply Corrections")
        self._apply_button.clicked.connect(self._apply_corrections)
        self._apply_button.setEnabled(False)

        apply_layout.addWidget(self._apply_button)

        # Add apply group to main layout
        main_layout.addWidget(apply_group)

        # Stats group
        self._stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(self._stats_group)

        # Stats labels
        self._entries_count_label = QLabel("0")
        self._corrections_count_label = QLabel("0")
        self._entries_corrected_label = QLabel("0")
        self._corrections_made_label = QLabel("0")

        stats_layout.addRow("Entries loaded:", self._entries_count_label)
        stats_layout.addRow("Correction rules:", self._corrections_count_label)
        stats_layout.addRow("Entries corrected:", self._entries_corrected_label)
        stats_layout.addRow("Corrections made:", self._corrections_made_label)

        # Add stats group to main layout
        main_layout.addWidget(self._stats_group)

        # Add spacer
        main_layout.addStretch()

    def _open_input_file(self):
        """
        Open a file dialog to select an input file.
        """
        import logging
        from pathlib import Path
        from PySide6.QtWidgets import QFileDialog

        logger = logging.getLogger(__name__)
        logger.info("Opening file dialog to select input file")

        # Get the default directory using the new path API
        default_dir = self._config.get_path("input_dir", "data/input")

        # Open the file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Input File", default_dir, "All Files (*)"
        )

        # If a file was selected
        if file_path:
            # Update the config
            path = Path(file_path)
            self._config.set_path("input_dir", str(path.parent))
            self._config.set_path("last_input_file", str(path))

            # Load the file
            self._file_parser.load_file(file_path)

    def _load_correction_list(self):
        """
        Open a file dialog to select a correction list file.
        """
        import logging
        from pathlib import Path
        from PySide6.QtWidgets import QFileDialog

        logger = logging.getLogger(__name__)
        logger.info("Opening file dialog to select correction list file")

        # Get the default directory using the new path API
        default_dir = self._config.get_path("corrections_dir", "data/corrections")

        # Open the file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Correction List", default_dir, "All Files (*)"
        )

        # If a file was selected
        if file_path:
            # Update the config
            path = Path(file_path)
            self._config.set_path("corrections_dir", str(path.parent))
            self._config.set_path("correction_rules_file", str(path))

            # Load the correction list
            self._correction_widget.load_correction_list(file_path)

    def _load_input_file(self) -> None:
        """Load the input file."""
        file_path = self._input_file_edit.text()
        if not file_path:
            return

        try:
            self._entries = TextParser.parse_file(file_path)
            self._entries_count_label.setText(str(len(self._entries)))

            # Emit signal
            self.entries_loaded.emit(self._entries)

            # Auto-apply corrections if enabled
            if self._apply_auto_checkbox.isChecked() and self._correction_rules and self._entries:
                self._apply_corrections()

        except Exception as e:
            print(f"Error loading input file: {e}")
            # TODO: Show error dialog

    def _load_correction_file(self) -> None:
        """Load the correction list file."""
        file_path = self._correction_file_edit.text()
        if not file_path:
            return

        try:
            self._correction_rules = CSVParser.parse_file(file_path)
            self._corrections_count_label.setText(str(len(self._correction_rules)))

            # Emit signal
            self.corrections_loaded.emit(self._correction_rules)

            # Auto-apply corrections if enabled
            if self._apply_auto_checkbox.isChecked() and self._correction_rules and self._entries:
                self._apply_corrections()

        except Exception as e:
            print(f"Error loading correction file: {e}")
            # TODO: Show error dialog

    def _apply_corrections(self) -> None:
        """Apply corrections to the entries."""
        if not self._entries or not self._correction_rules:
            return

        # Create a corrector
        corrector = Corrector(self._correction_rules)

        # Apply corrections
        corrected_entries = corrector.apply_corrections(self._entries)

        # Get stats
        stats = corrector.get_stats()

        # Update UI
        self._entries_corrected_label.setText(str(stats.get("entries_corrected", 0)))
        self._corrections_made_label.setText(str(stats.get("corrections_made", 0)))

        # Emit signal
        self.corrections_applied.emit(corrected_entries, stats)

    def _on_auto_apply_changed(self, state: int) -> None:
        """
        Handle auto-apply checkbox changes.

        Args:
            state (int): Checkbox state
        """
        is_checked = state == Qt.Checked
        self._config.set("Correction", "auto_save_corrections", is_checked)
        self._config.save()

        # Update apply button state - make sure we use proper boolean values
        should_enable = not is_checked and bool(self._entries) and bool(self._correction_rules)
        self._apply_button.setEnabled(should_enable)

        # Auto-apply if enabled and both files are loaded
        if is_checked and self._entries and self._correction_rules:
            # Use QTimer to ensure this executes after the current event cycle
            QTimer.singleShot(100, self._apply_corrections)

    def update_ui_state(self) -> None:
        """Update UI state based on loaded data."""
        has_input = bool(self._entries)
        has_corrections = bool(self._correction_rules)

        self._load_file_button.setEnabled(bool(self._input_file_edit.text()))
        self._load_correction_button.setEnabled(bool(self._correction_file_edit.text()))

        # Only enable apply button if auto-apply is disabled
        self._apply_button.setEnabled(
            has_input and has_corrections and not self._apply_auto_checkbox.isChecked()
        )

        # Update statistics
        self._entries_count_label.setText(str(len(self._entries)))
