"""
config_manager.py

Description: Configuration management for the Chest Tracker Correction Tool
Usage:
    from src.services.config_manager import ConfigManager
    config = ConfigManager()
    value = config.get("Section", "key")
"""

import configparser
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ConfigManager:
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

    def __init__(self, config_file: Optional[Path] = None) -> None:
        """
        Initialize the ConfigManager.

        Args:
            config_file (Optional[Path]): Path to the configuration file
        """
        if self._initialized:
            return

        self._config = configparser.ConfigParser()
        self._config_file = config_file or self._DEFAULT_CONFIG_FILE

        # Load configuration
        if self._config_file.exists():
            self._config.read(self._config_file)
        else:
            self._create_default_config()

        self._initialized = True

    def _create_default_config(self) -> None:
        """
        Create a default configuration file.
        """
        # General section
        self._config["General"] = {
            "app_name": "Chest Tracker Correction Tool",
            "version": "0.1.0",
            "default_theme": "dark",
        }

        # UI section
        self._config["UI"] = {
            "theme_color": "blueish-purple",
            "accent_color": "gold",
            "font_size": "10",
            "window_width": "1280",
            "window_height": "800",
            "left_panel_ratio": "0.5",
        }

        # Files section
        self._config["Files"] = {
            "default_input_dir": "",
            "default_output_dir": "",
            "default_correction_list": "",
            "default_validation_dir": "",
        }

        # Correction section
        self._config["Correction"] = {
            "fuzzy_match_threshold": "0.85",
            "validation_enabled": "true",
            "auto_save_corrections": "true",
            "preview_mode_enabled": "true",
        }

        # Validation section
        self._config["Validation"] = {
            "highlight_errors": "true",
            "validation_player_list": "",
            "validation_chest_list": "",
            "validation_source_list": "",
        }

        # Logging section
        self._config["Logging"] = {"log_level": "INFO", "log_file": "app.log"}

        # Save the configuration
        self.save()

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
        return self._config.get(section, key, fallback=fallback)

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
        return self._config.getint(section, key, fallback=fallback)

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
        return self._config.getfloat(section, key, fallback=fallback)

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """
        Get a boolean configuration value.

        Args:
            section (str): The configuration section
            key (str): The configuration key
            fallback (bool, optional): Default value if key doesn't exist

        Returns:
            bool: The configuration value as a boolean
        """
        return self._config.getboolean(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            section (str): The configuration section
            key (str): The configuration key
            value (Any): The value to set
        """
        if not self._config.has_section(section):
            self._config.add_section(section)

        self._config.set(section, key, str(value))

    def save(self) -> None:
        """
        Save the configuration to file.
        """
        with open(self._config_file, "w") as f:
            self._config.write(f)

    def reset_to_defaults(self) -> None:
        """Reset the configuration to default values."""
        # Create a new config parser
        self._config = configparser.ConfigParser()

        # Create default configuration
        self._create_default_config()

        # Save the default configuration
        self.save()

    def get_all(self) -> Dict[str, Dict[str, str]]:
        """
        Get all configuration values.

        Returns:
            Dict[str, Dict[str, str]]: Dictionary of all configuration values
        """
        result = {}
        for section in self._config.sections():
            result[section] = {}
            for key, value in self._config[section].items():
                result[section][key] = value
        return result
