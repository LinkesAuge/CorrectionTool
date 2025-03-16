"""
main_window.py

Description: Main application window
Usage:
    from src.ui.main_window import MainWindow
    window = MainWindow()
    window.show()
"""

import sys
from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QMainWindow, QSplitter, QStackedWidget, QVBoxLayout, QWidget
)

from src.services.config_manager import ConfigManager
from src.ui.navigation_panel import NavigationPanel
from src.ui.file_panel import FilePanel
from src.ui.corrector_panel import CorrectorPanel
from src.ui.validation_panel import ValidationPanel
from src.ui.styles import get_stylesheet


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Provides the main UI framework for the application.
    
    Attributes:
        _config (ConfigManager): Application configuration
        _navigation_panel (NavigationPanel): Left navigation panel
        _content_stack (QStackedWidget): Stacked widget for content pages
        _content_widgets (Dict[str, QWidget]): Dictionary of content widgets
        
    Implementation Notes:
        - Uses a horizontal layout with navigation panel on the left
        - Content area is split horizontally (filter panel + data panel)
        - Pages are managed with a stacked widget
    """
    
    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        
        # Initialize configuration
        self._config = ConfigManager()
        
        # Setup window properties
        self.setWindowTitle("Chest Tracker Correction Tool")
        self._window_width = self._config.get_int("UI", "window_width", fallback=1280)
        self._window_height = self._config.get_int("UI", "window_height", fallback=800)
        self.resize(self._window_width, self._window_height)
        
        # Apply the stylesheet
        self.setStyleSheet(get_stylesheet())
        
        # Initialize UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Create main widget and layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create navigation panel
        self._navigation_panel = NavigationPanel()
        self._navigation_panel.navigation_changed.connect(self._on_navigation_changed)
        
        # Create content stack
        self._content_stack = QStackedWidget()
        self._content_widgets = {}
        
        # Add initial pages
        self._setup_dashboard_page()
        self._setup_file_management_page()
        self._setup_corrections_page()
        self._setup_validation_page()
        self._setup_reports_page()
        self._setup_settings_page()
        
        # Add widgets to layouts
        main_layout.addWidget(self._navigation_panel)
        main_layout.addWidget(self._content_stack)
        
        # Set main layout
        self.setCentralWidget(central_widget)
    
    def _setup_dashboard_page(self) -> None:
        """Set up the dashboard page."""
        # Create dashboard page
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        
        # Split dashboard layout
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - File Panel
        self._file_panel = FilePanel()
        
        # Right panel - Corrector Panel
        self._corrector_panel = CorrectorPanel()
        
        # Add panels to splitter
        splitter.addWidget(self._file_panel)
        splitter.addWidget(self._corrector_panel)
        
        # Set initial splitter sizes
        left_panel_ratio = self._config.get_float("UI", "left_panel_ratio", fallback=0.33)
        splitter.setSizes([
            int(self._window_width * left_panel_ratio),
            int(self._window_width * (1 - left_panel_ratio))
        ])
        
        # Add splitter to layout
        dashboard_layout.addWidget(splitter)
        
        # Add page to content stack
        self._add_content_page("Dashboard", dashboard_widget)
    
    def _setup_file_management_page(self) -> None:
        """Set up the file management page."""
        # Create file management page
        file_widget = QWidget()
        file_layout = QVBoxLayout(file_widget)
        file_layout.setContentsMargins(20, 20, 20, 20)
        
        # For now, reuse the file panel
        file_panel = FilePanel()
        file_layout.addWidget(file_panel)
        
        # Add page to content stack
        self._add_content_page("File Management", file_widget)
    
    def _setup_corrections_page(self) -> None:
        """Set up the corrections page."""
        # Create corrections page
        corrections_widget = QWidget()
        corrections_layout = QVBoxLayout(corrections_widget)
        corrections_layout.setContentsMargins(20, 20, 20, 20)
        
        # For now, reuse the corrector panel
        corrector_panel = CorrectorPanel()
        corrections_layout.addWidget(corrector_panel)
        
        # Add page to content stack
        self._add_content_page("Corrections", corrections_widget)
    
    def _setup_validation_page(self) -> None:
        """Set up the validation page."""
        # Create validation page
        validation_widget = QWidget()
        validation_layout = QVBoxLayout(validation_widget)
        validation_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add validation panel
        self._validation_panel = ValidationPanel()
        validation_layout.addWidget(self._validation_panel)
        
        # Add page to content stack
        self._add_content_page("Validation", validation_widget)
    
    def _setup_reports_page(self) -> None:
        """Set up the reports page."""
        # Placeholder for reports page
        reports_widget = QWidget()
        reports_layout = QVBoxLayout(reports_widget)
        reports_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add page to content stack
        self._add_content_page("Reports", reports_widget)
    
    def _setup_settings_page(self) -> None:
        """Set up the settings page."""
        # Placeholder for settings page
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add page to content stack
        self._add_content_page("Settings", settings_widget)
    
    def _add_content_page(self, name: str, widget: QWidget) -> None:
        """
        Add a content page.
        
        Args:
            name (str): Page name
            widget (QWidget): Page widget
        """
        self._content_stack.addWidget(widget)
        self._content_widgets[name] = widget
    
    def _connect_signals(self) -> None:
        """Connect signals between components."""
        # Connect file panel signals to corrector panel
        self._file_panel.entries_loaded.connect(self._corrector_panel.set_entries)
        self._file_panel.corrections_applied.connect(self._corrector_panel.on_corrections_applied)
        
        # Connect validation panel signals to corrector panel
        self._validation_panel.validation_lists_updated.connect(self._corrector_panel.set_validation_lists)
    
    def _on_navigation_changed(self, page_name: str) -> None:
        """
        Handle navigation changes.
        
        Args:
            page_name (str): Name of the selected page
        """
        if page_name in self._content_widgets:
            index = self._content_stack.indexOf(self._content_widgets[page_name])
            if index >= 0:
                self._content_stack.setCurrentIndex(index)
    
    def closeEvent(self, event) -> None:
        """
        Handle window close event.
        
        Save configuration before closing.
        
        Args:
            event: Close event
        """
        # Save window size
        self._config.set("UI", "window_width", self.width())
        self._config.set("UI", "window_height", self.height())
        self._config.save()
        
        # Accept the event
        event.accept() 