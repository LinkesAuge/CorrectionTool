"""
test_dashboard_bridge.py

Description: Tests for the DashboardBridge class
Usage:
    Run with pytest:
    python -m pytest tests/test_dashboard_bridge.py
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from PySide6.QtWidgets import QApplication

from src.ui.dashboard_bridge import DashboardBridge


@pytest.fixture
def app():
    """Fixture for QApplication."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def dashboard_bridge(app):
    """Fixture for creating the DashboardBridge instance with a mocked DashboardInterface."""
    with patch("src.ui.dashboard_bridge.DashboardInterface") as mock_interface_class:
        # Create a mock instance
        mock_interface = MagicMock()
        mock_interface_class.return_value = mock_interface

        # Create the bridge with the mocked interface
        bridge = DashboardBridge()

        # Give access to the mock interface
        bridge._mock_interface = mock_interface

        yield bridge


def test_bridge_initialization(dashboard_bridge):
    """Test that the bridge is properly initialized with a DashboardInterface."""
    assert hasattr(dashboard_bridge, "_interface")
    assert hasattr(dashboard_bridge, "_service_factory")
    assert hasattr(dashboard_bridge, "_logger")


def test_on_file_loaded_delegation(dashboard_bridge):
    """Test that _on_file_loaded delegates to the interface."""
    # Setup test data
    entries = {"test": "data"}

    # Call the method
    dashboard_bridge._on_file_loaded(entries)

    # Verify delegation
    dashboard_bridge._mock_interface._on_file_loaded.assert_called_once_with(entries)


def test_on_load_text_delegation(dashboard_bridge):
    """Test that _on_load_text delegates to the interface."""
    # Call the method
    dashboard_bridge._on_load_text()

    # Verify delegation
    dashboard_bridge._mock_interface._on_load_text.assert_called_once()


def test_on_correction_rules_loaded_delegation(dashboard_bridge):
    """Test that _on_correction_rules_loaded delegates to the interface."""
    # Setup test data
    event_data = {"count": 5, "file_path": "test.json"}

    # Call the method
    dashboard_bridge._on_correction_rules_loaded(event_data)

    # Verify delegation
    dashboard_bridge._mock_interface._on_correction_rules_loaded.assert_called_once_with(event_data)


def test_on_apply_corrections_delegation(dashboard_bridge):
    """Test that _on_apply_corrections delegates to the interface."""
    # Call the method
    dashboard_bridge._on_apply_corrections()

    # Verify delegation
    dashboard_bridge._mock_interface._on_apply_corrections.assert_called_once()


def test_validate_entries_delegation(dashboard_bridge):
    """Test that _validate_entries delegates to the interface."""
    # Call the method
    dashboard_bridge._validate_entries()

    # Verify delegation
    dashboard_bridge._mock_interface._validate_entries.assert_called_once()


def test_update_validation_status_delegation(dashboard_bridge):
    """Test that _update_validation_status delegates to the interface."""
    # Setup test data
    status = {"valid": True, "invalid_count": 0}

    # Call the method
    dashboard_bridge._update_validation_status(status)

    # Verify delegation
    dashboard_bridge._mock_interface._update_validation_status.assert_called_once_with(status)
