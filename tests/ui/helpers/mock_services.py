"""
mock_services.py

Description: Mock implementations of application services for UI testing
Usage:
    Used in UI tests to isolate components from real services
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional, Union, Set
import copy
from datetime import datetime

from src.interfaces.i_data_store import IDataStore, EventType
from src.interfaces.i_validation_service import IValidationService
from src.interfaces.i_correction_service import ICorrectionService
from src.interfaces.i_config_manager import IConfigManager
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_service_factory import IServiceFactory
from src.interfaces.events import EventHandler, EventData

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal


class MockDataStore(IDataStore):
    """
    Mock implementation of the data store for testing.
    """

    def __init__(self):
        """Initialize the mock data store."""
        self.entries = pd.DataFrame()
        self.validation_lists = {
            "player": pd.DataFrame(columns=["value"]),
            "chest_type": pd.DataFrame(columns=["value"]),
            "source": pd.DataFrame(columns=["value"]),
        }
        self.correction_rules = pd.DataFrame()
        self.event_handlers = {}
        self.transaction_active = False
        self.transaction_backup = None
        self.register_history = []

    def get_entries(self) -> pd.DataFrame:
        """
        Get all entries as a DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing all entries
        """
        return self.entries.copy()

    def set_entries(self, entries_df: pd.DataFrame, source: str = "") -> bool:
        """
        Set the entries DataFrame.

        Args:
            entries_df: DataFrame containing entries
            source: Optional source identifier for the update

        Returns:
            bool: True if successful, False otherwise
        """
        self.entries = entries_df.copy()
        self._notify(EventType.ENTRIES_UPDATED, {"source": source})
        return True

    def get_validation_list(self, list_type: str) -> pd.DataFrame:
        """
        Get a validation list by type.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')

        Returns:
            pd.DataFrame: DataFrame containing the validation list
        """
        if list_type in self.validation_lists:
            return self.validation_lists[list_type].copy()
        return pd.DataFrame(columns=["value"])

    def set_validation_list(self, list_type: str, entries_df: pd.DataFrame) -> bool:
        """
        Set a validation list.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            entries_df: DataFrame containing the validation list

        Returns:
            bool: True if successful, False otherwise
        """
        if list_type in self.validation_lists:
            self.validation_lists[list_type] = entries_df.copy()
            self._notify(EventType.VALIDATION_LIST_UPDATED, {"list_type": list_type})
            return True
        return False

    def add_validation_list(self, list_type: str, entries: List[str]) -> bool:
        """
        Add a validation list with the given entries.

        Args:
            list_type: Type of validation list to add (e.g., 'players', 'chest_types', 'sources')
            entries: List of entries to add to the validation list

        Returns:
            bool: True if successful
        """
        # Convert list_type to the expected internal format
        # 'players' -> 'player', 'chest_types' -> 'chest_type', 'sources' -> 'source'
        internal_type = list_type.rstrip("s")  # Remove trailing 's' if present

        # Create a DataFrame for the entries
        df = pd.DataFrame({internal_type: entries})

        # Set the validation list
        return self.set_validation_list(internal_type, df)

    def add_validation_entry(self, list_type: str, entry: str) -> bool:
        """
        Add an entry to a validation list.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            entry: Entry to add

        Returns:
            bool: True if successful, False otherwise
        """
        if list_type in self.validation_lists:
            new_entry = pd.DataFrame({"value": [entry]})
            self.validation_lists[list_type] = pd.concat(
                [self.validation_lists[list_type], new_entry], ignore_index=True
            )
            self._notify(EventType.VALIDATION_LIST_UPDATED, {"list_type": list_type})
            return True
        return False

    def remove_validation_entry(self, list_type: str, entry: str) -> bool:
        """
        Remove an entry from a validation list.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            entry: Entry to remove

        Returns:
            bool: True if successful, False otherwise
        """
        if list_type in self.validation_lists:
            before_count = len(self.validation_lists[list_type])
            self.validation_lists[list_type] = self.validation_lists[list_type][
                self.validation_lists[list_type]["value"] != entry
            ]
            after_count = len(self.validation_lists[list_type])

            if before_count != after_count:
                self._notify(EventType.VALIDATION_LIST_UPDATED, {"list_type": list_type})
                return True
        return False

    def get_correction_rules(self) -> pd.DataFrame:
        """
        Get all correction rules.

        Returns:
            pd.DataFrame: DataFrame containing all correction rules
        """
        return self.correction_rules.copy()

    def set_correction_rules(self, rules_df: pd.DataFrame) -> bool:
        """
        Set the correction rules DataFrame.

        Args:
            rules_df: DataFrame containing correction rules

        Returns:
            bool: True if successful, False otherwise
        """
        self.correction_rules = rules_df.copy()
        self._notify(EventType.CORRECTION_RULES_UPDATED, {})
        return True

    def begin_transaction(self) -> bool:
        """
        Begin a transaction.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.transaction_active:
            self.transaction_active = True
            self.transaction_backup = {
                "entries": self.entries.copy(),
                "validation_lists": {k: v.copy() for k, v in self.validation_lists.items()},
                "correction_rules": self.correction_rules.copy(),
            }
            return True
        return False

    def commit_transaction(self) -> bool:
        """
        Commit the current transaction.

        Returns:
            bool: True if successful, False otherwise
        """
        if self.transaction_active:
            self.transaction_active = False
            self.transaction_backup = None
            return True
        return False

    def rollback_transaction(self) -> bool:
        """
        Rollback the current transaction.

        Returns:
            bool: True if successful, False otherwise
        """
        if self.transaction_active and self.transaction_backup is not None:
            self.entries = self.transaction_backup["entries"].copy()
            self.validation_lists = {
                k: v.copy() for k, v in self.transaction_backup["validation_lists"].items()
            }
            self.correction_rules = self.transaction_backup["correction_rules"].copy()
            self.transaction_active = False
            self.transaction_backup = None
            return True
        return False

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to be called when the event occurs
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        if handler not in self.event_handlers[event_type]:
            self.event_handlers[event_type].append(handler)

        self.register_history.append(("subscribe", event_type, handler))

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Callback function to remove
        """
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            self.register_history.append(("unsubscribe", event_type, handler))

    def _notify(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """
        Notify all subscribers of an event.

        Args:
            event_type: Type of event that occurred
            data: Event data to be passed to handlers
        """
        if event_type in self.event_handlers:
            event_data = EventData(event_type=event_type, data=data)
            for handler in self.event_handlers[event_type]:
                handler(event_data)

    # Additional helper methods for testing
    def get_register_history(self) -> List[tuple]:
        """
        Get the history of register/unregister operations.

        Returns:
            List[tuple]: List of operations performed
        """
        return self.register_history.copy()

    def set_data(self, data: pd.DataFrame) -> None:
        """
        Set the entries data (compatibility method for tests).

        This is an alias for set_entries for backward compatibility with tests.

        Args:
            data: DataFrame to store as entries
        """
        self.set_entries(data)
        # For backward compatibility
        self.data = data.copy()


class MockConfigManager(IConfigManager):
    """
    Mock implementation of the configuration manager for testing.
    """

    def __init__(self):
        """Initialize the mock configuration manager."""
        self.config = {}
        self.save_calls = []
        self.load_calls = []

    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if key does not exist

        Returns:
            Any: Configuration value
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default

    def set_value(self, section: str, key: str, value: Any) -> bool:
        """
        Set a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set

        Returns:
            bool: True if successful, False otherwise
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        return True

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get all values in a configuration section.

        Args:
            section: Configuration section

        Returns:
            Dict[str, Any]: Dictionary of key-value pairs
        """
        return self.config.get(section, {}).copy()

    def save_config(self) -> bool:
        """
        Save the configuration to file.

        Returns:
            bool: True if successful, False otherwise
        """
        self.save_calls.append({"time": datetime.now(), "config": copy.deepcopy(self.config)})
        return True

    def load_config(self) -> bool:
        """
        Load the configuration from file.

        Returns:
            bool: True if successful, False otherwise
        """
        self.load_calls.append({"time": datetime.now()})
        return True

    def get_str(self, section: str, key: str, fallback: str = "") -> str:
        """
        Get a string value from the configuration.

        Args:
            section: Configuration section
            key: Configuration key
            fallback: Default value if key does not exist

        Returns:
            str: String value
        """
        value = self.get_value(section, key, fallback)
        return str(value)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """
        Get an integer value from the configuration.

        Args:
            section: Configuration section
            key: Configuration key
            fallback: Default value if key does not exist

        Returns:
            int: Integer value
        """
        value = self.get_value(section, key, fallback)
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """
        Get a boolean value from the configuration.

        Args:
            section: Configuration section
            key: Configuration key
            fallback: Default value if key does not exist

        Returns:
            bool: Boolean value
        """
        value = self.get_value(section, key, fallback)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "t", "y")
        return bool(value)

    # Additional helper methods for testing
    def get_save_history(self) -> List[Dict[str, Any]]:
        """
        Get the save history.

        Returns:
            List[Dict[str, Any]]: List of save operations
        """
        return self.save_calls.copy()

    def get_load_history(self) -> List[Dict[str, Any]]:
        """
        Get the load history.

        Returns:
            List[Dict[str, Any]]: List of load operations
        """
        return self.load_calls.copy()


class MockFileService(IFileService):
    """
    Mock implementation of the IFileService interface for testing.

    This class tracks calls to its methods and provides simple mock implementations.
    """

    def __init__(self):
        """Initialize a new MockFileService instance."""
        self.load_entries_calls = []
        self.save_entries_calls = []
        self.load_validation_list_calls = []
        self.save_validation_list_calls = []
        self.load_correction_rules_calls = []
        self.save_correction_rules_calls = []
        self.success_value = True  # Can be set to False to simulate failures

    def load_entries(self, file_path: Path) -> bool:
        """
        Mock implementation of loading entries from a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: The current success_value
        """
        self.load_entries_calls.append(str(file_path))
        return self.success_value

    def save_entries(self, file_path: Path) -> bool:
        """
        Mock implementation of saving entries to a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: The current success_value
        """
        self.save_entries_calls.append(str(file_path))
        return self.success_value

    def load_validation_list(self, list_type: str, file_path: Path) -> bool:
        """
        Mock implementation of loading a validation list from a file.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            file_path: Path to the file

        Returns:
            bool: The current success_value
        """
        self.load_validation_list_calls.append((list_type, str(file_path)))
        return self.success_value

    def save_validation_list(self, list_type: str, file_path: Path) -> bool:
        """
        Mock implementation of saving a validation list to a file.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            file_path: Path to the file

        Returns:
            bool: The current success_value
        """
        self.save_validation_list_calls.append((list_type, str(file_path)))
        return self.success_value

    def load_correction_rules(self, file_path: Path) -> bool:
        """
        Mock implementation of loading correction rules from a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: The current success_value
        """
        self.load_correction_rules_calls.append(str(file_path))
        return self.success_value

    def save_correction_rules(self, file_path: Path) -> bool:
        """
        Mock implementation of saving correction rules to a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: The current success_value
        """
        self.save_correction_rules_calls.append(str(file_path))
        return self.success_value

    def set_success_value(self, value: bool) -> None:
        """
        Set the success value to be returned by mock methods.

        Args:
            value: True for success, False for failure
        """
        self.success_value = value

    def reset_call_history(self) -> None:
        """Reset all call history."""
        self.load_entries_calls = []
        self.save_entries_calls = []
        self.load_validation_list_calls = []
        self.save_validation_list_calls = []
        self.load_correction_rules_calls = []
        self.save_correction_rules_calls = []


class MockCorrectionService(ICorrectionService):
    """
    Mock implementation of ICorrectionService for testing.

    Attributes:
        correction_rules: List of correction rules
        applied_corrections: List of applied corrections
        correction_enabled: Flag for correction enabled state

    Implementation Notes:
        - Simulates correction rule application without actual processing
        - Records applied corrections for verification during testing
        - Provides methods to preset rules and inspect operations
    """

    def __init__(self):
        """Initialize the MockCorrectionService with empty rules."""
        self.correction_rules = []
        self.applied_corrections = []
        self.correction_enabled = True
        self.specific_corrections = []
        self.reset_history = []

    def load_correction_rules(self, file_path: str) -> bool:
        """
        Load correction rules from a file.

        Args:
            file_path: Path to the rules file

        Returns:
            bool: Always True for mock
        """
        # Mock implementation - doesn't actually load from file
        return True

    def save_correction_rules(self, file_path: str) -> bool:
        """
        Save correction rules to a file.

        Args:
            file_path: Path to save the rules

        Returns:
            bool: Always True for mock
        """
        # Mock implementation - doesn't actually save to file
        return True

    def apply_corrections(self, specific_entries: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Apply all correction rules to entries.

        Args:
            specific_entries: Optional list of entry IDs to correct (corrects all if None)

        Returns:
            Dict[str, int]: Correction statistics (applied, total)
        """
        # Record that corrections were applied
        self.applied_corrections.append(
            {"specific_entries": specific_entries, "rules_count": len(self.correction_rules)}
        )

        if not self.correction_enabled or not self.correction_rules:
            return {"applied": 0, "total": 0}

        # Mock implementation - returns fake stats
        applied_count = len(specific_entries) if specific_entries else 10
        return {"applied": applied_count, "total": applied_count}

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
        # Record the specific correction for verification
        self.specific_corrections.append(
            {"entry_id": entry_id, "field": field, "from_text": from_text, "to_text": to_text}
        )

        # Mock always returns success
        return True

    def reset_corrections(self, entry_ids: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Reset corrections by restoring original values.

        Args:
            entry_ids: Optional list of entry IDs to reset (resets all if None)

        Returns:
            Dict[str, int]: Reset statistics (reset, total)
        """
        # Record the reset operation for verification
        self.reset_history.append({"entry_ids": entry_ids})

        # Mock implementation - returns fake stats
        reset_count = len(entry_ids) if entry_ids else 10
        return {"reset": reset_count, "total": reset_count}

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
        self.correction_rules.append(
            {
                "field": field,
                "incorrect_value": incorrect_value,
                "correct_value": correct_value,
                "case_sensitive": case_sensitive,
                "match_type": match_type,
                "enabled": enabled,
            }
        )
        return True

    def set_correction_rules(self, rules: List[dict]) -> None:
        """
        Set the correction rules.

        Args:
            rules: List of rule dictionaries
        """
        self.correction_rules = rules.copy()

    def get_correction_rules(self) -> List[dict]:
        """
        Get the correction rules.

        Returns:
            List[dict]: List of rule dictionaries
        """
        return self.correction_rules.copy()

    def set_correction_enabled(self, enabled: bool) -> None:
        """
        Set the correction enabled state.

        Args:
            enabled: Whether corrections are enabled
        """
        self.correction_enabled = enabled

    def is_correction_enabled(self) -> bool:
        """
        Check if corrections are enabled.

        Returns:
            bool: True if corrections are enabled
        """
        return self.correction_enabled

    def get_applied_corrections(self) -> List[dict]:
        """
        Get list of applied corrections.

        Returns:
            List[dict]: List of applied correction details
        """
        return self.applied_corrections.copy()

    def get_specific_corrections(self) -> List[dict]:
        """
        Get list of specific corrections applied.

        Returns:
            List[dict]: List of specific correction details
        """
        return self.specific_corrections.copy()

    def get_reset_history(self) -> List[dict]:
        """
        Get history of reset operations.

        Returns:
            List[dict]: List of reset operation details
        """
        return self.reset_history.copy()

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self.correction_rules = []
        self.applied_corrections = []
        self.specific_corrections = []
        self.reset_history = []
        self.correction_enabled = True


class MockValidationService(IValidationService):
    """
    Mock implementation of IValidationService for testing.

    Attributes:
        validation_lists: Dictionary of validation lists
        validation_results: Dictionary of validation results
        validation_enabled: Flag for validation enabled state

    Implementation Notes:
        - Simulates validation without actual processing
        - Records validation operations for verification during testing
        - Provides methods to preset validation lists and inspect operations
    """

    def __init__(self):
        """Initialize the MockValidationService with empty lists."""
        self.validation_lists = {}
        self.validation_results = {}
        self.validation_enabled = True
        self.validation_history = []
        self.invalid_entries = []

    def load_validation_list(self, list_name: str, file_path: str) -> bool:
        """
        Load a validation list from a file.

        Args:
            list_name: Name of the validation list
            file_path: Path to the list file

        Returns:
            bool: Always True for mock
        """
        # Mock implementation - doesn't actually load from file
        return True

    def save_validation_list(self, list_name: str, file_path: str) -> bool:
        """
        Save a validation list to a file.

        Args:
            list_name: Name of the validation list
            file_path: Path to save the list

        Returns:
            bool: Always True for mock
        """
        # Mock implementation - doesn't actually save to file
        return True

    def validate(self, data: pd.DataFrame) -> Dict[str, Dict[str, Set[str]]]:
        """
        Validate data against validation lists.

        Args:
            data: DataFrame to validate

        Returns:
            Dict[str, Dict[str, Set[str]]]: Validation results
        """
        if not self.validation_enabled:
            return {}

        # Record validation operation
        self.validation_history.append(
            {"data_shape": data.shape, "validation_lists": list(self.validation_lists.keys())}
        )

        # Return mock validation results
        return self.validation_results.copy()

    def validate_entries(self, specific_entries: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Validate all entries or specific entries against validation lists.

        Args:
            specific_entries: Optional list of entry IDs to validate (validates all if None)

        Returns:
            Dict[str, int]: Validation statistics (valid, invalid, total)
        """
        if not self.validation_enabled:
            return {"valid": 0, "invalid": 0, "total": 0}

        # Record validation operation
        self.validation_history.append(
            {
                "specific_entries": specific_entries,
                "validation_lists": list(self.validation_lists.keys()),
            }
        )

        # Return mock validation statistics
        total = len(specific_entries) if specific_entries else 100
        invalid = len(self.invalid_entries) if self.invalid_entries else 10
        return {"valid": total - invalid, "invalid": invalid, "total": total}

    def get_invalid_entries(self) -> List[int]:
        """
        Get a list of invalid entry IDs.

        Returns:
            List[int]: List of entry IDs that failed validation
        """
        return self.invalid_entries.copy()

    def set_validation_list(self, list_name: str, items: List[str]) -> None:
        """
        Set a validation list.

        Args:
            list_name: Name of the validation list
            items: List of items for validation
        """
        self.validation_lists[list_name] = items.copy()

    def get_validation_list(self, list_name: str) -> List[str]:
        """
        Get a validation list.

        Args:
            list_name: Name of the validation list

        Returns:
            List[str]: List of validation items or empty list
        """
        return self.validation_lists.get(list_name, []).copy()

    def set_validation_results(self, results: Dict[str, Dict[str, Set[str]]]) -> None:
        """
        Set mock validation results.

        Args:
            results: Validation results to return
        """
        self.validation_results = results.copy()

    def set_invalid_entries(self, invalid_entries: List[int]) -> None:
        """
        Set mock invalid entries.

        Args:
            invalid_entries: List of entry IDs that are invalid
        """
        self.invalid_entries = invalid_entries.copy()

    def set_validation_enabled(self, enabled: bool) -> None:
        """
        Set the validation enabled state.

        Args:
            enabled: Whether validation is enabled
        """
        self.validation_enabled = enabled

    def is_validation_enabled(self) -> bool:
        """
        Check if validation is enabled.

        Returns:
            bool: True if validation is enabled
        """
        return self.validation_enabled

    def get_validation_history(self) -> List[dict]:
        """
        Get validation operation history.

        Returns:
            List[dict]: List of validation operation details
        """
        return self.validation_history.copy()

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self.validation_lists = {}
        self.validation_results = {}
        self.validation_enabled = True
        self.validation_history = []
        self.invalid_entries = []


class MockServiceFactory(IServiceFactory):
    """
    Mock implementation of IServiceFactory for testing.

    Attributes:
        services: Dictionary of registered services

    Implementation Notes:
        - Allows registration and retrieval of mock services
        - Provides methods to preset services and inspect registrations
        - Used to inject mock services into components under test
    """

    def __init__(
        self,
        correction_service=None,
        validation_service=None,
        data_store=None,
        config_manager=None,
        file_service=None,
    ):
        """
        Initialize the MockServiceFactory with provided services or empty services.

        Args:
            correction_service: Optional MockCorrectionService instance
            validation_service: Optional MockValidationService instance
            data_store: Optional MockDataStore instance
            config_manager: Optional MockConfigManager instance
            file_service: Optional MockFileService instance
        """
        self.services = {}
        self.service_creation_history = []

        # Register provided services or create defaults
        if correction_service:
            self.services[ICorrectionService] = correction_service
        if validation_service:
            self.services[IValidationService] = validation_service
        if data_store:
            self.services[IDataStore] = data_store
        if config_manager:
            self.services[IConfigManager] = config_manager
        if file_service:
            self.services[IFileService] = file_service

    def get_service(self, service_type):
        """
        Get a service by type.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Any: The service instance

        Raises:
            ValueError: If no implementation is registered for the service type
        """
        self.service_creation_history.append(service_type)
        service = self.services.get(service_type)
        if service is None:
            raise ValueError(f"No implementation registered for service type: {service_type}")
        return service

    def register_service(self, service_type, service: Any) -> None:
        """
        Register a service.

        Args:
            service_type: Type of service to register
            service: Service instance to register
        """
        self.services[service_type] = service

    def create_default_services(self) -> None:
        """Create and register default mock services."""
        self.services = {
            IDataStore: MockDataStore(),
            IConfigManager: MockConfigManager(),
            IFileService: MockFileService(),
            ICorrectionService: MockCorrectionService(),
            IValidationService: MockValidationService(),
        }

    def get_registered_services(self) -> Dict[str, Any]:
        """
        Get dictionary of registered services.

        Returns:
            Dict[str, Any]: Dictionary of service type to service instance
        """
        return self.services.copy()

    def get_service_creation_history(self) -> List[str]:
        """
        Get history of service creation requests.

        Returns:
            List[str]: List of service types requested
        """
        return self.service_creation_history.copy()

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self.services = {}
        self.service_creation_history = []


class MockRuleEditDialog(QWidget):
    """
    Mock implementation of RuleEditDialog for testing.

    Attributes:
        rule: The rule being edited
        validation_lists: Validation lists available
        rule_data: Current rule data
    """

    def __init__(self, rule=None, validation_lists=None, parent=None):
        """
        Initialize the RuleEditDialog mock.

        Args:
            rule: Optional rule data dictionary
            validation_lists: Optional dictionary of validation lists
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.rule = rule or {}
        self.validation_lists = validation_lists or {}
        self.rule_data = None
        self.accepted = False
        self.rejected = False

        # Default properties for the dialog
        self._title = "Mock Rule Editor"

        # Initialize with rule data if provided
        if rule:
            self.rule_data = {
                "player": rule.get("player", ""),
                "chest_type": rule.get("chest_type", ""),
                "replace_chest_type": rule.get("replace_chest_type", ""),
                "source": rule.get("source", ""),
                "enabled": rule.get("enabled", True),
            }
        else:
            self.rule_data = {
                "player": "",
                "chest_type": "",
                "replace_chest_type": "",
                "source": "",
                "enabled": True,
            }

        # UI elements expected by tests
        self.player_dropdown = MockComboBox()
        self.chest_type_dropdown = MockComboBox()
        self.source_dropdown = MockComboBox()

        # Set up mock UI elements
        if validation_lists:
            # Populate dropdowns from validation lists
            if "player" in validation_lists:
                self.player_dropdown.addItems(
                    ["-- Select --"] + validation_lists["player"].get_items()
                )
            if "chest_type" in validation_lists:
                self.chest_type_dropdown.addItems(
                    ["-- Select --"] + validation_lists["chest_type"].get_items()
                )
            if "source" in validation_lists:
                self.source_dropdown.addItems(
                    ["-- Select --"] + validation_lists["source"].get_items()
                )

    def accept(self):
        """Accept the dialog."""
        self.accepted = True

    def reject(self):
        """Reject the dialog."""
        self.rejected = True

    def get_rule_data(self):
        """Get the rule data from the dialog."""
        return self.rule

    def windowTitle(self):
        """Get the window title."""
        return "Edit Correction Rule"


class MockComboBox:
    """Mock combo box for testing."""

    def __init__(self):
        self.items = []
        self.current_index = 0

    def addItems(self, items):
        """Add items to the combo box."""
        self.items.extend(items)

    def count(self):
        """Get the number of items in the combo box."""
        return len(self.items)

    def setCurrentIndex(self, index):
        """Set the current index."""
        self.current_index = index

    def currentIndex(self):
        """Get the current index."""
        return self.current_index


class MockCorrectionRulesTable(QWidget):
    """
    Mock implementation of the CorrectionRulesTable for testing.

    Attributes:
        rules: List of correction rules
        validation_lists: Dictionary of validation lists
    """

    # Define signals
    rules_updated = Signal()

    def __init__(self, validation_lists=None, parent=None):
        """
        Initialize the MockCorrectionRulesTable.

        Args:
            validation_lists: Optional dictionary of validation lists by name
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.rules = []
        self.validation_lists = validation_lists or {}
        self.columns = [
            "Enabled",
            "Player",
            "Chest Type",
            "Replace With",
            "Source",
            "Actions",
        ]

        # Track signal connections
        self._rules_updated_connections = []

        # Initialize header items
        self._header_items = {}
        for i, col in enumerate(self.columns):
            self._header_items[i] = MockHeaderItem(col)

        # Add signal callback tracking
        self.signal = MockSignal()

    def columnCount(self):
        """Get the number of columns."""
        return len(self.columns)

    def rowCount(self):
        """Get the number of rows."""
        return len(self.rules)

    def horizontalHeaderItem(self, column):
        """Get the horizontal header item at the given column."""
        return self._header_items.get(column, MockHeaderItem(""))

    def set_rules(self, rules):
        """Set the rules in the table."""
        self.rules = rules
        self.rules_updated.emit(rules)

    def get_rules(self):
        """Get the rules from the table."""
        return self.rules

    def set_all_rules_enabled(self, enabled):
        """Set all rules as enabled or disabled."""
        for rule in self.rules:
            rule["enabled"] = enabled
        self.rules_updated.emit(self.rules)


class MockHeaderItem:
    """Mock header item for testing."""

    def __init__(self, text):
        self._text = text

    def text(self):
        """Get the text of the header item."""
        return self._text


class MockSignal:
    """Mock signal for testing."""

    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        """Connect a callback to the signal."""
        self.callbacks.append(callback)

    def emit(self, *args, **kwargs):
        """Emit the signal."""
        for callback in self.callbacks:
            callback(*args, **kwargs)
