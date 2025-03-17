"""
correction_manager_panel.py

Description: Panel for managing correction rules and validation lists
Usage:
    from src.ui.correction_manager_panel import CorrectionManagerPanel
    panel = CorrectionManagerPanel(parent=self)
"""

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, Slot, QModelIndex
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QSplitter,
    QGroupBox,
    QLabel,
    QPushButton,
    QTableView,
    QHeaderView,
    QAbstractItemView,
    QLineEdit,
    QCheckBox,
    QTabWidget,
    QComboBox,
    QMessageBox,
    QMenu,
    QDialog,
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.models.validation_list import ValidationList
from src.ui.correction_rules_table import CorrectionRulesTable
from src.ui.validation_list_widget import ValidationListWidget
from src.ui.enhanced_table_view import EnhancedTableView


class CorrectionManagerPanel(QWidget):
    """
    Panel for managing correction rules and validation lists.

    This panel provides a UI for managing correction rules and validation
    lists. It has a split layout with correction tools on the left and
    entries on the right.

    Signals:
        correction_rules_updated: Signal emitted when correction rules are updated
        validation_lists_updated: Signal emitted when validation lists are updated
        entries_updated: Signal emitted when entries are updated

    Attributes:
        _correction_rules: List of correction rules
        _validation_lists: Dictionary of validation lists
        _entries: List of chest entries
    """

    # Signals
    correction_rules_updated = Signal(list)  # List[CorrectionRule]
    validation_lists_updated = Signal(dict)  # Dict[str, ValidationList]
    entries_updated = Signal(list)  # List[ChestEntry]

    def __init__(self, parent=None):
        """
        Initialize the correction manager panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize properties
        self._correction_rules: List[CorrectionRule] = []
        self._validation_lists: Dict[str, ValidationList] = {}
        self._entries: List[ChestEntry] = []

        # Get configuration manager
        from src.services.config_manager import ConfigManager

        self._config = ConfigManager()

        # Track the current file path
        self._current_file_path = None

        # Set up UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Add header with reduced size
        header_layout = QHBoxLayout()
        header_label = QLabel("Correction Manager")
        header_label.setObjectName("title")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Create splitter for left and right panels
        self._splitter = QSplitter(Qt.Horizontal)

        # Setup left panel (correction tools)
        self._setup_correction_tools_panel()

        # Setup right panel (entries table)
        self._setup_entries_panel()

        # Add splitter to main layout
        main_layout.addWidget(
            self._splitter, 1
        )  # Give stretch factor to make it take up available space

    def showEvent(self, event):
        """
        Handle the show event.

        This ensures the splitter is properly sized after the widget is shown.

        Args:
            event: Show event
        """
        super().showEvent(event)

        # Set splitter sizes to give 1/3 to left panel and 2/3 to right panel
        total_width = self.width()
        self._splitter.setSizes([total_width // 3, (total_width * 2) // 3])

    def _setup_entries_panel(self):
        """Set up the entries panel with the table of loaded entries."""
        # Create group box for entries
        entries_group = QGroupBox("Loaded Entries")
        entries_layout = QVBoxLayout(entries_group)

        # Create entries table
        self._entries_table = EnhancedTableView()

        # Connect entry selection and editing signals
        self._entries_table.entry_selected.connect(self._on_entry_selected)
        self._entries_table.entry_edited.connect(self._on_entry_edited)

        # Add the table to the layout
        entries_layout.addWidget(self._entries_table)

        # Add search field
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self._search_field = QLineEdit()
        self._search_field.setPlaceholderText("Search entries...")
        self._search_field.textChanged.connect(self._on_search_entries)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_field)
        entries_layout.addLayout(search_layout)

        # Add to splitter as the second (right) widget
        self._splitter.addWidget(entries_group)

    def _setup_correction_tools_panel(self):
        """Set up the left panel with correction tools."""
        # Create the left panel widget
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Create tabs for different tools
        self._tools_tabs = QTabWidget()

        # Create tab for correction rules
        self._correction_rules_tab = QWidget()
        self._setup_correction_rules_tab()
        self._tools_tabs.addTab(self._correction_rules_tab, "Correction Rules")

        # Create tab for validation lists
        self._validation_lists_tab = QWidget()
        self._setup_validation_lists_tab()
        self._tools_tabs.addTab(self._validation_lists_tab, "Validation Lists")

        # Add tabs to layout
        left_layout.addWidget(self._tools_tabs)

        # Add to splitter as the first (left) widget
        self._splitter.addWidget(left_panel)

    def _setup_correction_rules_tab(self):
        """Set up the correction rules tab."""
        # Create tab content
        rules_tab = QWidget()
        rules_layout = QVBoxLayout(rules_tab)
        rules_layout.setContentsMargins(0, 0, 0, 0)

        # Add header with tools
        tools_layout = QHBoxLayout()
        tools_layout.setContentsMargins(5, 5, 5, 5)

        # Search field
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        search_layout.addWidget(QLabel("Search:"))

        self._search_field = QLineEdit()
        self._search_field.setPlaceholderText("Filter rules...")
        self._search_field.setMaximumWidth(200)
        search_layout.addWidget(self._search_field)

        tools_layout.addLayout(search_layout)
        tools_layout.addStretch()

        # Import/export buttons
        import_button = QPushButton("Import")
        import_button.setToolTip("Import correction rules from a file")
        import_button.clicked.connect(self._on_import_rules)
        tools_layout.addWidget(import_button)

        export_button = QPushButton("Export")
        export_button.setToolTip("Export correction rules to a file")
        export_button.clicked.connect(self._on_export_rules)
        tools_layout.addWidget(export_button)

        # Add button
        add_button = QPushButton("Add Rule")
        add_button.setToolTip("Add a new correction rule")
        add_button.clicked.connect(self._on_add_rule)
        tools_layout.addWidget(add_button)

        rules_layout.addLayout(tools_layout)

        # Add correction rules table
        self._correction_rules_table = CorrectionRulesTable()
        rules_layout.addWidget(self._correction_rules_table)

        # Connect signals
        self._search_field.textChanged.connect(self._on_search_text_changed)
        self._correction_rules_table.file_path_changed.connect(self._on_file_path_changed)

        # Store the tab widget for later reference
        self._correction_rules_tab = rules_tab

    def _setup_validation_lists_tab(self):
        """Set up the validation lists tab."""
        # Create layout for validation lists tab
        layout = QVBoxLayout(self._validation_lists_tab)

        # Create tabs for different validation list types
        self._validation_tabs = QTabWidget()

        # Create validation list widgets
        self._player_list_widget = ValidationListWidget("Players")
        self._chest_type_list_widget = ValidationListWidget("Chest Types")
        self._source_list_widget = ValidationListWidget("Sources")

        # Add tabs
        self._validation_tabs.addTab(self._player_list_widget, "Players")
        self._validation_tabs.addTab(self._chest_type_list_widget, "Chest Types")
        self._validation_tabs.addTab(self._source_list_widget, "Sources")

        # Add to main layout
        layout.addWidget(self._validation_tabs)

        # Connect signals
        self._player_list_widget.list_updated.connect(self._on_player_list_updated)
        self._chest_type_list_widget.list_updated.connect(self._on_chest_type_list_updated)
        self._source_list_widget.list_updated.connect(self._on_source_list_updated)

    @Slot()
    def _on_add_rule(self):
        """Handle add rule button click."""
        self._correction_rules_table.add_rule()

    @Slot()
    def _on_edit_rule(self):
        """Handle edit rule button click."""
        selected_rows = self._correction_rules_table.selectionModel().selectedRows()
        if selected_rows:
            self._correction_rules_table.edit_rule(selected_rows[0].row())

    @Slot()
    def _on_delete_rule(self):
        """Handle delete rule button click."""
        selected_rows = self._correction_rules_table.selectionModel().selectedRows()
        if selected_rows:
            self._correction_rules_table.delete_rule(selected_rows[0].row())

    @Slot()
    def _on_import_rules(self):
        """Handle import rules button click."""
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Importing correction rules")

        # Delegate to the correction rules table
        imported_rules = self._correction_rules_table.import_rules()

        # If import was cancelled or failed, do nothing
        if imported_rules is None:
            logger.info("Import cancelled or failed")
            return

        # Update our local copy
        self._correction_rules = imported_rules
        logger.info(f"Successfully imported {len(imported_rules)} rules")

        # Store current file path if it exists in the table
        if (
            hasattr(self._correction_rules_table, "_current_file_path")
            and self._correction_rules_table._current_file_path
        ):
            self._current_file_path = self._correction_rules_table._current_file_path

            # Save to config if available
            if hasattr(self, "_config") and self._config:
                self._config.set("General", "last_correction_file", str(self._current_file_path))

        # Ensure the correction rules tab is visible
        self._tools_tabs.setCurrentIndex(0)

        # Notify Dashboard
        logger.info(f"Emitting correction_rules_updated signal with {len(imported_rules)} rules")
        self.correction_rules_updated.emit(imported_rules)

    @Slot()
    def _on_export_rules(self):
        """Handle export rules button click."""
        self._correction_rules_table.export_rules()

    @Slot(str)
    def _on_search_rules(self, text: str):
        """
        Handle search text changed for rules.

        Args:
            text: Search text
        """
        self._correction_rules_table.filter_rules(text)

    @Slot(str)
    def _on_search_entries(self, text: str):
        """
        Handle search text changed for entries.

        Args:
            text: Search text
        """
        if hasattr(self._entries_table, "filter_entries"):
            self._entries_table.filter_entries(text)

    @Slot(int)
    def _on_toggle_all_rules(self, state: int):
        """
        Handle toggle all rules checkbox changed.

        Args:
            state: Checkbox state
        """
        enabled = state == Qt.Checked
        self._correction_rules_table.set_all_rules_enabled(enabled)

    @Slot()
    def _on_rule_selection_changed(self):
        """Handle rule selection changed."""
        selected_rows = self._correction_rules_table.selectionModel().selectedRows()
        self._edit_rule_button.setEnabled(len(selected_rows) > 0)
        self._delete_rule_button.setEnabled(len(selected_rows) > 0)

    @Slot(object)
    def _on_player_list_updated(self, player_list: ValidationList):
        """
        Handle player list updated.

        Args:
            player_list: Updated player list
        """
        self._validation_lists["player"] = player_list
        self._emit_validation_lists_updated()

    @Slot(object)
    def _on_chest_type_list_updated(self, chest_type_list: ValidationList):
        """
        Handle chest type list updated.

        Args:
            chest_type_list: Updated chest type list
        """
        self._validation_lists["chest_type"] = chest_type_list
        self._emit_validation_lists_updated()

    @Slot(object)
    def _on_source_list_updated(self, source_list: ValidationList):
        """
        Handle source list updated.

        Args:
            source_list: Updated source list
        """
        self._validation_lists["source"] = source_list
        self._emit_validation_lists_updated()

    def _emit_validation_lists_updated(self):
        """Emit validation lists updated signal."""
        self.validation_lists_updated.emit(self._validation_lists)

    @Slot(object)
    def _on_entry_selected(self, entry: ChestEntry):
        """
        Handle entry selection.

        Args:
            entry: Selected entry
        """
        self._create_rule_button.setEnabled(True)

    @Slot(object)
    def _on_entry_edited(self, entry: ChestEntry):
        """
        Handle entry edited.

        Args:
            entry: Edited entry
        """
        # Update the entries list
        for i, e in enumerate(self._entries):
            if (
                e == entry
            ):  # Using equality comparison (may need to be modified based on how ChestEntry equality is defined)
                self._entries[i] = entry
                break

        # Emit the entries updated signal
        self.entries_updated.emit(self._entries)

        # Ask if user wants to create a correction rule for this edit
        if entry.has_corrections():
            field = None
            original = None
            corrected = None

            # Find the field that was edited
            for field_name, original_value in entry.original_values.items():
                current_value = getattr(entry, field_name)
                if original_value != current_value:
                    field = field_name
                    original = original_value
                    corrected = current_value
                    break

            if field and original and corrected:
                # Ask if user wants to create a rule
                response = QMessageBox.question(
                    self,
                    "Create Correction Rule",
                    f"Do you want to create a correction rule for this change?\n\n"
                    f"Original: {original}\n"
                    f"Corrected: {corrected}\n"
                    f"Field: {field}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if response == QMessageBox.Yes:
                    # Map field to category
                    field_to_category = {
                        "chest_type": "chest",
                        "player": "player",
                        "source": "source",
                    }
                    category = field_to_category.get(field, "general")

                    # Create the rule
                    self._correction_rules_table.create_rule_from_entry(
                        original, corrected, category
                    )

                    # Switch to the correction rules tab
                    self._tools_tabs.setCurrentIndex(0)

    @Slot()
    def _on_create_rule_from_selection(self):
        """Handle create rule from selection button click."""
        # Get the selected entry
        entry = self._entries_table.get_selected_entry()
        if not entry:
            return

        # Show a dialog to let the user choose what to correct
        dialog = CreateRuleDialog(entry, self)
        if dialog.exec():
            original, corrected, category = dialog.get_values()
            if original and corrected and category:
                # Create the rule
                self._correction_rules_table.create_rule_from_entry(original, corrected, category)

                # Switch to the correction rules tab
                self._tools_tabs.setCurrentIndex(0)

    def set_correction_rules(self, rules: List[CorrectionRule]):
        """
        Set the correction rules.

        Args:
            rules: List of correction rules
        """
        import logging
        from pathlib import Path

        logger = logging.getLogger(__name__)
        logger.info(f"CorrectionManagerPanel.set_correction_rules called with {len(rules)} rules")

        if not rules:
            logger.warning("Empty rules list passed to set_correction_rules")
            return

        # Check if rules are already set and unchanged
        if self._correction_rules == rules:
            logger.info("Rules are unchanged, no need to update")
            # Still make sure the tab is visible
            if self._tools_tabs.currentIndex() != 0:
                self._tools_tabs.setCurrentIndex(0)
            return

        # Log some rules for debugging
        for i, rule in enumerate(rules[:5]):  # Log first 5 rules for debugging
            logger.info(
                f"Panel Rule {i}: {rule.from_text} -> {rule.to_text} (category: {rule.category})"
            )

        # Store the rules locally
        self._correction_rules = rules

        # Set rules in the table - this will update the display
        self._correction_rules_table.set_rules(rules)

        # Make sure table is visible and the rules tab is active
        if self._tools_tabs.currentIndex() != 0:  # If not on correction rules tab
            logger.info("Switching to correction rules tab")
            self._tools_tabs.setCurrentIndex(0)

        # Update the count in the tab text
        self._tools_tabs.setTabText(0, f"Correction Rules ({len(rules)})")

        # Check if we have a current file path and update config
        if hasattr(self, "_current_file_path") and self._current_file_path:
            file_path = str(self._current_file_path)
            folder_path = str(Path(file_path).parent)

            # Update all config settings to ensure consistency
            self._config.set("General", "last_correction_file", file_path)
            self._config.set("General", "last_folder", folder_path)
            self._config.set("Files", "last_correction_directory", folder_path)
            self._config.set("Paths", "default_correction_rules", file_path)

            # Save changes to disk
            self._config.save()
            logger.info(f"Saved config with correction file: {file_path}")

        # Apply table update and make sure it's visually updated
        self._correction_rules_table.reset()
        self._correction_rules_table.resizeColumnsToContents()
        self._correction_rules_table.resizeRowsToContents()

        # Make sure the table has the right size
        self._correction_rules_table.setMinimumHeight(400)

        # Update status message if parent has status bar
        if self.parent() and hasattr(self.parent(), "statusBar"):
            self.parent().statusBar().showMessage(f"Loaded {len(rules)} correction rules", 3000)

        # Emit signal - but only emit if we weren't called from the Dashboard
        # to avoid signal loops
        parent_is_setting_rules = False
        try:
            parent_is_setting_rules = getattr(self.parent(), "_processing_signal", False)
        except (AttributeError, Exception):
            pass

        if not parent_is_setting_rules:
            logger.info(f"Emitting correction_rules_updated signal with {len(rules)} rules")
            self.correction_rules_updated.emit(rules)

    @Slot(dict)
    def set_validation_lists(self, lists: Dict[str, ValidationList]):
        """
        Set the validation lists.

        Args:
            lists: Dictionary of validation lists
        """
        self._validation_lists = lists

        # Update the validation list widgets
        if "player" in lists:
            self._player_list_widget.set_list(lists["player"])

        if "chest_type" in lists:
            self._chest_type_list_widget.set_list(lists["chest_type"])

        if "source" in lists:
            self._source_list_widget.set_list(lists["source"])

        self.validation_lists_updated.emit(lists)

    def get_correction_rules(self) -> List[CorrectionRule]:
        """
        Get the correction rules.

        Returns:
            List of correction rules
        """
        return self._correction_rules_table.get_rules()

    def get_validation_lists(self) -> Dict[str, ValidationList]:
        """
        Get the validation lists.

        Returns:
            Dictionary of validation lists
        """
        return self._validation_lists

    def set_entries(self, entries):
        """
        Set the entries to be displayed in the table.

        Args:
            entries: List of entries
        """
        self._entries = entries
        self._entries_table.set_entries(entries)

        # No need to update a button that doesn't exist
        # self._create_rule_button.setEnabled(False)

    @Slot(str)
    def _on_file_path_changed(self, file_path):
        """
        Handle file path changed signal.

        Args:
            file_path: The new file path
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"CorrectionManagerPanel received file_path_changed: {file_path}")

        # Store the path
        self._current_file_path = file_path

    @Slot(str)
    def _on_search_text_changed(self, text):
        """
        Handle search text changed.

        Args:
            text: The search text
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(f"Search text changed: {text}")

        # Apply filter to the rules table
        if hasattr(self, "_correction_rules_table"):
            self._correction_rules_table.filter_rules(text)


class CreateRuleDialog(QDialog):
    """
    Dialog for creating a correction rule from an entry.
    """

    def __init__(self, entry: ChestEntry, parent=None):
        """
        Initialize the dialog.

        Args:
            entry: Entry to create rule from
            parent: Parent widget
        """
        super().__init__(parent)

        self._entry = entry
        self._original = ""
        self._corrected = ""
        self._category = "general"

        self.setWindowTitle("Create Correction Rule")
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create form layout
        form_layout = QVBoxLayout()

        # Field selector
        field_layout = QHBoxLayout()
        field_label = QLabel("Field:")
        self._field_combo = QComboBox()
        self._field_combo.addItems(["chest_type", "player", "source"])
        self._field_combo.currentIndexChanged.connect(self._on_field_changed)

        field_layout.addWidget(field_label)
        field_layout.addWidget(self._field_combo)

        # Original text
        original_label = QLabel("Original Text:")
        self._original_edit = QLineEdit()

        # Corrected text
        corrected_label = QLabel("Corrected Text:")
        self._corrected_edit = QLineEdit()

        # Add to form layout
        form_layout.addLayout(field_layout)
        form_layout.addWidget(original_label)
        form_layout.addWidget(self._original_edit)
        form_layout.addWidget(corrected_label)
        form_layout.addWidget(self._corrected_edit)

        # Add form layout to main layout
        layout.addLayout(form_layout)

        # Add buttons
        button_layout = QHBoxLayout()
        self._ok_button = QPushButton("Create Rule")
        self._cancel_button = QPushButton("Cancel")

        self._ok_button.clicked.connect(self.accept)
        self._cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self._ok_button)
        button_layout.addWidget(self._cancel_button)

        layout.addLayout(button_layout)

        # Initialize fields
        self._on_field_changed(0)

    def _on_field_changed(self, index):
        """
        Handle field selection changed.

        Args:
            index: Index of selected field
        """
        field = self._field_combo.currentText()

        # Update field values
        self._original_edit.setText(getattr(self._entry, field, ""))
        self._corrected_edit.setText("")

        # Update category
        field_to_category = {"chest_type": "chest", "player": "player", "source": "source"}
        self._category = field_to_category.get(field, "general")

    def accept(self):
        """Handle dialog acceptance."""
        # Validate fields
        original = self._original_edit.text().strip()
        corrected = self._corrected_edit.text().strip()

        if not original:
            QMessageBox.warning(self, "Validation Error", "Original text cannot be empty.")
            return

        if not corrected:
            QMessageBox.warning(self, "Validation Error", "Corrected text cannot be empty.")
            return

        if original == corrected:
            QMessageBox.warning(
                self, "Validation Error", "Original and corrected text must be different."
            )
            return

        # Store values
        self._original = original
        self._corrected = corrected

        super().accept()

    def get_values(self) -> Tuple[str, str, str]:
        """
        Get the dialog values.

        Returns:
            Tuple of (original, corrected, category)
        """
        return self._original, self._corrected, self._category
