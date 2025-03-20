"""
test_service_factory_interface_compliance.py

Description: Detailed tests for ServiceFactory's compliance with the IServiceFactory interface
Usage:
    python -m pytest tests/test_service_factory_interface_compliance.py
"""

import pytest
import logging
import pandas as pd
from typing import Dict, Any, Type, List

# Import the interface and implementation
from src.interfaces.i_service_factory import IServiceFactory
from src.services.service_factory import ServiceFactory

# Import other interfaces for testing service resolution
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_correction_service import ICorrectionService
from src.interfaces.i_validation_service import IValidationService
from src.interfaces.i_config_manager import IConfigManager

# Import service helper functions
from src.services import (
    get_service,
    get_dataframe_store,
    get_file_service,
    get_correction_service,
    get_validation_service,
    get_config_manager,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@pytest.fixture
def service_factory():
    """Create a fresh ServiceFactory instance for testing."""
    # Reset the singleton instance for clean tests
    ServiceFactory._instance = None
    return ServiceFactory.get_instance()


def test_inheritance():
    """Test that ServiceFactory inherits from IServiceFactory."""
    assert issubclass(ServiceFactory, IServiceFactory)


def test_instance_type():
    """Test that ServiceFactory instance is an instance of IServiceFactory."""
    factory = ServiceFactory.get_instance()
    assert isinstance(factory, IServiceFactory)


def test_singleton_pattern():
    """Test that ServiceFactory implements the singleton pattern correctly."""
    # Get the instance
    factory1 = ServiceFactory.get_instance()

    # Get it again
    factory2 = ServiceFactory.get_instance()

    # They should be the same instance
    assert factory1 is factory2

    # And the class variable should be set
    assert ServiceFactory._instance is factory1


def test_register_service(service_factory):
    """Test the register_service method."""

    # Create a test class
    class TestInterface:
        pass

    class TestImplementation(TestInterface):
        pass

    # Register the service
    test_implementation = TestImplementation()
    service_factory.register_service(TestInterface, test_implementation)

    # Verify the service was registered
    service = service_factory.get_service(TestInterface)
    assert service is test_implementation
    assert isinstance(service, TestImplementation)


def test_get_service(service_factory):
    """Test the get_service method."""

    # Create a test class
    class TestInterface:
        pass

    class TestImplementation(TestInterface):
        pass

    # Register the service
    test_instance = TestImplementation()
    service_factory.register_service(TestInterface, test_instance)

    # Get the service
    service = service_factory.get_service(TestInterface)

    # Verify the service is the same instance
    assert service is test_instance


def test_get_service_exception():
    """Test that get_service raises an exception for unregistered services."""
    # Reset factory to ensure it's clean
    ServiceFactory._instance = None
    factory = ServiceFactory.get_instance()

    # Create a test class that's not registered
    class UnregisteredInterface:
        pass

    # Attempt to get the service
    with pytest.raises(ValueError):
        factory.get_service(UnregisteredInterface)


def test_helper_functions():
    """Test the helper functions for service access."""
    # Reset the factory for clean test
    ServiceFactory._instance = None
    factory = ServiceFactory.get_instance()

    # Create mock implementations
    class MockDataStore(IDataStore):
        def get_entries(self):
            return pd.DataFrame()

        def set_entries(self, entries_df, source="", emit_event=True):
            return True

        def get_validation_list(self, list_type):
            return pd.DataFrame()

        def set_validation_list(self, list_type, entries_df):
            return True

        def add_validation_entry(self, list_type, entry):
            return True

        def remove_validation_entry(self, list_type, entry):
            return True

        def get_correction_rules(self):
            return pd.DataFrame()

        def set_correction_rules(self, rules_df):
            return True

        def begin_transaction(self):
            return True

        def commit_transaction(self):
            return True

        def rollback_transaction(self):
            return True

        def subscribe(self, event_type, handler):
            pass

        def unsubscribe(self, event_type, handler):
            pass

    class MockFileService(IFileService):
        def load_entries(self, file_path):
            pass

        def save_entries(self, file_path):
            pass

        def load_correction_rules(self, file_path):
            pass

        def save_correction_rules(self, file_path):
            pass

        def load_validation_list(self, list_type, file_path):
            pass

        def save_validation_list(self, list_type, file_path):
            pass

        def get_default_directory(self):
            return ""

        def set_default_directory(self, directory):
            pass

    class MockCorrectionService(ICorrectionService):
        def apply_corrections(self, specific_entries=None):
            return {"applied": 0, "total": 0}

        def apply_specific_correction(self, entry_id, field, from_text, to_text):
            return True

        def reset_corrections(self, entry_ids=None):
            return {"reset": 0, "total": 0}

        def add_correction_rule(
            self,
            field,
            incorrect_value,
            correct_value,
            case_sensitive=True,
            match_type="exact",
            enabled=True,
        ):
            return True

    class MockValidationService(IValidationService):
        def validate_entries(self, specific_entries=None):
            return {"valid": 0, "invalid": 0, "total": 0}

        def get_invalid_entries(self):
            return []

    class MockConfigManager(IConfigManager):
        # Base methods
        def get_config(self, section, key, default=None):
            return default

        def set_config(self, section, key, value):
            pass

        def save_config(self):
            return True

        def load_config(self):
            return True

        # Interface-specific methods
        def get_value(self, section, key, default=None):
            return default

        def set_value(self, section, key, value):
            return True

        def get_section(self, section):
            return {}

        def get_str(self, section, key, fallback=""):
            return fallback

        def get_int(self, section, key, fallback=0):
            return fallback

        def get_bool(self, section, key, fallback=False):
            return fallback

    # Register the mock services
    factory.register_service(IDataStore, MockDataStore())
    factory.register_service(IFileService, MockFileService())
    factory.register_service(ICorrectionService, MockCorrectionService())
    factory.register_service(IValidationService, MockValidationService())
    factory.register_service(IConfigManager, MockConfigManager())

    # Test the helper functions
    assert isinstance(get_dataframe_store(), IDataStore)
    assert isinstance(get_file_service(), IFileService)
    assert isinstance(get_correction_service(), ICorrectionService)
    assert isinstance(get_validation_service(), IValidationService)
    assert isinstance(get_config_manager(), IConfigManager)

    # Test the generic get_service function
    assert isinstance(get_service(IDataStore), IDataStore)
    assert isinstance(get_service(IFileService), IFileService)
    assert isinstance(get_service(ICorrectionService), ICorrectionService)
    assert isinstance(get_service(IValidationService), IValidationService)
    assert isinstance(get_service(IConfigManager), IConfigManager)


def test_method_signature_compliance():
    """Test that all methods have the correct signatures according to the interface."""
    # Define expected method signatures
    expected_methods = {
        "register_service": {"args": ["interface_type", "implementation"]},
        "get_service": {"args": ["interface_type"]},
    }

    # Verify methods have correct signatures
    for method_name, expected in expected_methods.items():
        # Verify method exists
        assert hasattr(ServiceFactory, method_name), f"Method {method_name} is missing"

        # Get the method
        method = getattr(ServiceFactory, method_name)

        # Check if method is callable
        assert callable(method), f"{method_name} is not callable"

        # Check required arguments if specified (skipping self)
        if "args" in expected:
            method_args = method.__code__.co_varnames[1 : method.__code__.co_argcount]
            for arg in expected["args"]:
                assert arg in method_args, (
                    f"Method {method_name} is missing required argument {arg}"
                )
