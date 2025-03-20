"""
dashboard_interface.py

Description: Interface-based dashboard widget that uses dependency injection
Usage:
    from src.ui.dashboard_interface import DashboardInterface
    dashboard = DashboardInterface(service_factory)
"""

import logging
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, cast
import os
import csv
import pandas as pd
from datetime import datetime

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QEvent
from PySide6.QtGui import QColor, QIcon, QAction, QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QFileDialog,
    QMenuBar,
    QApplication,
    QMenu,
    QCheckBox,
    QComboBox,
    QStatusBar,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QTableView,
    QToolBar,
    QTabWidget,
    QToolButton,
    QSizePolicy,
    QProgressDialog,
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.models.validation_list import ValidationList

# Import interfaces
from src.interfaces import (
    IServiceFactory,
    IDataStore,
    IFileService,
    ICorrectionService,
    IValidationService,
    IConfigManager,
    IFilterManager,
)
from src.interfaces.events import EventType, EventHandler, EventData

from src.ui.action_button_group import ActionButtonGroup
from src.ui.enhanced_table_view import EnhancedTableView
from src.ui.file_import_widget import FileImportWidget
from src.ui.statistics_widget import StatisticsWidget
from src.ui.validation_status_indicator import ValidationStatusIndicator
from src.ui.adapters.filter_adapter import FilterAdapter
from src.ui.adapters.entry_table_adapter import EntryTableAdapter

from src.services.dataframe_store import IDataStore
from src.services.event_manager import EventType, EventManager


class DashboardInterface(QWidget):
    """
    Interface-based dashboard widget that uses dependency injection.

    This is the central widget of the application, providing a unified
    interface for all chest tracking and correction features.

    Signals:
        entries_loaded (list): Signal emitted when entries are loaded
        entries_updated (list): Signal emitted when entries are updated
        corrections_loaded (list): Signal emitted when corrections are loaded
        corrections_applied (list): Signal emitted when corrections are applied
        validation_lists_updated (list): Signal emitted when validation lists are updated
        correction_rules_updated (list): Signal emitted when correction rules are updated

    Implementation Notes:
        - Uses dependency injection for services
        - Uses QSplitter for flexible layout
        - Integrates components like FileImportWidget, StatisticsWidget, etc.
        - Manages data flow between components
        - Handles state persistence via IConfigManager
    """

    # Signals
    entries_loaded = Signal(list)  # List[ChestEntry]
    entries_updated = Signal(list)  # List[ChestEntry]
    corrections_loaded = Signal(list)  # List[CorrectionRule]
    corrections_applied = Signal(list)  # List[ChestEntry]
    validation_lists_updated = Signal(list)  # List of validation lists
    correction_rules_updated = Signal(list)  # List of correction rules

    def __init__(self, service_factory: IServiceFactory, parent=None):
        """
        Initialize the dashboard with dependency injection.

        Args:
            service_factory: IServiceFactory instance for accessing services
            parent: Parent widget
        """
        super().__init__(parent)

        # Store the service factory
        self._service_factory = service_factory

        # Get services from factory
        self._config_manager = cast(
            IConfigManager, self._service_factory.get_service(IConfigManager)
        )
        self._data_store = cast(IDataStore, self._service_factory.get_service(IDataStore))
        self._file_service = cast(IFileService, self._service_factory.get_service(IFileService))
        self._correction_service = cast(
            ICorrectionService, self._service_factory.get_service(ICorrectionService)
        )
        self._validation_service = cast(
            IValidationService, self._service_factory.get_service(IValidationService)
        )
        self._filter_manager = cast(
            IFilterManager, self._service_factory.get_service(IFilterManager)
        )

        # Create filter adapter
        self._filter_adapter = FilterAdapter(self._data_store)
        self._filter_adapter.set_config_manager(self._config_manager)
        self._filter_panel = self._filter_adapter.create_filter_panel()

        # Create table view and entry table adapter
        self._table_adapter = EntryTableAdapter(self._data_store, self._config_manager)
        self._table_view = self._table_adapter.get_table_view()
        self._table_adapter.setup_connections()

        # Initialize logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("Initializing DashboardInterface")

        # Initialize signal processing flags
        self._processing_signal = False
        self._processing_entries_loaded = False
        self._processing_corrections_applied = False
        self._emitting_signal = False
        self._connected_events = set()  # Track connected events
        self._validation_in_progress = False  # Flag to prevent validation loops

        # Set up main widget
        self._setup_ui()

        # Connect signals
        self._connect_signals()

        # Initialize status bar reference - will be populated later
        self._status_bar = None
        if self.parent() and hasattr(self.parent(), "statusBar"):
            self._status_bar = self.parent().statusBar()
            self._logger.info("Status bar initialized from parent")
        else:
            self._logger.warning("No parent statusBar available, status_bar will be None")

        # Load saved rules and validation lists
        self._load_saved_correction_rules()
        self._load_saved_validation_lists()

        self._logger.info("DashboardInterface initialized")

    def statusBar(self):
        """
        Get the status bar from the parent window.

        Returns:
            QStatusBar or MockStatusBar: The status bar from the parent window or a mock object
        """
        # Try to get status bar from parent (MainWindow) if not already set
        if self._status_bar is None and self.parent() and hasattr(self.parent(), "statusBar"):
            self._status_bar = self.parent().statusBar()

        # If still None, return a mock object with showMessage method
        if self._status_bar is None:

            class MockStatusBar:
                def showMessage(self, message, timeout=0):
                    pass

            return MockStatusBar()

        return self._status_bar

    def _setup_ui(self) -> None:
        """Set up the dashboard user interface components."""
        self._logger.debug("Setting up dashboard UI components")

        # Create main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create and add top toolbar
        toolbar = QToolBar()
        self._setup_toolbar(toolbar)
        layout.addWidget(toolbar)

        # Create and add main content area
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        content_layout.addWidget(splitter)
        self._main_splitter = splitter

        layout.addWidget(content_container)

        # Create filter adapter
        self._filter_adapter = FilterAdapter(self._data_store)
        self._filter_adapter.set_config_manager(self._config_manager)
        self._filter_panel = self._filter_adapter.create_filter_panel()

        # Create table view and entry table adapter
        self._table_adapter = EntryTableAdapter(self._data_store, self._config_manager)
        self._table_view = self._table_adapter.get_table_view()
        self._table_adapter.setup_connections()

        # Add filter panel to left side
        filter_container = QWidget()
        filter_layout = QVBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(QLabel("Filters"))
        filter_layout.addWidget(self._filter_panel)
        splitter.addWidget(filter_container)

        # Add right side container (table and statistics)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(right_container)

        # Set initial sizes for the splitter (30% left, 70% right)
        splitter.setSizes([300, 700])

        # Add table to right container
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Add actions above table
        actions_container = QWidget()
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        # Add search box
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search entries...")
        actions_layout.addWidget(self._search_box)

        # Add table actions toolbar
        table_actions = QToolBar()
        self._setup_table_actions(table_actions)
        actions_layout.addWidget(table_actions)

        table_layout.addWidget(actions_container)
        table_layout.addWidget(self._table_view)

        # Create statistics widget
        self._stats_widget = StatisticsWidget()

        # Add tab widget for table and stats
        tabs = QTabWidget()
        tabs.addTab(table_container, "Entries")
        tabs.addTab(self._stats_widget, "Statistics")

        right_layout.addWidget(tabs)

        # Add status bar
        self._status_bar = QStatusBar()
        layout.addWidget(self._status_bar)

        # Set initial status
        self._status_bar.showMessage("Ready")

        # Connect signals
        self._connect_signals()

        # Load filter state if available
        self._filter_adapter.load_filter_state()

    def _connect_signals(self) -> None:
        """Connect signals and slots for application events."""
        self._logger.debug("Connecting dashboard signals")

        # File import signals
        self._file_import.entries_loaded.connect(self._on_file_imported)
        self._file_import.corrections_loaded.connect(self._on_corrections_loaded)
        self._file_import.corrections_applied.connect(self._on_corrections_applied)

        # Button signals
        self._add_entry_button.clicked.connect(self._on_add_entry)
        self._edit_entry_button.clicked.connect(self._on_edit_entry)
        self._delete_entry_button.clicked.connect(self._on_delete_entry)
        self._validate_button.clicked.connect(self._on_validate_entries)
        self._export_button.clicked.connect(self._on_export_data)

        # Table view signals
        self._table_view.doubleClicked.connect(self._on_entry_double_clicked)
        self._table_adapter.selection_changed.connect(self._on_selection_changed)

        # Filter adapter signals
        self._filter_adapter.filtered_data.connect(self._on_data_filtered)

        # Event manager signals
        EventManager.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
        EventManager.subscribe(EventType.IMPORT_COMPLETED, self._on_entries_updated)

    def _setup_toolbar(self, toolbar: QToolBar) -> None:
        """Set up the main toolbar with actions.

        Args:
            toolbar: The toolbar to set up
        """
        # Add file import widget
        self._file_import = FileImportWidget()
        toolbar.addWidget(self._file_import)

        # Add spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        # Add main action buttons
        self._validate_button = QPushButton("Validate Entries")
        self._export_button = QPushButton("Export Data")

        toolbar.addWidget(self._validate_button)
        toolbar.addWidget(self._export_button)

    def _setup_table_actions(self, toolbar: QToolBar) -> None:
        """Set up the table actions toolbar.

        Args:
            toolbar: The toolbar to set up
        """
        # Add entry manipulation buttons
        self._add_entry_button = QToolButton()
        self._add_entry_button.setText("Add")
        self._add_entry_button.setToolTip("Add new entry")

        self._edit_entry_button = QToolButton()
        self._edit_entry_button.setText("Edit")
        self._edit_entry_button.setToolTip("Edit selected entry")

        self._delete_entry_button = QToolButton()
        self._delete_entry_button.setText("Delete")
        self._delete_entry_button.setToolTip("Delete selected entry")

        toolbar.addWidget(self._add_entry_button)
        toolbar.addWidget(self._edit_entry_button)
        toolbar.addWidget(self._delete_entry_button)

    def _load_saved_correction_rules(self):
        """Load saved correction rules."""
        try:
            # Get correction rules file path from config
            correction_rules_path = self._config_manager.get_path("correction_rules_file")

            if correction_rules_path and Path(correction_rules_path).exists():
                self._logger.info(f"Loading correction rules from {correction_rules_path}")

                # Load correction rules
                self._file_service.load_correction_rules(correction_rules_path)

                # Update status
                self.statusBar().showMessage(
                    f"Loaded correction rules from {Path(correction_rules_path).name}"
                )
            else:
                self._logger.info("No saved correction rules found or file doesn't exist")
        except Exception as e:
            self._logger.error(f"Error loading correction rules: {e}")
            self.statusBar().showMessage("Error loading correction rules")

    def _on_load_correction_file(self, file_path=None):
        """
        Load correction rules from a file.

        Args:
            file_path: Path to the correction rules file. If None, open a file dialog.
        """
        try:
            if not file_path:
                # Get input directory from config
                input_dir = self._config_manager.get_path("input_dir")

                # Open file dialog
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Open Correction Rules File",
                    str(input_dir),
                    "CSV Files (*.csv);;All Files (*.*)",
                )

                if not file_path:
                    return

                # Update input directory in config
                self._config_manager.set_path("correction_rules_file", file_path)

            # Load correction rules
            self._file_service.load_correction_rules(file_path)

            # Update status
            self.statusBar().showMessage(f"Loaded correction rules from {Path(file_path).name}")

        except Exception as e:
            self._logger.error(f"Error loading correction rules: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error loading correction rules: {str(e)}",
                QMessageBox.Ok,
            )

    def _load_saved_validation_lists(self):
        """Load saved validation lists."""
        try:
            # Load validation lists from files defined in config
            player_list_file = self._config_manager.get_path("player_list_file")
            chest_type_list_file = self._config_manager.get_path("chest_type_list_file")
            source_list_file = self._config_manager.get_path("source_list_file")

            validation_files = {
                "player": player_list_file,
                "chest_type": chest_type_list_file,
                "source": source_list_file,
            }

            # Load each validation list file if it exists
            for list_type, file_path in validation_files.items():
                if file_path and Path(file_path).exists():
                    self._logger.info(f"Loading {list_type} validation list from {file_path}")
                    self._file_service.load_validation_list(list_type, file_path)

            # Update status
            self.statusBar().showMessage("Loaded validation lists")

        except Exception as e:
            self._logger.error(f"Error loading validation lists: {e}")
            self.statusBar().showMessage("Error loading validation lists")

    @Slot(list)
    def _on_file_imported(self, entries):
        """
        Handle entries loaded signal from the file import widget.

        Args:
            entries: List of ChestEntry objects
        """
        self._logger.debug(f"File imported event received: {len(entries)} entries")
        # Convert entries to DataFrame and update the data store
        if entries:
            entries_df = pd.DataFrame([entry.to_dict() for entry in entries])
            self._data_store.set_entries(entries_df)

            # Update the table view with entries
            self._table_adapter.set_entries(entries_df)

            # Update statistics
            self._stats_widget.set_entries(entries)

            # Update filter panel with new data
            if self._filter_adapter:
                self._filter_adapter.on_data_changed()

            # Update status bar
            self.statusBar().showMessage(f"Loaded {len(entries)} entries")

    @Slot(list)
    def _on_corrections_loaded(self, rules):
        """
        Handle corrections loaded signal from the file import widget.

        Args:
            rules: List of CorrectionRule objects
        """
        # Log the event
        self._logger.info(f"Loaded {len(rules)} correction rules")

        # Store correction rules in the data store if needed
        rules_df = pd.DataFrame([rule.to_dict() for rule in rules])
        self._data_store.set_correction_rules(rules_df)

    @Slot(list)
    def _on_corrections_applied(self, entries):
        """
        Handle corrections applied signal from the file import widget.

        Args:
            entries: List of corrected ChestEntry objects
        """
        self._logger.debug(f"Corrections applied event received: {len(entries)} entries")
        # No need to implement if handled elsewhere
        pass

    @Slot(bool)
    def _on_corrections_enabled_changed(self, enabled):
        """
        Handle corrections enabled/disabled signal from the file import widget.

        Args:
            enabled: Whether corrections are enabled
        """
        self._logger.debug(f"Corrections enabled changed event received: {enabled}")
        # Store the setting in the config
        self._config_manager.set("Correction", "auto_apply_corrections", str(enabled).lower())

    def _on_import_completed(self, event_data: Dict[str, Any]):
        """
        Handle import completed event from DataFrameStore.

        Args:
            event_data: Event data containing import information
        """
        count = event_data.get("count", 0)

        # Log the event
        self._logger.info(f"Import completed with {count} entries")

        # Update status bar
        self.statusBar().showMessage(f"Import completed with {count} entries")

    def _on_entries_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle entries updated event.

        Args:
            event_data: Event data
        """
        count = event_data.get("count", 0)

        # Check if update is from validation, if so, don't trigger another validation
        source = event_data.get("source", "")
        if source == "validation_service" and self._validation_in_progress:
            self._logger.debug("Skipping validation loop - update from validation service")
            return

        # Log the update
        self._logger.info(f"Handling entries update event with {count} entries")

        # Update table view
        entries_df = self._data_store.get_entries()
        self._logger.debug(f"Retrieved {len(entries_df)} entries from data store")

        # Check if entries are available
        if entries_df.empty:
            self._logger.warning("Retrieved empty DataFrame from data store")
            return

        try:
            # Convert DataFrame rows to ChestEntry objects
            entries = []
            for _, row in entries_df.iterrows():
                try:
                    entry = ChestEntry(
                        chest_type=row.get("chest_type", ""),
                        player=row.get("player", ""),
                        source=row.get("source", ""),
                        id=row.get("id"),
                    )

                    # Copy additional attributes if they exist
                    if "status" in row:
                        entry.status = row["status"]
                    if "validation_errors" in row:
                        entry.validation_errors = row["validation_errors"]
                    if "original_values" in row:
                        entry.original_values = row["original_values"]

                    entries.append(entry)
                except Exception as e:
                    self._logger.error(f"Error converting row to ChestEntry: {e}")
                    self._logger.error(f"Row data: {row}")

            self._logger.debug(f"Converted {len(entries)} rows to ChestEntry objects")
            self._table_view.set_entries(entries)
            self._logger.debug(f"Successfully set {len(entries)} entries to table view")
        except Exception as e:
            self._logger.error(f"Error setting entries to table view: {str(e)}")
            import traceback

            self._logger.error(traceback.format_exc())

        # Update statistics
        self._stats_widget.set_entries(entries)

        # Update status
        self.statusBar().showMessage(f"Updated {count} entries")

        # Log the event
        self._logger.info(f"Updated {count} entries")

        # Only validate entries if this update wasn't from the validation service
        if source != "validation_service":
            self._validate_entries()

    def _on_correction_rules_loaded(self, event_data: Dict[str, Any]) -> None:
        """
        Handle correction rules loaded event.

        Args:
            event_data: Event data
        """
        count = event_data.get("count", 0)
        file_path = event_data.get("file_path", "")

        # Update status
        self._file_import.set_correction_rules_loaded(True)

        # Get the correction rules from the data store
        correction_rules = self._data_store.get_correction_rules()

        # Create CorrectionRule objects and update the statistics widget
        rules = [CorrectionRule.from_dict(rule) for _, rule in correction_rules.iterrows()]
        self._stats_widget.set_correction_rules(rules)

        # Update status bar
        self.statusBar().showMessage(f"Loaded {count} correction rules from {Path(file_path).name}")

        # Log the event
        self._logger.info(f"Loaded {count} correction rules from {file_path}")

    def _on_correction_rules_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle correction rules updated event.

        Args:
            event_data: Event data
        """
        count = event_data.get("count", 0)

        # Update statistics
        # Get the correction rules from the data store
        correction_rules = self._data_store.get_correction_rules()

        # Create CorrectionRule objects and update the statistics widget
        rules = [CorrectionRule.from_dict(rule) for _, rule in correction_rules.iterrows()]
        self._stats_widget.set_correction_rules(rules)

        # Update status
        self.statusBar().showMessage(f"Updated {count} correction rules")

        # Log the event
        self._logger.info(f"Updated {count} correction rules")

    def _on_validation_lists_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle validation lists updated event.

        Args:
            event_data: Event data
        """
        list_type = event_data.get("list_type", "")
        count = event_data.get("count", 0)

        # Update status
        if list_type:
            self._stats_widget.set_validation_list_count(list_type, count)
            self.statusBar().showMessage(
                f"Updated {list_type} validation list with {count} entries"
            )
        else:
            self.statusBar().showMessage("Updated validation lists")

        # Log the event
        self._logger.info(f"Updated validation list: {list_type} with {count} entries")

        # Re-validate entries if we have any
        if not self._data_store.get_entries().empty:
            self._validate_entries()

    def _on_file_loaded(self, file_path: str, count: int):
        """
        Handle file loaded signal from FileImportWidget.

        Args:
            file_path: Path to the loaded file
            count: Number of entries loaded
        """
        # Load the file
        try:
            self._load_input_file(file_path)

            # Update status bar
            self.statusBar().showMessage(f"Loaded {count} entries from {Path(file_path).name}")

            # Log the event
            self._logger.info(f"Loaded {count} entries from {file_path}")
        except Exception as e:
            self._logger.error(f"Error loading input file: {e}")
            QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}", QMessageBox.Ok)

    def _on_save_requested(self):
        """Handle save requested signal from ActionButtonGroup."""
        self._on_save_output()

    def _on_export_requested(self):
        """Handle export requested signal from ActionButtonGroup."""
        self._export_entries()

    def _on_manage_rules(self):
        """Handle settings button click from ActionButtonGroup."""
        self._logger.info("Settings/Manage rules requested")

        # Check if we have a parent MainWindow and request to show the settings page
        if hasattr(self.parent(), "show_page"):
            # Request the parent (MainWindow) to show the settings page
            self.parent().show_page("settings")
        else:
            QMessageBox.information(
                self,
                "Settings",
                "Settings functionality is available in the Settings tab.",
                QMessageBox.Ok,
            )

    def _on_apply_corrections(self):
        """
        Handle the signal for applying corrections.
        Triggered when the user clicks the apply corrections button.
        """
        self._logger.debug("Apply corrections requested")
        self._apply_corrections()

    def _on_validate_entries(self):
        """
        Handle the signal for validating entries.
        Triggered when the user clicks the validate button.
        """
        self._logger.debug("Validate entries requested")
        self._validate_entries()

    def _apply_corrections(self):
        """Apply correction rules to entries."""
        try:
            # Get entries and correction rules
            entries_df = self._data_store.get_entries()

            if entries_df.empty:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "No entries to apply corrections to.",
                    QMessageBox.Ok,
                )
                return

            # Apply corrections
            self._logger.info("Applying corrections to entries")
            results = self._correction_service.apply_corrections_to_entries()

            # Check if we had any corrections applied
            if results["total_corrections"] > 0:
                # Update status
                self.statusBar().showMessage(
                    f"Applied {results['total_corrections']} corrections to {results['entries_modified']} entries"
                )

                # Update table view
                entries_df = self._data_store.get_entries()
                self._table_view.set_entries(entries_df.to_dict("records"))

                # Validate entries
                self._validate_entries()

                # Log the event
                self._logger.info(
                    f"Applied {results['total_corrections']} corrections to {results['entries_modified']} entries"
                )
            else:
                self.statusBar().showMessage("No corrections applied")
                self._logger.info("No corrections applied")

        except Exception as e:
            self._logger.error(f"Error applying corrections: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error applying corrections: {str(e)}",
                QMessageBox.Ok,
            )

    def _on_settings_requested(self):
        """Handle settings button click."""
        # This is a stub. In a real application, this would open a settings dialog
        # or switch to a settings panel.
        self._logger.info("Settings requested")

        # Show message to inform user
        QMessageBox.information(
            self,
            "Settings",
            "Settings functionality is available in the Settings tab.",
            QMessageBox.Ok,
        )

    def _on_entry_selected(self, entry: Dict):
        """
        Handle entry selected signal from EnhancedTableView.

        Args:
            entry: Selected entry
        """
        # Currently just a stub - could be used to update details panel, etc.
        self._logger.debug(f"Entry selected: {entry}")

    def _on_context_menu_requested(self, position):
        """
        Show context menu for table items when requested.

        Args:
            position: Position where the context menu was requested
        """
        self._logger.debug(f"Context menu requested at position: {position}")

        # Get the selected entry
        entry = self._table_view.get_selected_entry()
        if not entry:
            return

        # Create context menu
        menu = QMenu(self)

        # Add actions
        copy_action = menu.addAction("Copy Value")
        apply_correction_action = menu.addAction("Apply Correction")
        validate_entry_action = menu.addAction("Validate")

        # Enable/disable actions based on context
        apply_correction_action.setEnabled(self._correction_service is not None)
        validate_entry_action.setEnabled(self._validation_service is not None)

        # Show the menu and get selected action
        action = menu.exec_(self._table_view.viewport().mapToGlobal(position))

        # Handle selected action
        if action == copy_action:
            if entry and "value" in entry:
                QApplication.clipboard().setText(str(entry["value"]))
        elif action == apply_correction_action:
            self._apply_corrections()
        elif action == validate_entry_action:
            self._validate_entries()

    def _on_entry_edited(self, entry: Dict):
        """
        Handle entry edited signal from EnhancedTableView.

        Args:
            entry: Edited entry
        """
        try:
            # Update the entry in the data store
            self._data_store.update_entry(entry)

            # Validate the updated entry
            self._validate_entries()

            # Update status
            self.statusBar().showMessage("Entry updated")

        except Exception as e:
            self._logger.error(f"Error updating entry: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error updating entry: {str(e)}",
                QMessageBox.Ok,
            )

    def _validate_entries(self):
        """Validate all entries against validation lists."""
        # Prevent recursive validation
        if self._validation_in_progress:
            self._logger.debug("Validation already in progress, skipping")
            return

        try:
            # Set validation in progress flag
            self._validation_in_progress = True

            # Get entries
            entries_df = self._data_store.get_entries()

            if entries_df is None or (isinstance(entries_df, pd.DataFrame) and entries_df.empty):
                # No entries to validate
                self._stats_widget.set_validation_errors(0)
                self._validation_status.set_validation_status(
                    0, 0
                )  # Pass 0 warnings as second parameter
                return

            # Validate entries
            self._logger.info("Validating entries")
            validation_results = self._validation_service.validate_entries()

            # Get validation list from results
            validation_list = validation_results.get("validation_list")

            # Update validation results in store and UI
            if validation_list:
                # Pass DataFrame to event handlers that expect it
                self._event_bus.emit(
                    EventType.VALIDATION_UPDATED,
                    {
                        "validation_list": validation_list,
                        "entries": entries_df,  # Pass the DataFrame, not dict
                    },
                )

            # Update UI with validation results
            self._stats_widget.set_validation_errors(validation_results["invalid"])
            # Pass both invalid count and 0 warnings
            self._validation_status.set_validation_status(validation_results["invalid"], 0)

            # Update table with validation results
            entries_df = self._data_store.get_entries()
            self._table_view.set_entries(entries_df.to_dict("records"))

            # Highlight validation errors in table if the method exists
            if hasattr(self._table_view, "highlight_validation_errors"):
                self._table_view.highlight_validation_errors()

            # Update status
            if validation_results["invalid"] > 0:
                self.statusBar().showMessage(
                    f"Found {validation_results['invalid']} validation errors"
                )
            else:
                self.statusBar().showMessage("All entries validated successfully")

            # Log the event
            self._logger.info(
                f"Validated {validation_results['total']} entries, found {validation_results['invalid']} errors"
            )

        except Exception as e:
            self._logger.error(f"Error validating entries: {e}")
            import traceback

            self._logger.error(traceback.format_exc())
            QMessageBox.critical(
                self,
                "Error",
                f"Error validating entries: {str(e)}",
                QMessageBox.Ok,
            )
        finally:
            # Clear validation in progress flag
            self._validation_in_progress = False

    def _on_load_text(self, file_path=None):
        """
        Load entries from a text file.

        Args:
            file_path: Path to the text file. If None, open a file dialog.
        """
        try:
            if not file_path:
                # Get input directory from config
                input_dir = self._config_manager.get_path("input_dir")

                # Open file dialog
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Open Text File",
                    str(input_dir),
                    "Text Files (*.txt);;All Files (*.*)",
                )

                if not file_path:
                    return

                # Update input directory in config
                self._config_manager.set_path("entries_file", file_path)

            # Load entries
            self._load_input_file(file_path)

        except Exception as e:
            self._logger.error(f"Error loading text file: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error loading text file: {str(e)}",
                QMessageBox.Ok,
            )

    def _load_input_file(self, file_path):
        """
        Load entries from a file using the FileService.

        Args:
            file_path: Path to the input file (str or Path)
        """
        try:
            # Validate file path - ensure it's a Path object
            if isinstance(file_path, str):
                path = Path(file_path)
            else:
                path = file_path

            if not path.exists():
                raise FileNotFoundError(f"File not found: {str(path)}")

            # Convert to string for FileService
            file_path_str = str(path)

            # Load entries
            entries_count = self._file_service.load_entries(file_path_str)

            # Update file import widget
            self._file_import.set_loaded_file(file_path_str)

            return entries_count

        except Exception as e:
            self._logger.error(f"Error loading input file: {e}")
            raise

    def _on_save_output(self):
        """Save entries to a text file."""
        try:
            # Get entries
            entries_df = self._data_store.get_entries()

            if entries_df.empty:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "No entries to save.",
                    QMessageBox.Ok,
                )
                return

            # Get output directory from config
            output_dir = self._config_manager.get_path("output_dir")

            # Open file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Output",
                str(output_dir),
                "Text Files (*.txt);;All Files (*.*)",
            )

            if not file_path:
                return

            # Update output directory in config
            self._config_manager.set_path("output_file", file_path)

            # Save entries
            self._file_service.save_entries(file_path)

            # Update status
            self.statusBar().showMessage(
                f"Saved {len(entries_df)} entries to {Path(file_path).name}"
            )

            # Log the event
            self._logger.info(f"Saved {len(entries_df)} entries to {file_path}")

        except Exception as e:
            self._logger.error(f"Error saving output: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error saving output: {str(e)}",
                QMessageBox.Ok,
            )

    def _export_entries(self):
        """Export entries to a CSV file."""
        try:
            # Get entries
            entries_df = self._data_store.get_entries()

            if entries_df.empty:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "No entries to export.",
                    QMessageBox.Ok,
                )
                return

            # Get output directory from config
            output_dir = self._config_manager.get_path("output_dir")

            # Open file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Entries",
                str(output_dir),
                "CSV Files (*.csv);;All Files (*.*)",
            )

            if not file_path:
                return

            # Update output directory in config
            self._config_manager.set_path("export_file", file_path)

            # Export entries
            self._file_service.export_entries_to_csv(file_path)

            # Update status
            self.statusBar().showMessage(
                f"Exported {len(entries_df)} entries to {Path(file_path).name}"
            )

            # Log the event
            self._logger.info(f"Exported {len(entries_df)} entries to {file_path}")

        except Exception as e:
            self._logger.error(f"Error exporting entries: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error exporting entries: {str(e)}",
                QMessageBox.Ok,
            )

    def _show_validation_lists(self):
        """Show the validation lists panel."""
        # Request the parent (MainWindow) to show the settings page
        if self.parent() and hasattr(self.parent(), "_on_sidebar_button_clicked"):
            # Assuming settings is at index 3
            self.parent()._on_sidebar_button_clicked(3)

            # Then request to show the validation lists tab
            if hasattr(self.parent(), "_settings_panel") and hasattr(
                self.parent()._settings_panel, "show_validation_lists"
            ):
                self.parent()._settings_panel.show_validation_lists()

    def _show_correction_rules(self):
        """Show the correction rules panel."""
        # Request the parent (MainWindow) to show the correction manager page
        if self.parent() and hasattr(self.parent(), "_on_sidebar_button_clicked"):
            # Assuming correction manager is at index 1
            self.parent()._on_sidebar_button_clicked(1)

    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Chest Tracker Correction Tool",
            "Chest Tracker Correction Tool\n\n"
            "A tool for correcting and validating chest tracking data.\n\n"
            "Version: 1.0.0",
        )

    def showEvent(self, event: QEvent) -> None:
        """
        Handle show event.

        Args:
            event: The show event
        """
        super().showEvent(event)

        # Restore splitter sizes
        if self._config_manager:
            sidebar_width = int(self._config_manager.get_value("Dashboard", "sidebar_width", "300"))
            content_width = int(self._config_manager.get_value("Dashboard", "content_width", "700"))
            self._main_splitter.setSizes([sidebar_width, content_width])

        # Restore filter state
        self._filter_adapter.load_filter_state()

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle close event.

        Args:
            event: The close event
        """
        # Save splitter sizes
        if self._config_manager:
            sizes = self._main_splitter.sizes()
            if len(sizes) >= 2:
                self._config_manager.set_value("Dashboard", "sidebar_width", str(sizes[0]))
                self._config_manager.set_value("Dashboard", "content_width", str(sizes[1]))

        # Save filter state
        self._filter_adapter.save_filter_state()

        super().closeEvent(event)

    # Bridge methods for backward compatibility

    def get_entry_table_view(self):
        """
        Get the entry table view.

        Returns:
            The entry table view
        """
        return self._table_view

    @property
    def filter_adapter(self) -> FilterAdapter:
        """
        Get the filter adapter.

        Returns:
            Filter adapter instance
        """
        return self._filter_adapter

    @Slot()
    def _on_data_filtered(self):
        """Handle when data is filtered."""
        # Update the table view with filtered data
        filtered_df = self._filter_manager.apply_filters(self._data_store.get_entries())
        self._table_view.set_entries(filtered_df.to_dict("records"))

        # Update statistics
        row_count = len(filtered_df)
        total_rows = len(self._data_store.get_entries())
        filtered_entries = [ChestEntry(**entry) for entry in filtered_df.to_dict("records")]
        self._stats_widget.set_entries(filtered_entries)

        # Update status bar
        if self._status_bar:
            if row_count == total_rows:
                self._status_bar.showMessage(f"Showing all {row_count} entries")
            else:
                self._status_bar.showMessage(
                    f"Filtered: showing {row_count} of {total_rows} entries"
                )

        # Save filter state to configuration
        self._filter_adapter.save_filter_state()

    def _on_data_changed(self) -> None:
        """Handle data change events."""
        # Update filter adapter
        self._filter_adapter.on_data_changed()

        # Update statistics
        self._stats_widget.update_statistics()

        # Update status
        self._status_bar.showMessage(f"Data updated: {self._data_store.get_entry_count()} entries")

    def _on_data_filtered(self, filtered_data: dict) -> None:
        """Handle filtered data from the filter adapter.

        Args:
            filtered_data: Dictionary of filtered data
        """
        self._logger.debug(f"Data filtered, {len(filtered_data)} entries remain visible")

        # Update visible entries in the table adapter
        self._table_adapter.set_visible_rows(filtered_data.keys())

        # Update statistics with filtered data
        entries_df = self._data_store.get_entries()
        if entries_df is not None:
            filtered_df = entries_df.loc[list(filtered_data.keys())]
            self._stats_widget.update_statistics(filtered_df)

        # Update status bar with count of visible entries
        total_count = (
            len(self._data_store.get_entries()) if self._data_store.get_entries() is not None else 0
        )
        visible_count = len(filtered_data)

        if total_count > 0:
            self._status_bar.showMessage(f"Showing {visible_count} of {total_count} entries")

        # Save filter state to configuration
        self._filter_adapter.save_filter_state()

    def _on_add_entry(self):
        """
        Handle add entry button click.
        Creates a new entry and adds it to the data store.
        """
        self._logger.info("Add entry requested")

        try:
            # Create a simple dialog to input basic entry data
            dialog = QDialog(self)
            dialog.setWindowTitle("Add New Entry")
            layout = QFormLayout(dialog)

            # Create input fields
            player_input = QLineEdit()
            chest_input = QLineEdit()
            source_input = QLineEdit()
            items_input = QLineEdit()

            # Add fields to form
            layout.addRow("Player:", player_input)
            layout.addRow("Chest:", chest_input)
            layout.addRow("Source:", source_input)
            layout.addRow("Items:", items_input)

            # Add buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addRow(button_box)

            # Show dialog and process result
            if dialog.exec_() == QDialog.Accepted:
                # Create new entry
                new_entry = {
                    "player": player_input.text(),
                    "chest": chest_input.text(),
                    "source": source_input.text(),
                    "items": items_input.text(),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                # Add entry to data store
                self._data_store.add_entry(new_entry)

                # Update UI
                self._on_data_changed()

                # Update status
                self._status_bar.showMessage(f"New entry added")
                self._logger.info(f"New entry added: {new_entry}")

        except Exception as e:
            self._logger.error(f"Error adding entry: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error adding entry: {str(e)}",
                QMessageBox.Ok,
            )

    def _on_edit_entry(self):
        """
        Handle edit entry button click.
        Edits the currently selected entry.
        """
        self._logger.info("Edit entry requested")

        try:
            # Get selected entry
            selected_entry = self._table_adapter.get_selected_entry()
            if not selected_entry:
                self._status_bar.showMessage("No entry selected")
                return

            # Create a dialog to edit entry data
            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Entry")
            layout = QFormLayout(dialog)

            # Create input fields with current values
            player_input = QLineEdit(selected_entry.get("player", ""))
            chest_input = QLineEdit(selected_entry.get("chest", ""))
            source_input = QLineEdit(selected_entry.get("source", ""))
            items_input = QLineEdit(selected_entry.get("items", ""))

            # Add fields to form
            layout.addRow("Player:", player_input)
            layout.addRow("Chest:", chest_input)
            layout.addRow("Source:", source_input)
            layout.addRow("Items:", items_input)

            # Add buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addRow(button_box)

            # Show dialog and process result
            if dialog.exec_() == QDialog.Accepted:
                # Update entry values
                updated_entry = selected_entry.copy()
                updated_entry["player"] = player_input.text()
                updated_entry["chest"] = chest_input.text()
                updated_entry["source"] = source_input.text()
                updated_entry["items"] = items_input.text()

                # Update entry in data store
                self._data_store.update_entry(updated_entry)

                # Update UI
                self._on_data_changed()

                # Update status
                self._status_bar.showMessage(f"Entry updated")
                self._logger.info(f"Entry updated: {updated_entry}")

        except Exception as e:
            self._logger.error(f"Error editing entry: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error editing entry: {str(e)}",
                QMessageBox.Ok,
            )

    def _on_delete_entry(self) -> None:
        """Handle deleting an entry."""
        if not self._table_adapter.has_selection():
            QMessageBox.warning(self, "No Selection", "Please select an entry to delete.")
            return

        entry = self._table_adapter.get_selected_entry()
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this entry?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Get index of the entry
            entry_idx = self._table_adapter.get_selected_row_index()
            if entry_idx is not None:
                # Remove from data store
                self._data_store.remove_entry(entry_idx)
                self._logger.info(f"Deleted entry at index {entry_idx}")
                self._status_bar.showMessage(f"Entry deleted")

    def _on_validate_entries(self) -> None:
        """Handle validating entries."""
        # Get the validation service
        validation_service = self._service_factory.get_service("IValidationService")
        if validation_service is None:
            self._logger.error("ValidationService not found")
            QMessageBox.critical(self, "Error", "Validation service not available")
            return

        # Get entries from data store
        entries_df = self._data_store.get_entries()
        if entries_df is None or len(entries_df) == 0:
            QMessageBox.information(self, "No Data", "No entries to validate.")
            return

        # Show progress dialog
        progress = QProgressDialog("Validating entries...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(500)  # Don't show for operations < 500ms

        try:
            # Validate entries
            self._logger.info(f"Starting validation of {len(entries_df)} entries")
            validation_service.validate_entries(entries_df, progress_callback=progress.setValue)

            # Validation results are saved to the data store automatically
            progress.setValue(100)

            # Refresh the table view
            self._table_adapter.refresh_data()

            # Show validation summary
            error_count = (
                entries_df["validation_errors"]
                .apply(lambda x: len(x) if isinstance(x, list) else 0)
                .sum()
            )
            self._logger.info(f"Validation complete: {error_count} errors found")

            if error_count > 0:
                self._status_bar.showMessage(f"Validation complete: {error_count} errors found")
                QMessageBox.information(
                    self, "Validation Complete", f"Validation complete: {error_count} errors found."
                )
            else:
                self._status_bar.showMessage("Validation complete: No errors found")
                QMessageBox.information(self, "Validation Complete", "No errors found in the data.")

        except Exception as e:
            self._logger.error(f"Error during validation: {str(e)}")
            progress.cancel()
            QMessageBox.critical(self, "Validation Error", f"Error during validation: {str(e)}")

    def _on_entry_double_clicked(self, model_index):
        """
        Handle double-click on an entry in the table view.
        Opens the selected entry for editing.

        Args:
            model_index: The model index of the clicked item
        """
        self._logger.debug(f"Entry double-clicked at row {model_index.row()}")
        self._on_edit_entry()

    def _on_selection_changed(self) -> None:
        """Handle selection changes in the table view."""
        has_selection = self._table_adapter.has_selection()
        self._edit_entry_button.setEnabled(has_selection)
        self._delete_entry_button.setEnabled(has_selection)

    def _on_export_data(self) -> None:
        """Handle exporting data when the export button is clicked."""
        # Get current entries from data store
        entries = self._data_store.get_all_entries()

        if not entries:
            QMessageBox.warning(self, "Export Warning", "No data to export.")
            return

        # Ask user for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "", "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Use file service to export data
            self._file_service.export_entries_to_csv(file_path, entries)
            QMessageBox.information(
                self, "Export Successful", f"Data successfully exported to {file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting data: {str(e)}")
            logging.error(f"Export error: {str(e)}")
