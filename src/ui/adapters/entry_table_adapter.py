"""
entry_table_adapter.py

Description: Adapter between DataFrameStore entries and table views
Usage:
    from src.ui.adapters.entry_table_adapter import EntryTableAdapter
    adapter = EntryTableAdapter(table_view)
    adapter.connect()
"""

import logging
from typing import Dict, List, Optional, Any, cast
import pandas as pd
from PySide6.QtCore import QObject, Signal, Slot, QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QTableView

# Import interfaces
from src.interfaces import ITableAdapter, IDataStore, EventType, EventData

# Import implementations
from src.services.dataframe_store import DataFrameStore


class EntryTableModel(QAbstractTableModel):
    """
    Table model for entries in DataFrameStore.

    This model implements the Qt Model/View architecture for displaying
    entries from the DataFrameStore in a QTableView.

    Attributes:
        _store: DataFrameStore instance
        _entries_df: Current entries DataFrame
        _displayed_columns: List of columns to display
        _column_labels: Human-readable column labels
    """

    def __init__(self, parent=None):
        """
        Initialize the EntryTableModel.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._store = DataFrameStore.get_instance()
        self._entries_df = pd.DataFrame()
        self._logger = logging.getLogger(__name__)

        # Define which columns to display and in what order
        self._displayed_columns = ["id", "date", "chest_type", "player", "source", "status"]

        # Define human-readable column labels
        self._column_labels = {
            "id": "ID",
            "date": "Date",
            "chest_type": "Chest Type",
            "player": "Player",
            "source": "Source",
            "status": "Status",
        }

        # Subscribe to events
        self._store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)

        # Load initial data
        self.refresh_data()

    def _on_entries_updated(self, event_data: EventData) -> None:
        """
        Handle entries updated event.

        Args:
            event_data: Event data dictionary with df, source, and count fields
        """
        self._logger.debug(
            f"Received entries_updated event from {event_data.get('source', 'unknown')}"
        )
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh the model data from DataFrameStore."""
        self.beginResetModel()
        self._entries_df = self._store.get_entries()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Return the number of rows in the model.

        Args:
            parent: Parent index (unused)

        Returns:
            int: Number of rows
        """
        if parent.isValid():
            return 0
        return len(self._entries_df)

    def columnCount(self, parent=QModelIndex()) -> int:
        """
        Return the number of columns in the model.

        Args:
            parent: Parent index (unused)

        Returns:
            int: Number of columns
        """
        if parent.isValid():
            return 0
        return len(self._displayed_columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        """
        Return data for the given index and role.

        Args:
            index: Model index
            role: Data role

        Returns:
            Any: Data for the given index and role
        """
        if not index.isValid():
            return None

        row = index.row()
        if row < 0 or row >= len(self._entries_df):
            return None

        column_name = self._displayed_columns[index.column()]

        # Get the value from the DataFrame
        try:
            value = self._entries_df.iloc[row][column_name]
        except (KeyError, IndexError):
            return None

        if role == Qt.DisplayRole:
            # Format the value for display
            if pd.isna(value) or value is None:
                return ""
            elif column_name == "original_values" and isinstance(value, dict):
                return ", ".join(f"{k}: {v}" for k, v in value.items())
            elif column_name == "validation_errors" and isinstance(value, list):
                return ", ".join(value)
            else:
                return str(value)

        elif role == Qt.BackgroundRole:
            # Set background color based on status
            status = self._entries_df.iloc[row].get("status", "")
            if status == "Invalid":
                return Qt.red
            elif status == "Valid":
                return Qt.green
            elif status == "Pending":
                return Qt.yellow

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        """
        Return header data for the given section and role.

        Args:
            section: Header section
            orientation: Header orientation
            role: Data role

        Returns:
            Any: Header data for the given section and role
        """
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section < 0 or section >= len(self._displayed_columns):
                return None
            column_name = self._displayed_columns[section]
            return self._column_labels.get(column_name, column_name.capitalize())

        return str(section + 1)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Return flags for the given index.

        Args:
            index: Model index

        Returns:
            Qt.ItemFlags: Flags for the given index
        """
        if not index.isValid():
            return Qt.NoItemFlags

        column_name = self._displayed_columns[index.column()]

        # Make editable columns editable
        if column_name in ["chest_type", "player", "source"]:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index: QModelIndex, value: Any, role=Qt.EditRole) -> bool:
        """
        Set data for the given index and role.

        Args:
            index: Model index
            value: New value
            role: Data role

        Returns:
            bool: True if data was set successfully, False otherwise
        """
        if not index.isValid() or role != Qt.EditRole:
            return False

        row = index.row()
        column_name = self._displayed_columns[index.column()]

        # Only allow editing certain columns
        if column_name not in ["chest_type", "player", "source"]:
            return False

        try:
            # Get the entry ID
            entry_id = self._entries_df.index[row]

            # Start a transaction
            self._store.begin_transaction()

            # Get current entries
            entries_df = self._store.get_entries()

            # Get the original value
            original_value = entries_df.at[entry_id, column_name]

            # Skip if the value hasn't changed
            if original_value == value:
                self._store.rollback_transaction()
                return False

            # Store original value if this is the first correction to this field
            if not isinstance(entries_df.at[entry_id, "original_values"], dict):
                entries_df.at[entry_id, "original_values"] = {}

            original_values = entries_df.at[entry_id, "original_values"]

            # Only store the original value once (first correction)
            if column_name not in original_values:
                original_values[column_name] = original_value

            # Update the value
            entries_df.at[entry_id, column_name] = value

            # Update the timestamp
            entries_df.at[entry_id, "last_modified"] = pd.Timestamp.now()

            # Set the updated entries
            self._store.set_entries(entries_df)

            # Commit the transaction
            self._store.commit_transaction()

            # Indicate success
            return True

        except Exception as e:
            # Log the error and roll back the transaction
            self._logger.error(f"Error updating entry: {str(e)}")
            self._store.rollback_transaction()
            return False


class EntryTableAdapter(QObject):
    """
    Adapter between DataFrameStore and QTableView.

    This class adapts the DataFrameStore to a QTableView widget,
    handling the connection between the data store and UI.

    Attributes:
        _table_view: QTableView widget
        _model: EntryTableModel instance
        dataChanged: Signal emitted when data changes

    Implementation Notes:
        - Implements ITableAdapter interface
        - Uses custom model for displaying entries
        - Handles selection changes and filtering
        - Provides methods for accessing selected rows
    """

    # Signals
    dataChanged = Signal()

    def __init__(self, table_view: QTableView):
        """
        Initialize the EntryTableAdapter.

        Args:
            table_view: QTableView widget
        """
        super().__init__(table_view)

        self._table_view = table_view
        self._model = EntryTableModel()
        self._data_store = DataFrameStore.get_instance()
        self._logger = logging.getLogger(__name__)

        # Connected flag
        self._connected = False

        # Filters
        self._filters = {}

    def connect(self) -> None:
        """
        Connect the adapter to the data store and table view.

        Sets up the model and connects signals.
        """
        if not self._connected:
            # Set the model on the table view
            self._table_view.setModel(self._model)

            # Connect signals
            self._model.dataChanged.connect(self.dataChanged)

            # Mark as connected
            self._connected = True

            # Initial refresh
            self.refresh()

    def disconnect(self) -> None:
        """
        Disconnect the adapter from the data store and table view.

        Cleans up signals and resources.
        """
        if self._connected:
            # Disconnect signals
            try:
                self._model.dataChanged.disconnect(self.dataChanged)
            except TypeError:
                # Signal was not connected
                pass

            # Mark as disconnected
            self._connected = False

    def refresh(self) -> None:
        """
        Refresh the table view with current data.
        """
        if self._connected:
            self._model.refresh_data()

            # Resize columns to contents
            if hasattr(self._table_view, "resizeColumnsToContents"):
                self._table_view.resizeColumnsToContents()

    def get_selected_rows(self) -> List[int]:
        """
        Get the currently selected rows.

        Returns:
            List[int]: List of selected row indices
        """
        if not self._connected:
            return []

        # Get selected indexes
        selection = self._table_view.selectionModel()
        if not selection:
            return []

        # Get unique rows from selection
        rows = set()
        for index in selection.selectedIndexes():
            rows.add(index.row())

        return sorted(list(rows))

    def get_row_data(self, row_index: int) -> Dict[str, Any]:
        """
        Get data for a specific row.

        Args:
            row_index: Index of the row

        Returns:
            Dict[str, Any]: Dictionary containing row data
        """
        if not self._connected or row_index < 0 or row_index >= len(self._model._entries_df):
            return {}

        # Get row data as dictionary
        try:
            return self._model._entries_df.iloc[row_index].to_dict()
        except (IndexError, KeyError):
            return {}

    def set_filter(self, column: str, value: Any) -> None:
        """
        Set a filter for the table.

        Args:
            column: Column to filter on
            value: Value to filter for
        """
        if not self._connected:
            return

        if value:
            self._filters[column] = value
        elif column in self._filters:
            del self._filters[column]

        # Apply filters
        self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply current filters to the model."""
        if not self._connected or not self._filters:
            # If no filters, refresh with all data
            self._model.refresh_data()
            return

        # Start with all entries
        entries_df = self._data_store.get_entries()

        # Apply filters
        for column, value in self._filters.items():
            if column in entries_df.columns:
                # Apply filter for this column
                entries_df = entries_df[
                    entries_df[column].astype(str).str.contains(str(value), case=False, na=False)
                ]

        # Update model with filtered data
        self._model.beginResetModel()
        self._model._entries_df = entries_df
        self._model.endResetModel()
