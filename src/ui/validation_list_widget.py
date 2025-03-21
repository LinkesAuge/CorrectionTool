"""
validation_list_widget.py

Description: Widget for managing validation lists
Usage:
    from src.ui.validation_list_widget import ValidationListWidget
    widget = ValidationListWidget("Players")
"""

import logging
import os
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
    QStringListModel,
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
    QListWidget,
    QInputDialog,
    QGroupBox,
    QAbstractItemView,
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
    Widget for displaying and interacting with validation lists.

    This widget provides a searchable list view with buttons for adding,
    editing, deleting, importing and exporting validation list entries.

    Signals:
        list_updated: Emitted when the list is updated

    Attributes:
        _list: The validation list
        _model: The model for the list view
        _config: Configuration manager for saving/loading paths
    """

    list_updated = Signal(object)  # ValidationList

    def __init__(
        self,
        list_type: str,
        validation_list,
        config_manager,
        parent=None,
        with_actions=True,
        search_placeholder="Search...",
        list_tooltip="Double-click to edit",
    ):
        """
        Initialize the ValidationListWidget.

        Args:
            list_type: The type of validation list (player, chest_type, source)
            validation_list: The validation list data
            config_manager: Configuration manager for saving/loading settings
            parent: The parent widget
            with_actions: Whether to show the action buttons
            search_placeholder: The placeholder text for the search field
            list_tooltip: The tooltip for the list view
        """
        super().__init__(parent)
        self._list_type = list_type
        self._list = validation_list
        self._config_manager = config_manager
        self._with_actions = with_actions
        self._search_placeholder = search_placeholder
        self._list_tooltip = list_tooltip
        self._model = QStringListModel()
        self._filtered_model = QStringListModel()
        self._search_term = ""  # Initialize the search term

        # Create UI
        self._setup_ui()

        # Populate the widget
        self.populate()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Search input
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self._search_input = QLineEdit()
        if self._search_placeholder:
            self._search_input.setPlaceholderText(self._search_placeholder)
        else:
            self._search_input.setPlaceholderText("Filter items...")
        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_input)

        # List view
        self._list_view = QListView()
        self._list_view.setModel(self._filtered_model)
        self._list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._list_view.setSelectionMode(QListView.SingleSelection)

        # Create group boxes for organizing controls
        edit_group = QGroupBox("Edit")
        edit_layout = QHBoxLayout(edit_group)

        # Edit buttons
        self._add_button = QPushButton("Add")
        self._edit_button = QPushButton("Edit")
        self._delete_button = QPushButton("Delete")

        # Add buttons to edit layout
        edit_layout.addWidget(self._add_button)
        edit_layout.addWidget(self._edit_button)
        edit_layout.addWidget(self._delete_button)

        # Import/Export group
        import_export_group = QGroupBox("Import/Export")
        import_export_layout = QHBoxLayout(import_export_group)

        # Import/Export buttons
        self._import_button = QPushButton("Import...")
        self._export_button = QPushButton("Export...")

        # Add buttons to import/export layout
        import_export_layout.addWidget(self._import_button)
        import_export_layout.addWidget(self._export_button)

        # Add all elements to main layout
        layout.addLayout(search_layout)
        layout.addWidget(self._list_view)
        layout.addWidget(edit_group)
        layout.addWidget(import_export_group)

        # Connect signals
        self._search_input.textChanged.connect(self._filter_items)
        self._list_view.clicked.connect(self._on_item_clicked)
        self._add_button.clicked.connect(self.add_item)
        self._edit_button.clicked.connect(self.edit_item)
        self._delete_button.clicked.connect(self.delete_item)
        self._import_button.clicked.connect(self._import_list)
        self._export_button.clicked.connect(self._export_list)

        # Initially disable edit and delete buttons until an item is selected
        self._edit_button.setEnabled(False)
        self._delete_button.setEnabled(False)

    def populate(self):
        """Populate the list view with items from the validation list."""
        # Handle different types of validation_list objects
        if hasattr(self._list, "get_all_items"):
            # It's a ValidationListItemModel
            items = self._list.get_all_items()
        elif hasattr(self._list, "items"):
            # It's a ValidationList object
            if callable(self._list.items):
                # It's a method
                items = self._list.items()
            else:
                # It's a property/attribute
                items = self._list.items
        elif hasattr(self._list, "to_list"):
            # It's a DataFrame
            if len(self._list.columns) > 0:
                # Take the first column if multiple columns exist
                items = self._list.iloc[:, 0].to_list()
            else:
                items = []
        else:
            # Try a basic list conversion
            try:
                items = list(self._list)
            except (TypeError, ValueError):
                logging.getLogger(__name__).error(
                    f"Couldn't convert validation list of type {type(self._list)} to a list"
                )
                items = []

        self._model.setStringList(items)
        self._filtered_model.setStringList(items)
        self._list_view.setModel(self._filtered_model)

    def _filter_items(self, text: str = None):
        """Filter the list based on the search text."""
        # Use saved search term if no text is provided
        if text is not None:
            self._search_term = text

        # Get the items using the same approach as populate()
        if hasattr(self._list, "get_all_items"):
            # It's a ValidationListItemModel
            items = self._list.get_all_items()
        elif hasattr(self._list, "items"):
            # It's a ValidationList object
            if callable(self._list.items):
                # It's a method
                items = self._list.items()
            else:
                # It's a property/attribute
                items = self._list.items
        elif hasattr(self._list, "to_list"):
            # It's a DataFrame
            if len(self._list.columns) > 0:
                # Take the first column if multiple columns exist
                items = self._list.iloc[:, 0].to_list()
            else:
                items = []
        else:
            # Try a basic list conversion
            try:
                items = list(self._list)
            except (TypeError, ValueError):
                logging.getLogger(__name__).error(
                    f"Couldn't convert validation list of type {type(self._list)} to a list"
                )
                items = []

        # Filter items based on search term
        filtered_items = [
            item
            for item in items
            if not self._search_term or self._search_term.lower() in str(item).lower()
        ]

        self._filtered_model.setStringList(filtered_items)
        self._list_view.setModel(self._filtered_model)

    def _on_item_clicked(self, index):
        """Handle item selection."""
        self._selected_item = self._filtered_model.data(index, Qt.DisplayRole)
        self._edit_button.setEnabled(True)
        self._delete_button.setEnabled(True)

    def add_item(self):
        """Add a new item to the validation list."""
        # Show input dialog to get new item
        text, ok = QInputDialog.getText(self, "Add Item", "Enter new item:")
        if ok and text.strip():
            self._list.add_item(text)
            self.populate()
            self.list_updated.emit(self._list)

    def edit_item(self):
        """Edit the selected item."""
        if self._selected_item:
            dialog = ValidationListItemDialog(self._selected_item, self)
            if dialog.exec() == QDialog.Accepted:
                self._list.update_item(self._selected_item, dialog.item)
                self.populate()
                self.list_updated.emit(self._list)

    def delete_item(self):
        """Delete the selected item."""
        if self._selected_item:
            self._list.remove_item(self._selected_item)
            self.populate()
            self.list_updated.emit(self._list)

    def _import_list(self):
        """Import validation list from a file."""
        # Get the directory path to use as initial dir
        initial_dir = str(Path.home())
        if self._config_manager:
            config_dir = self._config_manager.get_path("validation_dir")
            if config_dir:
                initial_dir = config_dir

        # Get the file to import from
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Import {self._list_type} List",
            initial_dir,
            "Text Files (*.txt *.csv);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            # Load the validation list from file
            imported_list = ValidationList.load_from_file(
                file_path, list_type=self._list_type, config_manager=self._config_manager
            )

            if not imported_list.entries:
                QMessageBox.warning(
                    self, "Import Error", f"No valid entries found in the selected file."
                )
                return

            # Update our list with the imported one
            self._list = imported_list
            self.populate()

            # Save the directory path for future use
            if self._config_manager:
                dir_path = os.path.dirname(file_path)
                self._config_manager.set_path("validation_dir", dir_path)

            # Show success message
            QMessageBox.information(
                self,
                "Import Successful",
                f"Successfully imported {len(self._list.entries)} {self._list_type} entries.",
            )

            # Emit the list_updated signal
            self.list_updated.emit(self._list)

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error importing {self._list_type} list: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Import Error", f"Failed to import list: {str(e)}")

    def _export_list(self):
        """Export validation list to a file."""
        # Check if list is empty
        if not self._list.entries:
            QMessageBox.warning(
                self,
                "Empty List",
                f"The {self._list_type} list is empty. There's nothing to export.",
            )
            return

        # Get the directory path to use as initial dir
        initial_dir = str(Path.home())
        if self._config_manager:
            config_dir = self._config_manager.get_path("validation_dir")
            if config_dir:
                initial_dir = config_dir

        # Default filename
        default_filename = f"{self._list_type}_list.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {self._list_type} List",
            os.path.join(initial_dir, default_filename),
            "Text Files (*.txt *.csv);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            # Save the validation list to file
            self._list.save_to_file(file_path)

            # Save the directory path for future use
            if self._config_manager:
                dir_path = os.path.dirname(file_path)
                self._config_manager.set_path("validation_dir", dir_path)

            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Successfully exported {len(self._list.entries)} {self._list_type} entries to {file_path}.",
            )

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error exporting {self._list_type} list: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"Failed to export list: {str(e)}")

    def get_list(self) -> ValidationList:
        """
        Get the validation list.

        Returns:
            The validation list
        """
        return self._list

    def get_items(self) -> List[str]:
        """
        Get all items in the list.

        Returns:
            List of all items
        """
        return self._list.get_all_items()
