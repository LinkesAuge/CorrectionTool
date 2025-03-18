#!/usr/bin/env python
"""
test_validation_lists.py

Description: Tests the ValidationList's ability to load all validation list types
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
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def test_player_list_csv_import():
    """Test importing a player list from a CSV file."""
    file_path = Path("tests/sample_data/validation_samples/player_list.csv")
    if not file_path.exists():
        logger.error(f"Test file {file_path} does not exist!")
        return False

    logger.info(f"Testing player list import from: {file_path.absolute()}")

    try:
        validation_list = ValidationList.load_from_file(file_path)

        logger.info(
            f"Successfully loaded player list: {validation_list.name}, type: {validation_list.list_type}"
        )
        logger.info(f"Number of entries: {validation_list.count()}")

        sample_entries = list(validation_list.entries)[:5]
        logger.info(f"Sample player entries: {sample_entries}")

        assert validation_list.list_type == "player", (
            f"List type should be 'player', got '{validation_list.list_type}'"
        )
        assert validation_list.count() > 0, "Player list should have entries"

        logger.info("✅ Player list CSV import test PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Player list test failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def test_chest_type_list_csv_import():
    """Test importing a chest type list from a CSV file."""
    file_path = Path("tests/sample_data/validation_samples/chest_type_list.csv")
    if not file_path.exists():
        logger.error(f"Test file {file_path} does not exist!")
        return False

    logger.info(f"Testing chest type list import from: {file_path.absolute()}")

    try:
        validation_list = ValidationList.load_from_file(file_path)

        logger.info(
            f"Successfully loaded chest type list: {validation_list.name}, type: {validation_list.list_type}"
        )
        logger.info(f"Number of entries: {validation_list.count()}")

        sample_entries = list(validation_list.entries)[:5]
        logger.info(f"Sample chest type entries: {sample_entries}")

        assert validation_list.list_type == "chest_type", (
            f"List type should be 'chest_type', got '{validation_list.list_type}'"
        )
        assert validation_list.count() > 0, "Chest type list should have entries"

        logger.info("✅ Chest type list CSV import test PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Chest type list test failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def test_source_list_csv_import():
    """Test importing a source list from a CSV file."""
    file_path = Path("tests/sample_data/validation_samples/source_list.csv")
    if not file_path.exists():
        logger.error(f"Test file {file_path} does not exist!")
        return False

    logger.info(f"Testing source list import from: {file_path.absolute()}")

    try:
        validation_list = ValidationList.load_from_file(file_path)

        logger.info(
            f"Successfully loaded source list: {validation_list.name}, type: {validation_list.list_type}"
        )
        logger.info(f"Number of entries: {validation_list.count()}")

        sample_entries = list(validation_list.entries)[:5]
        logger.info(f"Sample source entries: {sample_entries}")

        assert validation_list.list_type == "source", (
            f"List type should be 'source', got '{validation_list.list_type}'"
        )
        assert validation_list.count() > 0, "Source list should have entries"

        logger.info("✅ Source list CSV import test PASSED")
        return True
    except Exception as e:
        logger.error(f"❌ Source list test failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def main():
    """Run all tests."""
    logger.info("Starting validation list import tests...")

    player_success = test_player_list_csv_import()
    chest_type_success = test_chest_type_list_csv_import()
    source_success = test_source_list_csv_import()

    overall_success = player_success and chest_type_success and source_success

    logger.info("All tests completed.")
    if overall_success:
        logger.info("✅ All validation list tests PASSED")
        sys.exit(0)
    else:
        logger.error("❌ Some validation list tests FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
