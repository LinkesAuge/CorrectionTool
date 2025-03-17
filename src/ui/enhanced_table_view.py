"""
enhanced_table_view.py

Description: Enhanced table view with advanced features and custom delegates
Usage:
    from src.ui.enhanced_table_view import EnhancedTableView
    table_view = EnhancedTableView(parent=self)
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union
import logging

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QModelIndex,
    QAbstractTableModel,
    QSortFilterProxyModel,
    QTimer,
)
from PySide6.QtGui import QColor, QBrush, QFont, QPalette
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
                    return str(entry.id) if entry.id is not None else ""
                elif index.column() == ChestEntryTableModel.COLUMN_CHEST_TYPE:
                    return entry.chest_type if entry.chest_type else ""
                elif index.column() == ChestEntryTableModel.COLUMN_PLAYER:
                    return entry.player if entry.player else ""
                elif index.column() == ChestEntryTableModel.COLUMN_SOURCE:
                    return entry.source if entry.source else ""

            elif role == Qt.BackgroundRole:
                # Use background color for validation error indication
                has_error = getattr(entry, "has_validation_error", False)
                if has_error:
                    return QBrush(QColor(255, 200, 200))  # Light red for errors

            elif role == self.VALIDATION_ERROR_ROLE:
                return getattr(entry, "validation_error", None)

            elif role == self.ORIGINAL_VALUE_ROLE:
                if index.column() == ChestEntryTableModel.COLUMN_CHEST_TYPE:
                    return getattr(entry, "original_chest_type", entry.chest_type)
                elif index.column() == ChestEntryTableModel.COLUMN_PLAYER:
                    return getattr(entry, "original_player", entry.player)
                elif index.column() == ChestEntryTableModel.COLUMN_SOURCE:
                    return getattr(entry, "original_source", entry.source)

            elif role == self.HAS_CORRECTION_ROLE:
                if index.column() == ChestEntryTableModel.COLUMN_CHEST_TYPE:
                    return hasattr(entry, "original_chest_type")
                elif index.column() == ChestEntryTableModel.COLUMN_PLAYER:
                    return hasattr(entry, "original_player")
                elif index.column() == ChestEntryTableModel.COLUMN_SOURCE:
                    return hasattr(entry, "original_source")

            return None
        except Exception as e:
            logger.error(
                f"Error in data method for row {index.row()}, column {index.column()}, role {role}: {str(e)}"
            )
            import traceback

            logger.error(traceback.format_exc())

            # Log additional information about the entry if possible
            try:
                if index.row() < len(self._entries):
                    entry = self._entries[index.row()]
                    logger.error(
                        f"Entry details: ID={entry.id}, Type={entry.chest_type}, Player={entry.player}, Source={entry.source}"
                    )
            except Exception as inner_e:
                logger.error(f"Could not log entry details: {str(inner_e)}")

            # Return some default values based on the role to avoid crashes
            if role == Qt.DisplayRole:
                return "Error"
            elif role == Qt.BackgroundRole:
                return QBrush(QColor(255, 200, 200))  # Light red for errors
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

            # Store original value if not already set
            if field_name not in entry.original_values:
                entry.original_values[field_name] = getattr(entry, field_name)

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
        """Set the entries for this model.

        Args:
            entries (list): List of ChestEntry objects
        """
        logger = logging.getLogger(__name__)
        try:
            logger.debug(f"Setting {len(entries)} entries in table model")
            self.beginResetModel()
            try:
                self._entries = entries
            except Exception as e:
                logger.error(f"Error setting entries: {str(e)}")
                import traceback

                logger.error(traceback.format_exc())
                self._entries = []
            self.endResetModel()
            logger.debug("Successfully set entries in table model")
        except Exception as e:
            logger.error(f"Unexpected error in set_entries: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())


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

            # Connect context menu signal
            self.customContextMenuRequested.connect(self._show_context_menu)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in _setup_view: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def set_entries(self, entries):
        """
        Set the entries to display.

        Args:
            entries: List of ChestEntry objects
        """
        # Log the operation for debugging
        logger = logging.getLogger(__name__)
        logger.debug(f"Setting {len(entries)} entries in table view")

        try:
            # Make a defensive copy of entries to prevent modification of original
            self._entries = list(entries)

            # Create model for the entries - use a try/except to handle model creation
            try:
                model = ChestEntryTableModel(self._entries)
            except Exception as model_error:
                logger.error(f"Error creating table model: {model_error}")
                import traceback

                logger.error(traceback.format_exc())
                # Create a model with empty entries as fallback
                model = ChestEntryTableModel([])

            # Create proxy model for sorting and filtering
            try:
                self._proxy_model = QSortFilterProxyModel()
                self._proxy_model.setSourceModel(model)
                self._proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
                self._proxy_model.setFilterKeyColumn(-1)  # Filter on all columns
            except Exception as proxy_error:
                logger.error(f"Error creating proxy model: {proxy_error}")
                import traceback

                logger.error(traceback.format_exc())
                # Try to recover by using direct model
                self._proxy_model = None
                self.setModel(model)
                return

            # Set the model on the view
            try:
                self.setModel(self._proxy_model)
            except Exception as set_model_error:
                logger.error(f"Error setting model: {set_model_error}")
                import traceback

                logger.error(traceback.format_exc())
                return

            # Connect selection signals (must be done after setting model)
            try:
                self.selectionModel().selectionChanged.connect(self._on_selection_changed)
            except Exception as selection_error:
                logger.error(f"Error connecting selection changed signal: {selection_error}")
                import traceback

                logger.error(traceback.format_exc())

            # Configure the view
            try:
                self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                self.setColumnWidth(0, 50)  # ID column
            except Exception as header_error:
                logger.error(f"Error configuring headers: {header_error}")
                import traceback

                logger.error(traceback.format_exc())

            # Create delegates for validation errors and corrections
            try:
                self.setItemDelegate(ValidationErrorDelegate(self))
            except Exception as delegate_error:
                logger.error(f"Error setting delegate: {delegate_error}")
                import traceback

                logger.error(traceback.format_exc())

            # Sort by ID
            try:
                self.sortByColumn(0, Qt.AscendingOrder)
            except Exception as sort_error:
                logger.error(f"Error setting initial sort: {sort_error}")
                import traceback

                logger.error(traceback.format_exc())

            logger.debug("Successfully set up table view with entries")
        except Exception as e:
            logger.error(f"Error in set_entries: {e}")
            import traceback

            logger.error(f"Stack trace: {traceback.format_exc()}")
            # Still set the entries to avoid completely breaking functionality
            self._entries = entries

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
            entry (ChestEntry): The entry to update

        Returns:
            bool: True if the entry was found and updated, False otherwise
        """
        logger = logging.getLogger(__name__)
        logger.debug(f"Updating entry with ID {entry.id if hasattr(entry, 'id') else 'None'}")

        try:
            # First try to find the entry by ID if possible
            if hasattr(entry, "id") and entry.id is not None:
                try:
                    # Convert IDs to strings for comparison to handle type differences
                    entry_id_str = str(entry.id)
                    for i, existing_entry in enumerate(self._entries):
                        if hasattr(existing_entry, "id") and existing_entry.id is not None:
                            if str(existing_entry.id) == entry_id_str:
                                logger.debug(f"Found entry by ID at index {i}")
                                self._entries[i] = entry
                                return True
                except Exception as e:
                    logger.error(f"Error finding entry by ID: {str(e)}")
                    import traceback

                    logger.error(traceback.format_exc())

            # If we couldn't find by ID, try to find by index or content
            try:
                for i, existing_entry in enumerate(self._entries):
                    if (
                        existing_entry.chest_type == entry.chest_type
                        and existing_entry.player == entry.player
                        and existing_entry.source == entry.source
                    ):
                        logger.debug(f"Found entry by content at index {i}")
                        self._entries[i] = entry
                        return True
            except Exception as e:
                logger.error(f"Error finding entry by content: {str(e)}")
                import traceback

                logger.error(traceback.format_exc())

            logger.warning(
                f"Entry with ID {entry.id if hasattr(entry, 'id') else 'None'} not found for updating"
            )
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
            entry: Entry to create rule from
        """
        logger = logging.getLogger(__name__)
        try:
            logger.debug(
                f"Creating correction rule from entry: {entry.chest_type}, {entry.player}, {entry.source}"
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
            entry: Entry to reset
        """
        logger = logging.getLogger(__name__)
        try:
            logger.debug(
                f"Resetting entry to original values: {entry.chest_type}, {entry.player}, {entry.source}"
            )

            # Reset the entry
            if hasattr(entry, "reset_corrections"):
                entry.reset_corrections()
            else:
                logger.warning(f"Entry does not have reset_corrections method: {entry}")
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
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self, "Error", f"An error occurred while trying to reset the entry: {str(e)}"
            )

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
            ChestEntry: Selected entry or None if no entry is selected
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
            ChestEntry: Entry at index or None if index is invalid
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
                logger.debug(
                    f"Found entry at index {source_row}: {entry.chest_type if hasattr(entry, 'chest_type') else 'Unknown'}"
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
        """Refresh the view to reflect changes in the model."""
        # This is a simple way to refresh the view - a more sophisticated
        # approach would be to emit dataChanged signals from the model
        if self._proxy_model and self._proxy_model.sourceModel():
            self._proxy_model.sourceModel().layoutChanged.emit()
