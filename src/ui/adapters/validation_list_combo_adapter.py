"""
validation_list_combo_adapter.py

Description: Adapter that connects validation lists to combo boxes
Usage:
    from src.ui.adapters.validation_list_combo_adapter import ValidationListComboAdapter
    adapter = ValidationListComboAdapter(combo_box, "player")
    adapter.connect()
"""

import logging
from typing import Dict, List, Optional, Any, cast
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QComboBox

# Import interfaces
from src.interfaces import IDataStore, EventType, EventData

# Import implementations
from src.services.dataframe_store import DataFrameStore


class ValidationListComboAdapter(QObject):
    """
    Adapter between DataFrameStore validation lists and QComboBox.

    This class adapts the validation lists in DataFrameStore to a QComboBox widget,
    handling the connection between the data store and UI.

    Attributes:
        _combo_box: QComboBox widget
        _data_store: IDataStore instance
        dataChanged: Signal emitted when data changes

    Implementation Notes:
        - Implements IComboBoxAdapter interface
        - Uses DataFrameStore events for updates
        - Maintains bidirectional synchronization between combo box and data store
        - Provides methods for manipulating validation lists
    """

    # Signals
    dataChanged = Signal()

    def __init__(self, combo_box: QComboBox, list_type: str):
        """
        Initialize the ValidationListComboAdapter.

        Args:
            combo_box: QComboBox widget
            list_type: Type of validation list ('player', 'chest_type', 'source')
        """
        super().__init__(combo_box)

        # Store the combo box and list type
        self._combo_box = combo_box
        self._list_type = list_type

        # Get the data store
        self._data_store = DataFrameStore.get_instance()

        # Setup logging
        self._logger = logging.getLogger(__name__)

        # Connected flag to track if we're connected to events
        self._connected = False

    def _on_validation_list_updated(self, event_data: EventData) -> None:
        """
        Handle validation list updated event.

        Args:
            event_data: Event data dictionary
        """
        list_type = event_data.get("list_type", "")
        if list_type == self._list_type or not list_type:
            self.refresh()

    def _on_item_selected(self, text: str) -> None:
        """
        Handle item selection in the combo box.

        Args:
            text: Selected item text
        """
        self._logger.debug(f"Item selected: {text}")
        self.dataChanged.emit()

    def connect(self) -> None:
        """
        Connect the adapter to the data store and combo box.

        Subscribes to relevant events and sets up signal connections.
        """
        if not self._connected:
            # Subscribe to validation list updates
            self._data_store.subscribe(
                EventType.VALIDATION_LISTS_UPDATED, self._on_validation_list_updated
            )

            # Connect combo box signals
            self._combo_box.currentTextChanged.connect(self._on_item_selected)

            # Mark as connected
            self._connected = True

            # Initial refresh
            self.refresh()

    def disconnect(self) -> None:
        """
        Disconnect the adapter from the data store and combo box.

        Unsubscribes from events and disconnects signals.
        """
        if self._connected:
            # Unsubscribe from validation list updates
            self._data_store.unsubscribe(
                EventType.VALIDATION_LISTS_UPDATED, self._on_validation_list_updated
            )

            # Disconnect combo box signals
            self._combo_box.currentTextChanged.disconnect(self._on_item_selected)

            # Mark as disconnected
            self._connected = False

    def refresh(self) -> None:
        """
        Refresh the combo box with current data from the data store.
        """
        # Get the validation list from the data store
        items = self._data_store.get_validation_list(self._list_type)

        # Remember the current selection
        current_text = self._combo_box.currentText()

        # Clear the combo box
        self._combo_box.clear()

        # Add empty item at the start
        self._combo_box.addItem("")

        # Add all items from the validation list
        for item in sorted(items):
            self._combo_box.addItem(item)

        # Restore the selection if possible
        if current_text:
            index = self._combo_box.findText(current_text)
            if index >= 0:
                self._combo_box.setCurrentIndex(index)

    def get_selected_item(self) -> str:
        """
        Get the currently selected item.

        Returns:
            str: Selected item text
        """
        return self._combo_box.currentText()

    def set_selected_item(self, item: str) -> None:
        """
        Set the selected item.

        Args:
            item: Item to select
        """
        index = self._combo_box.findText(item)
        if index >= 0:
            self._combo_box.setCurrentIndex(index)
        else:
            # If the item is not in the list, add it and select it
            self._combo_box.addItem(item)
            self._combo_box.setCurrentText(item)

    def add_item(self, item: str) -> None:
        """
        Add an item to the combo box.

        Args:
            item: Item to add
        """
        # Check if the item already exists
        index = self._combo_box.findText(item)
        if index < 0:
            # Add to combo box
            self._combo_box.addItem(item)

            # Add to validation list in data store
            items = self._data_store.get_validation_list(self._list_type)
            if item not in items:
                items.append(item)
                self._data_store.set_validation_list(self._list_type, items)
