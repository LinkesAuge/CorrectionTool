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
from src.interfaces.i_service_factory import IServiceFactory

# Instead of importing classes directly, we'll use service factory to get interfaces
# to avoid circular dependencies


def get_dataframe_store(service_factory=None):
    """
    Get the DataStore implementation from the service factory.
    This is a lazy-loaded function to prevent circular imports.

    Args:
        service_factory: Optional service factory to use

    Returns:
        IDataStore: The DataStore implementation
    """
    if service_factory:
        return service_factory.get_service(IDataStore)

    # Fallback to traditional import if needed
    from src.services.dataframe_store import DataFrameStore
    from src.services.service_factory import ServiceFactory

    factory = ServiceFactory.get_instance()
    return factory.get_service(IDataStore)


def get_file_service(service_factory=None):
    """
    Get the FileService implementation from the service factory.
    This is a lazy-loaded function to prevent circular imports.

    Args:
        service_factory: Optional service factory to use

    Returns:
        IFileService: The FileService implementation
    """
    if service_factory:
        return service_factory.get_service(IFileService)

    # Fallback to traditional import if needed
    from src.services.file_service import FileService
    from src.services.service_factory import ServiceFactory

    factory = ServiceFactory.get_instance()
    return factory.get_service(IFileService)


def get_correction_service(service_factory=None):
    """
    Get the CorrectionService implementation from the service factory.
    This is a lazy-loaded function to prevent circular imports.

    Args:
        service_factory: Optional service factory to use

    Returns:
        ICorrectionService: The CorrectionService implementation
    """
    if service_factory:
        return service_factory.get_service(ICorrectionService)

    # Fallback to traditional import if needed
    from src.services.correction_service import CorrectionService
    from src.services.service_factory import ServiceFactory

    factory = ServiceFactory.get_instance()
    return factory.get_service(ICorrectionService)


def get_validation_service(service_factory=None):
    """
    Get the ValidationService implementation from the service factory.
    This is a lazy-loaded function to prevent circular imports.

    Args:
        service_factory: Optional service factory to use

    Returns:
        IValidationService: The ValidationService implementation
    """
    if service_factory:
        return service_factory.get_service(IValidationService)

    # Fallback to traditional import if needed
    from src.services.validation_service import ValidationService
    from src.services.service_factory import ServiceFactory

    factory = ServiceFactory.get_instance()
    return factory.get_service(IValidationService)


def get_service_factory():
    """
    Get the ServiceFactory singleton instance.
    This is a lazy-loaded function to prevent circular imports.

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
    "get_dataframe_store",
    "get_file_service",
    "get_correction_service",
    "get_validation_service",
    "get_service_factory",
    # Interface imports
    "IDataStore",
    "IFileService",
    "ICorrectionService",
    "IValidationService",
    "IServiceFactory",
]
