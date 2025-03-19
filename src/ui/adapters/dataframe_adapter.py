"""
dataframe_adapter.py

Description: Adapter between DataFrameStore and UI components
Usage:
    from src.ui.adapters.dataframe_adapter import EntryTableAdapter
    adapter = EntryTableAdapter(table_widget)
    adapter.connect()
"""

import logging
from typing import Dict, List, Optional, Any, Callable
import pandas as pd
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QTableView, QTableWidget, QTableWidgetItem, QComboBox

from src.services.dataframe_store import DataFrameStore, EventType


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

    def _on_entries_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle entries updated event.

        Args:
            event_data: Event data dictionary
        """
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
            entries_df.at[entry_id, "original_values"] = original_values

            # Update entries in store
            self._store.set_entries(entries_df)

            # Commit the transaction
            self._store.commit_transaction()

            # Emit dataChanged signal
            self.dataChanged.emit(index, index, [role])

            return True

        except Exception as e:
            # Rollback the transaction on error
            self._store.rollback_transaction()
            self._logger.error(f"Error setting data: {e}")
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
    """

    # Signals
    dataChanged = Signal()

    def __init__(self, table_view: QTableView):
        """
        Initialize the EntryTableAdapter.

        Args:
            table_view: QTableView widget
        """
        super().__init__()
        self._table_view = table_view
        self._model = EntryTableModel()
        self._logger = logging.getLogger(__name__)

    def connect(self) -> None:
        """Connect the model to the view."""
        self._table_view.setModel(self._model)
        self._table_view.resizeColumnsToContents()
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._logger.info("EntryTableAdapter connected to view")

    def refresh(self) -> None:
        """Refresh the model data."""
        self._model.refresh_data()
        self._table_view.resizeColumnsToContents()
        self.dataChanged.emit()
        self._logger.info("EntryTableAdapter data refreshed")


class ValidationListComboAdapter(QObject):
    """
    Adapter between DataFrameStore validation lists and QComboBox.

    This class adapts a validation list in DataFrameStore to a QComboBox widget,
    handling the connection between the data store and UI.

    Attributes:
        _combo_box: QComboBox widget
        _store: DataFrameStore instance
        _list_type: Type of validation list ('chest_types', 'players', 'sources')
        itemSelected: Signal emitted when an item is selected
    """

    # Signals
    itemSelected = Signal(str)

    def __init__(self, combo_box: QComboBox, list_type: str):
        """
        Initialize the ValidationListComboAdapter.

        Args:
            combo_box: QComboBox widget
            list_type: Type of validation list ('chest_types', 'players', 'sources')
        """
        super().__init__()
        self._combo_box = combo_box
        self._store = DataFrameStore.get_instance()
        self._list_type = list_type
        self._logger = logging.getLogger(__name__)

        # Validate list type
        if list_type not in ["chest_types", "players", "sources"]:
            raise ValueError(f"Invalid validation list type: {list_type}")

        # Subscribe to events
        self._store.subscribe(EventType.VALIDATION_LIST_UPDATED, self._on_validation_list_updated)

        # Connect signals
        self._combo_box.currentTextChanged.connect(self._on_item_selected)

    def _on_validation_list_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle validation list updated event.

        Args:
            event_data: Event data dictionary
        """
        list_type = event_data.get("list_type", None)
        if list_type is None or list_type == self._list_type:
            self.refresh()

    def _on_item_selected(self, text: str) -> None:
        """
        Handle item selected event.

        Args:
            text: Selected item text
        """
        if text:
            self.itemSelected.emit(text)

    def connect(self) -> None:
        """Connect the adapter to the combo box."""
        self.refresh()
        self._logger.info(f"ValidationListComboAdapter connected to {self._list_type} combo box")

    def refresh(self) -> None:
        """Refresh the combo box data."""
        current_text = self._combo_box.currentText()

        # Clear the combo box
        self._combo_box.clear()

        # Get the validation list
        validation_list = self._store.get_validation_list(self._list_type)

        if not validation_list.empty:
            # Add items to combo box
            self._combo_box.addItems(validation_list["value"].tolist())

            # Restore selection if possible
            index = self._combo_box.findText(current_text)
            if index >= 0:
                self._combo_box.setCurrentIndex(index)

        self._logger.info(
            f"ValidationListComboAdapter refreshed with {self._combo_box.count()} items"
        )

    def get_current_item(self) -> str:
        """
        Get the currently selected item.

        Returns:
            str: Currently selected item text
        """
        return self._combo_box.currentText()

    def set_current_item(self, text: str) -> bool:
        """
        Set the currently selected item.

        Args:
            text: Item text to select

        Returns:
            bool: True if item was selected, False otherwise
        """
        index = self._combo_box.findText(text)
        if index >= 0:
            self._combo_box.setCurrentIndex(index)
            return True
        return False


class CorrectionRuleTableAdapter(QObject):
    """
    Adapter between DataFrameStore correction rules and QTableWidget.

    This class adapts the correction rules in DataFrameStore to a QTableWidget,
    handling the connection between the data store and UI.

    Attributes:
        _table_widget: QTableWidget widget
        _store: DataFrameStore instance
        ruleEnabled: Signal emitted when a rule is enabled/disabled
        ruleDeleted: Signal emitted when a rule is deleted
    """

    # Signals
    ruleEnabled = Signal(int, bool)
    ruleDeleted = Signal(int)

    def __init__(self, table_widget: QTableWidget):
        """
        Initialize the CorrectionRuleTableAdapter.

        Args:
            table_widget: QTableWidget widget
        """
        super().__init__()
        self._table_widget = table_widget
        self._store = DataFrameStore.get_instance()
        self._logger = logging.getLogger(__name__)

        # Subscribe to events
        self._store.subscribe(EventType.CORRECTION_RULES_UPDATED, self._on_correction_rules_updated)

    def _on_correction_rules_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle correction rules updated event.

        Args:
            event_data: Event data dictionary
        """
        self.refresh()

    def connect(self) -> None:
        """Connect the adapter to the table widget."""
        # Set up table columns
        self._table_widget.setColumnCount(5)
        self._table_widget.setHorizontalHeaderLabels(["ID", "From", "To", "Category", "Enabled"])

        # Set column widths
        self._table_widget.setColumnWidth(0, 50)  # ID
        self._table_widget.setColumnWidth(1, 200)  # From
        self._table_widget.setColumnWidth(2, 200)  # To
        self._table_widget.setColumnWidth(3, 100)  # Category
        self._table_widget.setColumnWidth(4, 80)  # Enabled

        # Load initial data
        self.refresh()

        self._logger.info("CorrectionRuleTableAdapter connected to table widget")

    def refresh(self) -> None:
        """Refresh the table widget data."""
        # Get correction rules
        rules_df = self._store.get_correction_rules()

        # Clear the table
        self._table_widget.setRowCount(0)

        if rules_df.empty:
            return

        # Set row count
        self._table_widget.setRowCount(len(rules_df))

        # Populate the table
        for i, (rule_id, rule) in enumerate(rules_df.iterrows()):
            # ID
            id_item = QTableWidgetItem(str(rule_id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self._table_widget.setItem(i, 0, id_item)

            # From
            from_item = QTableWidgetItem(rule["from_text"])
            self._table_widget.setItem(i, 1, from_item)

            # To
            to_item = QTableWidgetItem(rule["to_text"])
            self._table_widget.setItem(i, 2, to_item)

            # Category
            category_item = QTableWidgetItem(rule["category"])
            self._table_widget.setItem(i, 3, category_item)

            # Enabled
            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(enabled_item.flags() | Qt.ItemIsUserCheckable)
            enabled_item.setCheckState(Qt.Checked if rule["enabled"] else Qt.Unchecked)
            self._table_widget.setItem(i, 4, enabled_item)

        self._logger.info(f"CorrectionRuleTableAdapter refreshed with {len(rules_df)} rules")

    def get_rule_data(self, row: int) -> Optional[Dict[str, Any]]:
        """
        Get rule data for the given row.

        Args:
            row: Table row

        Returns:
            Optional[Dict[str, Any]]: Rule data, or None if row is invalid
        """
        if row < 0 or row >= self._table_widget.rowCount():
            return None

        rule_id = int(self._table_widget.item(row, 0).text())
        from_text = self._table_widget.item(row, 1).text()
        to_text = self._table_widget.item(row, 2).text()
        category = self._table_widget.item(row, 3).text()
        enabled = self._table_widget.item(row, 4).checkState() == Qt.Checked

        return {
            "id": rule_id,
            "from_text": from_text,
            "to_text": to_text,
            "category": category,
            "enabled": enabled,
        }

    def update_rule(self, row: int) -> bool:
        """
        Update a rule from table data.

        Args:
            row: Table row

        Returns:
            bool: True if rule was updated successfully, False otherwise
        """
        rule_data = self.get_rule_data(row)
        if not rule_data:
            return False

        try:
            rule_id = rule_data.pop("id")
            self._store.update_correction_rule(rule_id, rule_data)
            return True

        except Exception as e:
            self._logger.error(f"Error updating rule: {e}")
            return False

    def delete_rule(self, row: int) -> bool:
        """
        Delete a rule.

        Args:
            row: Table row

        Returns:
            bool: True if rule was deleted successfully, False otherwise
        """
        if row < 0 or row >= self._table_widget.rowCount():
            return False

        try:
            rule_id = int(self._table_widget.item(row, 0).text())
            self._store.remove_correction_rule(rule_id)
            self.ruleDeleted.emit(rule_id)
            return True

        except Exception as e:
            self._logger.error(f"Error deleting rule: {e}")
            return False

    def enable_rule(self, row: int, enabled: bool) -> bool:
        """
        Enable or disable a rule.

        Args:
            row: Table row
            enabled: Whether to enable or disable the rule

        Returns:
            bool: True if rule was enabled/disabled successfully, False otherwise
        """
        if row < 0 or row >= self._table_widget.rowCount():
            return False

        try:
            rule_id = int(self._table_widget.item(row, 0).text())
            self._store.update_correction_rule(rule_id, {"enabled": enabled})
            self.ruleEnabled.emit(rule_id, enabled)
            return True

        except Exception as e:
            self._logger.error(f"Error enabling/disabling rule: {e}")
            return False

    @Slot(int, int)
    def on_item_changed(self, row: int, column: int) -> None:
        """
        Handle item changed event.

        Args:
            row: Table row
            column: Table column
        """
        if column == 4:  # Enabled column
            enabled = self._table_widget.item(row, 4).checkState() == Qt.Checked
            rule_id = int(self._table_widget.item(row, 0).text())
            self.enable_rule(row, enabled)
        else:
            self.update_rule(row)
