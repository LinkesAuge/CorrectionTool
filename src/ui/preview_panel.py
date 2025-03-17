"""
preview_panel.py

Description: Panel for previewing and applying corrections
Usage:
    from src.ui.preview_panel import PreviewPanel
    preview_panel = PreviewPanel(parent=self)
"""

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.services.corrector import Corrector
from src.services.file_parser import FileParser
from src.ui.styles import COLORS


class PreviewPanel(QWidget):
    """
    Panel for previewing and applying corrections.

    This panel shows a preview of the corrected text and allows the user
    to apply the corrections.

    Signals:
        corrections_applied (list): Signal emitted when corrections are applied

    Attributes:
        _entries (List[ChestEntry]): Current entries
        _correction_rules (List[CorrectionRule]): Current correction rules
        _corrector (Corrector): Corrector service
        _parser (FileParser): File parser service
    """

    # Signals
    corrections_applied = Signal(list)  # List[ChestEntry]

    def __init__(self, parent=None):
        """
        Initialize the preview panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize properties
        self._entries: List[ChestEntry] = []
        self._correction_rules: List[CorrectionRule] = []
        self._corrector = Corrector()
        self._parser = FileParser()

        # Set up UI
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)

        # Create preview text area
        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setFont(QFont("Consolas", 10))
        self._preview_text.setPlaceholderText(
            "No entries loaded. Import a file to preview corrections."
        )

        # Add to layout
        main_layout.addWidget(QLabel("Preview:"))
        main_layout.addWidget(self._preview_text)

        # Create buttons
        button_layout = QHBoxLayout()

        self._apply_button = QPushButton("Apply Corrections")
        self._apply_button.setEnabled(False)
        self._apply_button.clicked.connect(self._apply_corrections)

        self._save_button = QPushButton("Save Corrected File")
        self._save_button.setEnabled(False)
        self._save_button.clicked.connect(self._save_corrected_file)

        button_layout.addWidget(self._apply_button)
        button_layout.addWidget(self._save_button)

        # Add to layout
        main_layout.addLayout(button_layout)

    @Slot(list)
    def set_entries(self, entries: List[ChestEntry]):
        """
        Set the entries to preview.

        Args:
            entries: List of chest entries
        """
        self._entries = entries
        self._update_preview()
        self._apply_button.setEnabled(bool(entries) and bool(self._correction_rules))

    @Slot(list)
    def set_correction_rules(self, rules: List[CorrectionRule]):
        """
        Set the correction rules.

        Args:
            rules: List of correction rules
        """
        self._correction_rules = rules
        self._update_preview()
        self._apply_button.setEnabled(bool(self._entries) and bool(rules))

    def _update_preview(self):
        """Update the preview text with original and corrected entries."""
        if not self._entries or not self._correction_rules:
            self._preview_text.clear()
            self._preview_text.setPlaceholderText("No entries or correction rules loaded.")
            return

        # Generate preview by applying corrections to a copy of the entries
        corrected_entries = self._corrector.apply_corrections(
            [entry.clone() for entry in self._entries], self._correction_rules
        )

        # Create HTML preview with original and corrected side-by-side
        html = "<html><body style='font-family: Consolas, monospace;'>"
        html += "<table width='100%'>"
        html += (
            "<tr><th style='text-align: left; padding: 5px; color: "
            + COLORS["text_primary"]
            + ";'>Original</th>"
        )
        html += (
            "<th style='text-align: left; padding: 5px; color: "
            + COLORS["accent"]
            + ";'>Corrected</th></tr>"
        )

        for original, corrected in zip(self._entries, corrected_entries):
            if original != corrected:
                html += "<tr>"

                # Original column
                html += (
                    "<td style='padding: 5px; border: 1px solid "
                    + COLORS["border"]
                    + "; vertical-align: top;'>"
                )
                html += self._format_entry_html(original)
                html += "</td>"

                # Corrected column
                html += (
                    "<td style='padding: 5px; border: 1px solid "
                    + COLORS["border"]
                    + "; vertical-align: top;'>"
                )
                html += self._format_entry_html(corrected, original)
                html += "</td>"

                html += "</tr>"

        html += "</table></body></html>"

        # Set the HTML preview
        self._preview_text.setHtml(html)

    def _format_entry_html(self, entry: ChestEntry, original: Optional[ChestEntry] = None) -> str:
        """
        Format an entry as HTML.

        Args:
            entry: Entry to format
            original: Original entry to compare with (for highlighting changes)

        Returns:
            HTML representation of the entry
        """
        html = ""

        # Format chest type
        if original and entry.chest_type != original.chest_type:
            html += f"<div><b>Chest Type:</b> <span style='color: {COLORS['accent']};'>{entry.chest_type}</span></div>"
        else:
            html += f"<div><b>Chest Type:</b> {entry.chest_type}</div>"

        # Format player
        if original and entry.player != original.player:
            html += f"<div><b>Player:</b> <span style='color: {COLORS['accent']};'>{entry.player}</span></div>"
        else:
            html += f"<div><b>Player:</b> {entry.player}</div>"

        # Format source
        if original and entry.source != original.source:
            html += f"<div><b>Source:</b> <span style='color: {COLORS['accent']};'>{entry.source}</span></div>"
        else:
            html += f"<div><b>Source:</b> {entry.source}</div>"

        return html

    def _apply_corrections(self):
        """Apply corrections to entries and emit signal."""
        if not self._entries or not self._correction_rules:
            return

        # Apply corrections to the actual entries
        self._entries = self._corrector.apply_corrections(self._entries, self._correction_rules)

        # Enable save button
        self._save_button.setEnabled(True)

        # Emit signal with corrected entries
        self.corrections_applied.emit(self._entries)

    def _save_corrected_file(self):
        """Save corrected entries to a file."""
        from PySide6.QtWidgets import QFileDialog

        # Get save file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Corrected File", str(Path.cwd()), "Text Files (*.txt);;All Files (*.*)"
        )

        if not file_path:
            return

        # Save entries to file
        self._parser.save_entries_to_file(self._entries, file_path)
