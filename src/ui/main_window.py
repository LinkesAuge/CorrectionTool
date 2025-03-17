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

from PySide6.QtCore import QSize, Qt, Signal, Slot
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
from src.ui.dashboard import Dashboard
from src.ui.correction_manager_panel import CorrectionManagerPanel
from src.ui.reports_panel import ReportPanel
from src.ui.settings_dialog import SettingsDialog
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
        self._dashboard = None
        self._validation_panel = None
        self._report_panel = None
        self._validation_lists = {}
        self._correction_rules = []
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
        self._settings_action.triggered.connect(self._on_settings)

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

        # Add navigation buttons to sidebar
        sidebar_layout.addWidget(self._dashboard_btn)
        sidebar_layout.addWidget(self._validation_btn)
        sidebar_layout.addWidget(self._reports_btn)

        # Add spacer
        sidebar_layout.addStretch()

        # Add settings button to sidebar
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self._on_settings)
        sidebar_layout.addWidget(settings_btn)

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

        # Switch content page
        self._content_widget.setCurrentIndex(page_index)

        # Save active tab
        self._config.set("window", "active_tab", page_index)

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

        # Set initial page
        active_tab = self._config.get_int("window", "active_tab", fallback=0)
        self._content_widget.setCurrentIndex(active_tab)

        # Update button states
        self._dashboard_btn.setChecked(active_tab == 0)
        self._validation_btn.setChecked(active_tab == 1)
        self._reports_btn.setChecked(active_tab == 2)

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

    def _connect_signals(self):
        """Connect signals to slots."""
        try:
            # Dashboard signals
            self._dashboard.entries_loaded.connect(self._correction_manager.set_entries)
            self._dashboard.entries_loaded.connect(self._report_panel.set_entries)
            self._dashboard.entries_loaded.connect(self._on_entries_loaded)

            self._dashboard.entries_updated.connect(self._correction_manager.set_correction_rules)
            self._dashboard.entries_updated.connect(self._report_panel.set_entries)
            self._dashboard.entries_updated.connect(self._on_entries_updated)

            self._dashboard.corrections_loaded.connect(
                self._correction_manager.set_correction_rules
            )
            self._dashboard.corrections_loaded.connect(self._report_panel.set_correction_rules)
            self._dashboard.corrections_loaded.connect(self._on_corrections_loaded)

            self._dashboard.corrections_applied.connect(self._on_corrections_applied)

            # Correction manager signals
            self._correction_manager.correction_rules_updated.connect(
                self._dashboard.set_correction_rules
            )
            self._correction_manager.validation_lists_updated.connect(
                self._dashboard.set_validation_lists
            )
            self._correction_manager.validation_lists_updated.connect(
                self._report_panel.set_validation_lists
            )

            # Audit signals to prevent multiple connections
            self._audit_signal_connections()

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
                self._correction_manager.set_correction_rules,
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
                self._dashboard.set_correction_rules,
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
        """Restore window state from configuration."""
        # Restore window geometry
        geometry = self._config.get("window", "geometry", fallback=None)
        if geometry:
            self.restoreGeometry(geometry)

        # Restore window state
        state = self._config.get("window", "state", fallback=None)
        if state:
            self.restoreState(state)

        # Restore active tab
        active_tab = self._config.get_int("window", "active_tab", fallback=0)
        self._content_widget.setCurrentIndex(active_tab)

        # Update sidebar button states
        self._dashboard_btn.setChecked(active_tab == 0)
        self._validation_btn.setChecked(active_tab == 1)
        self._reports_btn.setChecked(active_tab == 2)

    def closeEvent(self, event: QCloseEvent):
        """
        Handle close event.

        Args:
            event: Close event
        """
        # Save window state
        self._config.set("window", "geometry", self.saveGeometry())
        self._config.set("window", "state", self.saveState())
        self._config.set("window", "active_tab", self._content_widget.currentIndex())

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
    def _on_settings(self):
        """Handle Settings action."""
        # Create and show settings dialog
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec():
            # Settings were saved, update UI if needed
            self._status_bar.showMessage("Settings saved", 2000)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
