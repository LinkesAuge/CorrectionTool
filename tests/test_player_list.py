#!/usr/bin/env python
"""
test_player_list.py

Description: Tests the ValidationList's ability to load player_list.csv
"""

import sys
import os
import logging
import traceback
from pathlib import Path

# Add the parent directory to the Python path so we can import the src module
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.models.validation_list import ValidationList

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def test_player_list_csv_import():
    """Test importing a player list from a CSV file with the problematic format."""
    # Check if players.txt exists
    file_path = Path("tests/sample_data/validation_samples/players.txt")
    assert file_path.exists(), f"Test file {file_path} does not exist!"

    logger.info(f"Testing import from: {file_path.absolute()}")

    try:
        # Try to load the validation list
        validation_list = ValidationList.load_from_file(file_path)

        # Log the loaded list
        logger.info(
            f"Successfully loaded validation list: {validation_list.name}, type: {validation_list.list_type}"
        )
        logger.info(f"Number of entries: {validation_list.count()}")

        # Print the first few lines of the file for debugging
        logger.debug("First few lines of the file:")
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < 10:  # Print first 10 lines
                    logger.debug(f"Line {i + 1}: {line.strip()}")
                else:
                    break

        # Check a few entries to make sure they're loaded correctly
        sample_entries = list(validation_list.entries)[:5]
        logger.info(f"Sample entries: {sample_entries}")

        # Verify that the list was loaded correctly
        assert validation_list.list_type == "player", (
            f"List type should be 'player', got '{validation_list.list_type}'"
        )
        assert validation_list.count() > 0, "List should have entries"

        logger.info("✅ Player list CSV import test PASSED")
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        logger.error(traceback.format_exc())
        assert False, f"Test failed: {str(e)}"


def main():
    """Run all tests."""
    logger.info("Starting validation list import tests...")

    try:
        test_player_list_csv_import()
        logger.info("All tests completed.")
        logger.info("✅ All tests PASSED")
        sys.exit(0)
    except AssertionError as e:
        logger.error("❌ Some tests FAILED")
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
