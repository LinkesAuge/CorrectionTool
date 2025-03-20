#!/usr/bin/env python3
"""
run_interface_app.py

Description: Entry point for the interface-based application
Usage:
    python -m src.run_interface_app
"""

import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.app_bootstrapper import AppBootstrapper
from src.ui.main_window_interface import MainWindowInterface


def setup_logging():
    """Set up logging configuration."""
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(logs_dir / "app.log"),
        ],
    )


def main():
    """Run the interface-based application."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting interface-based application")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Chest Tracker Correction Tool")
    app.setOrganizationName("Chest Tracker")

    # Create the bootstrapper
    bootstrapper = AppBootstrapper()

    try:
        # Initialize the bootstrapper
        logger.info("Initializing bootstrapper")
        bootstrapper.initialize()

        # Get service factory
        logger.info("Creating main window with interface implementation")
        service_factory = bootstrapper.service_factory

        # Create main window using the interface directly
        main_window = MainWindowInterface(service_factory)
        main_window.show()

        # Run the application
        logger.info("Running application")
        return app.exec()
    except Exception as e:
        logger.exception(f"Error during application startup: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
