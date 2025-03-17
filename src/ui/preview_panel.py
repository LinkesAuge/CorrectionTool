"""
preview_panel.py

Description: Panel for previewing original and corrected entries side by side
Usage:
    from src.ui.preview_panel import PreviewPanel
    preview_panel = PreviewPanel(parent=self)
"""

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QColor, QTextCursor
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QSplitter, QTextEdit, 
    QVBoxLayout, QWidget, QPushButton
)

from src.models.chest_entry import ChestEntry
from src.services.config_manager import ConfigManager
from src.ui.styles import ThemeColors


class PreviewPanel(QWidget):
    """
    Panel for previewing original and corrected entries side by side.
    
    Provides a side-by-side view of original and corrected entries for comparison.
    
    Attributes:
        _current_entry (Optional[ChestEntry]): The currently displayed entry
        _theme_colors (ThemeColors): Theme colors for styling
        
    Implementation Notes:
        - Shows original text on the left, corrected on the right
        - Highlights changes between original and corrected text
        - Provides navigation between entries
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the preview panel.
        
        Args:
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        
        # Initialize data
        self._config = ConfigManager()
        self._current_entry: Optional[ChestEntry] = None
        self._entries: List[ChestEntry] = []
        self._current_index: int = -1
        self._theme_colors = ThemeColors()
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Main splitter (original vs corrected)
        self._splitter = QSplitter(Qt.Horizontal)
        
        # Original text group
        original_group = QGroupBox("Original Text")
        original_layout = QVBoxLayout(original_group)
        
        self._original_text = QTextEdit()
        self._original_text.setReadOnly(True)
        
        original_layout.addWidget(self._original_text)
        
        # Corrected text group
        corrected_group = QGroupBox("Corrected Text")
        corrected_layout = QVBoxLayout(corrected_group)
        
        self._corrected_text = QTextEdit()
        self._corrected_text.setReadOnly(True)
        
        corrected_layout.addWidget(self._corrected_text)
        
        # Add groups to splitter
        self._splitter.addWidget(original_group)
        self._splitter.addWidget(corrected_group)
        
        # Set initial splitter sizes
        self._splitter.setSizes([self.width() // 2, self.width() // 2])
        
        # Add splitter to main layout
        main_layout.addWidget(self._splitter)
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        
        self._prev_button = QPushButton("Previous")
        self._prev_button.setEnabled(False)
        self._prev_button.clicked.connect(self._show_previous)
        
        self._entry_label = QLabel("No entries loaded")
        self._entry_label.setAlignment(Qt.AlignCenter)
        
        self._next_button = QPushButton("Next")
        self._next_button.setEnabled(False)
        self._next_button.clicked.connect(self._show_next)
        
        nav_layout.addWidget(self._prev_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self._entry_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self._next_button)
        
        # Add navigation controls to main layout
        main_layout.addLayout(nav_layout)
        
        # Change details group
        changes_group = QGroupBox("Change Details")
        changes_layout = QVBoxLayout(changes_group)
        
        self._changes_text = QTextEdit()
        self._changes_text.setReadOnly(True)
        
        changes_layout.addWidget(self._changes_text)
        
        # Add changes group to main layout
        main_layout.addWidget(changes_group)
    
    @Slot(list)
    def set_entries(self, entries: List[ChestEntry]) -> None:
        """
        Set the entries to preview.
        
        Args:
            entries (List[ChestEntry]): The entries to preview
        """
        self._entries = entries
        self._current_index = -1
        
        # Enable navigation if there are entries with corrections
        has_corrected = any(entry.has_corrections() for entry in entries)
        
        self._prev_button.setEnabled(False)
        self._next_button.setEnabled(has_corrected and len(entries) > 0)
        
        if not has_corrected:
            self._entry_label.setText("No corrected entries")
            self._clear_preview()
        else:
            self._entry_label.setText("Navigate to view corrected entries")
            
            # Find first corrected entry
            for i, entry in enumerate(entries):
                if entry.has_corrections():
                    self._current_index = i
                    self._show_current_entry()
                    break
    
    def _show_previous(self) -> None:
        """Show the previous corrected entry."""
        if not self._entries:
            return
        
        # Find previous corrected entry
        index = self._current_index - 1
        while index >= 0:
            if self._entries[index].has_corrections():
                self._current_index = index
                self._show_current_entry()
                return
            index -= 1
        
        # If we get here, no previous corrected entry
        self._prev_button.setEnabled(False)
    
    def _show_next(self) -> None:
        """Show the next corrected entry."""
        if not self._entries:
            return
        
        # Find next corrected entry
        index = self._current_index + 1
        while index < len(self._entries):
            if self._entries[index].has_corrections():
                self._current_index = index
                self._show_current_entry()
                return
            index += 1
        
        # If we get here, no next corrected entry
        self._next_button.setEnabled(False)
    
    def _show_current_entry(self) -> None:
        """Show the current entry in the preview."""
        if not self._entries or self._current_index < 0 or self._current_index >= len(self._entries):
            self._clear_preview()
            return
        
        entry = self._entries[self._current_index]
        self._current_entry = entry
        
        # Update navigation buttons
        has_prev = False
        for i in range(self._current_index - 1, -1, -1):
            if self._entries[i].has_corrections():
                has_prev = True
                break
        
        has_next = False
        for i in range(self._current_index + 1, len(self._entries)):
            if self._entries[i].has_corrections():
                has_next = True
                break
        
        self._prev_button.setEnabled(has_prev)
        self._next_button.setEnabled(has_next)
        
        # Update entry label
        self._entry_label.setText(f"Entry {self._current_index + 1} of {len(self._entries)}")
        
        # Show original text
        self._show_original_text(entry)
        
        # Show corrected text
        self._show_corrected_text(entry)
        
        # Show changes
        self._show_changes(entry)
    
    def _show_original_text(self, entry: ChestEntry) -> None:
        """
        Show the original text of an entry.
        
        Args:
            entry (ChestEntry): The entry to show
        """
        self._original_text.clear()
        
        # Format original text
        original_chest_type = entry.original_chest_type or entry.chest_type
        original_player = entry.original_player or entry.player
        original_source = entry.original_source or entry.source
        
        # Format player with "From: " prefix if it doesn't have it
        player_line = original_player
        if not player_line.lower().startswith("from:"):
            player_line = f"From: {player_line}"
        
        # Format source with "Source: " prefix if it doesn't have it
        source_line = original_source
        if not source_line.lower().startswith("source:"):
            source_line = f"Source: {source_line}"
        
        original_text = f"{original_chest_type}\n{player_line}\n{source_line}"
        
        self._original_text.setPlainText(original_text)
    
    def _show_corrected_text(self, entry: ChestEntry) -> None:
        """
        Show the corrected text for an entry.
        
        Args:
            entry (ChestEntry): The entry to show
        """
        # Get the corrected text
        corrected_text = entry.to_text()
        
        # Set the text
        self._corrected_text.setPlainText(corrected_text)
        
        # Highlight corrections
        print(f"Showing corrected text for entry: {entry.chest_type}")
        print(f"Corrections: {entry.corrections}")
        
        cursor = self._corrected_text.textCursor()
        format_changed = self._corrected_text.currentCharFormat()
        format_changed.setBackground(QColor(self._theme_colors.primary).lighter(300))
        format_changed.setForeground(QColor(self._theme_colors.primary))
        
        # Check for field corrections and highlight
        for field, from_val, to_val in entry.corrections:
            print(f"Highlighting correction: {field} from '{from_val}' to '{to_val}'")
            if field == "chest_type":
                # Chest type is the first line
                cursor.setPosition(0)
                cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                cursor.setCharFormat(format_changed)
            elif field == "player":
                # Player is in the second line
                player_start = corrected_text.find("From:")
                if player_start >= 0:
                    print(f"Player start position: {player_start}")
                    cursor.setPosition(player_start + 5)  # Move past "From:"
                    cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                    cursor.setCharFormat(format_changed)
            elif field == "source":
                # Source is in the third line
                source_start = corrected_text.rfind("Source:")
                if source_start >= 0:
                    print(f"Source start position: {source_start}")
                    cursor.setPosition(source_start + 7)  # Move past "Source:"
                    cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                    cursor.setCharFormat(format_changed)
    
    def _show_changes(self, entry: ChestEntry) -> None:
        """
        Show the changes made to an entry.
        
        Args:
            entry (ChestEntry): The entry to show
        """
        self._changes_text.clear()
        
        if not entry.has_corrections():
            self._changes_text.setPlainText("No changes made to this entry.")
            return
        
        changes_text = "Changes made to this entry:\n\n"
        
        for field, from_val, to_val in entry.corrections:
            field_name = field.capitalize()
            if field == "chest_type":
                field_name = "Chest Type"
            changes_text += f"{field_name}:\n  From: {from_val}\n  To: {to_val}\n\n"
        
        self._changes_text.setPlainText(changes_text)
    
    def _clear_preview(self) -> None:
        """Clear the preview."""
        self._current_entry = None
        self._original_text.clear()
        self._corrected_text.clear()
        self._changes_text.clear()
        self._entry_label.setText("No entries loaded")
        self._prev_button.setEnabled(False)
        self._next_button.setEnabled(False) 