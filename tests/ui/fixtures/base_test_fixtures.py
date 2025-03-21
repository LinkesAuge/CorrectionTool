"""
base_test_fixtures.py

Description: Common pytest fixtures for UI testing
Usage:
    Import these fixtures in UI test files
"""

import pytest
import pandas as pd
from typing import Dict, Any, List
from PyQt5.QtCore import QObject

from tests.ui.helpers.mock_services import (
    MockCorrectionService,
    MockValidationService,
    MockDataStore,
    MockServiceFactory,
)


@pytest.fixture
def qtbot_fixture(qtbot):
    """
    Provide a qtbot fixture for UI testing.

    Args:
        qtbot: The pytest-qt bot fixture

    Returns:
        qtbot: The configured qtbot instance
    """
    return qtbot


@pytest.fixture
def sample_validation_list_data() -> Dict[str, List[str]]:
    """
    Provide sample validation list data for testing.

    Returns:
        Dict[str, List[str]]: Dictionary containing validation lists
    """
    return {
        "players": ["Player 1", "Player 2", "Player 3"],
        "teams": ["Team A", "Team B", "Team C"],
        "competitions": ["League 1", "Cup", "International"],
    }


@pytest.fixture
def sample_correction_rules() -> List[Dict[str, Any]]:
    """
    Provide sample correction rules for testing.

    Returns:
        List[Dict[str, Any]]: List of correction rule dictionaries
    """
    return [
        {"from": "Player 1", "to": "Player One", "enabled": True},
        {"from": "Team A", "to": "Team Alpha", "enabled": True},
        {"from": "League 1", "to": "Premier League", "enabled": False},
    ]


@pytest.fixture
def sample_data_frame() -> pd.DataFrame:
    """
    Provide a sample DataFrame for testing.

    Returns:
        pd.DataFrame: Sample data for testing
    """
    data = {
        "player": ["Player 1", "Player 2", "Player 3"],
        "team": ["Team A", "Team B", "Team C"],
        "competition": ["League 1", "Cup", "International"],
        "score": [1, 2, 3],
    }
    return pd.DataFrame(data)


@pytest.fixture
def default_services() -> Dict[str, Any]:
    """
    Provide default mock services for testing.

    Returns:
        Dict[str, Any]: Dictionary containing mock services
    """
    correction_service = MockCorrectionService()
    validation_service = MockValidationService()
    data_store = MockDataStore()

    service_factory = MockServiceFactory(
        correction_service=correction_service,
        validation_service=validation_service,
        data_store=data_store,
    )

    return {
        "correction_service": correction_service,
        "validation_service": validation_service,
        "data_store": data_store,
        "service_factory": service_factory,
    }


@pytest.fixture
def setup_validation_lists(default_services, sample_validation_list_data) -> Dict[str, Any]:
    """
    Set up mock services with validation lists data.

    Args:
        default_services: The mock services
        sample_validation_list_data: Sample validation list data

    Returns:
        Dict[str, Any]: Dictionary containing configured mock services
    """
    validation_service = default_services["validation_service"]

    # Set up validation lists
    for list_name, items in sample_validation_list_data.items():
        validation_service.set_validation_list(list_name, items)

    return default_services


@pytest.fixture
def setup_correction_rules(default_services, sample_correction_rules) -> Dict[str, Any]:
    """
    Set up mock services with correction rules.

    Args:
        default_services: The mock services
        sample_correction_rules: Sample correction rules

    Returns:
        Dict[str, Any]: Dictionary containing configured mock services
    """
    correction_service = default_services["correction_service"]

    # Set up correction rules
    correction_service.set_correction_rules(sample_correction_rules)

    return default_services


@pytest.fixture
def setup_data(default_services, sample_data_frame) -> Dict[str, Any]:
    """
    Set up mock services with sample data.

    Args:
        default_services: The mock services
        sample_data_frame: Sample DataFrame

    Returns:
        Dict[str, Any]: Dictionary containing configured mock services
    """
    data_store = default_services["data_store"]

    # Set up data
    data_store.set_data(sample_data_frame)

    return default_services


@pytest.fixture
def setup_all(setup_validation_lists, setup_correction_rules, setup_data) -> Dict[str, Any]:
    """
    Set up mock services with all sample data.

    Args:
        setup_validation_lists: Services with validation lists
        setup_correction_rules: Services with correction rules
        setup_data: Services with data

    Returns:
        Dict[str, Any]: Dictionary containing fully configured mock services
    """
    # Since all these fixtures use the same default_services instance,
    # we can just return any of them - they all have the fully configured services
    return setup_data
