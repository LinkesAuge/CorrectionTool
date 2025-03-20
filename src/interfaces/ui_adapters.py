"""
ui_adapters.py

Description: Interfaces for UI adapters that connect UI components to the data store
Usage:
    from src.interfaces.ui_adapters import ITableAdapter, IComboBoxAdapter

    class MyTableAdapter(ITableAdapter):
        # Implement interface methods
"""

from typing import Any, Dict, List, Optional, Callable, Protocol, runtime_checkable
import pandas as pd
from PySide6.QtCore import QObject, QMimeData
from PySide6.QtWidgets import QWidget


@runtime_checkable
class IUiAdapter(Protocol):
    """
    Interface for UI adapters.

    Base interface for UI adapters.

    This interface defines the common contract for all UI adapters, which are responsible
    for connecting UI components to the data store.

    Implementation Notes:
        - Should subscribe to relevant events from the data store
        - Should update UI when data changes
        - Should provide methods for UI components to update data
    """

    def connect(self) -> None:
        """
        Connect the adapter to the data store and UI component.

        This method should subscribe to relevant events from the data store
        and set up event handlers for the UI component.
        """
        ...

    def disconnect(self) -> None:
        """
        Disconnect the adapter from the data store and UI component.

        This method should unsubscribe from events and clean up resources.
        """
        ...


@runtime_checkable
class ITableAdapter(IUiAdapter, Protocol):
    """
    Interface for table adapters.

    Table adapters connect a table view UI component to the data store,
    handling data display, filtering, and selection.

    Implementation Notes:
        - Should provide methods for accessing selected rows
        - Should handle table view events (selection, edit, etc.)
        - Should provide filtering capabilities
    """

    def refresh(self) -> None:
        """
        Refresh the table view with current data from the data store.
        """
        ...

    def get_selected_rows(self) -> List[int]:
        """
        Get the indices of selected rows in the table view.

        Returns:
            List[int]: List of selected row indices
        """
        ...

    def get_row_data(self, row_index: int) -> Dict[str, Any]:
        """
        Get data for a specific row.

        Args:
            row_index (int): Index of the row

        Returns:
            Dict[str, Any]: Row data as a dictionary of column name to value
        """
        ...

    def set_filter(self, column: str, value: Any) -> None:
        """
        Set a filter on the table view.

        Args:
            column (str): Column name to filter on
            value (Any): Value to filter for
        """
        ...


@runtime_checkable
class IComboBoxAdapter(IUiAdapter, Protocol):
    """
    Interface for combo box adapters.

    Combo box adapters connect a combo box UI component to the data store,
    handling item selection and updates.

    Implementation Notes:
        - Should provide methods for getting/setting selected item
        - Should update items when data changes
        - Should emit signals when selection changes
    """

    def refresh(self) -> None:
        """
        Refresh the combo box with current data from the data store.
        """
        ...

    def get_selected_item(self) -> str:
        """
        Get the currently selected item.

        Returns:
            str: Selected item text
        """
        ...

    def set_selected_item(self, item: str) -> None:
        """
        Set the selected item.

        Args:
            item (str): Item text to select
        """
        ...

    def add_item(self, item: str) -> None:
        """
        Add a new item to the combo box.

        Args:
            item (str): Item text to add
        """
        ...


@runtime_checkable
class IStatusAdapter(IUiAdapter, Protocol):
    """
    Interface for status bar adapters.

    Status bar adapters connect a status bar UI component to application events,
    displaying status messages and progress.

    Implementation Notes:
        - Should display status messages with optional timeout
        - Should show progress indicators
        - Should clear status when needed
    """

    def set_status(self, message: str, timeout: int = 0) -> None:
        """
        Set the status message.

        Args:
            message (str): Status message to display
            timeout (int, optional): Timeout in milliseconds. Defaults to 0 (no timeout).
        """
        ...

    def clear_status(self) -> None:
        """
        Clear the status message.
        """
        ...

    def show_progress(self, value: int, maximum: int) -> None:
        """
        Show progress in the status bar.

        Args:
            value (int): Current progress value
            maximum (int): Maximum progress value
        """
        ...


class IDragDropAdapter(QObject):
    """
    Interface for drag-and-drop adapters.

    Drag-and-drop adapters enable drag-and-drop functionality between different
    UI components, such as validation lists and correction rules.

    Implementation Notes:
        - Should handle the drag start event
        - Should handle the drop event
        - Should provide visual cues for drag operations
        - Should validate and transform data between different components
    """

    def connect(self) -> None:
        """
        Connect the adapter to the widget and set up event filters.

        This method should set up event filters and connections needed for drag-and-drop.
        """
        ...

    def disconnect(self) -> None:
        """
        Disconnect the adapter from the widget and remove event filters.

        This method should remove event filters and clean up connections.
        """
        ...

    def eventFilter(self, watched: QWidget, event: Any) -> bool:
        """
        Filter events for the widget.

        Args:
            watched: The widget being watched
            event: The event to filter

        Returns:
            bool: True if the event was handled, False otherwise
        """
        ...

    def can_accept_drop(self, mime_data: QMimeData) -> bool:
        """
        Check if the adapter can accept the drop.

        Args:
            mime_data: The MIME data to check

        Returns:
            bool: True if the adapter can accept the drop, False otherwise
        """
        ...
