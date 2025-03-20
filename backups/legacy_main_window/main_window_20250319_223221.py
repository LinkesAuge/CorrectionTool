"""
main_window.py

Description: Main application window
Usage:
    from src.ui.main_window import MainWindow
    main_window = MainWindow()
    main_window.show()
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.models.validation_list import ValidationList
from src.services.config_manager import ConfigManager
from src.services.data_manager import DataManager
from src.ui.dashboard import Dashboard
from src.ui.correction_manager_panel import CorrectionManagerPanel
from src.ui.reports_panel import ReportPanel
from src.ui.settings_panel import SettingsPanel
from src.ui.validation_panel import ValidationPanel
from src.ui.styles import COLORS, SIDEBAR_STYLE


class MainWindow(QMainWindow):
    """
    Main application window.

    This is the main window of the application, containing a sidebar menu,
    content area, and status bar.

    Implementation Notes:
        - Uses sidebar navigation instead of menu bar
        - Uses tabbed content area for different views
        - Stores application state in ConfigManager
        - Provides access to application-wide data
    """

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Initialize properties
        self._config = ConfigManager()

        # Initialize the data manager (must be done before creating UI components)
        self._data_manager = DataManager.get_instance()

        # These will be created during setup
        self._dashboard = None
        self._correction_manager = None
        self._validation_panel = None
        self._report_panel = None
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
        # Create dashboard
        self._dashboard = Dashboard(self)

        # Add to content stack
        self._content_widget.addWidget(self._dashboard)

    def _setup_correction_manager_page(self):
        """Set up the correction manager page."""
        # Create correction manager panel
        self._correction_manager = CorrectionManagerPanel(self)

        # Add to content stack
        self._content_widget.addWidget(self._correction_manager)

    def _setup_validation_page(self):
        """Set up the validation panel."""
        # Create validation panel
        self._validation_panel = ValidationPanel(self)

        # Add to content stack
        self._content_widget.addWidget(self._validation_panel)

    def _setup_reports_page(self):
        """Set up the reports page."""
        # Create reports panel
        self._report_panel = ReportPanel(self)

        # Add to content stack
        self._content_widget.addWidget(self._report_panel)

    def _setup_settings_page(self):
        """Set up the settings page."""
        # Create settings panel
        self._settings_panel = SettingsPanel(self)

        # Connect signals
        self._settings_panel.settings_changed.connect(self._on_settings_changed)

        # Add to content stack
        self._content_widget.addWidget(self._settings_panel)

    def _connect_signals(self):
        """Connect signals to slots."""
        try:
            import logging

            logger = logging.getLogger(__name__)
            logger.info("Connecting MainWindow signals")

            # Connect DataManager signals to components
            # This is the key change - all components listen to the central DataManager
            data_manager = self._data_manager

            # Connect DataManager to Dashboard - SIMPLIFIED SIGNAL FLOW
            # Only connect to dashboard's set methods, not to its emit methods
            data_manager.correction_rules_changed.connect(self._dashboard.set_correction_rules)
            data_manager.validation_lists_changed.connect(self._dashboard.set_validation_lists)
            data_manager.entries_changed.connect(self._dashboard.set_entries)

            # Connect DataManager to CorrectionManagerPanel
            data_manager.correction_rules_changed.connect(
                self._correction_manager.set_correction_rules
            )
            data_manager.validation_lists_changed.connect(
                self._correction_manager.set_validation_lists
            )
            data_manager.entries_changed.connect(self._correction_manager.set_entries)

            # Connect DataManager to ReportPanel
            data_manager.entries_changed.connect(self._report_panel.set_entries)
            data_manager.correction_rules_changed.connect(self._report_panel.set_correction_rules)
            data_manager.validation_lists_changed.connect(self._report_panel.set_validation_lists)

            # Connect components to DataManager - SIMPLIFIED TO AVOID LOOPS
            # Only primary sources should connect to DataManager

            # Dashboard -> DataManager (dashboard is the primary UI for file loading)
            self._dashboard.entries_loaded.connect(data_manager.set_entries)
            self._dashboard.entries_updated.connect(data_manager.set_entries)

            # FileImportWidget -> DataManager
            # Get a reference to file_import_widget from dashboard
            file_import_widget = getattr(self._dashboard, "_file_import_widget", None)
            if file_import_widget:
                # This is where corrections are initially loaded
                file_import_widget.corrections_loaded.connect(data_manager.set_correction_rules)

            # CorrectionManagerPanel -> DataManager (for manual edits)
            self._correction_manager.correction_rules_updated.connect(
                data_manager.set_correction_rules
            )
            self._correction_manager.validation_lists_updated.connect(
                data_manager.set_validation_lists
            )

            # Dashboard to MainWindow signals (for status updates ONLY)
            self._dashboard.entries_loaded.connect(self._on_entries_loaded)
            self._dashboard.entries_updated.connect(self._on_entries_updated)
            self._dashboard.corrections_applied.connect(self._on_corrections_applied)

            # For status bar updates only, not to trigger processing
            data_manager.correction_rules_changed.connect(self._on_corrections_loaded)

            # Audit signals to prevent multiple connections
            self._audit_signal_connections()

            logger.info("All signals connected successfully")

        except Exception as e:
            logging.error(f"Error connecting signals: {str(e)}")
            import traceback

            logging.error(traceback.format_exc())

    def _audit_signal_connections(self):
        """
        Audit signal connections to prevent multiple connections.

        This checks for conflicts in signal connections and logs warnings.
        """
        # Dashboard signals to audit
        dashboard_signals = {
            self._dashboard.entries_loaded: [
                self._correction_manager.set_entries,
                self._report_panel.set_entries,
                self._on_entries_loaded,
            ],
            self._dashboard.entries_updated: [
                self._correction_manager.set_entries,
                self._report_panel.set_entries,
                self._on_entries_updated,
            ],
            self._dashboard.corrections_loaded: [
                self._correction_manager.set_correction_rules,
                self._report_panel.set_correction_rules,
                self._on_corrections_loaded,
            ],
            self._dashboard.corrections_applied: [
                self._on_corrections_applied,
            ],
        }

        # Correction manager signals to audit
        correction_manager_signals = {
            self._correction_manager.correction_rules_updated: [
                self._dashboard.corrections_loaded.emit,
            ],
            self._correction_manager.validation_lists_updated: [
                self._dashboard.set_validation_lists,
                self._report_panel.set_validation_lists,
            ],
        }

        # Check for any conflicts in Dashboard signals
        for signal, slots in dashboard_signals.items():
            for slot in slots:
                connection = (signal, slot)
                if connection in self._connected_signals:
                    logging.warning(f"Signal {signal} already connected to slot {slot}")
                else:
                    self._connected_signals.add(connection)

        # Check for any conflicts in Correction manager signals
        for signal, slots in correction_manager_signals.items():
            for slot in slots:
                connection = (signal, slot)
                if connection in self._connected_signals:
                    logging.warning(f"Signal {signal} already connected to slot {slot}")
                else:
                    self._connected_signals.add(connection)

    def _restore_state(self):
        """Restore window state and settings from config."""
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Restoring application state")

        try:
            # Restore window geometry
            geometry_str = self._config.get("Window", "geometry", "")
            if geometry_str:
                try:
                    # Convert from Base64 string back to QByteArray
                    geometry_bytes = QByteArray.fromBase64(geometry_str.encode())
                    self.restoreGeometry(geometry_bytes)
                except Exception as e:
                    logger.warning(f"Failed to restore window geometry: {str(e)}")

            # Restore window state
            state_str = self._config.get("Window", "state", "")
            if state_str:
                try:
                    # Convert from Base64 string back to QByteArray
                    state_bytes = QByteArray.fromBase64(state_str.encode())
                    self.restoreState(state_bytes)
                except Exception as e:
                    logger.warning(f"Failed to restore window state: {str(e)}")

            # Set active tab (convert from string to int)
            active_tab_str = self._config.get("Window", "active_tab", "0")
            try:
                active_tab = int(active_tab_str)
                self._content_widget.setCurrentIndex(active_tab)
            except (ValueError, TypeError):
                logger.warning(f"Invalid active tab value: {active_tab_str}, using default")
                self._content_widget.setCurrentIndex(0)

            # Load initial data from DataManager
            logger.info("Loading initial data")

            # Load correction rules
            rules = self._data_manager.load_saved_correction_rules()
            if rules:
                logger.info(f"Loaded {len(rules)} correction rules")
                # Emit the signal to notify all components
                self._data_manager.correction_rules_changed.emit(rules)

            # Load validation lists
            success = self._data_manager._load_saved_validation_lists()
            lists = self._data_manager.get_validation_lists()

            if not lists or len(lists) < 3:
                logger.info("Not all validation lists were loaded from saved configuration")
                # Try to load default lists as a backup
                logger.info("Loading default validation lists")
                self._data_manager._load_default_validation_lists()
                # Update the lists with any newly loaded ones
                lists = self._data_manager.get_validation_lists()

            # Make sure we have all three types of lists
            if lists and len(lists) > 0:
                logger.info(f"Loaded {len(lists)} validation lists")
                # Emit the signal to notify all components
                self._data_manager.validation_lists_changed.emit(lists)
            else:
                logger.warning("No validation lists could be loaded")

            logger.info("Application state restored successfully")

        except Exception as e:
            logger.error(f"Error restoring state: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())

    def _save_state(self):
        """Save window state to configuration."""
        # Convert QByteArray to Base64 string before saving
        geometry_bytes = self.saveGeometry()
        geometry_str = geometry_bytes.toBase64().data().decode()
        self._config.set("Window", "geometry", geometry_str)

        state_bytes = self.saveState()
        state_str = state_bytes.toBase64().data().decode()
        self._config.set("Window", "state", state_str)

        # Convert index to string
        self._config.set("Window", "active_tab", str(self._content_widget.currentIndex()))

    def closeEvent(self, event: QCloseEvent):
        """
        Handle close event.

        Args:
            event: Close event
        """
        # Save window state
        self._save_state()

        # Accept the event
        event.accept()

    @Slot()
    def _on_new(self):
        """Handle New action."""
        # Display the status message
        self._status_bar.showMessage("New file action triggered", 2000)

    @Slot()
    def _on_open(self):
        """Handle Open action."""
        # Display the status message
        self._status_bar.showMessage("Open file action triggered", 2000)

    @Slot()
    def _on_save(self):
        """Handle Save action."""
        # Display the status message
        self._status_bar.showMessage("Save file action triggered", 2000)

    @Slot()
    def _on_save_as(self):
        """Handle Save As action."""
        # Display the status message
        self._status_bar.showMessage("Save as action triggered", 2000)

    @Slot()
    def _on_about(self):
        """Handle About action."""
        # Show about dialog
        QMessageBox.about(
            self,
            "About Chest Tracker Correction Tool",
            "Chest Tracker Correction Tool v1.0\n\n"
            "A tool for correcting OCR-extracted chest data from Total Battle.",
        )

    @Slot(list)
    def _on_entries_loaded(self, entries: List[ChestEntry]):
        """
        Handle entries loaded.

        Args:
            entries: List of loaded entries
        """
        # Update status bar
        self._status_bar.showMessage(f"Loaded {len(entries)} entries", 2000)

    @Slot(list)
    def _on_entries_updated(self, entries: List[ChestEntry]):
        """
        Handle entries updated.

        Args:
            entries: List of updated entries
        """
        # Update status bar
        self._status_bar.showMessage(f"Updated {len(entries)} entries", 2000)

    @Slot(list)
    def _on_corrections_loaded(self, rules: List[CorrectionRule]):
        """
        Handle corrections loaded.

        Args:
            rules: List of loaded correction rules
        """
        # Update status bar
        self._status_bar.showMessage(f"Loaded {len(rules)} correction rules", 2000)

    @Slot(list)
    def _on_corrections_applied(self, entries: List[ChestEntry]):
        """
        Handle corrections applied.

        Args:
            entries: List of entries with corrections applied
        """
        # Count how many entries were actually corrected
        corrected_count = sum(1 for entry in entries if entry.has_corrections())

        # Update status bar
        if corrected_count > 0:
            self._status_bar.showMessage(f"Applied corrections to {corrected_count} entries", 2000)
        else:
            self._status_bar.showMessage("No corrections were needed", 2000)

    @Slot(str)
    def _on_settings_changed(self, category: str):
        """
        Handle settings changed.

        Args:
            category: Category of settings that changed
        """
        # Update status bar
        self._status_bar.showMessage(f"Settings updated: {category}", 2000)

    @Slot(list)
    def _on_correction_rules_updated(self, rules: List[CorrectionRule]):
        """
        Handle correction rules updated signal.

        Args:
            rules: Updated list of correction rules
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"MainWindow: Received {len(rules)} updated correction rules")

        # Update status bar
        self.statusBar().showMessage(f"Correction rules updated: {len(rules)} rules", 3000)

        # Update data manager - will propagate to all components
        self._data_manager.set_correction_rules(rules)

    def get_entries(self) -> List[ChestEntry]:
        """
        Get the current entries.

        Returns:
            List of chest entries
        """
        if self._dashboard:
            return self._dashboard.get_entries()
        return []

    def get_correction_rules(self) -> List[CorrectionRule]:
        """
        Get the current correction rules.

        Returns:
            List of correction rules
        """
        return self._correction_rules

    def get_validation_lists(self) -> Dict[str, ValidationList]:
        """
        Get the current validation lists.

        Returns:
            Dictionary of validation lists
        """
        if self._validation_panel:
            return self._validation_panel.get_validation_lists()
        return {}

    def _connect_dashboard_signals(self):
        """
        Connect dashboard signals to various components.

        SIMPLIFIED: Only connect signals that don't trigger processing loops
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Connecting dashboard signals")

        # Check if dashboard is initialized
        if not hasattr(self, "_dashboard") or not self._dashboard:
            logger.error("Dashboard not initialized, cannot connect signals")
            return

        # Check if correction manager is initialized
        if not hasattr(self, "_correction_manager") or not self._correction_manager:
            logger.warning("Correction manager not available for signal connection")
            return

        # REMOVED: We don't need these - they already come from DataManager
        # self._dashboard.corrections_loaded.connect(self._correction_manager.set_correction_rules)
        # self._dashboard.correction_rules_updated.connect(
        #     self._correction_manager.set_correction_rules
        # )
        # self._dashboard.validation_lists_updated.connect(
        #     self._correction_manager.set_validation_lists
        # )

        # SIMPLIFIED: Only connect UI update signals, not data processing signals
        self._dashboard.entries_loaded.connect(self._on_entries_loaded)
        self._dashboard.entries_updated.connect(self._on_entries_updated)
        self._dashboard.corrections_applied.connect(self._on_corrections_applied)

        # REMOVED: Circular references
        # self._correction_manager.correction_rules_updated.connect(
        #     self._dashboard.set_correction_rules
        # )
        # self._correction_manager.validation_lists_updated.connect(
        #     self._dashboard.set_validation_lists
        # )

        logger.info("Dashboard signals connected successfully")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
