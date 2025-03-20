#!/usr/bin/env python3
"""
test_validation_service.py

Description: Tests the ValidationService implementation with the new interface-based architecture
Usage:
    python test_validation_service.py
"""

import logging
import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List

from src.app_bootstrapper import AppBootstrapper
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_validation_service import IValidationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    try:
        logger.info("Starting ValidationService test with interface-based architecture")

        # Initialize the app bootstrapper to get service implementations
        bootstrapper = AppBootstrapper()
        bootstrapper.initialize()

        logger.info("Getting service implementations...")
        data_store = bootstrapper.service_factory.get_service(IDataStore)
        file_service = bootstrapper.service_factory.get_service(IFileService)
        validation_service = bootstrapper.service_factory.get_service(IValidationService)

        # Create test validation lists
        logger.info("Creating test validation lists...")

        # Players
        players = [
            "TestPlayer",
            "TestPlayer2",
            "TestPlayer3",
            "Gondolin",
            "Sir Met",
            "Engelchen",
            "TacoBell",
        ]
        logger.info(f"Adding {len(players)} players to validation list")
        for player in players:
            data_store.add_validation_entry("player", player)

        # Chest types
        chests = [
            "Common Wood Chest",
            "Rare Wood Chest",
            "Elegant Chest",
            "Golden Chest",
            "Forgotten Chest",
        ]
        logger.info(f"Adding {len(chests)} chest types to validation list")
        for chest in chests:
            data_store.add_validation_entry("chest_type", chest)

        # Sources
        sources = ["Level 5 Cave", "Mercenary Exchange", "Dragon Chest", "Daily Mission"]
        logger.info(f"Adding {len(sources)} sources to validation list")
        for source in sources:
            data_store.add_validation_entry("source", source)

        logger.info(
            f"Created validation lists: players={len(players)}, chests={len(chests)}, sources={len(sources)}\n"
        )

        # Load sample data
        logger.info("Loading entries from sample_data.txt...")
        sample_file = Path("sample_data.txt")
        if not sample_file.exists():
            logger.error(f"Sample data file not found: {sample_file}")
            return 1

        loaded = file_service.load_entries(sample_file)
        if loaded:
            logger.info(f"Loaded entries from {sample_file}")
        else:
            logger.error(f"Failed to load entries from {sample_file}")
            return 1

        entries = data_store.get_entries()
        logger.info(f"DataStore has {len(entries)} entries")

        # Run validation
        logger.info("Running validation...")
        result = validation_service.validate_entries()

        if result:
            logger.info(
                f"Validation results: {result['valid']} valid, {result['invalid']} invalid, {result['total']} total"
            )

            # Check for validation count mismatch
            expected_total = len(entries)
            actual_total = result["valid"] + result["invalid"]
            if expected_total != actual_total or expected_total != result["total"]:
                logger.warning(
                    f"Validation count mismatch: expected {expected_total}, got {actual_total} ({result['valid']} valid + {result['invalid']} invalid)"
                )

            # Get invalid entries
            invalid_entries = validation_service.get_invalid_entries()
            logger.info("Validation successful!")

            # Show some examples of invalid entries
            if invalid_entries:
                logger.info(f"Sample of invalid entries ({len(invalid_entries)} total):")
                for i, entry_id in enumerate(invalid_entries[:5]):  # Show up to 5 examples
                    entry = entries.loc[entry_id]
                    errors = validation_service.get_validation_errors(entry_id)
                    logger.info(f"Entry #{entry_id}: {entry['chest_type']} - Errors: {errors}")
            else:
                logger.info("No invalid entries found.")
        else:
            logger.error("Validation failed!")
            return 1

        logger.info("ValidationService test completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
