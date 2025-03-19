"""
Models module for the Chest Tracker Correction Tool.

This module contains the data models for the application.
Implements lazy loading for classes with circular dependencies.
"""

# Direct imports for classes without circular dependencies
from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule


# Lazy-loaded imports to break circular dependencies
def get_validation_list():
    """Lazy loading getter for ValidationList class."""
    from src.models.validation_list import ValidationList

    return ValidationList


__all__ = [
    "ChestEntry",
    "CorrectionRule",
    "get_validation_list",
]
