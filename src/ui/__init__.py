"""
UI module for the Chest Tracker Correction Tool.

This module contains UI components for the application.
Implements lazy loading for components with circular dependencies.
"""

# Direct imports for utility functions and constants
from src.ui.styles import get_stylesheet, COLORS


# Lazy-loaded getters for UI components
def get_main_window():
    """Lazy loading getter for MainWindow class."""
    from src.ui.main_window_interface import MainWindowInterface

    return MainWindowInterface


def get_navigation_panel():
    """Lazy loading getter for NavigationPanel class."""
    from src.ui.navigation_panel import NavigationPanel

    return NavigationPanel


def get_file_panel():
    """Lazy loading getter for FilePanel class."""
    from src.ui.file_panel import FilePanel

    return FilePanel


def get_corrector_panel():
    """Lazy loading getter for CorrectorPanel class."""
    from src.ui.corrector_panel import CorrectorPanel

    return CorrectorPanel


def get_validation_panel():
    """Lazy loading getter for ValidationPanel class."""
    from src.ui.validation_panel import ValidationPanel

    return ValidationPanel


def get_preview_panel():
    """Lazy loading getter for PreviewPanel class."""
    from src.ui.preview_panel import PreviewPanel

    return PreviewPanel


def get_settings_panel():
    """Lazy loading getter for SettingsPanel class."""
    from src.ui.settings_panel import SettingsPanel

    return SettingsPanel


def get_report_panel():
    """Lazy loading getter for ReportPanel class."""
    from src.ui.report_panel import ReportPanel

    return ReportPanel


def get_table_models():
    """Lazy loading getter for table model classes."""
    from src.ui.table_models import ChestEntryTableModel, ChestEntryFilterProxyModel

    return ChestEntryTableModel, ChestEntryFilterProxyModel


# Define what is publicly available
__all__ = [
    # Direct imports
    "get_stylesheet",
    "COLORS",
    # Lazy-loaded getters
    "get_main_window",
    "get_navigation_panel",
    "get_file_panel",
    "get_corrector_panel",
    "get_validation_panel",
    "get_preview_panel",
    "get_settings_panel",
    "get_report_panel",
    "get_table_models",
]
