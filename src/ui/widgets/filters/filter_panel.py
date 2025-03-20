"""
filter_panel.py

Description: Panel widget for organizing and managing filters
"""

from typing import Dict, List, Optional, Set, Any, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
)

from src.interfaces import IDataStore
from src.services.filters import (
    FilterManager,
    TextFilter,
    ValidationListFilter,
    DateFilter,
)
from src.ui.widgets.filters.filter_search_bar import FilterSearchBar
from src.ui.widgets.filters.filter_dropdown import FilterDropdown
from src.ui.widgets.filters.filter_date_range import FilterDateRange


class FilterPanel(QWidget):
    """
    A panel widget for organizing and managing filters.

    This panel integrates various filter UI components and
    manages their interaction with the filter manager.

    Attributes:
        filter_applied (Signal): Signal emitted when a filter is applied
    """

    filter_applied = Signal()

    def __init__(
        self,
        filter_manager: FilterManager,
        data_store: IDataStore,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the filter panel.

        Args:
            filter_manager: The filter manager to use
            data_store: Data store containing data to be filtered
            parent: The parent widget
        """
        super().__init__(parent)
        self._filter_manager = filter_manager
        self._data_store = data_store
        self._search_bar: Optional[FilterSearchBar] = None
        self._dropdown_filters: Dict[str, FilterDropdown] = {}
        self._date_filters: Dict[str, FilterDateRange] = {}
        self._active_filter_count = 0

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the panel's UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Panel title
        title_layout = QHBoxLayout()
        title_label = QLabel("Filters")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Clear all filters button
        self._clear_all_button = QPushButton("Clear All")
        self._clear_all_button.setFixedHeight(25)
        self._clear_all_button.clicked.connect(self.clear_all_filters)

        # Filter status indicator
        self._filter_status = QLabel("(0 active)")
        self._filter_status.setStyleSheet("color: gray;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(self._filter_status)
        title_layout.addStretch()
        title_layout.addWidget(self._clear_all_button)

        main_layout.addLayout(title_layout)

        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #cccccc;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)

        # Create scroll area for filters
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Container for filters
        self._filter_container = QWidget()
        self._filter_layout = QVBoxLayout(self._filter_container)
        self._filter_layout.setSpacing(0)
        self._filter_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area.setWidget(self._filter_container)
        main_layout.addWidget(scroll_area)

    def _connect_signals(self) -> None:
        """Connect filter signals to slots."""
        # Connect search bar if available
        if self._search_bar:
            self._search_bar.filter_changed.connect(self._emit_filter_applied)

        # Connect dropdown filters
        for filter_dropdown in self._dropdown_filters.values():
            filter_dropdown.filter_changed.connect(self._emit_filter_applied)

        # Connect date filters
        for date_filter in self._date_filters.values():
            date_filter.filter_changed.connect(self._emit_filter_applied)

    def set_search_bar(self, search_bar: FilterSearchBar) -> None:
        """
        Set the search bar for the panel.

        Args:
            search_bar: The search bar widget to use
        """
        self._search_bar = search_bar
        self._filter_layout.insertWidget(0, search_bar)

        # Connect signal
        search_bar.filter_changed.connect(self._emit_filter_applied)

    def add_validation_filter(
        self, filter_id: str, filter_obj: ValidationListFilter, title: str
    ) -> None:
        """
        Add a validation list filter to the panel.

        Args:
            filter_id: Unique identifier for the filter
            filter_obj: The validation list filter object
            title: Display title for the dropdown
        """
        # Create dropdown widget
        dropdown = FilterDropdown(filter_obj, title)

        # Add to layout
        self._filter_layout.addWidget(dropdown)

        # Store reference
        self._dropdown_filters[filter_id] = dropdown

        # Connect signal
        dropdown.filter_changed.connect(self._emit_filter_applied)

        # Register with filter manager
        self._filter_manager.register_filter(filter_id, filter_obj)

    def add_date_filter(self, filter_id: str, filter_obj: DateFilter, title: str) -> None:
        """
        Add a date filter to the panel.

        Args:
            filter_id: Unique identifier for the filter
            filter_obj: The date filter object
            title: Display title for the date range picker
        """
        # Create date range widget
        date_range = FilterDateRange(filter_obj, title)

        # Add to layout
        self._filter_layout.addWidget(date_range)

        # Store reference
        self._date_filters[filter_id] = date_range

        # Connect signal
        date_range.filter_changed.connect(self._emit_filter_applied)

        # Register with filter manager
        self._filter_manager.register_filter(filter_id, filter_obj)

    def update_filter_values(self, filter_id: str, values: List[str]) -> None:
        """
        Update the values for a dropdown filter.

        Args:
            filter_id: The filter identifier
            values: List of values to set
        """
        if filter_id in self._dropdown_filters:
            self._dropdown_filters[filter_id].set_items(values)

    def get_dropdown_filters(self) -> Dict[str, FilterDropdown]:
        """
        Get the dictionary of dropdown filters by ID.

        Returns:
            Dictionary of dropdown filters
        """
        return self._dropdown_filters

    def get_date_filters(self) -> Dict[str, FilterDateRange]:
        """
        Get the dictionary of date filters by ID.

        Returns:
            Dictionary of date filters
        """
        return self._date_filters

    def clear_all_filters(self) -> None:
        """Clear all filters in the panel."""
        # Clear search bar if available
        if self._search_bar:
            self._search_bar.clear()

        # Clear all dropdown selections
        for dropdown in self._dropdown_filters.values():
            dropdown.clear()

        # Clear all date filters
        for date_filter in self._date_filters.values():
            date_filter.clear()

        # Clear all filters in filter manager
        self._filter_manager.clear_all_filters()

        # Update status indicator
        self._update_filter_status()

        # Emit signal
        self.filter_applied.emit()

    def _emit_filter_applied(self) -> None:
        """Emit the filter_applied signal and update status."""
        self._update_filter_status()
        self.filter_applied.emit()

    def _update_filter_status(self) -> None:
        """Update the filter status indicator."""
        # Count active filters
        active_count = self._filter_manager.get_active_filter_count()

        # Update status text and style
        if active_count > 0:
            self._filter_status.setText(f"({active_count} active)")
            self._filter_status.setStyleSheet("font-weight: bold; color: #2c6496;")
        else:
            self._filter_status.setText("(0 active)")
            self._filter_status.setStyleSheet("color: gray;")

        # Store active count
        self._active_filter_count = active_count

    def get_active_filter_count(self) -> int:
        """
        Get the number of active filters.

        Returns:
            Number of active filters
        """
        return self._active_filter_count

    def save_filter_state(self, config: Any) -> None:
        """
        Save the state of all filters using the provided configuration manager.

        Args:
            config: The configuration manager to use
        """
        self._filter_manager.save_filter_state(config)

    def load_filter_state(self, config: Any) -> None:
        """
        Load the state of all filters using the provided configuration manager.

        Args:
            config: The configuration manager to use
        """
        self._filter_manager.load_filter_state(config)

        # Update UI elements based on loaded state
        self._update_ui_from_filter_state()

        # Update status indicator
        self._update_filter_status()

    def _update_ui_from_filter_state(self) -> None:
        """Update UI elements based on the current filter state."""
        # Update search bar if available
        if self._search_bar:
            text_filter = self._filter_manager.get_filter(self._search_bar.get_filter_id())
            if text_filter and isinstance(text_filter, TextFilter):
                self._search_bar.set_search_text(text_filter.get_search_text())
                self._search_bar.set_case_sensitive(text_filter.case_sensitive)
                self._search_bar.set_whole_word(text_filter.whole_word)
                self._search_bar.set_regex_enabled(text_filter.regex_enabled)

        # Update dropdown filters
        for filter_id, dropdown in self._dropdown_filters.items():
            filter_obj = self._filter_manager.get_filter(filter_id)
            if filter_obj and isinstance(filter_obj, ValidationListFilter):
                dropdown.set_selected_values(filter_obj.get_selected_values())

        # Update date filters
        for filter_id, date_filter in self._date_filters.items():
            filter_obj = self._filter_manager.get_filter(filter_id)
            if filter_obj and isinstance(filter_obj, DateFilter):
                date_filter.set_dates(filter_obj.get_start_date(), filter_obj.get_end_date())
