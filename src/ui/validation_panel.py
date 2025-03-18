"""
validation_panel.py

Description: Panel for managing validation lists
Usage:
    from src.ui.validation_panel import ValidationPanel
    validation_panel = ValidationPanel(parent=self)
"""

from pathlib import Path
from typing import Dict, List, Optional, Set

from PySide6.QtCore import QSize, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QSlider,
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.models.validation_list import ValidationList
from src.services.config_manager import ConfigManager


class ValidationPanel(QWidget):
    """
    Panel for managing validation lists.

    Provides UI for creating, editing, and saving validation lists for
    chest types, players, and sources.

    Attributes:
        validation_lists_updated (Signal): Signal emitted when validation lists are updated
        validation_errors_updated (Signal): Signal emitted when validation errors are updated

    Implementation Notes:
        - Uses tabs for different list types
        - Provides list view with add/remove controls
        - Supports import/export to CSV
    """

    validation_lists_updated = Signal(dict)  # Dict[str, ValidationList]
    validation_errors_updated = Signal(list)  # List of entries with validation errors

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the validation panel.

        Args:
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)

        # Initialize data
        self._config = ConfigManager()
        self._validation_lists: Dict[str, ValidationList] = {
            "player": ValidationList(list_type="player", name="Default Player List"),
            "chest_type": ValidationList(list_type="chest_type", name="Default Chest Type List"),
            "source": ValidationList(list_type="source", name="Default Source List"),
        }
        self._entries: List[ChestEntry] = []
        self._correction_rules: List[CorrectionRule] = []

        # Setup UI
        self._setup_ui()

        # Load any existing validation lists from config
        self._load_validation_lists_from_config()

        # Apply fuzzy matching settings
        self._apply_fuzzy_settings()

        # Emit signal to share validation lists with other components
        self.validation_lists_updated.emit(self._validation_lists)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create tab widget
        self._tab_widget = QTabWidget()

        # Create tabs for each validation list type
        self._setup_player_tab()
        self._setup_chest_type_tab()
        self._setup_source_tab()

        # Add tab widget to layout
        main_layout.addWidget(self._tab_widget)

        # Add fuzzy matching controls
        self._setup_fuzzy_controls(main_layout)

    def _setup_player_tab(self) -> None:
        """Set up the player validation tab."""
        self._setup_validation_tab("player", "Player Validation")

    def _setup_chest_type_tab(self) -> None:
        """Set up the chest type validation tab."""
        self._setup_validation_tab("chest_type", "Chest Type Validation")

    def _setup_source_tab(self) -> None:
        """Set up the source validation tab."""
        self._setup_validation_tab("source", "Source Validation")

    def _setup_validation_tab(self, list_type: str, tab_title: str) -> None:
        """
        Set up a validation tab.

        Args:
            list_type (str): The validation list type
            tab_title (str): The tab title
        """
        # Create tab widget
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # List name group
        name_group = QGroupBox("List Name")
        name_layout = QHBoxLayout(name_group)

        self._name_edit = QLineEdit()
        self._name_edit.setObjectName(f"{list_type}_name_edit")
        self._name_edit.setText(self._validation_lists[list_type].name)
        self._name_edit.textChanged.connect(lambda text: self._on_name_changed(list_type, text))

        name_layout.addWidget(self._name_edit)

        # Add to tab layout
        tab_layout.addWidget(name_group)

        # Create splitter for list and controls
        splitter = QSplitter(Qt.Horizontal)

        # Entries list
        list_widget = QListWidget()
        list_widget.setObjectName(f"{list_type}_list_widget")
        list_widget.setSelectionMode(QListWidget.ExtendedSelection)

        # Add existing entries
        for entry in self._validation_lists[list_type].get_entries():
            list_widget.addItem(entry)

        # Controls group
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)

        # Add entry group
        add_group = QGroupBox("Add Entry")
        add_layout = QVBoxLayout(add_group)

        # Entry input and add button
        entry_layout = QHBoxLayout()
        entry_edit = QLineEdit()
        entry_edit.setObjectName(f"{list_type}_entry_edit")
        entry_edit.setPlaceholderText("Enter new entry...")

        add_button = QPushButton("Add")
        add_button.clicked.connect(lambda: self._add_entry(list_type, entry_edit.text()))

        entry_layout.addWidget(entry_edit)
        entry_layout.addWidget(add_button)

        # Add to add group
        add_layout.addLayout(entry_layout)

        # Remove button
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(lambda: self._remove_selected_entries(list_type, list_widget))

        # Clear button
        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(lambda: self._clear_entries(list_type, list_widget))

        # Add to controls layout
        controls_layout.addWidget(add_group)
        controls_layout.addWidget(remove_button)
        controls_layout.addWidget(clear_button)

        # Import/Export group
        io_group = QGroupBox("Import/Export")
        io_layout = QVBoxLayout(io_group)

        # Import button
        import_button = QPushButton("Import from CSV...")
        import_button.clicked.connect(lambda: self._import_list(list_type, list_widget))

        # Export button
        export_button = QPushButton("Export to CSV...")
        export_button.clicked.connect(lambda: self._export_list(list_type))

        # Add to IO layout
        io_layout.addWidget(import_button)
        io_layout.addWidget(export_button)

        # Add IO group to controls layout
        controls_layout.addWidget(io_group)

        # Spacer
        controls_layout.addStretch()

        # Add widgets to splitter
        splitter.addWidget(list_widget)
        splitter.addWidget(controls_widget)

        # Set initial splitter sizes
        splitter.setSizes([200, 100])

        # Add splitter to tab layout
        tab_layout.addWidget(splitter)

        # Add tab to tab widget
        self._tab_widget.addTab(tab, tab_title)

        # Store list widget reference
        setattr(self, f"_{list_type}_list_widget", list_widget)

    def _on_name_changed(self, list_type: str, name: str) -> None:
        """
        Handle name changes.

        Args:
            list_type (str): The validation list type
            name (str): The new name
        """
        self._validation_lists[list_type].name = name
        self._save_validation_lists_to_config()

    def _add_entry(self, list_type: str, entry: str) -> None:
        """
        Add an entry to a validation list.

        Args:
            list_type (str): The validation list type
            entry (str): The entry to add
        """
        if not entry.strip():
            return

        # Add to validation list
        self._validation_lists[list_type].add_entry(entry)

        # Update list widget
        list_widget = getattr(self, f"_{list_type}_list_widget")

        # Check if item already exists
        found = False
        for i in range(list_widget.count()):
            if list_widget.item(i).text() == entry:
                found = True
                break

        if not found:
            list_widget.addItem(entry)

        # Clear the entry edit
        entry_edit = self.findChild(QLineEdit, f"{list_type}_entry_edit")
        if entry_edit:
            entry_edit.clear()

        # Save to config
        self._save_validation_lists_to_config()

        # Emit signal
        self.validation_lists_updated.emit(self._validation_lists)

    def _remove_selected_entries(self, list_type: str, list_widget: QListWidget) -> None:
        """
        Remove selected entries from a validation list.

        Args:
            list_type (str): The validation list type
            list_widget (QListWidget): The list widget
        """
        selected_items = list_widget.selectedItems()

        if not selected_items:
            return

        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_items)} entries?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        # Remove from validation list and list widget
        for item in selected_items:
            self._validation_lists[list_type].remove_entry(item.text())
            row = list_widget.row(item)
            list_widget.takeItem(row)

        # Save to config
        self._save_validation_lists_to_config()

        # Emit signal
        self.validation_lists_updated.emit(self._validation_lists)

    def _clear_entries(self, list_type: str, list_widget: QListWidget) -> None:
        """
        Clear all entries from a validation list.

        Args:
            list_type (str): The validation list type
            list_widget (QListWidget): The list widget
        """
        if list_widget.count() == 0:
            return

        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to clear all {list_widget.count()} entries?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        # Clear validation list and list widget
        self._validation_lists[list_type].clear()
        list_widget.clear()

        # Save to config
        self._save_validation_lists_to_config()

        # Emit signal
        self.validation_lists_updated.emit(self._validation_lists)

    def _import_list(self, list_type: str, list_widget: QListWidget) -> None:
        """
        Import a validation list from a file.

        Args:
            list_type (str): The validation list type
            list_widget (QListWidget): The list widget
        """
        # Get default directory
        default_dir = self._config.get(
            "Files", "default_validation_dir", fallback="data/validation"
        )

        file_filter = "All Files (*.*)"
        if list_type == "player":
            file_filter = "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)"
        else:
            file_filter = "CSV Files (*.csv);;Text Files (*.txt);;All Files (*.*)"

        # Get file path
        file_path, selected_filter = QFileDialog.getOpenFileName(
            self,
            f"Import {list_type.capitalize()} List",
            default_dir,
            file_filter,
        )

        if not file_path:
            return

        try:
            # Save the directory
            self._config.set("Files", "default_validation_dir", str(Path(file_path).parent))
            self._config.save()

            # Log import attempt
            logging.info(f"Importing {list_type} list from: {file_path}")

            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext == ".txt" and list_type == "player":
                logging.info(f"Detected text file for player list: {file_path}")

            # Load validation list - explicitly passing list_type for text files
            validation_list = ValidationList.load_from_file(file_path, list_type=list_type)

            logging.info(f"Loaded {list_type} list with {validation_list.count()} entries")

            # Update list
            self._validation_lists[list_type] = validation_list

            # Update name edit
            name_edit = self.findChild(QLineEdit, f"{list_type}_name_edit")
            if name_edit:
                name_edit.setText(validation_list.name)

            # Update list widget
            list_widget.clear()
            for entry in validation_list.get_entries():
                list_widget.addItem(entry)

            # Save to config
            self._save_validation_lists_to_config()

            # Emit signal to notify corrector panels
            self.validation_lists_updated.emit(self._validation_lists)

            # Show success message
            QMessageBox.information(
                self,
                "Import Successful",
                f"{list_type.capitalize()} list successfully imported from {file_path} with {validation_list.count()} entries.",
            )

        except Exception as e:
            # Show error message
            QMessageBox.critical(self, "Import Error", f"Error importing {list_type} list: {e}")
            logging.error(f"Error importing {list_type} list: {str(e)}", exc_info=True)

    def _export_list(self, list_type: str) -> None:
        """
        Export a validation list to a CSV file.

        Args:
            list_type (str): The validation list type
        """
        # Get default directory
        default_dir = self._config.get(
            "Files", "default_validation_dir", fallback="data/validation"
        )

        # Make sure the directory exists
        Path(default_dir).mkdir(parents=True, exist_ok=True)

        # Create default filename
        default_filename = (
            f"{list_type}_{self._validation_lists[list_type].name.lower().replace(' ', '_')}.csv"
        )
        default_path = str(Path(default_dir) / default_filename)

        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Validation List", default_path, "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            # Save the directory
            self._config.set("Files", "default_validation_dir", str(Path(file_path).parent))
            self._config.save()

            # Save validation list - pass the string path directly
            self._validation_lists[list_type].save_to_file(file_path)

            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Validation list successfully exported to {file_path}.",
            )

        except Exception as e:
            # Show error message
            QMessageBox.critical(self, "Export Error", f"Error exporting validation list: {e}")
            logging.error(f"Error exporting validation list: {str(e)}", exc_info=True)

    def _save_validation_lists_to_config(self) -> None:
        """Save validation lists to configuration."""
        # Get validation directory
        validation_dir = Path(
            self._config.get("Files", "default_validation_dir", fallback="data/validation")
        )

        # Make sure the directory exists
        validation_dir.mkdir(parents=True, exist_ok=True)

        # Save validation lists and update config
        for list_type, validation_list in self._validation_lists.items():
            if validation_list.count() > 0:
                try:
                    # Create filename
                    filename = f"{list_type}_default.csv"
                    file_path = validation_dir / filename

                    # Save validation list
                    validation_list.save_to_file(file_path)

                    # Update config
                    self._config.set("Validation", f"validation_{list_type}_list", str(file_path))
                except Exception as e:
                    print(f"Error saving validation list: {e}")

        # Save config
        self._config.save()

    def _load_validation_lists_from_config(self) -> None:
        """Load validation lists from configuration."""
        lists_loaded = False

        for list_type in ["player", "chest_type", "source"]:
            # Get validation list path
            list_path = self._config.get("Validation", f"validation_{list_type}_list", fallback="")

            if list_path and Path(list_path).exists():
                try:
                    # Load validation list
                    validation_list = ValidationList.load_from_file(Path(list_path))

                    # Update list
                    self._validation_lists[list_type] = validation_list
                    lists_loaded = True

                    # Update UI if initialized
                    if hasattr(self, f"_{list_type}_list_widget"):
                        # Update name edit
                        name_edit = self.findChild(QLineEdit, f"{list_type}_name_edit")
                        if name_edit:
                            name_edit.setText(validation_list.name)

                        # Update list widget
                        list_widget = getattr(self, f"_{list_type}_list_widget")
                        list_widget.clear()
                        for entry in validation_list.get_entries():
                            list_widget.addItem(entry)
                except Exception as e:
                    print(f"Error loading validation list: {e}")

        # If any lists were loaded, emit signal to update other components
        if lists_loaded:
            print(f"Validation lists loaded from config: {len(self._validation_lists)} lists")
            self.validation_lists_updated.emit(self._validation_lists)

    def get_validation_lists(self) -> Dict[str, ValidationList]:
        """
        Get the validation lists.

        Returns:
            Dict[str, ValidationList]: The validation lists
        """
        return self._validation_lists.copy()

    def _setup_fuzzy_controls(self, layout: QVBoxLayout) -> None:
        """
        Set up fuzzy matching controls.

        Args:
            layout (QVBoxLayout): Layout to add controls to
        """
        # Create group box
        fuzzy_group = QGroupBox("Fuzzy Matching")
        fuzzy_layout = QVBoxLayout(fuzzy_group)

        # Create enable checkbox
        self._enable_fuzzy_checkbox = QCheckBox("Enable fuzzy matching for validation")
        self._enable_fuzzy_checkbox.setChecked(
            self._config.get_bool("Validation", "enable_fuzzy_matching", fallback=False)
        )
        self._enable_fuzzy_checkbox.stateChanged.connect(self._on_fuzzy_enabled_changed)
        fuzzy_layout.addWidget(self._enable_fuzzy_checkbox)

        # Create threshold slider
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Match Threshold:")
        threshold_layout.addWidget(threshold_label)

        self._fuzzy_threshold_slider = QSlider(Qt.Horizontal)
        self._fuzzy_threshold_slider.setMinimum(50)
        self._fuzzy_threshold_slider.setMaximum(100)
        self._fuzzy_threshold_slider.setValue(
            self._config.get_int("Validation", "fuzzy_threshold", fallback=75)
        )
        self._fuzzy_threshold_slider.setTickInterval(5)
        self._fuzzy_threshold_slider.setTickPosition(QSlider.TicksBelow)
        self._fuzzy_threshold_slider.valueChanged.connect(self._on_fuzzy_threshold_changed)
        threshold_layout.addWidget(self._fuzzy_threshold_slider)

        self._fuzzy_threshold_label = QLabel(f"{self._fuzzy_threshold_slider.value()}%")
        self._fuzzy_threshold_slider.valueChanged.connect(
            lambda value: self._fuzzy_threshold_label.setText(f"{value}%")
        )
        threshold_layout.addWidget(self._fuzzy_threshold_label)

        fuzzy_layout.addLayout(threshold_layout)

        # Add description
        description = QLabel(
            "Fuzzy matching allows validation against similar but not exact matches.\n"
            "Higher threshold means stricter matching (fewer matches)."
        )
        description.setWordWrap(True)
        fuzzy_layout.addWidget(description)

        # Add to main layout
        layout.addWidget(fuzzy_group)

    def _on_fuzzy_enabled_changed(self, state: int) -> None:
        """
        Handle fuzzy matching enabled state change.

        Args:
            state (int): Checkbox state
        """
        enabled = state == Qt.Checked
        self._config.set("Validation", "enable_fuzzy_matching", enabled)

        # Update all validation lists
        for validation_list in self._validation_lists.values():
            validation_list.use_fuzzy_matching = enabled

        # Emit signal to update other components
        self.validation_lists_updated.emit(self._validation_lists)

    def _on_fuzzy_threshold_changed(self, value: int) -> None:
        """
        Handle fuzzy threshold change.

        Args:
            value (int): New threshold value
        """
        self._config.set("Validation", "fuzzy_threshold", value)
        threshold = value / 100.0

        # Update all validation lists
        for validation_list in self._validation_lists.values():
            validation_list.update_fuzzy_threshold(threshold)

        # Emit signal to update other components
        self.validation_lists_updated.emit(self._validation_lists)

    def _apply_fuzzy_settings(self) -> None:
        """Apply current fuzzy matching settings to validation lists."""
        enable_fuzzy = self._config.get_bool("Validation", "enable_fuzzy_matching", fallback=False)
        threshold = self._config.get_int("Validation", "fuzzy_threshold", fallback=75) / 100.0

        for validation_list in self._validation_lists.values():
            validation_list.use_fuzzy_matching = enable_fuzzy
            validation_list.update_fuzzy_threshold(threshold)

    @Slot(list)
    def set_entries(self, entries: List[ChestEntry]):
        """
        Set the current entries.

        Args:
            entries (List[ChestEntry]): The entries to set
        """
        # Store the entries for validation
        self._entries = entries

    @Slot(list)
    def set_correction_rules(self, rules: List[CorrectionRule]):
        """
        Set the current correction rules.

        Args:
            rules (List[CorrectionRule]): The correction rules to set
        """
        # Store the correction rules
        self._correction_rules = rules

    @Slot(dict)
    def set_validation_lists(self, lists: Dict[str, ValidationList]):
        """
        Set the current validation lists.

        Args:
            lists (Dict[str, ValidationList]): The validation lists to set
        """
        # Update the validation lists
        self._validation_lists = lists
