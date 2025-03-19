"""
chest_entry.py

Description: Chest entry model class
Usage:
    from src.models.chest_entry import ChestEntry
    entry = ChestEntry(chest_type="Cobra Chest", player="Engelchen", source="Level 15 Crypt")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import uuid
import logging


@dataclass
class ChestEntry:
    """
    Chest entry model class.

    This class represents a chest entry with its attributes and validation status.

    Attributes:
        id (Optional[int]): Entry ID (auto-generated if not provided)
        chest_type (str): The type of chest (e.g., "Cobra Chest")
        player (str): The player who received the chest (e.g., "Engelchen")
        source (str): The source of the chest (e.g., "Level 15 Crypt")
        status (str): Status of the entry (e.g., "Pending", "Valid", "Invalid")
        original_values (Dict[str, str]): Original values before corrections
        validation_errors (List[str]): List of validation errors for this entry
        field_validation (Dict[str, Dict]): Validation status for each field

    Implementation Notes:
        - Uses dataclass for simplified initialization
        - Tracks original values for comparison
        - Maintains correction history for reporting
        - Auto-generates IDs if not provided
    """

    chest_type: str
    player: str
    source: str
    id: Optional[int] = None
    status: str = "Pending"
    validation_errors: List[str] = field(default_factory=list)
    original_values: Dict[str, str] = field(default_factory=dict)
    field_validation: Dict[str, Dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Initialize the entry after creation.

        - Sets an ID if not provided
        - Initializes field validation status
        """
        try:
            # Auto-generate ID if not provided
            if self.id is None:
                # Use a hash of the content to create a stable ID
                self.id = abs(hash((self.chest_type, self.player, self.source))) % (10**8)

            # Initialize field validation status
            self.reset_validation()

            # Don't initialize original_values by default - we want it to start empty
            # and only store values when corrections are made

        except Exception as e:
            print(f"Error in ChestEntry.__post_init__: {e}")
            # Ensure we have the basic structure even if there was an error
            if not hasattr(self, "validation_errors"):
                self.validation_errors = []
            if not hasattr(self, "original_values"):
                self.original_values = {}

    def apply_correction(self, field_name: str, new_value: str) -> None:
        """
        Apply a correction to a field.

        Args:
            field_name (str): Name of the field
            new_value (str): New value for the field

        Raises:
            ValueError: If field_name is not valid
        """
        if field_name == "chest_type":
            # Store original value if this is the first correction
            if field_name not in self.original_values:
                self.original_values[field_name] = self.chest_type
            self.chest_type = new_value
        elif field_name == "player":
            if field_name not in self.original_values:
                self.original_values[field_name] = self.player
            self.player = new_value
        elif field_name == "source":
            if field_name not in self.original_values:
                self.original_values[field_name] = self.source
            self.source = new_value
        else:
            raise ValueError(f"Invalid field name: {field_name}")

    def has_corrections(self) -> bool:
        """
        Check if the entry has corrections.

        Returns:
            True if the entry has corrections, False otherwise
        """
        return bool(self.original_values)

    def has_validation_errors(self) -> bool:
        """
        Check if the entry has validation errors.

        Returns:
            True if the entry has validation errors, False otherwise
        """
        return len(self.validation_errors) > 0

    def add_validation_error(self, error: str) -> None:
        """
        Add a validation error to the entry.

        Args:
            error: Validation error message
        """
        if error not in self.validation_errors:
            self.validation_errors.append(error)
            self.status = "Invalid"

    def clear_validation_errors(self) -> None:
        """Clear all validation errors."""
        self.validation_errors.clear()
        self.status = "Valid" if self.has_corrections() else "Pending"

    def reset_corrections(self) -> None:
        """Reset all corrections to original values."""
        for field, original_value in self.original_values.items():
            setattr(self, field, original_value)
        self.original_values.clear()
        self.status = "Valid" if not self.has_validation_errors() else "Invalid"

    def add_correction(self, field: str, corrected_value: str) -> None:
        """
        Add a correction to the entry.

        Args:
            field: Field name to correct
            corrected_value: Corrected value
        """
        current_value = getattr(self, field)
        if current_value != corrected_value:
            # Store the original value if not already stored
            if field not in self.original_values:
                self.original_values[field] = current_value

            # Set the corrected value
            setattr(self, field, corrected_value)

    def copy(self) -> "ChestEntry":
        """
        Create a copy of this entry.

        Returns:
            A new ChestEntry instance with the same values
        """
        # Create a new instance
        new_entry = ChestEntry(
            chest_type=self.chest_type,
            player=self.player,
            source=self.source,
            id=self.id,
            status=self.status,
        )

        # Copy validation errors
        new_entry.validation_errors = self.validation_errors.copy()

        # Copy original values
        new_entry.original_values = self.original_values.copy()

        # Copy field validation
        if hasattr(self, "field_validation"):
            new_entry.field_validation = self.field_validation.copy()

        return new_entry

    def get_field(self, field_name: str) -> str:
        """
        Get the value of a field.

        Args:
            field_name: Name of the field

        Returns:
            Value of the field
        """
        return getattr(self, field_name, "")

    def get_original_field(self, field_name: str) -> str:
        """
        Get the original value of a field before corrections.

        Args:
            field_name: Name of the field

        Returns:
            Original value of the field or current value if no correction
        """
        return self.original_values.get(field_name, getattr(self, field_name, ""))

    def to_dict(self, include_id: bool = False) -> Dict[str, str]:
        """
        Convert the entry to a dictionary.

        Args:
            include_id: Whether to include the ID in the dictionary

        Returns:
            Dictionary representation of the entry
        """
        result = {
            "chest_type": self.chest_type,
            "player": self.player,
            "source": self.source,
            "status": self.status,
        }

        if include_id and self.id is not None:
            result["id"] = str(self.id)

        return result

    def to_tuple(self) -> Tuple[str, str, str]:
        """
        Convert the entry to a tuple.

        Returns:
            Tuple representation of the entry (chest_type, player, source)
        """
        return (self.chest_type, self.player, self.source)

    def to_text(self) -> str:
        """
        Convert the entry to its original text format.

        Returns:
            str: Text representation with 3 lines (chest_type, player, source)
        """
        # Format player with "From: " prefix if it doesn't have it
        player_line = self.player
        if not player_line.lower().startswith("from:"):
            player_line = f"From: {player_line}"

        # Format source with "Source: " prefix if it doesn't have it
        source_line = self.source
        if not source_line.lower().startswith("source:"):
            source_line = f"Source: {source_line}"

        return f"{self.chest_type}\n{player_line}\n{source_line}"

    @classmethod
    def from_text(cls, text: str) -> "ChestEntry":
        """
        Create a ChestEntry from text.

        Args:
            text: Text containing chest entry (3 lines: chest_type, player, source)

        Returns:
            ChestEntry: The created entry

        Raises:
            ValueError: If the text is not in the expected format
        """
        try:
            # Split text into lines
            lines = text.strip().splitlines()

            # Validate line count
            if len(lines) < 3:
                raise ValueError(f"Text must contain at least 3 lines, got {len(lines)}")

            # Extract chest type (first line)
            chest_type = lines[0].strip()
            if not chest_type:
                raise ValueError("Chest type cannot be empty")

            # Extract player (second line)
            player_line = lines[1].strip()
            if not player_line:
                raise ValueError("Player line cannot be empty")

            # Check if player line starts with "From:"
            if player_line.lower().startswith("from:"):
                player = player_line[5:].strip()  # Remove "From:" prefix
            else:
                player = player_line

            if not player:
                raise ValueError("Player cannot be empty")

            # Extract source (third line)
            source_line = lines[2].strip()
            if not source_line:
                raise ValueError("Source line cannot be empty")

            # Check if source line starts with "Source:"
            if source_line.lower().startswith("source:"):
                source = source_line[7:].strip()  # Remove "Source:" prefix
            else:
                source = source_line

            if not source:
                raise ValueError("Source cannot be empty")

            # Create entry
            return cls(
                chest_type=chest_type,
                player=player,
                source=source,
            )
        except Exception as e:
            # Add context to the error
            raise ValueError(f"Error parsing chest entry: {str(e)}\nText: {text}") from e

    def reset_validation(self) -> None:
        """Reset all validation information."""
        self.validation_errors.clear()
        self.field_validation = {
            "chest_type": {"valid": None, "confidence": 0.0, "fuzzy_match": None},
            "player": {"valid": None, "confidence": 0.0, "fuzzy_match": None},
            "source": {"valid": None, "confidence": 0.0, "fuzzy_match": None},
        }

    def set_field_validation(
        self, field: str, valid: bool, confidence: float = 1.0, fuzzy_match: Optional[str] = None
    ) -> None:
        """
        Set validation status for a field.

        Args:
            field (str): Field name
            valid (bool): Whether the field is valid
            confidence (float, optional): Confidence score (0.0-1.0)
            fuzzy_match (Optional[str], optional): Matched value for fuzzy matches
        """
        if field not in self.field_validation:
            return

        self.field_validation[field] = {
            "valid": valid,
            "confidence": confidence,
            "fuzzy_match": fuzzy_match,
        }

        # Add validation error if invalid
        if not valid:
            self.add_validation_error(f"Invalid {field}: {self.get_field(field)}")

    def get_field_validation(self, field: str) -> Dict:
        """
        Get validation information for a field.

        Args:
            field (str): Field name

        Returns:
            Dict: Validation information
        """
        return self.field_validation.get(
            field, {"valid": None, "confidence": 0.0, "fuzzy_match": None}
        )

    def is_field_valid(self, field: str) -> Optional[bool]:
        """
        Check if a field is valid.

        Args:
            field (str): Field name

        Returns:
            Optional[bool]: True if valid, False if invalid, None if not validated
        """
        return self.field_validation.get(field, {}).get("valid")

    def is_fuzzy_match(self, field: str) -> bool:
        """
        Check if a field has a fuzzy match.

        Args:
            field (str): Field name

        Returns:
            bool: True if the field has a fuzzy match, False otherwise
        """
        validation = self.field_validation.get(field, {})
        return validation.get("valid", False) and validation.get("confidence", 1.0) < 1.0

    def get_match_confidence(self, field: str) -> float:
        """
        Get the confidence score for a field match.

        Args:
            field (str): Field name

        Returns:
            float: Confidence score (0.0-1.0)
        """
        return self.field_validation.get(field, {}).get("confidence", 0.0)

    def is_player_valid(self) -> Optional[bool]:
        """
        Check if the player field is valid.

        Returns:
            Optional[bool]: True if valid, False if invalid, None if not validated
        """
        return self.is_field_valid("player")

    def is_chest_type_valid(self) -> Optional[bool]:
        """
        Check if the chest_type field is valid.

        Returns:
            Optional[bool]: True if valid, False if invalid, None if not validated
        """
        return self.is_field_valid("chest_type")

    def is_source_valid(self) -> Optional[bool]:
        """
        Check if the source field is valid.

        Returns:
            Optional[bool]: True if valid, False if invalid, None if not validated
        """
        return self.is_field_valid("source")

    def get_fuzzy_match(self, field: str) -> Optional[str]:
        """
        Get the fuzzy match value for a field.

        Args:
            field (str): Field name

        Returns:
            Optional[str]: Matched value or None
        """
        return self.field_validation.get(field, {}).get("fuzzy_match")

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ChestEntry":
        """
        Create a chest entry from a dictionary.

        Args:
            data: Dictionary with entry data

        Returns:
            ChestEntry instance
        """
        # Create entry with only required fields (ID will be auto-generated)
        return cls(
            chest_type=data.get("chest_type", ""),
            player=data.get("player", ""),
            source=data.get("source", ""),
            id=int(data["id"]) if "id" in data else None,
        )

    def __str__(self) -> str:
        """
        Get string representation of the entry.

        Returns:
            String representation
        """
        return f"{self.chest_type} - From: {self.player} - Source: {self.source}"

    def __eq__(self, other):
        """
        Check if two ChestEntry objects are equal based on their ID.

        Args:
            other: Another ChestEntry object to compare with

        Returns:
            bool: True if the entries have the same ID, False otherwise
        """
        try:
            # Check if other is a ChestEntry object
            if not isinstance(other, ChestEntry):
                return False

            # Compare IDs as strings to handle potential type differences
            if self.id is None and other.id is None:
                return (
                    self.chest_type == other.chest_type
                    and self.player == other.player
                    and self.source == other.source
                )

            if self.id is None or other.id is None:
                return False

            return str(self.id) == str(other.id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error comparing ChestEntry objects: {str(e)}")
            # Log attributes of both entries to help diagnose issues
            try:
                logger.error(
                    f"Self: ID={self.id}, Type={self.chest_type}, Player={self.player}, Source={self.source}"
                )
                logger.error(
                    f"Other: ID={other.id}, Type={other.chest_type}, Player={other.player}, Source={other.source}"
                )
            except Exception as inner_e:
                logger.error(f"Error logging entry details: {str(inner_e)}")
            return False
