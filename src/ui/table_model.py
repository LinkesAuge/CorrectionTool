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
from src.ui.styles import ThemeColors


class ChestEntryTableModel(QAbstractTableModel):
    """
    Table model for displaying chest entries.
    
    Provides a model for a table view to display chest entries.
    
    Attributes:
        _entries (List[ChestEntry]): The chest entries to display
        _headers (List[str]): The column headers
        _columns (List[str]): The data columns to display
        _theme_colors (ThemeColors): Theme colors for styling
        
    Implementation Notes:
        - Handles display of chest entry data in a table
        - Supports highlighting for corrected entries and validation errors
        - Provides custom tooltips with correction details
    """
    
    def __init__(
        self, 
        entries: Optional[List[ChestEntry]] = None, 
        parent=None
    ) -> None:
        """
        Initialize the table model.
        
        Args:
            entries (Optional[List[ChestEntry]]): The chest entries to display
            parent: Parent object
        """
        super().__init__(parent)
        self._entries = entries or []
        self._headers = ["Chest Type", "Player", "Source", "Status"]
        self._columns = ["chest_type", "player", "source", "status"]
        self._theme_colors = ThemeColors()
    
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
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
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
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """
        Get data for display in the table.
        
        Args:
            index (QModelIndex): Item index
            role (int): Data role
            
        Returns:
            Any: Item data
        """
        if not index.isValid() or index.row() >= len(self._entries):
            return None
        
        entry = self._entries[index.row()]
        col = index.column()
        
        # Handle display role - showing the data
        if role == Qt.DisplayRole:
            if col < 3:  # Chest Type, Player, Source
                return entry.get_field(self._columns[col])
            elif col == 3:  # Status
                if entry.has_validation_errors():
                    return "Error"
                elif entry.has_corrections():
                    return "Corrected"
                else:
                    return "Valid"
        
        # Handle tooltip role - showing additional information
        elif role == Qt.ToolTipRole:
            if col < 3 and entry.has_corrections():
                # Find corrections for this field
                field = self._columns[col]
                field_corrections = [c for c in entry.corrections if c[0] == field]
                
                if field_corrections:
                    original = getattr(entry, f"original_{field}")
                    current = entry.get_field(field)
                    return f"Original: {original}\nCorrected: {current}"
            
            elif col == 3:  # Status column tooltip
                if entry.has_validation_errors():
                    return "\n".join(entry.validation_errors)
                elif entry.has_corrections():
                    corrections = []
                    for field, from_val, to_val in entry.corrections:
                        corrections.append(f"{field.capitalize()}: {from_val} → {to_val}")
                    return "Corrections:\n" + "\n".join(corrections)
        
        # Handle background role - cell background color
        elif role == Qt.BackgroundRole:
            # Highlight cells with corrections
            if col < 3:  # Chest Type, Player, Source
                field = self._columns[col]
                field_corrections = [c for c in entry.corrections if c[0] == field]
                
                if field_corrections:
                    # Light highlight for corrected fields
                    return QBrush(QColor(self._theme_colors.primary).lighter(300))
            
            # Highlight status cell based on status
            elif col == 3:  # Status
                if entry.has_validation_errors():
                    return QBrush(QColor(self._theme_colors.error).lighter(250))
                elif entry.has_corrections():
                    return QBrush(QColor(self._theme_colors.success).lighter(250))
        
        # Handle foreground role - text color
        elif role == Qt.ForegroundRole:
            if col == 3:  # Status column
                if entry.has_validation_errors():
                    return QBrush(QColor(self._theme_colors.error))
                elif entry.has_corrections():
                    return QBrush(QColor(self._theme_colors.success))
        
        return None
    
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
    Filter proxy model for chest entry table.
    
    Provides filtering capability for the chest entry table.
    
    Attributes:
        _chest_type_filter (str): Filter for chest type
        _player_filter (str): Filter for player
        _source_filter (str): Filter for source
        _status_filter (str): Filter for status
        
    Implementation Notes:
        - Provides filtering for each column
        - Case-insensitive filtering
        - Supports multiple filter criteria
    """
    
    def __init__(self, parent=None) -> None:
        """
        Initialize the filter model.
        
        Args:
            parent: Parent object
        """
        super().__init__(parent)
        self._chest_type_filter = ""
        self._player_filter = ""
        self._source_filter = ""
        self._status_filter = ""
    
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Check if a row should be accepted by the filter.
        
        Args:
            source_row (int): Row in the source model
            source_parent (QModelIndex): Parent index
            
        Returns:
            bool: True if row should be shown, False otherwise
        """
        source_model = self.sourceModel()
        entry = source_model.getEntry(source_row)
        
        if not entry:
            return False
        
        # Check chest type filter
        if self._chest_type_filter and self._chest_type_filter.lower() not in entry.chest_type.lower():
            return False
        
        # Check player filter
        if self._player_filter and self._player_filter.lower() not in entry.player.lower():
            return False
        
        # Check source filter
        if self._source_filter and self._source_filter.lower() not in entry.source.lower():
            return False
        
        # Check status filter
        if self._status_filter:
            status = ""
            if entry.has_validation_errors():
                status = "error"
            elif entry.has_corrections():
                status = "corrected"
            else:
                status = "valid"
                
            if self._status_filter.lower() not in status:
                return False
        
        return True
    
    def set_filters(
        self,
        chest_type: str = "",
        player: str = "",
        source: str = "",
        status: str = ""
    ) -> None:
        """
        Set the filter criteria.
        
        Args:
            chest_type (str, optional): Filter for chest type
            player (str, optional): Filter for player
            source (str, optional): Filter for source
            status (str, optional): Filter for status
        """
        self._chest_type_filter = chest_type
        self._player_filter = player
        self._source_filter = source
        self._status_filter = status
        self.invalidateFilter() 