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

    # Set up logging format and level - using WARNING as default root level
    logging.basicConfig(
        level=logging.WARNING,  # Default level for all loggers - less verbose
        format="%(levelname)s - %(name)s - %(message)s",
        handlers=[
            # Log all levels to file with UTF-8 encoding
            logging.FileHandler(log_file, encoding="utf-8"),
            # Only show warnings and above on console to reduce noise
        ],
    )

    # Configure console handler to be even more minimal - ERROR level only
    # Force ASCII encoding for console output to avoid encoding errors with non-ASCII characters
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    # Define a filter to remove non-ASCII characters for console output
    class ASCIIFilter(logging.Filter):
        def filter(self, record):
            if isinstance(record.msg, str):
                # Replace non-ASCII characters with '?' for console output
                record.msg = record.msg.encode("ascii", "replace").decode("ascii")
            return True

    # Add the filter to the console handler
    console_handler.addFilter(ASCIIFilter())

    # Replace the default console handler with our custom one
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            root_logger.removeHandler(handler)
    root_logger.addHandler(console_handler)

    # Set application logger to INFO for basic app status messages
    app_logger = logging.getLogger("src")
    app_logger.setLevel(logging.INFO)

    # Set PySide logging to ERROR level to only show serious issues
    for logger_name in ["PySide6", "QtCore", "QtWidgets", "QtGui"]:
        logging.getLogger(logger_name).setLevel(logging.ERROR)

    # Reduce verbosity for validation and correction logs - only show warnings
    for logger_name in [
        "src.models.validation_list",
        "src.services.corrector",
        "src.services.data_manager",
        "src.ui.validation_list_widget",
        "src.ui.dashboard",
        "src.ui.correction_manager_panel",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Log uncaught exceptions
    def exception_handler(exc_type, exc_value, exc_traceback):
        logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler

    # Set recursion limit to prevent infinite loops
    sys.setrecursionlimit(1000)  # Default is 1000, setting explicitly

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
            logging.info(f"Ensured directory exists: {directory}")  # Changed from debug to info

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
