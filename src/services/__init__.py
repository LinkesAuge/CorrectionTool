"""
services package for the Chest Tracker Correction Tool.

This package contains service classes that handle various aspects of the application logic.
"""

# Import utility classes that don't create circular dependencies
from src.services.config_manager import ConfigManager
from src.services.corrector import Corrector
from src.services.file_parser import TextParser, CSVParser
from src.services.fuzzy_matcher import FuzzyMatcher

# Import interface definitions
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_correction_service import ICorrectionService
from src.interfaces.i_validation_service import IValidationService
from src.interfaces.i_config_manager import IConfigManager
from src.interfaces.i_service_factory import IServiceFactory

# Type variable for generic service types
from typing import TypeVar, Type, Any, Optional

T = TypeVar("T")


def get_service(interface_type: Type[T]) -> T:
    """
    Generic function to get a service by its interface type.

    Args:
        interface_type: Interface type to resolve

    Returns:
        Implementation of the requested interface

    Raises:
        ValueError: If no implementation is registered for the interface
    """
    from src.services.service_factory import ServiceFactory

    factory = ServiceFactory.get_instance()
    return factory.get_service(interface_type)


def get_dataframe_store() -> IDataStore:
    """
    Get the DataStore implementation.

    Returns:
        IDataStore: The DataStore implementation
    """
    return get_service(IDataStore)


def get_file_service() -> IFileService:
    """
    Get the FileService implementation.

    Returns:
        IFileService: The FileService implementation
    """
    return get_service(IFileService)


def get_correction_service() -> ICorrectionService:
    """
    Get the CorrectionService implementation.

    Returns:
        ICorrectionService: The CorrectionService implementation
    """
    return get_service(ICorrectionService)


def get_validation_service() -> IValidationService:
    """
    Get the ValidationService implementation.

    Returns:
        IValidationService: The ValidationService implementation
    """
    return get_service(IValidationService)


def get_config_manager() -> IConfigManager:
    """
    Get the ConfigManager implementation.

    Returns:
        IConfigManager: The ConfigManager implementation
    """
    return get_service(IConfigManager)


def get_service_factory() -> IServiceFactory:
    """
    Get the ServiceFactory singleton instance.

    Returns:
        IServiceFactory: The ServiceFactory implementation
    """
    from src.services.service_factory import ServiceFactory

    return ServiceFactory.get_instance()


__all__ = [
    # Directly importable classes
    "ConfigManager",
    "Corrector",
    "TextParser",
    "CSVParser",
    "FuzzyMatcher",
    # Lazy-loaded getter functions
    "get_service",
    "get_dataframe_store",
    "get_file_service",
    "get_correction_service",
    "get_validation_service",
    "get_config_manager",
    "get_service_factory",
    # Interface imports
    "IDataStore",
    "IFileService",
    "ICorrectionService",
    "IValidationService",
    "IConfigManager",
    "IServiceFactory",
]
