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
    assert player_list is not None, "Player list not loaded"
    assert player_list.entries, "Player list is empty"

    # Check that chest type list has entries
    chest_type_list = lists.get("chest_type", None)
    assert chest_type_list is not None, "Chest type list not loaded"
    assert chest_type_list.entries, "Chest type list is empty"

    # Check that source list has entries
    source_list = lists.get("source", None)
    assert source_list is not None, "Source list not loaded"
    assert source_list.entries, "Source list is empty"

    logger.info("Validation list loading test PASSED")


def main():
    """Run all tests and report results."""
    try:
        test_validation_lists_loading()
        logger.info("All tests PASSED")
        return 0
    except AssertionError as e:
        logger.error(f"Some tests FAILED: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
