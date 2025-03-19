#!/usr/bin/env python3
"""
interface_architecture_demo.py

Description: Demonstrates the interface-based architecture and dependency injection
Usage:
    python -m src.interface_architecture_demo
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("interface_architecture_demo")

# Import interfaces
from src.interfaces import (
    IServiceFactory,
    IDataStore,
    IFileService,
    ICorrectionService,
    IValidationService,
    IConfigManager,
    EventType,
)

# Import implementations
from src.app_bootstrapper import AppBootstrapper
from src.services.service_factory import ServiceFactory
from src.models.validation_list import ValidationList


def handle_entries_updated(data: Dict[str, Any]) -> None:
    """
    Handle entries updated event.

    Args:
        data: Event data
    """
    count = data.get("count", 0)
    logger.info(f"Entries updated: {count} entries")


def run_demo() -> None:
    """
    Run a demonstration of the interface-based architecture and dependency injection.
    """
    logger.info("Starting interface-based architecture demo")

    # Initialize the application
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()

    # Get services through interfaces
    service_factory: IServiceFactory = bootstrapper.get_service_factory()
    data_store: IDataStore = service_factory.get_data_store()
    file_service: IFileService = service_factory.get_file_service()
    validation_service: IValidationService = service_factory.get_validation_service()
    config_manager: IConfigManager = bootstrapper.get_config_manager()

    # Subscribe to events
    data_store.subscribe(EventType.ENTRIES_UPDATED, handle_entries_updated)

    # Create a validation list using the interface-based approach
    player_list = ValidationList(
        list_type="player",
        entries=["Player1", "Player2", "Player3"],
        name="Demo Player List",
        config_manager=config_manager,  # Pass the interface
    )
    logger.info(f"Created ValidationList with {player_list.count()} entries")

    # Test validation
    test_name = "Player1"
    is_valid, confidence, matched = player_list.is_valid(test_name)
    logger.info(
        f"Testing validation for '{test_name}': valid={is_valid}, confidence={confidence:.2f}"
    )

    # Enable fuzzy matching
    player_list.use_fuzzy_matching = True

    # Set fuzzy threshold through config manager
    config_manager.set_value("Validation", "fuzzy_threshold", 50)  # 50%

    # Test fuzzy matching
    test_name = "Playr1"  # Intentional typo
    is_valid, confidence, matched = player_list.is_valid(test_name)
    logger.info(
        f"Testing fuzzy match for '{test_name}': valid={is_valid}, confidence={confidence:.2f}, matched='{matched}'"
    )

    # Create sample data file path
    sample_data_path = Path("sample_data.txt")
    if not sample_data_path.exists():
        # Create a sample data file
        with open(sample_data_path, "w", encoding="utf-8") as f:
            f.write("Forgotten Chest\n")
            f.write("From: Engelchen\n")
            f.write("Source: Level 15 Crypt\n")
            f.write("Rare Dragon Chest\n")
            f.write("From: Engelchen\n")
            f.write("Source: Level 15 rare Crypt\n")
        logger.info(f"Created sample data file at {sample_data_path}")

    # Try loading entries using FileService through interface
    logger.info(f"Loading entries from {sample_data_path}")
    total_entries, valid_entries = file_service.load_entries_from_file(str(sample_data_path))
    logger.info(f"Loaded {total_entries} entries, {valid_entries} valid")

    # Get entries from DataStore through interface
    entries_df = data_store.get_entries()
    logger.info(f"Retrieved {len(entries_df)} entries from data store")

    # Create a validation list and add to data store
    data_store.set_validation_list("player", ["Engelchen", "Player1", "Player2"])
    player_names = data_store.get_validation_list("player")
    logger.info(f"Player validation list: {player_names}")

    # Validate entries using ValidationService through interface
    valid_count, invalid_count = validation_service.validate_entries()
    logger.info(f"Validation result: {valid_count} valid, {invalid_count} invalid entries")

    # Clean up
    if sample_data_path.exists():
        sample_data_path.unlink()
        logger.info(f"Removed sample data file {sample_data_path}")

    logger.info("Interface-based architecture and dependency injection demo completed successfully")


if __name__ == "__main__":
    run_demo()
