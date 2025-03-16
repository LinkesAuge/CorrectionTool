"""
corrector.py

Description: Service for applying corrections to chest entries
Usage:
    from src.services.corrector import Corrector
    corrector = Corrector(rules)
    corrected_entries = corrector.apply_corrections(entries)
"""

from typing import Dict, List, Optional, Set, Tuple

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule


class Corrector:
    """
    Service for applying corrections to chest entries.
    
    Applies correction rules to chest entries, tracking stats and changes.
    
    Attributes:
        rules (List[CorrectionRule]): The correction rules to apply
        stats (Dict[str, int]): Statistics about applied corrections
        
    Implementation Notes:
        - Processes rules in order of priority
        - Tracks statistics for reporting
        - Supports exact string matching
    """
    
    def __init__(self, rules: List[CorrectionRule]) -> None:
        """
        Initialize a Corrector with correction rules.
        
        Args:
            rules (List[CorrectionRule]): The correction rules to apply
        """
        self.rules = sorted(rules, key=lambda r: r.priority, reverse=True)
        self.stats: Dict[str, int] = {
            'entries_processed': 0,
            'entries_corrected': 0,
            'corrections_made': 0,
        }
    
    def apply_corrections(self, entries: List[ChestEntry]) -> List[ChestEntry]:
        """
        Apply corrections to a list of chest entries.
        
        Args:
            entries (List[ChestEntry]): The entries to correct
            
        Returns:
            List[ChestEntry]: The corrected entries
        """
        self.stats = {
            'entries_processed': 0,
            'entries_corrected': 0,
            'corrections_made': 0,
        }
        
        for entry in entries:
            self.stats['entries_processed'] += 1
            entry_corrected = False
            
            # Process fields
            for field in ['chest_type', 'player', 'source']:
                field_value = entry.get_field(field)
                corrected_value, was_corrected = self._apply_rules_to_text(field_value, field)
                
                if was_corrected:
                    entry.apply_correction(field, corrected_value)
                    entry_corrected = True
                    self.stats['corrections_made'] += 1
            
            if entry_corrected:
                self.stats['entries_corrected'] += 1
        
        return entries
    
    def _apply_rules_to_text(self, text: str, field: str = None) -> Tuple[str, bool]:
        """
        Apply correction rules to a text string.
        
        Args:
            text (str): The text to correct
            field (str, optional): The field being corrected
            
        Returns:
            Tuple[str, bool]: (Corrected text, Whether correction was applied)
        """
        original_text = text
        corrected_text = text
        
        for rule in self.rules:
            # Skip rules that don't apply to this field
            if field and not rule.applies_to_field(field):
                continue
                
            # Apply the rule
            corrected_text, _ = rule.apply_to_text(corrected_text)
        
        return corrected_text, corrected_text != original_text
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get correction statistics.
        
        Returns:
            Dict[str, int]: Dictionary of statistics
        """
        return self.stats 