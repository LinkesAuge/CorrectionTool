#!/usr/bin/env python
"""
Test App Startup

Description: Test script to verify that validation lists are loaded at app startup
"""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the Python path so we can import the src module
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_validation_lists_loading():
    """Test if validation lists are loaded at app startup."""
    logger.info("Starting validation list loading test")

    # Import here to avoid circular imports
    from src.services.data_manager import DataManager

    # Initialize the DataManager
    logger.info("Initializing DataManager")
    data_manager = DataManager()

    # Explicitly load validation lists
    lists = data_manager.load_default_validation_lists()

    # Check if all required validation lists are loaded

    # Log the loaded validation lists
    logger.info(
        f"Loaded player list with {len(lists.get('player', {}).entries if 'player' in lists else [])} entries"
    )
    logger.info(
        f"Loaded chest type list with {len(lists.get('chest_type', {}).entries if 'chest_type' in lists else [])} entries"
    )
    logger.info(
        f"Loaded source list with {len(lists.get('source', {}).entries if 'source' in lists else [])} entries"
    )

    # Verify lists are loaded
    # Check that player list has entries
    player_list = lists.get("player", None)
    if not player_list or not player_list.entries:
        logger.error("Player list not loaded or empty")
        return False

    # Check that chest type list has entries
    chest_type_list = lists.get("chest_type", None)
    if not chest_type_list or not chest_type_list.entries:
        logger.error("Chest type list not loaded or empty")
        return False

    # Check that source list has entries
    source_list = lists.get("source", None)
    if not source_list or not source_list.entries:
        logger.error("Source list not loaded or empty")
        return False

    logger.info("Validation list loading test PASSED")
    return True


def main():
    """Run all tests and report results."""
    success = test_validation_lists_loading()

    if success:
        logger.info("All tests PASSED")
        return 0
    else:
        logger.error("Some tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
