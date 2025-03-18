"""
correction_manager_panel.py

Description: Panel for managing correction rules and validation lists
Usage:
    from src.ui.correction_manager_panel import CorrectionManagerPanel
    panel = CorrectionManagerPanel(parent=self)
"""

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, Slot, QModelIndex, QTimer
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
        self._processing_signal = False

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
        # Create layout for the tab
        layout = QVBoxLayout(self._correction_rules_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add header with tools
        tools_layout = QHBoxLayout()
        tools_layout.setContentsMargins(5, 5, 5, 5)

        # Search field
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        search_layout.addWidget(QLabel("Search:"))

        self._rules_search_field = QLineEdit()
        self._rules_search_field.setPlaceholderText("Filter rules...")
        self._rules_search_field.setMaximumWidth(200)
        search_layout.addWidget(self._rules_search_field)

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

        layout.addLayout(tools_layout)

        # Add correction rules table
        self._correction_rules_table = CorrectionRulesTable()
        layout.addWidget(self._correction_rules_table)

        # Connect signals
        self._rules_search_field.textChanged.connect(self._on_search_text_changed)
        self._correction_rules_table.file_path_changed.connect(self._on_file_path_changed)

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

        # Prevent recursive signal processing
        if getattr(self, "_processing_signal", False):
            logger.warning("Already processing signal, skipping duplicate call")
            return

        try:
            # Set processing flag
            self._processing_signal = True

            # Store the rules locally
            self._correction_rules = rules.copy()

            # Set rules in the table - this will update the display
            if hasattr(self, "_correction_rules_table"):
                logger.info("Setting rules in correction rules table")
                self._correction_rules_table.set_rules(rules)

                # Force a reset and update of the table
                self._correction_rules_table.reset()
                self._correction_rules_table.viewport().update()

            # Make sure the correction tab is visible if we're currently displayed
            if self.isVisible() and hasattr(self, "_tools_tabs"):
                logger.info("Making correction rules tab active")

                # Set the tab as active
                self._tools_tabs.setCurrentIndex(0)

                # Update the tab text
                tab_text = f"Correction Rules ({len(rules)})"
                self._tools_tabs.setTabText(0, tab_text)

            # Emit signal to notify other components
            logger.info(f"Emitting correction_rules_updated signal with {len(rules)} rules")
            self.correction_rules_updated.emit(rules)

            # Update status message
            if self.parent() and hasattr(self.parent(), "statusBar"):
                status_bar = self.parent().statusBar()
                if status_bar:
                    status_bar.showMessage(f"Loaded {len(rules)} correction rules", 3000)

        except Exception as e:
            logger.error(f"Error in set_correction_rules: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
        finally:
            # Always reset processing flag
            self._processing_signal = False

    @Slot(dict)
    def set_validation_lists(self, lists: Dict[str, ValidationList]):
        """
        Set the validation lists.

        Args:
            lists: Dictionary of validation lists
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"CorrectionManagerPanel.set_validation_lists called with {len(lists)} lists")

        # Add signal loop prevention
        if getattr(self, "_processing_signal", False):
            logger.warning("Skipping due to signal loop prevention")
            return

        try:
            self._processing_signal = True

            if not lists:
                logger.warning("Empty validation lists passed")
                return

            # Store the lists locally
            self._validation_lists = lists

            # Log the lists for debugging
            for list_type, validation_list in lists.items():
                logger.info(
                    f"Setting {list_type} validation list with {len(validation_list.items)} items"
                )

            # Make the validation lists tab active first
            try:
                if hasattr(self, "_tools_tabs") and self._tools_tabs.count() > 1:
                    logger.info("Switching to validation lists tab")
                    self._tools_tabs.setCurrentIndex(1)  # Switch to validation lists tab
            except Exception as e:
                logger.error(f"Error switching to validation tab: {str(e)}")

            # Update the validation list widgets if they exist
            try:
                if hasattr(self, "_player_list_widget") and "player" in lists:
                    logger.info("Setting player list in widget")
                    self._player_list_widget.set_list(lists["player"])

                if hasattr(self, "_chest_type_list_widget") and "chest_type" in lists:
                    logger.info("Setting chest type list in widget")
                    self._chest_type_list_widget.set_list(lists["chest_type"])

                if hasattr(self, "_source_list_widget") and "source" in lists:
                    logger.info("Setting source list in widget")
                    self._source_list_widget.set_list(lists["source"])
            except Exception as e:
                logger.error(f"Error setting lists in widgets: {str(e)}")

            # Make sure validation lists tab is properly initialized
            if hasattr(self, "_tools_tabs") and self._tools_tabs.count() > 1:
                # Update the tab text to show list counts
                tab_text = "Validation Lists"
                if lists:
                    list_counts = []
                    if "player" in lists:
                        list_counts.append(f"Players: {len(lists['player'].items)}")
                    if "chest_type" in lists:
                        list_counts.append(f"Chests: {len(lists['chest_type'].items)}")
                    if "source" in lists:
                        list_counts.append(f"Sources: {len(lists['source'].items)}")

                    if list_counts:
                        tab_text += f" ({', '.join(list_counts)})"

                logger.info(f"Updating validation lists tab text: {tab_text}")
                self._tools_tabs.setTabText(1, tab_text)

            # Only emit signal if this is not a signal loop - crucial change
            from_dashboard = (
                hasattr(self.parent(), "_dashboard") and self.parent()._dashboard is not None
            )
            if from_dashboard and getattr(self.parent()._dashboard, "_processing_signal", False):
                logger.info("Dashboard already processing signals, skipping emission")
            else:
                logger.info(f"Emitting validation_lists_updated signal with {len(lists)} lists")
                self.validation_lists_updated.emit(lists)

                # Schedule a delayed refresh only if needed
                QTimer.singleShot(500, lambda: self._delayed_refresh_validation_lists(lists))
        finally:
            self._processing_signal = False

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

    def _delayed_refresh_rules(self, rules):
        """
        Perform a delayed refresh of the correction rules table.
        This is called after a delay to ensure the UI has time to initialize.

        Args:
            rules: List of correction rules
        """
        import logging
        import traceback

        logger = logging.getLogger(__name__)
        logger.info(f"Performing delayed refresh with {len(rules)} rules")
        logger.info(f"Widget is now visible: {self.isVisible()}")

        # Prevent recursive signal processing
        if getattr(self, "_processing_signal", False):
            logger.warning("Already processing signal, skipping delayed refresh")
            return

        try:
            # Set processing flag
            self._processing_signal = True

            # This is critical: FIRST make the correction manager panel visible
            # before attempting to show the rules
            if hasattr(self.parent(), "_validation_btn") and not self.isVisible():
                logger.info("Making correction manager tab visible")
                self.parent()._validation_btn.click()

            # Check if we're on the right tab
            current_tab = (
                self.parent()._content_widget.currentIndex()
                if hasattr(self.parent(), "_content_widget")
                else -1
            )
            logger.info(f"Current widget stack index: {current_tab}")

            # Force the model to update with the rules again
            self._correction_rules_table.set_rules(rules)

            # Make the correction rules tab active
            if hasattr(self, "_tools_tabs"):
                logger.info("Ensuring correction rules tab is active")
                self._tools_tabs.setCurrentIndex(0)  # Force to correction rules tab

            # Force a viewport update
            logger.info("Forcing viewport update")
            self._correction_rules_table.viewport().update()

            # Log the visible state of the rules
            model = self._correction_rules_table._model
            if model:
                visible_count = model.rowCount()
                logger.info(f"Model now shows {visible_count} rows")
        except Exception as e:
            logger.error(f"Error in delayed refresh: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            # Reset processing flag
            self._processing_signal = False

    def _delayed_refresh_validation_lists(self, lists):
        """
        Perform a delayed refresh of the validation lists.
        This is called after a delay to ensure the UI has time to initialize.

        Args:
            lists: Dictionary of validation lists
        """
        import logging
        import traceback

        logger = logging.getLogger(__name__)
        logger.info(f"Performing delayed refresh with {len(lists)} lists")
        logger.info(f"Widget is now visible: {self.isVisible()}")

        try:
            # This is critical: FIRST make the correction manager panel visible
            # before attempting to show the lists
            if hasattr(self.parent(), "_validation_btn") and not self.isVisible():
                logger.info("Making correction manager tab visible")
                self.parent()._validation_btn.click()

            # Check if we're on the right tab
            current_tab = (
                self.parent()._content_widget.currentIndex()
                if hasattr(self.parent(), "_content_widget")
                else -1
            )
            logger.info(f"Current widget stack index: {current_tab}")

            # Force the model to update with the lists again
            self._player_list_widget.set_list(lists["player"])
            self._chest_type_list_widget.set_list(lists["chest_type"])
            self._source_list_widget.set_list(lists["source"])

            # Make the validation lists tab active
            if hasattr(self, "_tools_tabs"):
                logger.info("Ensuring validation lists tab is active")
                self._tools_tabs.setCurrentIndex(1)  # Force to validation lists tab

            # Force a viewport update
            logger.info("Forcing viewport update")
            try:
                # Check if the widgets have a viewport method before calling it
                # This is needed because ValidationListWidget might not have this method
                # depending on which QWidget it inherits from
                if hasattr(self._player_list_widget, "viewport") and callable(
                    getattr(self._player_list_widget, "viewport", None)
                ):
                    self._player_list_widget.viewport().update()
                else:
                    # Alternative: update the widget itself
                    self._player_list_widget.update()

                if hasattr(self._chest_type_list_widget, "viewport") and callable(
                    getattr(self._chest_type_list_widget, "viewport", None)
                ):
                    self._chest_type_list_widget.viewport().update()
                else:
                    self._chest_type_list_widget.update()

                if hasattr(self._source_list_widget, "viewport") and callable(
                    getattr(self._source_list_widget, "viewport", None)
                ):
                    self._source_list_widget.viewport().update()
                else:
                    self._source_list_widget.update()
            except Exception as e:
                logger.warning(f"Error updating viewports: {e}")
                # Fallback: try to update the widgets directly
                self._player_list_widget.update()
                self._chest_type_list_widget.update()
                self._source_list_widget.update()

            # Log the visible state of the lists
            model = self._player_list_widget._model
            if model:
                visible_count = model.rowCount()
                logger.info(f"Model now shows {visible_count} rows")
        except Exception as e:
            logger.error(f"Error in delayed refresh: {str(e)}")
            logger.error(traceback.format_exc())


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
