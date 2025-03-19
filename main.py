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
from src.ui.main_window import MainWindow
from src.services.config_manager import ConfigManager
from src.ui.styles import get_stylesheet
from src.utils.logging_config import configure_logging


def setup_environment():
    """
    Setup the application environment.

    Creates necessary directories if they don't exist and
    initializes basic configuration.
    """
    try:
        # Initialize configuration first - ConfigManager will create default directories
        logging.info("Initializing ConfigManager...")
        config_manager = ConfigManager()
        logging.info("ConfigManager initialized successfully")

        # Log the configuration sections
        sections = config_manager.get_sections()
        logging.info(f"Configuration sections: {sections}")

        # Check if the Paths section exists
        if "Paths" in sections:
            logging.info("Paths section found in configuration")

            # Log key path settings
            data_dir = config_manager.get_path("data_dir")
            abs_data_dir = config_manager.get_absolute_path(data_dir)
            logging.info(f"Data directory: {data_dir} (absolute: {abs_data_dir})")

            correction_rules_file = config_manager.get_path("correction_rules_file")
            abs_correction_rules = config_manager.get_absolute_path(correction_rules_file)
            logging.info(
                f"Correction rules file: {correction_rules_file} (absolute: {abs_correction_rules})"
            )

            # Check if critical paths exist
            if not abs_data_dir.exists():
                logging.warning(f"Data directory does not exist: {abs_data_dir}")
                config_manager._create_default_directories()
        else:
            logging.warning("Paths section not found in configuration! Creating default config...")
            config_manager._create_default_config()
            config_manager.save()
            config_manager._create_default_directories()
    except Exception as e:
        logging.error(f"Error setting up environment: {e}")
        traceback.print_exc()


def main():
    """
    Main entry point for the application.

    Creates the Qt application and main window.
    """
    try:
        # Set up enhanced logging with timestamps
        configure_logging(log_to_file=True, debug_mode=True)

        # Log starting of application with details
        logging.info("=" * 80)
        logging.info("APPLICATION STARTING")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Working directory: {Path.cwd()}")
        logging.info(f"Command line: {' '.join(sys.argv)}")
        logging.info("=" * 80)

        # Initialize environment
        setup_environment()

        # Create QApplication instance
        app = QApplication(sys.argv)
        app.setApplicationName("Chest Tracker Correction Tool")
        app.setOrganizationName("TotalBattleTools")

        # Set application stylesheet
        app.setStyleSheet(get_stylesheet())

        # Set up signal tracking
        logging.info("Setting up MainWindow")

        try:
            # Create main window - with extra error handling
            main_window = MainWindow()
            logging.info("MainWindow created successfully")

            # Show main window
            main_window.show()
            logging.info("MainWindow shown successfully")
        except Exception as window_error:
            logging.critical(f"Error creating or showing MainWindow: {window_error}", exc_info=True)
            raise

        logging.info("Application started successfully")

        # Start the event loop
        return app.exec()
    except Exception as e:
        logging.critical(f"Fatal error starting application: {e}")
        logging.critical(traceback.format_exc())

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
