#!/usr/bin/env python3
"""
main.py

Description: Main entry point for the Chest Tracker Correction Tool
Usage:
    python main.py
"""

import sys
import traceback
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon, QFontDatabase

from src.ui.main_window import MainWindow
from src.services.config_manager import ConfigManager
from src.utils.helpers import ensure_directory_exists
from src.utils.constants import DEFAULT_DIRECTORIES
from src.ui.styles import get_stylesheet


# Configure logging
def setup_logging():
    """Configure logging for the application."""
    log_file = Path("correction_tool.log")

    # Set up logging format and level
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
    )

    # Log uncaught exceptions
    def exception_handler(exc_type, exc_value, exc_traceback):
        logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler

    logging.info("Logging initialized")


def setup_environment():
    """
    Setup the application environment.

    Creates necessary directories if they don't exist and
    initializes basic configuration.
    """
    try:
        # Create data directories if they don't exist
        for directory in DEFAULT_DIRECTORIES:
            ensure_directory_exists(directory)
            logging.info(f"Ensured directory exists: {directory}")

        # Initialize configuration
        config_manager = ConfigManager()
        # The ConfigManager loads configuration automatically in its __init__ method
        # Just create an instance to ensure it exists
        logging.info("Configuration initialized")
    except Exception as e:
        logging.error(f"Error setting up environment: {e}")
        traceback.print_exc()


def main():
    """
    Main entry point for the application.

    Creates the Qt application and main window.
    """
    try:
        # Set up logging first
        setup_logging()

        # Initialize environment
        setup_environment()

        # Create QApplication instance
        app = QApplication(sys.argv)
        app.setApplicationName("Chest Tracker Correction Tool")
        app.setOrganizationName("TotalBattleTools")

        # Set application stylesheet
        app.setStyleSheet(get_stylesheet())

        # Load custom fonts if needed
        # QFontDatabase.addApplicationFont("resources/fonts/custom_font.ttf")

        # Set application icon
        # app.setWindowIcon(QIcon("resources/icons/app_icon.png"))

        # Create and show main window
        main_window = MainWindow()
        main_window.show()

        logging.info("Application started successfully")

        # Start the event loop
        return app.exec()
    except Exception as e:
        logging.critical(f"Fatal error starting application: {e}")
        traceback.print_exc()

        # Show error dialog to user
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setWindowTitle("Application Error")
        error_msg.setText("Failed to start the application")
        error_msg.setInformativeText(str(e))
        error_msg.setDetailedText(traceback.format_exc())
        error_msg.exec()

        return 1


if __name__ == "__main__":
    sys.exit(main())
