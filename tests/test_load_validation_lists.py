#!/usr/bin/env python
"""
test_load_validation_lists.py

Description: Tests the DataManager's ability to load validation lists by default
"""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the Python path so we can import the src module
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.services.data_manager import DataManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def test_data_manager_load_default_lists():
    """Test DataManager loading default validation lists."""
    try:
        logger.info("Testing DataManager validation list loading")

        # Initialize the data manager
        data_manager = DataManager()

        # Load the default validation lists
        logger.info("Loading default validation lists from sample data")
        lists = data_manager.load_default_validation_lists()

        # Check for player list
        player_list = lists.get("player", None)
        assert player_list is not None, "Player list not loaded"
        assert player_list.entries, "Player list is empty"
        logger.info(f"Loaded player list with {len(player_list.entries)} items")

        # Check for chest type list
        chest_type_list = lists.get("chest_type", None)
        assert chest_type_list is not None, "Chest type list not loaded"
        assert chest_type_list.entries, "Chest type list is empty"
        logger.info(f"Loaded chest type list with {len(chest_type_list.entries)} items")

        # Check for source list
        source_list = lists.get("source", None)
        assert source_list is not None, "Source list not loaded"
        assert source_list.entries, "Source list is empty"
        logger.info(f"Loaded source list with {len(source_list.entries)} items")

        # Count loaded lists
        lists_loaded = len(lists)
        expected_lists = 3
        logger.info(f"Successfully loaded {lists_loaded} out of {expected_lists} validation lists")
        assert lists_loaded == expected_lists, (
            f"Expected {expected_lists} lists, got {lists_loaded}"
        )

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        assert False, f"Error during test: {str(e)}"


def main():
    """Run all tests."""
    logger.info("Starting validation list loading test...")

    # Test loading default validation lists
    try:
        test_data_manager_load_default_lists()
        logger.info("✅ All validation lists loaded successfully")
    except AssertionError as e:
        logger.error(f"❌ Failed to load all validation lists: {str(e)}")
        return 1

    logger.info("Test completed.")
    logger.info("✅ Validation list loading test PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
