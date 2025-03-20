"""
main_window_refactor.py

Description: Refactored main application window using the new data management system
Usage:
    from src.ui.main_window_refactor import MainWindow
    main_window = MainWindow()
    main_window.show()
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from PySide6.QtCore import QSize, Qt, Signal, Slot, QByteArray
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSplitter,
    QFrame,
    QLabel,
    QStackedWidget,
    QTableView,
)

# Import services from new data management system
from src.services.service_factory import ServiceFactory
from src.services.dataframe_store import DataFrameStore, EventType
from src.services.file_service import FileService
from src.services.correction_service import CorrectionService
from src.services.validation_service import ValidationService

# Import UI components
from src.services.config_manager import ConfigManager
from src.ui.dashboard import Dashboard
from src.ui.correction_manager_panel import CorrectionManagerPanel
from src.ui.reports_panel import ReportPanel
from src.ui.settings_panel import SettingsPanel
from src.ui.validation_panel import ValidationPanel
from src.ui.styles import COLORS, SIDEBAR_STYLE


class MainWindow(QMainWindow):
    """
    Refactored main application window.

    This is the main window of the application, using the new data management system.
    It connects UI components with the new services and adapters.

    Implementation Notes:
        - Uses the new DataFrameStore as the central data store
        - Uses service classes for all data operations
        - Connects UI events to service methods
        - Uses the ServiceFactory to get service instances
    """

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Initialize properties
        self._config = ConfigManager()

        # Initialize services via the ServiceFactory
        self._service_factory = ServiceFactory.get_instance()
        self._service_factory.initialize_all_services()

        # Get service instances
        self._dataframe_store = self._service_factory.get_dataframe_store()
        self._file_service = self._service_factory.get_file_service()
        self._correction_service = self._service_factory.get_correction_service()
        self._validation_service = self._service_factory.get_validation_service()

        # Set up logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("MainWindow initialized with new data management system")

        # These will be created during setup
        self._dashboard = None
        self._correction_manager = None
        self._validation_panel = None
        self._report_panel = None
        self._settings_panel = None
        self._connected_signals = set()  # Track connected signals

        # Set window properties
        self.setWindowTitle("Chest Tracker Correction Tool")
        self.resize(1280, 800)

        # Setup UI
        self._setup_actions()
        self._setup_sidebar()
        self._setup_status_bar()
        self._setup_content()

        # Connect signals
        self._connect_signals()

        # Restore state
        self._restore_state()

        # Subscribe to DataFrameStore events
        self._subscribe_to_events()

    def _setup_actions(self):
        """Set up the actions."""
        # File actions
        self._new_action = QAction("New", self)
        self._new_action.setShortcut(QKeySequence.New)
        self._new_action.setStatusTip("Create a new file")
        self._new_action.triggered.connect(self._on_new)

        self._open_action = QAction("Open", self)
        self._open_action.setShortcut(QKeySequence.Open)
        self._open_action.setStatusTip("Open a file")
        self._open_action.triggered.connect(self._on_open)

        self._save_action = QAction("Save", self)
        self._save_action.setShortcut(QKeySequence.Save)
        self._save_action.setStatusTip("Save the current file")
        self._save_action.triggered.connect(self._on_save)

        self._exit_action = QAction("Exit", self)
        self._exit_action.setShortcut(QKeySequence.Quit)
        self._exit_action.setStatusTip("Exit the application")
        self._exit_action.triggered.connect(self.close)

        # Edit actions
        self._settings_action = QAction("Settings", self)
        self._settings_action.setStatusTip("Edit application settings")
        self._settings_action.triggered.connect(lambda: self._on_sidebar_button_clicked(3))

    def _setup_sidebar(self):
        """Set up the sidebar."""
        # Create central widget with horizontal splitter
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar
        self._sidebar = QWidget()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setStyleSheet(SIDEBAR_STYLE)
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Add app title to sidebar
        sidebar_header = QLabel("Chest Tracker")
        sidebar_header.setObjectName("sidebarHeader")
        sidebar_layout.addWidget(sidebar_header)

        # Create navigation buttons
        self._dashboard_btn = self._create_sidebar_button("Dashboard", 0)
        self._validation_btn = self._create_sidebar_button("Correction Manager", 1)
        self._reports_btn = self._create_sidebar_button("Reports", 2)
        self._settings_btn = self._create_sidebar_button("Settings", 3)

        # Add navigation buttons to sidebar
        sidebar_layout.addWidget(self._dashboard_btn)
        sidebar_layout.addWidget(self._validation_btn)
        sidebar_layout.addWidget(self._reports_btn)
        sidebar_layout.addWidget(self._settings_btn)

        # Add spacer
        sidebar_layout.addStretch()

        # Add sidebar and content to main layout
        self._content_widget = QStackedWidget()

        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._content_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 1080])  # Set initial sizes

        main_layout.addWidget(splitter)

        self.setCentralWidget(central_widget)

    def _create_sidebar_button(self, text, page_index):
        """
        Create a sidebar button for navigation.

        Args:
            text: Button text
            page_index: Index of the page to switch to

        Returns:
            The created button
        """
        button = QPushButton(text)
        button.setCheckable(True)

        # Set button properties
        button.clicked.connect(lambda: self._on_sidebar_button_clicked(page_index))

        return button

    def _on_sidebar_button_clicked(self, page_index):
        """
        Handle sidebar button click.

        Args:
            page_index: Index of the page to switch to
        """
        # Update button states
        self._dashboard_btn.setChecked(page_index == 0)
        self._validation_btn.setChecked(page_index == 1)
        self._reports_btn.setChecked(page_index == 2)
        self._settings_btn.setChecked(page_index == 3)

        # Switch content page
        self._content_widget.setCurrentIndex(page_index)

        # Save active tab (convert to string)
        self._config.set("Window", "active_tab", str(page_index))

    def _setup_status_bar(self):
        """Set up the status bar."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    def _setup_content(self):
        """Set up the content area."""
        # Create content pages
        self._setup_dashboard_page()
        self._setup_correction_manager_page()
        self._setup_reports_page()
        self._setup_settings_page()

        # Set initial page
        active_tab = self._config.get_int("Window", "active_tab", fallback=0)
        self._content_widget.setCurrentIndex(active_tab)

        # Update button states
        self._dashboard_btn.setChecked(active_tab == 0)
        self._validation_btn.setChecked(active_tab == 1)
        self._reports_btn.setChecked(active_tab == 2)
        self._settings_btn.setChecked(active_tab == 3)

    def _setup_dashboard_page(self):
        """Set up the dashboard page."""
        # Create dashboard with the services factory
        self._dashboard = Dashboard(self)

        # Connect dashboard to the services
        entry_table_view = self._dashboard.get_entry_table_view()
        if entry_table_view:
            # Create and connect entry table adapter
            entry_adapter = self._service_factory.get_entry_table_adapter(entry_table_view)
            entry_adapter.connect()

            # Store adapter reference to prevent garbage collection
            self._entry_adapter = entry_adapter

        # Add to content stack
        self._content_widget.addWidget(self._dashboard)

    def _setup_correction_manager_page(self):
        """Set up the correction manager page."""
        # Create correction manager panel
        self._correction_manager = CorrectionManagerPanel(self)

        # Connect correction rules table to DataFrameStore via adapter
        rules_table = self._correction_manager.get_correction_rules_table()
        if rules_table:
            # Create and connect correction rules table adapter
            rules_adapter = self._service_factory.get_correction_rule_table_adapter(rules_table)
            rules_adapter.connect()

            # Store adapter reference to prevent garbage collection
            self._rules_adapter = rules_adapter

        # Connect validation list combo boxes to DataFrameStore via adapters
        chest_types_combo = self._correction_manager.get_chest_types_combo()
        players_combo = self._correction_manager.get_players_combo()
        sources_combo = self._correction_manager.get_sources_combo()

        if chest_types_combo:
            chest_types_adapter = self._service_factory.get_validation_list_combo_adapter(
                chest_types_combo, "chest_types"
            )
            chest_types_adapter.connect()
            self._chest_types_adapter = chest_types_adapter

        if players_combo:
            players_adapter = self._service_factory.get_validation_list_combo_adapter(
                players_combo, "players"
            )
            players_adapter.connect()
            self._players_adapter = players_adapter

        if sources_combo:
            sources_adapter = self._service_factory.get_validation_list_combo_adapter(
                sources_combo, "sources"
            )
            sources_adapter.connect()
            self._sources_adapter = sources_adapter

        # Add to content stack
        self._content_widget.addWidget(self._correction_manager)

    def _setup_reports_page(self):
        """Set up the reports page."""
        # Create report panel
        self._report_panel = ReportPanel(self)

        # Connect to DataFrameStore for statistics
        # The report panel can subscribe to entries updates and generate reports

        # Add to content stack
        self._content_widget.addWidget(self._report_panel)

    def _setup_settings_page(self):
        """Set up the settings page."""
        # Create settings panel
        self._settings_panel = SettingsPanel(self)

        # Connect settings panel to services
        self._settings_panel.settings_changed.connect(self._on_settings_changed)

        # Add to content stack
        self._content_widget.addWidget(self._settings_panel)

    def _connect_signals(self):
        """Connect signals between components."""
        self._logger.info("Connecting signals between components")

        # Connect dashboard signals
        self._connect_dashboard_signals()

        # Connect correction manager signals
        if self._correction_manager:
            # Connect correction manager signals to services
            self._correction_manager.correction_rule_added.connect(
                lambda from_text, to_text, category: self._correction_service.add_correction_rule(
                    from_text, to_text, category
                )
            )
            self._correction_manager.correction_rules_imported.connect(
                lambda file_path: self._file_service.load_correction_rules_from_csv(file_path)
            )
            self._correction_manager.validation_list_item_added.connect(
                lambda list_type, value: self._validation_service.add_to_validation_list(
                    list_type, value
                )
            )

        # Connect settings panel signals
        if self._settings_panel:
            self._settings_panel.settings_changed.connect(self._on_settings_changed)

        # Add signals to connected_signals set to keep track
        self._connected_signals.update(
            [
                (self._dashboard.entries_loaded, self._on_entries_loaded_bridge),
                (self._dashboard.correction_rules_loaded, self._on_correction_rules_updated_bridge),
                (self._dashboard.corrections_applied, self._on_corrections_applied_bridge),
            ]
        )

    def _connect_dashboard_signals(self):
        """Connect dashboard signals to service methods."""
        if not self._dashboard:
            return

        self._logger.info("Connecting dashboard signals to service methods")

        # Connect file loading signals to file service
        self._dashboard.entries_loaded.connect(self._on_entries_loaded_bridge)
        self._dashboard.correction_rules_loaded.connect(self._on_correction_rules_updated_bridge)

        # Connect correction signals to correction service
        self._dashboard.corrections_applied.connect(self._on_corrections_applied_bridge)

        # Connect validation signals to validation service
        self._dashboard.validate_requested.connect(
            lambda: self._validation_service.validate_entries()
        )

        # Connect file save signals to file service
        self._dashboard.save_entries_requested.connect(
            lambda file_path: self._file_service.save_entries_to_file(file_path)
        )

    def _subscribe_to_events(self):
        """Subscribe to DataFrameStore events."""
        self._logger.info("Subscribing to DataFrameStore events")

        # Subscribe to entries updated events
        self._dataframe_store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)

        # Subscribe to correction rules updated events
        self._dataframe_store.subscribe(
            EventType.CORRECTION_RULES_UPDATED, self._on_correction_rules_updated
        )

        # Subscribe to validation lists updated events
        self._dataframe_store.subscribe(
            EventType.VALIDATION_LISTS_UPDATED, self._on_validation_lists_updated
        )

        # Subscribe to correction applied events
        self._dataframe_store.subscribe(EventType.CORRECTION_APPLIED, self._on_correction_applied)

        # Subscribe to validation completed events
        self._dataframe_store.subscribe(
            EventType.VALIDATION_COMPLETED, self._on_validation_completed
        )

        # Subscribe to error events
        self._dataframe_store.subscribe(EventType.ERROR_OCCURRED, self._on_error_occurred)

    def _on_entries_updated(self, event_data: Any):
        """
        Handle entries updated event from DataFrameStore.

        Args:
            event_data: Event data from DataFrameStore
        """
        self._logger.info("Entries updated event received")

        # Update the status bar with information about the entries
        stats = self._dataframe_store.get_entry_statistics()
        total = stats.get("total", 0)
        self._status_bar.showMessage(f"Entries updated: {total} entries")

        # Notify the dashboard of the entries update
        if hasattr(self._dashboard, "on_entries_updated") and callable(
            getattr(self._dashboard, "on_entries_updated")
        ):
            self._dashboard.on_entries_updated(
                None
            )  # The parameter is kept for backward compatibility

    def _on_correction_rules_updated(self, event_data: Any):
        """
        Handle correction rules updated event from DataFrameStore.

        Args:
            event_data: Event data from DataFrameStore
        """
        self._logger.info("Correction rules updated event received")

        # Update the status bar
        rules_df = self._dataframe_store.get_correction_rules()
        rule_count = len(rules_df)
        self._status_bar.showMessage(f"Correction rules updated: {rule_count} rules")

        # Notify the dashboard of the correction rules update
        if hasattr(self._dashboard, "on_correction_rules_updated") and callable(
            getattr(self._dashboard, "on_correction_rules_updated")
        ):
            self._dashboard.on_correction_rules_updated(
                None
            )  # The parameter is kept for backward compatibility

    def _on_validation_lists_updated(self, event_data: Any):
        """
        Handle validation lists updated event from DataFrameStore.

        Args:
            event_data: Event data from DataFrameStore
        """
        self._logger.info("Validation lists updated event received")

        # Get the list type that was updated
        list_type = None
        if isinstance(event_data, dict) and "list_type" in event_data:
            list_type = event_data["list_type"]

        # Update the status bar
        if list_type:
            list_df = self._dataframe_store.get_validation_list(list_type)
            self._status_bar.showMessage(
                f"Validation list '{list_type}' updated: {len(list_df)} items"
            )
        else:
            self._status_bar.showMessage("Validation lists updated")

    def _on_correction_applied(self, event_data: Any):
        """
        Handle correction applied event from DataFrameStore.

        Args:
            event_data: Event data from DataFrameStore
        """
        self._logger.info("Correction applied event received")

        # Extract correction information from event data
        count = 0
        entries_affected = 0
        if isinstance(event_data, dict):
            count = event_data.get("corrections_applied", 0)
            entries_affected = event_data.get("entries_affected", 0)

        # Update the status bar
        self._status_bar.showMessage(f"Applied {count} corrections to {entries_affected} entries")

        # Notify dashboard of corrections applied
        if hasattr(self._dashboard, "on_corrections_applied") and callable(
            getattr(self._dashboard, "on_corrections_applied")
        ):
            self._dashboard.on_corrections_applied(
                None
            )  # The parameter is kept for backward compatibility

    def _on_validation_completed(self, event_data: Any):
        """
        Handle validation completed event from DataFrameStore.

        Args:
            event_data: Event data from DataFrameStore
        """
        self._logger.info("Validation completed event received")

        # Extract validation results from event data
        valid_count = 0
        invalid_count = 0
        total_count = 0
        if isinstance(event_data, dict):
            valid_count = event_data.get("valid", 0)
            invalid_count = event_data.get("invalid", 0)
            total_count = event_data.get("total", 0)

        # Update the status bar
        self._status_bar.showMessage(
            f"Validation completed: {valid_count} valid, {invalid_count} invalid out of {total_count} entries"
        )

        # Notify dashboard of validation completed
        if hasattr(self._dashboard, "on_validation_completed") and callable(
            getattr(self._dashboard, "on_validation_completed")
        ):
            self._dashboard.on_validation_completed(event_data)

    def _on_error_occurred(self, event_data: Any):
        """
        Handle error event from DataFrameStore.

        Args:
            event_data: Event data from DataFrameStore
        """
        # Extract error information
        error_message = "An unknown error occurred"
        if isinstance(event_data, dict) and "message" in event_data:
            error_message = event_data["message"]
        elif isinstance(event_data, Exception):
            error_message = str(event_data)
        elif isinstance(event_data, str):
            error_message = event_data

        # Log the error
        self._logger.error(f"Error in DataFrameStore: {error_message}")

        # Update the status bar
        self._status_bar.showMessage(f"Error: {error_message}")

        # Show error dialog
        QMessageBox.critical(self, "Error", error_message)

    # Bridge methods to connect old signals to new service methods
    def _on_entries_loaded_bridge(self, entries):
        """
        Bridge method to connect old entries_loaded signal to new FileService.

        Args:
            entries: Entries information, which might be a file path or a list of entries
        """
        self._logger.info("Bridging entries_loaded signal to FileService")

        try:
            # First, check if entries is a file path
            if isinstance(entries, str) and Path(entries).exists():
                # Load entries from file
                self._file_service.load_entries_from_file(entries)
                return

            # If it's not a file path, check if it's a list of dictionaries
            if isinstance(entries, list) and all(isinstance(item, dict) for item in entries):
                # Convert to DataFrame and set in store
                entries_df = pd.DataFrame(entries)

                # Ensure object columns are properly initialized
                if "validation_errors" not in entries_df.columns:
                    entries_df["validation_errors"] = [[] for _ in range(len(entries_df))]
                if "original_values" not in entries_df.columns:
                    entries_df["original_values"] = [{} for _ in range(len(entries_df))]

                # Set in store
                self._dataframe_store.set_entries(entries_df, "signal_bridge")
                return

            # If it's a list of objects (old ChestEntry objects)
            if isinstance(entries, list) and len(entries) > 0:
                # Try to convert to dictionaries based on common attributes
                entries_dicts = []
                for entry in entries:
                    entry_dict = {}
                    for attr in ["chest_type", "player", "source", "status", "date"]:
                        if hasattr(entry, attr):
                            entry_dict[attr] = getattr(entry, attr)

                    # Add default values for missing attributes
                    if "status" not in entry_dict:
                        entry_dict["status"] = "Pending"
                    if "date" not in entry_dict:
                        entry_dict["date"] = pd.Timestamp.now().strftime("%Y-%m-%d")

                    # Add empty objects for validation_errors and original_values
                    entry_dict["validation_errors"] = []
                    entry_dict["original_values"] = {}

                    entries_dicts.append(entry_dict)

                # Convert to DataFrame and set in store
                entries_df = pd.DataFrame(entries_dicts)
                self._dataframe_store.set_entries(entries_df, "signal_bridge")
                return

            # If we get here, we couldn't handle the entries
            self._logger.warning(f"Couldn't handle entries: {type(entries)}")

        except Exception as e:
            self._logger.error(f"Error in entries_loaded bridge: {str(e)}")
            # Emit error event
            self._dataframe_store._emit_event(
                EventType.ERROR_OCCURRED,
                {"message": f"Error loading entries: {str(e)}", "source": "entries_loaded_bridge"},
            )

    def _on_corrections_applied_bridge(self, entries):
        """
        Bridge method to connect old corrections_applied signal to new CorrectionService.

        Args:
            entries: Entries information, which might be specific entries to correct
        """
        self._logger.info("Bridging corrections_applied signal to CorrectionService")

        try:
            # Simply call the correction service
            # The entries parameter is ignored as the service will use the entries in the store
            self._correction_service.apply_corrections()

        except Exception as e:
            self._logger.error(f"Error in corrections_applied bridge: {str(e)}")
            # Emit error event
            self._dataframe_store._emit_event(
                EventType.ERROR_OCCURRED,
                {
                    "message": f"Error applying corrections: {str(e)}",
                    "source": "corrections_applied_bridge",
                },
            )

    def _on_correction_rules_updated_bridge(self, rules):
        """
        Bridge method to connect old correction_rules_updated signal to new DataFrameStore.

        Args:
            rules: Rules information, which might be a file path or a list of rules
        """
        self._logger.info("Bridging correction_rules_updated signal to FileService")

        try:
            # First, check if rules is a file path
            if isinstance(rules, str) and Path(rules).exists():
                # Load rules from file
                self._file_service.load_correction_rules_from_csv(rules)
                return

            # If it's not a file path, check if it's a list of dictionaries
            if isinstance(rules, list) and all(isinstance(item, dict) for item in rules):
                # Convert to DataFrame and set in store
                rules_df = pd.DataFrame(rules)

                # Rename columns to match the expected schema
                if "from_text" not in rules_df.columns and "From" in rules_df.columns:
                    rules_df = rules_df.rename(columns={"From": "from_text"})
                if "to_text" not in rules_df.columns and "To" in rules_df.columns:
                    rules_df = rules_df.rename(columns={"To": "to_text"})

                # Add default values for missing columns
                if "category" not in rules_df.columns:
                    rules_df["category"] = "general"
                if "enabled" not in rules_df.columns:
                    rules_df["enabled"] = True
                if "timestamp" not in rules_df.columns:
                    rules_df["timestamp"] = pd.Timestamp.now()

                # Set in store
                self._dataframe_store.set_correction_rules(rules_df)
                return

            # If it's a list of objects (old CorrectionRule objects)
            if isinstance(rules, list) and len(rules) > 0:
                # Try to convert to dictionaries based on common attributes
                rules_dicts = []
                for rule in rules:
                    rule_dict = {}
                    for attr in ["from_text", "to_text", "category", "enabled"]:
                        if hasattr(rule, attr):
                            rule_dict[attr] = getattr(rule, attr)

                    # Add default values for missing attributes
                    if "category" not in rule_dict:
                        rule_dict["category"] = "general"
                    if "enabled" not in rule_dict:
                        rule_dict["enabled"] = True
                    if "timestamp" not in rule_dict:
                        rule_dict["timestamp"] = pd.Timestamp.now()

                    rules_dicts.append(rule_dict)

                # Convert to DataFrame and set in store
                rules_df = pd.DataFrame(rules_dicts)
                self._dataframe_store.set_correction_rules(rules_df)
                return

            # If we get here, we couldn't handle the rules
            self._logger.warning(f"Couldn't handle rules: {type(rules)}")

        except Exception as e:
            self._logger.error(f"Error in correction_rules_updated bridge: {str(e)}")
            # Emit error event
            self._dataframe_store._emit_event(
                EventType.ERROR_OCCURRED,
                {
                    "message": f"Error updating correction rules: {str(e)}",
                    "source": "correction_rules_updated_bridge",
                },
            )

    def _on_settings_changed(self, category):
        """
        Handle settings changed signal.

        Args:
            category: Category of settings that changed
        """
        self._logger.info(f"Settings changed: {category}")

        # Refresh UI components based on settings changes
        if category == "Appearance":
            # Refresh UI appearance
            pass
        elif category == "Validation":
            # Re-validate entries with new settings
            self._validation_service.validate_entries()
        elif category == "General":
            # Update general settings
            pass

    # Action handlers
    @Slot()
    def _on_new(self):
        """Handle new action."""
        # Clear the entries in the store
        self._dataframe_store.set_entries(pd.DataFrame(), "new_file")
        self._status_bar.showMessage("New file created")

    @Slot()
    def _on_open(self):
        """Handle open action."""
        # Show file open dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            str(Path(self._config.get_path("Paths", "input_dir", fallback="."))),
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                # Save the selected directory as the input directory
                input_dir = str(Path(file_path).parent)
                self._config.set_path("Paths", "input_dir", input_dir)

                # Load the file using the file service
                self._file_service.load_entries_from_file(file_path)

                # Validate the entries
                self._validation_service.validate_entries()

                self._status_bar.showMessage(f"Opened file: {file_path}")
            except Exception as e:
                self._logger.error(f"Error opening file: {str(e)}")
                QMessageBox.critical(self, "Error Opening File", str(e))

    @Slot()
    def _on_save(self):
        """Handle save action."""
        # Show file save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            str(Path(self._config.get_path("Paths", "output_dir", fallback="."))),
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                # Save the selected directory as the output directory
                output_dir = str(Path(file_path).parent)
                self._config.set_path("Paths", "output_dir", output_dir)

                # Save the file using the file service
                self._file_service.save_entries_to_file(file_path)

                self._status_bar.showMessage(f"Saved file: {file_path}")
            except Exception as e:
                self._logger.error(f"Error saving file: {str(e)}")
                QMessageBox.critical(self, "Error Saving File", str(e))

    def _restore_state(self):
        """Restore the window state from configuration."""
        # Restore window geometry
        width = self._config.get_int("Window", "width", fallback=1280)
        height = self._config.get_int("Window", "height", fallback=800)
        self.resize(width, height)

        # Restore window position
        x = self._config.get_int("Window", "x", fallback=-1)
        y = self._config.get_int("Window", "y", fallback=-1)
        if x >= 0 and y >= 0:
            self.move(x, y)

        # Restore maximized state
        if self._config.get_bool("Window", "maximized", fallback=False):
            self.showMaximized()

        # Restore active tab
        active_tab = self._config.get_int("Window", "active_tab", fallback=0)
        self._content_widget.setCurrentIndex(active_tab)
        self._on_sidebar_button_clicked(active_tab)

    def _save_state(self):
        """Save the window state to configuration."""
        # Save window geometry
        if not self.isMaximized():
            self._config.set("Window", "width", str(self.width()))
            self._config.set("Window", "height", str(self.height()))
            self._config.set("Window", "x", str(self.x()))
            self._config.set("Window", "y", str(self.y()))

        # Save maximized state
        self._config.set("Window", "maximized", str(self.isMaximized()))

        # Save active tab
        active_tab = self._content_widget.currentIndex()
        self._config.set("Window", "active_tab", str(active_tab))

    def closeEvent(self, event: QCloseEvent):
        """Handle close event."""
        # Save window state
        self._save_state()

        # Accept the event
        event.accept()
