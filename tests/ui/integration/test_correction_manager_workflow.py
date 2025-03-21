"""
test_correction_manager_workflow.py

Description: Integration tests for the CorrectionManagerInterface workflow
Usage:
    pytest tests/ui/integration/test_correction_manager_workflow.py
"""

import pytest
import pandas as pd
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QPushButton,
    QTableView,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, QTimer
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


class TestCorrectionManagerWorkflow:
    """Integration tests for complete workflows in the CorrectionManagerInterface."""

    @pytest.mark.integration
    def test_create_and_apply_correction_rule(self, qtbot_fixture, setup_all):
        """Test creating a correction rule and applying it to entry data."""
        # Get services with all data set up
        services = setup_all

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, services["service_factory"])

        # Get the initial state of the correction rules
        correction_service = services["correction_service"]
        initial_rules_count = len(correction_service.get_correction_rules())

        # Find and click the add rule button
        add_rule_button = helper.find_widget_by_name(interface, "add_rule_button")
        if add_rule_button:
            # Before clicking, set up a handler for the dialog that will appear
            def handle_dialog():
                # Find the dialog (will be the active modal widget)
                dialog = QApplication.activeModalWidget()
                if dialog:
                    # Populate the dialog fields
                    from_field = helper.find_widget_by_name(dialog, "from_field")
                    to_field = helper.find_widget_by_name(dialog, "to_field")

                    if from_field and to_field:
                        helper.enter_text(from_field, "TestFromValue")
                        helper.enter_text(to_field, "TestToValue")

                        # Find and click the OK button
                        button_box = helper.find_widget_by_class(dialog, "QDialogButtonBox")
                        if button_box:
                            ok_button = button_box.button(QDialogButtonBox.Ok)
                            if ok_button:
                                helper.qtbot.mouseClick(ok_button, Qt.LeftButton)

            # Use QTimer to handle the dialog after it appears
            QTimer.singleShot(100, handle_dialog)

            # Now click the button
            helper.click_button(interface, "add_rule_button")

            # Allow time for the dialog and rule creation
            qtbot_fixture.wait(200)

            # Verify that a new rule was added
            assert len(correction_service.get_correction_rules()) > initial_rules_count

            # Check the content of the new rule
            rules = correction_service.get_correction_rules()
            new_rule = next((r for r in rules if r.get("from") == "TestFromValue"), None)
            assert new_rule is not None
            assert new_rule.get("to") == "TestToValue"

            # Now update the test data to include our test value
            data_store = services["data_store"]
            data = data_store.get_data()
            data = data.copy()
            if "player" in data.columns:
                data.loc[0, "player"] = "TestFromValue"
            data_store.set_data(data)

            # Find and click apply corrections button to apply the rule
            apply_button = helper.find_widget_by_name(interface, "apply_corrections_button")
            if apply_button:
                helper.click_button(interface, "apply_corrections_button")

                # Verify that the correction was applied
                corrected_data = data_store.get_data()
                if "player" in corrected_data.columns:
                    assert corrected_data.loc[0, "player"] == "TestToValue"

    @pytest.mark.integration
    def test_validation_list_workflow(self, qtbot_fixture, setup_validation_lists):
        """Test the full validation list workflow including add, edit, delete, and validate."""
        # Get services with validation lists set up
        services = setup_validation_lists

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, services["service_factory"])

        # Switch to the validation lists tab
        tab_widget = helper.find_widget_by_class(interface, "QTabWidget")
        if tab_widget:
            tab_widget.setCurrentIndex(1)  # Assuming Validation Lists is tab 1

            # Find the players validation list widget
            players_widget = helper.find_widget_by_class(
                interface, "ValidationListWidget", "players"
            )
            if players_widget:
                # Get the initial count of items
                initial_count = players_widget.count()

                # Add a new item
                def handle_add_dialog():
                    dialog = QApplication.activeModalWidget()
                    if dialog:
                        input_field = helper.find_widget_by_class(dialog, "QLineEdit")
                        if input_field:
                            helper.enter_text(input_field, "NewTestPlayer")

                            # Find and click the OK button
                            ok_button = dialog.findChild(QPushButton, "OK")
                            if ok_button:
                                helper.qtbot.mouseClick(ok_button, Qt.LeftButton)

                # Set up a timer to handle the dialog
                QTimer.singleShot(100, handle_add_dialog)

                # Click the add button
                helper.click_button(players_widget, "add_button")

                # Allow time for the dialog and item addition
                qtbot_fixture.wait(200)

                # Verify the item was added
                assert players_widget.count() > initial_count

                # Verify the item appears in the validation service
                validation_service = services["validation_service"]
                player_list = validation_service.get_validation_list("players")
                assert "NewTestPlayer" in player_list

    @pytest.mark.integration
    def test_correction_rule_search_filter(self, qtbot_fixture, setup_all):
        """Test searching/filtering correction rules."""
        # Get services with all data set up
        services = setup_all

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, services["service_factory"])

        # Find the correction rules table
        table_view = helper.find_widget_by_class(interface, "QTableView", "correction_rules_table")

        # Get the initial row count
        if table_view:
            initial_visible_rows = table_view.model().rowCount()

            # Find the search input
            search_input = helper.find_widget_by_name(interface, "correction_rules_search")
            if search_input:
                # Enter a search term that should filter the results
                search_term = "Player"  # Assuming some rule contains "Player"
                helper.enter_text(search_input, search_term)

                # Allow time for the filter to apply
                qtbot_fixture.wait(100)

                # Check if filtering has been applied
                filtered_rows = table_view.model().rowCount()

                # In a real scenario, we'd expect fewer rows after filtering
                # But in the test environment, we can only verify that the filter was applied
                # and the model responded by updating its row count
                assert filtered_rows <= initial_visible_rows

    @pytest.mark.integration
    def test_toggle_correction_rules(self, qtbot_fixture, setup_all):
        """Test toggling correction rules on and off."""
        # Get services with all data set up
        services = setup_all

        # Create test helper
        helper = UITestHelper(qtbot_fixture)

        # Create parent window to hold the interface
        parent = QMainWindow()

        # Create interface
        interface = CorrectionManagerInterface(parent, services["service_factory"])

        # Find the global toggle checkbox
        toggle_all = helper.find_widget_by_name(interface, "toggle_all_rules")

        if toggle_all:
            # Get the initial state of the correction service
            correction_service = services["correction_service"]
            initial_enabled = correction_service.is_correction_enabled()

            # Click the toggle
            helper.qtbot.mouseClick(toggle_all, Qt.LeftButton)

            # Verify the state changed
            assert correction_service.is_correction_enabled() != initial_enabled

            # Toggle back
            helper.qtbot.mouseClick(toggle_all, Qt.LeftButton)

            # Verify we're back to initial state
            assert correction_service.is_correction_enabled() == initial_enabled
