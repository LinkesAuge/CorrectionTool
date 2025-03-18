#!/usr/bin/env python
"""
Test Player Text Import

Description: Tests the ability to import player lists from plain text files
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

# Configure logging
handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[handler],
)
logger = logging.getLogger(__name__)
# Force immediate output
handler.flush()


def test_player_text_import():
    """Test importing a player list from a text file."""
    try:
        logger.info("===== Starting player text import test =====")
        handler.flush()

        # Import the ValidationList class
        from src.models.validation_list import ValidationList

        # Use the real players.txt file
        player_file = Path("data/validation/players.txt")

        if not player_file.exists():
            logger.error(f"Player file {player_file} does not exist!")
            handler.flush()
            return False

        logger.info(f"Attempting to load players from {player_file}")
        handler.flush()

        # Test loading with default parameters (should detect it's a player list)
        player_list = ValidationList.load_from_file(str(player_file))

        logger.info(f"Loaded player list with {len(player_list.entries)} entries")
        logger.info(f"List type: {player_list.list_type}")
        logger.info(f"List name: {player_list.name}")
        handler.flush()

        # Show a sample of the entries
        sample_entries = list(player_list.entries)[:3]
        logger.info(f"First few entries: {sample_entries}")
        handler.flush()

        # Verify the list
        if player_list.list_type != "player":
            logger.error(f"Expected list_type 'player', got '{player_list.list_type}'")
            handler.flush()
            return False

        if len(player_list.entries) <= 0:
            logger.error("Player list should have entries")
            handler.flush()
            return False

        logger.info("Player text import test PASSED")
        handler.flush()
        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        logger.error(traceback.format_exc())
        handler.flush()
        return False


def main():
    """Run the tests and report results."""
    success = test_player_text_import()

    if success:
        logger.info("===== All tests PASSED =====")
        handler.flush()
        return 0
    else:
        logger.error("===== Tests FAILED =====")
        handler.flush()
        return 1


if __name__ == "__main__":
    exit_code = main()
    logger.info(f"Exiting with code: {exit_code}")
    handler.flush()
    sys.exit(exit_code)
