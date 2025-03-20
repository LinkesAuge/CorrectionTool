"""
Enhanced table view with additional features like sorting, filtering, and context menu.

This module provides an extended QTableView with capabilities for advanced
data handling, filtering, and user interaction.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union, Callable
import logging
import time
import math

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QModelIndex,
    QAbstractTableModel,
    QSortFilterProxyModel,
    QTimer,
    QEvent,
    QObject,
    QItemSelectionModel,
)
from PySide6.QtGui import QColor, QBrush, QFont, QPalette, QStandardItemModel, QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QMenu,
    QStyledItemDelegate,
    QTableView,
    QWidget,
    QToolTip,
    QDialog,
    QStyleOptionViewItem,
    QMessageBox,
)

from src.models.chest_entry import ChestEntry


class ChestEntryTableModel(QAbstractTableModel):
    """
    Table model for chest entries.

    This model manages the data for chest entries, providing methods for
    accessing and manipulating the data.

    Attributes:
        _entries: List of chest entries
        _columns: List of column definitions
    """

    # Define column indices
    COLUMN_ID = 0
    COLUMN_CHEST_TYPE = 1
    COLUMN_PLAYER = 2
    COLUMN_SOURCE = 3

    # Define custom roles (should be beyond Qt.UserRole)
    VALIDATION_ERROR_ROLE = Qt.UserRole + 1
    ORIGINAL_VALUE_ROLE = Qt.UserRole + 2
    HAS_CORRECTION_ROLE = Qt.UserRole + 3

    def __init__(self, entries=None, parent=None):
        """
        Initialize the model.

        Args:
            entries: List of chest entries
            parent: Parent object
        """
        super().__init__(parent)
        self._entries = entries or []

        # Define columns
        self._columns = [
            {"name": "ID", "key": "id"},
            {"name": "Chest Type", "key": "chest_type"},
            {"name": "Player", "key": "player"},
            {"name": "Source", "key": "source"},
            {"name": "Status", "key": "status"},
        ]

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of rows in the model.

        Args:
            parent: Parent index

        Returns:
            Number of rows
        """
        if parent.isValid():
            return 0
        return len(self._entries)

    def columnCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of columns in the model.

        Args:
            parent: Parent index

        Returns:
            Number of columns
        """
        if parent.isValid():
            return 0
        return len(self._columns)

    def _get_value(self, entry, key, default=""):
        """
        Helper method to get a value from an entry, handling both objects and dictionaries.

        Args:
            entry: The entry object or dictionary
            key: The attribute or key to retrieve
            default: Default value if not found

        Returns:
            The value from the entry
        """
        # Check if entry is a dictionary
        if isinstance(entry, dict):
            return entry.get(key, default)
        # Otherwise treat as object with attributes
        return getattr(entry, key, default)

    def data(self, index, role=Qt.DisplayRole):
        """
        Return data for the given role at the given index.

        Args:
            index (QModelIndex): The index to get data for
            role (int): The role to get data for

        Returns:
            Any: The data for the given role at the given index
        """
        logger = logging.getLogger(__name__)
        if not index.isValid():
            return None

        try:
            if index.row() >= len(self._entries) or index.row() < 0:
                logger.warning(
                    f"Invalid row index: {index.row()}, max: {len(self._entries) - 1 if len(self._entries) > 0 else 0}"
                )
                return None

            entry = self._entries[index.row()]

            if role == Qt.DisplayRole:
                if index.column() == ChestEntryTableModel.COLUMN_ID:
                    # For ID column, try multiple ways to get the ID to ensure it's always displayed
                    entry_id = None

                    # Try to get ID from dictionary key
                    if isinstance(entry, dict):
                        entry_id = entry.get("id", None)
                    # Try to get ID from object attribute
                    else:
                        entry_id = getattr(entry, "id", None)

                    # If still None, try to get row number
                    if entry_id is None:
                        entry_id = index.row()

                    return str(entry_id) if entry_id is not None else str(index.row())
                elif index.column() == ChestEntryTableModel.COLUMN_CHEST_TYPE:
                    return self._get_value(entry, "chest_type")
                elif index.column() == ChestEntryTableModel.COLUMN_PLAYER:
                    return self._get_value(entry, "player")
                elif index.column() == ChestEntryTableModel.COLUMN_SOURCE:
                    return self._get_value(entry, "source")
                elif index.column() == 4:  # Status column
                    return self._get_value(entry, "status", "Pending")

            elif role == Qt.BackgroundRole:
                # Use background color for validation error indication
                has_error = self._get_value(entry, "has_validation_error", False)
                if has_error:
                    return QBrush(QColor(255, 200, 200))  # Light red for errors

            elif role == self.VALIDATION_ERROR_ROLE:
                return self._get_value(entry, "validation_error")

            elif role == self.ORIGINAL_VALUE_ROLE:
                if index.column() == ChestEntryTableModel.COLUMN_CHEST_TYPE:
                    original = self._get_value(entry, "original_chest_type")
                    return original if original else self._get_value(entry, "chest_type")
                elif index.column() == ChestEntryTableModel.COLUMN_PLAYER:
                    original = self._get_value(entry, "original_player")
                    return original if original else self._get_value(entry, "player")
                elif index.column() == ChestEntryTableModel.COLUMN_SOURCE:
                    original = self._get_value(entry, "original_source")
                    return original if original else self._get_value(entry, "source")

            elif role == self.HAS_CORRECTION_ROLE:
                if index.column() == ChestEntryTableModel.COLUMN_CHEST_TYPE:
                    return self._get_value(entry, "original_chest_type") is not None
                elif index.column() == ChestEntryTableModel.COLUMN_PLAYER:
                    return self._get_value(entry, "original_player") is not None
                elif index.column() == ChestEntryTableModel.COLUMN_SOURCE:
                    return self._get_value(entry, "original_source") is not None

            return None
        except Exception as e:
            logger.error(
                f"Error in data method for row {index.row()}, column {index.column()}, role {role}: {str(e)}"
            )
            import traceback

            logger.error(traceback.format_exc())
            return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
        """
        Get header data for the specified section and role.

        Args:
            section: Row or column number
            orientation: Header orientation
            role: Data role

        Returns:
            Header data
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._columns[section]["name"]

        return None

    def setData(self, index: QModelIndex, value: Any, role=Qt.EditRole) -> bool:
        """
        Set data for the specified index and role.

        Args:
            index: Model index
            value: New value
            role: Data role

        Returns:
            True if successful, False otherwise
        """
        if not index.isValid() or index.row() >= len(self._entries):
            return False

        if role == Qt.EditRole and index.column() in [1, 2, 3]:
            entry = self._entries[index.row()]
            field_name = ["chest_type", "player", "source"][index.column() - 1]

            if isinstance(entry, dict):
                # For dictionaries, store original value and update
                original_values = entry.get("original_values", {})
                if field_name not in original_values:
                    original_values[field_name] = entry.get(field_name, "")
                    entry["original_values"] = original_values
                # Update the value
                entry[field_name] = value
            else:
                # For objects, use attribute access
                # Store original value if not already set
                if not hasattr(entry, "original_values"):
                    entry.original_values = {}
                if field_name not in entry.original_values:
                    entry.original_values[field_name] = getattr(entry, field_name, "")
                # Update the value
                setattr(entry, field_name, value)

            # Emit data changed signal
            self.dataChanged.emit(index, index)
            return True

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Get the flags for the specified index.

        Args:
            index: Model index

        Returns:
            Item flags
        """
        flags = super().flags(index)

        # Make everything selectable
        flags |= Qt.ItemIsSelectable

        # Make ID and Status columns not editable
        if index.column() in [1, 2, 3]:
            flags |= Qt.ItemIsEditable

        return flags

    def set_entries(self, entries):
        """
        Set the entries to display.

        Args:
            entries: List of ChestEntry objects
        """
        # Log the operation for debugging
        logger = logging.getLogger(__name__)

        # Prevent redundant processing
        if hasattr(self, "_processing_signal") and self._processing_signal:
            logger.warning("Signal loop detected in set_entries, skipping")
            return

        # Throttle updates to avoid excessive refreshes
        current_time = time.time()
        if hasattr(self, "_last_update_time") and current_time - self._last_update_time < 0.5:
            logger.debug("Update throttled (too frequent), skipping")
            return

        # Check if entries are identical
        if hasattr(self, "_entries") and len(self._entries) == len(entries):
            # Quick check - if same number of entries, might be the same
            # Do a deeper check on a few entries
            sample_size = min(5, len(entries))
            if sample_size > 0:
                same_entries = True
                for i in range(sample_size):
                    if entries[i] != self._entries[i]:
                        same_entries = False
                        break

                if same_entries:
                    logger.debug("Entries appear unchanged, skipping redundant update")
                    return

        logger.debug(f"Setting {len(entries)} entries in table view")

        try:
            # Set flags to prevent recursive calls
            if not hasattr(self, "_processing_signal"):
                self._processing_signal = False
            if not hasattr(self, "_last_update_time"):
                self._last_update_time = 0

            self._processing_signal = True
            self._last_update_time = current_time

            # Make a defensive copy of entries to prevent modification of original
            self._entries = list(entries)

            # Create model for the entries
            model = ChestEntryTableModel(self._entries)

            # Update or create proxy model
            if self._proxy_model is None:
                self._proxy_model = QSortFilterProxyModel()
                self._proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
                self._proxy_model.setFilterKeyColumn(-1)  # Filter on all columns
                self.setModel(self._proxy_model)

            # Update the source model
            self._proxy_model.setSourceModel(model)

            # Ensure selection signals are connected
            if self.selectionModel():
                self.selectionModel().selectionChanged.connect(self._on_selection_changed)

            # Refresh the view
            self._refresh_view()

            # Log success
            logger.debug(f"Successfully set {len(entries)} entries in table view")

        except Exception as e:
            logger.error(f"Error setting entries in table view: {e}")
            import traceback

            logger.error(traceback.format_exc())
        finally:
            if hasattr(self, "_processing_signal"):
                self._processing_signal = False


class ValidationErrorDelegate(QStyledItemDelegate):
    """
    Delegate for displaying validation errors and corrections.

    This delegate provides custom rendering for cells with validation errors
    or corrections, including visual indicators and tooltips.
    """

    def __init__(self, parent=None):
        """
        Initialize the delegate.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        # Define custom roles as instance attributes
        self.VALIDATION_ERROR_ROLE = Qt.UserRole + 1
        self.ORIGINAL_VALUE_ROLE = Qt.UserRole + 2
        self.HAS_CORRECTION_ROLE = Qt.UserRole + 3

        # Set up logger
        self.logger = logging.getLogger(__name__)

    def paint(self, painter, option, index):
        """
        Paint the cell with custom styling for validation errors and corrections.

        Args:
            painter: Painter to use
            option: Style options
            index: Model index
        """
        try:
            # Create a copy of the style option to modify
            opt = QStyleOptionViewItem(option)

            # Get the model
            model = index.model()
            if not model:
                # Fall back to default painting if no model
                self.logger.warning("No model found in ValidationErrorDelegate.paint")
                super().paint(painter, option, index)
                return

            # Check for validation errors
            has_error = False
            try:
                # Try to get validation error role from model
                if hasattr(model, "VALIDATION_ERROR_ROLE"):
                    has_error = bool(model.data(index, model.VALIDATION_ERROR_ROLE))
                else:
                    # Fall back to our instance attribute
                    has_error = bool(model.data(index, self.VALIDATION_ERROR_ROLE))
            except Exception as e:
                # If there's an error, log it and continue
                self.logger.error(f"Error checking validation error role: {e}")
                self.logger.error(f"Row: {index.row()}, Column: {index.column()}")
                import traceback

                self.logger.error(f"Stack trace: {traceback.format_exc()}")

            # Check for corrections
            has_correction = False
            try:
                # Try to get correction role from model
                if hasattr(model, "HAS_CORRECTION_ROLE"):
                    has_correction = bool(model.data(index, model.HAS_CORRECTION_ROLE))
                else:
                    # Fall back to our instance attribute
                    has_correction = bool(model.data(index, self.HAS_CORRECTION_ROLE))
            except Exception as e:
                # If there's an error, log it and continue
                self.logger.error(f"Error checking correction role: {e}")
                self.logger.error(f"Row: {index.row()}, Column: {index.column()}")
                import traceback

                self.logger.error(f"Stack trace: {traceback.format_exc()}")

            # Apply custom styling based on validation status
            if has_error:
                # Red background for validation errors
                opt.backgroundBrush = QBrush(QColor(255, 200, 200))
            elif has_correction:
                # Green background for corrections
                opt.backgroundBrush = QBrush(QColor(200, 255, 200))

            # Use the parent class to draw the item with our modified style
            super().paint(painter, opt, index)

        except Exception as e:
            # If there's an error, log it and fall back to default painting
            self.logger.error(f"Error in ValidationErrorDelegate.paint: {e}")
            self.logger.error(f"Row: {index.row()}, Column: {index.column()}")
            import traceback

            self.logger.error(f"Stack trace: {traceback.format_exc()}")

            try:
                # Try basic painting with default style as a fallback
                super().paint(painter, option, index)
            except Exception as paint_error:
                self.logger.error(f"Error during fallback painting: {paint_error}")
                # If even the fallback fails, do nothing to avoid crashing

    def createEditor(self, parent, option, index):
        """
        Create an editor for the cell.

        Args:
            parent: Parent widget
            option: Style options
            index: Model index

        Returns:
            Editor widget
        """
        try:
            # Use default editor
            return super().createEditor(parent, option, index)
        except Exception as e:
            self.logger.error(f"Error in ValidationErrorDelegate.createEditor: {e}")
            self.logger.error(f"Row: {index.row()}, Column: {index.column()}")
            import traceback

            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            return None

    def setEditorData(self, editor, index):
        """
        Set the editor data.

        Args:
            editor: Editor widget
            index: Model index
        """
        try:
            # Use default implementation
            super().setEditorData(editor, index)
        except Exception as e:
            self.logger.error(f"Error in ValidationErrorDelegate.setEditorData: {e}")
            self.logger.error(f"Row: {index.row()}, Column: {index.column()}")
            import traceback

            self.logger.error(f"Stack trace: {traceback.format_exc()}")

    def setModelData(self, editor, model, index):
        """
        Set the model data from the editor.

        Args:
            editor: Editor widget
            model: Model
            index: Model index
        """
        try:
            # Use default implementation
            super().setModelData(editor, model, index)
        except Exception as e:
            self.logger.error(f"Error in ValidationErrorDelegate.setModelData: {e}")
            self.logger.error(f"Row: {index.row()}, Column: {index.column()}")
            import traceback

            self.logger.error(f"Stack trace: {traceback.format_exc()}")


class EnhancedTableView(QTableView):
    """
    Enhanced table view with custom delegates and advanced features.

    This table view provides advanced features like custom delegates
    for different column types, validation error display, and inline editing.

    Signals:
        entry_selected (ChestEntry): Signal emitted when an entry is selected
        entry_edited (ChestEntry): Signal emitted when an entry is edited

    Implementation Notes:
        - Uses custom delegates for different column types
        - Shows validation errors inline
        - Enables in-place editing
        - Provides filtering and sorting
        - Shows visual indicators for corrected entries
    """

    # Signals
    entry_selected = Signal(object)  # ChestEntry
    entry_edited = Signal(object)  # ChestEntry

    def __init__(self, parent=None):
        """
        Initialize the enhanced table view.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize properties
        self._entries: List[ChestEntry] = []
        self._proxy_model = None
        self._current_index = None

        # Set up the view
        self._setup_view()

    def _setup_view(self):
        """Set up the view configuration."""
        try:
            # Configure the view
            self.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.setSelectionMode(QAbstractItemView.SingleSelection)
            self.setAlternatingRowColors(True)
            self.setSortingEnabled(True)
            self.setContextMenuPolicy(Qt.CustomContextMenu)

            # Initialize with empty model
            model = ChestEntryTableModel([])
            self._proxy_model = QSortFilterProxyModel()
            self._proxy_model.setSourceModel(model)
            self._proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
            self._proxy_model.setFilterKeyColumn(-1)  # Filter on all columns
            self.setModel(self._proxy_model)

            # Configure headers
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.setColumnWidth(0, 50)  # ID column

            # Set up delegate
            self.setItemDelegate(ValidationErrorDelegate(self))

            # Connect context menu signal
            self.customContextMenuRequested.connect(self._show_context_menu)

            # Sort by ID initially
            self.sortByColumn(0, Qt.AscendingOrder)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in _setup_view: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def _on_selection_changed(self, selected, deselected):
        """
        Handle selection changed.

        Args:
            selected: Selected indexes
            deselected: Deselected indexes
        """
        # Get the selected entry
        entry = self.get_selected_entry()
        if entry:
            self.entry_selected.emit(entry)

    def _show_context_menu(self, position):
        """
        Show context menu at position.

        Args:
            position: Position to show menu
        """
        logger = logging.getLogger(__name__)

        try:
            # Get the entry at position
            index = self.indexAt(position)
            if not index.isValid():
                logger.debug("No valid index at position for context menu")
                return

            # Get the entry
            entry = self.get_entry_at_index(index)
            if not entry:
                logger.debug("No entry found at index for context menu")
                return

            logger.debug(
                f"Showing context menu for entry: {entry.chest_type}, {entry.player}, {entry.source}"
            )

            # Create context menu
            menu = QMenu(self)

            # Add edit action
            edit_action = menu.addAction("Edit Entry")
            edit_action.triggered.connect(lambda: self._edit_entry(entry))

            # Add create rule action
            create_rule_action = menu.addAction("Create Correction Rule")
            create_rule_action.triggered.connect(lambda: self._create_rule_from_entry(entry))

            # Add reset action if entry has corrections
            if hasattr(entry, "has_corrections") and entry.has_corrections():
                reset_action = menu.addAction("Reset to Original")
                reset_action.triggered.connect(lambda: self._reset_entry(entry))

            # Show menu
            menu.exec(self.viewport().mapToGlobal(position))
        except Exception as e:
            logger.error(f"Error showing context menu: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())

    def _edit_entry(self, entry):
        """
        Edit the entry.

        Args:
            entry: Entry to edit
        """
        try:
            logger = logging.getLogger(__name__)
            # Log differently based on entry type
            if isinstance(entry, dict):
                logger.debug(
                    f"Opening edit dialog for entry: {entry.get('chest_type', '')}, {entry.get('player', '')}, {entry.get('source', '')}"
                )
            else:
                logger.debug(
                    f"Opening edit dialog for entry: {entry.chest_type}, {entry.player}, {entry.source}"
                )

            # Create edit dialog
            try:
                from src.ui.entry_edit_dialog import EntryEditDialog

                dialog = EntryEditDialog(entry, self)

                # Show dialog
                if dialog.exec():
                    # Get edited entry
                    edited_entry = dialog.get_entry()

                    # Update the entries list
                    self._update_entry_in_list(edited_entry)

                    # Emit entry edited signal
                    self.entry_edited.emit(edited_entry)

                    # Refresh the view
                    self._refresh_view()

                    # Log differently based on entry type
                    if isinstance(edited_entry, dict):
                        logger.debug(
                            f"Entry edited successfully: {edited_entry.get('chest_type', '')}, {edited_entry.get('player', '')}, {edited_entry.get('source', '')}"
                        )
                    else:
                        logger.debug(
                            f"Entry edited successfully: {edited_entry.chest_type}, {edited_entry.player}, {edited_entry.source}"
                        )
            except ImportError as ie:
                logger.error(f"Could not import EntryEditDialog: {str(ie)}")
                QMessageBox.critical(
                    self,
                    "Feature Not Available",
                    "The edit feature is not available. Please contact the developer.",
                )
        except Exception as e:
            logger.error(f"Error in _edit_entry: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())

            # Show error message to user
            QMessageBox.critical(
                self, "Error", f"An error occurred while trying to edit the entry: {str(e)}"
            )

    def _update_entry_in_list(self, entry):
        """
        Update an entry in the entries list.

        Args:
            entry: The entry to update (dict or object)

        Returns:
            bool: True if the entry was found and updated, False otherwise
        """
        logger = logging.getLogger(__name__)

        # Get entry ID with type handling
        entry_id = None
        if isinstance(entry, dict):
            entry_id = entry.get("id")
            logger.debug(f"Updating dictionary entry with ID {entry_id}")
        else:
            entry_id = getattr(entry, "id", None)
            logger.debug(f"Updating object entry with ID {entry_id}")

        try:
            # First try to find the entry by ID if possible
            if entry_id is not None:
                try:
                    # Convert IDs to strings for comparison to handle type differences
                    entry_id_str = str(entry_id)
                    for i, existing_entry in enumerate(self._entries):
                        existing_id = None
                        if isinstance(existing_entry, dict):
                            existing_id = existing_entry.get("id")
                        else:
                            existing_id = getattr(existing_entry, "id", None)

                        if existing_id is not None and str(existing_id) == entry_id_str:
                            logger.debug(f"Found entry by ID at index {i}")
                            self._entries[i] = entry
                            return True
                except Exception as e:
                    logger.error(f"Error finding entry by ID: {str(e)}")
                    import traceback

                    logger.error(traceback.format_exc())

            # If we couldn't find by ID, try to find by content
            try:
                for i, existing_entry in enumerate(self._entries):
                    # Get values based on entry type
                    if isinstance(existing_entry, dict) and isinstance(entry, dict):
                        if (
                            existing_entry.get("chest_type") == entry.get("chest_type")
                            and existing_entry.get("player") == entry.get("player")
                            and existing_entry.get("source") == entry.get("source")
                        ):
                            logger.debug(f"Found dictionary entry by content at index {i}")
                            self._entries[i] = entry
                            return True
                    elif not isinstance(existing_entry, dict) and not isinstance(entry, dict):
                        if (
                            existing_entry.chest_type == entry.chest_type
                            and existing_entry.player == entry.player
                            and existing_entry.source == entry.source
                        ):
                            logger.debug(f"Found object entry by content at index {i}")
                            self._entries[i] = entry
                            return True
                    # Mixed types - try to compare using the _get_value helper
                    else:
                        e1_chest = self._get_value(existing_entry, "chest_type", "")
                        e1_player = self._get_value(existing_entry, "player", "")
                        e1_source = self._get_value(existing_entry, "source", "")

                        e2_chest = self._get_value(entry, "chest_type", "")
                        e2_player = self._get_value(entry, "player", "")
                        e2_source = self._get_value(entry, "source", "")

                        if (
                            e1_chest == e2_chest
                            and e1_player == e2_player
                            and e1_source == e2_source
                        ):
                            logger.debug(f"Found mixed-type entry by content at index {i}")
                            self._entries[i] = entry
                            return True
            except Exception as e:
                logger.error(f"Error finding entry by content: {str(e)}")
                import traceback

                logger.error(traceback.format_exc())

            logger.warning(f"Entry with ID {entry_id} not found for updating")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in _update_entry_in_list: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def _create_rule_from_entry(self, entry):
        """
        Create a correction rule from entry.

        Args:
            entry: Entry to create rule from (dict or object)
        """
        logger = logging.getLogger(__name__)
        try:
            # Log differently based on entry type
            if isinstance(entry, dict):
                logger.debug(
                    f"Creating correction rule from dictionary entry: {entry.get('chest_type', '')}, {entry.get('player', '')}, {entry.get('source', '')}"
                )
            else:
                logger.debug(
                    f"Creating correction rule from object entry: {entry.chest_type}, {entry.player}, {entry.source}"
                )

            # This is a stub - the actual implementation will come from signals
            # connected to this view from the correction manager panel
            self.entry_selected.emit(entry)

            logger.debug("Entry selected signal emitted for rule creation")
        except Exception as e:
            logger.error(f"Error in _create_rule_from_entry: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())

    def _reset_entry(self, entry):
        """
        Reset entry to original values.

        Args:
            entry: Entry to reset (dict or object)
        """
        logger = logging.getLogger(__name__)
        try:
            # Log differently based on entry type
            if isinstance(entry, dict):
                logger.debug(
                    f"Resetting dictionary entry to original values: {entry.get('chest_type', '')}, {entry.get('player', '')}, {entry.get('source', '')}"
                )

                # Reset dictionary entry
                if "original_values" in entry:
                    for field, original in entry["original_values"].items():
                        entry[field] = original
                    entry["original_values"] = {}
                else:
                    logger.warning(f"Dictionary entry does not have original_values: {entry}")
                    return
            else:
                logger.debug(
                    f"Resetting object entry to original values: {entry.chest_type}, {entry.player}, {entry.source}"
                )

                # Reset object entry
                if hasattr(entry, "reset_corrections"):
                    entry.reset_corrections()
                elif hasattr(entry, "original_values"):
                    for field, original in entry.original_values.items():
                        setattr(entry, field, original)
                    entry.original_values = {}
                else:
                    logger.warning(
                        f"Object entry does not have reset_corrections method or original_values: {entry}"
                    )
                    return

            # Update the entries list
            self._update_entry_in_list(entry)

            # Emit entry edited signal
            self.entry_edited.emit(entry)

            # Refresh the view
            self._refresh_view()

            logger.debug("Entry reset successfully")
        except Exception as e:
            logger.error(f"Error in _reset_entry: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())

            # Show error message to user
            QMessageBox.critical(
                self, "Error", f"An error occurred while trying to reset the entry: {str(e)}"
            )

    def set_entries(self, entries):
        """
        Set the entries to display in the table.

        Args:
            entries: List of ChestEntry objects
        """
        # Log the operation for debugging
        logger = logging.getLogger(__name__)

        # Prevent redundant processing
        if hasattr(self, "_processing_signal") and self._processing_signal:
            logger.warning("Signal loop detected in EnhancedTableView.set_entries, skipping")
            return

        # Throttle updates to avoid excessive refreshes
        current_time = time.time()
        if hasattr(self, "_last_update_time") and current_time - self._last_update_time < 0.5:
            logger.debug("Update throttled (too frequent), skipping")
            return

        logger.debug(f"Setting {len(entries)} entries in EnhancedTableView")

        try:
            # Set flags to prevent recursive calls
            if not hasattr(self, "_processing_signal"):
                self._processing_signal = False
            if not hasattr(self, "_last_update_time"):
                self._last_update_time = 0

            self._processing_signal = True
            self._last_update_time = current_time

            # Store entries for direct access
            self._entries = list(entries)

            # Create a new model with the entries
            model = ChestEntryTableModel(self._entries)

            # Update or create proxy model
            if not hasattr(self, "_proxy_model") or self._proxy_model is None:
                self._proxy_model = QSortFilterProxyModel()
                self._proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
                self._proxy_model.setFilterKeyColumn(-1)  # Filter on all columns
                self.setModel(self._proxy_model)

            # Set the source model for the proxy
            self._proxy_model.setSourceModel(model)

            # Ensure selection signals are connected
            if self.selectionModel():
                self.selectionModel().selectionChanged.connect(self._on_selection_changed)

            # Refresh the view
            self._refresh_view()

            logger.debug(f"Successfully set {len(entries)} entries in EnhancedTableView")

        except Exception as e:
            logger.error(f"Error setting entries in EnhancedTableView: {e}")
            import traceback

            logger.error(traceback.format_exc())
        finally:
            if hasattr(self, "_processing_signal"):
                self._processing_signal = False

    def filter_entries(self, text):
        """
        Filter entries by text.

        Args:
            text: Text to filter by
        """
        if self._proxy_model:
            self._proxy_model.setFilterFixedString(text)

    def get_selected_row(self):
        """
        Get the row index of the selected entry.

        Returns:
            int: Row index or -1 if nothing selected
        """
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            return -1

        # Get the source row (accounting for proxy model)
        proxy_index = indexes[0]
        source_index = self._proxy_model.mapToSource(proxy_index)
        return source_index.row()

    def get_selected_entry(self):
        """
        Get the currently selected entry.

        Returns:
            The selected entry (dict or object) or None if no entry is selected
        """
        # Get selected indexes
        indexes = self.selectionModel().selectedRows()
        if not indexes:
            return None

        # Get the entry at the selected row
        return self.get_entry_at_index(indexes[0])

    def get_entry_at_index(self, index):
        """
        Get the entry at the given index.

        Args:
            index: Model index

        Returns:
            Entry at index (dict or object) or None if index is invalid
        """
        logger = logging.getLogger(__name__)
        try:
            if not index.isValid():
                logger.debug("Invalid index provided to get_entry_at_index")
                return None

            # Map to source index if using proxy model
            if self._proxy_model is None:
                logger.warning("Proxy model is None in get_entry_at_index")
                return None

            source_index = self._proxy_model.mapToSource(index)
            if not source_index.isValid():
                logger.warning("Invalid source index after mapping")
                return None

            source_row = source_index.row()

            # Get the entry
            if not self._entries:
                logger.warning("Entries list is empty in get_entry_at_index")
                return None

            if 0 <= source_row < len(self._entries):
                entry = self._entries[source_row]
                # Log differently based on entry type
                if isinstance(entry, dict):
                    logger.debug(
                        f"Found dictionary entry at index {source_row}: {entry.get('chest_type', 'Unknown')}"
                    )
                else:
                    logger.debug(
                        f"Found object entry at index {source_row}: {getattr(entry, 'chest_type', 'Unknown')}"
                    )
                return entry
            else:
                logger.warning(
                    f"Row index out of range: {source_row}, max: {len(self._entries) - 1 if self._entries else -1}"
                )
                return None
        except Exception as e:
            logger.error(f"Error in get_entry_at_index: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return None

    def _refresh_view(self):
        """Refresh the table view to reflect model changes."""
        # Configure headers
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setColumnWidth(0, 50)  # ID column

        # Reset sorting
        self.sortByColumn(0, Qt.AscendingOrder)

        # Resize columns and rows to content
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

        # Force a visual update
        self.viewport().update()

    def highlight_validation_errors(self):
        """
        Highlight rows with validation errors.

        This method refreshes the view and ensures the validation error
        highlighting is applied by the item delegate.
        """
        logger = logging.getLogger(__name__)
        try:
            # Force refresh to apply highlighting
            if hasattr(self, "_proxy_model") and self._proxy_model:
                self._proxy_model.invalidate()

            # Ensure custom delegates are applied
            if not self.itemDelegate() or not isinstance(
                self.itemDelegate(), ValidationHighlightDelegate
            ):
                # Create a validation highlight delegate if not already set
                self.setItemDelegate(ValidationHighlightDelegate(self))

            # Update the view
            self.viewport().update()
            logger.debug("Applied validation error highlighting")
        except Exception as e:
            logger.error(f"Error highlighting validation errors: {e}")
            import traceback

            logger.error(traceback.format_exc())


class ValidationHighlightDelegate(QStyledItemDelegate):
    """
    Delegate for highlighting validation errors in the table.

    This delegate applies visual styling to rows that have validation errors.
    """

    def __init__(self, parent=None):
        """Initialize the delegate."""
        super().__init__(parent)

    def paint(self, painter, option, index):
        """
        Paint the cell with appropriate styling based on validation status.

        Args:
            painter: QPainter instance
            option: Style options
            index: Model index
        """
        # Get the source model index if using a proxy model
        source_index = index
        if isinstance(index.model(), QSortFilterProxyModel):
            source_index = index.model().mapToSource(index)

        # Get the source model
        source_model = source_index.model()

        # Check if the row has validation errors
        row = source_index.row()
        has_error = False

        try:
            # Get the entry from the model
            if hasattr(source_model, "_entries") and row < len(source_model._entries):
                entry = source_model._entries[row]

                # Check for validation_errors field
                if isinstance(entry, dict) and "validation_errors" in entry:
                    has_error = entry["validation_errors"] and len(entry["validation_errors"]) > 0
                elif hasattr(entry, "validation_errors"):
                    has_error = entry.validation_errors and len(entry.validation_errors) > 0

            # Apply highlighting if has errors
            if has_error:
                # Save original state
                original_bg = option.palette.brush(QPalette.Base)

                # Set error background
                error_option = QStyleOptionViewItem(option)
                error_option.backgroundBrush = QBrush(QColor(255, 220, 220))  # Light red

                # Paint with modified option
                super().paint(painter, error_option, index)
            else:
                # Paint normally
                super().paint(painter, option, index)
        except Exception:
            # Fall back to normal painting if any error
            super().paint(painter, option, index)
