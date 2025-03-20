"""
app_bootstrapper.py

Description: Bootstrapper for the application that initializes services and UI components
Usage:
    from src.app_bootstrapper import AppBootstrapper
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()
"""

import logging
from typing import Dict, Any, Type

# Import interface types
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_correction_service import ICorrectionService
from src.interfaces.i_validation_service import IValidationService
from src.interfaces.i_service_factory import IServiceFactory
from src.interfaces.i_config_manager import IConfigManager
from src.interfaces.i_filter import IFilterManager

# Import concrete service implementations
from src.services.config_manager import ConfigManager
from src.services.dataframe_store import DataFrameStore
from src.services.file_service import FileService
from src.services.validation_service import ValidationService
from src.services.correction_service import CorrectionService
from src.services.service_factory import ServiceFactory
from src.services.filters.filter_manager import FilterManager


class AppBootstrapper:
    """
    Application bootstrapper for initializing services and UI components.

    This class is responsible for initializing all services in the correct order
    and registering them with the service factory.

    Attributes:
        service_factory: ServiceFactory instance
        _logger: Logger instance
        _initialized: Flag indicating if bootstrapper has been initialized

    Implementation Notes:
        - Handles dependency injection for services
        - Initializes services in the correct order
        - Registers services with the service factory
        - Provides methods for resolving service implementations
    """

    def __init__(self):
        """
        Initialize the AppBootstrapper.
        """
        self._logger = logging.getLogger(__name__)
        self.service_factory = None
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize the application, setting up all services and configurations.
        """
        if self._initialized:
            self._logger.warning("AppBootstrapper already initialized. Skipping.")
            return

        self._logger.info("Initializing application...")

        # Initialize services in the correct order
        self._initialize_config_manager()
        self._initialize_data_store()
        self._initialize_services()
        self._initialize_filter_manager()

        # Register all services with the service factory
        self._register_services_with_factory()

        self._initialized = True
        self._logger.info("Application initialized successfully.")

    def _initialize_config_manager(self) -> None:
        """
        Initialize the configuration manager.
        """
        self._logger.info("Initializing ConfigManager...")

        # Create the config manager
        config_manager = ConfigManager()

        # Get the service factory singleton and register the config manager
        self.service_factory = ServiceFactory.get_instance()
        self.service_factory.register_service(IConfigManager, config_manager)

    def _initialize_data_store(self) -> None:
        """
        Initialize the data store.
        """
        self._logger.info("Initializing DataFrameStore...")

        # Get the config manager from the service factory
        config_manager = self.service_factory.get_service(IConfigManager)

        # Create the DataFrameStore with dependency injection
        data_store = DataFrameStore.get_instance()

        # Register as IDataStore implementation
        self.service_factory.register_service(IDataStore, data_store)

    def _initialize_services(self) -> None:
        """
        Initialize service layer components.
        """
        self._logger.info("Initializing services...")

        # Get dependencies
        data_store = self.service_factory.get_service(IDataStore)

        # Create service instances with dependency injection
        file_service = FileService(data_store)
        validation_service = ValidationService(data_store)
        correction_service = CorrectionService(data_store)

        # Register services with the service factory
        self.service_factory.register_service(IServiceFactory, self.service_factory)
        self.service_factory.register_service(IFileService, file_service)
        self.service_factory.register_service(IValidationService, validation_service)
        self.service_factory.register_service(ICorrectionService, correction_service)

    def _initialize_filter_manager(self) -> None:
        """
        Initialize the filter manager.
        """
        self._logger.info("Initializing FilterManager...")

        # Create the filter manager
        filter_manager = FilterManager()

        # Load filter state from config if available
        config_manager = self.service_factory.get_service(IConfigManager)
        filter_manager.load_filter_state(config_manager)

        # Register as IFilterManager implementation
        self.service_factory.register_service(IFilterManager, filter_manager)

    def _register_services_with_factory(self) -> None:
        """
        Register all services with the service factory.
        """
        self._logger.info("Registering services with ServiceFactory...")

        # Log all registered services for debugging
        services = [
            IConfigManager,
            IDataStore,
            IServiceFactory,
            IFileService,
            IValidationService,
            ICorrectionService,
            IFilterManager,
        ]

        for service_type in services:
            self._logger.debug(f"Registering service: {service_type.__name__}")

        self._logger.debug(f"Registered {len(services)} services with ServiceFactory.")
