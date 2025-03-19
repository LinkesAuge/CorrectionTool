"""
demo.py

Description: Demonstration of interface-based architecture
Usage:
    python -m src.interfaces.demo
"""

import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("interface_demo")

# Import interfaces
from src.interfaces import (
    IDataStore,
    IFileService,
    ICorrectionService,
    IValidationService,
    IConfigManager,
)

# Import concrete implementations
from src.services.config_manager import ConfigManager
from src.services.dataframe_store import DataFrameStore
from src.models.validation_list import ValidationList


def run_demo():
    """
    Run a demonstration of interface-based architecture.
    """
    logger.info("Starting interface-based architecture demo")

    # Create ConfigManager using the interface
    config: IConfigManager = ConfigManager()
    logger.info(f"Created ConfigManager instance: {config}")

    # Use the interface methods
    logger.info(f"App name from config: {config.get_str('General', 'app_name', 'Default App')}")

    # Create a ValidationList using the interface
    player_list = ValidationList(
        list_type="player",
        entries=["Player1", "Player2", "Player3"],
        name="Demo Player List",
        use_fuzzy_matching=True,
        config_manager=config,  # Pass the interface instead of concrete class
    )
    logger.info(f"Created ValidationList with {player_list.count()} entries")

    # Test validation
    test_name = "Player1"
    is_valid, confidence, matched = player_list.is_valid(test_name)
    logger.info(f"Validation test for '{test_name}': valid={is_valid}, confidence={confidence:.2f}")

    # Test fuzzy matching
    test_name = "Playr1"  # Misspelled
    is_valid, confidence, matched = player_list.is_valid(test_name)
    logger.info(
        f"Fuzzy match test for '{test_name}': valid={is_valid}, confidence={confidence:.2f}, matched='{matched}'"
    )

    # DataFrameStore can be accessed through IDataStore interface
    # This would typically be done through a ServiceFactory
    logger.info("Interface-based architecture demo completed successfully")


if __name__ == "__main__":
    run_demo()
