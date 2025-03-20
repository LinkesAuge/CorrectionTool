"""
filter_search_bar.py

Description: Search bar widget for text-based filtering
"""

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QComboBox,
    QCheckBox,
    QFrame,
)

from src.services.filters import TextFilter


class FilterSearchBar(QWidget):
    """
    A search bar widget for text-based filtering.

    This widget provides a search input field with options
    to filter data based on text content.

    Attributes:
        search_changed (Signal): Signal emitted when search text changes
    """

    search_changed = Signal()

    def __init__(
        self,
        filter_obj: TextFilter,
        columns: Optional[List[str]] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the search bar widget.

        Args:
            filter_obj: The text filter object
            columns: List of column names for column selection
            parent: The parent widget
        """
        super().__init__(parent)
        self._filter = filter_obj
        self._columns = columns or []

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the widget's UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Search bar layout
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        # Search input
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search...")

        # Clear button
        self._clear_button = QPushButton("✕")
        self._clear_button.setFixedSize(24, 24)
        self._clear_button.setVisible(False)

        search_layout.addWidget(self._search_edit, 1)
        search_layout.addWidget(self._clear_button, 0)

        main_layout.addLayout(search_layout)

        # Options layout
        options_layout = QHBoxLayout()
        options_layout.setSpacing(16)

        # Column selector (optional)
        if self._columns:
            column_layout = QHBoxLayout()
            column_layout.setSpacing(8)

            column_label = QLabel("Column:")
            self._column_combo = QComboBox()
            self._column_combo.addItem("All Columns")
            self._column_combo.addItems(self._columns)

            column_layout.addWidget(column_label)
            column_layout.addWidget(self._column_combo)
            options_layout.addLayout(column_layout)
        else:
            self._column_combo = None

        # Options checkboxes
        self._case_sensitive_check = QCheckBox("Case Sensitive")
        self._whole_word_check = QCheckBox("Whole Word")
        self._regex_check = QCheckBox("Regex")

        options_layout.addWidget(self._case_sensitive_check)
        options_layout.addWidget(self._whole_word_check)
        options_layout.addWidget(self._regex_check)
        options_layout.addStretch()

        main_layout.addLayout(options_layout)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #cccccc;")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)

    def _connect_signals(self) -> None:
        """Connect widget signals to slots."""
        self._search_edit.textChanged.connect(self._on_search_text_changed)
        self._clear_button.clicked.connect(self._clear_search)

        # Connect options signals
        self._case_sensitive_check.stateChanged.connect(self._on_option_changed)
        self._whole_word_check.stateChanged.connect(self._on_option_changed)
        self._regex_check.stateChanged.connect(self._on_option_changed)

        # Connect column selector if available
        if self._column_combo:
            self._column_combo.currentIndexChanged.connect(self._on_column_changed)

    def _on_search_text_changed(self, text: str) -> None:
        """
        Handle search text changes.

        Args:
            text: The new search text
        """
        self._clear_button.setVisible(bool(text))
        self._filter.set_search_text(text)
        self.search_changed.emit()

    def _clear_search(self) -> None:
        """Clear the search text."""
        self._search_edit.clear()

    def _on_option_changed(self) -> None:
        """Handle option checkbox changes."""
        self._filter.case_sensitive = self._case_sensitive_check.isChecked()
        self._filter.whole_word = self._whole_word_check.isChecked()
        self._filter.use_regex = self._regex_check.isChecked()

        # Update the filter if there's search text
        if self._search_edit.text():
            self.search_changed.emit()

    def _on_column_changed(self, index: int) -> None:
        """
        Handle column selection changes.

        Args:
            index: The selected column index
        """
        if index == 0:
            # "All Columns" selected
            self._filter.target_columns = []
        else:
            # Specific column selected
            column_name = self._column_combo.currentText()
            self._filter.target_columns = [column_name]

        # Update the filter if there's search text
        if self._search_edit.text():
            self.search_changed.emit()

    def set_search_text(self, text: str) -> None:
        """
        Set the search text programmatically.

        Args:
            text: The search text to set
        """
        self._search_edit.setText(text)

    def get_search_text(self) -> str:
        """
        Get the current search text.

        Returns:
            The current search text
        """
        return self._search_edit.text()

    def set_case_sensitive(self, enabled: bool) -> None:
        """
        Set case sensitivity option.

        Args:
            enabled: Whether case sensitivity is enabled
        """
        self._case_sensitive_check.setChecked(enabled)

    def set_whole_word(self, enabled: bool) -> None:
        """
        Set whole word matching option.

        Args:
            enabled: Whether whole word matching is enabled
        """
        self._whole_word_check.setChecked(enabled)

    def set_regex_enabled(self, enabled: bool) -> None:
        """
        Set regex matching option.

        Args:
            enabled: Whether regex matching is enabled
        """
        self._regex_check.setChecked(enabled)

    def clear(self) -> None:
        """Clear the search and reset options."""
        self._search_edit.clear()
        self._case_sensitive_check.setChecked(False)
        self._whole_word_check.setChecked(False)
        self._regex_check.setChecked(False)

        if self._column_combo:
            self._column_combo.setCurrentIndex(0)
