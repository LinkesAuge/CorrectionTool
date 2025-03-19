#!/usr/bin/env python3
"""
test_simple_validation.py

A simplified test script to debug pandas DataFrame issues when setting list values
"""

import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Main test function"""
    # Create a simple DataFrame simulating entries
    entries_df = pd.DataFrame(
        {
            "chest_type": ["Ancient Chest", "Dragon Chest", "Unknown Chest"],
            "player": ["TestPlayer", "TestPlayer2", "Unknown Player"],
            "source": ["Level 10 Crypt", "Level 20 Crypt", "Unknown Source"],
            "status": ["Pending", "Pending", "Pending"],
            "validation_errors": [[], [], []],
        }
    )

    # Set index
    entries_df.index = [1, 2, 3]

    logger.info(f"Created DataFrame with {len(entries_df)} rows")
    logger.info(f"DataFrame columns: {entries_df.columns.tolist()}")
    logger.info(f"Initial validation_errors: {entries_df['validation_errors'].tolist()}")

    # Create validation lists
    valid_chest_types = ["Ancient Chest", "Dragon Chest", "Wooden Chest"]
    valid_players = ["TestPlayer", "TestPlayer2", "TestPlayer3"]
    valid_sources = ["Level 10 Crypt", "Level 20 Crypt", "Level 5 Cave"]

    logger.info("Starting validation")
    logger.info(f"Valid chest types: {valid_chest_types}")
    logger.info(f"Valid players: {valid_players}")
    logger.info(f"Valid sources: {valid_sources}")

    # Create a copy of the DataFrame
    new_df = entries_df.copy()

    # Reset validation errors
    new_df["validation_errors"] = [[] for _ in range(len(new_df))]

    # Try different approaches
    try:
        logger.info("Approach 1: Using DataFrame.at")

        # Validate chest_type
        for idx, row in new_df.iterrows():
            chest_type = row["chest_type"]
            if chest_type not in valid_chest_types:
                errors = list(row["validation_errors"])
                errors.append(f"Invalid chest type: '{chest_type}'")
                logger.info(f"Setting validation_errors for row {idx} to {errors}")
                new_df.at[idx, "validation_errors"] = errors

        logger.info("Approach 1 successful")
        logger.info(f"Updated validation_errors: {new_df['validation_errors'].tolist()}")
    except Exception as e:
        logger.error(f"Approach 1 failed: {str(e)}")

    try:
        logger.info("Approach 2: Using apply and lambda")

        def validate_chest_type(row):
            if row["chest_type"] not in valid_chest_types:
                errors = list(row["validation_errors"])
                errors.append(f"Invalid chest type: '{row['chest_type']}'")
                return errors
            return row["validation_errors"]

        new_df["validation_errors"] = new_df.apply(validate_chest_type, axis=1)

        logger.info("Approach 2 successful")
        logger.info(f"Updated validation_errors: {new_df['validation_errors'].tolist()}")
    except Exception as e:
        logger.error(f"Approach 2 failed: {str(e)}")

    try:
        logger.info("Approach 3: Using loc with boolean indexing")

        # Create a mask for invalid chest types
        invalid_mask = ~new_df["chest_type"].isin(valid_chest_types)

        # For rows with invalid chest types, add error message
        for idx in new_df[invalid_mask].index:
            chest_type = new_df.at[idx, "chest_type"]
            errors = list(new_df.at[idx, "validation_errors"])
            errors.append(f"Invalid chest type: '{chest_type}'")
            new_df.at[idx, "validation_errors"] = errors

        logger.info("Approach 3 successful")
        logger.info(f"Updated validation_errors: {new_df['validation_errors'].tolist()}")
    except Exception as e:
        logger.error(f"Approach 3 failed: {str(e)}")

    # Update status based on validation errors
    try:
        logger.info("Updating status based on validation errors")

        for idx, row in new_df.iterrows():
            if row["validation_errors"]:
                new_df.at[idx, "status"] = "Invalid"
            else:
                new_df.at[idx, "status"] = "Valid"

        logger.info(f"Updated status: {new_df['status'].tolist()}")
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")

    logger.info("Test completed")
    return 0


if __name__ == "__main__":
    main()
