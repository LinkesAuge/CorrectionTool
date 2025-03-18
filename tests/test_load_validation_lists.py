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
        player_entries = player_list.entries if player_list else []
        logger.info(f"Loaded player list with {len(player_entries)} items")

        # Check for chest type list
        chest_type_list = lists.get("chest_type", None)
        chest_type_entries = chest_type_list.entries if chest_type_list else []
        logger.info(f"Loaded chest type list with {len(chest_type_entries)} items")

        # Check for source list
        source_list = lists.get("source", None)
        source_entries = source_list.entries if source_list else []
        logger.info(f"Loaded source list with {len(source_entries)} items")

        # Verify lists are loaded and have entries
        lists_loaded = 0
        expected_lists = 3

        if player_entries and len(player_entries) > 0:
            lists_loaded += 1
        else:
            logger.error("Player list not loaded or empty")

        if chest_type_entries and len(chest_type_entries) > 0:
            lists_loaded += 1
        else:
            logger.error("Chest type list not loaded or empty")

        if source_entries and len(source_entries) > 0:
            lists_loaded += 1
        else:
            logger.error("Source list not loaded or empty")

        logger.info(f"Successfully loaded {lists_loaded} out of {expected_lists} validation lists")

        return lists_loaded == expected_lists
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False


def main():
    """Run all tests."""
    logger.info("Starting validation list loading test...")

    # Test loading default validation lists
    if test_data_manager_load_default_lists():
        logger.info("✅ All validation lists loaded successfully")
    else:
        logger.error("❌ Failed to load all validation lists")
        return 1

    logger.info("Test completed.")
    logger.info("✅ Validation list loading test PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
