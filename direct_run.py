#!/usr/bin/env python3
"""
direct_run.py

A direct entry point to run the MainWindow with minimal imports.
This avoids circular dependencies by directly importing the MainWindow class.
"""

import logging
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def bypass_init_modules():
    """
    Bypass __init__.py module importing to avoid circular dependencies.
    This is a hack for testing purposes.
    """
    import builtins

    original_import = builtins.__import__

    def custom_import(name, *args, **kwargs):
        # Skip certain imports to avoid circular dependencies
        if name in [
            "src.ui.__init__",
            "src.models.__init__",
            "src.services.__init__",
            "src.utils.__init__",
        ]:
            import sys
            from types import ModuleType

            module = ModuleType(name)
            sys.modules[name] = module
            return module
        return original_import(name, *args, **kwargs)

    builtins.__import__ = custom_import


if __name__ == "__main__":
    logger.info("Starting application directly")

    try:
        # Bypass initialization to avoid circular imports
        bypass_init_modules()

        # Add the project root to path
        sys.path.insert(0, os.path.abspath("."))

        # Import PySide6
        from PySide6.QtWidgets import QApplication

        # Import the MainWindow directly without going through __init__.py
        # We load the module directly to avoid circular dependencies
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "main_window_refactor", "src/ui/main_window_refactor.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        MainWindow = module.MainWindow

        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("Chest Tracker Correction Tool")
        app.setOrganizationName("ChestTracker")

        # Create and show main window
        main_window = MainWindow()
        main_window.show()

        logger.info("Application started")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        sys.exit(1)
