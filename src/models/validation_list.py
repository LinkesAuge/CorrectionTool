"""
validation_list.py

Description: Data model for validation lists of valid players, chest types, or sources
Usage:
    from src.models.validation_list import ValidationList
    player_list = ValidationList("player", ["Engelchen", "Sir Met", "Moony"])
"""

import csv
from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, Tuple

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

    Implementation Notes:
        - Uses set for O(1) lookup time
        - Supports import/export from CSV
        - Supports exact, case-insensitive, and fuzzy matching
    """

    def __init__(
        self,
        list_type: Literal["player", "chest_type", "source"] = "player",
        entries: Optional[List[str]] = None,
        name: str = "default",
    ) -> None:
        """
        Initialize a ValidationList.

        Args:
            list_type (Literal["player", "chest_type", "source"]): Type of list
            entries (Optional[List[str]]): Initial entries
            name (str): Name of the validation list
        """
        self.list_type = list_type
        self.entries: Set[str] = set()
        self.name = name
        self._use_fuzzy_matching = False

        # Initialize fuzzy matcher with default threshold
        config = ConfigManager()
        threshold = config.get_float("Validation", "fuzzy_threshold", fallback=75) / 100.0
        self._fuzzy_matcher = FuzzyMatcher(threshold=threshold)

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
            bool: True if fuzzy matching is enabled, False otherwise
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

    def save_to_file(self, file_path: Path) -> None:
        """
        Save the validation list to a CSV file.

        Args:
            file_path (Path): Path to save to
        """
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Type", self.list_type])
            writer.writerow(["Name", self.name])
            writer.writerow(["Entry"])
            for entry in sorted(self.entries):
                writer.writerow([entry])

    @classmethod
    def load_from_file(cls, file_path: Path) -> "ValidationList":
        """
        Load a validation list from a CSV file.

        Args:
            file_path (Path): Path to load from

        Returns:
            ValidationList: The loaded validation list

        Raises:
            ValueError: If the file format is invalid
        """
        with open(file_path, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)

            # Read type
            try:
                type_row = next(reader)
                if len(type_row) != 2 or type_row[0] != "Type":
                    raise ValueError("Invalid validation list file format: missing Type row")
                list_type = type_row[1]

                # Validate list type
                if list_type not in ("player", "chest_type", "source"):
                    raise ValueError(f"Invalid list type: {list_type}")

                # Read name
                name_row = next(reader)
                if len(name_row) != 2 or name_row[0] != "Name":
                    raise ValueError("Invalid validation list file format: missing Name row")
                name = name_row[1]

                # Read header
                header_row = next(reader)
                if len(header_row) != 1 or header_row[0] != "Entry":
                    raise ValueError("Invalid validation list file format: missing Entry header")

                # Read entries
                entries = []
                for row in reader:
                    if row and len(row) > 0:
                        entries.append(row[0])

                return cls(list_type=list_type, entries=entries, name=name)  # type: ignore
            except StopIteration:
                raise ValueError("Invalid validation list file format: file is too short")
            except Exception as e:
                raise ValueError(f"Error loading validation list: {str(e)}")
