#!/usr/bin/env python3
"""
check_dependencies.py

Description: Script to verify that there are no circular dependencies in the codebase
Usage:
    python check_dependencies.py
"""

import importlib
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# List of modules to check
MODULES_TO_CHECK = [
    # Core modules
    "src",
    "src.models",
    "src.services",
    "src.ui",
    "src.interfaces",
    # Models
    "src.models.chest_entry",
    "src.models.validation_list",
    "src.models.correction_rule",
    # Services
    "src.services.dataframe_store",
    "src.services.file_service",
    "src.services.correction_service",
    "src.services.validation_service",
    "src.services.service_factory",
    "src.services.config_manager",
    # UI components
    "src.ui.main_window_refactor",
    "src.ui.adapters.entry_table_adapter",
    "src.ui.adapters.correction_rule_table_adapter",
    "src.ui.adapters.validation_list_combo_adapter",
    # Interfaces
    "src.interfaces.events",
    "src.interfaces.data_store",
    "src.interfaces.ui_adapters",
    "src.interfaces.service_factory",
    "src.interfaces.file_service",
    "src.interfaces.correction_service",
    "src.interfaces.validation_service",
    "src.interfaces.config_manager",
]


def check_module(module_name):
    """
    Attempt to import a module and report any errors.

    Args:
        module_name (str): Name of the module to import

    Returns:
        bool: True if import succeeded, False otherwise
    """
    try:
        # Force reload to ensure we're not getting cached results
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)
        logger.info(f"✓ Successfully imported {module_name}")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import {module_name}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"✗ Error importing {module_name}: {str(e)}")
        return False


def main():
    """
    Main function to check all modules for circular dependencies.
    """
    logger.info("Checking for circular dependencies...")

    success_count = 0
    failure_count = 0

    for module_name in MODULES_TO_CHECK:
        if check_module(module_name):
            success_count += 1
        else:
            failure_count += 1

    logger.info(f"Dependency check complete. Success: {success_count}, Failures: {failure_count}")

    if failure_count > 0:
        logger.warning("Some modules have circular dependencies. Review the errors above.")
        return 1
    else:
        logger.info("No circular dependencies detected!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
