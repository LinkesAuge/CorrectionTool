"""
correction_rule.py

Description: Data model for correction rules
Usage:
    from src.models.correction_rule import CorrectionRule
    rule = CorrectionRule(from_text="Krimelmonster", to_text="Krümelmonster")
"""

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional


@dataclass
class CorrectionRule:
    """
    Represents a correction rule for text replacement.
    
    A rule defines a text string to be replaced and its replacement value.
    
    Attributes:
        from_text (str): The text to be replaced
        to_text (str): The replacement text
        rule_type (str): Type of rule ('exact' or 'fuzzy')
        priority (int): Priority of the rule (higher numbers = higher priority)
        field_target (Optional[str]): Target field for the rule (None = all fields)
        
    Implementation Notes:
        - Uses dataclass for simplified initialization
        - Supports exact string matching and fuzzy matching
        - Higher priority rules are applied first
    """
    
    from_text: str
    to_text: str
    rule_type: Literal["exact", "fuzzy"] = "exact"
    priority: int = 0
    field_target: Optional[Literal["chest_type", "player", "source"]] = None
    
    def apply_to_text(self, text: str) -> tuple[str, bool]:
        """
        Apply the rule to a text string.
        
        Args:
            text (str): The text to apply the rule to
            
        Returns:
            tuple[str, bool]: (Corrected text, Whether correction was applied)
        """
        if self.rule_type == "exact":
            if self.from_text in text:
                corrected = text.replace(self.from_text, self.to_text)
                return corrected, corrected != text
            return text, False
        else:
            # Fuzzy matching would be implemented here
            # For now, return unchanged text
            return text, False
    
    def applies_to_field(self, field: str) -> bool:
        """
        Check if this rule applies to a specific field.
        
        Args:
            field (str): The field to check ('chest_type', 'player', or 'source')
            
        Returns:
            bool: True if the rule applies to the field, False otherwise
        """
        return self.field_target is None or self.field_target == field
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert the rule to a dictionary.
        
        Returns:
            Dict[str, str]: Dictionary representation of the rule
        """
        result = {
            'from_text': self.from_text,
            'to_text': self.to_text,
            'rule_type': self.rule_type,
            'priority': str(self.priority)
        }
        
        if self.field_target:
            result['field_target'] = self.field_target
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "CorrectionRule":
        """
        Create a CorrectionRule from a dictionary.
        
        Args:
            data (Dict[str, str]): Dictionary representation of the rule
            
        Returns:
            CorrectionRule: The created rule
            
        Raises:
            ValueError: If required fields are missing
        """
        if 'from_text' not in data or 'to_text' not in data:
            raise ValueError("Dictionary must contain 'from_text' and 'to_text' keys")
        
        rule_type = data.get('rule_type', "exact")
        if rule_type not in ("exact", "fuzzy"):
            rule_type = "exact"
            
        priority = int(data.get('priority', 0))
        
        field_target = data.get('field_target')
        if field_target not in (None, "chest_type", "player", "source"):
            field_target = None
            
        return cls(
            from_text=data['from_text'],
            to_text=data['to_text'],
            rule_type=rule_type,  # type: ignore
            priority=priority,
            field_target=field_target,  # type: ignore
        )
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> "CorrectionRule":
        """
        Create a CorrectionRule from a CSV row.
        
        Args:
            row (Dict[str, str]): CSV row with 'From' and 'To' columns
            
        Returns:
            CorrectionRule: The created rule
            
        Raises:
            ValueError: If required fields are missing
        """
        if 'From' not in row or 'To' not in row:
            raise ValueError("CSV row must contain 'From' and 'To' columns")
            
        return cls(from_text=row['From'], to_text=row['To'])
    
    def to_csv_row(self) -> Dict[str, str]:
        """
        Convert the rule to a CSV row.
        
        Returns:
            Dict[str, str]: CSV row with 'From' and 'To' columns
        """
        return {
            'From': self.from_text,
            'To': self.to_text
        } 