"""
drag_drop_manager.py

Description: Manages drag and drop functionality between UI components
Usage:
    manager = DragDropManager(data_store)
    manager.setup_drag_drop(validation_lists, correction_rules_table)
"""

import logging
from typing import Dict, Optional

from PySide6.QtWidgets import QWidget

from src.interfaces.i_data_store import IDataStore
from src.ui.adapters.validation_list_drag_drop_adapter import ValidationListDragDropAdapter
from src.ui.adapters.correction_rules_drag_drop_adapter import CorrectionRulesDragDropAdapter
from src.ui.validation_list_widget import ValidationListWidget
from src.ui.correction_rules_table import CorrectionRulesTable


logger = logging.getLogger(__name__)


class DragDropManager:
    """
    Manages drag and drop functionality between UI components.

    Attributes:
        _data_store (IDataStore): The data store
        _adapters (list): List of active drag-drop adapters

    Implementation Notes:
        - Creates and manages adapters for drag-drop operations
        - Handles connecting and disconnecting adapters
        - Provides cleanup to properly release resources
    """

    def __init__(self, data_store: IDataStore):
        """
        Initialize the DragDropManager.

        Args:
            data_store (IDataStore): The data store to use for drag-drop operations
        """
        self._data_store = data_store
        self._adapters = []
        logger.info("DragDropManager initialized")

    def setup_drag_drop(
        self,
        validation_lists: Dict[str, ValidationListWidget],
        correction_rules_table: CorrectionRulesTable,
    ) -> None:
        """
        Set up drag and drop functionality between validation lists and the correction rules table.

        Args:
            validation_lists (Dict[str, ValidationListWidget]): Dictionary of validation lists
            correction_rules_table (CorrectionRulesTable): The correction rules table
        """
        logger.info("Setting up drag-drop functionality")

        # Create and initialize adapters for validation lists
        for list_type, list_widget in validation_lists.items():
            logger.debug(f"Setting up drag-drop for {list_type} validation list")
            adapter = ValidationListDragDropAdapter(list_widget, self._data_store, list_type)
            adapter.connect()
            self._adapters.append(adapter)

        # Create and initialize adapter for correction rules table
        logger.debug("Setting up drag-drop for correction rules table")
        rules_adapter = CorrectionRulesDragDropAdapter(correction_rules_table, self._data_store)
        rules_adapter.connect()
        self._adapters.append(rules_adapter)

        logger.info(f"Drag-drop setup completed with {len(self._adapters)} adapters")

    def cleanup(self) -> None:
        """
        Clean up all adapters, disconnecting them from their widgets and the data store.
        """
        logger.info(f"Cleaning up {len(self._adapters)} drag-drop adapters")
        for adapter in self._adapters:
            try:
                adapter.disconnect()
                logger.debug(f"Disconnected adapter: {adapter.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error disconnecting adapter: {str(e)}")

        # Clear the adapters list
        self._adapters.clear()
        logger.info("Drag-drop cleanup completed")
