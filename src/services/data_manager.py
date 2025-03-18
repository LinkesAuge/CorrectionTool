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
        self._logger.info(f"Setting {len(rules)} correction rules in DataManager")

        # Store the rules
        self._correction_rules = rules.copy()

        # Store the file path if provided
        if file_path:
            self._correction_file_path = Path(file_path)

            # Update config
            file_path_str = str(file_path)
            folder_path = str(Path(file_path_str).parent)

            self._config.set("General", "last_correction_file", file_path_str)
            self._config.set("General", "last_folder", folder_path)
            self._config.set("Files", "last_correction_directory", folder_path)
            self._config.set("Correction", "default_correction_rules", file_path_str)
            self._config.save()

        # Emit signal to notify components
        self._logger.info(f"Emitting correction_rules_changed signal with {len(rules)} rules")
        self.correction_rules_changed.emit(self._correction_rules)

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
        self._logger.info(f"Setting {len(lists)} validation lists in DataManager")

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
        self._logger.info(f"Setting {len(entries)} entries in DataManager")

        # Store the entries
        self._entries = entries.copy()

        # Emit signal to notify components
        self._logger.info(f"Emitting entries_changed signal with {len(entries)} entries")
        self.entries_changed.emit(self._entries)

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

        # Get the previously saved correction rules file
        rule_file = self._config.get("Correction", "default_correction_rules", "")

        if not rule_file:
            # Try alternate location
            rule_file = self._config.get("General", "last_correction_file", "")
            if not rule_file:
                self._logger.info("No saved correction rules file found")
                return []

        self._logger.info(f"Loading correction rules from: {rule_file}")
        rule_path = Path(rule_file)

        if not rule_path.exists():
            self._logger.warning(f"Correction rules file not found: {rule_path}")
            return []

        try:
            # Parse the correction file using FileParser
            parser = FileParser()
            rules = parser.parse_correction_file(rule_path)

            if not rules:
                self._logger.warning("No rules loaded from file")
                return []

            self._logger.info(f"Loaded {len(rules)} correction rules")

            # Store the file path
            self._correction_file_path = rule_path

            # Store the rules and return them (but don't emit signal yet)
            self._correction_rules = rules
            return rules

        except Exception as e:
            self._logger.error(f"Error loading correction rules: {str(e)}")
            self._logger.error(traceback.format_exc())
            return []

    def load_saved_validation_lists(self) -> Dict[str, ValidationList]:
        """
        Load validation lists from the default paths in the config.

        Returns:
            Dictionary of loaded validation lists, or empty dict if loading failed
        """
        import traceback

        self._logger.info("DataManager: Loading saved validation lists")

        lists = {}
        try:
            # Load player list
            for key in ["player_list", "player_list_path"]:
                for section in ["Validation", "General"]:
                    player_list_path = self._config.get(section, key, "")
                    if player_list_path:
                        player_path = Path(player_list_path)
                        self._logger.info(f"Loading player list from: {player_path}")

                        if player_path.exists():
                            try:
                                player_list = ValidationList.load_from_file(player_path)
                                if player_list is not None:
                                    lists["player"] = player_list
                                    self._logger.info(
                                        f"Loaded player list with {len(player_list.items)} items"
                                    )
                                    break
                            except Exception as e:
                                self._logger.warning(f"Error loading player list: {str(e)}")
                                # Try alternate loading approach
                                with open(player_path, "r", encoding="utf-8") as f:
                                    items = [line.strip() for line in f if line.strip()]
                                    if items:
                                        player_list = ValidationList(
                                            list_type="player", entries=items
                                        )
                                        player_list.file_path = player_path
                                        lists["player"] = player_list
                                        self._logger.info(
                                            f"Loaded player list with {len(items)} items (alternate method)"
                                        )
                                        break
                if "player" in lists:
                    break

            # Load chest type list
            for key in ["chest_type_list", "chest_type_list_path"]:
                for section in ["Validation", "General"]:
                    chest_type_list_path = self._config.get(section, key, "")
                    if chest_type_list_path:
                        chest_path = Path(chest_type_list_path)
                        self._logger.info(f"Loading chest type list from: {chest_path}")

                        if chest_path.exists():
                            try:
                                chest_list = ValidationList.load_from_file(chest_path)
                                if chest_list is not None:
                                    lists["chest_type"] = chest_list
                                    self._logger.info(
                                        f"Loaded chest type list with {len(chest_list.items)} items"
                                    )
                                    break
                            except Exception as e:
                                self._logger.warning(f"Error loading chest type list: {str(e)}")
                                # Try alternate loading approach
                                with open(chest_path, "r", encoding="utf-8") as f:
                                    items = [line.strip() for line in f if line.strip()]
                                    if items:
                                        chest_list = ValidationList(
                                            list_type="chest_type", entries=items
                                        )
                                        chest_list.file_path = chest_path
                                        lists["chest_type"] = chest_list
                                        self._logger.info(
                                            f"Loaded chest type list with {len(items)} items (alternate method)"
                                        )
                                        break
                if "chest_type" in lists:
                    break

            # Load source list
            for key in ["source_list", "source_list_path"]:
                for section in ["Validation", "General"]:
                    source_list_path = self._config.get(section, key, "")
                    if source_list_path:
                        source_path = Path(source_list_path)
                        self._logger.info(f"Loading source list from: {source_path}")

                        if source_path.exists():
                            try:
                                source_list = ValidationList.load_from_file(source_path)
                                if source_list is not None:
                                    lists["source"] = source_list
                                    self._logger.info(
                                        f"Loaded source list with {len(source_list.items)} items"
                                    )
                                    break
                            except Exception as e:
                                self._logger.warning(f"Error loading source list: {str(e)}")
                                # Try alternate loading approach
                                with open(source_path, "r", encoding="utf-8") as f:
                                    items = [line.strip() for line in f if line.strip()]
                                    if items:
                                        source_list = ValidationList(
                                            list_type="source", entries=items
                                        )
                                        source_list.file_path = source_path
                                        lists["source"] = source_list
                                        self._logger.info(
                                            f"Loaded source list with {len(items)} items (alternate method)"
                                        )
                                        break
                if "source" in lists:
                    break

            # Store the lists (but don't emit signal yet)
            self._validation_lists = lists
            return lists

        except Exception as e:
            self._logger.error(f"Error loading validation lists: {str(e)}")
            self._logger.error(traceback.format_exc())
            return {}
