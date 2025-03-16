"""
corrector_panel.py

Description: Panel for displaying and interacting with chest entries
Usage:
    from src.ui.corrector_panel import CorrectorPanel
    corrector_panel = CorrectorPanel(parent=self)
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from PySide6.QtCore import Qt, QSortFilterProxyModel, Slot
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.models.validation_list import ValidationList
from src.services.config_manager import ConfigManager
from src.services.file_parser import TextParser
from src.ui.table_model import ChestEntryTableModel, ChestEntryFilterProxyModel


class CorrectorPanel(QWidget):
    """
    Panel for displaying and interacting with chest entries.
    
    Provides a table view for chest entries with filtering and correction capabilities.
    
    Attributes:
        _entries (List[ChestEntry]): The chest entries to display
        _model (ChestEntryTableModel): The table model
        _proxy_model (ChestEntryFilterProxyModel): The proxy model for filtering
        
    Implementation Notes:
        - Uses a table view with custom model
        - Provides filtering controls
        - Shows correction status with highlighting
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the corrector panel.
        
        Args:
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        
        # Initialize data
        self._entries: List[ChestEntry] = []
        self._config = ConfigManager()
        self._validation_lists: Dict[str, ValidationList] = {}
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Filter group
        filter_group = QGroupBox("Filters")
        filter_layout = QFormLayout(filter_group)
        
        # Filter controls
        self._chest_type_filter = QLineEdit()
        self._chest_type_filter.setPlaceholderText("Filter by chest type...")
        self._chest_type_filter.textChanged.connect(self._apply_filters)
        
        self._player_filter = QLineEdit()
        self._player_filter.setPlaceholderText("Filter by player...")
        self._player_filter.textChanged.connect(self._apply_filters)
        
        self._source_filter = QLineEdit()
        self._source_filter.setPlaceholderText("Filter by source...")
        self._source_filter.textChanged.connect(self._apply_filters)
        
        self._status_filter = QComboBox()
        self._status_filter.addItem("All", "")
        self._status_filter.addItem("Valid", "valid")
        self._status_filter.addItem("Corrected", "corrected")
        self._status_filter.addItem("Error", "error")
        self._status_filter.currentIndexChanged.connect(self._apply_filters)
        
        # Add to filter layout
        filter_layout.addRow("Chest Type:", self._chest_type_filter)
        filter_layout.addRow("Player:", self._player_filter)
        filter_layout.addRow("Source:", self._source_filter)
        filter_layout.addRow("Status:", self._status_filter)
        
        # Add to main layout
        main_layout.addWidget(filter_group)
        
        # Table view
        self._table_view = QTableView()
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSortingEnabled(True)
        self._table_view.setSelectionBehavior(QTableView.SelectRows)
        self._table_view.setSelectionMode(QTableView.ExtendedSelection)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Create models
        self._model = ChestEntryTableModel()
        self._proxy_model = ChestEntryFilterProxyModel()
        self._proxy_model.setSourceModel(self._model)
        
        # Set model
        self._table_view.setModel(self._proxy_model)
        
        # Add to main layout
        main_layout.addWidget(self._table_view)
        
        # Actions group
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        # Validation buttons
        self._validate_button = QPushButton("Apply Validation")
        self._validate_button.setEnabled(False)
        self._validate_button.clicked.connect(self._validate_entries)
        
        self._clear_validation_button = QPushButton("Clear Validation")
        self._clear_validation_button.setEnabled(False)
        self._clear_validation_button.clicked.connect(self._clear_validation)
        
        # Export button
        self._export_button = QPushButton("Export Corrected")
        self._export_button.setEnabled(False)
        self._export_button.clicked.connect(self._export_corrected)
        
        # Preview toggle
        self._preview_checkbox = QCheckBox("Show Preview")
        self._preview_checkbox.setChecked(True)
        
        # Add to actions layout
        actions_layout.addWidget(self._validate_button)
        actions_layout.addWidget(self._clear_validation_button)
        actions_layout.addWidget(self._export_button)
        actions_layout.addStretch()
        actions_layout.addWidget(self._preview_checkbox)
        
        # Add to main layout
        main_layout.addWidget(actions_group)
        
        # Stats group
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)
        
        # Stats labels
        self._total_entries_label = QLabel("0")
        self._displayed_entries_label = QLabel("0")
        self._valid_entries_label = QLabel("0")
        self._corrected_entries_label = QLabel("0")
        self._error_entries_label = QLabel("0")
        
        # Add to stats layout
        stats_layout.addRow("Total entries:", self._total_entries_label)
        stats_layout.addRow("Displayed entries:", self._displayed_entries_label)
        stats_layout.addRow("Valid entries:", self._valid_entries_label)
        stats_layout.addRow("Corrected entries:", self._corrected_entries_label)
        stats_layout.addRow("Entries with errors:", self._error_entries_label)
        
        # Add to main layout
        main_layout.addWidget(stats_group)
    
    @Slot(list)
    def set_entries(self, entries: List[ChestEntry]) -> None:
        """
        Set entries to display.
        
        Args:
            entries (List[ChestEntry]): The entries to display
        """
        self._entries = entries
        
        # Update model
        self._model.setEntries(self._entries)
        
        # Enable buttons
        self._export_button.setEnabled(True)
        self._validate_button.setEnabled(True)
        self._clear_validation_button.setEnabled(True)
        
        # Update stats
        self._update_stats()
    
    @Slot(list, dict)
    def on_corrections_applied(self, entries: List[ChestEntry], stats: Dict[str, int]) -> None:
        """
        Handle corrections being applied.
        
        Args:
            entries (List[ChestEntry]): The corrected entries
            stats (Dict[str, int]): Correction statistics
        """
        # Update entries
        self._entries = entries
        self._model.setEntries(entries)
        
        # Update stats
        self._update_stats()
        
        # Enable export
        self._export_button.setEnabled(len(entries) > 0)
    
    def _apply_filters(self) -> None:
        """Apply filters to the table."""
        # Get filter values
        chest_type = self._chest_type_filter.text()
        player = self._player_filter.text()
        source = self._source_filter.text()
        
        # Get status filter
        status = self._status_filter.currentData()
        
        # Apply filters
        self._proxy_model.set_filters(
            chest_type=chest_type,
            player=player,
            source=source,
            status=status
        )
        
        # Update displayed count
        self._displayed_entries_label.setText(str(self._proxy_model.rowCount()))
    
    def _update_stats(self) -> None:
        """Update statistics labels."""
        total = len(self._entries)
        valid = 0
        corrected = 0
        errors = 0
        
        for entry in self._entries:
            if entry.has_validation_errors():
                errors += 1
            elif entry.has_corrections():
                corrected += 1
            else:
                valid += 1
        
        self._total_entries_label.setText(str(total))
        self._displayed_entries_label.setText(str(self._proxy_model.rowCount()))
        self._valid_entries_label.setText(str(valid))
        self._corrected_entries_label.setText(str(corrected))
        self._error_entries_label.setText(str(errors))
    
    def _export_corrected(self) -> None:
        """Export corrected entries to a file."""
        if not self._entries:
            return
        
        # Get default output directory
        default_dir = self._config.get("Files", "default_output_dir", fallback="data/output")
        
        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Corrected Entries", default_dir, "Text Files (*.txt)"
        )
        
        if not file_path:
            return
        
        try:
            # Save entries to file
            TextParser.save_entries_to_file(self._entries, file_path)
            
            # Save the directory
            self._config.set("Files", "default_output_dir", str(Path(file_path).parent))
            self._config.save()
            
            # Show success message
            QMessageBox.information(
                self, 
                "Export Successful", 
                f"Entries successfully exported to {file_path}"
            )
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self, 
                "Export Error", 
                f"Error exporting entries: {e}"
            )
    
    def set_validation_lists(self, validation_lists: Dict[str, ValidationList]) -> None:
        """
        Set the validation lists.
        
        Args:
            validation_lists (Dict[str, ValidationList]): The validation lists
        """
        self._validation_lists = validation_lists
        
        # If auto-validation is enabled, validate entries
        if self._config.get_bool("Validation", "auto_validate", fallback=True):
            self._validate_entries()
    
    def _validate_entries(self) -> None:
        """Validate entries against validation lists."""
        if not self._entries:
            return
        
        validation_counts = {
            'total': len(self._entries),
            'errors': 0
        }
        
        # Clear existing validation errors
        for entry in self._entries:
            entry.clear_validation_errors()
        
        # Apply validation
        for entry in self._entries:
            # Check player validation
            if "player" in self._validation_lists and self._validation_lists["player"].count() > 0:
                if not self._validation_lists["player"].is_valid(entry.player):
                    entry.add_validation_error(f"Invalid player: {entry.player}")
                    validation_counts['errors'] += 1
            
            # Check chest type validation
            if "chest_type" in self._validation_lists and self._validation_lists["chest_type"].count() > 0:
                if not self._validation_lists["chest_type"].is_valid(entry.chest_type):
                    entry.add_validation_error(f"Invalid chest type: {entry.chest_type}")
                    validation_counts['errors'] += 1
            
            # Check source validation
            if "source" in self._validation_lists and self._validation_lists["source"].count() > 0:
                if not self._validation_lists["source"].is_valid(entry.source):
                    entry.add_validation_error(f"Invalid source: {entry.source}")
                    validation_counts['errors'] += 1
        
        # Update model
        self._model.layoutChanged.emit()
        
        # Update stats
        self._update_stats()
        
        # Show message
        QMessageBox.information(
            self,
            "Validation Complete",
            f"Validation complete: {validation_counts['errors']} errors found in {validation_counts['total']} entries."
        )
    
    def _clear_validation(self) -> None:
        """Clear validation errors from entries."""
        if not self._entries:
            return
        
        # Clear validation errors
        for entry in self._entries:
            entry.clear_validation_errors()
        
        # Update model
        self._model.layoutChanged.emit()
        
        # Update stats
        self._update_stats()
        
        # Show message
        QMessageBox.information(
            self,
            "Validation Cleared",
            "Validation errors have been cleared."
        ) 