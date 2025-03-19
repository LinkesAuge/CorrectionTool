"""
i_validation_service.py

Description: Interface for the validation service
Usage:
    from src.interfaces.i_validation_service import IValidationService
    validation_service = service_factory.get_service(IValidationService)
    result = validation_service.validate_entries()
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class IValidationService(ABC):
    """
    Interface for the validation service.

    This interface defines methods for validating entries against validation lists.
    """

    @abstractmethod
    def validate_entries(self, specific_entries: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Validate all entries or specific entries against validation lists.

        Args:
            specific_entries: Optional list of entry IDs to validate (validates all if None)

        Returns:
            Dict[str, int]: Validation statistics (valid, invalid, total)
        """
        pass

    @abstractmethod
    def get_invalid_entries(self) -> List[int]:
        """
        Get a list of invalid entry IDs.

        Returns:
            List[int]: List of entry IDs that failed validation
        """
        pass
