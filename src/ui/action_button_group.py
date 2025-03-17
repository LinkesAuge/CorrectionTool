"""
action_button_group.py

Description: Widget containing commonly used action buttons
Usage:
    from src.ui.action_button_group import ActionButtonGroup
    button_group = ActionButtonGroup(parent=self)
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QToolButton,
    QSizePolicy,
    QWidget,
)

from src.services.config_manager import ConfigManager


class ActionButtonGroup(QWidget):
    """
    Widget containing commonly used action buttons.

    This widget provides a set of action buttons for common operations
    in the application, such as save, export, apply corrections, etc.

    Signals:
        save_requested: Signal emitted when the save button is clicked
        export_requested: Signal emitted when the export button is clicked
        apply_corrections_requested: Signal emitted when the apply corrections button is clicked
        settings_requested: Signal emitted when the settings button is clicked

    Implementation Notes:
        - Provides a horizontal layout of tool buttons
        - Each button has an icon and tooltip
        - Buttons can be enabled/disabled based on application state
        - Configuration options loaded from ConfigManager
    """

    # Signals
    save_requested = Signal()
    export_requested = Signal()
    apply_corrections_requested = Signal()
    settings_requested = Signal()

    def __init__(self, parent=None):
        """
        Initialize the action button group.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize properties
        self._config = ConfigManager()
        self._buttons = {}

        # Set up UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # Create buttons
        self._buttons["save"] = self._create_action_button(
            icon_name="save", tooltip="Save current entries", enabled=False
        )

        self._buttons["export"] = self._create_action_button(
            icon_name="export", tooltip="Export entries to file", enabled=False
        )

        main_layout.addStretch(1)  # Flexible spacer

        self._buttons["apply_corrections"] = self._create_action_button(
            icon_name="apply", tooltip="Apply corrections to entries", enabled=False
        )

        main_layout.addStretch(1)  # Flexible spacer

        self._buttons["settings"] = self._create_action_button(
            icon_name="settings", tooltip="Open settings", enabled=True
        )

        # Add buttons to layout
        for button_name, button in self._buttons.items():
            main_layout.addWidget(button)

    def _connect_signals(self):
        """Connect signals to slots."""
        self._buttons["save"].clicked.connect(self.save_requested.emit)
        self._buttons["export"].clicked.connect(self.export_requested.emit)
        self._buttons["apply_corrections"].clicked.connect(self.apply_corrections_requested.emit)
        self._buttons["settings"].clicked.connect(self.settings_requested.emit)

    def _create_action_button(
        self, icon_name: str, tooltip: str, enabled: bool = True
    ) -> QToolButton:
        """
        Create an action button with the specified properties.

        Args:
            icon_name: Name of the icon (without extension)
            tooltip: Tooltip text for the button
            enabled: Whether the button should be enabled initially

        Returns:
            The created tool button
        """
        button = QToolButton(self)

        # Try to load icon
        try:
            # In a real implementation, we would load an actual icon
            # For now, just set the text
            button.setText(icon_name)

            # Uncomment this when icons are available
            # icon_path = f":/icons/{icon_name}.png"
            # button.setIcon(QIcon(icon_path))
            # button.setIconSize(QSize(24, 24))
        except Exception:
            # Fallback to text if icon not found
            button.setText(icon_name[0].upper())

        # Set properties
        button.setToolTip(tooltip)
        button.setEnabled(enabled)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        return button

    def set_entries_loaded(self, loaded: bool) -> None:
        """
        Update button states based on whether entries are loaded.

        Args:
            loaded: Whether entries are loaded
        """
        self._buttons["save"].setEnabled(loaded)
        self._buttons["export"].setEnabled(loaded)

    def set_corrections_loaded(self, loaded: bool) -> None:
        """
        Update button states based on whether correction rules are loaded.

        Args:
            loaded: Whether correction rules are loaded
        """
        # Only enable if we have correction rules
        self._buttons["apply_corrections"].setEnabled(loaded)

    def set_button_enabled(self, button_name: str, enabled: bool) -> None:
        """
        Set the enabled state of a specific button.

        Args:
            button_name: Name of the button to update
            enabled: Whether the button should be enabled
        """
        if button_name in self._buttons:
            self._buttons[button_name].setEnabled(enabled)
