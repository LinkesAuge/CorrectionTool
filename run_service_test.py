#!/usr/bin/env python3
"""
run_service_test.py

Description: Tests just the service layer with the new interface-based architecture
Usage:
    python run_service_test.py
"""

import sys
import logging
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    """
    Main function to test the service layer with the new interface architecture.
    """
    logger.info("Starting service layer test with interface-based architecture")

    # Import after logging setup to capture initialization logs
    from src.app_bootstrapper import AppBootstrapper
    from src.interfaces import (
        IDataStore,
        IFileService,
        ICorrectionService,
        IValidationService,
    )

    # Initialize bootstrapper
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()

    # Get services using the interface types
    logger.info("Getting service implementations...")
    data_store = bootstrapper.get_service(IDataStore)
    file_service = bootstrapper.get_service(IFileService)

    # Test basic file operations
    try:
        # Load entries from sample_data.txt
        sample_path = Path("sample_data.txt")
        if sample_path.exists():
            logger.info(f"Loading entries from {sample_path}...")
            file_service.load_entries_from_file(sample_path)
            logger.info("Entries loaded successfully")

            # Check if entries were loaded into the data store
            entries_df = data_store._entries_df
            logger.info(f"DataStore now has {len(entries_df)} entries")

            # Print some details about the loaded entries
            if not entries_df.empty:
                logger.info(f"Entry columns: {entries_df.columns.tolist()}")

            # Save entries to output file
            output_path = Path("data/output/test_interface_output.txt")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving entries to {output_path}...")
            file_service.save_entries_to_file(output_path)
            logger.info(f"Entries saved successfully to {output_path}")
        else:
            logger.warning(f"Sample data file not found at {sample_path}")
    except Exception as e:
        logger.error(f"Error in file operations: {str(e)}", exc_info=True)

    # Test loading correction rules
    try:
        # Load correction rules
        rules_path = Path("sample_rules.csv")
        if rules_path.exists():
            logger.info(f"Loading correction rules from {rules_path}...")
            count = file_service.load_correction_rules_from_csv(rules_path)
            logger.info(f"Loaded {count} correction rules successfully")

            # Check if rules were loaded into the data store
            rules_df = data_store._correction_rules_df
            logger.info(f"DataStore now has {len(rules_df)} correction rules")

            # Print some details about the loaded rules
            if not rules_df.empty:
                logger.info(f"Rule columns: {rules_df.columns.tolist()}")
        else:
            logger.warning(f"Sample rules file not found at {rules_path}")
    except Exception as e:
        logger.error(f"Error loading correction rules: {str(e)}", exc_info=True)

    logger.info("Service layer basic test completed!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)
