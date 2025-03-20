"""
dataframe_table_adapter.py

Description: Adapter between DataFrameStore and UI components using PySide6
Usage:
    from src.ui.adapters.dataframe_table_adapter import EntryTableAdapter
    adapter = EntryTableAdapter(data_store, config_manager)
    table_view = adapter.get_table_view()
"""

import logging
from typing import Dict, List, Optional, Any, Callable, cast
import pandas as pd
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QTableView, QHeaderView

from src.interfaces.events import EventType, EventData
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_config_manager import IConfigManager
from src.services.event_manager import EventManager

from src.ui.enhanced_table_view import EnhancedTableView


class EntryTableModel(QAbstractTableModel):
    """
    Table model for entries in DataFrameStore.

    This model implements the Qt Model/View architecture for displaying
    entries from the DataFrameStore in a QTableView.

    Attributes:
        _data_store: DataFrameStore instance
        _entries_df: Current entries DataFrame
        _displayed_columns: List of columns to display
        _column_labels: Human-readable column labels
        _visible_rows: List of visible rows
    """

    def __init__(self, data_store: IDataStore, parent=None):
        """
        Initialize the EntryTableModel.

        Args:
            data_store: The data store containing entries
            parent: Parent object
        """
        super().__init__(parent)
        self._data_store = data_store
        self._entries_df = pd.DataFrame()
        self._displayed_columns = ["player", "source", "chest_type", "pieces", "timestamp"]
        self._column_labels = {
            "player": "Player",
            "source": "Source",
            "chest_type": "Chest Type",
            "pieces": "Pieces",
            "timestamp": "Timestamp",
        }
        self._visible_rows = None  # All rows visible by default
        self._logger = logging.getLogger(__name__)

        # Connect to data store events
        EventManager.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
        EventManager.subscribe(EventType.IMPORT_COMPLETED, self._on_entries_updated)

        # Initialize with current data
        self.refresh_data()

    def _on_entries_updated(self, event_data: EventData) -> None:
        """
        Handle entries updated event.

        Args:
            event_data: Event data containing updated entries
        """
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh the model data from the data store."""
        self.beginResetModel()

        # Get entries from data store
        if self._data_store is not None:
            if self._data_store.get_entries() is not None:
                self._entries_df = self._data_store.get_entries().copy()

                # If we have a list of visible rows, apply it
                if self._visible_rows is not None:
                    valid_indices = [
                        idx for idx in self._visible_rows if idx in self._entries_df.index
                    ]
                    self._entries_df = self._entries_df.loc[valid_indices]
            else:
                self._entries_df = None
        else:
            self._entries_df = None

        # Set displayed columns
        if self._entries_df is not None and not self._entries_df.empty:
            self._displayed_columns = list(self._entries_df.columns)
        else:
            self._displayed_columns = []

        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Return the number of rows in the model.

        Args:
            parent: Parent index (unused in table models)

        Returns:
            Number of rows
        """
        if parent.isValid() or self._entries_df is None:
            return 0
        return len(self._entries_df)

    def columnCount(self, parent=QModelIndex()) -> int:
        """
        Return the number of columns in the model.

        Args:
            parent: Parent index (unused in table models)

        Returns:
            Number of columns
        """
        if parent.isValid() or self._entries_df is None or self._entries_df.empty:
            return len(self._displayed_columns)
        return len(self._displayed_columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        """
        Return data for the given index and role.

        Args:
            index: The index to get data for
            role: The data role (display, edit, etc.)

        Returns:
            Data value for the role, or None if not found
        """
        if not index.isValid() or self._entries_df is None or self._entries_df.empty:
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._entries_df):
            return None

        column_name = self._displayed_columns[col]

        # Get the value from the DataFrame
        value = self._entries_df.iloc[row].get(column_name, "")

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return str(value)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        """
        Return header data for the given section and orientation.

        Args:
            section: Section index (row or column)
            orientation: Horizontal or vertical orientation
            role: The data role (display, edit, etc.)

        Returns:
            Header data, or None if not found
        """
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section < len(self._displayed_columns):
                col_name = self._displayed_columns[section]
                return self._column_labels.get(col_name, col_name)

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Return item flags for the given index.

        Args:
            index: The index to get flags for

        Returns:
            Item flags
        """
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def set_visible_rows(self, visible_indices: List[int]) -> None:
        """
        Set which rows should be visible in the model.

        Args:
            visible_indices: List of row indices that should be visible
        """
        self._visible_rows = visible_indices
        self.refresh_data()

    def get_row_data(self, row_index: int) -> Dict[str, Any]:
        """
        Get all data for a specific row.

        Args:
            row_index: The row index

        Returns:
            Dictionary with column names as keys and cell values as values
        """
        if self._entries_df is None or row_index >= len(self._entries_df):
            return {}

        # Get the actual index from the filtered DataFrame
        actual_index = self._entries_df.index[row_index]

        # Return the row as a dictionary
        return self._entries_df.loc[actual_index].to_dict()


class EntryTableAdapter(QObject):
    """
    Adapter between DataFrameStore and QTableView.

    This adapter manages the connection between the data store and the UI,
    handling data updates, filtering, and selection.

    Attributes:
        dataChanged: Signal emitted when data changes
        selection_changed: Signal emitted when the selection changes
    """

    # Signals
    dataChanged = Signal()
    selection_changed = Signal()

    def __init__(self, data_store: IDataStore, config_manager: IConfigManager):
        """
        Initialize the EntryTableAdapter.

        Args:
            data_store: The data store containing entries
            config_manager: Configuration manager for settings
        """
        super().__init__()
        self._data_store = data_store
        self._config_manager = config_manager
        self._model = EntryTableModel(data_store)
        self._table_view = EnhancedTableView()
        self._setup_table_view()
        self._logger = logging.getLogger(__name__)

    def _setup_table_view(self) -> None:
        """Set up the table view with the model and styling."""
        # Set model
        self._table_view.setModel(self._model)

        # Set section resize mode
        header = self._table_view.horizontalHeader()
        for i in range(self._model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        # Configure table view
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSelectionBehavior(QTableView.SelectRows)
        self._table_view.setSelectionMode(QTableView.ExtendedSelection)
        self._table_view.setSortingEnabled(True)

        # Load column widths from config if available
        self._load_column_widths()

    def _load_column_widths(self) -> None:
        """Load column widths from configuration."""
        if self._config_manager is None:
            return

        # Check if we have stored column widths
        for i, col_name in enumerate(self._model._displayed_columns):
            width_key = f"column_width_{col_name}"

            # Try to get width from config
            if self._config_manager.has_option("TableView", width_key):
                width = self._config_manager.get_int("TableView", width_key, fallback=100)
                self._table_view.setColumnWidth(i, width)

    def _save_column_widths(self) -> None:
        """Save column widths to configuration."""
        if self._config_manager is None:
            return

        # Store current column widths
        for i, col_name in enumerate(self._model._displayed_columns):
            width = self._table_view.columnWidth(i)
            width_key = f"column_width_{col_name}"
            self._config_manager.set_value("TableView", width_key, str(width))

        # Save configuration
        self._config_manager.save_config()

    def get_table_view(self) -> QTableView:
        """
        Get the table view widget.

        Returns:
            The table view widget
        """
        return self._table_view

    def refresh(self) -> None:
        """Refresh the model data from the data store."""
        self._model.refresh_data()
        self.dataChanged.emit()

    def get_selected_rows(self) -> List[int]:
        """
        Get the currently selected rows.

        Returns:
            List of selected row indices
        """
        selection = self._table_view.selectionModel()
        if selection is None:
            return []

        return [index.row() for index in selection.selectedRows()]

    def get_row_data(self, row_index: int) -> Dict[str, Any]:
        """
        Get data for a specific row.

        Args:
            row_index: The row index to get data for

        Returns:
            Dictionary of column name to value
        """
        if (
            row_index < 0
            or self._model._entries_df is None
            or row_index >= len(self._model._entries_df)
        ):
            return {}

        row_data = self._model._entries_df.iloc[row_index].to_dict()
        return row_data

    def has_selection(self) -> bool:
        """Check if any rows are selected.

        Returns:
            True if at least one row is selected, False otherwise
        """
        return len(self._table_view.selectionModel().selectedRows()) > 0

    def get_selected_entry(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected entry.

        Returns:
            The selected entry data or None if no selection
        """
        if not self.has_selection():
            return None

        # Get selected row index
        selected_rows = self._table_view.selectionModel().selectedRows()
        if not selected_rows:
            return None

        # Get model index and data
        model_index = selected_rows[0]
        row_idx = model_index.row()

        # Get entry data from the model
        return self._model.get_row_data(row_idx)

    def get_selected_row_index(self) -> Optional[int]:
        """Get the index of the selected row.

        Returns:
            The index of the selected row or None if no selection
        """
        if not self.has_selection():
            return None

        # Get selected row index
        selected_rows = self._table_view.selectionModel().selectedRows()
        if not selected_rows:
            return None

        return selected_rows[0].row()

    def set_visible_rows(self, visible_indices: List[int]) -> None:
        """Set which rows should be visible in the table view.

        Args:
            visible_indices: List of row indices that should be visible
        """
        self._model.set_visible_rows(visible_indices)
        self._table_view.reset()
        self.dataChanged.emit()

    def get_visible_row_count(self) -> int:
        """Get the number of visible rows in the table view.

        Returns:
            Number of visible rows
        """
        return self._model.rowCount()

    def connect(self) -> None:
        """Connect signals and slots."""
        # Connect data store to model
        if hasattr(self._data_store, "data_changed"):
            self._data_store.data_changed.connect(self.refresh_data)

        # Connect selection model signals
        selection_model = self._table_view.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)

        # Save column widths when changed
        header = self._table_view.horizontalHeader()
        header.sectionResized.connect(self._on_column_resized)

    def _on_selection_changed(self, selected, deselected) -> None:
        """Handle selection changes in the table view.

        Args:
            selected: The newly selected items
            deselected: The deselected items
        """
        self._logger.debug("Table selection changed")
        self.selection_changed.emit()

    def _on_column_resized(self, section: int, oldSize: int, newSize: int) -> None:
        """Handle column resizing in the table view.

        Args:
            section: The section index that was resized
            oldSize: The old size of the section
            newSize: The new size of the section
        """
        self._logger.debug(f"Column {section} resized from {oldSize} to {newSize}")
        self._save_column_widths()
