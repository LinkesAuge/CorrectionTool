"""
entry_edit_dialog.py

Description: Dialog for editing a chest entry
Usage:
    from src.ui.entry_edit_dialog import EntryEditDialog
    dialog = EntryEditDialog(entry, parent)
    if dialog.exec():
        edited_entry = dialog.get_entry()
"""

from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
)

from src.models.chest_entry import ChestEntry


class EntryEditDialog(QDialog):
    """
    Dialog for editing a chest entry.

    This dialog allows editing the fields of a chest entry and provides validation
    for the entered values.

    Attributes:
        _entry: The chest entry being edited
        _fields: Dictionary of field editors
    """

    def __init__(self, entry: ChestEntry, parent=None):
        """
        Initialize the dialog.

        Args:
            entry: Chest entry to edit
            parent: Parent widget
        """
        super().__init__(parent)

        # Store the entry
        self._entry = (
            entry.copy() if hasattr(entry, "copy") else entry
        )  # Create a copy to avoid modifying the original
        self._original_entry = entry  # Keep reference to original for comparison

        # Initialize field editors
        self._fields: Dict[str, QLineEdit] = {}

        # Set up the dialog
        self.setWindowTitle("Edit Entry")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)

        # Form layout for fields
        form = QFormLayout()

        # Add entry ID (read-only)
        id_label = QLabel(f"ID: {self._entry.id if hasattr(self._entry, 'id') else 'New Entry'}")
        form.addRow(id_label)

        # Add editable fields
        self._add_field(form, "chest_type", "Chest Type:")
        self._add_field(form, "player", "Player:")
        self._add_field(form, "source", "Source:")

        # Add form to main layout
        layout.addLayout(form)

        # Add buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def _add_field(self, form, field_name: str, label_text: str):
        """
        Add a field editor to the form.

        Args:
            form: Form layout to add the field to
            field_name: Name of the field
            label_text: Label text for the field
        """
        # Create editor
        editor = QLineEdit()

        # Set current value
        value = getattr(self._entry, field_name, "")
        editor.setText(str(value) if value is not None else "")

        # Store editor
        self._fields[field_name] = editor

        # Add to form
        form.addRow(label_text, editor)

    def accept(self):
        """Handle dialog acceptance with validation."""
        # Update entry with edited values
        try:
            for field_name, editor in self._fields.items():
                # Get the current value
                current_value = getattr(self._entry, field_name)

                # Get the new value
                new_value = editor.text().strip()

                # Check if the value has changed
                if current_value != new_value:
                    # If this is the first change, save original values
                    if not hasattr(self._entry, "original_values"):
                        self._entry.original_values = {}

                    if field_name not in self._entry.original_values:
                        self._entry.original_values[field_name] = current_value

                    # Update the field
                    setattr(self._entry, field_name, new_value)

            # Accept the dialog
            super().accept()

        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self, "Error", f"An error occurred while updating the entry: {str(e)}"
            )

    def get_entry(self) -> ChestEntry:
        """
        Get the edited entry.

        Returns:
            The edited chest entry
        """
        return self._entry
