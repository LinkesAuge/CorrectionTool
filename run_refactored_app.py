#!/usr/bin/env python3
"""
run_refactored_app.py

Description: Script to run the refactored application with the new data management system
Usage:
    python run_refactored_app.py
"""

import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting refactored application")

    try:
        # Import PySide6
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QSize, Qt, Signal, Slot, QByteArray
        from PySide6.QtGui import QAction, QCloseEvent, QIcon, QKeySequence

        # Import services directly
        from src.services.service_factory import ServiceFactory
        from src.services.dataframe_store import DataFrameStore, EventType
        from src.services.file_service import FileService
        from src.services.correction_service import CorrectionService
        from src.services.validation_service import ValidationService
        from src.services.config_manager import ConfigManager

        # Now attempt to import the MainWindow
        sys.path.insert(0, str(Path("D:/Projekte/CorrectionTool").absolute()))
        from src.ui.main_window_refactor import MainWindow

        # Create app
        app = QApplication(sys.argv)
        app.setApplicationName("Chest Tracker Correction Tool")
        app.setOrganizationName("ChestTracker")

        # Create main window
        main_window = MainWindow()
        main_window.show()

        logger.info("Application started")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        sys.exit(1)
