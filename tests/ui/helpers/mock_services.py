"""
mock_services.py

Description: Mock implementations of interfaces for UI testing
Usage:
    from tests.ui.helpers.mock_services import MockDataStore, MockConfigManager

    mock_data_store = MockDataStore()
    mock_config = MockConfigManager()
"""

from typing import Dict, List, Any, Optional, Set, Type, Union, Callable
import pandas as pd
from pathlib import Path

from src.interfaces.data_store import IDataStore
from src.interfaces.config_manager import IConfigManager
from src.interfaces.file_service import IFileService
from src.interfaces.correction_service import ICorrectionService
from src.interfaces.validation_service import IValidationService
from src.interfaces.service_factory import IServiceFactory
from src.interfaces.events import EventType, EventData, IEventCallback


class MockDataStore(IDataStore):
    """
    Mock implementation of IDataStore for testing.

    Attributes:
        data: Dictionary storing test data
        validation_lists: Dictionary storing test validation lists
        event_handlers: Dictionary of registered event handlers

    Implementation Notes:
        - Simulates data storage without actual persistence
        - Records events for verification during testing
        - Provides access to internal state for test assertions
    """

    def __init__(self):
        """Initialize the MockDataStore with empty data structures."""
        self.data = {}
        self.validation_lists = {}
        self.event_handlers = {event_type: [] for event_type in EventType}
        self.events_triggered = []

    def set_data(self, data: pd.DataFrame) -> None:
        """
        Set the internal data.

        Args:
            data: DataFrame to store
        """
        self.data = data.copy()
        self._trigger_event(EventType.ENTRIES_UPDATED, {"data": self.data})

    def get_data(self) -> pd.DataFrame:
        """
        Get the stored data.

        Returns:
            pd.DataFrame: The stored data or empty DataFrame if none
        """
        if isinstance(self.data, pd.DataFrame):
            return self.data.copy()
        return pd.DataFrame()

    def add_validation_list(self, list_name: str, items: List[str]) -> None:
        """
        Add a validation list.

        Args:
            list_name: Name of the validation list
            items: List of items to store
        """
        self.validation_lists[list_name] = items
        self._trigger_event(
            EventType.VALIDATION_LIST_UPDATED, {"list_name": list_name, "items": items}
        )

    def get_validation_list(self, list_name: str) -> Any:
        """
        Get a validation list by name.

        Args:
            list_name: Name of the validation list

        Returns:
            Any: The validation list or empty list if not found
        """
        return self.validation_lists.get(list_name, [])

    def update_validation_list(self, list_name: str, items: Any) -> bool:
        """
        Update a validation list.

        Args:
            list_name: Name of the validation list
            items: New items for the list

        Returns:
            bool: True if successful
        """
        self.validation_lists[list_name] = items
        self._trigger_event(
            EventType.VALIDATION_LIST_UPDATED, {"list_name": list_name, "items": items}
        )
        return True

    def register_handler(self, event_type: EventType, callback: IEventCallback) -> None:
        """
        Register an event handler.

        Args:
            event_type: Type of event to handle
            callback: Callback function to execute when event occurs
        """
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(callback)

    def unregister_handler(self, event_type: EventType, callback: IEventCallback) -> None:
        """
        Unregister an event handler.

        Args:
            event_type: Type of event to unregister from
            callback: Callback function to remove
        """
        if event_type in self.event_handlers and callback in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(callback)

    def clear_handlers(self) -> None:
        """Clear all event handlers."""
        self.event_handlers = {event_type: [] for event_type in EventType}

    def _trigger_event(self, event_type: EventType, data: dict) -> None:
        """
        Trigger an event.

        Args:
            event_type: Type of event to trigger
            data: Event data to pass to handlers
        """
        event_data = EventData(event_type, data)
        self.events_triggered.append((event_type, data))

        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                handler(event_data)

    def get_triggered_events(self) -> List[tuple]:
        """
        Get the list of triggered events.

        Returns:
            List[tuple]: List of (event_type, data) tuples
        """
        return self.events_triggered.copy()

    def clear_triggered_events(self) -> None:
        """Clear the list of triggered events."""
        self.events_triggered = []

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self.data = {}
        self.validation_lists = {}
        self.events_triggered = []


class MockConfigManager(IConfigManager):
    """
    Mock implementation of IConfigManager for testing.

    Attributes:
        config: Dictionary storing test configuration values
        accessed_keys: Set of keys that have been accessed
        modified_keys: Set of keys that have been modified

    Implementation Notes:
        - Simulates configuration storage without actual file persistence
        - Records accessed and modified keys for verification during testing
        - Provides methods to inspect and reset state
    """

    def __init__(self):
        """Initialize the MockConfigManager with empty configuration."""
        self.config = {}
        self.accessed_keys = set()
        self.modified_keys = set()

        # Set some default configuration values
        self._set_defaults()

    def _set_defaults(self) -> None:
        """Set default configuration values."""
        self.config = {
            "Application": {"theme": "dark", "language": "en"},
            "Paths": {
                "data_dir": "data",
                "input_dir": "input",
                "output_dir": "output",
                "last_used_input": "",
                "last_used_output": "",
            },
            "ValidationLists": {
                "players_list": "data/players.csv",
                "chest_types_list": "data/chest_types.csv",
                "sources_list": "data/sources.csv",
            },
            "CorrectionRules": {"rules_file": "data/correction_rules.csv", "enabled": True},
            "UI": {
                "font_size": 10,
                "show_tooltips": True,
                "window_width": 1200,
                "window_height": 800,
            },
        }

    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found

        Returns:
            Any: Configuration value or default
        """
        self.accessed_keys.add((section, key))

        if section in self.config and key in self.config[section]:
            return self.config[section][key]

        return default

    def set_value(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        self.modified_keys.add((section, key))

        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value

    def get_path(self, path_type: str, default: Optional[str] = None) -> str:
        """
        Get a path from configuration.

        Args:
            path_type: Type of path to retrieve
            default: Default path if not found

        Returns:
            str: Path string or default
        """
        self.accessed_keys.add(("Paths", path_type))

        if "Paths" in self.config and path_type in self.config["Paths"]:
            return self.config["Paths"][path_type]

        return default or ""

    def set_path(self, path_type: str, path: str) -> None:
        """
        Set a path in configuration.

        Args:
            path_type: Type of path to set
            path: Path string to store
        """
        self.modified_keys.add(("Paths", path_type))

        if "Paths" not in self.config:
            self.config["Paths"] = {}

        self.config["Paths"][path_type] = path

    def save(self) -> bool:
        """
        Simulate saving configuration.

        Returns:
            bool: Always True for mock
        """
        return True

    def get_accessed_keys(self) -> Set[tuple]:
        """
        Get set of accessed keys.

        Returns:
            Set[tuple]: Set of (section, key) tuples
        """
        return self.accessed_keys.copy()

    def get_modified_keys(self) -> Set[tuple]:
        """
        Get set of modified keys.

        Returns:
            Set[tuple]: Set of (section, key) tuples
        """
        return self.modified_keys.copy()

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self._set_defaults()
        self.accessed_keys = set()
        self.modified_keys = set()


class MockFileService(IFileService):
    """
    Mock implementation of IFileService for testing.

    Attributes:
        files: Dictionary of mock file content
        imported_files: List of imported file paths
        exported_files: List of exported file paths

    Implementation Notes:
        - Simulates file operations without actual file system access
        - Records imported and exported files for verification during testing
        - Provides methods to preset file content and inspect operations
    """

    def __init__(self):
        """Initialize the MockFileService with empty files."""
        self.files = {}
        self.imported_files = []
        self.exported_files = []

    def import_csv(self, file_path: str) -> pd.DataFrame:
        """
        Import a CSV file.

        Args:
            file_path: Path to the file

        Returns:
            pd.DataFrame: DataFrame with file content or empty DataFrame
        """
        self.imported_files.append(file_path)

        if file_path in self.files:
            return self.files[file_path].copy()

        # Return a default empty DataFrame
        return pd.DataFrame()

    def export_csv(self, data: pd.DataFrame, file_path: str) -> bool:
        """
        Export a DataFrame to CSV.

        Args:
            data: DataFrame to export
            file_path: Path to save the file

        Returns:
            bool: Always True for mock
        """
        self.exported_files.append(file_path)
        self.files[file_path] = data.copy()
        return True

    def import_validation_list(self, file_path: str) -> List[str]:
        """
        Import a validation list.

        Args:
            file_path: Path to the file

        Returns:
            List[str]: List of items from the file or empty list
        """
        self.imported_files.append(file_path)

        if file_path in self.files:
            content = self.files[file_path]
            if isinstance(content, pd.DataFrame):
                return content.iloc[:, 0].tolist()
            if isinstance(content, list):
                return content.copy()

        return []

    def export_validation_list(self, items: List[str], file_path: str) -> bool:
        """
        Export a validation list.

        Args:
            items: List of items to export
            file_path: Path to save the file

        Returns:
            bool: Always True for mock
        """
        self.exported_files.append(file_path)
        self.files[file_path] = items.copy()
        return True

    def set_mock_file(self, file_path: str, content: Union[pd.DataFrame, List[str]]) -> None:
        """
        Set content for a mock file.

        Args:
            file_path: Path of the mock file
            content: Content to return when the file is imported
        """
        self.files[file_path] = content

    def get_imported_files(self) -> List[str]:
        """
        Get list of imported files.

        Returns:
            List[str]: List of imported file paths
        """
        return self.imported_files.copy()

    def get_exported_files(self) -> List[str]:
        """
        Get list of exported files.

        Returns:
            List[str]: List of exported file paths
        """
        return self.exported_files.copy()

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self.files = {}
        self.imported_files = []
        self.exported_files = []


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

    def apply_corrections(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Apply correction rules to data.

        Args:
            data: DataFrame to apply corrections to

        Returns:
            pd.DataFrame: DataFrame with corrections applied
        """
        if not self.correction_enabled or not self.correction_rules:
            return data.copy()

        # Create a copy to simulate corrections
        result = data.copy()

        # Record that corrections were applied
        self.applied_corrections.append(
            {"data_shape": data.shape, "rules_count": len(self.correction_rules)}
        )

        # Apply mock corrections (doesn't actually change the data)
        return result

    def add_correction_rule(
        self, from_value: str, to_value: str, rule_type: str = "default"
    ) -> bool:
        """
        Add a correction rule.

        Args:
            from_value: Value to correct from
            to_value: Value to correct to
            rule_type: Type of correction rule

        Returns:
            bool: Always True for mock
        """
        self.correction_rules.append(
            {"from": from_value, "to": to_value, "type": rule_type, "enabled": True}
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

    def reset(self) -> None:
        """Reset the mock to its initial state."""
        self.correction_rules = []
        self.applied_corrections = []
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
            self.services["correction_service"] = correction_service
        if validation_service:
            self.services["validation_service"] = validation_service
        if data_store:
            self.services["data_store"] = data_store
        if config_manager:
            self.services["config_manager"] = config_manager
        if file_service:
            self.services["file_service"] = file_service

    def get_service(self, service_type: str) -> Any:
        """
        Get a service by type.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Any: The service instance or None
        """
        self.service_creation_history.append(service_type)
        return self.services.get(service_type)

    def register_service(self, service_type: str, service: Any) -> None:
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
            "data_store": MockDataStore(),
            "config_manager": MockConfigManager(),
            "file_service": MockFileService(),
            "correction_service": MockCorrectionService(),
            "validation_service": MockValidationService(),
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
