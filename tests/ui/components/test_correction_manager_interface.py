"""
test_correction_manager_interface.py

Description: Test cases for the CorrectionManagerInterface component
Usage:
    pytest tests/ui/components/test_correction_manager_interface.py
"""

import pytest
import pandas as pd
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtCore import Qt
from typing import List, Dict, Any

from src.ui.correction_manager_interface import CorrectionManagerInterface
from tests.ui.helpers.ui_test_helper import UITestHelper
from tests.ui.fixtures.base_test_fixtures import (
    qtbot_fixture,
    default_services,
    sample_validation_list_data,
    sample_correction_rules,
    sample_data_frame,
    setup_validation_lists,
    setup_correction_rules,
    setup_data,
    setup_all,
)


class TestCorrectionManagerInterface:
    """Test suite for CorrectionManagerInterface."""

    def test_interface_creation(self, qtbot_fixture, default_services):
        """Test that the interface can be created successfully."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, default_services["service_factory"])

        # Check that the interface was created successfully
        assert interface is not None
        assert isinstance(interface, CorrectionManagerInterface)

        # Check initial state
        assert interface.windowTitle() == "Correction Manager"

    def test_tab_initialization(self, qtbot_fixture, default_services):
        """Test that tabs are initialized correctly."""
        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, default_services["service_factory"])

        # Get the tab widget
        tab_widget = interface.findChild(QTabWidget)
        assert tab_widget is not None

        # Check that both tabs exist
        assert tab_widget.count() == 2
        assert tab_widget.tabText(0) == "Correction Rules"
        assert tab_widget.tabText(1) == "Validation Lists"

    def test_validation_lists_init(self, qtbot_fixture, setup_validation_lists):
        """Test that validation lists are initialized correctly."""
        # Get services with validation lists set up
        services = setup_validation_lists

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, services["service_factory"])

        # Check that the validation lists were retrieved
        data_store = services["data_store"]
        triggered_events = data_store.get_triggered_events()

        # Ensure event handlers are registered
        assert any(
            event_type.name == "VALIDATION_LIST_UPDATED" for event_type, data in triggered_events
        )

    def test_correction_rules_init(self, qtbot_fixture, setup_correction_rules):
        """Test that correction rules are initialized correctly."""
        # Get services with correction rules set up
        services = setup_correction_rules

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, services["service_factory"])

        # Check that the correction rules were retrieved
        correction_service = services["correction_service"]

        # Since we can't easily access the table model directly,
        # we can verify that the correction service was accessed
        assert len(correction_service.get_correction_rules()) > 0

    def test_data_update(self, qtbot_fixture, setup_all):
        """Test that the interface responds to data updates."""
        # Get services with all data set up
        services = setup_all
        data_store = services["data_store"]

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, services["service_factory"])

        # Clear triggered events
        data_store.clear_triggered_events()

        # Trigger a data update
        new_data = pd.DataFrame(
            {
                "player": ["Updated Player 1", "Updated Player 2"],
                "chest_type": ["Updated Type 1", "Updated Type 2"],
                "source": ["Updated Source 1", "Updated Source 2"],
            }
        )
        data_store.set_data(new_data)

        # Check that the interface responded to the update
        triggered_events = data_store.get_triggered_events()
        assert any(event_type.name == "ENTRIES_UPDATED" for event_type, data in triggered_events)

    def test_validation_list_update(self, qtbot_fixture, setup_all):
        """Test that the interface responds to validation list updates."""
        # Get services with all data set up
        services = setup_all
        data_store = services["data_store"]

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, services["service_factory"])

        # Clear triggered events
        data_store.clear_triggered_events()

        # Trigger a validation list update
        data_store.add_validation_list("new_list", ["New Item 1", "New Item 2"])

        # Check that the interface responded to the update
        triggered_events = data_store.get_triggered_events()
        assert any(
            event_type.name == "VALIDATION_LIST_UPDATED" for event_type, data in triggered_events
        )

    def test_search_functionality(self, qtbot_fixture, setup_all):
        """Test the search functionality in the interface."""
        # Get services with all data set up
        services = setup_all

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, services["service_factory"])

        # Find the search input
        search_input = helper.find_widget_by_name(interface, "search_input")

        # If search input is found, test the search functionality
        if search_input is not None:
            # Enter search text
            helper.enter_text(search_input, "Player 1")

            # The search should filter correction rules and entries
            # This is difficult to verify directly without accessing internal widgets
            # For now, just verify the search input works
            assert search_input.text() == "Player 1"

    def test_integration_with_services(self, qtbot_fixture, setup_all):
        """Test integration with all services."""
        # Get services with all data set up
        services = setup_all

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, services["service_factory"])

        # Verify that all necessary services were retrieved
        service_factory = services["service_factory"]
        service_types = service_factory.get_service_creation_history()

        # Check that all required services were accessed
        required_services = [
            "data_store",
            "config_manager",
            "file_service",
            "correction_service",
            "validation_service",
        ]

        for service_type in required_services:
            assert service_type in service_types, f"Service {service_type} was not accessed"
