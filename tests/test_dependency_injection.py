"""
test_dependency_injection.py

Description: Tests for the dependency injection system refinements
Usage:
    python -m pytest tests/test_dependency_injection.py
"""

import pytest
import logging

# Import interfaces
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_correction_service import ICorrectionService
from src.interfaces.i_validation_service import IValidationService
from src.interfaces.i_config_manager import IConfigManager
from src.interfaces.i_service_factory import IServiceFactory

# Import service helpers
from src.services import (
    get_service,
    get_dataframe_store,
    get_file_service,
    get_correction_service,
    get_validation_service,
    get_config_manager,
    get_service_factory,
)

# Import service factory
from src.services.service_factory import ServiceFactory

# Import app bootstrapper
from src.app_bootstrapper import AppBootstrapper

# Setup logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_service_factory_singleton():
    """Test that ServiceFactory is a proper singleton."""
    # Get instance directly
    factory1 = ServiceFactory.get_instance()
    factory2 = ServiceFactory.get_instance()

    # Verify they are the same instance
    assert factory1 is factory2

    # Verify helper function returns the same instance
    factory3 = get_service_factory()
    assert factory1 is factory3


def test_app_bootstrapper_with_service_factory():
    """Test that AppBootstrapper works with the ServiceFactory singleton."""
    # Initialize app bootstrapper
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()

    # Get service factory from bootstrapper
    factory1 = bootstrapper.service_factory

    # Get service factory from helper
    factory2 = get_service_factory()

    # Verify they are the same instance
    assert factory1 is factory2


def test_service_resolution():
    """Test that services can be resolved through different methods."""
    # Initialize app bootstrapper
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()

    # Get services through ServiceFactory.get_service
    factory = ServiceFactory.get_instance()
    data_store1 = factory.get_service(IDataStore)
    file_service1 = factory.get_service(IFileService)

    # Get services through helper functions
    data_store2 = get_dataframe_store()
    file_service2 = get_file_service()

    # Get services through generic get_service function
    data_store3 = get_service(IDataStore)
    file_service3 = get_service(IFileService)

    # Verify they are the same instances
    assert data_store1 is data_store2
    assert data_store1 is data_store3
    assert file_service1 is file_service2
    assert file_service1 is file_service3


def test_all_services_available():
    """Test that all core services are available through the dependency injection system."""
    # Initialize app bootstrapper
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()

    # Get all services
    data_store = get_dataframe_store()
    file_service = get_file_service()
    correction_service = get_correction_service()
    validation_service = get_validation_service()
    config_manager = get_config_manager()

    # Verify they are of the correct types
    assert isinstance(data_store, IDataStore)
    assert isinstance(file_service, IFileService)
    assert isinstance(correction_service, ICorrectionService)
    assert isinstance(validation_service, IValidationService)
    assert isinstance(config_manager, IConfigManager)
