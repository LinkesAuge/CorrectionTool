import logging
import pandas as pd
import sys
import traceback
from pathlib import Path
from typing import Dict, List

from src.app_bootstrapper import AppBootstrapper
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_correction_service import ICorrectionService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level to see more detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Enable logging for other modules
logging.getLogger("src").setLevel(logging.DEBUG)


def main():
    try:
        logger.info("Starting CorrectionService test with interface-based architecture")

        # Initialize the app bootstrapper to get service implementations
        bootstrapper = AppBootstrapper()
        bootstrapper.initialize()

        logger.info("Getting service implementations...")
        data_store = bootstrapper.service_factory.get_service(IDataStore)
        file_service = bootstrapper.service_factory.get_service(IFileService)
        correction_service = bootstrapper.service_factory.get_service(ICorrectionService)

        # Create test correction rules
        logger.info("Creating test correction rules...")

        # Define rules - matching the columns expected by DataFrameStore
        rules_data = [
            {
                "field": "chest_type",
                "from_text": "Rare Dragon Chest",
                "to_text": "Rare Wood Chest",
                "case_sensitive": True,
                "match_type": "exact",
                "enabled": True,
            },
            {
                "field": "player",
                "from_text": "Moony",
                "to_text": "TacoBell",
                "case_sensitive": True,
                "match_type": "exact",
                "enabled": True,
            },
            {
                "field": "source",
                "from_text": "epic Crypt",
                "to_text": "Dragon Chest",
                "case_sensitive": False,
                "match_type": "contains",
                "enabled": True,
            },
        ]

        # Create a DataFrame from the rules and set it in the store
        try:
            logger.debug("Creating rules DataFrame")
            rules_df = pd.DataFrame(rules_data)
            logger.debug(f"Rules DataFrame: \n{rules_df}")

            logger.debug("Setting correction rules in data store")
            data_store.set_correction_rules(rules_df)
            logger.info(f"Added {len(rules_df)} correction rules to the data store")
        except Exception as e:
            logger.error(f"Error setting correction rules: {e}")
            traceback.print_exc()
            return 1

        # Load sample data
        logger.info("Loading entries from sample_data.txt...")
        sample_file = Path("sample_data.txt")
        if not sample_file.exists():
            logger.error(f"Sample data file not found: {sample_file}")
            return 1

        try:
            loaded = file_service.load_entries(sample_file)
            if loaded:
                logger.info(f"Loaded entries from {sample_file}")
            else:
                logger.error(f"Failed to load entries from {sample_file}")
                return 1
        except Exception as e:
            logger.error(f"Error loading entries: {e}")
            traceback.print_exc()
            return 1

        try:
            entries = data_store.get_entries()
            logger.info(f"DataStore has {len(entries)} entries")

            # Display some entries
            if not entries.empty:
                logger.debug("Sample of loaded entries:")
                logger.debug(f"{entries.head(2)}")
        except Exception as e:
            logger.error(f"Error getting entries: {e}")
            traceback.print_exc()
            return 1

        # Verify the correction rules were set
        try:
            correction_rules = data_store.get_correction_rules()
            logger.info(f"DataStore has {len(correction_rules)} correction rules")

            # Display the rules
            if not correction_rules.empty:
                logger.debug("Correction rules in data store:")
                logger.debug(f"{correction_rules}")
        except Exception as e:
            logger.error(f"Error getting correction rules: {e}")
            traceback.print_exc()
            return 1

        # Run correction
        logger.info("Running correction...")
        try:
            # Start a transaction if needed
            if hasattr(data_store, "begin_transaction"):
                data_store.begin_transaction()

            # Apply corrections
            result = correction_service.apply_corrections()

            # Commit transaction if needed
            if hasattr(data_store, "commit_transaction"):
                data_store.commit_transaction()

            if result:
                logger.info(f"Correction results: {result}")

                # Check for correction count discrepancies
                expected_total = len(entries)
                if "total" in result and expected_total != result["total"]:
                    logger.warning(
                        f"Correction count mismatch: expected {expected_total}, got {result['total']}"
                    )

                # Get corrected entries
                try:
                    current_entries = data_store.get_entries()
                    corrected_entries = current_entries[current_entries["status"] == "Corrected"]

                    # Show some examples of corrected entries
                    if not corrected_entries.empty:
                        logger.info(
                            f"Sample of corrected entries ({len(corrected_entries)} total):"
                        )
                        for i, (idx, entry) in enumerate(corrected_entries.head(5).iterrows()):
                            original = entry.get("original_values", {})
                            changes = []

                            for field, old_value in original.items():
                                new_value = entry[field]
                                changes.append(f"{field}: '{old_value}' -> '{new_value}'")

                            logger.info(
                                f"Entry #{idx}: {entry['chest_type']} - Changes: {', '.join(changes)}"
                            )
                    else:
                        logger.info("No corrected entries found.")
                except Exception as e:
                    logger.error(f"Error processing corrected entries: {e}")
                    traceback.print_exc()
            else:
                logger.error("Correction failed - result is None or empty!")
                return 1
        except Exception as e:
            # Rollback transaction if needed
            if hasattr(data_store, "rollback_transaction"):
                data_store.rollback_transaction()

            logger.error(f"Error applying corrections: {e}")
            traceback.print_exc()
            return 1

        logger.info("CorrectionService test completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
