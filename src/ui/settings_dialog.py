"""
settings_dialog.py

Description: Dialog for application settings
Usage:
    from src.ui.settings_dialog import SettingsDialog
    dialog = SettingsDialog(parent)
    if dialog.exec():
        # Settings were saved
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.services.config_manager import ConfigManager


class SettingsDialog(QDialog):
    """
    Dialog for application settings.

    This dialog allows users to configure various application settings,
    such as default paths, appearance options, and behavior preferences.

    Attributes:
        settings_updated (Signal): Signal emitted when settings are updated
    """

    settings_updated = Signal()

    def __init__(self, parent=None):
        """
        Initialize the SettingsDialog.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._config = ConfigManager()

        self.setWindowTitle("Settings")
        self.resize(500, 400)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Create tabs
        self._tabs = QTabWidget()
        self._setup_general_tab()
        self._setup_paths_tab()
        self._setup_appearance_tab()

        layout.addWidget(self._tabs)

        # Add standard buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _setup_general_tab(self):
        """Set up the general settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Placeholder for general settings
        layout.addRow(QLabel("General settings coming soon..."))

        self._tabs.addTab(tab, "General")

    def _setup_paths_tab(self):
        """Set up the paths settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Default correction rules path
        self._correction_rules_path = QLineEdit()
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_correction_rules)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self._correction_rules_path)
        path_layout.addWidget(browse_button)

        layout.addRow("Default correction rules path:", path_layout)

        self._tabs.addTab(tab, "Paths")

    def _setup_appearance_tab(self):
        """Set up the appearance settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Placeholder for appearance settings
        layout.addRow(QLabel("Appearance settings coming soon..."))

        self._tabs.addTab(tab, "Appearance")

    def _browse_correction_rules(self):
        """Browse for the default correction rules file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Default Correction Rules File",
            str(Path.home()),
            "CSV Files (*.csv);;All Files (*.*)",
        )

        if file_path:
            self._correction_rules_path.setText(file_path)

    def _load_settings(self):
        """Load settings from the config manager."""
        # Load correction rules path
        correction_rules_path = self._config.get(
            "Paths", "default_correction_rules", fallback=str(Path.cwd() / "corrections.csv")
        )
        self._correction_rules_path.setText(str(correction_rules_path))

    def _save_settings(self):
        """Save settings to the config manager and accept the dialog."""
        # Save correction rules path
        self._config.set("Paths", "default_correction_rules", self._correction_rules_path.text())

        # Save the config
        self._config.save()

        # Emit the settings updated signal
        self.settings_updated.emit()

        # Accept the dialog
        self.accept()
