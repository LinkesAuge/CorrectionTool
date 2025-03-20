"""
correction_manager_interface.py

Description: Interface-based correction manager panel that uses dependency injection
Usage:
    from src.ui.correction_manager_interface import CorrectionManagerInterface
    panel = CorrectionManagerInterface(service_factory)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, cast
import traceback

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
    QFileDialog,
    QFrame,
)

# Import standardized EventType
from src.interfaces.events import EventType, EventHandler, EventData

# Import interfaces
from src.interfaces import (
    IServiceFactory,
    IDataStore,
    IFileService,
    ICorrectionService,
    IValidationService,
    IConfigManager,
)

from src.ui.correction_rules_table import CorrectionRulesTable
from src.ui.validation_list_widget import ValidationListWidget
from src.ui.enhanced_table_view import EnhancedTableView
from src.ui.helpers.drag_drop_manager import DragDropManager
from src.ui.widgets.validation_lists_control_panel import ValidationListsControlPanel

import pandas as pd


class CorrectionManagerInterface(QWidget):
    """
    Interface-based correction manager panel that uses dependency injection.

    This panel provides a UI for managing correction rules and validation
    lists. It has a split layout with correction tools on the left and
    entries on the right.

    Signals:
        correction_rules_updated: Signal emitted when correction rules are updated
        validation_lists_updated: Signal emitted when validation lists are updated
        entries_updated: Signal emitted when entries are updated

    Attributes:
        _service_factory: IServiceFactory instance for accessing services
        _data_store: IDataStore instance for data access
        _file_service: IFileService instance for file operations
        _correction_service: ICorrectionService instance for correction operations
        _validation_service: IValidationService instance for validation operations
        _config_manager: IConfigManager instance for configuration management
        _drag_drop_manager: DragDropManager instance for drag-and-drop functionality
    """

    # Signals
    correction_rules_updated = Signal(list)  # List of rules
    validation_lists_updated = Signal(dict)  # Dict of validation lists
    entries_updated = Signal(list)  # List of entries

    def __init__(self, service_factory: IServiceFactory, parent=None):
        """
        Initialize the correction manager interface with dependency injection.

        Args:
            service_factory: IServiceFactory instance for accessing services
            parent: Parent widget
        """
        super().__init__(parent)
        self.setObjectName("correction_manager_interface")

        self._logger = logging.getLogger(__name__)
        self._logger.info("Initializing CorrectionManagerInterface")

        # Store the service factory
        self._service_factory = service_factory

        # Get services from the factory
        self._data_store = service_factory.get_service(IDataStore)
        self._file_service = service_factory.get_service(IFileService)
        self._correction_service = service_factory.get_service(ICorrectionService)
        self._validation_service = service_factory.get_service(IValidationService)
        self._config_manager = service_factory.get_service(IConfigManager)

        # Initialize drag-drop manager
        self._drag_drop_manager = None

        # Initialize UI
        self._correction_rules_table = None
        self._player_list_widget = None
        self._chest_type_list_widget = None
        self._source_list_widget = None
        self._entry_table = None

        self._search_rules_entry = None
        self._search_entries_entry = None
        self._show_all_rules_checkbox = None

        self._setup_ui()
        self._connect_signals()
        self._load_saved_data()

        # Initialize drag-and-drop functionality
        self._setup_drag_drop()

        self._logger.info("CorrectionManagerInterface initialized")

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
        self._main_splitter = QSplitter(Qt.Horizontal)

        # Create panels
        self._setup_correction_tools_panel()
        self._setup_entries_panel()

        # Add panels to splitter
        self._main_splitter.addWidget(self._correction_tools_panel)
        self._main_splitter.addWidget(self._entries_panel)

        # Set initial sizes (40% left, 60% right)
        self._main_splitter.setSizes([400, 600])

        # Add splitter to main layout
        main_layout.addWidget(self._main_splitter, 1)  # 1 = stretch factor

    def _setup_correction_tools_panel(self):
        """Set up the correction tools panel (left side)."""
        # Create panel
        self._correction_tools_panel = QWidget()
        panel_layout = QVBoxLayout(self._correction_tools_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)

        # Create tabs
        self._tabs = QTabWidget()

        # Create tab content
        self._setup_correction_rules_tab()
        self._setup_validation_lists_tab()

        # Add tabs to panel
        panel_layout.addWidget(self._tabs)

    def _setup_correction_rules_tab(self):
        """Set up the correction rules tab."""
        # Create tab content
        rules_tab = QWidget()
        tab_layout = QVBoxLayout(rules_tab)

        # Add controls
        controls_layout = QHBoxLayout()

        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self._search_rules_entry = QLineEdit()
        self._search_rules_entry.setPlaceholderText("Filter rules...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_rules_entry, 1)  # 1 = stretch factor
        controls_layout.addLayout(search_layout, 1)  # 1 = stretch factor

        # Toggle checkbox
        self._show_all_rules_checkbox = QCheckBox("Enable All")
        self._show_all_rules_checkbox.setChecked(True)
        controls_layout.addWidget(self._show_all_rules_checkbox)

        tab_layout.addLayout(controls_layout)

        # Create correction rules table
        self._correction_rules_table = CorrectionRulesTable()
        tab_layout.addWidget(self._correction_rules_table, 1)  # 1 = stretch factor

        # Add buttons
        buttons_layout = QHBoxLayout()
        self._add_rule_button = QPushButton("Add Rule")
        self._edit_rule_button = QPushButton("Edit Rule")
        self._delete_rule_button = QPushButton("Delete Rule")
        self._import_rules_button = QPushButton("Import Rules")
        self._export_rules_button = QPushButton("Export Rules")

        buttons_layout.addWidget(self._add_rule_button)
        buttons_layout.addWidget(self._edit_rule_button)
        buttons_layout.addWidget(self._delete_rule_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self._import_rules_button)
        buttons_layout.addWidget(self._export_rules_button)

        tab_layout.addLayout(buttons_layout)

        # Add tab
        self._tabs.addTab(rules_tab, "Correction Rules")

    def _setup_validation_lists_tab(self):
        """Set up the validation lists tab."""
        # Create tab content
        validation_tab = QWidget()
        tab_layout = QVBoxLayout(validation_tab)

        # Add unified controls panel at the top
        validation_lists_dict = {}

        # Create group boxes for each validation list
        lists_container = QWidget()
        lists_layout = QVBoxLayout(lists_container)

        # Player list
        player_group = QGroupBox("Players")
        player_layout = QVBoxLayout(player_group)
        self._player_list_widget = ValidationListWidget("player")
        player_layout.addWidget(self._player_list_widget)
        validation_lists_dict["player"] = self._player_list_widget

        # Chest type list
        chest_group = QGroupBox("Chest Types")
        chest_layout = QVBoxLayout(chest_group)
        self._chest_type_list_widget = ValidationListWidget("chest_type")
        chest_layout.addWidget(self._chest_type_list_widget)
        validation_lists_dict["chest_type"] = self._chest_type_list_widget

        # Source list
        source_group = QGroupBox("Sources")
        source_layout = QVBoxLayout(source_group)
        self._source_list_widget = ValidationListWidget("source")
        source_layout.addWidget(self._source_list_widget)
        validation_lists_dict["source"] = self._source_list_widget

        # Add unified control panel
        self._validation_lists_control_panel = ValidationListsControlPanel(
            validation_lists=validation_lists_dict,
            config_manager=self._config_manager,
            data_store=self._data_store,
        )
        tab_layout.addWidget(self._validation_lists_control_panel)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        tab_layout.addWidget(separator)

        # Add groups to tab
        lists_layout.addWidget(player_group)
        lists_layout.addWidget(chest_group)
        lists_layout.addWidget(source_group)

        # Add the lists container to the tab
        tab_layout.addWidget(lists_container, 1)  # 1 = stretch factor

        # Add tab
        self._tabs.addTab(validation_tab, "Validation Lists")

    def _setup_entries_panel(self):
        """Set up the entries panel (right side)."""
        # Create panel
        self._entries_panel = QWidget()
        panel_layout = QVBoxLayout(self._entries_panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)

        # Add controls
        controls_layout = QHBoxLayout()

        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self._search_entries_entry = QLineEdit()
        self._search_entries_entry.setPlaceholderText("Filter entries...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_entries_entry, 1)  # 1 = stretch factor
        controls_layout.addLayout(search_layout, 1)  # 1 = stretch factor

        panel_layout.addLayout(controls_layout)

        # Create entries table
        self._entries_table = EnhancedTableView()
        panel_layout.addWidget(self._entries_table, 1)  # 1 = stretch factor

        # Add create rule button
        button_layout = QHBoxLayout()
        self._create_rule_button = QPushButton("Create Rule from Selection")
        self._create_rule_button.setEnabled(False)
        button_layout.addStretch()
        button_layout.addWidget(self._create_rule_button)

        panel_layout.addLayout(button_layout)

    def _connect_signals(self):
        """
        Connect signals to slots.
        """
        self._logger.info("Connecting signals")

        # Connect data store events
        self._data_store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
        self._data_store.subscribe(
            EventType.VALIDATION_LIST_UPDATED, self._on_validation_lists_updated
        )
        self._data_store.subscribe(
            EventType.CORRECTION_RULES_UPDATED, self._on_correction_rules_updated
        )

        # Connect correction rules table signals
        if self._correction_rules_table:
            self._correction_rules_table.rules_updated.connect(self.correction_rules_updated)

        # Connect validation list signals
        if self._player_list_widget:
            self._player_list_widget.list_updated.connect(self._on_player_list_updated)

        if self._chest_type_list_widget:
            self._chest_type_list_widget.list_updated.connect(self._on_chest_type_list_updated)

        if self._source_list_widget:
            self._source_list_widget.list_updated.connect(self._on_source_list_updated)

        # Connect unified control panel signals
        if self._validation_lists_control_panel:
            self._validation_lists_control_panel.lists_updated.connect(
                self.validation_lists_updated
            )

        # Connect entry table signals
        if self._entry_table:
            self._entry_table.entry_selected.connect(self._on_entry_selected)
            self._entry_table.entry_edited.connect(self._on_entry_edited)

        # Connect controls signals
        if self._search_rules_entry:
            self._search_rules_entry.textChanged.connect(self._on_search_rules)

        if self._search_entries_entry:
            self._search_entries_entry.textChanged.connect(self._on_search_entries)

        if self._show_all_rules_checkbox:
            self._show_all_rules_checkbox.stateChanged.connect(self._on_toggle_all_rules)

    def _setup_drag_drop(self):
        """
        Set up drag and drop functionality between validation lists and the correction rules table.
        """
        # Check if drag-drop is enabled in config
        if not self._config_manager.get_boolean("Features", "enable_drag_drop", fallback=False):
            self._logger.info("Drag-and-drop functionality is disabled in config")
            return

        self._logger.info("Setting up drag-and-drop functionality")

        # Create a dictionary of validation lists
        validation_lists = {
            "player": self._player_list_widget,
            "chest_type": self._chest_type_list_widget,
            "source": self._source_list_widget,
        }

        # Create drag-drop manager
        self._drag_drop_manager = DragDropManager(self._data_store)

        # Set up drag-drop between validation lists and correction rules table
        self._drag_drop_manager.setup_drag_drop(validation_lists, self._correction_rules_table)

    def _load_saved_data(self):
        """
        Load saved data from the data store.
        """
        try:
            # Load correction rules
            correction_rules_path = self._config_manager.get_path("correction_rules_file")
            if correction_rules_path and Path(correction_rules_path).exists():
                self._logger.info(f"Loading correction rules from {correction_rules_path}")
                self._file_service.load_correction_rules(correction_rules_path)

            # Load validation lists
            player_list_path = self._config_manager.get_path("player_list_file")
            chest_type_list_path = self._config_manager.get_path("chest_type_list_file")
            source_list_path = self._config_manager.get_path("source_list_file")

            if player_list_path and Path(player_list_path).exists():
                self._logger.info(f"Loading player list from {player_list_path}")
                self._file_service.load_validation_list("player", player_list_path)

            if chest_type_list_path and Path(chest_type_list_path).exists():
                self._logger.info(f"Loading chest type list from {chest_type_list_path}")
                self._file_service.load_validation_list("chest_type", chest_type_list_path)

            if source_list_path and Path(source_list_path).exists():
                self._logger.info(f"Loading source list from {source_list_path}")
                self._file_service.load_validation_list("source", source_list_path)

        except Exception as e:
            self._logger.error(f"Error loading saved data: {e}")
            QMessageBox.warning(
                self,
                "Error Loading Data",
                f"There was an error loading saved data: {str(e)}",
                QMessageBox.Ok,
            )

    def _on_entries_updated(self, event_data: Dict[str, Any]):
        """
        Handle entries updated event.

        Args:
            event_data: Event data containing updated entries information
        """
        try:
            # Log the start of the update process
            self._logger.info(
                f"Handling entries updated event with {event_data.get('count', 0)} entries"
            )

            # Get entries from data store
            entries_df = self._data_store.get_entries()
            self._logger.debug(f"Retrieved {len(entries_df)} entries from data store")

            # Check if entries are available - handle both DataFrame and dict
            if isinstance(entries_df, pd.DataFrame):
                if entries_df.empty:
                    self._logger.warning("Retrieved empty DataFrame from data store")
                    return
                # Convert DataFrame to records
                records = entries_df.to_dict("records")
            elif isinstance(entries_df, list):
                # Already a list (of dicts or objects), use directly
                records = entries_df
                if not records:
                    self._logger.warning("Retrieved empty list from data store")
                    return
            else:
                self._logger.warning(f"Unexpected type from get_entries(): {type(entries_df)}")
                return

            self._logger.debug(f"Converting {len(records)} entries to records for table")

            # Update entries table
            try:
                self._entries_table.set_entries(records)
                self._logger.debug(f"Successfully set {len(records)} entries to table")
            except Exception as e:
                self._logger.error(f"Error setting entries to table: {str(e)}")
                import traceback

                self._logger.error(traceback.format_exc())

            # Log the event
            count = event_data.get("count", 0)
            self._logger.info(f"Updated {count} entries")

        except Exception as e:
            self._logger.error(f"Error handling entries updated event: {e}")
            import traceback

            self._logger.error(traceback.format_exc())

    def _on_correction_rules_updated(self, event_data: Dict[str, Any]):
        """
        Handle correction rules updated event.

        Args:
            event_data: Event data containing update information
        """
        try:
            rules = self._data_store.get_correction_rules()

            if isinstance(rules, pd.DataFrame) and not rules.empty:
                self._logger.info(f"Setting {len(rules)} correction rules to table")
                self._correction_rules_table.set_rules(rules)
            else:
                self._logger.warning("No correction rules to display")
                self._correction_rules_table.clear_rules()

        except Exception as e:
            self._logger.error(f"Error setting correction rules to table: {e}")

        try:
            list_type = event_data.get("list_type", "")

            # If no specific list type, we might need to refresh all validation lists
            if not list_type:
                # Try to update all validation lists
                try:
                    player_list = self._data_store.get_validation_list("player")
                    self._player_list_widget.set_validation_list(player_list)
                except Exception as e:
                    self._logger.warning(f"Could not update player list: {e}")

                try:
                    chest_type_list = self._data_store.get_validation_list("chest_type")
                    self._chest_type_list_widget.set_validation_list(chest_type_list)
                except Exception as e:
                    self._logger.warning(f"Could not update chest type list: {e}")

                try:
                    source_list = self._data_store.get_validation_list("source")
                    self._source_list_widget.set_validation_list(source_list)
                except Exception as e:
                    self._logger.warning(f"Could not update source list: {e}")

                return

            # Handle update for a specific list type
            if list_type in ["player", "chest_type", "source"]:
                try:
                    list_widget = getattr(self, f"_{list_type}_list_widget")
                    validation_list = self._data_store.get_validation_list(list_type)
                    list_widget.set_validation_list(validation_list)
                except Exception as e:
                    self._logger.warning(f"Could not update {list_type} list: {e}")

        except Exception as e:
            self._logger.error(f"Error updating validation lists: {e}")

    def _on_validation_lists_updated(self, event_data: Dict[str, Any]):
        """
        Handle validation lists updated event.

        Args:
            event_data: Event data containing updated validation lists information
        """
        try:
            list_type = event_data.get("list_type", "")

            # If no specific list type, we might need to refresh all validation lists
            if not list_type:
                # Try to update all validation lists
                try:
                    player_list = self._data_store.get_validation_list("player")
                    self._player_list_widget.set_validation_list(player_list)
                except Exception as e:
                    self._logger.warning(f"Could not update player list: {e}")

                try:
                    chest_type_list = self._data_store.get_validation_list("chest_type")
                    self._chest_type_list_widget.set_validation_list(chest_type_list)
                except Exception as e:
                    self._logger.warning(f"Could not update chest type list: {e}")

                try:
                    source_list = self._data_store.get_validation_list("source")
                    self._source_list_widget.set_validation_list(source_list)
                except Exception as e:
                    self._logger.warning(f"Could not update source list: {e}")

                return

            # Update the appropriate validation list widget
            if list_type == "player":
                player_list = self._data_store.get_validation_list("player")
                if player_list is not None:
                    self._player_list_widget.set_validation_list(player_list)
                    count = len(player_list) if hasattr(player_list, "__len__") else 0
                    self._logger.info(f"Updated player validation list with {count} entries")

            elif list_type == "chest_type":
                chest_type_list = self._data_store.get_validation_list("chest_type")
                if chest_type_list is not None:
                    self._chest_type_list_widget.set_validation_list(chest_type_list)
                    count = len(chest_type_list) if hasattr(chest_type_list, "__len__") else 0
                    self._logger.info(f"Updated chest_type validation list with {count} entries")

            elif list_type == "source":
                source_list = self._data_store.get_validation_list("source")
                if source_list is not None:
                    self._source_list_widget.set_validation_list(source_list)
                    count = len(source_list) if hasattr(source_list, "__len__") else 0
                    self._logger.info(f"Updated source validation list with {count} entries")

        except Exception as e:
            self._logger.error(f"Error handling validation lists updated event: {e}")
            self._logger.error(f"Exception details: {traceback.format_exc()}")

    @Slot()
    def _on_add_rule(self):
        """Handle add rule button click."""
        try:
            # Let the correction rules table handle adding a rule
            self._correction_rules_table.add_rule()

        except Exception as e:
            self._logger.error(f"Error adding rule: {e}")
            QMessageBox.warning(
                self,
                "Error Adding Rule",
                f"There was an error adding a rule: {str(e)}",
                QMessageBox.Ok,
            )

    @Slot()
    def _on_edit_rule(self):
        """Handle edit rule button click."""
        try:
            # Let the correction rules table handle editing a rule
            self._correction_rules_table.edit_selected_rule()

        except Exception as e:
            self._logger.error(f"Error editing rule: {e}")
            QMessageBox.warning(
                self,
                "Error Editing Rule",
                f"There was an error editing the selected rule: {str(e)}",
                QMessageBox.Ok,
            )

    @Slot()
    def _on_delete_rule(self):
        """Handle delete rule button click."""
        try:
            # Let the correction rules table handle deleting a rule
            self._correction_rules_table.delete_selected_rule()

        except Exception as e:
            self._logger.error(f"Error deleting rule: {e}")
            QMessageBox.warning(
                self,
                "Error Deleting Rule",
                f"There was an error deleting the selected rule: {str(e)}",
                QMessageBox.Ok,
            )

    @Slot()
    def _on_import_rules(self):
        """Handle import rules button click."""
        try:
            # Get input directory from config
            input_dir = self._config_manager.get_path("input_dir")

            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Correction Rules",
                str(input_dir),
                "CSV Files (*.csv);;All Files (*.*)",
            )

            if not file_path:
                return

            # Convert to Path object to verify existence
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Update config with string path (not the Path object)
            self._config_manager.set_path("correction_rules_file", str(path_obj))

            # Import correction rules using string path
            self._file_service.load_correction_rules(str(path_obj))

            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Successfully imported correction rules from {path_obj.name}",
                QMessageBox.Ok,
            )

        except Exception as e:
            self._logger.error(f"Error importing rules: {e}")
            QMessageBox.warning(
                self,
                "Error Importing Rules",
                f"There was an error importing correction rules: {str(e)}",
                QMessageBox.Ok,
            )

    @Slot()
    def _on_export_rules(self):
        """Handle export rules button click."""
        try:
            # Get correction rules from data store
            rules_df = self._data_store.get_correction_rules()

            if rules_df.empty:
                QMessageBox.warning(
                    self,
                    "No Rules",
                    "There are no correction rules to export.",
                    QMessageBox.Ok,
                )
                return

            # Get output directory from config
            output_dir = self._config_manager.get_path("output_dir")

            # Open file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Correction Rules",
                str(output_dir),
                "CSV Files (*.csv);;All Files (*.*)",
            )

            if not file_path:
                return

            # Update config
            self._config_manager.set_path("correction_rules_file", file_path)

            # Export correction rules
            self._file_service.save_correction_rules(file_path)

            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Successfully exported correction rules to {Path(file_path).name}",
                QMessageBox.Ok,
            )

        except Exception as e:
            self._logger.error(f"Error exporting rules: {e}")
            QMessageBox.warning(
                self,
                "Error Exporting Rules",
                f"There was an error exporting correction rules: {str(e)}",
                QMessageBox.Ok,
            )

    @Slot(str)
    def _on_search_rules(self, text: str):
        """
        Handle search rules text changed.

        Args:
            text: Search text
        """
        try:
            # Filter correction rules table
            self._correction_rules_table.set_filter(text)

        except Exception as e:
            self._logger.error(f"Error filtering rules: {e}")

    @Slot(str)
    def _on_search_entries(self, text: str):
        """
        Handle search entries text changed.

        Args:
            text: Search text
        """
        try:
            # Filter entries table
            self._entries_table.set_filter(text)

        except Exception as e:
            self._logger.error(f"Error filtering entries: {e}")

    @Slot(int)
    def _on_toggle_all_rules(self, state: int):
        """
        Handle toggle all rules checkbox state changed.

        Args:
            state: Checkbox state (Qt.Checked or Qt.Unchecked)
        """
        try:
            # Update all rules
            enabled = state == Qt.Checked
            self._correction_rules_table.toggle_all_rules(enabled)

        except Exception as e:
            self._logger.error(f"Error toggling all rules: {e}")

    @Slot(object)
    def _on_entry_selected(self, entry):
        """
        Handle entry selected.

        Args:
            entry: Selected entry
        """
        try:
            # Enable create rule button if an entry is selected
            self._create_rule_button.setEnabled(True)

        except Exception as e:
            self._logger.error(f"Error handling entry selection: {e}")

    @Slot(object)
    def _on_entry_edited(self, entry):
        """
        Handle entry edited.

        Args:
            entry: Edited entry
        """
        try:
            # Update the entry in the data store
            self._data_store.update_entry(entry)

            # Update UI
            entries_df = self._data_store.get_entries()
            self._entries_table.set_entries(entries_df.to_dict("records"))

            # Log the event
            self._logger.info(f"Updated entry: {entry}")

        except Exception as e:
            self._logger.error(f"Error handling entry edit: {e}")
            QMessageBox.warning(
                self,
                "Error Updating Entry",
                f"There was an error updating the entry: {str(e)}",
                QMessageBox.Ok,
            )

    @Slot(object)
    def _on_player_list_updated(self, player_list):
        """
        Handle player list updated.

        Args:
            player_list: Updated player list
        """
        try:
            # Save the updated player list to the data store
            self._data_store.update_validation_list("player", player_list)

            # Log the event
            self._logger.info(f"Updated player list with {len(player_list)} entries")

        except Exception as e:
            self._logger.error(f"Error handling player list update: {e}")

    @Slot(object)
    def _on_chest_type_list_updated(self, chest_type_list):
        """
        Handle chest type list updated.

        Args:
            chest_type_list: Updated chest type list
        """
        try:
            # Save the updated chest type list to the data store
            self._data_store.update_validation_list("chest_type", chest_type_list)

            # Log the event
            self._logger.info(f"Updated chest type list with {len(chest_type_list)} entries")

        except Exception as e:
            self._logger.error(f"Error handling chest type list update: {e}")

    @Slot(object)
    def _on_source_list_updated(self, source_list):
        """
        Handle source list updated.

        Args:
            source_list: Updated source list
        """
        try:
            # Save the updated source list to the data store
            self._data_store.update_validation_list("source", source_list)

            # Log the event
            self._logger.info(f"Updated source list with {len(source_list)} entries")

        except Exception as e:
            self._logger.error(f"Error handling source list update: {e}")

    @Slot()
    def _on_create_rule_from_selection(self):
        """Handle create rule from selection button click."""
        try:
            # Get selected entry
            selected_entry = self._entries_table.get_selected_entry()

            if not selected_entry:
                QMessageBox.warning(
                    self,
                    "No Selection",
                    "Please select an entry to create a rule from.",
                    QMessageBox.Ok,
                )
                return

            # Create dialog to get rule details
            dialog = CreateRuleDialog(selected_entry, self)

            if dialog.exec() == QDialog.Accepted:
                # Get values from dialog
                field, from_text, to_text = dialog.get_values()

                if not field or not from_text:
                    QMessageBox.warning(
                        self,
                        "Invalid Rule",
                        "Field and 'From' text are required.",
                        QMessageBox.Ok,
                    )
                    return

                # Create rule
                rule = {
                    "field": field,
                    "from_text": from_text,
                    "to_text": to_text,
                    "enabled": True,
                }

                # Add rule to data store
                self._data_store.add_correction_rule(rule)

                # Show success message
                QMessageBox.information(
                    self,
                    "Success",
                    "Successfully created correction rule.",
                    QMessageBox.Ok,
                )

        except Exception as e:
            self._logger.error(f"Error creating rule from selection: {e}")
            QMessageBox.warning(
                self,
                "Error Creating Rule",
                f"There was an error creating a rule from the selection: {str(e)}",
                QMessageBox.Ok,
            )

    def showEvent(self, event):
        """
        Handle show event.

        Args:
            event: Show event
        """
        super().showEvent(event)

        # Update data when shown
        self._refresh_validation_lists()
        self._refresh_correction_rules()
        self._refresh_entries()

        # Restore splitter sizes from config
        splitter_sizes = self._config_manager.get_value("CorrectionManager", "splitter_sizes")
        if splitter_sizes:
            sizes = [int(size) for size in splitter_sizes.split(",")]
            self._main_splitter.setSizes(sizes)

    def closeEvent(self, event):
        """
        Handle close event.

        Saves configuration and unsubscribes from events.

        Args:
            event: Close event
        """
        self._logger.info("CorrectionManagerInterface closing")

        # Clean up drag-drop manager
        if hasattr(self, "_drag_drop_manager") and self._drag_drop_manager:
            self._drag_drop_manager.cleanup()

        # Unsubscribe from events
        self._data_store.unsubscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
        # ENTRIES_LOADED was removed
        self._data_store.unsubscribe(
            EventType.VALIDATION_LIST_UPDATED, self._on_validation_lists_updated
        )
        self._data_store.unsubscribe(
            EventType.CORRECTION_RULES_UPDATED, self._on_correction_rules_updated
        )

        # Save configuration
        try:
            # Save configuration here if needed
            if self._config_manager:
                self._config_manager.save()
        except Exception as e:
            self._logger.error(f"Error saving configuration: {e}")

        # Accept the event
        event.accept()

    def _refresh_validation_lists(self):
        """Refresh validation list widgets with current data."""
        try:
            # Get validation lists from data store
            player_list = self._data_store.get_validation_list("player")
            chest_type_list = self._data_store.get_validation_list("chest_type")
            source_list = self._data_store.get_validation_list("source")

            # Update widgets
            if isinstance(player_list, pd.DataFrame):
                if not player_list.empty:
                    self._player_list_widget.set_validation_list(player_list)
            elif player_list:  # Handle if it's a list or ValidationList object
                self._player_list_widget.set_validation_list(player_list)

            if isinstance(chest_type_list, pd.DataFrame):
                if not chest_type_list.empty:
                    self._chest_type_list_widget.set_validation_list(chest_type_list)
            elif chest_type_list:  # Handle if it's a list or ValidationList object
                self._chest_type_list_widget.set_validation_list(chest_type_list)

            if isinstance(source_list, pd.DataFrame):
                if not source_list.empty:
                    self._source_list_widget.set_validation_list(source_list)
            elif source_list:  # Handle if it's a list or ValidationList object
                self._source_list_widget.set_validation_list(source_list)

        except Exception as e:
            self._logger.error(f"Error refreshing validation lists: {e}")

    def _refresh_correction_rules(self):
        """Refresh correction rules table with current data."""
        try:
            # Get correction rules from data store
            rules_df = self._data_store.get_correction_rules()

            # Log columns for debugging
            self._logger.info(f"DataFrame columns: {list(rules_df.columns)}")

            # Check if DataFrame has an index column that's causing issues
            if rules_df.index.name:
                self._logger.info(f"DataFrame has an index column named: {rules_df.index.name}")
                # Reset index to make sure it doesn't get included in to_dict
                rules_df = rules_df.reset_index()

            # Standardize column names: convert From/To/Category to from_text/to_text/category if needed
            column_mapping = {
                "From": "from_text",
                "To": "to_text",
                "Category": "category",
                "Enabled": "enabled",
                "Disabled": "disabled",  # if this exists, we'll handle it
            }

            # Rename columns if they match our mapping (case-sensitive)
            for old_col, new_col in column_mapping.items():
                if old_col in rules_df.columns and new_col not in rules_df.columns:
                    rules_df = rules_df.rename(columns={old_col: new_col})

            # Handle Disabled column if it exists (convert to enabled)
            if "disabled" in rules_df.columns and "enabled" not in rules_df.columns:
                rules_df["enabled"] = ~rules_df["disabled"].astype(bool)
                rules_df = rules_df.drop(columns=["disabled"])

            # Ensure 'enabled' column exists
            if "enabled" not in rules_df.columns:
                rules_df["enabled"] = True

            # Convert to list of dictionaries
            # Use orient='records' to ensure we get a list of dictionaries without index
            rules_dicts = rules_df.to_dict(orient="records")

            # Debug the first dictionary to see its structure
            if rules_dicts:
                self._logger.info(f"First dictionary keys: {list(rules_dicts[0].keys())}")
                self._logger.info(f"Dictionary sample: {rules_dicts[0]}")

            # Update table
            if not rules_df.empty:
                self._logger.info(f"Setting {len(rules_dicts)} correction rules to table")
                self._correction_rules_table.set_rules(rules_dicts)

        except Exception as e:
            self._logger.error(f"Error setting correction rules to table: {e}")
            import traceback

            self._logger.error(traceback.format_exc())

    def _refresh_entries(self):
        """Refresh entries table with current data."""
        try:
            # Get entries from data store
            entries_df = self._data_store.get_entries()

            # Update table
            if not entries_df.empty:
                self._entries_table.set_entries(entries_df.to_dict("records"))

            # Log the refresh
            self._logger.debug(f"Refreshed entries table with {len(entries_df)} entries")

        except Exception as e:
            self._logger.error(f"Error refreshing entries: {e}")


class CreateRuleDialog(QDialog):
    """Dialog for creating a correction rule from an entry."""

    def __init__(self, entry, parent=None):
        """
        Initialize dialog.

        Args:
            entry: The entry to create a rule from
            parent: Parent widget
        """
        super().__init__(parent)

        self._entry = entry
        self._setup_ui()

    def _setup_ui(self):
        """Set up UI."""
        # Set dialog properties
        self.setWindowTitle("Create Correction Rule")
        self.setMinimumWidth(400)

        # Main layout
        layout = QVBoxLayout(self)

        # Field selection
        field_layout = QHBoxLayout()
        field_label = QLabel("Field:")
        self._field_combo = QComboBox()
        self._field_combo.addItems(["player", "chest_type", "source"])
        field_layout.addWidget(field_label)
        field_layout.addWidget(self._field_combo, 1)
        layout.addLayout(field_layout)

        # From text
        from_layout = QHBoxLayout()
        from_label = QLabel("From:")
        self._from_edit = QLineEdit()
        from_layout.addWidget(from_label)
        from_layout.addWidget(self._from_edit, 1)
        layout.addLayout(from_layout)

        # To text
        to_layout = QHBoxLayout()
        to_label = QLabel("To:")
        self._to_edit = QLineEdit()
        to_layout.addWidget(to_label)
        to_layout.addWidget(self._to_edit, 1)
        layout.addLayout(to_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self._ok_button = QPushButton("OK")
        self._cancel_button = QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(self._ok_button)
        button_layout.addWidget(self._cancel_button)
        layout.addLayout(button_layout)

        # Connect signals
        self._field_combo.currentIndexChanged.connect(self._on_field_changed)
        self._ok_button.clicked.connect(self.accept)
        self._cancel_button.clicked.connect(self.reject)

        # Set initial field
        self._field_combo.setCurrentIndex(0)
        self._on_field_changed(0)

    def _on_field_changed(self, index):
        """
        Handle field selection changed.

        Args:
            index: Index of selected field
        """
        field = self._field_combo.currentText()

        # Update from text based on selected field
        if field == "player":
            self._from_edit.setText(self._entry.get("player", ""))
        elif field == "chest_type":
            self._from_edit.setText(self._entry.get("chest_type", ""))
        elif field == "source":
            self._from_edit.setText(self._entry.get("source", ""))

        # Clear to text
        self._to_edit.setText("")
        self._to_edit.setFocus()

    def accept(self):
        """Handle OK button click."""
        field = self._field_combo.currentText()
        from_text = self._from_edit.text().strip()
        to_text = self._to_edit.text().strip()

        # Validate inputs
        if not field:
            QMessageBox.warning(
                self,
                "Invalid Field",
                "Please select a field.",
                QMessageBox.Ok,
            )
            return

        if not from_text:
            QMessageBox.warning(
                self,
                "Invalid From Text",
                "Please enter the text to correct from.",
                QMessageBox.Ok,
            )
            return

        # Accept dialog
        super().accept()

    def get_values(self) -> Tuple[str, str, str]:
        """
        Get the values entered in the dialog.

        Returns:
            Tuple of (field, from_text, to_text)
        """
        field = self._field_combo.currentText()
        from_text = self._from_edit.text().strip()
        to_text = self._to_edit.text().strip()
        return field, from_text, to_text
