"""
correction_service.py

Description: Service for applying corrections to entries
Usage:
    from src.services.correction_service import CorrectionService
    from src.interfaces.i_correction_service import ICorrectionService
    service = service_factory.get_service(ICorrectionService)
    result = service.apply_corrections()
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import pandas as pd
from pathlib import Path

from src.interfaces.i_correction_service import ICorrectionService
from src.interfaces.i_data_store import IDataStore
from src.enums.event_type import EventType


class CorrectionService(ICorrectionService):
    """
    Service for applying corrections to entries.

    This class handles the application of correction rules to entries,
    providing a clean interface for applying rules and tracking changes.

    Attributes:
        _store: IDataStore instance
        _logger: Logger instance

    Implementation Notes:
        - Applies corrections directly to DataFrameStore
        - Tracks original values for change history
        - Supports batch correction application
    """

    def __init__(self, data_store: IDataStore):
        """
        Initialize the CorrectionService.

        Args:
            data_store: Data store service
        """
        # Store the data store
        self._store = data_store

        # Setup logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("CorrectionService initialized")

    def apply_corrections(self, specific_entries: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Apply all enabled correction rules to entries.

        Args:
            specific_entries: Optional list of entry IDs to correct (corrects all if None)

        Returns:
            Dict[str, int]: Correction statistics (applied, total)
        """
        # Get entries and rules from DataFrameStore
        entries_df = self._store.get_entries()
        rules_df = self._store.get_correction_rules()

        if entries_df.empty:
            self._logger.warning("No entries to correct")
            return {"applied": 0, "total": 0}

        if rules_df.empty:
            self._logger.warning("No correction rules to apply")
            return {"applied": 0, "total": 0}

        # Filter entries if specific_entries is provided
        if specific_entries:
            entries_df = entries_df.loc[entries_df.index.isin(specific_entries)]
            if entries_df.empty:
                self._logger.warning("No matching entries found for correction")
                return {"applied": 0, "total": 0}

        # Start a transaction
        self._store.begin_transaction()

        try:
            # Create a copy of the entries DataFrame
            new_entries_df = entries_df.copy()

            # Track number of corrections applied
            total_corrections = 0
            entries_affected = 0
            entries_affected_set = set()

            # Apply the rules one by one
            for rule_id, rule in rules_df.iterrows():
                field = rule["field"]

                # Get pattern/replacement from from_text/to_text columns
                pattern = rule.get("from_text") if "from_text" in rule else rule.get("pattern")
                replacement = rule.get("to_text") if "to_text" in rule else rule.get("replacement")

                # Skip empty rules
                if not pattern or replacement is None:
                    continue

                # Skip if field is not in DataFrame
                if field not in new_entries_df.columns:
                    continue

                # Create a mask for entries matching the rule
                mask = new_entries_df[field] == pattern
                matching_entries = new_entries_df[mask]

                # Skip if no matching entries
                if matching_entries.empty:
                    continue

                # Apply the correction to each matching entry
                for entry_id in matching_entries.index:
                    try:
                        # Store the original value
                        original_value = new_entries_df.at[entry_id, field]

                        # Create a new dict for original_values if it doesn't exist
                        if pd.isna(
                            new_entries_df.at[entry_id, "original_values"]
                        ) or not isinstance(new_entries_df.at[entry_id, "original_values"], dict):
                            new_entries_df.at[entry_id, "original_values"] = {}

                        # Get original values as dict (safely)
                        original_values = {}
                        if isinstance(new_entries_df.at[entry_id, "original_values"], dict):
                            original_values = new_entries_df.at[entry_id, "original_values"].copy()

                        # Only store the original value once (first correction)
                        if field not in original_values:
                            original_values[field] = original_value

                        # Apply the correction directly
                        new_entries_df.at[entry_id, field] = replacement

                        # Create a new row with updated values to avoid pandas indexing issues
                        new_row = new_entries_df.loc[entry_id].copy()
                        new_row["original_values"] = original_values
                        new_row["status"] = "Corrected"

                        # Update the row in the DataFrame
                        new_entries_df.loc[entry_id] = new_row

                        # Track affected entries
                        entries_affected_set.add(entry_id)
                        total_corrections += 1

                    except Exception as e:
                        self._logger.error(f"Error applying correction to entry {entry_id}: {e}")
                        continue

            # Update the entries in DataFrameStore if we made changes
            if total_corrections > 0:
                entries_affected = len(entries_affected_set)

                # Update entries in store
                self._store.set_entries(new_entries_df, source="correction_service")

                # Commit the transaction
                self._store.commit_transaction()

                # Emit correction applied event
                try:
                    self._store._emit_event(
                        EventType.CORRECTION_APPLIED,
                        {
                            "count": total_corrections,
                            "entries_affected": entries_affected,
                        },
                    )
                except KeyError:
                    self._logger.warning(
                        f"No handlers registered for {EventType.CORRECTION_APPLIED}"
                    )
                except Exception as emit_error:
                    self._logger.warning(f"Error emitting event: {emit_error}")

                self._logger.info(
                    f"Applied {total_corrections} corrections to {entries_affected} entries"
                )
            else:
                # Rollback the transaction since we didn't make any changes
                self._store.rollback_transaction()
                self._logger.info("No corrections applied")

            return {"applied": total_corrections, "total": len(new_entries_df)}

        except Exception as e:
            # Rollback the transaction on error
            self._store.rollback_transaction()
            self._logger.error(f"Error applying corrections: {e}")

            # Emit error event
            try:
                self._store._emit_event(
                    EventType.ERROR_OCCURRED, {"type": "correction", "error": str(e)}
                )
            except KeyError:
                self._logger.warning(f"No handlers registered for {EventType.ERROR_OCCURRED}")
            except Exception as emit_error:
                self._logger.warning(f"Error emitting event: {emit_error}")

            raise

    def apply_specific_correction(
        self, entry_id: int, field: str, from_text: str, to_text: str
    ) -> bool:
        """
        Apply a specific correction to a single entry.

        Args:
            entry_id: ID of the entry to correct
            field: Field to correct ('chest_type', 'player', 'source')
            from_text: Original text to replace
            to_text: New text to use

        Returns:
            bool: True if correction was applied, False otherwise
        """
        # Validate field
        if field not in ["chest_type", "player", "source"]:
            self._logger.error(f"Invalid field for correction: {field}")
            return False

        # Get entries from DataFrameStore
        entries_df = self._store.get_entries()

        # Check if entry exists
        if entry_id not in entries_df.index:
            self._logger.warning(f"Entry with ID {entry_id} not found")
            return False

        # Check if field value matches from_text
        if entries_df.at[entry_id, field] != from_text:
            self._logger.warning(f"Field {field} value doesn't match expected value")
            return False

        # Start a transaction
        self._store.begin_transaction()

        try:
            # Create a copy to avoid modifying the original
            new_entries_df = entries_df.copy()

            # Store original value if this is the first correction to this field
            if not isinstance(new_entries_df.at[entry_id, "original_values"], dict):
                new_entries_df.at[entry_id, "original_values"] = {}

            original_values = new_entries_df.at[entry_id, "original_values"]

            # Only store the original value once (first correction)
            if field not in original_values:
                original_values[field] = new_entries_df.at[entry_id, field]

            # Apply the correction
            new_entries_df.at[entry_id, field] = to_text
            new_entries_df.at[entry_id, "original_values"] = original_values
            new_entries_df.at[entry_id, "status"] = "Corrected"

            # Update entries in store
            self._store.set_entries(new_entries_df, source="correction_service")

            # Commit the transaction
            self._store.commit_transaction()

            # Emit correction applied event
            try:
                self._store._emit_event(
                    EventType.CORRECTION_APPLIED,
                    {"count": 1, "entries_affected": 1},
                )
            except KeyError:
                self._logger.warning(f"No handlers registered for {EventType.CORRECTION_APPLIED}")

            self._logger.info(
                f"Applied correction to entry {entry_id}: {field} '{from_text}' -> '{to_text}'"
            )
            return True

        except Exception as e:
            # Rollback the transaction on error
            self._store.rollback_transaction()
            self._logger.error(f"Error applying correction: {e}")

            # Emit error event
            try:
                self._store._emit_event(
                    EventType.ERROR_OCCURRED, {"type": "correction", "error": str(e)}
                )
            except KeyError:
                self._logger.warning(f"No handlers registered for {EventType.ERROR_OCCURRED}")
            except Exception as emit_error:
                self._logger.warning(f"Error emitting event: {emit_error}")

            return False

    def reset_corrections(self, entry_ids: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Reset corrections by restoring original values.

        Args:
            entry_ids: Optional list of entry IDs to reset (resets all if None)

        Returns:
            Dict[str, int]: Reset statistics (reset, total)
        """
        # Get entries from DataFrameStore
        entries_df = self._store.get_entries()

        if entries_df.empty:
            self._logger.warning("No entries to reset")
            return {"reset": 0, "total": 0}

        # Filter entries with original_values
        corrected_mask = entries_df["original_values"].apply(
            lambda x: isinstance(x, dict) and bool(x)
        )
        corrected_entries = entries_df[corrected_mask]

        if corrected_entries.empty:
            self._logger.info("No corrected entries to reset")
            return {"reset": 0, "total": len(entries_df)}

        # Filter for specific entry IDs if provided
        if entry_ids:
            corrected_entries = corrected_entries.loc[corrected_entries.index.isin(entry_ids)]
            if corrected_entries.empty:
                self._logger.warning("No matching corrected entries found")
                return {"reset": 0, "total": 0}

        # Start a transaction
        self._store.begin_transaction()

        try:
            # Create a copy for modifications
            new_entries_df = entries_df.copy()

            # Track the number of entries reset
            reset_count = 0

            # Reset corrections for each entry
            for entry_id, entry in corrected_entries.iterrows():
                original_values = entry["original_values"]
                if not original_values:
                    continue

                # Restore original values
                for field, original_value in original_values.items():
                    new_entries_df.at[entry_id, field] = original_value

                # Clear original values
                new_entries_df.at[entry_id, "original_values"] = {}

                # Set status to Invalid if there are validation errors
                if entry["validation_errors"]:
                    new_entries_df.at[entry_id, "status"] = "Invalid"
                else:
                    new_entries_df.at[entry_id, "status"] = "Pending"

                reset_count += 1

            # Update entries in DataFrameStore if we made changes
            if reset_count > 0:
                # Update entries in store
                self._store.set_entries(new_entries_df, source="correction_service")

                # Commit the transaction
                self._store.commit_transaction()

                # Emit corrections reset event
                self._store._emit_event(EventType.CORRECTIONS_RESET, {"count": reset_count})

                self._logger.info(f"Reset corrections for {reset_count} entries")
            else:
                # Rollback the transaction since we didn't make any changes
                self._store.rollback_transaction()
                self._logger.info("No corrections reset")

            return {"reset": reset_count, "total": len(entries_df)}

        except Exception as e:
            # Rollback the transaction on error
            self._store.rollback_transaction()
            self._logger.error(f"Error resetting corrections: {e}")

            # Emit error event
            self._store._emit_event(
                EventType.ERROR_OCCURRED, {"type": "correction_reset", "error": str(e)}
            )

            raise

    def add_correction_rule(
        self,
        field: str,
        incorrect_value: str,
        correct_value: str,
        case_sensitive: bool = True,
        match_type: str = "exact",
        enabled: bool = True,
    ) -> bool:
        """
        Add a new correction rule.

        Args:
            field: Field to apply the correction to ('chest_type', 'player', 'source')
            incorrect_value: The value to be corrected
            correct_value: The corrected value to use
            case_sensitive: Whether the match should be case sensitive
            match_type: Type of match ('exact', 'contains', 'startswith', 'endswith', 'regex')
            enabled: Whether the rule should be active

        Returns:
            bool: True if rule was added successfully, False otherwise
        """
        # Validate field
        if field not in ["chest_type", "player", "source"]:
            self._logger.error(f"Invalid field for correction rule: {field}")
            return False

        # Validate match_type
        valid_match_types = ["exact", "contains", "startswith", "endswith", "regex"]
        if match_type not in valid_match_types:
            self._logger.error(
                f"Invalid match type: {match_type}. Valid types: {valid_match_types}"
            )
            return False

        # Get current rules
        rules_df = self._store.get_correction_rules()

        # Create a new rule to add
        new_rule = pd.DataFrame(
            {
                "field": [field],
                "pattern": [incorrect_value],
                "replacement": [correct_value],
                "case_sensitive": [case_sensitive],
                "match_type": [match_type],
                "enabled": [enabled],
            }
        )

        # Combine existing rules with new rule
        if rules_df.empty:
            combined_rules = new_rule
        else:
            combined_rules = pd.concat([rules_df, new_rule], ignore_index=True)

        # Update the rules in the store
        self._store.set_correction_rules(combined_rules, source="correction_service")

        # Emit an event for the rule update
        try:
            self._store._emit_event(
                EventType.CORRECTION_RULES_UPDATED, {"count": len(combined_rules)}
            )
        except KeyError:
            self._logger.warning(f"No handlers registered for {EventType.CORRECTION_RULES_UPDATED}")

        self._logger.info(
            f"Added correction rule: {field} '{incorrect_value}' -> '{correct_value}' "
            f"(match: {match_type}, case sensitive: {case_sensitive}, enabled: {enabled})"
        )
        return True
