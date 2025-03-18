"""
reports_panel.py

Description: Panel for generating and displaying reports
Usage:
    from src.ui.reports_panel import ReportPanel
    report_panel = ReportPanel(parent)
"""

import logging
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.models.validation_list import ValidationList


class ReportPanel(QWidget):
    """
    Panel for generating and displaying reports.

    This panel allows users to generate various reports based on the loaded entries,
    applied corrections, and validation results.

    Attributes:
        entries (List[ChestEntry]): The current list of chest entries
        correction_rules (List[CorrectionRule]): The current list of correction rules
        validation_lists (Dict[str, ValidationList]): The current validation lists
    """

    def __init__(self, parent=None):
        """
        Initialize the ReportPanel.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._entries: List[ChestEntry] = []
        self._correction_rules: List[CorrectionRule] = []
        self._validation_lists: Dict[str, ValidationList] = {}

        # Signal processing flag to prevent recursion
        self._processing_signal = False

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Placeholder label
        placeholder = QLabel("Reports functionality coming soon...")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)

        self.setLayout(layout)

    @Slot(list)
    def set_entries(self, entries: List[ChestEntry]):
        """
        Set the current entries.

        Args:
            entries (List[ChestEntry]): The entries to set
        """
        self._entries = entries

    @Slot(list)
    def set_correction_rules(self, rules: List[CorrectionRule]):
        """
        Set the current correction rules.

        Args:
            rules (List[CorrectionRule]): The correction rules to set
        """
        self._correction_rules = rules

    @Slot(dict)
    def set_validation_lists(self, lists: Dict[str, ValidationList]):
        """
        Set the current validation lists.

        Args:
            lists (Dict[str, ValidationList]): The validation lists to set
        """
        # Signal loop protection
        if hasattr(self, "_processing_signal") and self._processing_signal:
            logging.warning("ReportsPanel: Signal loop detected in set_validation_lists")
            return

        if not lists:
            logging.warning("ReportsPanel: Empty validation lists received")
            return

        try:
            self._processing_signal = True

            # Log the received lists
            logging.info(f"ReportsPanel: Received {len(lists)} validation lists")

            # Update the validation lists
            self._validation_lists = lists

            logging.info("ReportsPanel: Validation lists updated")
        except Exception as e:
            logging.error(f"ReportsPanel: Error in set_validation_lists: {e}")
        finally:
            self._processing_signal = False
