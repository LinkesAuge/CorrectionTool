"""
filter_date_range.py

Description: Date range filter widget for filtering by date ranges
"""

from typing import Optional
from datetime import datetime, date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QDateEdit,
    QCheckBox,
)

from src.services.filters import DateFilter


class FilterDateRange(QWidget):
    """
    A date range filter widget for filtering based on date ranges.

    This widget provides date pickers for selecting start and end dates
    to filter data based on a date column.

    Attributes:
        filter_changed (Signal): Signal emitted when filter date range changes
    """

    filter_changed = Signal()

    def __init__(self, filter_obj: DateFilter, title: str, parent: Optional[QWidget] = None):
        """
        Initialize the date range filter widget.

        Args:
            filter_obj: The date filter object
            title: The display title for the filter
            parent: The parent widget
        """
        super().__init__(parent)
        self._filter = filter_obj
        self._title = title
        self._expanded = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the widget's UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Header layout
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 8, 8, 8)

        # Title and status label
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet("font-weight: bold;")
        self._status_label = QLabel("(Inactive)")
        self._status_label.setStyleSheet("color: gray;")

        # Expand/collapse button
        self._expand_button = QPushButton("▼")
        self._expand_button.setFixedSize(24, 24)

        # Add header components
        header_layout.addWidget(self._title_label)
        header_layout.addWidget(self._status_label)
        header_layout.addStretch()
        header_layout.addWidget(self._expand_button)

        # Date range container (initially hidden)
        self._date_container = QWidget()
        self._date_container.setVisible(False)
        date_layout = QVBoxLayout(self._date_container)
        date_layout.setContentsMargins(8, 0, 8, 8)

        # Start date layout
        start_date_layout = QHBoxLayout()
        self._start_date_label = QLabel("Start Date:")
        self._start_date_check = QCheckBox()
        self._start_date_check.setChecked(False)
        self._start_date_edit = QDateEdit()
        self._start_date_edit.setCalendarPopup(True)
        self._start_date_edit.setDate(datetime.now().date())
        self._start_date_edit.setEnabled(False)

        start_date_layout.addWidget(self._start_date_check)
        start_date_layout.addWidget(self._start_date_label)
        start_date_layout.addWidget(self._start_date_edit)

        # End date layout
        end_date_layout = QHBoxLayout()
        self._end_date_label = QLabel("End Date:")
        self._end_date_check = QCheckBox()
        self._end_date_check.setChecked(False)
        self._end_date_edit = QDateEdit()
        self._end_date_edit.setCalendarPopup(True)
        self._end_date_edit.setDate(datetime.now().date())
        self._end_date_edit.setEnabled(False)

        end_date_layout.addWidget(self._end_date_check)
        end_date_layout.addWidget(self._end_date_label)
        end_date_layout.addWidget(self._end_date_edit)

        # Control buttons
        button_layout = QHBoxLayout()
        self._clear_button = QPushButton("Clear")
        self._apply_button = QPushButton("Apply")
        self._clear_button.setFixedHeight(30)
        self._apply_button.setFixedHeight(30)

        button_layout.addWidget(self._clear_button)
        button_layout.addWidget(self._apply_button)

        # Add components to date container
        date_layout.addLayout(start_date_layout)
        date_layout.addLayout(end_date_layout)
        date_layout.addLayout(button_layout)

        # Add components to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(self._date_container)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #cccccc;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)

    def _connect_signals(self) -> None:
        """Connect widget signals to slots."""
        self._expand_button.clicked.connect(self._toggle_expand)
        self._clear_button.clicked.connect(self._clear_filter)
        self._apply_button.clicked.connect(self._apply_filter)

        # Connect date checkboxes
        self._start_date_check.stateChanged.connect(self._on_start_date_checked)
        self._end_date_check.stateChanged.connect(self._on_end_date_checked)

        # Connect date edits
        self._start_date_edit.dateChanged.connect(self._on_date_changed)
        self._end_date_edit.dateChanged.connect(self._on_date_changed)

    def _toggle_expand(self) -> None:
        """Toggle the expanded/collapsed state of the filter."""
        self._expanded = not self._expanded
        self._date_container.setVisible(self._expanded)
        self._expand_button.setText("▲" if self._expanded else "▼")

    def _clear_filter(self) -> None:
        """Clear the date filter."""
        self._start_date_check.setChecked(False)
        self._end_date_check.setChecked(False)
        self._filter.clear()
        self._update_status_label()
        self.filter_changed.emit()

    def _apply_filter(self) -> None:
        """Apply the date filter with the current values."""
        start_date = (
            self._start_date_edit.date().toPython() if self._start_date_check.isChecked() else None
        )
        end_date = (
            self._end_date_edit.date().toPython() if self._end_date_check.isChecked() else None
        )

        self._filter.set_date_objects(start_date, end_date)
        self._update_status_label()
        self.filter_changed.emit()

    def _on_start_date_checked(self, state: int) -> None:
        """
        Handle start date checkbox state changes.

        Args:
            state: Checkbox state
        """
        self._start_date_edit.setEnabled(state == Qt.Checked)
        self._on_date_changed()

    def _on_end_date_checked(self, state: int) -> None:
        """
        Handle end date checkbox state changes.

        Args:
            state: Checkbox state
        """
        self._end_date_edit.setEnabled(state == Qt.Checked)
        self._on_date_changed()

    def _on_date_changed(self) -> None:
        """Handle date changes and update the filter."""
        # Update filter
        start_date = (
            self._start_date_edit.date().toPython() if self._start_date_check.isChecked() else None
        )
        end_date = (
            self._end_date_edit.date().toPython() if self._end_date_check.isChecked() else None
        )

        self._filter.set_date_objects(start_date, end_date)
        self._update_status_label()
        self.filter_changed.emit()

    def _update_status_label(self) -> None:
        """Update the status label with the current filter state."""
        if not self._filter.is_active():
            self._status_label.setText("(Inactive)")
            self._status_label.setStyleSheet("color: gray;")
            return

        # Get current filter dates
        start_date = self._filter.get_start_date()
        end_date = self._filter.get_end_date()

        status_text = ""

        if start_date and end_date:
            status_text = (
                f"{self._filter.format_date(start_date)} - {self._filter.format_date(end_date)}"
            )
        elif start_date:
            status_text = f"From {self._filter.format_date(start_date)}"
        elif end_date:
            status_text = f"Until {self._filter.format_date(end_date)}"

        self._status_label.setText(f"({status_text})")
        self._status_label.setStyleSheet("font-weight: bold; color: #2c6496;")

    def set_dates(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> None:
        """
        Set the date range programmatically.

        Args:
            start_date: Start date
            end_date: End date
        """
        # Update start date if provided
        if start_date:
            self._start_date_check.setChecked(True)
            self._start_date_edit.setDate(start_date)
        else:
            self._start_date_check.setChecked(False)

        # Update end date if provided
        if end_date:
            self._end_date_check.setChecked(True)
            self._end_date_edit.setDate(end_date)
        else:
            self._end_date_check.setChecked(False)

        # Apply the filter with the new dates
        self._apply_filter()

    def get_start_date(self) -> Optional[date]:
        """
        Get the current start date.

        Returns:
            The start date, or None if not set
        """
        return self._filter.get_start_date()

    def get_end_date(self) -> Optional[date]:
        """
        Get the current end date.

        Returns:
            The end date, or None if not set
        """
        return self._filter.get_end_date()

    def clear(self) -> None:
        """Clear the date filter."""
        self._clear_filter()

    def expand(self) -> None:
        """Expand the filter."""
        if not self._expanded:
            self._toggle_expand()

    def collapse(self) -> None:
        """Collapse the filter."""
        if self._expanded:
            self._toggle_expand()

    def set_filter_enabled(self, enabled: bool) -> None:
        """
        Enable or disable the filter.

        Args:
            enabled: True to enable, False to disable
        """
        self._filter.enabled = enabled
        self._update_status_label()
