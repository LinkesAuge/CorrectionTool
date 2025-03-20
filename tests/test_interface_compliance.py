"""
test_interface_compliance.py

Description: Comprehensive tests to verify interface compliance across implementations
Usage:
    python -m pytest tests/test_interface_compliance.py
"""

import pytest
import inspect
import logging
from abc import abstractmethod
import importlib
import pkgutil
from typing import Dict, List, Type, Set, Any

# Import core interfaces
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_correction_service import ICorrectionService
from src.interfaces.i_validation_service import IValidationService
from src.interfaces.i_config_manager import IConfigManager
from src.interfaces.i_service_factory import IServiceFactory

# Import implementations
from src.services.dataframe_store import DataFrameStore
from src.services.file_service import FileService
from src.services.correction_service import CorrectionService
from src.services.validation_service import ValidationService
from src.services.config_manager import ConfigManager
from src.services.service_factory import ServiceFactory

# Import bootstrapper for testing with real instances
from src.app_bootstrapper import AppBootstrapper

# Import service helpers
from src.services import get_service

# Setup logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Interface-implementation pairs to test
INTERFACE_IMPLEMENTATIONS = [
    (IDataStore, DataFrameStore),
    (IFileService, FileService),
    (ICorrectionService, CorrectionService),
    (IValidationService, ValidationService),
    (IConfigManager, ConfigManager),
    (IServiceFactory, ServiceFactory),
]


def get_abstract_methods(interface_class: Type) -> Set[str]:
    """Get all abstract methods from an interface class."""
    abstract_methods = set()

    for name, method in inspect.getmembers(interface_class, predicate=inspect.isfunction):
        if getattr(method, "__isabstractmethod__", False):
            abstract_methods.add(name)

    return abstract_methods


def get_method_signature(cls: Type, method_name: str) -> inspect.Signature:
    """Get the signature of a method from a class."""
    method = getattr(cls, method_name)
    return inspect.signature(method)


def test_interface_implementation_completeness():
    """Test that all interfaces are completely implemented."""
    for interface, implementation in INTERFACE_IMPLEMENTATIONS:
        # Get all abstract methods from the interface
        abstract_methods = get_abstract_methods(interface)

        # Check if the implementation implements all abstract methods
        for method_name in abstract_methods:
            assert hasattr(implementation, method_name), (
                f"Implementation {implementation.__name__} is missing method '{method_name}' "
                f"required by interface {interface.__name__}"
            )


def test_method_signature_compatibility():
    """Test that all implemented methods have compatible signatures with their interface definitions."""
    for interface, implementation in INTERFACE_IMPLEMENTATIONS:
        # Get all abstract methods from the interface
        abstract_methods = get_abstract_methods(interface)

        # Check if the implementation's method signatures are compatible with the interface
        for method_name in abstract_methods:
            interface_sig = get_method_signature(interface, method_name)
            implementation_sig = get_method_signature(implementation, method_name)

            # Check return type annotation
            if interface_sig.return_annotation != inspect.Signature.empty:
                assert implementation_sig.return_annotation != inspect.Signature.empty, (
                    f"Method '{implementation.__name__}.{method_name}' is missing return type annotation "
                    f"required by interface {interface.__name__}"
                )

            # Check parameter compatibility
            for param_name, param in interface_sig.parameters.items():
                # Skip 'self' parameter
                if param_name == "self":
                    continue

                # Check if parameter exists in implementation
                assert param_name in implementation_sig.parameters, (
                    f"Method '{implementation.__name__}.{method_name}' is missing "
                    f"parameter '{param_name}' required by interface {interface.__name__}"
                )

                # Check if parameter has default value if required by interface
                impl_param = implementation_sig.parameters[param_name]
                if param.default is not param.empty:
                    assert impl_param.default is not impl_param.empty, (
                        f"Parameter '{param_name}' in '{implementation.__name__}.{method_name}' "
                        f"should have a default value as required by interface {interface.__name__}"
                    )


def test_verify_interface_instances():
    """Test that service instances are proper instances of their interfaces."""
    # Initialize app bootstrapper
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()

    # Test each interface-implementation pair
    for interface, _ in INTERFACE_IMPLEMENTATIONS:
        # Get service instance
        service = get_service(interface)

        # Verify it's an instance of the interface
        assert isinstance(service, interface), (
            f"Service {service.__class__.__name__} is not an instance of interface {interface.__name__}"
        )


def test_interface_inheritance():
    """Test that implementations properly inherit from their interfaces."""
    for interface, implementation in INTERFACE_IMPLEMENTATIONS:
        # Check if implementation inherits from interface
        assert issubclass(implementation, interface), (
            f"Implementation {implementation.__name__} does not inherit from interface {interface.__name__}"
        )


def test_discover_missing_interface_implementations():
    """Test to discover any implementations that don't properly implement an interface."""
    # Import all modules in the services package
    import src.services

    # Get all classes in the services package
    service_classes = []
    for _, name, _ in pkgutil.iter_modules(src.services.__path__, f"{src.services.__name__}."):
        try:
            module = importlib.import_module(name)
            for class_name, cls in inspect.getmembers(module, inspect.isclass):
                if cls.__module__ == name:
                    service_classes.append(cls)
        except ImportError:
            logger.warning(f"Could not import module {name}")

    # Get all interfaces in the interfaces package
    import src.interfaces

    interfaces = []
    for _, name, _ in pkgutil.iter_modules(src.interfaces.__path__, f"{src.interfaces.__name__}."):
        try:
            module = importlib.import_module(name)
            for class_name, cls in inspect.getmembers(module, inspect.isclass):
                if cls.__module__ == name and hasattr(cls, "__abstractmethods__"):
                    interfaces.append(cls)
        except ImportError:
            logger.warning(f"Could not import module {name}")

    # Report any service classes that might be missing interface implementations
    for cls in service_classes:
        # Skip classes that are already in our test pairs
        if any(cls == impl for _, impl in INTERFACE_IMPLEMENTATIONS):
            continue

        # Check if this class looks like it should implement an interface
        if (
            cls.__name__.endswith("Service")
            or cls.__name__.endswith("Manager")
            or cls.__name__.endswith("Store")
        ):
            # Find potential interfaces it should implement
            potential_interfaces = []
            for interface in interfaces:
                if interface.__name__.lower().replace("i_", "") in cls.__name__.lower():
                    potential_interfaces.append(interface)

            if potential_interfaces:
                implemented = False
                for interface in potential_interfaces:
                    if issubclass(cls, interface):
                        implemented = True
                        break

                if not implemented:
                    logger.warning(
                        f"Class {cls.__name__} looks like it should implement one of these interfaces: "
                        f"{[i.__name__ for i in potential_interfaces]}, but it doesn't"
                    )


def test_interface_attribute_compliance():
    """Test that implementations have all expected attributes defined in interfaces."""
    for interface, implementation in INTERFACE_IMPLEMENTATIONS:
        # Get all properties and methods from the interface
        interface_attrs = set(dir(interface))

        # Exclude private attributes and common Python attributes
        interface_attrs = {
            attr
            for attr in interface_attrs
            if not attr.startswith("_") and attr not in ["register", "abstractmethod"]
        }

        # Check if the implementation has all the interface attributes
        for attr in interface_attrs:
            assert hasattr(implementation, attr), (
                f"Implementation {implementation.__name__} is missing attribute '{attr}' "
                f"defined in interface {interface.__name__}"
            )


def test_runtime_behavior():
    """Test that implementations behave as expected at runtime."""
    # Initialize app bootstrapper
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()

    # Test data store interface
    data_store = get_service(IDataStore)

    # Test basic operations
    # Get entries
    entries = data_store.get_entries()
    assert entries is not None

    # Test transaction methods
    assert data_store.begin_transaction() is True
    assert data_store.rollback_transaction() is True

    # Test service factory interface
    service_factory = get_service(IServiceFactory)

    # Test getting a service
    service = service_factory.get_service(IDataStore)
    assert service is not None
    assert isinstance(service, IDataStore)
