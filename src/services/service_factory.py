"""
service_factory.py

Description: Factory for creating and accessing services using dependency injection
Usage:
    from src.services.service_factory import ServiceFactory
    from src.interfaces.i_data_store import IDataStore
    factory = ServiceFactory()
    data_store = factory.get_service(IDataStore)
"""

import logging
from typing import Dict, Any, Optional, Type, TypeVar

from src.interfaces.i_service_factory import IServiceFactory

# Type variable for generic service types
T = TypeVar("T")


class ServiceFactory(IServiceFactory):
    """
    Factory for creating and accessing services using dependency injection.

    This class provides centralized access to all services through their interfaces,
    ensuring they are properly registered and resolved.

    Attributes:
        _services: Dictionary of service instances by interface type
        _logger: Logger instance

    Implementation Notes:
        - Implements dependency injection pattern
        - Manages service registrations by interface type
        - Provides type-safe service resolution
    """

    def __init__(self):
        """
        Initialize the ServiceFactory.
        """
        # Initialize dictionary for services
        self._services = {}

        # Setup logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("ServiceFactory initialized")

    def register_service(self, interface_type: Type[T], implementation: T) -> None:
        """
        Register a service implementation for an interface.

        Args:
            interface_type: Interface type (class) to register
            implementation: Implementation instance
        """
        self._services[interface_type] = implementation
        self._logger.debug(f"Registered service: {interface_type.__name__}")

    def get_service(self, interface_type: Type[T]) -> T:
        """
        Get a service by its interface type.

        Args:
            interface_type: Interface type to resolve

        Returns:
            Implementation of the requested interface

        Raises:
            ValueError: If no implementation is registered for the interface
        """
        if interface_type not in self._services:
            raise ValueError(f"No implementation registered for {interface_type.__name__}")

        return self._services[interface_type]
