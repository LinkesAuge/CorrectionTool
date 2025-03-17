"""
validation_list_widget.py

Description: Widget for managing validation lists
Usage:
    from src.ui.validation_list_widget import ValidationListWidget
    widget = ValidationListWidget("Players")
"""

from pathlib import Path
from typing import List, Optional, Set

from PySide6.QtCore import Qt, Signal, Slot, QModelIndex
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
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.models.validation_list import ValidationList


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

    def set_validation_list(self, validation_list: ValidationList):
        """
        Set the validation list.

        Args:
            validation_list: ValidationList instance
        """
        self._validation_list = validation_list
        self._items = validation_list.items.copy()
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
            self._items[index] = item
            self.setItem(index, 0, QStandardItem(item))

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

    def set_list(self, validation_list: ValidationList):
        """
        Set the validation list.

        Args:
            validation_list: ValidationList instance
        """
        self._validation_list = validation_list
        self._model.set_validation_list(validation_list)

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
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Import {self._list_name} List",
            str(Path.home()),
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)",
        )

        if not file_path:
            return

        # Load items from file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                items = [line.strip() for line in f if line.strip()]

            if items:
                # Confirm import
                response = QMessageBox.question(
                    self,
                    "Confirm Import",
                    f"Import {len(items)} items from {Path(file_path).name}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if response == QMessageBox.Yes:
                    # Add to validation list
                    for item in items:
                        self._model.add_item(item)

                    # Emit signal
                    self._emit_list_updated()

                    # Show success message
                    QMessageBox.information(
                        self,
                        "Import Successful",
                        f"Imported {len(items)} items from {Path(file_path).name}.",
                    )
            else:
                QMessageBox.warning(
                    self, "Import Failed", f"No valid items found in {Path(file_path).name}."
                )
        except Exception as e:
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
        """Handle selection changed."""
        has_selection = bool(self._table_view.selectionModel().selectedRows())
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

    def _emit_list_updated(self):
        """Emit list updated signal."""
        validation_list = self._model.get_validation_list()
        self.list_updated.emit(validation_list)
