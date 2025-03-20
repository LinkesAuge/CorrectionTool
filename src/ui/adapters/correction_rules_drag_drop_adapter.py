"""
correction_rules_drag_drop_adapter.py

Description: Adapter that enables drag-drop functionality for CorrectionRulesTable
Usage:
    adapter = CorrectionRulesDragDropAdapter(correction_rules_table, data_store)
    adapter.connect()
"""

import logging
from typing import Dict, List, Optional, Any, cast
import json

from PySide6.QtCore import QMimeData, Qt, QPoint, QEvent
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QTableView, QWidget

from src.interfaces.i_data_store import IDataStore
from src.interfaces.ui_adapters import IDragDropAdapter
from src.ui.correction_rules_table import CorrectionRulesTable
from src.models.correction_rule import CorrectionRule


logger = logging.getLogger(__name__)

# Define MIME types for drag and drop operations
VALIDATION_ITEM_MIME_TYPE = "application/x-validationitem"
CORRECTION_RULE_MIME_TYPE = "application/x-correctionrule"


class CorrectionRulesDragDropAdapter(IDragDropAdapter):
    """
    Adapter that enables drag and drop functionality for CorrectionRulesTable.

    Attributes:
        _widget (CorrectionRulesTable): The correction rules table widget
        _data_store (IDataStore): The data store

    Implementation Notes:
        - Enables dropping validation items onto the correction rules table
        - Processes drop events and creates new correction rules
        - Updates the data store when new rules are created
    """

    def __init__(self, widget: CorrectionRulesTable, data_store: IDataStore):
        """
        Initialize the adapter.

        Args:
            widget (CorrectionRulesTable): The correction rules table widget
            data_store (IDataStore): The data store
        """
        super().__init__()
        self._widget = widget
        self._data_store = data_store
        # Use the widget directly, since CorrectionRulesTable inherits from QTableView
        self._table = self._widget
        logger.debug("CorrectionRulesDragDropAdapter initialized")

    def connect(self) -> None:
        """Connect the adapter to the widget and set up event filters."""
        logger.debug("Connecting CorrectionRulesDragDropAdapter")

        # Enable drag and drop
        self._table.setAcceptDrops(True)
        self._table.setDragDropMode(QTableView.DropOnly)

        # Install event filter
        self._table.installEventFilter(self)
        logger.debug("CorrectionRulesDragDropAdapter connected")

    def disconnect(self) -> None:
        """Disconnect the adapter from the widget and remove event filters."""
        logger.debug("Disconnecting CorrectionRulesDragDropAdapter")

        # Disable drag and drop
        self._table.setAcceptDrops(False)
        self._table.setDragDropMode(QTableView.NoDragDrop)

        # Remove event filter
        self._table.removeEventFilter(self)
        logger.debug("CorrectionRulesDragDropAdapter disconnected")

    def eventFilter(self, watched: QWidget, event: Any) -> bool:
        """
        Filter events for the correction rules table widget.

        Args:
            watched (QWidget): The widget being watched
            event (Any): The event

        Returns:
            bool: True if the event was handled, False otherwise
        """
        if watched is not self._table:
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
            # Extract data from mime data
            mime_data = event.mimeData()
            source_data = mime_data.data(VALIDATION_ITEM_MIME_TYPE).data().decode()

            # Create a new correction rule
            # The source data becomes the "to" value
            new_rule = {"from_text": "", "to_text": source_data, "enabled": True}

            # Add the rule to the table
            self._widget.add_rule(new_rule)
            logger.debug(
                f"Added new correction rule with to_text='{source_data}' from validation list drop"
            )

            # Notify data store about the new rule
            rules = self._widget.get_rules()
            self._data_store.update_correction_rules(rules)

            event.acceptProposedAction()
            return True

        return False

    def can_accept_drop(self, mime_data: QMimeData) -> bool:
        """
        Check if the adapter can accept the drop.

        Args:
            mime_data (QMimeData): The mime data

        Returns:
            bool: True if the adapter can accept the drop, False otherwise
        """
        return mime_data.hasFormat(VALIDATION_ITEM_MIME_TYPE)
