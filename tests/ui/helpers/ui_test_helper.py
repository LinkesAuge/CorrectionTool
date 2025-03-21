"""
ui_test_helper.py

Description: Helper class for UI testing with pytest-qt
Usage:
    from tests.ui.helpers.ui_test_helper import UITestHelper

    def test_some_widget(qtbot):
        helper = UITestHelper(qtbot)
        widget = helper.create_validation_list_widget()
        helper.populate_widget_with_list(widget, ["Item1", "Item2"])
        assert widget.count() == 2
"""

from typing import List, Any, Optional, Callable, Dict, Type, TypeVar, Union
import logging
from contextlib import contextmanager
import pandas as pd

from PyQt5.QtCore import Qt, QPoint, QModelIndex
from PyQt5.QtWidgets import QApplication, QWidget, QListWidget, QTableView, QAbstractItemView
from PyQt5.QtTest import QTest

from src.ui.validation_list_widget import ValidationListWidget
from src.ui.correction_manager_interface import CorrectionManagerInterface
from src.interfaces.data_store import IDataStore
from src.interfaces.config_manager import IConfigManager
from src.interfaces.file_service import IFileService
from src.interfaces.correction_service import ICorrectionService
from src.interfaces.validation_service import IValidationService
from src.interfaces.service_factory import IServiceFactory

# Import mock services
from tests.ui.helpers.mock_services import (
    MockDataStore,
    MockConfigManager,
    MockFileService,
    MockCorrectionService,
    MockValidationService,
    MockServiceFactory,
)

# Type variable for widget types
T = TypeVar("T", bound=QWidget)


class UITestHelper:
    """
    Helper class for UI testing with pytest-qt.

    Attributes:
        qtbot: The pytest-qt bot for UI interaction
        logger: Logger instance for test logging

    Implementation Notes:
        - Provides helper methods for common UI testing tasks
        - Creates and configures widget instances for testing
        - Handles interaction with widgets through qtbot
    """

    def __init__(self, qtbot):
        """
        Initialize the UITestHelper.

        Args:
            qtbot: The pytest-qt bot for UI interaction
        """
        self.qtbot = qtbot
        self.logger = logging.getLogger("UITestHelper")
        self.mock_services = self._create_default_mock_services()

    def _create_default_mock_services(self) -> Dict[str, Any]:
        """
        Create default mock services for testing.

        Returns:
            Dict[str, Any]: Dictionary of mock service instances
        """
        data_store = MockDataStore()
        config_manager = MockConfigManager()
        file_service = MockFileService()
        correction_service = MockCorrectionService()
        validation_service = MockValidationService()

        # Configure some default test data
        data_store.add_validation_list("players", ["Player1", "Player2", "Player3"])
        data_store.add_validation_list("chest_types", ["Gold", "Silver", "Bronze"])
        data_store.add_validation_list("sources", ["Source1", "Source2", "Source3"])

        return {
            "data_store": data_store,
            "config_manager": config_manager,
            "file_service": file_service,
            "correction_service": correction_service,
            "validation_service": validation_service,
        }

    def create_service_factory(self) -> MockServiceFactory:
        """
        Create a mock service factory configured with default mock services.

        Returns:
            MockServiceFactory: Configured mock service factory
        """
        factory = MockServiceFactory()
        for service_type, service in self.mock_services.items():
            factory.register_service(service_type, service)
        return factory

    def create_widget(self, widget_class: Type[T], *args, **kwargs) -> T:
        """
        Create and initialize a widget instance for testing.

        Args:
            widget_class: The widget class to instantiate
            *args: Positional arguments for the widget constructor
            **kwargs: Keyword arguments for the widget constructor

        Returns:
            T: The created widget instance
        """
        widget = widget_class(*args, **kwargs)
        self.qtbot.addWidget(widget)
        return widget

    def create_validation_list_widget(self, list_name: str = "test_list") -> ValidationListWidget:
        """
        Create a ValidationListWidget for testing.

        Args:
            list_name: Name of the validation list

        Returns:
            ValidationListWidget: Configured widget instance
        """
        widget = ValidationListWidget(list_name)
        self.qtbot.addWidget(widget)

        # Set services for the widget
        widget._data_store = self.mock_services["data_store"]
        widget._config_manager = self.mock_services["config_manager"]

        return widget

    def create_correction_manager_interface(self) -> CorrectionManagerInterface:
        """
        Create a CorrectionManagerInterface for testing.

        Returns:
            CorrectionManagerInterface: Configured CorrectionManagerInterface instance
        """
        factory = self.create_service_factory()
        interface = CorrectionManagerInterface(factory)
        self.qtbot.addWidget(interface)
        return interface

    def populate_widget_with_list(self, widget: ValidationListWidget, items: List[str]) -> None:
        """
        Populate a ValidationListWidget with a list of items.

        Args:
            widget: The ValidationListWidget to populate
            items: List of string items to add
        """
        widget.set_validation_list(items)

    def populate_widget_with_dataframe(
        self, widget: ValidationListWidget, df: pd.DataFrame, column: str = None
    ) -> None:
        """
        Populate a ValidationListWidget with a DataFrame.

        Args:
            widget: The ValidationListWidget to populate
            df: DataFrame containing the items
            column: Optional column name to use (defaults to first column)
        """
        widget.set_validation_list(df)

    def click_button(self, widget: QWidget, button_name: str) -> None:
        """
        Click a button within a widget by its name.

        Args:
            widget: The widget containing the button
            button_name: The object name of the button
        """
        button = getattr(widget, button_name, None)
        if button:
            self.qtbot.mouseClick(button, Qt.LeftButton)
        else:
            self.logger.error(f"Button '{button_name}' not found in widget {widget}")
            raise AttributeError(f"Button '{button_name}' not found in widget {widget}")

    def click_add_button(self, widget: ValidationListWidget) -> None:
        """
        Click the add button on a ValidationListWidget.

        Args:
            widget: The ValidationListWidget
        """
        self.click_button(widget, "add_button")

    def click_edit_button(self, widget: ValidationListWidget) -> None:
        """
        Click the edit button on a ValidationListWidget.

        Args:
            widget: The ValidationListWidget
        """
        self.click_button(widget, "edit_button")

    def click_delete_button(self, widget: ValidationListWidget) -> None:
        """
        Click the delete button on a ValidationListWidget.

        Args:
            widget: The ValidationListWidget
        """
        self.click_button(widget, "delete_button")

    def click_import_button(self, widget: ValidationListWidget) -> None:
        """
        Click the import button on a ValidationListWidget.

        Args:
            widget: The ValidationListWidget
        """
        self.click_button(widget, "import_button")

    def click_export_button(self, widget: ValidationListWidget) -> None:
        """
        Click the export button on a ValidationListWidget.

        Args:
            widget: The ValidationListWidget
        """
        self.click_button(widget, "export_button")

    def select_item(self, list_widget: QListWidget, index: int) -> None:
        """
        Select an item in a QListWidget by index.

        Args:
            list_widget: The QListWidget
            index: The index of the item to select
        """
        item = list_widget.item(index)
        if item:
            list_widget.setCurrentItem(item)
        else:
            self.logger.error(f"Item at index {index} not found in list widget")
            raise IndexError(f"Item at index {index} not found in list widget")

    def select_items(self, list_widget: QListWidget, indices: List[int]) -> None:
        """
        Select multiple items in a QListWidget.

        Args:
            list_widget: The QListWidget
            indices: List of item indices to select
        """
        list_widget.clearSelection()
        for index in indices:
            item = list_widget.item(index)
            if item:
                item.setSelected(True)
            else:
                self.logger.warning(f"Item at index {index} not found in list widget")

    def get_selected_indices(self, list_widget: QListWidget) -> List[int]:
        """
        Get the indices of selected items in a QListWidget.

        Args:
            list_widget: The QListWidget

        Returns:
            List[int]: List of selected item indices
        """
        return [list_widget.row(item) for item in list_widget.selectedItems()]

    def enter_text(self, widget: QWidget, text: str) -> None:
        """
        Enter text into a widget that accepts text input.

        Args:
            widget: The widget to enter text into
            text: The text to enter
        """
        widget.clear()
        QTest.keyClicks(widget, text)

    def filter_list(self, widget: ValidationListWidget, filter_text: str) -> None:
        """
        Apply a filter to a ValidationListWidget.

        Args:
            widget: The ValidationListWidget
            filter_text: The text to filter by
        """
        self.enter_text(widget.filter_edit, filter_text)
        # Trigger the filter by pressing Enter
        QTest.keyClick(widget.filter_edit, Qt.Key_Return)

    @contextmanager
    def wait_signal(self, signal, timeout: int = 1000):
        """
        Context manager to wait for a signal to be emitted.

        Args:
            signal: The Qt signal to wait for
            timeout: Timeout in milliseconds

        Yields:
            None
        """
        with self.qtbot.waitSignal(signal, timeout=timeout) as blocker:
            yield blocker

    def verify_list_items(self, list_widget: QListWidget, expected_items: List[str]) -> None:
        """
        Verify that a QListWidget contains the expected items.

        Args:
            list_widget: The QListWidget to check
            expected_items: List of expected item texts
        """
        assert list_widget.count() == len(expected_items), (
            f"Expected {len(expected_items)} items, got {list_widget.count()}"
        )

        for i, expected_text in enumerate(expected_items):
            item = list_widget.item(i)
            assert item is not None, f"No item at index {i}"
            assert item.text() == expected_text, (
                f"Expected '{expected_text}' at index {i}, got '{item.text()}'"
            )

    def verify_visible_items(self, list_widget: QListWidget, expected_visible: List[str]) -> None:
        """
        Verify that the visible items in a QListWidget match the expected items.

        Args:
            list_widget: The QListWidget to check
            expected_visible: List of expected visible item texts
        """
        visible_items = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if not item.isHidden():
                visible_items.append(item.text())

        assert len(visible_items) == len(expected_visible), (
            f"Expected {len(expected_visible)} visible items, got {len(visible_items)}"
        )

        for expected_text in expected_visible:
            assert expected_text in visible_items, (
                f"Expected visible item '{expected_text}' not found"
            )

    def add_validation_list_item(self, widget: ValidationListWidget, text: str) -> None:
        """
        Add an item to a ValidationListWidget.

        Args:
            widget: The ValidationListWidget
            text: The text of the item to add
        """
        # Call the internal method directly to avoid the input dialog
        widget._add_item(text)

    def edit_validation_list_item(
        self, widget: ValidationListWidget, index: int, new_text: str
    ) -> None:
        """
        Edit an item in a ValidationListWidget.

        Args:
            widget: The ValidationListWidget
            index: The index of the item to edit
            new_text: The new text for the item
        """
        # Select the item first
        self.select_item(widget, index)

        # Call the internal method directly to avoid the input dialog
        widget._edit_item(new_text)

    def delete_validation_list_item(self, widget: ValidationListWidget, index: int) -> None:
        """
        Delete an item from a ValidationListWidget.

        Args:
            widget: The ValidationListWidget
            index: The index of the item to delete
        """
        # Select the item first
        self.select_item(widget, index)

        # Call the internal method directly
        widget._delete_selected_items()

    def simulate_drag_drop(
        self,
        source_widget: QWidget,
        target_widget: QWidget,
        source_index: int,
        target_position: QPoint,
    ) -> None:
        """
        Simulate drag and drop between widgets.

        Args:
            source_widget: The widget to drag from
            target_widget: The widget to drop onto
            source_index: The index of the item to drag
            target_position: The position to drop at
        """
        # This is a simplified version - actual implementation would be more complex
        # depending on the widgets involved
        self.logger.info(f"Simulating drag from index {source_index} to position {target_position}")

        # In a real implementation, this would simulate mouse events
        # for press, move, and release to trigger the drag and drop
        pass

    def simulate_key_sequence(self, widget: QWidget, key_sequence: List[int]) -> None:
        """
        Simulate a sequence of key presses on a widget.

        Args:
            widget: The widget to receive key events
            key_sequence: List of Qt key codes to press
        """
        for key in key_sequence:
            QTest.keyClick(widget, key)

    def get_model_data(self, model_index: QModelIndex) -> Any:
        """
        Get data from a model index.

        Args:
            model_index: The model index to get data from

        Returns:
            Any: The data at the model index
        """
        return model_index.data()

    def verify_table_cell(
        self, table_view: QTableView, row: int, column: int, expected_value: Any
    ) -> None:
        """
        Verify the value of a cell in a QTableView.

        Args:
            table_view: The QTableView to check
            row: The row of the cell
            column: The column of the cell
            expected_value: The expected value of the cell
        """
        model = table_view.model()
        index = model.index(row, column)
        actual_value = model.data(index)

        assert actual_value == expected_value, (
            f"Expected '{expected_value}' at cell ({row}, {column}), got '{actual_value}'"
        )

    def click_table_cell(self, table_view: QTableView, row: int, column: int) -> None:
        """
        Click a cell in a QTableView.

        Args:
            table_view: The QTableView
            row: The row of the cell
            column: The column of the cell
        """
        model = table_view.model()
        index = model.index(row, column)
        rect = table_view.visualRect(index)
        center = rect.center()
        self.qtbot.mouseClick(table_view.viewport(), Qt.LeftButton, pos=center)

    def double_click_table_cell(self, table_view: QTableView, row: int, column: int) -> None:
        """
        Double-click a cell in a QTableView.

        Args:
            table_view: The QTableView
            row: The row of the cell
            column: The column of the cell
        """
        model = table_view.model()
        index = model.index(row, column)
        rect = table_view.visualRect(index)
        center = rect.center()
        self.qtbot.mouseDClick(table_view.viewport(), Qt.LeftButton, pos=center)

    def right_click_table_cell(self, table_view: QTableView, row: int, column: int) -> None:
        """
        Right-click a cell in a QTableView.

        Args:
            table_view: The QTableView
            row: The row of the cell
            column: The column of the cell
        """
        model = table_view.model()
        index = model.index(row, column)
        rect = table_view.visualRect(index)
        center = rect.center()
        self.qtbot.mouseClick(table_view.viewport(), Qt.RightButton, pos=center)

    def select_table_rows(self, table_view: QTableView, rows: List[int]) -> None:
        """
        Select rows in a QTableView.

        Args:
            table_view: The QTableView
            rows: List of row indices to select
        """
        table_view.clearSelection()
        model = table_view.model()
        selection_model = table_view.selectionModel()

        for row in rows:
            index = model.index(row, 0)
            selection_model.select(index, selection_model.Select | selection_model.Rows)

    def get_selected_rows(self, table_view: QTableView) -> List[int]:
        """
        Get the indices of selected rows in a QTableView.

        Args:
            table_view: The QTableView

        Returns:
            List[int]: List of selected row indices
        """
        selection_model = table_view.selectionModel()
        return [index.row() for index in selection_model.selectedRows()]
