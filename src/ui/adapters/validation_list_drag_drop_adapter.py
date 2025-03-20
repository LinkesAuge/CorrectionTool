"""
validation_list_drag_drop_adapter.py

Description: Adapter that enables drag-drop functionality for ValidationListWidget
Usage:
    adapter = ValidationListDragDropAdapter(validation_list_widget, data_store, "player")
    adapter.connect()
"""

import logging
from typing import Dict, List, Optional, Set, Any, cast

from PySide6.QtCore import QMimeData, Qt, QPoint, QEvent
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent
from PySide6.QtWidgets import QTableView, QListWidgetItem, QWidget

from src.interfaces.i_data_store import IDataStore
from src.interfaces.ui_adapters import IDragDropAdapter
from src.ui.validation_list_widget import ValidationListWidget


logger = logging.getLogger(__name__)

# Define MIME types for drag and drop operations
VALIDATION_ITEM_MIME_TYPE = "application/x-validationitem"
CORRECTION_RULE_MIME_TYPE = "application/x-correctionrule"


class ValidationListDragDropAdapter(IDragDropAdapter):
    """
    Adapter that enables drag and drop functionality for ValidationListWidget.

    Attributes:
        _widget (ValidationListWidget): The validation list widget
        _data_store (IDataStore): The data store
        _list_type (str): The type of validation list (player, chest_type, source)
        _table_view (QTableView): The table view in the validation list widget

    Implementation Notes:
        - Enables dragging items from validation list to correction rules
        - Handles visual feedback during drag operations
        - Processes drop events and updates data store accordingly
    """

    def __init__(self, widget: ValidationListWidget, data_store: IDataStore, list_type: str):
        """
        Initialize the adapter.

        Args:
            widget (ValidationListWidget): The validation list widget
            data_store (IDataStore): The data store
            list_type (str): The type of validation list (player, chest_type, source)
        """
        super().__init__()
        self._widget = widget
        self._data_store = data_store
        self._list_type = list_type

        # Ensure we have access to the table view - this might be named _table_view
        if hasattr(self._widget, "_table_view"):
            self._table_view = self._widget._table_view
        else:
            # Fallback for backward compatibility or different implementations
            logger.error(
                f"ValidationListWidget does not have _table_view attribute. Widget attributes: {dir(self._widget)}"
            )
            # Create a safe fallback that won't cause exceptions
            self._table_view = None

        logger.debug(f"ValidationListDragDropAdapter initialized for {list_type}")

    def connect(self) -> None:
        """Connect the adapter to the widget and set up event filters."""
        logger.debug(f"Connecting ValidationListDragDropAdapter for {self._list_type}")

        # Safety check - make sure we have a table view to work with
        if self._table_view is None:
            logger.error("Cannot connect adapter: No table view available")
            return

        # Enable drag and drop
        self._table_view.setDragEnabled(True)
        self._table_view.setAcceptDrops(True)
        self._table_view.setDragDropMode(QTableView.DragDrop)

        # Install event filter
        self._table_view.installEventFilter(self)
        logger.debug("ValidationListDragDropAdapter connected")

    def disconnect(self) -> None:
        """Disconnect the adapter from the widget and remove event filters."""
        logger.debug(f"Disconnecting ValidationListDragDropAdapter for {self._list_type}")

        # Safety check - make sure we have a table view to work with
        if self._table_view is None:
            logger.error("Cannot disconnect adapter: No table view available")
            return

        # Disable drag and drop
        self._table_view.setDragEnabled(False)
        self._table_view.setAcceptDrops(False)
        self._table_view.setDragDropMode(QTableView.NoDragDrop)

        # Remove event filter
        self._table_view.removeEventFilter(self)
        logger.debug("ValidationListDragDropAdapter disconnected")

    def eventFilter(self, watched: QWidget, event: Any) -> bool:
        """
        Filter events for the validation list widget.

        Args:
            watched (QWidget): The widget being watched
            event (Any): The event

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Safety check - make sure we have a table view to work with
        if self._table_view is None:
            return False

        if watched is not self._table_view:
            return False

        # Handle different event types
        if event.type() == QEvent.DragEnter:
            return self._handle_drag_enter(cast(QDragEnterEvent, event))
        elif event.type() == QEvent.DragMove:
            return self._handle_drag_move(cast(QDragMoveEvent, event))
        elif event.type() == QEvent.Drop:
            return self._handle_drop(cast(QDropEvent, event))

        return False

    def _handle_drag_enter(self, event: QDragEnterEvent) -> bool:
        """
        Handle drag enter events.

        Args:
            event (QDragEnterEvent): The drag enter event

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Check if the mime data has the correct format
        if event.mimeData().hasFormat(VALIDATION_ITEM_MIME_TYPE):
            event.acceptProposedAction()
            return True

        return False

    def _handle_drag_move(self, event: QDragMoveEvent) -> bool:
        """
        Handle drag move events.

        Args:
            event (QDragMoveEvent): The drag move event

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Check if the mime data has the correct format
        if event.mimeData().hasFormat(VALIDATION_ITEM_MIME_TYPE):
            event.acceptProposedAction()
            return True

        return False

    def _handle_drop(self, event: QDropEvent) -> bool:
        """
        Handle drop events.

        Args:
            event (QDropEvent): The drop event

        Returns:
            bool: True if the event was handled, False otherwise
        """
        # Check if the mime data has the correct format
        if event.mimeData().hasFormat(VALIDATION_ITEM_MIME_TYPE):
            # Get the drop position and find the item at that position
            pos = event.position().toPoint()
            drop_index = self._table_view.indexAt(pos)

            # Extract data from mime data
            mime_data = event.mimeData()
            source_data = mime_data.data(VALIDATION_ITEM_MIME_TYPE).data().decode()

            # Add the item to the list if it's not already there
            items = self._widget.get_items()
            if source_data not in items:
                self._widget.add_item(source_data)
                logger.debug(f"Added item '{source_data}' to {self._list_type} validation list")

                # Notify data store about the changes
                self._data_store.update_validation_list(
                    self._list_type, list(self._widget.get_items())
                )

            event.acceptProposedAction()
            return True

        return False

    def start_drag(self, item: QListWidgetItem) -> None:
        """
        Start a drag operation.

        Args:
            item (QListWidgetItem): The item being dragged
        """
        # Create mime data with the item text
        mime_data = QMimeData()
        mime_data.setData(VALIDATION_ITEM_MIME_TYPE, item.text().encode())

        # Start the drag operation
        drag = self._table_view.drag
        if drag:
            drag.setMimeData(mime_data)
            drag.exec(Qt.CopyAction)
            logger.debug(f"Started drag for item '{item.text()}' from {self._list_type} list")

    def can_accept_drop(self, mime_data: QMimeData) -> bool:
        """
        Check if the adapter can accept the drop.

        Args:
            mime_data (QMimeData): The mime data

        Returns:
            bool: True if the adapter can accept the drop, False otherwise
        """
        return mime_data.hasFormat(VALIDATION_ITEM_MIME_TYPE)
