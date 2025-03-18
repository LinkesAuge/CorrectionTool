"""
validation_list.py

Description: Data model for validation lists of valid players, chest types, or sources
Usage:
    from src.models.validation_list import ValidationList
    player_list = ValidationList("player", ["Engelchen", "Sir Met", "Moony"])
"""

import csv
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, Tuple, Union
import logging
import os

from src.services.config_manager import ConfigManager
from src.services.fuzzy_matcher import FuzzyMatcher


class ValidationList:
    """
    Represents a list of valid entries for validation purposes.

    Used to validate chest entries against known valid values.

    Attributes:
        list_type (str): Type of list ('player', 'chest_type', 'source')
        entries (Set[str]): Set of valid entries
        items (List[str]): Same as entries but as a list for easier UI integration
        name (str): Name of the validation list
        use_fuzzy_matching (bool): Whether to use fuzzy matching for validation
        fuzzy_matcher (FuzzyMatcher): Fuzzy matching service
        file_path (str): Path to the file containing the validation list

    Implementation Notes:
        - Uses set for O(1) lookup time
        - Supports import/export from CSV
        - Supports exact, case-insensitive, and fuzzy matching
    """

    def __init__(
        self,
        list_type: str = "player",
        entries: Optional[List[str]] = None,
        name: str = "Default",
        use_fuzzy_matching: bool = False,
        file_path: Optional[str] = None,
    ):
        """
        Initialize a validation list.

        Args:
            list_type (str): The type of validation list (e.g., "player", "chest_type")
            entries (Optional[List[str]], optional): List of entries. Defaults to None.
            name (str, optional): Name of the list. Defaults to "Default".
            use_fuzzy_matching (bool, optional): Whether to use fuzzy matching. Defaults to False.
            file_path (Optional[str], optional): Path to the file containing the list. Defaults to None.
        """
        # Validate list type
        if list_type not in ("player", "chest_type", "source") and list_type:
            logger = logging.getLogger(__name__)
            logger.warning(f"Non-standard list type: {list_type}")

        self.list_type = list_type
        self.entries: Set[str] = set()
        self.name = name
        self.file_path = file_path

        # Initialize private attributes for property accessors
        self._use_fuzzy_matching = use_fuzzy_matching

        # Initialize fuzzy matcher with default threshold from config
        config = ConfigManager()
        threshold = config.get_float("Validation", "fuzzy_threshold", fallback=75) / 100.0
        self._fuzzy_matcher = FuzzyMatcher(threshold=threshold)

        # Add entries if provided
        if entries:
            for entry in entries:
                self.add_entry(entry)

    @property
    def items(self) -> List[str]:
        """
        Get all entries as a list.

        Returns:
            List[str]: List of entries
        """
        return sorted(list(self.entries))

    @items.setter
    def items(self, value: List[str]) -> None:
        """
        Set entries from a list.

        Args:
            value (List[str]): List of entries
        """
        self.entries = set(value)

    @property
    def use_fuzzy_matching(self) -> bool:
        """
        Get whether fuzzy matching is enabled.

        Returns:
            bool: Whether fuzzy matching is enabled
        """
        return self._use_fuzzy_matching

    @use_fuzzy_matching.setter
    def use_fuzzy_matching(self, value: bool) -> None:
        """
        Set whether fuzzy matching is enabled.

        Args:
            value (bool): Whether to enable fuzzy matching
        """
        self._use_fuzzy_matching = value

    @property
    def fuzzy_matcher(self) -> FuzzyMatcher:
        """
        Get the fuzzy matcher.

        Returns:
            FuzzyMatcher: The fuzzy matcher
        """
        return self._fuzzy_matcher

    @fuzzy_matcher.setter
    def fuzzy_matcher(self, value: FuzzyMatcher) -> None:
        """
        Set the fuzzy matcher.

        Args:
            value (FuzzyMatcher): The fuzzy matcher
        """
        self._fuzzy_matcher = value

    def update_fuzzy_threshold(self, threshold: float) -> None:
        """
        Update the fuzzy matching threshold.

        Args:
            threshold (float): New threshold value (0.0-1.0)
        """
        self._fuzzy_matcher = FuzzyMatcher(threshold=threshold)

    def add_entry(self, entry: str) -> None:
        """
        Add an entry to the validation list.

        Args:
            entry (str): Entry to add
        """
        self.entries.add(entry.strip())

    def remove_entry(self, entry: str) -> bool:
        """
        Remove an entry from the validation list.

        Args:
            entry (str): Entry to remove

        Returns:
            bool: True if entry was removed, False if it wasn't in the list
        """
        if entry in self.entries:
            self.entries.remove(entry)
            return True
        return False

    def is_valid(self, entry: str) -> Tuple[bool, float, Optional[str]]:
        """
        Check if an entry is valid.

        Args:
            entry (str): Entry to validate

        Returns:
            Tuple[bool, float, Optional[str]]:
                - Boolean indicating if entry is valid
                - Confidence score (1.0 for exact match, lower for fuzzy)
                - Matched entry (for fuzzy matches) or None for exact/no match
        """
        if not entry:
            return False, 0.0, None

        # Get config settings
        config = ConfigManager()
        case_sensitive = config.get_bool("Validation", "case_sensitive", fallback=False)

        # Normalize entry for comparison
        normalized_entry = entry.strip()

        # First try exact match (case sensitive or insensitive)
        for valid_entry in self.entries:
            # For exact matching
            if case_sensitive:
                if normalized_entry == valid_entry:
                    return True, 1.0, None
            else:
                if normalized_entry.lower() == valid_entry.lower():
                    return True, 1.0, None

        # If no exact match and fuzzy matching is enabled, try fuzzy matching
        if self._use_fuzzy_matching and self.entries:
            # Convert entries to list for fuzzy matching
            entries_list = list(self.entries)

            # Find best match
            best_match, score = self._fuzzy_matcher.find_best_match(normalized_entry, entries_list)

            # If score exceeds threshold, consider it valid
            if score >= self._fuzzy_matcher.threshold:
                return True, score, best_match

        # No match found
        return False, 0.0, None

    def get_entries(self) -> List[str]:
        """
        Get all entries in the validation list.

        Returns:
            List[str]: List of entries
        """
        return sorted(list(self.entries))

    def clear(self) -> None:
        """
        Clear all entries from the validation list.
        """
        self.entries.clear()

    def count(self) -> int:
        """
        Get the number of entries in the validation list.

        Returns:
            int: Number of entries
        """
        return len(self.entries)

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """
        Save the validation list to a CSV file.

        Args:
            file_path (Union[str, Path]): Path to save to
        """
        # Convert Path to string if needed
        if isinstance(file_path, Path):
            file_path = str(file_path)

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Type", self.list_type])
                writer.writerow(["Name", self.name])
                writer.writerow(["Entry"])
                for entry in sorted(self.entries):
                    writer.writerow([entry])

            # Update the file_path attribute
            self.file_path = file_path
            logger = logging.getLogger(__name__)
            logger.info(f"Saved validation list to {file_path} with {len(self.entries)} entries")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving validation list to {file_path}: {str(e)}")
            raise ValueError(f"Failed to save validation list: {str(e)}")

    @classmethod
    def load_from_file(
        cls, file_path: Union[str, Path], list_type: Optional[str] = None
    ) -> "ValidationList":
        """
        Load a validation list from a file.

        Args:
            file_path (Union[str, Path]): Path to the file containing the validation list.
            list_type (Optional[str]): Override the list type (useful for text files).

        Returns:
            ValidationList: The loaded validation list.

        Raises:
            ValueError: If the file format is invalid.
        """
        logger = logging.getLogger(__name__)

        # Convert Path to string if needed
        if isinstance(file_path, Path):
            file_path = str(file_path)

        logger.info(f"Loading validation list from: {file_path}")

        try:
            # Get file extension
            _, ext = os.path.splitext(file_path)

            # If it's a CSV file, try to parse with the expected format (with headers)
            if ext.lower() == ".csv":
                with open(file_path, "r", newline="", encoding="utf-8") as f:
                    # Try to detect the CSV format
                    sample = f.read(1024)
                    f.seek(0)  # Reset file position

                    # Check if this is a comma-separated file
                    if "," in sample:
                        reader = csv.reader(f)
                        try:
                            # Read the first row which should contain "Type"
                            type_row = next(reader)
                            if len(type_row) < 1:
                                raise ValueError("Invalid file format: Empty row")

                            # Special handling for 'Type,player' format
                            if type_row[0] == "Type":
                                detected_list_type = type_row[1] if len(type_row) > 1 else "player"
                            else:
                                detected_list_type = "player"  # Default

                            # Use provided list_type if available
                            final_list_type = list_type or detected_list_type

                            # Read the second row which should contain "Name"
                            name_row = next(reader)
                            if len(name_row) < 1:
                                raise ValueError("Invalid file format: Empty row")

                            # Special handling for 'Name,Default Player List' format
                            if name_row[0] == "Name":
                                name = name_row[1] if len(name_row) > 1 else "Default"
                            else:
                                name = "Default"  # Default name

                                # If we didn't find a Name row, this might be an entry, so reset position
                                f.seek(0)
                                next(reader)  # Skip the Type row

                            # Try to read the header row (might be just "Entry" without a comma)
                            header_row = next(reader)
                            if len(header_row) == 0:
                                raise ValueError("Invalid file format: Missing 'Entry' header")

                            # If the header isn't "Entry", this might already be an entry
                            if header_row[0] != "Entry" and "Entry" not in header_row:
                                # This is probably an entry already
                                entries = [header_row[0]] if header_row[0].strip() else []
                            else:
                                entries = []

                            # Read the entries
                            for row in reader:
                                if row and len(row) > 0 and row[0].strip():
                                    entries.append(row[0].strip())

                            logger.info(
                                f"Loaded {len(entries)} entries from CSV file. First few entries: {entries[:5] if entries else 'None'}"
                            )

                            # Create and return the validation list
                            validation_list = cls(list_type=final_list_type, name=name)
                            for entry in entries:
                                validation_list.add_entry(entry)
                            validation_list.file_path = file_path
                            return validation_list

                        except StopIteration:
                            raise ValueError("File is too short or not formatted correctly")
                    else:
                        # If no commas found, treat as simple text file
                        f.seek(0)  # Reset to beginning
                        entries = [line.strip() for line in f if line.strip()]

            # If it's not a CSV with proper formatting, try simple text format (one entry per line)
            with open(file_path, "r", encoding="utf-8") as f:
                # For simple text files, each line is an entry
                entries = [line.strip() for line in f if line.strip()]

                # Skip header lines if present
                if entries and (entries[0] == "Type,player" or entries[0].startswith("Type,")):
                    entries = entries[3:] if len(entries) > 3 else []
                elif entries and (entries[0].startswith("Type") or entries[0] == "Type"):
                    entries = entries[3:] if len(entries) > 3 else []

                # Use the filename without extension as the list name
                name = os.path.basename(file_path)
                name = os.path.splitext(name)[0]

                # Make the name more user-friendly
                if name.lower() == "player_list" or name.lower() == "players":
                    name = "Players"
                elif name.lower() == "chest_type_list" or name.lower() == "chest_types":
                    name = "Chest Types"
                elif name.lower() == "source_list" or name.lower() == "sources":
                    name = "Sources"

                # Determine list type based on provided parameter, file content, or name
                if list_type:
                    final_list_type = list_type
                elif "player" in file_path.lower():
                    final_list_type = "player"
                elif "chest" in file_path.lower() or "type" in file_path.lower():
                    final_list_type = "chest_type"
                elif "source" in file_path.lower():
                    final_list_type = "source"
                else:
                    # Default to player list
                    final_list_type = "player"

                # Set the display name based on the list type
                if final_list_type == "player":
                    name = "Players"
                elif final_list_type == "chest_type":
                    name = "Chest Types"
                elif final_list_type == "source":
                    name = "Sources"

                logger.info(
                    f"Loaded {len(entries)} entries from text file. First few entries: {entries[:5] if entries else 'None'}"
                )

                # Create and return the validation list
                validation_list = cls(list_type=final_list_type, name=name)
                for entry in entries:
                    validation_list.add_entry(entry)
                validation_list.file_path = file_path
                return validation_list

        except Exception as e:
            logger.error(f"Error loading validation list from {file_path}: {str(e)}")
            raise ValueError(f"Failed to load validation list: {str(e)}")
