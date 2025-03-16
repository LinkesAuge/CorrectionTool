#!/usr/bin/env python3
"""
main.py

Description: Main entry point for the Chest Tracker Correction Tool
Usage:
    python main.py
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.services.config_manager import ConfigManager
from src.utils.helpers import ensure_directory_exists
from src.utils.constants import DEFAULT_DIRECTORIES


def setup_environment():
    """
    Setup the application environment.
    
    Creates necessary directories if they don't exist and 
    initializes basic configuration.
    """
    # Create data directories if they don't exist
    for directory in DEFAULT_DIRECTORIES:
        ensure_directory_exists(directory)
    
    # Ensure config file exists
    config_file = Path("config.ini")
    if not config_file.exists():
        ConfigManager.create_default_config()


def main():
    """
    Main entry point for the application.
    
    Creates the application instance and starts the main event loop.
    """
    # Setup environment
    setup_environment()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Chest Tracker Correction Tool")
    app.setOrganizationName("OCR Correction Tools")
    
    # Create and show the main window
    main_window = MainWindow()
    main_window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
