"""
dataframe_store.py

Description: Central data store using pandas DataFrames as the primary data structure
Usage:
    from src.services.dataframe_store import DataFrameStore
    store = DataFrameStore.get_instance()
    entries_df = store.get_entries()
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable, TypeVar, Generic, Union
import functools
import threading
import uuid
from enum import Enum, auto

import pandas as pd

# Type variables for generic caching
T = TypeVar("T")
U = TypeVar("U")


class EventType(Enum):
    """Event types for the DataFrameStore event system."""

    ENTRIES_UPDATED = auto()
    CORRECTION_RULES_UPDATED = auto()
    VALIDATION_LISTS_UPDATED = auto()
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

    Attributes:
        _instance: Singleton instance
        _entries_df: DataFrame containing chest entries
        _correction_rules_df: DataFrame containing correction rules
        _validation_lists: Dictionary of DataFrames for validation lists
        _event_handlers: Dictionary of event handlers by event type
        _transaction_active: Flag indicating if a transaction is in progress

    Implementation Notes:
        - Uses singleton pattern for global access
        - Implements immutable state updates for data consistency
        - Provides transaction support for atomic operations
        - Uses pandas DataFrames for efficient data manipulation
    """

    # Singleton instance
    _instance = None
    _instance_lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance with thread-safety.

        Returns:
            DataFrameStore: The singleton instance
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = DataFrameStore()
        return cls._instance

    def __init__(self):
        """
        Initialize the DataFrameStore.

        Note: This should not be called directly. Use get_instance() instead.
        """
        # Setup logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("Initializing DataFrameStore")

        # Initialize DataFrames
        self._initialize_dataframes()

        # Event system
        self._event_handlers = {event_type: set() for event_type in EventType}

        # Transaction support
        self._transaction_active = False
        self._transaction_changes = {}

        # Cache for expensive operations
        self._cache = {}

        self._logger.info("DataFrameStore initialized")

    def _initialize_dataframes(self):
        """Initialize all DataFrames with proper schemas."""
        # Entries DataFrame
        self._entries_df = pd.DataFrame(
            {
                "id": pd.Series(dtype="int"),
                "chest_type": pd.Series(dtype="str"),
                "player": pd.Series(dtype="str"),
                "source": pd.Series(dtype="str"),
                "status": pd.Series(dtype="str"),
                "validation_errors": pd.Series(dtype="object"),  # List of strings
                "original_values": pd.Series(dtype="object"),  # Dict of original values
                "field_validation": pd.Series(dtype="object"),  # Dict of validation info
                "modified_at": pd.Series(dtype="datetime64[ns]"),
            }
        )

        # Create index on id column
        self._entries_df.set_index("id", inplace=True)

        # Correction Rules DataFrame
        self._correction_rules_df = pd.DataFrame(
            {
                "id": pd.Series(dtype="int"),
                "from_text": pd.Series(dtype="str"),
                "to_text": pd.Series(dtype="str"),
                "category": pd.Series(dtype="str"),
                "enabled": pd.Series(dtype="bool"),
                "created_at": pd.Series(dtype="datetime64[ns]"),
                "modified_at": pd.Series(dtype="datetime64[ns]"),
            }
        )

        # Create index on id column
        self._correction_rules_df.set_index("id", inplace=True)

        # Validation Lists as dictionary of DataFrames
        self._validation_lists = {
            "player": pd.DataFrame(
                {
                    "entry": pd.Series(dtype="str"),
                    "enabled": pd.Series(dtype="bool"),
                    "created_at": pd.Series(dtype="datetime64[ns]"),
                }
            ),
            "chest_type": pd.DataFrame(
                {
                    "entry": pd.Series(dtype="str"),
                    "enabled": pd.Series(dtype="bool"),
                    "created_at": pd.Series(dtype="datetime64[ns]"),
                }
            ),
            "source": pd.DataFrame(
                {
                    "entry": pd.Series(dtype="str"),
                    "enabled": pd.Series(dtype="bool"),
                    "created_at": pd.Series(dtype="datetime64[ns]"),
                }
            ),
        }

        # Create indexes on entry column for validation lists
        for list_type, df in self._validation_lists.items():
            df.set_index("entry", inplace=True)

    # =====================
    # Event System Methods
    # =====================

    def subscribe(self, event_type: EventType, handler: Callable):
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to be called when the event occurs
        """
        self._event_handlers[event_type].add(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Callback function to remove
        """
        if handler in self._event_handlers[event_type]:
            self._event_handlers[event_type].remove(handler)

    def _emit_event(self, event_type: EventType, data: Any = None):
        """
        Emit an event to all subscribers.

        Args:
            event_type: Type of event to emit
            data: Data to pass to the event handlers
        """
        for handler in self._event_handlers[event_type]:
            try:
                handler(data)
            except Exception as e:
                self._logger.error(f"Error in event handler for {event_type}: {e}")

    # =====================
    # Transaction Methods
    # =====================

    def begin_transaction(self):
        """
        Begin a transaction.

        This allows multiple changes to be made atomically.
        """
        if self._transaction_active:
            self._logger.warning("Transaction already in progress")
            return False

        self._transaction_active = True
        self._transaction_changes = {
            "entries_df": self._entries_df.copy(),
            "correction_rules_df": self._correction_rules_df.copy(),
            "validation_lists": {k: df.copy() for k, df in self._validation_lists.items()},
        }
        self._logger.debug("Transaction started")
        return True

    def commit_transaction(self):
        """
        Commit the current transaction.

        This applies all changes made during the transaction.
        """
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
        """
        Rollback the current transaction.

        This discards all changes made during the transaction.
        """
        if not self._transaction_active:
            self._logger.warning("No transaction in progress")
            return False

        # Restore original state
        self._entries_df = self._transaction_changes["entries_df"]
        self._correction_rules_df = self._transaction_changes["correction_rules_df"]
        self._validation_lists = self._transaction_changes["validation_lists"]

        # Clear transaction state
        self._transaction_active = False
        self._transaction_changes = {}

        self._logger.debug("Transaction rolled back")
        return True

    # =====================
    # Caching Methods
    # =====================

    def _cached(max_size: int = 128):
        """
        Decorator for caching method results.

        Args:
            max_size: Maximum number of items to cache
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                # Create a cache key from the function name and arguments
                key = (func.__name__, args, frozenset(kwargs.items()))

                # If key is in cache, return cached result
                if key in self._cache:
                    return self._cache[key]

                # Call the function and cache the result
                result = func(self, *args, **kwargs)

                # Limit cache size by removing oldest entries if needed
                if len(self._cache) >= max_size:
                    # Remove the first item (oldest)
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]

                self._cache[key] = result
                return result

            return wrapper

        return decorator

    def clear_cache(self):
        """Clear the cache of all stored results."""
        self._cache.clear()
        self._logger.debug("Cache cleared")

    # =====================
    # Data Access Methods
    # =====================

    # --- Entries DataFrame Methods ---

    def get_entries(self) -> pd.DataFrame:
        """
        Get the entries DataFrame.

        Returns:
            DataFrame: A copy of the entries DataFrame
        """
        return self._entries_df.copy()

    def set_entries(self, df: pd.DataFrame, source: str = "", emit_event: bool = True):
        """
        Set the entries DataFrame.

        Args:
            df: New entries DataFrame
            source: Source of the update (optional, for tracking)
            emit_event: Whether to emit an event after updating
        """
        # Validate DataFrame structure
        required_columns = {"chest_type", "player", "source", "status"}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            self._logger.error(f"Missing required columns in entries DataFrame: {missing}")
            raise ValueError(f"Missing required columns: {missing}")

        # Store a copy to ensure immutability
        self._entries_df = df.copy()

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            # Pass a dictionary with both the dataframe and metadata
            self._emit_event(
                EventType.ENTRIES_UPDATED,
                {"df": self._entries_df, "source": source, "count": len(df)},
            )

        self._logger.info(f"Entries DataFrame updated with {len(df)} rows")

    def add_entry(
        self, entry_data: Dict[str, Any], source: str = "", emit_event: bool = True
    ) -> int:
        """
        Add a new entry to the entries DataFrame.

        Args:
            entry_data: Dictionary with entry data
            source: Source of the update (optional, for tracking)
            emit_event: Whether to emit an event after updating

        Returns:
            int: ID of the added entry
        """
        # Validate required fields
        required_fields = {"chest_type", "player", "source"}
        if not required_fields.issubset(entry_data.keys()):
            missing = required_fields - set(entry_data.keys())
            self._logger.error(f"Missing required fields in entry data: {missing}")
            raise ValueError(f"Missing required fields: {missing}")

        # Generate ID if not provided
        if "id" not in entry_data:
            # Generate a unique ID
            entry_data["id"] = abs(
                hash((entry_data["chest_type"], entry_data["player"], entry_data["source"]))
            ) % (10**8)

        # Set default values for optional fields
        entry_data.setdefault("status", "Pending")
        entry_data.setdefault("validation_errors", [])
        entry_data.setdefault("original_values", {})
        entry_data.setdefault("field_validation", {})

        # Add timestamp
        import datetime

        entry_data.setdefault("modified_at", pd.Timestamp(datetime.datetime.now()))

        # Create new row
        new_row = pd.DataFrame([entry_data])

        # Set index
        if "id" in new_row.columns:
            new_row.set_index("id", inplace=True)

        # Append to existing DataFrame
        self._entries_df = pd.concat([self._entries_df, new_row])

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            # Pass a dictionary with both the dataframe and metadata
            self._emit_event(
                EventType.ENTRIES_UPDATED,
                {"df": self._entries_df, "source": source, "count": len(self._entries_df)},
            )

        entry_id = entry_data["id"]
        self._logger.info(f"Added new entry with ID {entry_id}")
        return entry_id

    def update_entry(
        self, entry_id: int, entry_data: Dict[str, Any], source: str = "", emit_event: bool = True
    ) -> bool:
        """
        Update an existing entry in the entries DataFrame.

        Args:
            entry_id: ID of the entry to update
            entry_data: Dictionary with updated entry data
            source: Source of the update (optional, for tracking)
            emit_event: Whether to emit an event after updating

        Returns:
            bool: True if entry was updated, False otherwise
        """
        if entry_id not in self._entries_df.index:
            self._logger.error(f"Entry with ID {entry_id} not found")
            return False

        # Update fields
        for key, value in entry_data.items():
            self._entries_df.at[entry_id, key] = value

        # Update modified timestamp
        import datetime

        self._entries_df.at[entry_id, "modified_at"] = pd.Timestamp(datetime.datetime.now())

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            # Pass a dictionary with both the dataframe and metadata
            self._emit_event(
                EventType.ENTRIES_UPDATED,
                {"df": self._entries_df, "source": source, "count": len(self._entries_df)},
            )

        self._logger.info(f"Updated entry with ID {entry_id}")
        return True

    def delete_entry(self, entry_id: int, source: str = "", emit_event: bool = True) -> bool:
        """
        Delete an entry from the entries DataFrame.

        Args:
            entry_id: ID of the entry to delete
            source: Source of the update (optional, for tracking)
            emit_event: Whether to emit an event after updating

        Returns:
            bool: True if entry was deleted, False otherwise
        """
        if entry_id not in self._entries_df.index:
            self._logger.error(f"Entry with ID {entry_id} not found")
            return False

        # Delete entry
        self._entries_df = self._entries_df.drop(entry_id)

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            # Pass a dictionary with both the dataframe and metadata
            self._emit_event(
                EventType.ENTRIES_UPDATED,
                {"df": self._entries_df, "source": source, "count": len(self._entries_df)},
            )

        self._logger.info(f"Deleted entry with ID {entry_id}")
        return True

    # --- Correction Rules DataFrame Methods ---

    def get_correction_rules(self) -> pd.DataFrame:
        """
        Get the correction rules DataFrame.

        Returns:
            DataFrame: A copy of the correction rules DataFrame
        """
        return self._correction_rules_df.copy()

    def set_correction_rules(self, df: pd.DataFrame, emit_event: bool = True):
        """
        Set the correction rules DataFrame.

        Args:
            df: New correction rules DataFrame
            emit_event: Whether to emit an event after updating
        """
        # Validate DataFrame structure
        required_columns = {"from_text", "to_text"}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            self._logger.error(f"Missing required columns in correction rules DataFrame: {missing}")
            raise ValueError(f"Missing required columns: {missing}")

        # Store a copy to ensure immutability
        self._correction_rules_df = df.copy()

        # Ensure 'enabled' column exists with default value True
        if "enabled" not in self._correction_rules_df.columns:
            self._correction_rules_df["enabled"] = True

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            self._emit_event(EventType.CORRECTION_RULES_UPDATED, self._correction_rules_df)

        self._logger.info(f"Correction rules DataFrame updated with {len(df)} rows")

    def add_correction_rule(self, rule_data: Dict[str, Any], emit_event: bool = True) -> int:
        """
        Add a new correction rule to the correction rules DataFrame.

        Args:
            rule_data: Dictionary with rule data
            emit_event: Whether to emit an event after updating

        Returns:
            int: ID of the added rule
        """
        # Validate required fields
        required_fields = {"from_text", "to_text"}
        if not required_fields.issubset(rule_data.keys()):
            missing = required_fields - set(rule_data.keys())
            self._logger.error(f"Missing required fields in rule data: {missing}")
            raise ValueError(f"Missing required fields: {missing}")

        # Generate ID if not provided
        if "id" not in rule_data:
            # Generate a unique ID
            rule_data["id"] = abs(hash((rule_data["from_text"], rule_data["to_text"]))) % (10**8)

        # Set default values for optional fields
        rule_data.setdefault("category", "general")
        rule_data.setdefault("enabled", True)

        # Add timestamps
        import datetime

        now = pd.Timestamp(datetime.datetime.now())
        rule_data.setdefault("created_at", now)
        rule_data.setdefault("modified_at", now)

        # Create new row
        new_row = pd.DataFrame([rule_data])

        # Set index
        if "id" in new_row.columns:
            new_row.set_index("id", inplace=True)

        # Append to existing DataFrame
        self._correction_rules_df = pd.concat([self._correction_rules_df, new_row])

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            self._emit_event(EventType.CORRECTION_RULES_UPDATED, self._correction_rules_df)

        rule_id = rule_data["id"]
        self._logger.info(f"Added new correction rule with ID {rule_id}")
        return rule_id

    def update_correction_rule(
        self, rule_id: int, rule_data: Dict[str, Any], emit_event: bool = True
    ) -> bool:
        """
        Update an existing correction rule in the correction rules DataFrame.

        Args:
            rule_id: ID of the rule to update
            rule_data: Dictionary with updated data
            emit_event: Whether to emit an event after updating

        Returns:
            bool: True if rule was updated, False if not found
        """
        # Check if rule exists
        if rule_id not in self._correction_rules_df.index:
            self._logger.warning(f"Correction rule with ID {rule_id} not found")
            return False

        # Update rule
        for key, value in rule_data.items():
            self._correction_rules_df.at[rule_id, key] = value

        # Update modified timestamp
        import datetime

        self._correction_rules_df.at[rule_id, "modified_at"] = pd.Timestamp(datetime.datetime.now())

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            self._emit_event(EventType.CORRECTION_RULES_UPDATED, self._correction_rules_df)

        self._logger.info(f"Updated correction rule with ID {rule_id}")
        return True

    def delete_correction_rule(self, rule_id: int, emit_event: bool = True) -> bool:
        """
        Delete a correction rule from the correction rules DataFrame.

        Args:
            rule_id: ID of the rule to delete
            emit_event: Whether to emit an event after updating

        Returns:
            bool: True if rule was deleted, False if not found
        """
        # Check if rule exists
        if rule_id not in self._correction_rules_df.index:
            self._logger.warning(f"Correction rule with ID {rule_id} not found")
            return False

        # Delete rule
        self._correction_rules_df = self._correction_rules_df.drop(rule_id)

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            self._emit_event(EventType.CORRECTION_RULES_UPDATED, self._correction_rules_df)

        self._logger.info(f"Deleted correction rule with ID {rule_id}")
        return True

    # --- Validation Lists DataFrame Methods ---

    def get_validation_list(self, list_type: str) -> pd.DataFrame:
        """
        Get a validation list DataFrame.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')

        Returns:
            DataFrame: A copy of the validation list DataFrame
        """
        if list_type not in self._validation_lists:
            self._logger.error(f"Invalid validation list type: {list_type}")
            raise ValueError(f"Invalid validation list type: {list_type}")

        return self._validation_lists[list_type].copy()

    def set_validation_list(self, list_type: str, df: pd.DataFrame, emit_event: bool = True):
        """
        Set a validation list DataFrame.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            df: New validation list DataFrame
            emit_event: Whether to emit an event after updating
        """
        if list_type not in self._validation_lists:
            self._logger.error(f"Invalid validation list type: {list_type}")
            raise ValueError(f"Invalid validation list type: {list_type}")

        # Validate DataFrame structure
        if "entry" not in df.columns and df.index.name != "entry":
            self._logger.error("Missing required 'entry' column in validation list DataFrame")
            raise ValueError("Missing required 'entry' column")

        # Store a copy to ensure immutability
        self._validation_lists[list_type] = df.copy()

        # Ensure 'enabled' column exists with default value True
        if "enabled" not in self._validation_lists[list_type].columns:
            self._validation_lists[list_type]["enabled"] = True

        # Make sure 'entry' is the index
        if df.index.name != "entry":
            self._validation_lists[list_type].set_index("entry", inplace=True)

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            self._emit_event(
                EventType.VALIDATION_LISTS_UPDATED, {list_type: self._validation_lists[list_type]}
            )

        self._logger.info(f"Validation list '{list_type}' updated with {len(df)} entries")

    def add_validation_entry(self, list_type: str, entry: str, emit_event: bool = True) -> bool:
        """
        Add a new entry to a validation list.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            entry: Entry text to add
            emit_event: Whether to emit an event after updating

        Returns:
            bool: True if entry was added, False if already exists
        """
        if list_type not in self._validation_lists:
            self._logger.error(f"Invalid validation list type: {list_type}")
            raise ValueError(f"Invalid validation list type: {list_type}")

        # Check if entry already exists
        if entry in self._validation_lists[list_type].index:
            self._logger.warning(f"Entry '{entry}' already exists in {list_type} validation list")
            return False

        # Add entry
        import datetime

        new_entry = pd.DataFrame(
            {"enabled": [True], "created_at": [pd.Timestamp(datetime.datetime.now())]},
            index=[entry],
        )
        new_entry.index.name = "entry"

        # Append to existing DataFrame
        self._validation_lists[list_type] = pd.concat(
            [self._validation_lists[list_type], new_entry]
        )

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            self._emit_event(
                EventType.VALIDATION_LISTS_UPDATED, {list_type: self._validation_lists[list_type]}
            )

        self._logger.info(f"Added '{entry}' to {list_type} validation list")
        return True

    def delete_validation_entry(self, list_type: str, entry: str, emit_event: bool = True) -> bool:
        """
        Delete an entry from a validation list.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            entry: Entry text to delete
            emit_event: Whether to emit an event after updating

        Returns:
            bool: True if entry was deleted, False if not found
        """
        if list_type not in self._validation_lists:
            self._logger.error(f"Invalid validation list type: {list_type}")
            raise ValueError(f"Invalid validation list type: {list_type}")

        # Check if entry exists
        if entry not in self._validation_lists[list_type].index:
            self._logger.warning(f"Entry '{entry}' not found in {list_type} validation list")
            return False

        # Delete entry
        self._validation_lists[list_type] = self._validation_lists[list_type].drop(entry)

        # Clear cache
        self._cache.clear()

        # Emit event
        if emit_event:
            self._emit_event(
                EventType.VALIDATION_LISTS_UPDATED, {list_type: self._validation_lists[list_type]}
            )

        self._logger.info(f"Deleted '{entry}' from {list_type} validation list")
        return True

    # =====================
    # Query Methods
    # =====================

    @_cached(max_size=32)
    def query_entries(self, query_str: str) -> pd.DataFrame:
        """
        Query the entries DataFrame using pandas query syntax.

        Args:
            query_str: Query string for pandas query method

        Returns:
            DataFrame: Filtered DataFrame with query results
        """
        try:
            result = self._entries_df.query(query_str)
            self._logger.debug(f"Query '{query_str}' returned {len(result)} results")
            return result.copy()
        except Exception as e:
            self._logger.error(f"Error executing query '{query_str}': {e}")
            raise ValueError(f"Invalid query: {e}")

    @_cached(max_size=32)
    def query_correction_rules(self, query_str: str) -> pd.DataFrame:
        """
        Query the correction rules DataFrame using pandas query syntax.

        Args:
            query_str: Query string for pandas query method

        Returns:
            DataFrame: Filtered DataFrame with query results
        """
        try:
            result = self._correction_rules_df.query(query_str)
            self._logger.debug(f"Query '{query_str}' returned {len(result)} results")
            return result.copy()
        except Exception as e:
            self._logger.error(f"Error executing query '{query_str}': {e}")
            raise ValueError(f"Invalid query: {e}")

    @_cached(max_size=32)
    def get_enabled_correction_rules(self) -> pd.DataFrame:
        """
        Get only enabled correction rules.

        Returns:
            DataFrame: DataFrame with only enabled correction rules
        """
        if "enabled" in self._correction_rules_df.columns:
            result = self._correction_rules_df[self._correction_rules_df["enabled"]]
            self._logger.debug(f"Found {len(result)} enabled correction rules")
            return result.copy()
        else:
            self._logger.warning(
                "No 'enabled' column in correction rules DataFrame, returning all rules"
            )
            return self._correction_rules_df.copy()

    # =====================
    # Statistics Methods
    # =====================

    @_cached(max_size=16)
    def get_entry_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the entries.

        Returns:
            Dict: Dictionary with statistics
        """
        stats = {}

        # Total counts
        stats["total_entries"] = len(self._entries_df)

        # Status counts
        if "status" in self._entries_df.columns:
            status_counts = self._entries_df["status"].value_counts().to_dict()
            stats["status_counts"] = status_counts
            stats["valid_entries"] = status_counts.get("Valid", 0)
            stats["invalid_entries"] = status_counts.get("Invalid", 0)
            stats["pending_entries"] = status_counts.get("Pending", 0)

        # Field counts
        stats["unique_players"] = (
            self._entries_df["player"].nunique() if "player" in self._entries_df.columns else 0
        )
        stats["unique_chest_types"] = (
            self._entries_df["chest_type"].nunique()
            if "chest_type" in self._entries_df.columns
            else 0
        )
        stats["unique_sources"] = (
            self._entries_df["source"].nunique() if "source" in self._entries_df.columns else 0
        )

        # Correction counts
        if "original_values" in self._entries_df.columns:
            stats["corrected_entries"] = self._entries_df["original_values"].apply(bool).sum()

        return stats

    @_cached(max_size=16)
    def get_correction_rule_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the correction rules.

        Returns:
            Dict: Dictionary with statistics
        """
        stats = {}

        # Total counts
        stats["total_rules"] = len(self._correction_rules_df)

        # Enabled/disabled counts
        if "enabled" in self._correction_rules_df.columns:
            stats["enabled_rules"] = self._correction_rules_df["enabled"].sum()
            stats["disabled_rules"] = len(self._correction_rules_df) - stats["enabled_rules"]

        # Category counts
        if "category" in self._correction_rules_df.columns:
            stats["category_counts"] = (
                self._correction_rules_df["category"].value_counts().to_dict()
            )

        return stats

    @_cached(max_size=16)
    def get_validation_list_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics about the validation lists.

        Returns:
            Dict: Dictionary with statistics for each list type
        """
        stats = {}

        for list_type, df in self._validation_lists.items():
            list_stats = {}

            # Total counts
            list_stats["total_entries"] = len(df)

            # Enabled/disabled counts
            if "enabled" in df.columns:
                list_stats["enabled_entries"] = df["enabled"].sum()
                list_stats["disabled_entries"] = len(df) - list_stats["enabled_entries"]

            stats[list_type] = list_stats
