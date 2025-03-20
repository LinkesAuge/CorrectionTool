"""
validation_list_widget.py

Description: Widget for managing validation lists
Usage:
    from src.ui.validation_list_widget import ValidationListWidget
    widget = ValidationListWidget("Players")
"""

import logging
from pathlib import Path
from typing import List, Optional, Set

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QModelIndex,
    QTimer,
    QPoint,
    QAbstractTableModel,
    QItemSelectionModel,
    QObject,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.models.validation_list import ValidationList
from src.services.config_manager import ConfigManager


class ValidationListItemModel(QAbstractTableModel):
    """Model for the items in a validation list."""

    def __init__(self, validation_list_or_parent=None):
        """
        Initialize the model.

        Args:
            validation_list_or_parent: Either a ValidationList instance or a parent QObject
        """
        # If the first argument is a ValidationList, use it for data and None as parent
        if hasattr(validation_list_or_parent, "items") and not isinstance(
            validation_list_or_parent, QObject
        ):
            parent = None
            validation_list = validation_list_or_parent
        else:
            parent = validation_list_or_parent
            validation_list = None

        super().__init__(parent)

        self._items = []
        self._all_items = []
        self._search_term = ""

        # If we have a validation list, populate from it
        if validation_list:
            self.populate(validation_list)

    def populate(self, validation_list):
        """
        Set the validation list and populate the model with items.

        Args:
            validation_list (ValidationList): The validation list to display
        """
        self.beginResetModel()
        if validation_list:
            self._all_items = [item for item in validation_list.items]
            self._filter_items()
        else:
            self._all_items = []
            self._items = []
        self.endResetModel()

    def _filter_items(self):
        """Filter items based on the current search term."""
        if not self._search_term:
            self._items = self._all_items.copy()
        else:
            self._items = [item for item in self._all_items if self._matches_filter(item)]

        # Signal that the model has changed
        self.layoutChanged.emit()

    def _matches_filter(self, item):
        """
        Check if an item matches the current filter.

        Args:
            item (str): The item to check

        Returns:
            bool: True if the item matches the filter, False otherwise
        """
        if not self._search_term:
            return True
        return self._search_term.lower() in item.lower()

    def rowCount(self, parent=QModelIndex()):
        """Return the number of rows in the model."""
        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        """Return the number of columns in the model."""
        return 1

    def data(self, index, role=Qt.DisplayRole):
        """Return the data for the given index and role."""
        if not index.isValid():
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self._items[index.row()]

        return None

    def setData(self, index, value, role=Qt.EditRole):
        """Set the data for the given index and role."""
        if not index.isValid() or role != Qt.EditRole:
            return False

        # Cast to string and strip whitespace
        value = str(value).strip()

        # Don't accept empty values
        if not value:
            return False

        if value == self._items[index.row()]:
            return False

        # Check for duplicates
        if value in self._all_items:
            return False

        # Find the item in the all_items list
        old_value = self._items[index.row()]
        all_items_index = self._all_items.index(old_value)

        # Update both lists
        self._all_items[all_items_index] = value
        self._items[index.row()] = value

        self.dataChanged.emit(index, index, [role])
        return True

    def flags(self, index):
        """Return the flags for the given index."""
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return the header data for the given section, orientation and role."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return "Item"

        return None

    def add_item(self, item):
        """
        Add an item to the model.

        Args:
            item (str): The item to add
        """
        # Add to the full list
        self._all_items.append(item)

        # If it matches the filter, add to the visible list
        if self._matches_filter(item):
            self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
            self._items.append(item)
            self.endInsertRows()

    def update_item(self, index, new_value):
        """
        Update an item in the model.

        Args:
            index (QModelIndex or int): The index of the item to update
            new_value (str): The new value for the item

        Returns:
            bool: True if the item was updated successfully
        """
        # Convert integer index to QModelIndex if needed
        if isinstance(index, int):
            index = self.index(index, 0)

        if not index.isValid():
            return False

        old_value = self._items[index.row()]
        # Find in the all_items list
        all_items_index = self._all_items.index(old_value)

        # Update both lists
        self._all_items[all_items_index] = new_value

        # If the updated item still matches the filter, update it
        if self._matches_filter(new_value):
            self._items[index.row()] = new_value
            self.dataChanged.emit(index, index)
            return True
        else:
            # If it no longer matches, remove it from the visible list
            self.beginRemoveRows(QModelIndex(), index.row(), index.row())
            self._items.pop(index.row())
            self.endRemoveRows()
            return True

    def delete_item(self, index):
        """
        Delete an item from the model.

        Args:
            index (QModelIndex): The index of the item to delete
        """
        if not index.isValid():
            return False

        # Get the item to delete
        item_to_delete = self._items[index.row()]

        # Remove from visible items
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._items.pop(index.row())
        self.endRemoveRows()

        # Also remove from the all items list
        self._all_items.remove(item_to_delete)

        return True

    def set_search_term(self, term):
        """
        Set the search term and filter the items.

        Args:
            term (str): The search term
        """
        if self._search_term == term:
            return

        self._search_term = term
        self._filter_items()

    def get_all_items(self):
        """
        Get all items in the model, regardless of filtering.

        Returns:
            list: All items in the model
        """
        return self._all_items.copy()

    def get_filtered_items(self):
        """
        Get the filtered items (currently visible).

        Returns:
            list: The filtered items
        """
        return self._items.copy()


class ValidationListItemDialog(QDialog):
    """
    Dialog for editing a validation list item.
    """

    def __init__(self, item: str = "", parent=None):
        """
        Initialize the dialog.

        Args:
            item: Item to edit
            parent: Parent widget
        """
        super().__init__(parent)

        self.item = item

        self.setWindowTitle("Edit Item" if item else "New Item")
        self.setMinimumWidth(300)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Form layout for fields
        form_layout = QFormLayout()

        # Item value
        self._item_edit = QLineEdit(self.item)
        form_layout.addRow("Value:", self._item_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        """Handle dialog acceptance."""
        # Validate fields
        item = self._item_edit.text().strip()

        if not item:
            QMessageBox.warning(self, "Validation Error", "Item value cannot be empty.")
            return

        # Update item
        self.item = item

        super().accept()


class ValidationListWidget(QWidget):
    """
    Widget for managing validation lists.

    This widget provides a UI for managing validation lists.

    Signals:
        list_updated: Signal emitted when the validation list is updated

    Attributes:
        _model: Model for validation list items
        _list_name: Name of the validation list
        _validation_list: ValidationList instance
        _search_field: QLineEdit for searching the list
    """

    # Signals
    list_updated = Signal(ValidationList)

    def __init__(self, list_name: str, parent=None):
        """
        Initialize the widget.

        Args:
            list_name: Name of the validation list
            parent: Parent widget
        """
        super().__init__(parent)

        self._list_name = list_name
        self._validation_list = ValidationList(name=list_name)
        self._model = ValidationListItemModel(self)
        self._search_field = QLineEdit(self)

        # Setup UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

        # Set the validation list
        self.set_list(self._validation_list)

    def set_validation_list(self, validation_list):
        """
        Set the validation list.

        Args:
            validation_list: ValidationList instance or DataFrame
        """
        self._validation_list = validation_list
        self._model.populate(validation_list)
        self._delayed_refresh()

    def set_list(self, validation_list):
        """
        Legacy method for setting the validation list.

        This method is kept for compatibility with existing code.

        Args:
            validation_list: ValidationList instance or DataFrame
        """
        import pandas as pd

        logger = logging.getLogger(__name__)

        # Check the type to count the number of items
        if isinstance(validation_list, pd.DataFrame):
            if validation_list.empty:
                item_count = 0
            else:
                item_count = len(validation_list)
        elif hasattr(validation_list, "items") and callable(validation_list.items):
            try:
                item_count = len(validation_list.items())
            except:
                item_count = "unknown"
        elif hasattr(validation_list, "items") and not callable(validation_list.items):
            item_count = len(validation_list.items)
        elif hasattr(validation_list, "entries") and not callable(validation_list.entries):
            item_count = len(validation_list.entries)
        else:
            item_count = "unknown"

        logger.info(
            f"ValidationListWidget.set_list called for {self._list_name} with approximately {item_count} items"
        )

        self.set_validation_list(validation_list)

    def _delayed_refresh(self):
        """Refresh the widget after a short delay to avoid UI freezes."""
        # Use a timer to ensure the UI doesn't freeze
        refresh_timer = QTimer(self)
        refresh_timer.setSingleShot(True)
        refresh_timer.timeout.connect(self._refresh_ui)
        refresh_timer.start(50)  # 50ms delay

    def _refresh_ui(self):
        """Refresh the UI to reflect the current model."""
        # Ensure the model is up to date
        self._table_view.resizeColumnsToContents()
        self._table_view.resizeRowsToContents()

        # Update button states
        self._on_selection_changed()

        # Emit list updated signal
        self._emit_list_updated()

    def get_list(self) -> ValidationList:
        """
        Get the validation list.

        Returns:
            ValidationList instance
        """
        # Update the validation list with current items
        self._validation_list.items = self._model.get_all_items()
        return self._validation_list

    @Slot()
    def _on_add(self):
        """Handle the add button click."""
        # Create and show the dialog
        dialog = ValidationListItemDialog(parent=self)
        if dialog.exec():
            # Get the value
            value = dialog.item.strip()
            if value:
                # Add the value to the model
                self._model.add_item(value)
                # Emit list updated signal
                self._emit_list_updated()

    @Slot()
    def _on_edit(self):
        """Handle the edit button click."""
        # Get the selected index
        index = self._table_view.selectionModel().currentIndex()
        if index.isValid():
            # Get the value
            value = self._model.data(index, Qt.DisplayRole)
            # Create and show the dialog
            dialog = ValidationListItemDialog(value, parent=self)
            if dialog.exec():
                # Get the new value
                new_value = dialog.item.strip()
                if new_value and new_value != value:
                    # Update the value in the model
                    self._model.update_item(index, new_value)
                    # Emit list updated signal
                    self._emit_list_updated()

    @Slot()
    def _on_delete(self):
        """Handle delete button click."""
        # Get selected indexes
        selection_model = self._table_view.selectionModel()
        if not selection_model.hasSelection():
            return

        index = selection_model.selectedIndexes()[0]
        item = self._model.data(index)

        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{item}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result == QMessageBox.Yes:
            # Delete the value from the model
            self._model.delete_item(index)
            # Emit list updated signal
            self._emit_list_updated()

    @Slot()
    def _on_import(self):
        """Handle the import button click."""
        # Get the file paths using the helper method
        import_path, file_paths = self._get_file_paths(self._list_name)
        if not import_path:
            return

        # Open the file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Import {self._list_name} Validation List",
            str(import_path),
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*.*)",
        )

        if not file_path:
            return

        # Create a ConfigManager to save the path
        config = ConfigManager.get_instance()
        if config and hasattr(config, "set_path"):
            # Use the new path API if available
            config.set_path(f"validation_list_{self._list_name.lower()}", file_path)
        elif config:
            # Fall back to the old API
            config.set_value("Paths", f"validation_list_{self._list_name.lower()}", file_path)

        # Load the validation list
        try:
            import pandas as pd

            if file_path.lower().endswith(".csv"):
                # CSV file
                df = pd.read_csv(file_path)

                # Try to find the column with the validation entries
                if "entry" in df.columns:
                    # Use the 'entry' column
                    validation_list = ValidationList(
                        list_type=self._list_name.lower(),
                        entries=df["entry"].tolist(),
                        name=self._list_name,
                    )
                elif df.shape[1] == 1:
                    # Single column, use it
                    validation_list = ValidationList(
                        list_type=self._list_name.lower(),
                        entries=df.iloc[:, 0].tolist(),
                        name=self._list_name,
                    )
                else:
                    # Multiple columns, use the first one
                    validation_list = ValidationList(
                        list_type=self._list_name.lower(),
                        entries=df.iloc[:, 0].tolist(),
                        name=self._list_name,
                    )
            else:
                # Text file, assume one entry per line
                with open(file_path, "r") as f:
                    entries = [line.strip() for line in f if line.strip()]

                validation_list = ValidationList(
                    list_type=self._list_name.lower(),
                    entries=entries,
                    name=self._list_name,
                )

            # Set the validation list
            self.set_validation_list(validation_list)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Error importing validation list: {str(e)}",
            )

    @Slot()
    def _on_export(self):
        """Handle the export button click."""
        # Get the file paths using the helper method
        export_path, _ = self._get_file_paths(self._list_name)
        if not export_path:
            return

        # Open the file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {self._list_name} Validation List",
            str(export_path),
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*.*)",
        )

        if not file_path:
            return

        # Save the validation list
        try:
            self._save_validation_list(self._list_name.lower(), file_path)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting validation list: {str(e)}",
            )

    @Slot()
    def _on_selection_changed(self):
        """Handle selection changes in the table view."""
        # Update button states based on selection
        has_selection = self._table_view.selectionModel().hasSelection()
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

    @Slot(QModelIndex, QModelIndex)
    def _on_data_changed(self, topLeft, bottomRight):
        """Handle data changes in the model."""
        # Emit list updated signal
        self._emit_list_updated()

    @Slot(QPoint)
    def _show_context_menu(self, pos):
        """
        Show a context menu at the specified position.

        Args:
            pos: Position to show the menu
        """
        # Get the model index at the position
        index = self._table_view.indexAt(pos)
        if not index.isValid():
            return

        # Create the menu
        menu = QMenu(self)

        # Add actions
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")

        # Show the menu and handle the selected action
        action = menu.exec(self._table_view.viewport().mapToGlobal(pos))
        if action == edit_action:
            self._on_edit_from_menu(index)
        elif action == delete_action:
            self._on_delete_from_menu(index)

    def _on_edit_from_menu(self, index):
        """
        Handle edit action from context menu.

        Args:
            index: Model index of the item to edit
        """
        # Start editing the cell
        self._table_view.edit(index)

    def _on_delete_from_menu(self, index):
        """
        Handle delete action from context menu.

        Args:
            index: Model index of the item to delete
        """
        # Get the value
        value = self._model.data(index, Qt.DisplayRole)
        # Confirm deletion
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{value}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            # Delete the value from the model
            self._model.delete_item(index)
            # Emit list updated signal
            self._emit_list_updated()

    def _emit_list_updated(self):
        """Emit the list_updated signal."""
        # Get the validation list from the model
        validation_list = self.get_list()

        # Set the name if it's not already set
        if not validation_list.name or validation_list.name == "unnamed":
            validation_list.name = self._list_name

        # Set the list type if it's not already set
        if not validation_list.list_type:
            validation_list.list_type = self._list_name.lower()

        # Emit the signal
        self.list_updated.emit(validation_list)

    def _get_file_paths(self, list_type):
        """
        Get the file paths for import/export.

        Args:
            list_type: Type of validation list

        Returns:
            tuple: (path, list of paths)
        """
        config = ConfigManager.get_instance()
        if not config:
            return Path.home(), []

        # Use the new path API if available
        if hasattr(config, "get_path"):
            # Get the last used path
            last_path = config.get_path(f"validation_list_{list_type.lower()}")

            # Get the default paths
            data_dir = config.get_path("data_dir")
            validation_dir = config.get_path("validation_dir")

            # Use the most specific path available
            if last_path and Path(last_path).parent.exists():
                return Path(last_path).parent, [last_path, validation_dir, data_dir, Path.home()]
            elif validation_dir and Path(validation_dir).exists():
                return Path(validation_dir), [validation_dir, data_dir, Path.home()]
            elif data_dir and Path(data_dir).exists():
                return Path(data_dir), [data_dir, Path.home()]
            else:
                return Path.home(), [Path.home()]
        else:
            # Fall back to the old API
            last_path = config.get_value("Paths", f"validation_list_{list_type.lower()}", "")

            if last_path and Path(last_path).parent.exists():
                return Path(last_path).parent, [last_path]
            else:
                return Path.home(), [Path.home()]

    def _save_validation_list(self, list_type, file_path):
        """
        Save the validation list to a file.

        Args:
            list_type: Type of validation list
            file_path: Path to save the file
        """
        import pandas as pd

        # Get the validation list
        validation_list = self.get_list()

        # Create a DataFrame from the validation list
        df = pd.DataFrame({"entry": validation_list.items})

        # Save the DataFrame to a file
        if file_path.lower().endswith(".csv"):
            # CSV file
            df.to_csv(file_path, index=False)
        else:
            # Text file, one entry per line
            with open(file_path, "w") as f:
                for entry in validation_list.items:
                    f.write(f"{entry}\n")

        # Create a ConfigManager to save the path
        config = ConfigManager.get_instance()
        if config and hasattr(config, "set_path"):
            # Use the new path API if available
            config.set_path(f"validation_list_{list_type}", file_path)
        elif config:
            # Fall back to the old API
            config.set_value("Paths", f"validation_list_{list_type}", file_path)

    def _setup_ui(self):
        """Set up the UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search layout
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self._search_field.setPlaceholderText("Enter search term...")
        self._search_field.setClearButtonEnabled(True)
        self._search_field.textChanged.connect(self._on_search_changed)

        self._clear_button = QPushButton("Clear")
        self._clear_button.clicked.connect(self._on_clear_search)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_field, 1)
        search_layout.addWidget(self._clear_button)

        layout.addLayout(search_layout)

        # Create table view
        self._table_view = QTableView(self)
        self._table_view.setModel(self._model)
        self._table_view.setSelectionBehavior(QTableView.SelectRows)
        self._table_view.setSelectionMode(QTableView.SingleSelection)
        self._table_view.setEditTriggers(QTableView.DoubleClicked | QTableView.EditKeyPressed)
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        # Add table view to layout
        layout.addWidget(self._table_view)

        # Create button layout
        button_layout = QHBoxLayout()

        # Create buttons
        self._add_button = QPushButton("Add", self)
        self._edit_button = QPushButton("Edit", self)
        self._delete_button = QPushButton("Delete", self)
        self._import_button = QPushButton("Import", self)
        self._export_button = QPushButton("Export", self)

        # Add buttons to layout
        button_layout.addWidget(self._add_button)
        button_layout.addWidget(self._edit_button)
        button_layout.addWidget(self._delete_button)
        button_layout.addWidget(self._import_button)
        button_layout.addWidget(self._export_button)

        # Add button layout to main layout
        layout.addLayout(button_layout)

        # Set button states
        self._edit_button.setEnabled(False)
        self._delete_button.setEnabled(False)

        # Enable direct editing
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)

        # Connect signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect signals."""
        # Button signals
        self._add_button.clicked.connect(self._on_add)
        self._edit_button.clicked.connect(self._on_edit)
        self._delete_button.clicked.connect(self._on_delete)
        self._import_button.clicked.connect(self._on_import)
        self._export_button.clicked.connect(self._on_export)

        # Table view signals
        selection_model = self._table_view.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self._on_selection_changed)

        # Model signals
        self._model.dataChanged.connect(self._on_data_changed)

        # Context menu signal
        self._table_view.customContextMenuRequested.connect(self._show_context_menu)

        # Search signals - search_field.textChanged is already connected in _setup_ui
        # No need to connect _clear_search_button as it's handled in _setup_ui
        pass

    @Slot(str)
    def _on_search_changed(self, text):
        """
        Handle changes in the search field.

        Args:
            text (str): Current text in the search field
        """
        # Get current selection
        table_view = self._table_view
        selection_model = table_view.selectionModel()
        selected_items = []

        if selection_model and selection_model.hasSelection():
            # Store the selected items before filtering
            for index in selection_model.selectedIndexes():
                item = self._model.data(index)
                selected_items.append(item)

        # Set the search term and filter the items
        self._model.set_search_term(text)

        # Restore selection if possible
        if selected_items:
            selection_model.clearSelection()
            # Try to select the previously selected items if they're still visible
            for i in range(self._model.rowCount()):
                item = self._model.data(self._model.index(i, 0))
                if item in selected_items:
                    # Select this item
                    index = self._model.index(i, 0)
                    selection_model.select(index, QItemSelectionModel.Select)

    @Slot()
    def _on_clear_search(self):
        """Clear the search field."""
        self._search_field.clear()
        self._on_search_changed("")

    def model(self):
        """
        Get the model used by this widget.

        Returns:
            ValidationListItemModel: The model
        """
        return self._model

    def get_items(self):
        """
        Get the items in the list.

        Returns:
            list: List of items
        """
        return self.get_list().items

    def add_item(self, item):
        """
        Add an item to the list.

        Args:
            item (str): Item to add
        """
        self._model.add_item(item)
        self._emit_list_updated()

    def delete_item(self, item):
        """
        Delete an item from the list.

        Args:
            item (str): Item to delete
        """
        # Find the item in the model
        for i in range(self._model.rowCount()):
            if self._model.data(self._model.index(i, 0)) == item:
                self._model.delete_item(self._model.index(i, 0))
                self._emit_list_updated()
                break
