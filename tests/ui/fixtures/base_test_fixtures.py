"""
base_test_fixtures.py

Description: Base test fixtures for UI testing with pytest-qt
Usage:
    from tests.ui.fixtures.base_test_fixtures import qtbot_fixture, default_services

    def test_validation_list_widget(qtbot_fixture, default_services):
        # Test implementation using fixtures
"""

import os
import pytest
import pandas as pd
from typing import Dict, Any

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from tests.ui.helpers.mock_services import (
    MockDataStore,
    MockConfigManager,
    MockFileService,
    MockCorrectionService,
    MockValidationService,
    MockServiceFactory,
)


@pytest.fixture
def qtbot_fixture(qtbot):
    """
    A pytest fixture that provides a qtbot instance for testing.

    Args:
        qtbot: The built-in qtbot fixture from pytest-qt

    Returns:
        The qtbot instance
    """
    return qtbot


@pytest.fixture
def default_services():
    """
    Creates a set of default mock services for testing.

    Returns:
        Dict[str, Any]: Dictionary of service instances
    """
    # Create mock services
    mock_data_store = MockDataStore()
    mock_config_manager = MockConfigManager()
    mock_file_service = MockFileService()
    mock_correction_service = MockCorrectionService()
    mock_validation_service = MockValidationService()
    mock_service_factory = MockServiceFactory()

    # Set up the service factory
    mock_service_factory.register_service("data_store", mock_data_store)
    mock_service_factory.register_service("config_manager", mock_config_manager)
    mock_service_factory.register_service("file_service", mock_file_service)
    mock_service_factory.register_service("correction_service", mock_correction_service)
    mock_service_factory.register_service("validation_service", mock_validation_service)

    # Return the services
    return {
        "data_store": mock_data_store,
        "config_manager": mock_config_manager,
        "file_service": mock_file_service,
        "correction_service": mock_correction_service,
        "validation_service": mock_validation_service,
        "service_factory": mock_service_factory,
    }


@pytest.fixture
def sample_validation_list_data():
    """
    Creates sample validation list data for testing.

    Returns:
        Dict[str, list]: Dictionary of validation list data
    """
    return {
        "players": ["Player 1", "Player 2", "Player 3", "Player 4", "Player 5"],
        "chest_types": ["Common", "Rare", "Epic", "Legendary"],
        "sources": ["Arena", "War", "Challenge", "Trophy Road", "Shop"],
    }


@pytest.fixture
def sample_correction_rules():
    """
    Creates sample correction rules for testing.

    Returns:
        List[dict]: List of correction rule dictionaries
    """
    return [
        {"from": "plyr1", "to": "Player 1", "type": "player", "enabled": True},
        {"from": "plyr2", "to": "Player 2", "type": "player", "enabled": True},
        {"from": "Comn", "to": "Common", "type": "chest_type", "enabled": True},
        {"from": "Rar", "to": "Rare", "type": "chest_type", "enabled": True},
        {"from": "Epik", "to": "Epic", "type": "chest_type", "enabled": False},
    ]


@pytest.fixture
def sample_data_frame():
    """
    Creates a sample DataFrame for testing.

    Returns:
        pd.DataFrame: Sample data
    """
    data = {
        "player": ["Player 1", "plyr2", "Player 3", "Unknown Player"],
        "chest_type": ["Common", "Rar", "Epic", "Unknown Type"],
        "source": ["Arena", "War", "Unknown Source", "Shop"],
        "quantity": [1, 2, 3, 4],
        "date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def setup_validation_lists(default_services, sample_validation_list_data):
    """
    Sets up validation lists in the data store.

    Args:
        default_services: Dictionary of mock services
        sample_validation_list_data: Sample validation list data

    Returns:
        Dict[str, Any]: Dictionary of services with validation lists set up
    """
    data_store = default_services["data_store"]

    # Add validation lists to data store
    for list_name, items in sample_validation_list_data.items():
        data_store.add_validation_list(list_name, items)

    return default_services


@pytest.fixture
def setup_correction_rules(default_services, sample_correction_rules):
    """
    Sets up correction rules in the correction service.

    Args:
        default_services: Dictionary of mock services
        sample_correction_rules: Sample correction rules

    Returns:
        Dict[str, Any]: Dictionary of services with correction rules set up
    """
    correction_service = default_services["correction_service"]

    # Set correction rules
    correction_service.set_correction_rules(sample_correction_rules)

    return default_services


@pytest.fixture
def setup_data(default_services, sample_data_frame):
    """
    Sets up data in the data store.

    Args:
        default_services: Dictionary of mock services
        sample_data_frame: Sample DataFrame

    Returns:
        Dict[str, Any]: Dictionary of services with data set up
    """
    data_store = default_services["data_store"]

    # Set data in data store
    data_store.set_data(sample_data_frame)

    return default_services


@pytest.fixture
def setup_all(setup_validation_lists, setup_correction_rules, setup_data):
    """
    Sets up all test data in the mock services.

    Args:
        setup_validation_lists: Fixture that sets up validation lists
        setup_correction_rules: Fixture that sets up correction rules
        setup_data: Fixture that sets up data

    Returns:
        Dict[str, Any]: Dictionary of services with all test data set up
    """
    # The setup_validation_lists fixture already contains the services dictionary
    # and has been modified by all other setup fixtures
    return setup_validation_lists
