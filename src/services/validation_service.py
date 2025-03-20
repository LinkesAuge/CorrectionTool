"""
validation_service.py

Description: Service for validating entries against validation lists
Usage:
    from src.services.validation_service import ValidationService
    from src.interfaces.i_validation_service import IValidationService
    service = service_factory.get_service(IValidationService)
    result = service.validate_entries()
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
import pandas as pd
from pathlib import Path

from src.interfaces.i_validation_service import IValidationService
from src.interfaces.i_data_store import IDataStore
from src.interfaces.events import EventType, EventHandler, EventData


class ValidationService(IValidationService):
    """
    Service for validating entries against validation lists.

    This class handles validation of entries against validation lists stored in the DataStore,
    providing a clean interface for validating entries and tracking validation errors.

    Attributes:
        _store: IDataStore instance
        _logger: Logger instance

    Implementation Notes:
        - Validates entries against validation lists in DataStore
        - Tracks validation errors for each entry
        - Uses efficient DataFrame operations for validation
    """

    def __init__(self, data_store: IDataStore):
        """
        Initialize the ValidationService with dependency injection.

        Args:
            data_store: Data store service
        """
        # Store injected dependencies
        self._store = data_store

        # Setup logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("ValidationService initialized")

    def validate_entries(self, specific_entries: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Validate all entries or specific entries against validation lists.

        Args:
            specific_entries: Optional list of entry IDs to validate (validates all if None)

        Returns:
            Dict[str, int]: Validation statistics (valid, invalid, total)
        """
        if not self._store:
            self._logger.warning("No data store available for validation")
            return {"valid": 0, "invalid": 0, "total": 0}

        # Get entries from store
        entries_df = self._store.get_entries()
        if entries_df.empty:
            self._logger.warning("No entries to validate")
            return {"valid": 0, "invalid": 0, "total": 0}

        # Get validation lists
        players = self._store.get_validation_list("player")
        chest_types = self._store.get_validation_list("chest_type")
        sources = self._store.get_validation_list("source")

        # Start a transaction
        self._store.begin_transaction()

        try:
            # Create a copy of the entries DataFrame
            new_entries_df = entries_df.copy()

            # Get sets of valid values from validation lists
            valid_players = set(players.index.tolist()) if not players.empty else set()
            valid_chest_types = set(chest_types.index.tolist()) if not chest_types.empty else set()
            valid_sources = set(sources.index.tolist()) if not sources.empty else set()

            self._logger.info(
                f"Validation sets: {len(valid_players)} players, {len(valid_chest_types)} chest types, {len(valid_sources)} sources"
            )

            # Initialize validation errors
            new_entries_df["validation_errors"] = [[] for _ in range(len(new_entries_df))]

            # Define validation function
            def validate_row(row):
                errors = []

                # Validate chest_type
                if (
                    "chest_type" in row
                    and row["chest_type"]
                    and valid_chest_types
                    and row["chest_type"] not in valid_chest_types
                ):
                    errors.append(f"Invalid chest type: '{row['chest_type']}'")

                # Validate player
                if (
                    "player" in row
                    and row["player"]
                    and valid_players
                    and row["player"] not in valid_players
                ):
                    errors.append(f"Invalid player name: '{row['player']}'")

                # Validate source
                if (
                    "source" in row
                    and row["source"]
                    and valid_sources
                    and row["source"] not in valid_sources
                ):
                    errors.append(f"Invalid source: '{row['source']}'")

                return errors

            # Apply validation
            new_entries_df["validation_errors"] = new_entries_df.apply(validate_row, axis=1)

            # Update status based on validation errors
            def update_status(row):
                if row["validation_errors"]:
                    return "Invalid"
                elif isinstance(row.get("original_values", None), dict) and row["original_values"]:
                    return "Corrected"
                else:
                    return "Pending"

            new_entries_df["status"] = new_entries_df.apply(update_status, axis=1)

            # Count validation results
            valid_entries = len(
                new_entries_df[new_entries_df["status"].isin(["Corrected", "Pending"])]
            )
            invalid_entries = len(new_entries_df[new_entries_df["status"] == "Invalid"])
            total_count = len(new_entries_df)

            # Update entries in store
            self._store.set_entries(new_entries_df, source="validation_service")

            # Commit the transaction
            self._store.commit_transaction()

            # Emit validation completed event - safely
            try:
                self._store._emit_event(
                    EventType.VALIDATION_COMPLETED,
                    {"valid": valid_entries, "invalid": invalid_entries, "total": total_count},
                )
            except KeyError:
                self._logger.warning(f"No handlers registered for {EventType.VALIDATION_COMPLETED}")

            self._logger.info(
                f"Validated {total_count} entries: {valid_entries} valid, {invalid_entries} invalid"
            )

            return {"valid": valid_entries, "invalid": invalid_entries, "total": total_count}

        except Exception as e:
            # Rollback the transaction on error
            self._store.rollback_transaction()
            self._logger.error(f"Error validating entries: {e}")

            # Emit error event - safely
            try:
                self._store._emit_event(
                    EventType.ERROR_OCCURRED, {"type": "validation", "error": str(e)}
                )
            except KeyError:
                self._logger.warning(f"No handlers registered for {EventType.ERROR_OCCURRED}")

            raise

    def get_invalid_entries(self) -> List[int]:
        """
        Get a list of invalid entry IDs.

        Returns:
            List[int]: List of entry IDs that failed validation
        """
        entries_df = self._store.get_entries()
        if entries_df.empty:
            return []

        # Find entries with status 'Invalid'
        invalid_mask = entries_df["status"] == "Invalid"
        invalid_entries = entries_df[invalid_mask]

        # Return the list of invalid entry IDs
        return invalid_entries.index.tolist()

    def get_validation_errors(self, entry_id: int) -> List[str]:
        """
        Get validation errors for a specific entry.

        Args:
            entry_id: ID of the entry to get errors for

        Returns:
            List[str]: List of validation error messages
        """
        entries_df = self._store.get_entries()

        if entry_id not in entries_df.index:
            self._logger.warning(f"Entry with ID {entry_id} not found")
            return []

        errors = entries_df.at[entry_id, "validation_errors"]
        if isinstance(errors, list):
            return errors
        return []

    def validate_entry(self, entry_id: int) -> bool:
        """
        Validate a specific entry against validation lists.

        Args:
            entry_id: ID of the entry to validate

        Returns:
            bool: True if entry is valid, False otherwise
        """
        result = self.validate_entries([entry_id])
        return result["invalid"] == 0

    def add_to_validation_list(self, list_type: str, value: str) -> bool:
        """
        Add a new value to a validation list.

        Args:
            list_type: Type of validation list ('chest_types', 'players', or 'sources')
            value: Value to add to the validation list

        Returns:
            bool: True if value was added, False otherwise
        """
        if list_type not in ["chest_types", "players", "sources"]:
            self._logger.error(f"Invalid validation list type: {list_type}")
            return False

        if not value:
            self._logger.error("Cannot add empty value to validation list")
            return False

        try:
            # Get the validation list
            validation_list = self._store.get_validation_list(list_type)

            # Check if value already exists
            if not validation_list.empty and value in validation_list["value"].values:
                self._logger.warning(
                    f"Value '{value}' already exists in '{list_type}' validation list"
                )
                return False

            # Add value to validation list
            self._store.add_validation_list_entry(list_type, value)

            self._logger.info(f"Added '{value}' to '{list_type}' validation list")

            # Re-validate entries
            self.validate_entries()

            return True

        except Exception as e:
            self._logger.error(f"Error adding value to validation list: {e}")

            # Emit error event
            self._store._emit_event(
                EventType.ERROR_OCCURRED, {"type": "validation_list_update", "error": str(e)}
            )

            return False

    def remove_from_validation_list(self, list_type: str, value: str) -> bool:
        """
        Remove a value from a validation list.

        Args:
            list_type: Type of validation list ('chest_types', 'players', or 'sources')
            value: Value to remove from the validation list

        Returns:
            bool: True if value was removed, False otherwise
        """
        if list_type not in ["chest_types", "players", "sources"]:
            self._logger.error(f"Invalid validation list type: {list_type}")
            return False

        if not value:
            self._logger.error("Cannot remove empty value from validation list")
            return False

        try:
            # Get the validation list
            validation_list = self._store.get_validation_list(list_type)

            # Check if value exists
            if validation_list.empty or value not in validation_list["value"].values:
                self._logger.warning(
                    f"Value '{value}' does not exist in '{list_type}' validation list"
                )
                return False

            # Get ID of the value
            value_id = validation_list[validation_list["value"] == value].index[0]

            # Remove value from validation list
            self._store.remove_validation_list_entry(list_type, value_id)

            self._logger.info(f"Removed '{value}' from '{list_type}' validation list")

            # Re-validate entries
            self.validate_entries()

            return True

        except Exception as e:
            self._logger.error(f"Error removing value from validation list: {e}")

            # Emit error event
            self._store._emit_event(
                EventType.ERROR_OCCURRED, {"type": "validation_list_update", "error": str(e)}
            )

            return False
