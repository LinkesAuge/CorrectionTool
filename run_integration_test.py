#!/usr/bin/env python3
"""
run_integration_test.py

Description: Run the integration test to verify the data management system works correctly
Usage:
    python run_integration_test.py
"""

import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Running integration test")

    try:
        # Run the integration test script which already works
        import src.integration_test

        logger.info("Integration test completed successfully")
    except Exception as e:
        logger.error(f"Error running integration test: {e}", exc_info=True)
        sys.exit(1)
