"""
simple_test.py

Description: Simple test for service factory and service retrieval
"""

import logging
import traceback
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    try:
        logger.info("Starting simple test of service factory and service retrieval")

        # Import AppBootstrapper
        from src.app_bootstrapper import AppBootstrapper

        # Import interfaces
        from src.interfaces.i_data_store import IDataStore
        from src.interfaces.i_file_service import IFileService
        from src.interfaces.i_validation_service import IValidationService
        from src.interfaces.i_correction_service import ICorrectionService
        from src.interfaces.i_service_factory import IServiceFactory

        # Initialize bootstrapper
        logger.info("Initializing bootstrapper")
        bootstrapper = AppBootstrapper()
        bootstrapper.initialize()

        # Test service factory
        logger.info("Testing service factory")
        service_factory = bootstrapper.service_factory

        # Try to get services
        logger.info("Retrieving services:")

        data_store = service_factory.get_service(IDataStore)
        logger.info(f"- DataStore: {data_store.__class__.__name__}")

        file_service = service_factory.get_service(IFileService)
        logger.info(f"- FileService: {file_service.__class__.__name__}")

        validation_service = service_factory.get_service(IValidationService)
        logger.info(f"- ValidationService: {validation_service.__class__.__name__}")

        correction_service = service_factory.get_service(ICorrectionService)
        logger.info(f"- CorrectionService: {correction_service.__class__.__name__}")

        # Test service interface methods
        logger.info("Testing ValidationService interface methods")
        validation_methods = [
            method for method in dir(validation_service) if not method.startswith("_")
        ]
        logger.info(f"ValidationService methods: {validation_methods}")

        logger.info("Testing CorrectionService interface methods")
        correction_methods = [
            method for method in dir(correction_service) if not method.startswith("_")
        ]
        logger.info(f"CorrectionService methods: {correction_methods}")

        # Test specific method exists
        logger.info("Testing if add_correction_rule method exists")
        has_method = hasattr(correction_service, "add_correction_rule")
        logger.info(f"CorrectionService has add_correction_rule: {has_method}")

        if not has_method:
            logger.error("Method 'add_correction_rule' doesn't exist on correction_service!")
            logger.info(f"Type of correction_service: {type(correction_service)}")
            logger.info(f"Class hierarchy: {correction_service.__class__.__mro__}")

        logger.info("Simple test completed")
        return 0

    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
