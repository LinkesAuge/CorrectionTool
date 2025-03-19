"""
i_config_manager.py

Description: Interface for configuration management
Usage:
    from src.interfaces.i_config_manager import IConfigManager
    config_manager = service_factory.get_service(IConfigManager)
    value = config_manager.get_value('section', 'key', 'default_value')
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IConfigManager(ABC):
    """
    Interface for the configuration manager.

    This interface defines methods for managing application configuration.
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get all values in a configuration section.

        Args:
            section: Configuration section

        Returns:
            Dict[str, Any]: Dictionary of key-value pairs
        """
        pass

    @abstractmethod
    def save_config(self) -> bool:
        """
        Save the configuration to file.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def load_config(self) -> bool:
        """
        Load the configuration from file.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
