"""
filter_status_indicator.py

Description: Widget that displays filter status and allows clearing all active filters
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from src.services.filters import FilterManager


class FilterStatusIndicator(QWidget):
    """
    A widget that displays the status of active filters.

    This widget shows how many filters are currently active and
    provides a button to clear all filters at once.

    Attributes:
        filters_cleared (Signal): Signal emitted when filters are cleared
    """

    filters_cleared = Signal()

    def __init__(self, filter_manager: FilterManager, parent: Optional[QWidget] = None):
        """
        Initialize the filter status indicator.

        Args:
            filter_manager: The filter manager instance
            parent: The parent widget
        """
        super().__init__(parent)
        self._filter_manager = filter_manager

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the widget's UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Status label
        self._status_label = QLabel("No active filters")
        self._status_label.setStyleSheet("color: #666666;")

        # Clear button
        self._clear_button = QPushButton("Clear All")
        self._clear_button.setFixedHeight(24)
        self._clear_button.setVisible(False)

        layout.addWidget(self._status_label, 1)
        layout.addWidget(self._clear_button, 0)

    def _connect_signals(self) -> None:
        """Connect widget signals to slots."""
        self._clear_button.clicked.connect(self._clear_all_filters)

    def _clear_all_filters(self) -> None:
        """Clear all active filters."""
        self._filter_manager.clear_all_filters()
        self.update_status()
        self.filters_cleared.emit()

    def update_status(self) -> None:
        """Update the status display based on active filters."""
        active_count = self._filter_manager.get_active_filter_count()

        if active_count == 0:
            self._status_label.setText("No active filters")
            self._status_label.setStyleSheet("color: #666666;")
            self._clear_button.setVisible(False)
        else:
            filter_text = "filter" if active_count == 1 else "filters"
            self._status_label.setText(f"{active_count} active {filter_text}")
            self._status_label.setStyleSheet("color: #2c6496; font-weight: bold;")
            self._clear_button.setVisible(True)
