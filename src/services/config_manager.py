"""
config_manager.py

Description: Configuration management for the Chest Tracker Correction Tool
Usage:
    from src.services.config_manager import ConfigManager
    config = ConfigManager()
    value = config.get("Section", "key")
"""

import configparser
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from functools import lru_cache
import json

from src.interfaces.i_config_manager import IConfigManager


class ConfigManager(IConfigManager):
    """
    Manages application configuration settings.

    Handles loading, saving, and accessing configuration values from config.ini.

    Attributes:
        _config (configparser.ConfigParser): The config parser instance
        _config_file (Path): Path to the configuration file

    Implementation Notes:
        - Uses ConfigParser to handle INI file format
        - Provides default values for missing settings
        - Supports saving configuration changes
    """

    _instance = None
    _DEFAULT_CONFIG_FILE = Path("config.ini")

    def __new__(cls, config_file: Optional[Path] = None) -> "ConfigManager":
        """
        Create or return the singleton instance of ConfigManager.

        Args:
            config_file (Optional[Path]): Path to the configuration file

        Returns:
            ConfigManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path=None):
        """
        Initialize the ConfigManager.

        Args:
            config_path (str, optional): Path to the config file. Defaults to None.
        """
        # Check if already initialized to prevent multiple initialization
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True

        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing ConfigManager")

        # Initialize the app root path
        self.app_root = Path(
            os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        )

        if config_path is None:
            # Use application root directory
            self.config_path = self.app_root / "config.ini"
        else:
            self.config_path = Path(config_path)

        self.logger.info(f"Using config path: {self.config_path}")

        # Create config directory if it doesn't exist
        config_dir = self.config_path.parent
        if not config_dir.exists():
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created config directory: {config_dir}")
            except Exception as e:
                self.logger.error(f"Error creating config directory: {e}")

        # Initialize the config parser
        self.config = configparser.ConfigParser()

        # Load existing config or create default
        if self.config_path.exists():
            self.load_config(str(self.config_path))
            # Check if we need to update from old format to new format
            if not self.config.has_section("Paths"):
                self.logger.info("Converting old config format to new consolidated format")
                self._create_default_config()
                self.save_config()
        else:
            self._create_default_config()
            self.save_config()
            self._create_default_directories()

        self.logger.info("ConfigManager initialized successfully")

    def _create_default_config(self) -> None:
        """
        Create a default configuration file with a consolidated structure.
        """
        logger = logging.getLogger(__name__)
        logger.info("Creating default configuration with consolidated structure")

        # General section
        self.config["General"] = {
            "app_name": "Chest Tracker Correction Tool",
            "version": "0.1.0",
            "default_theme": "dark",
            "auto_save_settings": "true",
            "remember_window_size": "true",
            "first_run": "true",
        }

        # UI section
        self.config["UI"] = {
            "theme": "dark",
            "font_size": "12",
            "row_height": "30",
            "show_grid": "true",
            "window_width": "1280",
            "window_height": "800",
            "window_pos_x": "0",
            "window_pos_y": "0",
        }

        # Consolidated Paths section - all file paths go here
        # Using relative paths to application root
        self.config["Paths"] = {
            # Standard directories
            "data_dir": "data",
            "input_dir": "data/input",
            "output_dir": "data/output",
            "corrections_dir": "data/corrections",
            "validation_dir": "data/validation",
            # Default files
            "correction_rules_file": "data/corrections/standard_corrections.csv",
            "player_list_file": "data/validation/players.txt",
            "chest_type_list_file": "data/validation/chest_types.txt",
            "source_list_file": "data/validation/sources.txt",
        }

        # LastUsed section for user-specific paths
        self.config["LastUsed"] = {
            "last_input_file": "",
            "last_output_file": "",
            "last_correction_file": "",
            "last_folder": "",
            "last_entry_directory": "",
            "last_correction_directory": "",
        }

        # Validation section
        self.config["Validation"] = {
            "enabled": "true",
            "strictness": "normal",
            "highlight_errors": "true",
        }

        # Correction section
        self.config["Correction"] = {
            "fuzzy_matching_enabled": "true",
            "fuzzy_match_threshold": "0.85",
            "auto_apply_corrections": "true",
        }

        # Files section
        self.config["Files"] = {
            "default_input_extension": "txt",
            "default_correction_extension": "csv",
        }

        # Logging section
        self.config["Logging"] = {
            "log_level": "INFO",
            "log_file": "correction_tool.log",
            "max_log_size": "10485760",  # 10MB
            "backup_count": "5",
        }

    def _create_default_directories(self) -> None:
        """
        Create the default directory structure for the application.
        """
        try:
            # Get directory paths from config
            directories = [
                self.get_absolute_path(self.config["Paths"]["data_dir"]),
                self.get_absolute_path(self.config["Paths"]["input_dir"]),
                self.get_absolute_path(self.config["Paths"]["output_dir"]),
                self.get_absolute_path(self.config["Paths"]["corrections_dir"]),
                self.get_absolute_path(self.config["Paths"]["validation_dir"]),
            ]

            # Create each directory
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created directory: {directory}")

            # Create empty default files
            for file_key in [
                "correction_rules_file",
                "player_list_file",
                "chest_type_list_file",
                "source_list_file",
            ]:
                file_path = self.get_absolute_path(self.config["Paths"][file_key])
                if not file_path.exists():
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, "w") as f:
                        if file_key == "correction_rules_file":
                            f.write("From;To\n")  # CSV header
                    self.logger.info(f"Created empty file: {file_path}")

        except Exception as e:
            self.logger.error(f"Error creating default directories: {e}")

    @classmethod
    def create_default_config(cls) -> None:
        """
        Create a default configuration file.

        Class method to create a default configuration without instantiating the class.
        """
        instance = cls()
        instance._create_default_config()

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            section (str): The configuration section
            key (str): The configuration key
            fallback (Any, optional): Default value if key doesn't exist

        Returns:
            Any: The configuration value
        """
        return self.config.get(section, key, fallback=fallback)

    def get_str(self, section: str, key: str, fallback: str = "") -> str:
        """
        Get a string value from the configuration.

        Args:
            section: Configuration section
            key: Configuration key
            fallback: Default value if the key is not found

        Returns:
            String value from the configuration or fallback
        """
        return self.config.get(section, key, fallback=fallback)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """
        Get an integer configuration value.

        Args:
            section (str): The configuration section
            key (str): The configuration key
            fallback (int, optional): Default value if key doesn't exist

        Returns:
            int: The configuration value as an integer
        """
        try:
            return int(self.config.get(section, key, fallback=str(fallback)))
        except ValueError:
            return fallback

    def get_boolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """
        Get a boolean configuration value.

        Args:
            section (str): The configuration section
            key (str): The configuration key
            fallback (bool, optional): Default value if key doesn't exist

        Returns:
            bool: The configuration value as a boolean
        """
        value = self.config.get(section, key, fallback=str(fallback))
        return value.lower() in ["true", "1", "yes", "y", "t"]

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """
        Alias for get_boolean.

        Args:
            section (str): The configuration section
            key (str): The configuration key
            fallback (bool, optional): Default value if key doesn't exist

        Returns:
            bool: The configuration value as a boolean
        """
        return self.get_boolean(section, key, fallback)

    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """
        Get a float configuration value.

        Args:
            section (str): The configuration section
            key (str): The configuration key
            fallback (float, optional): Default value if key doesn't exist

        Returns:
            float: The configuration value as a float
        """
        try:
            return float(self.config.get(section, key, fallback=str(fallback)))
        except ValueError:
            return fallback

    def get_path(self, path_key: str, fallback: Optional[Union[str, Path]] = None) -> Path:
        """
        Get a path from the Paths section.

        Args:
            path_key (str): The configuration key in the Paths section
            fallback (Optional[Union[str, Path]], optional): Default path if key doesn't exist

        Returns:
            Path: The path as a Path object
        """
        path_str = self.config.get("Paths", path_key, fallback=str(fallback) if fallback else "")
        if not path_str:
            return Path(str(fallback)) if fallback else Path()
        return Path(path_str)

    def get_absolute_path(self, path_value: Union[str, Path]) -> Path:
        """
        Convert a possibly relative path to an absolute path.

        If the path is already absolute, it is returned as is.
        If the path is relative, it is resolved relative to the app root.

        Args:
            path_value (Union[str, Path]): The path to convert

        Returns:
            Path: The absolute path
        """
        path = Path(path_value)
        if path.is_absolute():
            return path
        return self.app_root / path

    def get_last_used_path(self, key: str, fallback: Optional[Union[str, Path]] = None) -> Path:
        """
        Get a path from the LastUsed section.

        Args:
            key (str): The configuration key in the LastUsed section
            fallback (Optional[Union[str, Path]], optional): Default path if key doesn't exist

        Returns:
            Path: The path as a Path object
        """
        path_str = self.config.get("LastUsed", key, fallback=str(fallback) if fallback else "")
        if not path_str:
            return Path(str(fallback)) if fallback else Path()
        return Path(path_str)

    def set_path(self, path_key: str, value: Union[str, Path]) -> None:
        """
        Set a path in the Paths section.

        Args:
            path_key (str): The configuration key in the Paths section
            value (Union[str, Path]): The path to set
        """
        self.set_value("Paths", path_key, str(value))

    def set_last_used_path(self, key: str, value: Union[str, Path]) -> None:
        """
        Set a path in the LastUsed section.

        Args:
            key (str): The configuration key in the LastUsed section
            value (Union[str, Path]): The path to set
        """
        self.set_value("LastUsed", key, str(value))

    def set(self, section: str, key: str, value: str) -> None:
        """
        Set a configuration value.

        Args:
            section (str): The configuration section
            key (str): The configuration key
            value (str): The value to set
        """
        # Create the section if it doesn't exist
        if not self.config.has_section(section):
            self.config.add_section(section)

        # Set the value
        self.config.set(section, key, value)

        # Save the configuration
        self.save_config()

    def set_value(self, section: str, key: str, value: Any) -> None:
        """
        Set a value in the configuration.

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        self.set(section, key, str(value))

    def remove_option(self, section: str, key: str) -> bool:
        """
        Remove a configuration option.

        Args:
            section (str): The configuration section
            key (str): The configuration key

        Returns:
            bool: True if the option was removed, False otherwise
        """
        result = self.config.remove_option(section, key)
        self.save_config()
        return result

    def remove_section(self, section: str) -> bool:
        """
        Remove a configuration section.

        Args:
            section (str): The configuration section

        Returns:
            bool: True if the section was removed, False otherwise
        """
        result = self.config.remove_section(section)
        self.save_config()
        return result

    def get_sections(self) -> list:
        """
        Get all configuration sections.

        Returns:
            list: List of section names
        """
        return self.config.sections()

    def get_options(self, section: str) -> list:
        """
        Get all options in a section.

        Args:
            section (str): The configuration section

        Returns:
            list: List of option names
        """
        if not self.config.has_section(section):
            return []
        return self.config.options(section)

    def has_section(self, section: str) -> bool:
        """
        Check if a section exists in the configuration.

        Args:
            section: Configuration section

        Returns:
            True if the section exists, False otherwise
        """
        return self.config.has_section(section)

    def has_option(self, section: str, key: str) -> bool:
        """
        Check if a key exists in a section.

        Args:
            section: Configuration section
            key: Configuration key

        Returns:
            True if the key exists in the section, False otherwise
        """
        return self.config.has_option(section, key)

    def load_config(self, config_file: str) -> bool:
        """
        Load configuration from a file.

        Args:
            config_file: Path to the configuration file

        Returns:
            True if the configuration was loaded successfully, False otherwise
        """
        try:
            self.config.read(config_file)
            return True
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            # Create default configuration if loading fails
            self._create_default_config()
            self.save_config()
            return False

    def save_config(self, config_file: Optional[str] = None) -> bool:
        """
        Save the configuration to a file.

        Args:
            config_file (Optional[str]): Path to the configuration file

        Returns:
            bool: True on success, False on failure
        """
        try:
            if config_file:
                file_path = Path(config_file)
            else:
                file_path = self.config_path

            with open(file_path, "w") as configfile:
                self.config.write(configfile)
            self.logger.info(f"Configuration saved to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            return False

    def save(self, config_file: Optional[str] = None) -> bool:
        """
        Alias for save_config method for backward compatibility.

        Args:
            config_file (Optional[str]): Path to the configuration file

        Returns:
            bool: True on success, False on failure
        """
        return self.save_config(config_file)

    def reset_to_defaults(self) -> None:
        """Reset the configuration to default values."""
        self._create_default_config()
        self.save_config()
        self._create_default_directories()

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
        try:
            if not self.config.has_section(section):
                self.logger.warning(f"Section {section} not found in config")
                return default

            if not self.config.has_option(section, key):
                self.logger.warning(f"Key {key} not found in section {section}")
                return default

            value = self.config.get(section, key)
            return value
        except Exception as e:
            self.logger.error(f"Error getting config value: {e}")
            return default

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get all values in a configuration section.

        Args:
            section: Configuration section

        Returns:
            Dict[str, Any]: Dictionary of key-value pairs
        """
        try:
            if not self.config.has_section(section):
                self.logger.warning(f"Section {section} not found in config")
                return {}

            return dict(self.config[section])
        except Exception as e:
            self.logger.error(f"Error getting config section: {e}")
            return {}
