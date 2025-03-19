#!/usr/bin/env python3
"""
run_interface_app.py

Description: Runs the application with the new interface-based architecture
Usage:
    python run_interface_app.py
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    """
    Main function to run the application with the new interface architecture.
    """
    logger.info("Starting application with interface-based architecture")

    # Import after logging setup to capture initialization logs
    from src.app_bootstrapper import AppBootstrapper
    from src.ui import get_main_window

    # Initialize the application
    app = QApplication(sys.argv)

    # Initialize bootstrapper before creating UI
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()

    logger.info("Creating main window...")

    # Create main window using new architecture
    MainWindow = get_main_window()
    main_window = MainWindow()

    # Show window
    main_window.show()

    # Set window title
    main_window.setWindowTitle("Chest Tracker Correction Tool (Interface Edition)")

    logger.info("Application running")

    # Start event loop
    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)
