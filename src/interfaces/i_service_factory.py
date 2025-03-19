"""
i_service_factory.py

Description: Interface for the service factory
Usage:
    from src.interfaces.i_service_factory import IServiceFactory
    from src.interfaces.i_data_store import IDataStore
    service_factory = get_service_factory()
    data_store = service_factory.get_service(IDataStore)
"""

from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar

T = TypeVar("T")


class IServiceFactory(ABC):
    """
    Interface for the service factory.

    This interface defines methods for registering and retrieving services.
    """

    @abstractmethod
    def register_service(self, interface_type: Type[T], implementation: T) -> None:
        """
        Register a service implementation for an interface.

        Args:
            interface_type: The interface type
            implementation: The implementation instance
        """
        pass

    @abstractmethod
    def get_service(self, interface_type: Type[T]) -> T:
        """
        Get a service implementation for an interface.

        Args:
            interface_type: The interface type

        Returns:
            T: The service implementation

        Raises:
            ValueError: If no implementation is registered for the interface
        """
        pass
