"""
navigation_panel.py

Description: Left navigation panel with icon buttons
Usage:
    from src.ui.navigation_panel import NavigationPanel
    navigation = NavigationPanel(parent=self)
"""

from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QSpacerItem,
)


class NavigationPanel(QWidget):
    """
    Left navigation panel with icon buttons.

    Provides navigation options for the application with a vertical button layout.

    Attributes:
        navigation_changed (Signal): Signal emitted when navigation changes

    Implementation Notes:
        - Uses QPushButtons with icons and text
        - Buttons are styled to match the dark theme
        - Selected button is highlighted
    """

    navigation_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the navigation panel.

        Args:
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        self.setObjectName("navigationPanel")

        # Set size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Initialize data
        self._current_item = ""

        # Initialize UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(5)

        # App title
        title_label = QLabel("Chest Tracker\nCorrection Tool")
        title_label.setObjectName("appTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white; margin-bottom: 20px;"
        )
        layout.addWidget(title_label)

        # Navigation buttons
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # Button definitions: id, text, icon
        buttons = [
            (0, "Dashboard", "dashboard"),
            (1, "Correction Manager", "settings"),
            (2, "Reports", "chart"),
            (3, "Settings", "settings"),
            (4, "Help", "help"),
        ]

        # Create buttons
        for btn_id, text, icon_name in buttons:
            button = self._create_nav_button(text, icon_name)
            layout.addWidget(button)
            self.button_group.addButton(button, btn_id)

        # Add spacer
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Connect button signals
        self.button_group.buttonClicked.connect(self._on_button_clicked)

        # Set layout
        self.setLayout(layout)

        # Select default button
        default_button = self.button_group.button(0)
        if default_button:
            default_button.setChecked(True)
            self._current_item = "Dashboard"
            self.navigation_changed.emit("Dashboard")

    def _create_nav_button(self, text: str, icon_name: str) -> QPushButton:
        """
        Create a navigation button.

        Args:
            text (str): Button text
            icon_name (str): Icon name

        Returns:
            QPushButton: The created button
        """
        button = QPushButton(text)
        button.setCheckable(True)
        button.setFixedHeight(40)

        # TODO: Replace with actual icons when available
        # For now, we'll just use text
        # button.setIcon(QIcon(f":/icons/{icon_name}.png"))
        # button.setIconSize(QSize(24, 24))

        return button

    def _on_button_clicked(self, button: QPushButton) -> None:
        """
        Handle button click events.

        Args:
            button (QPushButton): The clicked button
        """
        self._current_item = button.text()
        self.navigation_changed.emit(button.text())

    def select_item(self, item_name: str) -> bool:
        """
        Select a navigation item by name.

        Args:
            item_name (str): Name of the item to select

        Returns:
            bool: True if item was found and selected, False otherwise
        """
        for button in self.button_group.buttons():
            if button.text() == item_name:
                button.setChecked(True)
                self._current_item = item_name
                return True
        return False

    def current_item(self) -> str:
        """
        Get the current selected item name.

        Returns:
            str: Name of the currently selected item
        """
        return self._current_item

    def add_item(self, text: str, icon_name: str, tooltip: str = "") -> None:
        """
        Add a new navigation item.

        Args:
            text (str): Button text
            icon_name (str): Icon name
            tooltip (str, optional): Tooltip text
        """
        # Get the next available ID
        next_id = len(self.button_group.buttons())

        # Create button
        button = self._create_nav_button(text, icon_name)
        if tooltip:
            button.setToolTip(tooltip)

        # Add to layout
        layout = self.layout()
        layout.insertWidget(layout.count() - 1, button)  # Insert before spacer

        # Add to button group
        self.button_group.addButton(button, next_id)
