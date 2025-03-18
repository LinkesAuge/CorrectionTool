#!/usr/bin/env python
"""
Test script for validation list import functionality.

This script tests the ability to load both CSV and plain text files into ValidationList objects.
"""

import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Add the parent directory to the Python path so we can import the src module
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the ValidationList class
from src.models.validation_list import ValidationList


def test_text_file_import():
    """Test importing a plain text file with player names."""
    logger = logging.getLogger(__name__)
    logger.info("Testing text file import")

    # Create a test file path
    test_file = Path("data/validation/players.txt")

    if not test_file.exists():
        logger.error(f"Test file {test_file} does not exist!")
        return False

    try:
        # Try to load the validation list from the text file
        validation_list = ValidationList.load_from_file(str(test_file))

        # Check if the validation list was loaded correctly
        logger.info(f"Loaded validation list: {validation_list.name} ({validation_list.list_type})")
        logger.info(f"Entries: {validation_list.get_entries()}")

        # Validate the loaded list
        if validation_list.list_type != "player":
            logger.error(f"Expected list_type 'player', got '{validation_list.list_type}'")
            return False

        if validation_list.name != "Players":
            logger.error(f"Expected name 'Players', got '{validation_list.name}'")
            return False

        # Check if entries were loaded
        if validation_list.count() <= 0:
            logger.error(f"Expected entries, got {validation_list.count()}")
            return False

        logger.info(f"Loaded {validation_list.count()} player entries successfully")
        logger.info("Text file import test passed")
        return True

    except Exception as e:
        logger.error(f"Error importing text file: {e}")
        return False


def main():
    """Run the tests."""
    logger = logging.getLogger(__name__)
    logger.info("Starting validation list import tests")

    # Test text file import
    if test_text_file_import():
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
