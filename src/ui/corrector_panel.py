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
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    QSplitter,
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.models.validation_list import ValidationList
from src.services.config_manager import ConfigManager
from src.services.file_parser import TextParser
from src.ui.table_model import ChestEntryTableModel, ChestEntryFilterProxyModel
from src.services.corrector import Corrector


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
        self._validation_lists: Dict[str, ValidationList] = {}
        self._config = ConfigManager()

        # Initialize corrector
        self._corrector = Corrector([])

        # Setup UI
        self._setup_ui()

        # Apply saved settings
        self._apply_saved_settings()

    def _setup_ui(self) -> None:
        """Set up the UI elements."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create top bar with controls
        self._setup_controls(layout)

        # Create content area
        self._content_widget = QWidget()
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Create content splitter (table vs details)
        self._content_splitter = QSplitter(Qt.Horizontal)

        # Table panel
        table_panel = QWidget()
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Create table
        self._setup_table(table_layout)

        # Add table panel to splitter
        self._content_splitter.addWidget(table_panel)

        # Details panel - this replaces the preview panel with a more focused UI
        self._details_panel = QWidget()
        details_layout = QVBoxLayout(self._details_panel)
        details_layout.setContentsMargins(10, 10, 10, 10)

        # Add details header
        details_header = QLabel("Entry Details")
        details_header.setStyleSheet("font-size: 14px; font-weight: bold;")
        details_layout.addWidget(details_header)

        # Add details content
        self._details_content = QWidget()
        details_content_layout = QFormLayout(self._details_content)

        self._entry_id_label = QLabel("")
        details_content_layout.addRow("ID:", self._entry_id_label)

        self._entry_name_label = QLabel("")
        details_content_layout.addRow("Name:", self._entry_name_label)

        self._entry_type_label = QLabel("")
        details_content_layout.addRow("Type:", self._entry_type_label)

        self._entry_player_label = QLabel("")
        details_content_layout.addRow("Player:", self._entry_player_label)

        self._entry_source_label = QLabel("")
        details_content_layout.addRow("Source:", self._entry_source_label)

        # Corrections group
        corrections_group = QGroupBox("Corrections")
        corrections_layout = QVBoxLayout(corrections_group)

        self._corrections_label = QLabel("No corrections applied")
        corrections_layout.addWidget(self._corrections_label)

        details_layout.addWidget(self._details_content)
        details_layout.addWidget(corrections_group)
        details_layout.addStretch()

        # Add details panel to splitter
        self._content_splitter.addWidget(self._details_panel)

        # Add splitter to content layout
        content_layout.addWidget(self._content_splitter)

        # Add content widget to main layout
        layout.addWidget(self._content_widget)

        # Set initial splitter sizes (70/30 split)
        self._content_splitter.setSizes([700, 300])

    def _setup_controls(self, layout: QVBoxLayout) -> None:
        """
        Set up the control panel.

        Args:
            layout (QVBoxLayout): The main layout to add controls to
        """
        control_panel = QWidget()
        control_panel.setObjectName("controlPanel")
        control_panel.setMaximumHeight(120)
        control_layout = QVBoxLayout(control_panel)

        # Top controls
        top_controls = QHBoxLayout()

        # Filter group
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout(filter_group)

        # Type filter
        filter_layout.addWidget(QLabel("Type:"))
        self._type_filter = QComboBox()
        self._type_filter.setMinimumWidth(120)
        filter_layout.addWidget(self._type_filter)

        # Player filter
        filter_layout.addWidget(QLabel("Player:"))
        self._player_filter = QComboBox()
        self._player_filter.setMinimumWidth(120)
        filter_layout.addWidget(self._player_filter)

        # Source filter
        filter_layout.addWidget(QLabel("Source:"))
        self._source_filter = QComboBox()
        self._source_filter.setMinimumWidth(120)
        filter_layout.addWidget(self._source_filter)

        # Search filter
        filter_layout.addWidget(QLabel("Search:"))
        self._search_filter = QLineEdit()
        self._search_filter.setPlaceholderText("Search entries...")
        filter_layout.addWidget(self._search_filter)

        top_controls.addWidget(filter_group)

        # Action group
        action_group = QGroupBox("Actions")
        action_layout = QHBoxLayout(action_group)

        # Auto-correct button
        self._auto_correct_button = QPushButton("Auto-Correct All")
        self._auto_correct_button.setToolTip("Apply automatic corrections to all entries")
        action_layout.addWidget(self._auto_correct_button)

        # Export button
        self._export_button = QPushButton("Export Corrected")
        self._export_button.setToolTip("Export corrected entries to a file")
        action_layout.addWidget(self._export_button)

        top_controls.addWidget(action_group)

        # Add top controls to control layout
        control_layout.addLayout(top_controls)

        # Status bar
        status_layout = QHBoxLayout()
        self._status_label = QLabel("No entries loaded")
        status_layout.addWidget(self._status_label)

        # Validation status
        self._validation_status = QLabel("")
        status_layout.addWidget(self._validation_status)

        control_layout.addLayout(status_layout)

        # Add control panel to main layout
        layout.addWidget(control_panel)

    def _apply_saved_settings(self) -> None:
        """Apply saved settings from config."""
        # No more preview settings

    def set_entries(self, entries: List[ChestEntry]) -> None:
        """
        Set the entries to display.

        Args:
            entries (List[ChestEntry]): The entries to display
        """
        self._entries = entries

        # Update the table model
        self._table_model.setEntries(self._entries)

        # Update stats
        self._update_stats()

        # Validate entries if auto-validate is enabled
        auto_validate = self._config.get_bool("Validation", "auto_validate", fallback=True)
        if auto_validate and self._validation_lists:
            self._validate_entries()

    def on_corrections_applied(self, entries: List[ChestEntry]) -> None:
        """
        Handle when corrections are applied.

        Args:
            entries (List[ChestEntry]): The corrected entries
        """
        # Update the entries
        self._entries = entries

        # Update the table model
        self._table_model.setEntries(entries)

        # Update stats
        self._update_stats()

        # Show message
        QMessageBox.information(
            self,
            "Corrections Applied",
            f"Applied {self._corrector.stats['corrections_made']} corrections to {self._corrector.stats['entries_corrected']} entries.",
        )

    def _apply_filters(self) -> None:
        """Apply filters to the table."""
        # Get filter values
        chest_type = self._type_filter.currentText()
        player = self._player_filter.currentText()
        source = self._source_filter.text()

        # Apply filters
        self._proxy_model.set_filters(chest_type=chest_type, player=player, source=source)

        # Update displayed count
        self._status_label.setText(f"{self._proxy_model.rowCount()} entries")

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

        self._status_label.setText(f"{total} entries")
        self._validation_status.setText(f"{valid} valid, {corrected} corrected, {errors} errors")

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
                self, "Export Successful", f"Entries successfully exported to {file_path}"
            )
        except Exception as e:
            # Show error message
            QMessageBox.critical(self, "Export Error", f"Error exporting entries: {e}")

    def set_validation_lists(self, validation_lists: Dict[str, ValidationList]) -> None:
        """
        Set validation lists for validation.

        Args:
            validation_lists (Dict[str, ValidationList]): Validation lists
        """
        self._validation_lists = validation_lists

        # Update corrector with validation lists
        if hasattr(self, "_corrector") and self._corrector:
            self._corrector.set_validation_lists(validation_lists)

        # Refresh validation status if entries are loaded
        if self._entries:
            self._validate_entries()

    def _validate_entries(self) -> None:
        """Validate all entries against validation lists."""
        if not self._validation_lists or not self._entries:
            return

        # Reset validation status
        for entry in self._entries:
            entry.reset_validation()

        # Validate each entry
        for entry in self._entries:
            self._validate_entry(entry)

        # Update the table to show validation status
        self._table_model.layoutChanged.emit()

    def _validate_entry(self, entry: ChestEntry) -> None:
        """
        Validate a single entry against validation lists.

        Args:
            entry (ChestEntry): Entry to validate
        """
        # Check each field
        for field in ["chest_type", "player", "source"]:
            field_value = entry.get_field(field)

            # Skip empty fields
            if not field_value:
                continue

            # Get validation list for this field
            validation_list = self._validation_lists.get(field)
            if not validation_list:
                continue

            # Validate the field
            is_valid, confidence, matched_value = validation_list.is_valid(field_value)

            # Update entry validation status
            if is_valid:
                if confidence == 1.0:
                    # Exact match
                    entry.set_field_validation(field, True)
                else:
                    # Fuzzy match
                    entry.set_field_validation(
                        field, True, confidence=confidence, fuzzy_match=matched_value
                    )
            else:
                entry.set_field_validation(field, False)

    def _on_selection_changed(self, selected, deselected) -> None:
        """
        Handle selection change in the table.

        Args:
            selected: The selected items
            deselected: The deselected items
        """
        # Get selected row
        indexes = selected.indexes()
        if not indexes:
            self._clear_details()
            return

        # Get entry ID from first column
        row = self._proxy_model.mapToSource(indexes[0]).row()
        if row < 0 or row >= len(self._entries):
            self._clear_details()
            return

        # Get entry and update details
        entry_id = self._model.data(self._model.index(row, 0))
        entry = self._get_entry_by_id(entry_id)
        if entry:
            self._update_details(entry)

    def _clear_details(self) -> None:
        """Clear the details panel."""
        self._entry_id_label.setText("")
        self._entry_name_label.setText("")
        self._entry_type_label.setText("")
        self._entry_player_label.setText("")
        self._entry_source_label.setText("")
        self._corrections_label.setText("No entry selected")

    def _update_details(self, entry: ChestEntry) -> None:
        """
        Update the details panel with entry information.

        Args:
            entry (ChestEntry): The entry to display
        """
        self._entry_id_label.setText(entry.id)
        self._entry_name_label.setText(entry.name)
        self._entry_type_label.setText(entry.chest_type)
        self._entry_player_label.setText(entry.player)
        self._entry_source_label.setText(entry.source)

        # Update corrections information
        if entry.has_corrections():
            corrections_text = ""
            for field, correction in entry.corrections.items():
                corrections_text += (
                    f"<b>{field}:</b> {correction.original} → {correction.corrected}<br>"
                )
            self._corrections_label.setText(corrections_text)
        else:
            # Check if the entry is valid
            if self._validation_lists:
                validation_result = self._validate_entry(entry)
                if validation_result["valid"]:
                    self._corrections_label.setText("Entry is valid")
                else:
                    issues = "<br>".join([f"- {issue}" for issue in validation_result["issues"]])
                    self._corrections_label.setText(f"Entry needs correction:<br>{issues}")
            else:
                self._corrections_label.setText("No corrections applied")

    def _connect_signals(self) -> None:
        """Connect UI signals to slots."""
        # Connect table selection
        selection_model = self._table_view.selectionModel()
        selection_model.selectionChanged.connect(self._on_selection_changed)

        # Connect filter controls
        self._type_filter.currentIndexChanged.connect(self._apply_filters)
        self._player_filter.currentIndexChanged.connect(self._apply_filters)
        self._source_filter.currentIndexChanged.connect(self._apply_filters)
        self._search_filter.textChanged.connect(self._apply_filters)

        # Connect buttons
        self._auto_correct_button.clicked.connect(self._auto_correct_entries)
        self._export_button.clicked.connect(self._export_corrected_entries)

        # Connect table headers for sorting
        self._table_view.horizontalHeader().sectionClicked.connect(
            lambda index: self._proxy_model.sort(index, self._proxy_model.sortOrder())
        )

    def _apply_settings(self) -> None:
        """Apply settings from configuration."""
        # Apply table columns
        show_ids = self._config.get_bool("Table", "show_ids", True)
        self._table_view.setColumnHidden(0, not show_ids)

        # Set table font size
        font_size = self._config.get_int("Table", "font_size", 10)
        font = self._table_view.font()
        font.setPointSize(font_size)
        self._table_view.setFont(font)

        # Set sort column
        sort_column = self._config.get_int("Table", "sort_column", 1)
        sort_order = Qt.SortOrder(self._config.get_int("Table", "sort_order", Qt.AscendingOrder))
        self._table_view.sortByColumn(sort_column, sort_order)

        # No more preview settings

    def _setup_table(self, layout: QVBoxLayout) -> None:
        """
        Set up the table for displaying chest entries.

        Args:
            layout (QVBoxLayout): Layout to add the table to
        """
        # Create table view
        self._table_view = QTableView()
        self._table_view.setSelectionBehavior(QTableView.SelectRows)
        self._table_view.setSelectionMode(QTableView.SingleSelection)
        self._table_view.setSortingEnabled(True)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.verticalHeader().setVisible(False)

        # Create table model
        self._table_model = ChestEntryTableModel()

        # Create proxy model for filtering
        self._proxy_model = ChestEntryFilterProxyModel()
        self._proxy_model.setSourceModel(self._table_model)

        # Set model on view
        self._table_view.setModel(self._proxy_model)

        # Connect selection changed signal
        self._table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # Add table to layout
        layout.addWidget(self._table_view)
