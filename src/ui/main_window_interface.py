"""
main_window_interface.py

Description: Interface-based main application window that uses dependency injection
Usage:
    from src.app_bootstrapper import AppBootstrapper
    from src.ui.main_window_interface import MainWindowInterface

    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()
    service_factory = bootstrapper.get_service_factory()

    main_window = MainWindowInterface(service_factory)
    main_window.show()
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, cast

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

# Import interfaces
from src.interfaces import (
    IServiceFactory,
    IDataStore,
    IFileService,
    ICorrectionService,
    IValidationService,
    IConfigManager,
)
from src.interfaces.events import EventType, EventHandler, EventData

# Import interface-based components
from src.ui.report_panel_interface import ReportPanelInterface
from src.ui.settings_panel_interface import SettingsPanelInterface
from src.ui.dashboard_interface import DashboardInterface
from src.ui.correction_manager_interface import CorrectionManagerInterface
from src.ui.validation_panel_interface import ValidationPanelInterface
from src.ui.styles import COLORS, SIDEBAR_STYLE


class MainWindowInterface(QMainWindow):
    """
    Interface-based main application window.

    This is the main window of the application, using interface-based architecture with
    dependency injection for services.

    Attributes:
        _service_factory: IServiceFactory instance
        _config_manager: IConfigManager instance
        _data_store: IDataStore instance
        _file_service: IFileService instance
        _correction_service: ICorrectionService instance
        _validation_service: IValidationService instance

    Implementation Notes:
        - Uses dependency injection for services
        - Uses sidebar navigation instead of menu bar
        - Uses stackable content area for different views
        - Uses interface-based services for all data operations
        - Implements event-based communication
    """

    def __init__(self, service_factory: IServiceFactory):
        """
        Initialize the main window with dependency injection.

        Args:
            service_factory: IServiceFactory instance for accessing services
        """
        super().__init__()

        # Store the service factory
        self._service_factory = service_factory

        # Get interfaces from service factory
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

        # Setup logging
        self._logger = logging.getLogger(__name__)

        # These will be created during setup
        self._dashboard = None
        self._correction_manager = None
        self._validation_panel = None
        self._report_panel = None
        self._connected_events = set()  # Track connected events

        # Set window properties
        self.setWindowTitle("Chest Tracker Correction Tool")
        self.resize(1280, 800)

        # Setup UI
        self._setup_actions()
        self._setup_sidebar()
        self._setup_status_bar()
        self._setup_content()

        # Connect events
        self._connect_events()

        # Restore state
        self._restore_state()
        self._logger.info("MainWindow initialized")

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
        self._config_manager.set_value("Window", "active_tab", str(page_index))

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
        active_tab = self._config_manager.get_int("Window", "active_tab", fallback=0)
        self._content_widget.setCurrentIndex(active_tab)

        # Update button states
        self._dashboard_btn.setChecked(active_tab == 0)
        self._validation_btn.setChecked(active_tab == 1)
        self._reports_btn.setChecked(active_tab == 2)
        self._settings_btn.setChecked(active_tab == 3)

    def _setup_dashboard_page(self):
        """Set up the dashboard page."""
        # Create dashboard with interfaces
        self._dashboard = DashboardInterface(self._service_factory, parent=self)

        # Add to content stack
        self._content_widget.addWidget(self._dashboard)

    def _setup_correction_manager_page(self):
        """Set up the correction manager page."""
        # Create correction manager with interfaces
        self._correction_manager = CorrectionManagerInterface(self._service_factory, parent=self)

        # Add to content stack
        self._content_widget.addWidget(self._correction_manager)

    def _setup_reports_page(self):
        """Set up the reports page."""
        # Create reports panel
        self._report_panel = ReportPanelInterface(self._service_factory, parent=self)

        # Add to content stack
        self._content_widget.addWidget(self._report_panel)

    def _setup_settings_page(self):
        """Set up the settings page."""
        # Create settings panel
        self._settings_panel = SettingsPanelInterface(self._service_factory, parent=self)

        # Add to content stack
        self._content_widget.addWidget(self._settings_panel)

    def _connect_events(self):
        """Connect to events from services."""
        # Subscribe to data store events
        self._data_store.subscribe(EventType.IMPORT_COMPLETED, self._on_entries_loaded)
        self._data_store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
        self._data_store.subscribe(EventType.CORRECTION_RULES_UPDATED, self._on_corrections_loaded)
        self._data_store.subscribe(
            EventType.CORRECTION_RULES_UPDATED, self._on_correction_rules_updated
        )
        self._data_store.subscribe(
            EventType.VALIDATION_LISTS_UPDATED, self._on_validation_lists_updated
        )

        # Add events to connected list
        self._connected_events.add(EventType.IMPORT_COMPLETED)
        self._connected_events.add(EventType.ENTRIES_UPDATED)
        self._connected_events.add(EventType.CORRECTION_RULES_UPDATED)
        self._connected_events.add(EventType.CORRECTION_RULES_UPDATED)
        self._connected_events.add(EventType.VALIDATION_LISTS_UPDATED)

        # Connect dashboard events
        self._connect_dashboard_events()

    def _restore_state(self):
        """Restore window state from config."""
        # Restore window geometry
        geometry = self._config_manager.get_value("Window", "geometry")
        if geometry:
            self.restoreGeometry(QByteArray.fromHex(geometry.encode()))

        # Restore window state
        state = self._config_manager.get_value("Window", "state")
        if state:
            self.restoreState(QByteArray.fromHex(state.encode()))

    def _save_state(self):
        """Save window state to config."""
        # Save window geometry
        self._config_manager.set_value(
            "Window", "geometry", self.saveGeometry().toHex().data().decode()
        )

        # Save window state
        self._config_manager.set_value("Window", "state", self.saveState().toHex().data().decode())

    def closeEvent(self, event: QCloseEvent):
        """
        Handle the window close event.

        Args:
            event: Close event
        """
        # Save window state
        self._save_state()

        # Accept the event
        event.accept()

    @Slot()
    def _on_new(self):
        """Handle the new action."""
        # Implement new file action
        self._data_store.clear_entries()
        self._status_bar.showMessage("Created new file")

    @Slot()
    def _on_open(self):
        """Handle the open action."""
        # Redirect to dashboard open
        if self._dashboard:
            self._dashboard.open_file()

    @Slot()
    def _on_save(self):
        """Handle the save action."""
        # Redirect to dashboard save
        if self._dashboard:
            self._dashboard.save_file()

    def _on_entries_loaded(self, event_data: Dict[str, Any]) -> None:
        """
        Handle entries loaded event.

        Args:
            event_data: Event data
        """
        count = event_data.get("count", 0)
        file_path = event_data.get("file_path", "")

        # Update status bar
        self._status_bar.showMessage(f"Loaded {count} entries from {Path(file_path).name}")

        # Log the event
        self._logger.info(f"Loaded {count} entries from {file_path}")

    def _on_entries_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle entries updated event.

        Args:
            event_data: Event data
        """
        count = event_data.get("count", 0)

        # Update status bar
        self._status_bar.showMessage(f"Updated {count} entries")

        # Log the event
        self._logger.info(f"Updated {count} entries")

    def _on_corrections_loaded(self, event_data: Dict[str, Any]) -> None:
        """
        Handle corrections loaded event.

        Args:
            event_data: Event data
        """
        count = event_data.get("count", 0)
        file_path = event_data.get("file_path", "")

        # Update status bar
        self._status_bar.showMessage(f"Loaded {count} correction rules from {Path(file_path).name}")

        # Log the event
        self._logger.info(f"Loaded {count} correction rules from {file_path}")

    def _on_correction_rules_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle correction rules updated event.

        Args:
            event_data: Event data
        """
        count = event_data.get("count", 0)

        # Update status bar
        self._status_bar.showMessage(f"Updated {count} correction rules")

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

        # Update status bar
        if list_type:
            self._status_bar.showMessage(
                f"Updated {list_type} validation list with {count} entries"
            )
        else:
            self._status_bar.showMessage(f"Updated validation lists")

        # Log the event
        self._logger.info(f"Updated validation list: {list_type} with {count} entries")

    def _connect_dashboard_events(self):
        """Connect dashboard-specific events."""
        # This will be implemented when Dashboard is updated to use interfaces
        pass

    # Bridge methods for backward compatibility with old MainWindow API

    def get_entries(self) -> List[Dict]:
        """
        Get the loaded entries as a list of dictionaries.

        Returns:
            List of entries
        """
        entries_df = self._data_store.get_entries()
        if entries_df.empty:
            return []

        return entries_df.to_dict("records")

    def get_correction_rules(self) -> List[Dict]:
        """
        Get the correction rules as a list of dictionaries.

        Returns:
            List of correction rules
        """
        rules_df = self._data_store.get_correction_rules()
        if rules_df.empty:
            return []

        return rules_df.to_dict("records")

    def get_validation_lists(self) -> Dict[str, List[str]]:
        """
        Get the validation lists.

        Returns:
            Dictionary of validation lists
        """
        return {
            "player": self._data_store.get_validation_list("player"),
            "chest_type": self._data_store.get_validation_list("chest_type"),
            "source": self._data_store.get_validation_list("source"),
        }
