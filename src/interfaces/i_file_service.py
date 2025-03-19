"""
i_file_service.py

Description: Interface for the file service
Usage:
    from src.interfaces.i_file_service import IFileService
    file_service = service_factory.get_service(IFileService)
    file_service.load_entries(file_path)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pathlib import Path


class IFileService(ABC):
    """
    Interface for the file service.

    This interface defines methods for loading and saving data from files.
    """

    @abstractmethod
    def load_entries(self, file_path: Path) -> bool:
        """
        Load entries from a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def save_entries(self, file_path: Path) -> bool:
        """
        Save entries to a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def load_validation_list(self, list_type: str, file_path: Path) -> bool:
        """
        Load a validation list from a file.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def save_validation_list(self, list_type: str, file_path: Path) -> bool:
        """
        Save a validation list to a file.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def load_correction_rules(self, file_path: Path) -> bool:
        """
        Load correction rules from a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def save_correction_rules(self, file_path: Path) -> bool:
        """
        Save correction rules to a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        pass
