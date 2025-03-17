"""
table_model.py

Description: Table model for displaying chest entries
Usage:
    from src.ui.table_model import ChestEntryTableModel
    model = ChestEntryTableModel(entries=entries)
    table_view.setModel(model)
"""

from typing import Dict, List, Optional, Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QSortFilterProxyModel
from PySide6.QtGui import QColor, QBrush

from src.models.chest_entry import ChestEntry
from src.ui.styles import COLORS


class ChestEntryTableModel(QAbstractTableModel):
    """
    Table model for displaying chest entries.

    Provides a model for a table view to display chest entries.

    Attributes:
        _entries (List[ChestEntry]): The chest entries to display
        _headers (List[str]): The column headers
        _columns (List[str]): The data columns to display
    """

    # Data columns
    COLUMNS = ["id", "chest_type", "player", "source", "validation"]
    HEADERS = ["ID", "Chest Type", "Player", "Source", "Validation"]

    # Custom roles
    HAS_ERROR_ROLE = Qt.UserRole + 1
    HAS_CORRECTION_ROLE = Qt.UserRole + 2
    ORIGINAL_VALUE_ROLE = Qt.UserRole + 3

    def __init__(self, entries: Optional[List[ChestEntry]] = None, parent=None) -> None:
        """
        Initialize the table model.

        Args:
            entries: List of chest entries to display
            parent: Parent object
        """
        super().__init__(parent)
        self._entries = entries or []
        self._headers = self.HEADERS
        self._columns = self.COLUMNS

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of rows.

        Args:
            parent: Parent index

        Returns:
            int: Number of rows
        """
        return len(self._entries)

    def columnCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of columns.

        Args:
            parent: Parent index

        Returns:
            int: Number of columns
        """
        return len(self._headers)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        """
        Get header data.

        Args:
            section (int): Section index
            orientation (Qt.Orientation): Header orientation
            role (int): Data role

        Returns:
            Any: Header data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        """
        Get data from the model.

        Args:
            index: Model index
            role: Data role

        Returns:
            The data for the given index and role
        """
        if not index.isValid() or not (0 <= index.row() < len(self._entries)):
            return None

        entry = self._entries[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            if column == 0:
                return entry.id
            elif column == 1:
                return entry.chest_type
            elif column == 2:
                return entry.player
            elif column == 3:
                return entry.source
            elif column == 4:
                return entry.validation

        elif role == Qt.ToolTipRole:
            field_name = self.get_field_name(column)
            if field_name in entry.original_values:
                original = entry.original_values[field_name]
                current = getattr(entry, field_name)
                return f"Original: {original}\nCorrected: {current}"
            elif field_name == "validation" and entry.has_validation_errors():
                return "\n".join(entry.validation_errors)
            return None

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter

        elif role == Qt.ForegroundRole:
            # If the field has been corrected, use a different color
            field_name = self.get_field_name(column)
            if field_name in entry.original_values:
                return QBrush(QColor(COLORS["accent"]))

            # If the entry has validation errors and this is the validation column
            if column == 4 and entry.has_validation_errors():
                return QBrush(QColor(COLORS["error"]))

            return None

        elif role == Qt.BackgroundRole:
            # If the entry has validation errors and this is the validation column
            if column == 4 and entry.has_validation_errors():
                return QBrush(QColor(COLORS["primary_dark"]))

            # If the field has been corrected, highlight the background
            field_name = self.get_field_name(column)
            if field_name in entry.original_values:
                return QBrush(QColor(COLORS["primary_light"]))

            return None

        elif role == self.HAS_ERROR_ROLE:
            return entry.has_validation_errors()
        elif role == self.HAS_CORRECTION_ROLE:
            return entry.has_corrections()
        elif role == self.ORIGINAL_VALUE_ROLE:
            return entry.get_original_field(self.get_field_name(column))

        return None

    def get_field_name(self, column: int) -> str:
        """
        Get the field name for a column.

        Args:
            column (int): Column index

        Returns:
            str: Field name
        """
        if column == 0:
            return "id"
        elif column == 1:
            return "chest_type"
        elif column == 2:
            return "player"
        elif column == 3:
            return "source"
        elif column == 4:
            return "validation"
        else:
            return ""

    def setEntries(self, entries: List[ChestEntry]) -> None:
        """
        Set the entries to display.

        Args:
            entries (List[ChestEntry]): The entries to display
        """
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()

    def getEntry(self, row: int) -> Optional[ChestEntry]:
        """
        Get the entry at a specific row.

        Args:
            row (int): Row index

        Returns:
            Optional[ChestEntry]: The entry or None if row is invalid
        """
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None


class ChestEntryFilterProxyModel(QSortFilterProxyModel):
    """
    Filter proxy model for chest entries.

    Allows filtering of chest entries by various criteria such as chest type,
    player, source, and validation status.

    Attributes:
        _chest_type_filter (str): Filter for chest type
        _player_filter (str): Filter for player
        _source_filter (str): Filter for source
        _status_filter (str): Filter for validation status
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize the filter proxy model.

        Args:
            parent: Parent object
        """
        super().__init__(parent)
        self._chest_type_filter = ""
        self._player_filter = ""
        self._source_filter = ""
        self._status_filter = ""  # Valid, Invalid, or Corrected

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Check if a row should be accepted by the filter.

        Args:
            source_row: Row index in the source model
            source_parent: Parent index in the source model

        Returns:
            Whether the row passes the filter
        """
        source_model = self.sourceModel()
        if not source_model:
            return False

        # Get the entry
        entry = source_model._entries[source_row]
        if not entry:
            return False

        # Check chest type filter
        if (
            self._chest_type_filter
            and self._chest_type_filter.lower() not in entry.chest_type.lower()
        ):
            return False

        # Check player filter
        if self._player_filter and self._player_filter.lower() not in entry.player.lower():
            return False

        # Check source filter
        if self._source_filter and self._source_filter.lower() not in entry.source.lower():
            return False

        # Check status filter
        if self._status_filter:
            if self._status_filter.lower() == "valid":
                if entry.has_validation_errors():
                    return False
            elif self._status_filter.lower() == "invalid":
                if not entry.has_validation_errors():
                    return False
            elif self._status_filter.lower() == "corrected":
                if not entry.has_corrections():
                    return False

        return True

    def set_filters(
        self, chest_type: str = "", player: str = "", source: str = "", status: str = ""
    ) -> None:
        """
        Set filter criteria.

        Args:
            chest_type: Filter for chest type
            player: Filter for player
            source: Filter for source
            status: Filter for validation status
        """
        self._chest_type_filter = chest_type
        self._player_filter = player
        self._source_filter = source
        self._status_filter = status
        self.invalidateFilter()
