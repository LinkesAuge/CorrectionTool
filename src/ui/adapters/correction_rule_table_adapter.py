"""
correction_rule_table_adapter.py

Description: Adapter between DataFrameStore correction rules and table widgets
Usage:
    from src.ui.adapters.correction_rule_table_adapter import CorrectionRuleTableAdapter
    adapter = CorrectionRuleTableAdapter(table_widget)
    adapter.connect()
"""

import logging
from typing import Dict, List, Optional, Any, cast
import pandas as pd
from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

# Import interfaces
from src.interfaces import ITableAdapter, IDataStore, EventType, EventData

# Import implementations
from src.services.dataframe_store import DataFrameStore


class CorrectionRuleTableAdapter(QObject):
    """
    Adapter between DataFrameStore correction rules and QTableView.

    This class adapts the DataFrameStore's correction rules to a QTableView widget,
    handling the connection between the data store and UI.

    Attributes:
        _table_view: QTableView widget
        _model: CorrectionRuleTableModel instance
        dataChanged: Signal emitted when data changes

    Implementation Notes:
        - Implements ITableAdapter interface
        - Uses custom model for displaying correction rules
        - Handles selection changes and filtering
        - Provides methods for accessing selected rows
    """

    # Signals
    dataChanged = Signal()
    ruleSelected = Signal(int)  # Emitted when a rule is selected (with rule index)

    def __init__(self, table_widget: QTableWidget):
        """
        Initialize the CorrectionRuleTableAdapter.

        Args:
            table_widget: QTableWidget widget
        """
        super().__init__(table_widget)

        self._table_widget = table_widget
        self._data_store = DataFrameStore.get_instance()
        self._logger = logging.getLogger(__name__)

        # Connected flag
        self._connected = False

        # Define columns for display
        self._columns = ["from_text", "to_text", "category", "enabled"]

        # Column headers
        self._headers = {
            "from_text": "From",
            "to_text": "To",
            "category": "Category",
            "enabled": "Enabled",
        }

        # Current filter
        self._filter_column = ""
        self._filter_value = None

    def _on_correction_rules_updated(self, event_data: EventData) -> None:
        """
        Handle correction rules updated event.

        Args:
            event_data: Event data dictionary
        """
        self.refresh()

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        """
        Handle item changed in the table widget.

        Args:
            item: Changed table item
        """
        # Skip if we're programmatically updating (to avoid circular updates)
        if not self._connected or self._table_widget.blockSignals(False):
            return

        row = item.row()
        col = item.column()
        column_name = self._columns[col]
        value = item.text()

        # For checkbox columns, get checkbox state
        if column_name == "enabled" and item.checkState() is not None:
            value = item.checkState() == Qt.Checked

        # Get the rule index from the row
        try:
            # We'll store the rule's original index as hidden data in the first column
            rule_index = self._table_widget.item(row, 0).data(Qt.UserRole)
            if rule_index is None:
                return

            # Start a transaction
            self._data_store.begin_transaction()

            # Get current rules
            rules_df = self._data_store.get_correction_rules()

            # Update the rule value
            if column_name in rules_df.columns:
                # Convert boolean strings to actual booleans if needed
                if column_name == "enabled" and isinstance(value, str):
                    if value.lower() in ["true", "1", "yes", "y"]:
                        value = True
                    elif value.lower() in ["false", "0", "no", "n"]:
                        value = False

                # Update the value in the DataFrame
                rules_df.at[rule_index, column_name] = value

                # Update the timestamp
                if "timestamp" in rules_df.columns:
                    rules_df.at[rule_index, "timestamp"] = pd.Timestamp.now()

                # Set the updated rules
                self._data_store.set_correction_rules(rules_df)

                # Commit the transaction
                self._data_store.commit_transaction()

                # Emit data changed signal
                self.dataChanged.emit()
            else:
                # Column doesn't exist in the DataFrame
                self._data_store.rollback_transaction()

        except Exception as e:
            # Log the error and roll back the transaction
            self._logger.error(f"Error updating correction rule: {str(e)}")
            self._data_store.rollback_transaction()

    def _on_item_selection_changed(self) -> None:
        """Handle selection change in the table widget."""
        selected_rows = self.get_selected_rows()
        if selected_rows:
            # Emit signal with the first selected rule's index
            selected_item = self._table_widget.item(selected_rows[0], 0)
            if selected_item:
                rule_index = selected_item.data(Qt.UserRole)
                if rule_index is not None:
                    self.ruleSelected.emit(rule_index)

    def connect(self) -> None:
        """
        Connect the adapter to the data store and table widget.

        Subscribes to relevant events and sets up signal connections.
        """
        if not self._connected:
            # Configure the table widget
            self._table_widget.setColumnCount(len(self._columns))
            self._table_widget.setHorizontalHeaderLabels(
                [self._headers.get(col, col) for col in self._columns]
            )

            # Set column properties
            header = self._table_widget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # From column
            header.setSectionResizeMode(1, QHeaderView.Stretch)  # To column
            if len(self._columns) > 2:
                header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Category column
                header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Enabled column

            # Subscribe to correction rules updates
            self._data_store.subscribe(
                EventType.CORRECTION_RULES_UPDATED, self._on_correction_rules_updated
            )

            # Connect table widget signals
            self._table_widget.itemChanged.connect(self._on_item_changed)
            self._table_widget.itemSelectionChanged.connect(self._on_item_selection_changed)

            # Mark as connected
            self._connected = True

            # Initial refresh
            self.refresh()

    def disconnect(self) -> None:
        """
        Disconnect the adapter from the data store and table widget.

        Unsubscribes from events and disconnects signals.
        """
        if self._connected:
            # Unsubscribe from correction rules updates
            self._data_store.unsubscribe(
                EventType.CORRECTION_RULES_UPDATED, self._on_correction_rules_updated
            )

            # Disconnect table widget signals
            self._table_widget.itemChanged.disconnect(self._on_item_changed)
            self._table_widget.itemSelectionChanged.disconnect(self._on_item_selection_changed)

            # Mark as disconnected
            self._connected = False

    def refresh(self) -> None:
        """
        Refresh the table widget with current data from the data store.
        """
        if not self._connected:
            return

        # Block signals to prevent triggering itemChanged while updating
        self._table_widget.blockSignals(True)

        # Get correction rules from data store
        rules_df = self._data_store.get_correction_rules()

        # Apply filter if set
        if self._filter_column and self._filter_value is not None:
            if self._filter_column in rules_df.columns:
                # For text columns, do a case-insensitive contains search
                if rules_df[self._filter_column].dtype == "object":
                    mask = rules_df[self._filter_column].str.contains(
                        str(self._filter_value), case=False, na=False
                    )
                    rules_df = rules_df[mask]
                else:
                    # For non-text columns, do an exact match
                    rules_df = rules_df[rules_df[self._filter_column] == self._filter_value]

        # Clear the table
        self._table_widget.setRowCount(0)

        # Fill the table with correction rules
        if not rules_df.empty:
            self._table_widget.setRowCount(len(rules_df))

            for i, (idx, rule) in enumerate(rules_df.iterrows()):
                # Create items for each column
                for j, col in enumerate(self._columns):
                    value = rule.get(col, "")

                    # Create and configure the table item
                    item = QTableWidgetItem(str(value) if value is not None else "")

                    # Store the original index as data in the first column
                    if j == 0:
                        item.setData(Qt.UserRole, idx)

                    # For boolean values like enabled, use a checkbox
                    if col == "enabled":
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                        item.setCheckState(Qt.Checked if value else Qt.Unchecked)

                    # Add the item to the table
                    self._table_widget.setItem(i, j, item)

        # Unblock signals
        self._table_widget.blockSignals(False)

    def get_selected_rows(self) -> List[int]:
        """
        Get the indices of selected rows in the table view.

        Returns:
            List[int]: List of selected row indices
        """
        selected_rows = []

        # Get selected ranges
        selected_ranges = self._table_widget.selectedRanges()

        # Also get selected items (for single cell selections)
        selected_items = self._table_widget.selectedItems()

        # Process ranges
        for selection_range in selected_ranges:
            for row in range(selection_range.topRow(), selection_range.bottomRow() + 1):
                if row not in selected_rows:
                    selected_rows.append(row)

        # Process individual items
        for item in selected_items:
            if item.row() not in selected_rows:
                selected_rows.append(item.row())

        return sorted(selected_rows)

    def get_row_data(self, row_index: int) -> Dict[str, Any]:
        """
        Get data for a specific row.

        Args:
            row_index (int): Index of the row

        Returns:
            Dict[str, Any]: Row data as a dictionary of column name to value
        """
        row_data = {}

        # Check if row index is valid
        if row_index < 0 or row_index >= self._table_widget.rowCount():
            return row_data

        # Get the original dataframe index from the first cell's user data
        first_item = self._table_widget.item(row_index, 0)
        if first_item is None:
            return row_data

        df_index = first_item.data(Qt.UserRole)
        if df_index is None:
            return row_data

        # Get the rules dataframe
        rules_df = self._data_store.get_correction_rules()

        # Check if the index exists in the dataframe
        if df_index in rules_df.index:
            # Return the row as a dictionary
            return rules_df.loc[df_index].to_dict()

        # If we reach here, construct the dictionary from the table items
        for col_idx, col_name in enumerate(self._columns):
            item = self._table_widget.item(row_index, col_idx)
            if item is not None:
                # Handle special case for checkboxes
                if col_name == "enabled" and item.checkState() is not None:
                    row_data[col_name] = item.checkState() == Qt.Checked
                else:
                    row_data[col_name] = item.text()

        return row_data

    def set_filter(self, column: str, value: Any) -> None:
        """
        Set a filter on the table view.

        Args:
            column (str): Column name to filter on
            value (Any): Value to filter for
        """
        self._filter_column = column
        self._filter_value = value

        # Apply the filter
        self.refresh()

    def clear_filters(self) -> None:
        """
        Clear all filters from the table view.
        """
        self._filter_column = ""
        self._filter_value = None

        # Refresh the table to show all data
        self.refresh()

    def add_rule(
        self, from_text: str, to_text: str, category: str = "", enabled: bool = True
    ) -> int:
        """
        Add a new correction rule.

        Args:
            from_text: Original text to correct
            to_text: Corrected text
            category: Rule category (optional)
            enabled: Whether the rule is enabled (default: True)

        Returns:
            int: Index of the new rule, or -1 if an error occurred
        """
        if not self._connected or not from_text:
            return -1

        try:
            # Start a transaction
            self._data_store.begin_transaction()

            # Get current rules
            rules_df = self._data_store.get_correction_rules()

            # Create a new rule
            new_rule = {
                "from_text": from_text,
                "to_text": to_text,
                "category": category,
                "enabled": enabled,
                "timestamp": pd.Timestamp.now(),
            }

            # Add the rule to the DataFrame (find a unique index if needed)
            if hasattr(rules_df, "empty") and not rules_df.empty:
                new_index = rules_df.index.max() + 1
            elif isinstance(rules_df.index, pd.RangeIndex):
                new_index = len(rules_df)
            else:
                new_index = 0

            # Ensure all required columns exist
            for col in ["from_text", "to_text", "category", "enabled", "timestamp"]:
                if col not in rules_df.columns:
                    rules_df[col] = None

            # Add the new rule
            rules_df.loc[new_index] = new_rule

            # Set the updated rules
            self._data_store.set_correction_rules(rules_df)

            # Commit the transaction
            self._data_store.commit_transaction()

            # Refresh the table
            self.refresh()

            # Return the new rule index
            return new_index

        except Exception as e:
            # Log the error and roll back the transaction
            self._logger.error(f"Error adding correction rule: {str(e)}")
            self._data_store.rollback_transaction()
            return -1

    def delete_rule(self, row_index: int) -> bool:
        """
        Delete a correction rule.

        Args:
            row_index: Index of the row to delete

        Returns:
            bool: True if the rule was deleted successfully, False otherwise
        """
        if not self._connected or row_index < 0 or row_index >= self._table_widget.rowCount():
            return False

        try:
            # Get the rule index from the first column
            item = self._table_widget.item(row_index, 0)
            if not item:
                return False

            rule_index = item.data(Qt.UserRole)
            if rule_index is None:
                return False

            # Start a transaction
            self._data_store.begin_transaction()

            # Get current rules
            rules_df = self._data_store.get_correction_rules()

            # Delete the rule
            if rule_index in rules_df.index:
                rules_df = rules_df.drop(rule_index)

                # Set the updated rules
                self._data_store.set_correction_rules(rules_df)

                # Commit the transaction
                self._data_store.commit_transaction()

                # Refresh the table
                self.refresh()

                return True
            else:
                self._data_store.rollback_transaction()
                return False

        except Exception as e:
            # Log the error and roll back the transaction
            self._logger.error(f"Error deleting correction rule: {str(e)}")
            self._data_store.rollback_transaction()
            return False

    def update_rule(
        self,
        rule_index: int,
        from_text: str = None,
        to_text: str = None,
        category: str = None,
        enabled: bool = None,
    ) -> bool:
        """
        Update a correction rule.

        Args:
            rule_index: Index of the rule to update
            from_text: New original text (optional)
            to_text: New corrected text (optional)
            category: New category (optional)
            enabled: New enabled state (optional)

        Returns:
            bool: True if the rule was updated successfully, False otherwise
        """
        if not self._connected:
            return False

        try:
            # Start a transaction
            self._data_store.begin_transaction()

            # Get current rules
            rules_df = self._data_store.get_correction_rules()

            # Check if the rule exists
            if rule_index not in rules_df.index:
                self._data_store.rollback_transaction()
                return False

            # Update the rule properties
            if from_text is not None:
                rules_df.at[rule_index, "from_text"] = from_text

            if to_text is not None:
                rules_df.at[rule_index, "to_text"] = to_text

            if category is not None and "category" in rules_df.columns:
                rules_df.at[rule_index, "category"] = category

            if enabled is not None and "enabled" in rules_df.columns:
                rules_df.at[rule_index, "enabled"] = enabled

            # Update the timestamp
            if "timestamp" in rules_df.columns:
                rules_df.at[rule_index, "timestamp"] = pd.Timestamp.now()

            # Set the updated rules
            self._data_store.set_correction_rules(rules_df)

            # Commit the transaction
            self._data_store.commit_transaction()

            # Refresh the table
            self.refresh()

            return True

        except Exception as e:
            # Log the error and roll back the transaction
            self._logger.error(f"Error updating correction rule: {str(e)}")
            self._data_store.rollback_transaction()
            return False
