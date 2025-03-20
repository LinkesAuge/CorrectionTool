#!/usr/bin/env python3
"""
test_bootstrapping.py

Description: Tests the AppBootstrapper and service initialization
Usage:
    python test_bootstrapping.py
"""

import logging
import sys
from typing import Dict, Any, Type

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Import interfaces
from src.interfaces import (
    IDataStore,
    IFileService,
    ICorrectionService,
    IValidationService,
    IServiceFactory,
    IConfigManager,
)

# Import bootstrapper
from src.app_bootstrapper import AppBootstrapper


def test_bootstrapper():
    """
    Test that the AppBootstrapper initializes correctly.
    """
    logger.info("Testing AppBootstrapper initialization...")

    # Create and initialize bootstrapper
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()

    logger.info("AppBootstrapper initialized successfully.")

    # Now test service resolution
    try:
        # Test getting each service type
        data_store = bootstrapper.get_service(IDataStore)
        file_service = bootstrapper.get_service(IFileService)
        correction_service = bootstrapper.get_service(ICorrectionService)
        validation_service = bootstrapper.get_service(IValidationService)
        service_factory = bootstrapper.get_service(IServiceFactory)
        config_manager = bootstrapper.get_service(IConfigManager)

        # Log successful resolutions
        logger.info(f"Resolved IDataStore: {data_store.__class__.__name__}")
        logger.info(f"Resolved IFileService: {file_service.__class__.__name__}")
        logger.info(f"Resolved ICorrectionService: {correction_service.__class__.__name__}")
        logger.info(f"Resolved IValidationService: {validation_service.__class__.__name__}")
        logger.info(f"Resolved IServiceFactory: {service_factory.__class__.__name__}")
        logger.info(f"Resolved IConfigManager: {config_manager.__class__.__name__}")

        # Test that service factory has all services registered
        for interface_type in [
            IDataStore,
            IFileService,
            ICorrectionService,
            IValidationService,
            IConfigManager,
        ]:
            implementation = service_factory.resolve_service(interface_type)
            logger.info(
                f"ServiceFactory resolved {interface_type.__name__}: "
                f"{implementation.__class__.__name__}"
            )

        logger.info("All service resolutions successful!")
        return True
    except Exception as e:
        logger.error(f"Error resolving services: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("Starting bootstrapper test...")
    success = test_bootstrapper()
    if success:
        logger.info("All tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("Tests failed!")
        sys.exit(1)
