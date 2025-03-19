"""
i_correction_service.py

Description: Interface for the correction service
Usage:
    from src.interfaces.i_correction_service import ICorrectionService
    service = service_factory.get_service(ICorrectionService)
    result = service.apply_corrections()
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class ICorrectionService(ABC):
    """
    Interface for the correction service.

    This interface defines methods for applying and managing corrections to entries.
    """

    @abstractmethod
    def apply_corrections(self, specific_entries: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Apply all correction rules to entries.

        Args:
            specific_entries: Optional list of entry IDs to correct (corrects all if None)

        Returns:
            Dict[str, int]: Correction statistics (applied, total)
        """
        pass

    @abstractmethod
    def apply_specific_correction(
        self, entry_id: int, field: str, from_text: str, to_text: str
    ) -> bool:
        """
        Apply a specific correction to a single entry.

        Args:
            entry_id: ID of the entry to correct
            field: Field to correct ('chest_type', 'player', 'source')
            from_text: Original text to replace
            to_text: New text to use

        Returns:
            bool: True if correction was applied, False otherwise
        """
        pass

    @abstractmethod
    def reset_corrections(self, entry_ids: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Reset corrections by restoring original values.

        Args:
            entry_ids: Optional list of entry IDs to reset (resets all if None)

        Returns:
            Dict[str, int]: Reset statistics (reset, total)
        """
        pass

    @abstractmethod
    def add_correction_rule(
        self,
        field: str,
        incorrect_value: str,
        correct_value: str,
        case_sensitive: bool = True,
        match_type: str = "exact",
        enabled: bool = True,
    ) -> bool:
        """
        Add a new correction rule.

        Args:
            field: Field to apply the correction to ('chest_type', 'player', 'source')
            incorrect_value: The value to be corrected
            correct_value: The corrected value to use
            case_sensitive: Whether the match should be case sensitive
            match_type: Type of match ('exact', 'contains', 'startswith', 'endswith', 'regex')
            enabled: Whether the rule should be active

        Returns:
            bool: True if rule was added successfully, False otherwise
        """
        pass
