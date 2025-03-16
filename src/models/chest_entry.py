"""
chest_entry.py

Description: Data model for chest entries from the Total Battle game
Usage:
    from src.models.chest_entry import ChestEntry
    entry = ChestEntry(chest_type="Cobra Chest", player="Engelchen", source="Level 15 Crypt")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ChestEntry:
    """
    Represents a chest entry from the Total Battle game.
    
    Contains information about a chest, including its type, player, and source.
    Tracks validation status and correction history.
    
    Attributes:
        chest_type (str): The type of chest (e.g., "Cobra Chest")
        player (str): The player who received the chest (e.g., "Engelchen")
        source (str): The source of the chest (e.g., "Level 15 Crypt")
        original_chest_type (str): The original chest type before corrections
        original_player (str): The original player before corrections
        original_source (str): The original source before corrections
        validation_errors (List[str]): List of validation errors for this entry
        corrections (List[Tuple[str, str, str]]): List of corrections made (field, from, to)
        
    Implementation Notes:
        - Uses dataclass for simplified initialization
        - Tracks original values for comparison
        - Maintains correction history for reporting
    """
    
    chest_type: str
    player: str
    source: str
    original_chest_type: Optional[str] = None
    original_player: Optional[str] = None
    original_source: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    corrections: List[Tuple[str, str, str]] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """
        Initialize the original values if not provided.
        """
        if self.original_chest_type is None:
            self.original_chest_type = self.chest_type
        if self.original_player is None:
            self.original_player = self.player
        if self.original_source is None:
            self.original_source = self.source
    
    def apply_correction(self, field: str, to_value: str) -> bool:
        """
        Apply a correction to a specific field.
        
        Args:
            field (str): The field to correct ('chest_type', 'player', or 'source')
            to_value (str): The corrected value
            
        Returns:
            bool: True if correction was applied, False otherwise
            
        Raises:
            ValueError: If field is not valid
        """
        if field not in ['chest_type', 'player', 'source']:
            raise ValueError(f"Invalid field: {field}")
        
        from_value = getattr(self, field)
        if from_value == to_value:
            return False
        
        # Record the correction
        self.corrections.append((field, from_value, to_value))
        
        # Apply the correction
        setattr(self, field, to_value)
        
        return True
    
    def has_corrections(self) -> bool:
        """
        Check if this entry has any corrections.
        
        Returns:
            bool: True if there are corrections, False otherwise
        """
        return len(self.corrections) > 0
    
    def has_validation_errors(self) -> bool:
        """
        Check if this entry has any validation errors.
        
        Returns:
            bool: True if there are validation errors, False otherwise
        """
        return len(self.validation_errors) > 0
    
    def add_validation_error(self, error: str) -> None:
        """
        Add a validation error to this entry.
        
        Args:
            error (str): The validation error message
        """
        if error not in self.validation_errors:
            self.validation_errors.append(error)
    
    def clear_validation_errors(self) -> None:
        """
        Clear all validation errors.
        """
        self.validation_errors.clear()
    
    def get_field(self, field: str) -> str:
        """
        Get the value of a specific field.
        
        Args:
            field (str): The field to get ('chest_type', 'player', or 'source')
            
        Returns:
            str: The field value
            
        Raises:
            ValueError: If field is not valid
        """
        if field not in ['chest_type', 'player', 'source']:
            raise ValueError(f"Invalid field: {field}")
        
        return getattr(self, field)
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert the entry to a dictionary.
        
        Returns:
            Dict[str, str]: Dictionary representation of the entry
        """
        return {
            'chest_type': self.chest_type,
            'player': self.player,
            'source': self.source
        }
    
    def to_tuple(self) -> Tuple[str, str, str]:
        """
        Convert the entry to a tuple.
        
        Returns:
            Tuple[str, str, str]: Tuple representation of the entry (chest_type, player, source)
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
        Create a ChestEntry from a 3-line text.
        
        Args:
            text (str): The 3-line text (chest_type, player, source)
            
        Returns:
            ChestEntry: The created entry
            
        Raises:
            ValueError: If text doesn't have 3 lines
        """
        lines = text.strip().split('\n')
        if len(lines) < 3:
            raise ValueError(f"Text must have at least 3 lines: {text}")
        
        chest_type = lines[0].strip()
        
        # Extract player (remove "From: " prefix if present)
        player_line = lines[1].strip()
        if player_line.lower().startswith("from:"):
            player = player_line[player_line.lower().index("from:") + 5:].strip()
        else:
            player = player_line
        
        # Extract source (remove "Source: " prefix if present)
        source_line = lines[2].strip()
        if source_line.lower().startswith("source:"):
            source = source_line[source_line.lower().index("source:") + 7:].strip()
        else:
            source = source_line
        
        return cls(chest_type=chest_type, player=player, source=source) 