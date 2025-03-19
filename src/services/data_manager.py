"""
data_manager.py

Description: Central data manager for sharing data between components
Usage:
    from src.services.data_manager import DataManager
    data_manager = DataManager.get_instance()
    rules = data_manager.get_correction_rules()
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

from PySide6.QtCore import QObject, Signal

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.models.validation_list import ValidationList
from src.services.config_manager import ConfigManager
from src.services.file_parser import FileParser


class DataManager(QObject):
    """
    Singleton class for managing application data centrally.

    This class provides a central point for storing and accessing shared data
    like correction rules, validation lists, and entries. It emits signals
    when data changes to keep all components in sync.

    Attributes:
        _instance: Singleton instance
        _correction_rules: List of correction rules
        _validation_lists: Dictionary of validation lists
        _entries: List of chest entries
    """

    # Singleton instance
    _instance = None

    # Signals
    correction_rules_changed = Signal(list)  # List[CorrectionRule]
    validation_lists_changed = Signal(dict)  # Dict[str, ValidationList]
    entries_changed = Signal(list)  # List[ChestEntry]

    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance.

        Returns:
            DataManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = DataManager()
        return cls._instance

    def __init__(self):
        """
        Initialize the data manager.

        Note: This should not be called directly. Use get_instance() instead.
        """
        super().__init__()

        # Initialize data
        self._correction_rules: List[CorrectionRule] = []
        self._validation_lists: Dict[str, ValidationList] = {}
        self._entries: List[ChestEntry] = []
        self._correction_file_path: Optional[Path] = None

        # Signal loop prevention
        self._processing_signal = False

        # Get config manager
        self._config = ConfigManager()

        # Setup logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("DataManager initialized")

    def set_correction_rules(self, rules: List[CorrectionRule], file_path: Optional[str] = None):
        """
        Set the correction rules and notify all components.

        Args:
            rules: List of correction rules
            file_path: Path to the file from which rules were loaded (optional)
        """
        # Prevent signal loops
        if self._processing_signal:
            self._logger.warning("Signal loop detected in set_correction_rules, skipping")
            return

        # If rules are the same, don't process
        if self._correction_rules == rules:
            self._logger.debug("Rules are unchanged, skipping")
            return

        self._logger.info(f"Setting {len(rules)} correction rules in DataManager")

        try:
            self._processing_signal = True

            # Store the rules
            self._correction_rules = rules.copy()

            # Store the file path if provided
            if file_path:
                self._correction_file_path = Path(file_path)

                # Update config using the new consolidated path structure
                file_path_str = str(file_path)
                folder_path = str(Path(file_path_str).parent)

                # Use the new path API for saving configs
                self._config.set_path("correction_rules_file", file_path_str)
                self._config.set_path("last_folder", folder_path)
                self._config.set_path("corrections_dir", folder_path)

            # Emit signal to notify components
            self._logger.info(f"Emitting correction_rules_changed signal with {len(rules)} rules")
            self.correction_rules_changed.emit(self._correction_rules)
        finally:
            self._processing_signal = False

    def get_correction_rules(self) -> List[CorrectionRule]:
        """
        Get the correction rules.

        Returns:
            List of correction rules
        """
        return self._correction_rules

    def set_validation_lists(self, lists: Dict[str, ValidationList]):
        """
        Set the validation lists and notify all components.

        Args:
            lists: Dictionary of validation lists
        """
        # Prevent signal loops
        if self._processing_signal:
            self._logger.warning("Signal loop detected in set_validation_lists, skipping")
            return

        # If lists are the same, don't process
        if self._validation_lists == lists:
            self._logger.debug("Validation lists are unchanged, skipping")
            return

        self._logger.info(f"Setting {len(lists)} validation lists in DataManager")

        try:
            self._processing_signal = True

            # Store the lists
            self._validation_lists = lists.copy()

            # Save list paths to config
            for list_type, validation_list in lists.items():
                if hasattr(validation_list, "file_path") and validation_list.file_path:
                    file_path_str = str(validation_list.file_path)
                    self._config.set("General", f"{list_type}_list_path", file_path_str)

                    # Also save in other config locations for consistency
                    if list_type == "player":
                        self._config.set("Validation", "player_list", file_path_str)
                    elif list_type == "chest_type":
                        self._config.set("Validation", "chest_type_list", file_path_str)
                    elif list_type == "source":
                        self._config.set("Validation", "source_list", file_path_str)

            # Save config changes
            self._config.save()

            # Emit signal to notify components
            self._logger.info(f"Emitting validation_lists_changed signal with {len(lists)} lists")
            self.validation_lists_changed.emit(self._validation_lists)
        finally:
            self._processing_signal = False

    def get_validation_lists(self) -> Dict[str, ValidationList]:
        """
        Get the validation lists.

        Returns:
            Dictionary of validation lists
        """
        return self._validation_lists

    def set_entries(self, entries: List[ChestEntry]):
        """
        Set the entries and notify all components.

        Args:
            entries: List of chest entries
        """
        # Prevent signal loops
        if self._processing_signal:
            self._logger.warning("Signal loop detected in set_entries, skipping")
            return

        # If entries are the same, don't process
        if self._entries == entries:
            self._logger.debug("Entries are unchanged, skipping")
            return

        self._logger.info(f"Setting {len(entries)} entries in DataManager")

        try:
            self._processing_signal = True

            # Store the entries
            self._entries = entries.copy()

            # Emit signal to notify components
            self._logger.info(f"Emitting entries_changed signal with {len(entries)} entries")
            self.entries_changed.emit(self._entries)
        finally:
            self._processing_signal = False

    def get_entries(self) -> List[ChestEntry]:
        """
        Get the entries.

        Returns:
            List of chest entries
        """
        return self._entries

    def get_correction_file_path(self) -> Optional[Path]:
        """
        Get the path to the last loaded correction file.

        Returns:
            Path to the last loaded correction file, or None if no file was loaded
        """
        return self._correction_file_path

    def load_saved_correction_rules(self) -> List[CorrectionRule]:
        """
        Load correction rules from the default path in the config.

        Returns:
            List of loaded correction rules, or empty list if loading failed
        """
        import traceback

        self._logger.info("DataManager: Loading saved correction rules")

        # Use the new consolidated path structure
        rule_file = self._config.get_path("correction_rules_file")

        if not rule_file:
            self._logger.warning("No correction rules file found in config")
            return []

        self._logger.info(f"Attempting to load correction rules from: {rule_file}")
        rule_path = Path(rule_file)

        if not rule_path.exists():
            self._logger.warning(f"Correction rules file not found: {rule_path}")
            return []

        try:
            # Parse the correction file using FileParser
            parser = FileParser()
            rules = parser.parse_correction_file(rule_path)

            if not rules:
                self._logger.warning(f"No rules loaded from file: {rule_path}")
                return []

            self._logger.info(f"Successfully loaded {len(rules)} correction rules from {rule_path}")

            # Store the file path
            self._correction_file_path = rule_path

            # Store the rules and return them (but don't emit signal yet)
            self._correction_rules = rules

            # Update the config to make this the default path in all locations
            self._config.set_path("correction_rules_file", str(rule_path))

            return rules

        except Exception as e:
            self._logger.error(f"Error loading correction rules from {rule_path}: {str(e)}")
            self._logger.error(traceback.format_exc())
            return []

    def _update_correction_file_path(self, file_path: str):
        """
        Update all correction file path references in the config.

        Args:
            file_path: Path to the correction file
        """
        # Use the new consolidated path structure
        self._config.set_path("correction_rules_file", file_path)

        # Also update the folder path
        folder_path = str(Path(file_path).parent)
        self._config.set_path("last_folder", folder_path)
        self._config.set_path("corrections_dir", folder_path)

    def _load_saved_validation_lists(self):
        """
        Load validation lists from paths saved in config.

        Loads player, chest type, and source validation lists from the paths
        configured in the ConfigManager.
        """
        self._logger.info("DataManager: Loading saved validation lists")

        # Get configured paths
        player_path = self._config.get_path("player_list_file", fallback=None)
        if player_path and Path(player_path).exists():
            self._logger.info(f"Loading player list from: {player_path}")
            try:
                player_list = ValidationList.load_from_file(player_path, "player")
                self._validation_lists["player"] = player_list
                self._logger.info(
                    f"Loaded player list with {len(player_list.get_entries())} entries"
                )
            except Exception as e:
                self._logger.warning(f"Error loading player list: {str(e)}")

        chest_path = self._config.get_path("chest_type_list_file", fallback=None)
        if chest_path and Path(chest_path).exists():
            self._logger.info(f"Loading chest type list from: {chest_path}")
            try:
                chest_list = ValidationList.load_from_file(chest_path, "chest_type")
                self._validation_lists["chest_type"] = chest_list
                self._logger.info(
                    f"Loaded chest type list with {len(chest_list.get_entries())} entries"
                )
            except Exception as e:
                self._logger.warning(f"Error loading chest type list: {str(e)}")

        source_path = self._config.get_path("source_list_file", fallback=None)
        if source_path and Path(source_path).exists():
            self._logger.info(f"Loading source list from: {source_path}")
            try:
                source_list = ValidationList.load_from_file(source_path, "source")
                self._validation_lists["source"] = source_list
                self._logger.info(
                    f"Loaded source list with {len(source_list.get_entries())} entries"
                )
            except Exception as e:
                self._logger.warning(f"Error loading source list: {str(e)}")

        # Emit signal with updated validation lists
        self._logger.info(
            f"Emitting validation_lists_changed signal with {len(self._validation_lists)} lists"
        )
        self.validation_lists_changed.emit(self._validation_lists)

        return len(self._validation_lists) > 0

    def _load_default_validation_lists(self):
        """
        Load default validation lists from the default paths.
        """
        self._logger.info("DataManager: Loading default validation lists")

        # Player list
        player_file = "data/validation/players.txt"
        if Path(player_file).exists():
            self._logger.info(f"Loading player list from: {player_file}")
            try:
                player_list = ValidationList.load_from_file(player_file, "player")
                self._validation_lists["player"] = player_list
                self._logger.info(
                    f"Loaded player list with {len(player_list.get_entries())} entries"
                )
            except Exception as e:
                self._logger.warning(f"Error loading player list: {str(e)}")

        # Chest type list
        chest_file = "data/validation/chest_types.txt"
        if Path(chest_file).exists():
            self._logger.info(f"Loading chest type list from: {chest_file}")
            try:
                chest_list = ValidationList.load_from_file(chest_file, "chest_type")
                self._validation_lists["chest_type"] = chest_list
                self._logger.info(
                    f"Loaded chest type list with {len(chest_list.get_entries())} entries"
                )
            except Exception as e:
                self._logger.warning(f"Error loading chest type list: {str(e)}")

        # Source list
        source_file = "data/validation/sources.txt"
        if Path(source_file).exists():
            self._logger.info(f"Loading source list from: {source_file}")
            try:
                source_list = ValidationList.load_from_file(source_file, "source")
                self._validation_lists["source"] = source_list
                self._logger.info(
                    f"Loaded source list with {len(source_list.get_entries())} entries"
                )
            except Exception as e:
                self._logger.warning(f"Error loading source list: {str(e)}")

        # Emit signal with updated validation lists
        self._logger.info(
            f"Emitting validation_lists_changed signal with {len(self._validation_lists)} lists"
        )
        self.validation_lists_changed.emit(self._validation_lists)

        return len(self._validation_lists) > 0
