"""
demo_data_management.py

Description: Standalone demonstration script for the new data management system
Usage:
    python demo_data_management.py
"""

import logging
import pandas as pd
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable, TypeVar, Generic, Union
import functools
import threading
import uuid
from enum import Enum, auto
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for the DataFrameStore event system."""

    ENTRIES_UPDATED = auto()
    CORRECTION_RULES_UPDATED = auto()
    VALIDATION_LIST_UPDATED = auto()
    IMPORT_COMPLETED = auto()
    EXPORT_COMPLETED = auto()
    CORRECTION_APPLIED = auto()
    VALIDATION_COMPLETED = auto()
    ERROR_OCCURRED = auto()


class DataFrameStore:
    """
    Singleton class for centralized data management using pandas DataFrames.

    This class serves as the single source of truth for all application data,
    implementing a clean, consistent API for data access and manipulation.
    """

    # Singleton instance
    _instance = None
    _instance_lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        """Get the singleton instance with thread-safety."""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = DataFrameStore()
        return cls._instance

    def __init__(self):
        """Initialize the DataFrameStore."""
        # Setup logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("Initializing DataFrameStore")

        # Initialize DataFrames
        self._entries_df = pd.DataFrame()
        self._correction_rules_df = pd.DataFrame()
        self._validation_lists = {
            "players": pd.DataFrame(),
            "chest_types": pd.DataFrame(),
            "sources": pd.DataFrame(),
        }

        # Event system
        self._event_handlers = {event_type: set() for event_type in EventType}

        # Transaction support
        self._transaction_active = False
        self._transaction_changes = {}

        # Cache for expensive operations
        self._cache = {}

        self._logger.info("DataFrameStore initialized")

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event type."""
        self._event_handlers[event_type].add(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe from an event type."""
        if handler in self._event_handlers[event_type]:
            self._event_handlers[event_type].remove(handler)

    def _emit_event(self, event_type: EventType, data: Any = None):
        """Emit an event to all subscribers."""
        for handler in self._event_handlers[event_type]:
            try:
                handler(data)
            except Exception as e:
                self._logger.error(f"Error in event handler for {event_type}: {e}")

    def begin_transaction(self):
        """Begin a transaction."""
        if self._transaction_active:
            self._logger.warning("Transaction already in progress")
            return False

        self._transaction_active = True
        self._transaction_changes = {
            "entries_df": self._entries_df.copy() if not self._entries_df.empty else None,
            "correction_rules_df": self._correction_rules_df.copy()
            if not self._correction_rules_df.empty
            else None,
            "validation_lists": {
                k: df.copy() if not df.empty else None for k, df in self._validation_lists.items()
            },
        }
        self._logger.debug("Transaction started")
        return True

    def commit_transaction(self):
        """Commit the current transaction."""
        if not self._transaction_active:
            self._logger.warning("No transaction in progress")
            return False

        # Clear transaction state
        self._transaction_active = False
        self._transaction_changes = {}

        # Clear cache since data has changed
        self._cache.clear()

        self._logger.debug("Transaction committed")
        return True

    def rollback_transaction(self):
        """Rollback the current transaction."""
        if not self._transaction_active:
            self._logger.warning("No transaction in progress")
            return False

        # Restore DataFrames from transaction changes
        if self._transaction_changes.get("entries_df") is not None:
            self._entries_df = self._transaction_changes["entries_df"]

        if self._transaction_changes.get("correction_rules_df") is not None:
            self._correction_rules_df = self._transaction_changes["correction_rules_df"]

        for list_type, df in self._transaction_changes.get("validation_lists", {}).items():
            if df is not None:
                self._validation_lists[list_type] = df

        # Clear transaction state
        self._transaction_active = False
        self._transaction_changes = {}

        self._logger.debug("Transaction rolled back")
        return True

    def get_entries(self) -> pd.DataFrame:
        """Get the entries DataFrame."""
        if self._entries_df.empty:
            return pd.DataFrame(
                {
                    "chest_type": pd.Series(dtype="str"),
                    "player": pd.Series(dtype="str"),
                    "source": pd.Series(dtype="str"),
                    "status": pd.Series(dtype="str"),
                    "validation_errors": pd.Series(dtype="object"),
                    "original_values": pd.Series(dtype="object"),
                    "date": pd.Series(dtype="str"),
                }
            )
        return self._entries_df.copy()

    def set_entries(self, df: pd.DataFrame, source: str = None) -> None:
        """Set the entries DataFrame."""
        if df is None:
            self._logger.error("Cannot set entries to None")
            return

        # Store a copy to ensure immutability
        self._entries_df = df.copy()

        # Clear cache
        self._cache.clear()

        # Emit event
        self._emit_event(EventType.ENTRIES_UPDATED, {"source": source, "count": len(df)})

        self._logger.info(f"Entries DataFrame updated with {len(df)} rows")

    def get_correction_rules(self) -> pd.DataFrame:
        """Get the correction rules DataFrame."""
        if self._correction_rules_df.empty:
            return pd.DataFrame(
                {
                    "from_text": pd.Series(dtype="str"),
                    "to_text": pd.Series(dtype="str"),
                    "category": pd.Series(dtype="str"),
                    "enabled": pd.Series(dtype="bool"),
                }
            )
        return self._correction_rules_df.copy()

    def set_correction_rules(self, df: pd.DataFrame) -> None:
        """Set the correction rules DataFrame."""
        if df is None:
            self._logger.error("Cannot set correction rules to None")
            return

        # Store a copy to ensure immutability
        self._correction_rules_df = df.copy()

        # Clear cache
        self._cache.clear()

        # Emit event
        self._emit_event(EventType.CORRECTION_RULES_UPDATED, self._correction_rules_df)

        self._logger.info(f"Correction rules DataFrame updated with {len(df)} rows")

    def add_correction_rule(self, rule_data: Dict[str, Any]) -> int:
        """Add a new correction rule."""
        # Validate required fields
        if "from_text" not in rule_data or "to_text" not in rule_data:
            self._logger.error("Missing required fields in correction rule data")
            return -1

        # Create DataFrame for the new rule
        rule_df = pd.DataFrame(
            {
                "from_text": [rule_data.get("from_text")],
                "to_text": [rule_data.get("to_text")],
                "category": [rule_data.get("category", "general")],
                "enabled": [rule_data.get("enabled", True)],
            }
        )

        # Get next available ID
        next_id = 0
        if not self._correction_rules_df.empty:
            next_id = self._correction_rules_df.index.max() + 1

        # Set the ID as index
        rule_df.index = [next_id]

        # Concatenate with existing rules
        if self._correction_rules_df.empty:
            self._correction_rules_df = rule_df
        else:
            self._correction_rules_df = pd.concat([self._correction_rules_df, rule_df])

        # Clear cache
        self._cache.clear()

        # Emit event
        self._emit_event(EventType.CORRECTION_RULES_UPDATED, self._correction_rules_df)

        self._logger.info(f"Added correction rule: {rule_data}")
        return next_id

    def update_correction_rule(self, rule_id: int, rule_data: Dict[str, Any]) -> bool:
        """Update an existing correction rule."""
        if rule_id not in self._correction_rules_df.index:
            self._logger.error(f"Correction rule with ID {rule_id} not found")
            return False

        # Update the rule
        for key, value in rule_data.items():
            if key in self._correction_rules_df.columns:
                self._correction_rules_df.at[rule_id, key] = value

        # Clear cache
        self._cache.clear()

        # Emit event
        self._emit_event(EventType.CORRECTION_RULES_UPDATED, self._correction_rules_df)

        self._logger.info(f"Updated correction rule with ID {rule_id}: {rule_data}")
        return True

    def remove_correction_rule(self, rule_id: int) -> bool:
        """Remove a correction rule."""
        if rule_id not in self._correction_rules_df.index:
            self._logger.error(f"Correction rule with ID {rule_id} not found")
            return False

        # Remove the rule
        self._correction_rules_df = self._correction_rules_df.drop(rule_id)

        # Clear cache
        self._cache.clear()

        # Emit event
        self._emit_event(EventType.CORRECTION_RULES_UPDATED, self._correction_rules_df)

        self._logger.info(f"Removed correction rule with ID {rule_id}")
        return True

    def get_validation_list(self, list_type: str) -> pd.DataFrame:
        """Get a validation list DataFrame."""
        if list_type not in self._validation_lists:
            self._logger.error(f"Invalid validation list type: {list_type}")
            return pd.DataFrame()

        if self._validation_lists[list_type].empty:
            return pd.DataFrame({"value": pd.Series(dtype="str")})

        return self._validation_lists[list_type].copy()

    def set_validation_list(self, list_type: str, df: pd.DataFrame) -> None:
        """Set a validation list DataFrame."""
        if list_type not in self._validation_lists:
            self._logger.error(f"Invalid validation list type: {list_type}")
            return

        if df is None:
            self._logger.error("Cannot set validation list to None")
            return

        # Validate DataFrame structure
        if "value" not in df.columns:
            self._logger.error("Missing required 'value' column in validation list DataFrame")
            return

        # Store a copy to ensure immutability
        self._validation_lists[list_type] = df.copy()

        # Ensure 'enabled' column exists with default value True
        if "enabled" not in self._validation_lists[list_type].columns:
            self._validation_lists[list_type]["enabled"] = True

        # Clear cache
        self._cache.clear()

        # Emit event
        self._emit_event(
            EventType.VALIDATION_LIST_UPDATED, {"list_type": list_type, "count": len(df)}
        )

        self._logger.info(f"Validation list '{list_type}' updated with {len(df)} entries")

    def add_validation_list_entry(self, list_type: str, value: str) -> bool:
        """Add a new entry to a validation list."""
        if list_type not in self._validation_lists:
            self._logger.error(f"Invalid validation list type: {list_type}")
            return False

        # Check if entry already exists
        if (
            not self._validation_lists[list_type].empty
            and value in self._validation_lists[list_type]["value"].values
        ):
            self._logger.warning(f"Entry '{value}' already exists in {list_type} validation list")
            return False

        # Create DataFrame for the new entry
        entry_df = pd.DataFrame({"value": [value], "enabled": [True]})

        # Get next available ID
        next_id = 0
        if not self._validation_lists[list_type].empty:
            next_id = self._validation_lists[list_type].index.max() + 1

        # Set the ID as index
        entry_df.index = [next_id]

        # Concatenate with existing entries
        if self._validation_lists[list_type].empty:
            self._validation_lists[list_type] = entry_df
        else:
            self._validation_lists[list_type] = pd.concat(
                [self._validation_lists[list_type], entry_df]
            )

        # Clear cache
        self._cache.clear()

        # Emit event
        self._emit_event(
            EventType.VALIDATION_LIST_UPDATED,
            {"list_type": list_type, "count": len(self._validation_lists[list_type])},
        )

        self._logger.info(f"Added '{value}' to '{list_type}' validation list")
        return True

    def remove_validation_list_entry(self, list_type: str, entry_id: int) -> bool:
        """Remove an entry from a validation list."""
        if list_type not in self._validation_lists:
            self._logger.error(f"Invalid validation list type: {list_type}")
            return False

        if (
            self._validation_lists[list_type].empty
            or entry_id not in self._validation_lists[list_type].index
        ):
            self._logger.error(f"Entry with ID {entry_id} not found in {list_type} validation list")
            return False

        # Remove the entry
        self._validation_lists[list_type] = self._validation_lists[list_type].drop(entry_id)

        # Clear cache
        self._cache.clear()

        # Emit event
        self._emit_event(
            EventType.VALIDATION_LIST_UPDATED,
            {"list_type": list_type, "count": len(self._validation_lists[list_type])},
        )

        self._logger.info(f"Removed entry with ID {entry_id} from '{list_type}' validation list")
        return True

    def get_enabled_correction_rules(self) -> pd.DataFrame:
        """Get the enabled correction rules."""
        return self._correction_rules_df[self._correction_rules_df["enabled"] == True].copy()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the data."""
        stats = {}

        # Entry statistics
        if not self._entries_df.empty:
            entry_stats = {
                "total": len(self._entries_df),
                "valid": len(self._entries_df[self._entries_df["status"] == "Valid"]),
                "invalid": len(self._entries_df[self._entries_df["status"] == "Invalid"]),
                "pending": len(self._entries_df[self._entries_df["status"] == "Pending"]),
                "chest_types": self._entries_df["chest_type"].value_counts().to_dict(),
                "players": self._entries_df["player"].value_counts().to_dict(),
                "sources": self._entries_df["source"].value_counts().to_dict(),
            }
            stats["entries"] = entry_stats

        # Correction rule statistics
        if not self._correction_rules_df.empty:
            rule_stats = {
                "total": len(self._correction_rules_df),
                "enabled": len(
                    self._correction_rules_df[self._correction_rules_df["enabled"] == True]
                ),
                "disabled": len(
                    self._correction_rules_df[self._correction_rules_df["enabled"] == False]
                ),
                "categories": self._correction_rules_df["category"].value_counts().to_dict(),
            }
            stats["rules"] = rule_stats

        # Validation list statistics
        validation_stats = {}
        for list_type, df in self._validation_lists.items():
            if not df.empty:
                validation_stats[list_type] = {
                    "total": len(df),
                    "enabled": len(df[df["enabled"] == True])
                    if "enabled" in df.columns
                    else len(df),
                }
        stats["validation_lists"] = validation_stats

        return stats


class CorrectionService:
    """Service for applying corrections to entries."""

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = CorrectionService()
        return cls._instance

    def __init__(self):
        """Initialize the CorrectionService."""
        # Get DataFrameStore instance
        self._store = DataFrameStore.get_instance()

        # Setup logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("CorrectionService initialized")

    def apply_corrections(self, specific_entries: Optional[List[int]] = None) -> int:
        """Apply all enabled correction rules to entries."""
        # Get entries and rules from DataFrameStore
        entries_df = self._store.get_entries()
        rules_df = self._store.get_enabled_correction_rules()

        if entries_df.empty:
            self._logger.warning("No entries to correct")
            return 0

        if rules_df.empty:
            self._logger.warning("No correction rules to apply")
            return 0

        # Filter entries if specific_entries is provided
        if specific_entries:
            entries_df = entries_df.loc[entries_df.index.isin(specific_entries)]
            if entries_df.empty:
                self._logger.warning("No matching entries found for correction")
                return 0

        # Start a transaction
        self._store.begin_transaction()

        try:
            # Track number of corrections applied
            total_corrections = 0

            # Apply the rules one by one
            for rule_id, rule in rules_df.iterrows():
                from_text = rule["from_text"]
                to_text = rule["to_text"]
                category = rule.get("category", "general")

                # Skip empty rules
                if not from_text or not to_text:
                    continue

                # Apply the rule to the appropriate field(s) based on category
                if category == "player":
                    fields = ["player"]
                elif category == "chest_type":
                    fields = ["chest_type"]
                elif category == "source":
                    fields = ["source"]
                else:  # 'general' or any other category
                    fields = ["chest_type", "player", "source"]

                # Apply the rule to each field
                for field in fields:
                    if field not in entries_df.columns:
                        continue

                    # Create a mask for entries matching the rule
                    mask = entries_df[field] == from_text
                    matching_entries = entries_df[mask]

                    # Skip if no matching entries
                    if matching_entries.empty:
                        continue

                    # Apply the correction
                    for entry_id in matching_entries.index:
                        # Store original value if this is the first correction to this field
                        if not isinstance(entries_df.at[entry_id, "original_values"], dict):
                            entries_df.at[entry_id, "original_values"] = {}

                        original_values = entries_df.at[entry_id, "original_values"]

                        # Only store the original value once (first correction)
                        if field not in original_values:
                            original_values[field] = entries_df.at[entry_id, field]

                        # Apply the correction
                        entries_df.at[entry_id, field] = to_text
                        entries_df.at[entry_id, "original_values"] = original_values

                        # Set status to Valid
                        entries_df.at[entry_id, "status"] = "Valid"

                        total_corrections += 1

            # Update the entries in DataFrameStore if we made changes
            if total_corrections > 0:
                # Update entries in store
                self._store.set_entries(entries_df)

                # Commit the transaction
                self._store.commit_transaction()

                # Emit correction applied event
                self._store._emit_event(
                    EventType.CORRECTION_APPLIED,
                    {
                        "count": total_corrections,
                        "entries_affected": len(
                            entries_df[
                                entries_df["original_values"].apply(
                                    lambda x: bool(x) if isinstance(x, dict) else False
                                )
                            ]
                        ),
                    },
                )

                self._logger.info(
                    f"Applied {total_corrections} corrections to {len(entries_df)} entries"
                )
            else:
                # Rollback the transaction since we didn't make any changes
                self._store.rollback_transaction()
                self._logger.info("No corrections applied")

            return total_corrections

        except Exception as e:
            # Rollback the transaction on error
            self._store.rollback_transaction()
            self._logger.error(f"Error applying corrections: {e}")
            raise


class ValidationService:
    """Service for validating entries against validation lists."""

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = ValidationService()
        return cls._instance

    def __init__(self):
        """Initialize the ValidationService."""
        # Get DataFrameStore instance
        self._store = DataFrameStore.get_instance()

        # Setup logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("ValidationService initialized")

        # Subscribe to events
        self._store.subscribe(EventType.VALIDATION_LIST_UPDATED, self._on_validation_list_updated)
        self._store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)

    def _on_validation_list_updated(self, event_data: Dict[str, Any]) -> None:
        """Handle validation list updated event."""
        self._logger.info(f"Validation list updated: {event_data}")
        self.validate_entries()

    def _on_entries_updated(self, event_data: Dict[str, Any]) -> None:
        """Handle entries updated event."""
        if event_data.get("source") != "validation_service":
            self._logger.info("Entries updated. Validating entries.")
            self.validate_entries()

    def validate_entries(self, specific_entries: Optional[List[int]] = None) -> Dict[str, int]:
        """Validate all entries or specific entries against validation lists."""
        # Get entries from DataFrameStore
        entries_df = self._store.get_entries()

        if entries_df.empty:
            self._logger.warning("No entries to validate")
            return {"valid": 0, "invalid": 0, "total": 0}

        # Filter entries if specific_entries is provided
        if specific_entries:
            entries_df = entries_df.loc[entries_df.index.isin(specific_entries)]
            if entries_df.empty:
                self._logger.warning("No matching entries found for validation")
                return {"valid": 0, "invalid": 0, "total": 0}

        # Get validation lists
        chest_types = self._store.get_validation_list("chest_types")
        player_names = self._store.get_validation_list("players")
        sources = self._store.get_validation_list("sources")

        # Start a transaction
        self._store.begin_transaction()

        try:
            # Reset validation errors for entries we're validating
            for entry_id in entries_df.index:
                entries_df.at[entry_id, "validation_errors"] = []

            # Validate chest_type
            if "chest_type" in entries_df.columns and not chest_types.empty:
                valid_chest_types = set(chest_types["value"].tolist())
                for entry_id, row in entries_df.iterrows():
                    chest_type = row["chest_type"]
                    if chest_type and chest_type not in valid_chest_types:
                        errors = entries_df.at[entry_id, "validation_errors"]
                        errors.append(f"Invalid chest type: '{chest_type}'")
                        entries_df.at[entry_id, "validation_errors"] = errors

            # Validate player
            if "player" in entries_df.columns and not player_names.empty:
                valid_players = set(player_names["value"].tolist())
                for entry_id, row in entries_df.iterrows():
                    player = row["player"]
                    if player and player not in valid_players:
                        errors = entries_df.at[entry_id, "validation_errors"]
                        errors.append(f"Invalid player name: '{player}'")
                        entries_df.at[entry_id, "validation_errors"] = errors

            # Validate source
            if "source" in entries_df.columns and not sources.empty:
                valid_sources = set(sources["value"].tolist())
                for entry_id, row in entries_df.iterrows():
                    source = row["source"]
                    if source and source not in valid_sources:
                        errors = entries_df.at[entry_id, "validation_errors"]
                        errors.append(f"Invalid source: '{source}'")
                        entries_df.at[entry_id, "validation_errors"] = errors

            # Update status based on validation errors
            for entry_id, row in entries_df.iterrows():
                if row["validation_errors"]:
                    entries_df.at[entry_id, "status"] = "Invalid"
                elif isinstance(row["original_values"], dict) and row["original_values"]:
                    # Has corrections applied
                    entries_df.at[entry_id, "status"] = "Valid"
                else:
                    entries_df.at[entry_id, "status"] = "Pending"

            # Update entries in store
            self._store.set_entries(entries_df, source="validation_service")

            # Commit the transaction
            self._store.commit_transaction()

            # Count validation results
            valid_count = len(entries_df[entries_df["status"].isin(["Valid", "Pending"])])
            invalid_count = len(entries_df[entries_df["status"] == "Invalid"])
            total_count = len(entries_df)

            # Emit validation completed event
            self._store._emit_event(
                EventType.VALIDATION_COMPLETED,
                {"valid": valid_count, "invalid": invalid_count, "total": total_count},
            )

            self._logger.info(
                f"Validated {total_count} entries: {valid_count} valid, {invalid_count} invalid"
            )

            return {"valid": valid_count, "invalid": invalid_count, "total": total_count}

        except Exception as e:
            # Rollback the transaction on error
            self._store.rollback_transaction()
            self._logger.error(f"Error validating entries: {e}")
            raise


class ServiceFactory:
    """Factory for creating and accessing services."""

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = ServiceFactory()
        return cls._instance

    def __init__(self):
        """Initialize the ServiceFactory."""
        # Initialize dictionaries for services
        self._services = {}

        # Setup logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("ServiceFactory initialized")

    def get_dataframe_store(self) -> DataFrameStore:
        """Get the DataFrameStore instance."""
        if "dataframe_store" not in self._services:
            self._services["dataframe_store"] = DataFrameStore.get_instance()
        return self._services["dataframe_store"]

    def get_correction_service(self) -> CorrectionService:
        """Get the CorrectionService instance."""
        if "correction_service" not in self._services:
            self._services["correction_service"] = CorrectionService.get_instance()
        return self._services["correction_service"]

    def get_validation_service(self) -> ValidationService:
        """Get the ValidationService instance."""
        if "validation_service" not in self._services:
            self._services["validation_service"] = ValidationService.get_instance()
        return self._services["validation_service"]

    def initialize_all_services(self) -> None:
        """Initialize all services."""
        self.get_dataframe_store()
        self.get_correction_service()
        self.get_validation_service()
        self._logger.info("All services initialized")


def on_entries_updated(event_data):
    """Handler for entries updated event."""
    print(f"Entries updated event received: {event_data}")

    # Get the updated entries
    store = DataFrameStore.get_instance()
    entries = store.get_entries()

    print(f"Total entries: {len(entries)}")
    if not entries.empty:
        print(f"Sample entry:\n{entries.iloc[0]}")


def on_correction_applied(event_data):
    """Handler for correction applied event."""
    print(f"Correction applied event received: {event_data}")

    # Get statistics on corrections
    store = DataFrameStore.get_instance()
    stats = store.get_statistics()

    print(f"Correction statistics: {stats.get('entries', {})}")


def demo_data_store():
    """Demonstrate the DataFrameStore functionality."""
    print("\n=== DataFrameStore Demo ===\n")

    # Get the data store instance
    store = DataFrameStore.get_instance()

    # Subscribe to events
    store.subscribe(EventType.ENTRIES_UPDATED, on_entries_updated)
    store.subscribe(EventType.CORRECTION_APPLIED, on_correction_applied)

    # Create some test entries
    entries_data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "chest_type": ["Gold", "Silver", "Bronze"],
        "player": ["Player1", "Player2", "Player3"],
        "source": ["Source1", "Source2", "Source3"],
        "status": ["Pending", "Pending", "Pending"],
        "validation_errors": [[], [], []],
        "original_values": [{}, {}, {}],
    }

    entries_df = pd.DataFrame(entries_data)

    # Start a transaction
    store.begin_transaction()

    # Set the entries
    store.set_entries(entries_df)

    # Commit the transaction
    store.commit_transaction()

    # Create validation lists
    chest_types_data = {"value": ["Gold", "Silver", "Bronze", "Platinum"]}
    player_names_data = {"value": ["Player1", "Player2", "Player3", "Player4"]}
    sources_data = {"value": ["Source1", "Source2", "Source3", "Source4"]}

    # Create DataFrames with the correct column name
    chest_types_df = pd.DataFrame(chest_types_data)
    player_names_df = pd.DataFrame(player_names_data)
    sources_df = pd.DataFrame(sources_data)

    # Set validation lists with the correct type names
    store.set_validation_list("players", player_names_df)
    store.set_validation_list("chest_types", chest_types_df)
    store.set_validation_list("sources", sources_df)

    # Create correction rules
    store.add_correction_rule(
        {
            "from_text": "Silver",
            "to_text": "Silver Chest",
            "category": "chest_type",
            "enabled": True,
        }
    )

    store.add_correction_rule(
        {"from_text": "Gold", "to_text": "Gold Chest", "category": "chest_type", "enabled": True}
    )

    # Display validation lists
    print("Chest Types:", store.get_validation_list("chest_types")["value"].tolist())
    print("Player Names:", store.get_validation_list("players")["value"].tolist())
    print("Sources:", store.get_validation_list("sources")["value"].tolist())

    # Display correction rules
    rules_df = store.get_correction_rules()
    print("\nCorrection Rules:")
    for rule_id, rule in rules_df.iterrows():
        print(f"  {rule_id}: {rule['from_text']} -> {rule['to_text']} ({rule['category']})")

    print("\nEntries before correction:")
    print(store.get_entries()[["chest_type", "player", "source", "status"]])

    return store


def demo_services():
    """Demonstrate the services functionality."""
    print("\n=== Services Demo ===\n")

    # Get the service factory
    factory = ServiceFactory.get_instance()

    # Initialize all services
    factory.initialize_all_services()

    # Get services
    correction_service = factory.get_correction_service()
    validation_service = factory.get_validation_service()

    # Apply corrections
    print("\nApplying corrections...")
    applied_count = correction_service.apply_corrections()
    print(f"Applied {applied_count} corrections")

    # Get the data store and display entries after correction
    store = factory.get_dataframe_store()
    print("\nEntries after correction:")
    print(store.get_entries()[["chest_type", "player", "source", "status", "original_values"]])

    # Validate entries
    print("\nValidating entries...")
    validation_result = validation_service.validate_entries()
    print(f"Validation result: {validation_result}")

    # Display entries after validation
    print("\nEntries after validation:")
    print(store.get_entries()[["chest_type", "player", "source", "status", "validation_errors"]])

    # Get statistics
    stats = store.get_statistics()
    print("\nStatistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    return factory


def main():
    """Main demo function."""
    print("=== Data Management System Demo ===")

    # Demo DataFrameStore
    store = demo_data_store()

    # Demo services
    factory = demo_services()

    print("\nDemo completed successfully!")


if __name__ == "__main__":
    main()
