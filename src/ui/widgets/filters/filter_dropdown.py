"""
filter_dropdown.py

Description: Dropdown filter widget for selecting values from a list
"""

from typing import List, Set, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QScrollArea,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QRadioButton,
    QButtonGroup,
)

from src.services.filters import ValidationListFilter


class FilterDropdown(QWidget):
    """
    A dropdown widget for filtering based on a list of values.

    This widget provides a collapsible list of checkable items
    that can be selected to filter data based on specific values.

    Attributes:
        filter_changed (Signal): Signal emitted when filter selection changes
    """

    filter_changed = Signal()

    def __init__(
        self, filter_obj: ValidationListFilter, title: str, parent: Optional[QWidget] = None
    ):
        """
        Initialize the filter dropdown widget.

        Args:
            filter_obj: The validation list filter object
            title: The display title for the dropdown
            parent: The parent widget
        """
        super().__init__(parent)
        self._filter = filter_obj
        self._title = title
        self._selected_items: Set[str] = set()
        self._all_items: List[str] = []
        self._expanded = False
        self._search_text = ""

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

        # Title and count label
        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet("font-weight: bold;")
        self._count_label = QLabel("(0)")
        self._count_label.setStyleSheet("color: gray;")

        # Expand/collapse button
        self._expand_button = QPushButton("▼")
        self._expand_button.setFixedSize(24, 24)

        # Add header components
        header_layout.addWidget(self._title_label)
        header_layout.addWidget(self._count_label)
        header_layout.addStretch()
        header_layout.addWidget(self._expand_button)

        # List container (initially hidden)
        self._list_container = QWidget()
        self._list_container.setVisible(False)
        list_layout = QVBoxLayout(self._list_container)
        list_layout.setContentsMargins(8, 0, 8, 8)

        # Filter selection type (include/exclude)
        selection_type_layout = QHBoxLayout()
        self._include_radio = QRadioButton("Include")
        self._exclude_radio = QRadioButton("Exclude")
        self._selection_type_group = QButtonGroup(self)
        self._selection_type_group.addButton(self._include_radio, 0)
        self._selection_type_group.addButton(self._exclude_radio, 1)
        self._include_radio.setChecked(True)  # Default to include

        selection_type_layout.addWidget(self._include_radio)
        selection_type_layout.addWidget(self._exclude_radio)
        selection_type_layout.addStretch()

        # Add checkbox for case sensitivity
        self._case_sensitive_checkbox = QCheckBox("Case Sensitive")
        selection_type_layout.addWidget(self._case_sensitive_checkbox)

        list_layout.addLayout(selection_type_layout)

        # Search box for filtering items
        search_layout = QHBoxLayout()
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText(f"Search {self._title}...")
        self._clear_search_button = QPushButton("×")
        self._clear_search_button.setFixedSize(24, 24)
        self._clear_search_button.setVisible(False)

        search_layout.addWidget(self._search_edit)
        search_layout.addWidget(self._clear_search_button)

        list_layout.addLayout(search_layout)

        # Create scroll area for items
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Create list widget for items
        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(QListWidget.NoSelection)
        self._list_widget.setMaximumHeight(300)  # Increased height for better usability
        scroll_area.setWidget(self._list_widget)

        # Control buttons
        button_layout = QHBoxLayout()
        self._select_all_button = QPushButton("Select All")
        self._clear_button = QPushButton("Clear")
        self._select_all_button.setFixedHeight(30)
        self._clear_button.setFixedHeight(30)

        # Invert selection button
        self._invert_button = QPushButton("Invert")
        self._invert_button.setFixedHeight(30)

        button_layout.addWidget(self._select_all_button)
        button_layout.addWidget(self._clear_button)
        button_layout.addWidget(self._invert_button)

        # Add components to list container
        list_layout.addWidget(scroll_area)
        list_layout.addLayout(button_layout)

        # Add components to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(self._list_container)

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
        self._select_all_button.clicked.connect(self._select_all)
        self._clear_button.clicked.connect(self._clear_selection)
        self._invert_button.clicked.connect(self._invert_selection)
        self._list_widget.itemChanged.connect(self._on_item_changed)

        # Connect search signals
        self._search_edit.textChanged.connect(self._on_search_text_changed)
        self._clear_search_button.clicked.connect(self._clear_search)

        # Connect selection type signals
        self._selection_type_group.buttonClicked.connect(self._on_selection_type_changed)
        self._case_sensitive_checkbox.stateChanged.connect(self._on_case_sensitivity_changed)

    def _toggle_expand(self) -> None:
        """Toggle the expanded/collapsed state of the dropdown."""
        self._expanded = not self._expanded
        self._list_container.setVisible(self._expanded)
        self._expand_button.setText("▲" if self._expanded else "▼")

    def _select_all(self) -> None:
        """Select all items in the list."""
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if not item.isHidden():  # Only select visible items
                item.setCheckState(Qt.Checked)

    def _clear_selection(self) -> None:
        """Clear all selected items in the list."""
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            item.setCheckState(Qt.Unchecked)

    def _invert_selection(self) -> None:
        """Invert the current selection."""
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if not item.isHidden():  # Only invert visible items
                new_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
                item.setCheckState(new_state)

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        """
        Handle item selection changes.

        Args:
            item: The list widget item that changed
        """
        value = item.text()
        is_checked = item.checkState() == Qt.Checked

        if is_checked and value not in self._selected_items:
            self._selected_items.add(value)
        elif not is_checked and value in self._selected_items:
            self._selected_items.remove(value)

        self._update_filter()
        self._update_count_label()
        self.filter_changed.emit()

    def _on_search_text_changed(self, text: str) -> None:
        """
        Handle search text changes.

        Args:
            text: New search text
        """
        self._search_text = text
        self._clear_search_button.setVisible(bool(text))

        # Filter list items
        self._filter_list_items()

    def _filter_list_items(self) -> None:
        """Filter list items based on current search text."""
        if not self._search_text:
            # Show all items
            for i in range(self._list_widget.count()):
                self._list_widget.item(i).setHidden(False)
            return

        # Case-insensitive search
        search_text = self._search_text.lower()

        # Filter items
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            item_text = item.text().lower()
            item.setHidden(search_text not in item_text)

    def _clear_search(self) -> None:
        """Clear the search field."""
        self._search_edit.clear()

    def _on_selection_type_changed(self, button) -> None:
        """
        Handle selection type radio button changes.

        Args:
            button: Radio button that was clicked
        """
        # Update filter selection type
        selection_type = "exclude" if button == self._exclude_radio else "include"
        self._filter.selection_type = selection_type

        # Update filter and emit change
        self._update_filter()
        self.filter_changed.emit()

    def _on_case_sensitivity_changed(self, state) -> None:
        """
        Handle case sensitivity checkbox changes.

        Args:
            state: Checkbox state
        """
        # Update filter case sensitivity
        self._filter.case_sensitive = bool(state)

        # Update filter and emit change
        self._update_filter()
        self.filter_changed.emit()

    def _update_count_label(self) -> None:
        """Update the count label with the number of selected items."""
        count = len(self._selected_items)
        self._count_label.setText(f"({count})")

        # Apply bold styling if there are selected items
        if count > 0:
            self._count_label.setStyleSheet("font-weight: bold; color: #2c6496;")
        else:
            self._count_label.setStyleSheet("color: gray;")

    def _update_filter(self) -> None:
        """Update the associated filter with selected values."""
        self._filter.set_selected_values(list(self._selected_items))

    def set_items(self, items: List[str]) -> None:
        """
        Set the list of items in the dropdown.

        Args:
            items: List of items to display
        """
        self._all_items = items.copy()
        self._list_widget.clear()

        # Store previously selected items
        previously_selected = self._selected_items.copy()

        # Clear selected items
        self._selected_items.clear()

        for item_text in items:
            item = QListWidgetItem(item_text)
            # Check the item if it was previously selected
            is_selected = item_text in previously_selected
            item.setCheckState(Qt.Checked if is_selected else Qt.Unchecked)

            # Add to selected items if previously selected
            if is_selected:
                self._selected_items.add(item_text)

            self._list_widget.addItem(item)

        # Apply search filter if any
        if self._search_text:
            self._filter_list_items()

        # Update count label
        self._update_count_label()

        # Update filter
        self._update_filter()

    def set_selected_values(self, values: List[str]) -> None:
        """
        Set the selected values programmatically.

        Args:
            values: List of values to select
        """
        self._selected_items = set(values)

        # Update checkboxes in the list
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            is_selected = item.text() in self._selected_items
            item.setCheckState(Qt.Checked if is_selected else Qt.Unchecked)

        self._update_filter()
        self._update_count_label()

    def get_selected_values(self) -> List[str]:
        """
        Get the currently selected values.

        Returns:
            List of selected values
        """
        return list(self._selected_items)

    def clear(self) -> None:
        """Clear all selections."""
        self._clear_selection()

    def expand(self) -> None:
        """Expand the dropdown."""
        if not self._expanded:
            self._toggle_expand()

    def collapse(self) -> None:
        """Collapse the dropdown."""
        if self._expanded:
            self._toggle_expand()
