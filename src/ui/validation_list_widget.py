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

from PySide6.QtCore import Qt, Signal, Slot, QModelIndex, QTimer, QPoint
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


class ValidationListItemModel(QStandardItemModel):
    """
    Model for validation list items.

    This model provides the data for the ValidationListWidget.

    Attributes:
        _items: List of validation items
        _validation_list: ValidationList instance
    """

    def __init__(self, validation_list: Optional[ValidationList] = None, parent=None):
        """
        Initialize the model.

        Args:
            validation_list: ValidationList instance
            parent: Parent widget
        """
        super().__init__(parent)

        self._validation_list = validation_list or ValidationList()
        self._items = self._validation_list.items.copy()

        # Set up model
        self.setColumnCount(1)
        self.setHeaderData(0, Qt.Horizontal, "Value")

        # Add items
        self._populate_model()

    def _populate_model(self):
        """Populate the model with items."""
        self.clear()
        self.setColumnCount(1)
        self.setHeaderData(0, Qt.Horizontal, "Value")

        for item in self._items:
            self.appendRow(QStandardItem(item))

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        """
        Set data at the specified index.

        This method is called when the user edits a cell in the view.

        Args:
            index: Model index of the item
            value: New value
            role: Data role

        Returns:
            bool: True if the data was set successfully, False otherwise
        """
        if not index.isValid() or role != Qt.EditRole:
            return False

        # Get the row and validate the value
        row = index.row()
        if row < 0 or row >= len(self._items):
            return False

        # Get the new value as a string
        new_value = str(value).strip()
        if not new_value:
            return False  # Don't accept empty values

        # Check if the value already exists
        if new_value in self._items and new_value != self._items[row]:
            return False  # Don't accept duplicate values

        # Update the item
        self._items[row] = new_value
        self.setItem(row, 0, QStandardItem(new_value))

        return True

    def flags(self, index: QModelIndex):
        """
        Get the flags for the specified index.

        Args:
            index: Model index

        Returns:
            Item flags
        """
        if not index.isValid():
            return Qt.NoItemFlags

        # Make items editable
        return super().flags(index) | Qt.ItemIsEditable

    def set_validation_list(self, validation_list):
        """
        Set the validation list.

        Args:
            validation_list: ValidationList instance or DataFrame
        """
        import logging
        import pandas as pd

        logger = logging.getLogger(__name__)

        # Check if validation_list is a method
        if callable(validation_list) and not hasattr(validation_list, "items"):
            logger.warning(f"validation_list is a method, cannot set in model")
            return

        # Determine what kind of object we have
        if isinstance(validation_list, pd.DataFrame):
            # It's a DataFrame
            self._validation_list = validation_list
            if validation_list.index.name == "entry":
                # Index is 'entry'
                self._items = list(validation_list.index)
            elif "entry" in validation_list.columns:
                # 'entry' is a column
                self._items = list(validation_list["entry"])
            else:
                # Just use whatever index it has
                self._items = list(validation_list.index)

        elif hasattr(validation_list, "items") and callable(validation_list.items):
            # It's an object with items() method
            try:
                self._validation_list = validation_list
                self._items = list(validation_list.items())
            except Exception as e:
                logger.warning(f"Could not get items from validation list: {e}")
                self._items = []

        elif hasattr(validation_list, "items") and not callable(validation_list.items):
            # It's a ValidationList with items attribute
            self._validation_list = validation_list
            self._items = validation_list.items.copy()

        elif hasattr(validation_list, "entries") and not callable(validation_list.entries):
            # It's a ValidationList with entries attribute
            self._validation_list = validation_list
            self._items = validation_list.entries.copy()

        else:
            # Not a valid object
            logger.error(f"Cannot set validation list: invalid type {type(validation_list)}")
            return

        self._populate_model()

    def get_validation_list(self) -> ValidationList:
        """
        Get the validation list.

        Returns:
            ValidationList instance
        """
        # Update the validation list with current items
        self._validation_list.items = self._items.copy()
        return self._validation_list

    def add_item(self, item: str):
        """
        Add an item.

        Args:
            item: Item to add
        """
        if item and item not in self._items:
            self._items.append(item)
            self.appendRow(QStandardItem(item))

    def update_item(self, index: int, item: str):
        """
        Update an item.

        Args:
            index: Index of item to update
            item: New item value
        """
        if 0 <= index < len(self._items) and item:
            old_item = self._items[index]
            if item != old_item and item not in self._items:  # Check for duplicates
                self._items[index] = item
                self.setItem(index, 0, QStandardItem(item))
                # Emit dataChanged signal
                model_index = self.index(index, 0)
                self.dataChanged.emit(model_index, model_index, [Qt.DisplayRole, Qt.EditRole])

    def delete_item(self, index: int):
        """
        Delete an item.

        Args:
            index: Index of item to delete
        """
        if 0 <= index < len(self._items):
            self._items.pop(index)
            self.removeRow(index)


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
    """

    # Signals
    list_updated = Signal(object)  # ValidationList

    def __init__(self, list_name: str, parent=None):
        """
        Initialize the widget.

        Args:
            list_name: Name of the validation list
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize properties
        self._list_name = list_name
        self._validation_list = ValidationList(name=list_name)
        self._model = ValidationListItemModel(self._validation_list)

        # Set up UI
        self._setup_ui()

    def set_validation_list(self, validation_list):
        """
        Compatibility method that calls set_list.

        Args:
            validation_list: ValidationList object or DataFrame
        """
        import logging
        import pandas as pd

        logger = logging.getLogger(__name__)
        logger.info(f"set_validation_list called for {self._list_name}, forwarding to set_list")

        # Check if validation_list is a method/function
        if callable(validation_list) and not hasattr(validation_list, "items"):
            logger.warning(f"validation_list is a method, cannot set in {self._list_name}")
            return

        # Now safe to proceed with set_list
        self.set_list(validation_list)

    def set_list(self, validation_list):
        """
        Set the validation list.

        Args:
            validation_list: ValidationList object
        """
        import logging
        import traceback
        import pandas as pd

        logger = logging.getLogger(__name__)

        # Add signal loop prevention
        if getattr(self, "_processing_signal", False):
            logger.warning(f"Skipping set_list for {self._list_name} due to signal loop prevention")
            return

        # Special check for DataFrames
        if isinstance(validation_list, pd.DataFrame):
            is_empty = validation_list.empty
        else:
            is_empty = not validation_list

        if is_empty:
            logger.warning(f"Empty validation list passed to {self._list_name}")
            return

        # Check if validation_list is a method
        if callable(validation_list) and not hasattr(validation_list, "items"):
            logger.warning(f"validation_list is a method, cannot set in {self._list_name}")
            return

        # Log item count if possible
        item_count = 0
        if hasattr(validation_list, "items"):
            if callable(validation_list.items):
                try:
                    items = validation_list.items()
                    item_count = len(items) if hasattr(items, "__len__") else 0
                except Exception as e:
                    logger.warning(f"Error getting items: {e}")
            else:
                item_count = (
                    len(validation_list.items) if hasattr(validation_list.items, "__len__") else 0
                )

        logger.info(
            f"ValidationListWidget.set_list called for {self._list_name} with approximately {item_count} items"
        )
        logger.info(f"Widget is visible: {self.isVisible()}")

        # Check if the validation list has a file path
        file_path = getattr(validation_list, "file_path", None)
        if file_path:
            logger.info(f"Validation list has file path: {file_path}")
        else:
            logger.warning(f"Validation list has no file path")

        try:
            self._processing_signal = True

            # Store the validation list
            self._validation_list = validation_list

            # Set in the model
            if self._model:
                logger.info(f"Setting validation list in model for {self._list_name}")
                self._model.set_validation_list(validation_list)

                # Log model state
                row_count = self._model.rowCount()
                logger.info(f"Model now has {row_count} rows")
            else:
                logger.error(f"No model exists for {self._list_name}")

            # Save to configuration
            if file_path:
                # Ensure file_path is a string
                file_path_str = str(file_path)
                logger.info(f"Saving file path to config: {file_path_str}")

                # Map list name to config key
                list_type_map = {
                    "Players": "player",
                    "Chest Types": "chest_type",
                    "Sources": "source",
                }

                list_type = list_type_map.get(self._list_name, self._list_name.lower())

                # Save in both config locations for redundancy
                config = ConfigManager()
                config.set("General", f"{list_type}_list_path", file_path_str)
                config.set("Validation", f"{list_type}_list", file_path_str)
                config.save()

                # Log saved paths
                general_path = config.get("General", f"{list_type}_list_path", "not set")
                validation_path = config.get("Validation", f"{list_type}_list", "not set")
                logger.info(
                    f"Saved paths in config - General: {general_path}, Validation: {validation_path}"
                )

            # UI updates
            self._table_view.reset()
            self._table_view.resizeColumnsToContents()
            self._table_view.viewport().update()

            # Schedule a delayed check
            QTimer.singleShot(500, self._delayed_refresh)

        except Exception as e:
            logger.error(f"Error in set_list: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            self._processing_signal = False

    def _delayed_refresh(self):
        """
        Perform a delayed refresh to ensure UI is properly updated.
        """
        import logging
        import traceback

        logger = logging.getLogger(__name__)
        logger.info(f"Performing delayed refresh for {self._list_name}")
        logger.info(f"Widget is visible: {self.isVisible()}")

        try:
            # Check if widget is visible
            if not self.isVisible():
                logger.warning(f"{self._list_name} widget not visible during refresh")
                return

            # Force visual updates
            self._table_view.reset()
            self._table_view.viewport().update()

            # Log state
            if hasattr(self._model, "rowCount"):
                row_count = self._model.rowCount()
                logger.info(f"Model shows {row_count} rows after refresh")

            # Verify validation list is stored
            if hasattr(self, "_validation_list"):
                # Handle items whether it's a method or attribute
                if hasattr(self._validation_list, "items"):
                    if callable(self._validation_list.items):
                        # It's a method
                        try:
                            items = self._validation_list.items()
                            item_count = len(items) if items is not None else 0
                            logger.info(f"Validation list has {item_count} items (from method)")
                        except Exception as e:
                            logger.warning(f"Couldn't get items from method: {e}")
                    else:
                        # It's an attribute
                        item_count = (
                            len(self._validation_list.items)
                            if self._validation_list.items is not None
                            else 0
                        )
                        logger.info(f"Validation list has {item_count} items (from attribute)")
                else:
                    logger.warning("Validation list has no 'items' attribute or method")

                # Get file path if available
                file_path = getattr(self._validation_list, "file_path", None)
                if file_path:
                    logger.info(f"File path: {file_path}")
                else:
                    logger.warning("Validation list has no file path")
            else:
                logger.warning("No validation list is stored!")

        except Exception as e:
            logger.error(f"Error in delayed refresh: {str(e)}")
            logger.error(traceback.format_exc())

    def get_list(self) -> ValidationList:
        """
        Get the validation list.

        Returns:
            ValidationList instance
        """
        return self._model.get_validation_list()

    @Slot()
    def _on_add(self):
        """Handle add button click."""
        dialog = ValidationListItemDialog(parent=self)
        if dialog.exec():
            item = dialog.item
            self._model.add_item(item)
            self._emit_list_updated()

    @Slot()
    def _on_edit(self):
        """Handle edit button click."""
        indexes = self._table_view.selectionModel().selectedRows()
        if indexes:
            row = indexes[0].row()
            item = self._model.data(self._model.index(row, 0))

            dialog = ValidationListItemDialog(item, parent=self)
            if dialog.exec():
                updated_item = dialog.item
                self._model.update_item(row, updated_item)
                self._emit_list_updated()

    @Slot()
    def _on_delete(self):
        """Handle delete button click."""
        indexes = self._table_view.selectionModel().selectedRows()
        if indexes:
            row = indexes[0].row()

            # Confirm deletion
            response = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete this item?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if response == QMessageBox.Yes:
                self._model.delete_item(row)
                self._emit_list_updated()

    @Slot()
    def _on_import(self):
        """Handle import button click."""
        # Determine list type from widget name
        list_type = "player"  # Default
        if "chest" in self._list_name.lower():
            list_type = "chest_type"
        elif "source" in self._list_name.lower():
            list_type = "source"

        file_filter = "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)"
        if list_type != "player":
            file_filter = "CSV Files (*.csv);;Text Files (*.txt);;All Files (*.*)"

        # Open file dialog
        file_path, selected_filter = QFileDialog.getOpenFileName(
            self,
            f"Import {self._list_name} List",
            str(Path.home()),
            file_filter,
        )

        if not file_path:
            return

        # Load items from file
        try:
            # Use ValidationList.load_from_file for consistent import behavior
            from src.models.validation_list import ValidationList

            logger = logging.getLogger(__name__)
            logger.info(f"Importing {list_type} list from {file_path}")

            # Load validation list
            imported_list = ValidationList.load_from_file(file_path, list_type=list_type)

            if imported_list.entries:
                # Confirm import
                response = QMessageBox.question(
                    self,
                    "Confirm Import",
                    f"Import {len(imported_list.entries)} items from {Path(file_path).name}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if response == QMessageBox.Yes:
                    # Add to validation list
                    for item in imported_list.entries:
                        self._model.add_item(item)

                    # Update validation list with file path for future reference
                    validation_list = self._model.get_validation_list()
                    validation_list.file_path = file_path

                    # Save file path to config
                    config = ConfigManager()
                    config.set("Files", "default_dir", str(Path(file_path).parent))
                    config.set("Files", f"default_{list_type}_list", file_path)
                    config.save()

                    logger.info(f"Saving file path to config: {file_path}")
                    logger.info(
                        f"Saved paths in config - General: {config.get('Files', 'default_dir')}, Validation: {config.get('Files', f'default_{list_type}_list')}"
                    )

                    # Emit signal
                    self._emit_list_updated()

                    # Show success message
                    QMessageBox.information(
                        self,
                        "Import Successful",
                        f"Imported {len(imported_list.entries)} items from {Path(file_path).name}.",
                    )
            else:
                QMessageBox.warning(
                    self, "Import Failed", f"No valid items found in {Path(file_path).name}."
                )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error importing items: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Import Error", f"Error importing items: {str(e)}")

    @Slot()
    def _on_export(self):
        """Handle export button click."""
        # Get validation list
        validation_list = self._model.get_validation_list()

        if not validation_list.items:
            QMessageBox.warning(self, "No Items", "There are no items to export.")
            return

        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {self._list_name} List",
            str(Path.home() / f"{self._list_name.lower()}_list.txt"),
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)",
        )

        if not file_path:
            return

        # Save items to file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for item in validation_list.items:
                    f.write(f"{item}\n")

            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(validation_list.items)} items to {Path(file_path).name}.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting items: {str(e)}")

    @Slot()
    def _on_selection_changed(self):
        """Handle selection changes in the table view."""
        selected = self._table_view.selectionModel().selectedRows()
        self._edit_button.setEnabled(len(selected) > 0)
        self._delete_button.setEnabled(len(selected) > 0)

    @Slot(QModelIndex, QModelIndex)
    def _on_data_changed(self, topLeft, bottomRight):
        """
        Handle data changes in the model.

        Args:
            topLeft: Top-left index of changed area
            bottomRight: Bottom-right index of changed area
        """
        # Emit the list_updated signal
        self._emit_list_updated()

    @Slot(QPoint)
    def _show_context_menu(self, pos):
        """
        Show context menu.

        Args:
            pos: Position where the context menu was requested
        """
        # Get the selected index
        index = self._table_view.indexAt(pos)
        if not index.isValid():
            return

        # Create the menu
        menu = QMenu(self)

        # Add actions
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self._on_edit_from_menu(index))

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._on_delete_from_menu(index))

        # Show the menu
        menu.exec_(self._table_view.viewport().mapToGlobal(pos))

    def _on_edit_from_menu(self, index):
        """
        Handle edit action from context menu.

        Args:
            index: Index of the item to edit
        """
        # Start editing the item
        self._table_view.edit(index)

    def _on_delete_from_menu(self, index):
        """
        Handle delete action from context menu.

        Args:
            index: Index of the item to delete
        """
        # Delete the item
        self._model.delete_item(index.row())
        self._emit_list_updated()

    def _emit_list_updated(self):
        """Emit list updated signal."""
        import logging

        logger = logging.getLogger(__name__)

        # Prevent signal loops
        if getattr(self, "_processing_signal", False):
            logger.warning(
                f"Skipping list_updated emission for {self._list_name} due to signal loop prevention"
            )
            return

        try:
            self._processing_signal = True
            validation_list = self._model.get_validation_list()
            logger.info(
                f"Emitting list_updated for {self._list_name} with {len(validation_list.items)} items"
            )
            self.list_updated.emit(validation_list)
        finally:
            self._processing_signal = False

    def _get_file_paths(self, list_type):
        """
        Get file paths from config.

        Args:
            list_type (str): Type of validation list

        Returns:
            tuple: (file_path, general_path, validation_path)
        """
        import logging

        logger = logging.getLogger(__name__)

        # Get config
        config = ConfigManager()

        # Use new consolidated path structure
        file_path = config.get_path(f"{list_type}_list_file")

        # For backward compatibility reporting, show the legacy paths too
        general_path = config.get("General", f"{list_type}_list_path", "not set")
        validation_path = config.get("Validation", f"{list_type}_list", "not set")

        logger.debug(f"File path for {list_type} list: {file_path}")
        logger.debug(f"Legacy paths - General: {general_path}, Validation: {validation_path}")

        return file_path, general_path, validation_path

    def _save_validation_list(self, list_type, file_path):
        """
        Save validation list to file and update config.

        Args:
            list_type (str): Type of validation list
            file_path (str): Path to the validation list file
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Saving {list_type} list to: {file_path}")

        validation_list = self._get_validation_list(list_type)
        if validation_list is None:
            logger.warning(f"No {list_type} list to save")
            return

        try:
            # Save the file
            validation_list.save_to_file(file_path)
            validation_list.file_path = file_path
            logger.info(
                f"Saved {list_type} list with {len(validation_list.items)} items to {file_path}"
            )

            # Update config using the new path API
            config = ConfigManager()
            config.set_path(f"{list_type}_list_file", file_path)

            # Update the validation directory in the config
            from pathlib import Path

            validation_dir = str(Path(file_path).parent)
            config.set_path("validation_dir", validation_dir)

            logger.info(f"Updated config with {list_type} list path: {file_path}")
        except Exception as e:
            logger.error(f"Error saving {list_type} list: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def model(self) -> ValidationListItemModel:
        """
        Get the model for the validation list.

        Returns:
            ValidationListItemModel: The model used by the widget
        """
        return self._model

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)

        # Create table
        self._table_view = QTableView()
        self._table_view.setModel(self._model)
        self._table_view.setSelectionBehavior(QTableView.SelectRows)
        self._table_view.setSelectionMode(QTableView.SingleSelection)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSortingEnabled(True)

        # Enable direct editing
        self._table_view.setEditTriggers(QTableView.DoubleClicked | QTableView.EditKeyPressed)

        # Set up context menu
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.customContextMenuRequested.connect(self._show_context_menu)

        # Configure header
        header = self._table_view.horizontalHeader()
        header.setStretchLastSection(True)

        # Add table to layout
        main_layout.addWidget(self._table_view)

        # Create buttons
        button_layout = QHBoxLayout()

        self._add_button = QPushButton("Add")
        self._add_button.clicked.connect(self._on_add)

        self._edit_button = QPushButton("Edit")
        self._edit_button.clicked.connect(self._on_edit)
        self._edit_button.setEnabled(False)

        self._delete_button = QPushButton("Delete")
        self._delete_button.clicked.connect(self._on_delete)
        self._delete_button.setEnabled(False)

        self._import_button = QPushButton("Import")
        self._import_button.clicked.connect(self._on_import)

        self._export_button = QPushButton("Export")
        self._export_button.clicked.connect(self._on_export)

        button_layout.addWidget(self._add_button)
        button_layout.addWidget(self._edit_button)
        button_layout.addWidget(self._delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self._import_button)
        button_layout.addWidget(self._export_button)

        # Add buttons to layout
        main_layout.addLayout(button_layout)

        # Connect selection signals
        self._table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # Connect editing signals
        self._model.dataChanged.connect(self._on_data_changed)
