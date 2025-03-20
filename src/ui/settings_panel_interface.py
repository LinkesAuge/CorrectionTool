"""
settings_panel_interface.py

Description: A panel for managing application settings using a tabbed interface
Usage:
    settings_panel = SettingsPanelInterface(service_factory)
    settings_panel.show()
"""

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QComboBox,
    QSlider,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from src.interfaces.i_config_manager import IConfigManager
from src.interfaces.i_service_factory import IServiceFactory


class SettingsPanelInterface(QWidget):
    """
    Interface for managing application settings through a tabbed interface.

    This panel allows users to configure various aspects of the application,
    including general settings, file paths, validation settings, and UI settings.
    Settings are loaded from and saved to a configuration manager service.

    Signals:
        settings_changed: Emitted when settings have been saved
    """

    settings_changed = Signal()

    def __init__(self, service_factory: IServiceFactory, parent=None):
        """
        Initialize the settings panel interface.

        Args:
            service_factory (IServiceFactory): Factory for getting service instances
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._logger.info("Initializing SettingsPanelInterface")

        self._service_factory = service_factory
        self._config_manager = self._service_factory.get_service(IConfigManager)

        # Track which settings have been modified and changed
        self._modified_settings = {}
        self._changed_settings = {}

        # Setup UI
        self.setWindowTitle("Settings")
        self.resize(600, 500)
        self._setup_ui()
        self._connect_signals()
        self._load_settings()

        self._logger.info("SettingsPanelInterface initialized")

    def _setup_ui(self):
        """Set up the settings panel UI with tabs for different setting categories."""
        main_layout = QVBoxLayout(self)

        # Create tab widget
        self._tab_widget = QTabWidget(self)

        # Create tabs for different settings categories
        self._setup_general_tab()
        self._setup_file_paths_tab()
        self._setup_validation_tab()
        self._setup_ui_settings()

        main_layout.addWidget(self._tab_widget)

        # Add buttons at the bottom
        button_layout = QHBoxLayout()

        # Spacer to push buttons to the right
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Save and Reset buttons
        self._save_button = QPushButton("Save Settings")
        self._reset_button = QPushButton("Reset to Defaults")

        button_layout.addWidget(self._save_button)
        button_layout.addWidget(self._reset_button)

        main_layout.addLayout(button_layout)

    def _setup_general_tab(self):
        """Set up the general settings tab."""
        general_tab = QWidget()
        layout = QVBoxLayout(general_tab)

        # Auto-save settings
        self._auto_save_checkbox = QCheckBox("Auto-save settings when changed")
        layout.addWidget(self._auto_save_checkbox)

        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Interface Theme:"))
        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Light", "light")
        self._theme_combo.addItem("Dark", "dark")
        theme_layout.addWidget(self._theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # Remember window size and position
        self._remember_size_checkbox = QCheckBox("Remember window size and position")
        layout.addWidget(self._remember_size_checkbox)

        # Add spacer to push everything to the top
        layout.addStretch()

        self._tab_widget.addTab(general_tab, "General")

    def _setup_file_paths_tab(self):
        """Set up the file paths tab with directory selection controls."""
        paths_tab = QWidget()
        layout = QVBoxLayout(paths_tab)

        # Input directory
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Default Input Directory:"))
        self._input_dir_edit = QLineEdit()
        input_layout.addWidget(self._input_dir_edit)
        input_browse_button = QPushButton("Browse...")
        input_browse_button.clicked.connect(lambda: self._browse_directory("input"))
        input_layout.addWidget(input_browse_button)
        layout.addLayout(input_layout)

        # Output directory
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Default Output Directory:"))
        self._output_dir_edit = QLineEdit()
        output_layout.addWidget(self._output_dir_edit)
        output_browse_button = QPushButton("Browse...")
        output_browse_button.clicked.connect(lambda: self._browse_directory("output"))
        output_layout.addWidget(output_browse_button)
        layout.addLayout(output_layout)

        # Corrections directory
        corrections_layout = QHBoxLayout()
        corrections_layout.addWidget(QLabel("Default Corrections Directory:"))
        self._corrections_dir_edit = QLineEdit()
        corrections_layout.addWidget(self._corrections_dir_edit)
        corrections_browse_button = QPushButton("Browse...")
        corrections_browse_button.clicked.connect(lambda: self._browse_directory("corrections"))
        corrections_layout.addWidget(corrections_browse_button)
        layout.addLayout(corrections_layout)

        # Validation lists directory
        validation_layout = QHBoxLayout()
        validation_layout.addWidget(QLabel("Default Validation Lists Directory:"))
        self._validation_dir_edit = QLineEdit()
        validation_layout.addWidget(self._validation_dir_edit)
        validation_browse_button = QPushButton("Browse...")
        validation_browse_button.clicked.connect(lambda: self._browse_directory("validation"))
        validation_layout.addWidget(validation_browse_button)
        layout.addLayout(validation_layout)

        # File extensions
        extensions_group = QGroupBox("Default File Extensions")
        extensions_layout = QFormLayout(extensions_group)

        self._input_ext_combo = QComboBox()
        self._input_ext_combo.addItem("CSV (.csv)", "csv")
        self._input_ext_combo.addItem("Text (.txt)", "txt")
        self._input_ext_combo.addItem("JSON (.json)", "json")
        extensions_layout.addRow("Input Files:", self._input_ext_combo)

        self._correction_ext_combo = QComboBox()
        self._correction_ext_combo.addItem("CSV (.csv)", "csv")
        self._correction_ext_combo.addItem("Text (.txt)", "txt")
        self._correction_ext_combo.addItem("JSON (.json)", "json")
        extensions_layout.addRow("Correction Files:", self._correction_ext_combo)

        layout.addWidget(extensions_group)

        # Add spacer to push everything to the top
        layout.addStretch()

        self._tab_widget.addTab(paths_tab, "File Paths")

    def _setup_validation_tab(self):
        """Set up the validation settings tab."""
        validation_tab = QWidget()
        layout = QVBoxLayout(validation_tab)

        # List names
        names_group = QGroupBox("Validation List Names")
        names_layout = QFormLayout(names_group)

        self._player_list_name_edit = QLineEdit()
        names_layout.addRow("Player List:", self._player_list_name_edit)

        self._chest_type_list_name_edit = QLineEdit()
        names_layout.addRow("Chest Type List:", self._chest_type_list_name_edit)

        self._source_list_name_edit = QLineEdit()
        names_layout.addRow("Source List:", self._source_list_name_edit)

        layout.addWidget(names_group)

        # Fuzzy matching settings
        fuzzy_group = QGroupBox("Fuzzy Matching")
        fuzzy_layout = QVBoxLayout(fuzzy_group)

        self._fuzzy_enabled_checkbox = QCheckBox("Enable fuzzy matching for validation lists")
        fuzzy_layout.addWidget(self._fuzzy_enabled_checkbox)

        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Match Threshold:"))
        self._fuzzy_threshold_slider = QSlider(Qt.Horizontal)
        self._fuzzy_threshold_slider.setMinimum(50)
        self._fuzzy_threshold_slider.setMaximum(100)
        self._fuzzy_threshold_slider.setTickInterval(5)
        self._fuzzy_threshold_slider.setTickPosition(QSlider.TicksBelow)
        threshold_layout.addWidget(self._fuzzy_threshold_slider)
        self._threshold_value_label = QLabel("80%")
        threshold_layout.addWidget(self._threshold_value_label)

        fuzzy_layout.addLayout(threshold_layout)
        layout.addWidget(fuzzy_group)

        # Add spacer to push everything to the top
        layout.addStretch()

        self._tab_widget.addTab(validation_tab, "Validation")

    def _setup_ui_settings(self):
        """Set up the UI settings tab."""
        ui_tab = QWidget()
        layout = QVBoxLayout(ui_tab)

        # Table appearance
        appearance_group = QGroupBox("Table Appearance")
        appearance_layout = QVBoxLayout(appearance_group)

        self._show_grid_checkbox = QCheckBox("Show grid lines")
        appearance_layout.addWidget(self._show_grid_checkbox)

        self._alternate_colors_checkbox = QCheckBox("Use alternate row colors")
        appearance_layout.addWidget(self._alternate_colors_checkbox)

        # Row height
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Row Height:"))
        self._row_height_slider = QSlider(Qt.Horizontal)
        self._row_height_slider.setMinimum(20)
        self._row_height_slider.setMaximum(50)
        self._row_height_slider.setTickInterval(5)
        self._row_height_slider.setTickPosition(QSlider.TicksBelow)
        height_layout.addWidget(self._row_height_slider)
        self._row_height_label = QLabel("30px")
        height_layout.addWidget(self._row_height_label)

        appearance_layout.addLayout(height_layout)

        # Font size
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font Size:"))
        self._font_size_slider = QSlider(Qt.Horizontal)
        self._font_size_slider.setMinimum(8)
        self._font_size_slider.setMaximum(16)
        self._font_size_slider.setTickInterval(1)
        self._font_size_slider.setTickPosition(QSlider.TicksBelow)
        font_layout.addWidget(self._font_size_slider)
        self._font_size_label = QLabel("10pt")
        font_layout.addWidget(self._font_size_label)

        appearance_layout.addLayout(font_layout)

        layout.addWidget(appearance_group)

        # Add spacer to push everything to the top
        layout.addStretch()

        self._tab_widget.addTab(ui_tab, "UI Settings")

    def _connect_signals(self):
        """Connect UI signals to their handlers."""
        # General tab
        self._auto_save_checkbox.stateChanged.connect(
            lambda state: self._mark_setting_changed("App", "auto_save_settings")
        )
        self._theme_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("UI", "theme")
        )
        self._remember_size_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("UI", "remember_window_size")
        )

        # File extensions
        self._input_ext_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_input_extension")
        )
        self._correction_ext_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_correction_extension")
        )

        # Validation settings
        self._player_list_name_edit.textChanged.connect(
            lambda: self._mark_setting_changed("ValidationLists", "player_list_name")
        )
        self._chest_type_list_name_edit.textChanged.connect(
            lambda: self._mark_setting_changed("ValidationLists", "chest_type_list_name")
        )
        self._source_list_name_edit.textChanged.connect(
            lambda: self._mark_setting_changed("ValidationLists", "source_list_name")
        )

        # Fuzzy matching
        self._fuzzy_enabled_checkbox.stateChanged.connect(self._on_fuzzy_enabled_changed)
        self._fuzzy_threshold_slider.valueChanged.connect(self._on_fuzzy_threshold_changed)

        # UI settings
        self._show_grid_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("UI", "show_grid_lines")
        )
        self._alternate_colors_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("UI", "alternate_row_colors")
        )
        self._row_height_slider.valueChanged.connect(self._on_row_height_changed)
        self._font_size_slider.valueChanged.connect(self._on_font_size_changed)

        # Button actions
        self._save_button.clicked.connect(self._on_save_clicked)
        self._reset_button.clicked.connect(self._on_reset_clicked)

    def _load_settings(self):
        """Load settings from the config manager and update UI controls."""
        self._logger.info("Loading settings")

        # General settings
        auto_save = self._config_manager.get_bool("App", "auto_save_settings", True)
        self._auto_save_checkbox.setChecked(auto_save)

        theme = self._config_manager.get_value("UI", "theme", "light")
        for i in range(self._theme_combo.count()):
            if self._theme_combo.itemData(i) == theme:
                self._theme_combo.setCurrentIndex(i)
                break

        remember_size = self._config_manager.get_bool("UI", "remember_window_size", True)
        self._remember_size_checkbox.setChecked(remember_size)

        # File paths
        input_dir = self._config_manager.get_path("default_input_dir", "")
        self._input_dir_edit.setText(str(input_dir))

        output_dir = self._config_manager.get_path("default_output_dir", "")
        self._output_dir_edit.setText(str(output_dir))

        corrections_dir = self._config_manager.get_path("default_corrections_dir", "")
        self._corrections_dir_edit.setText(str(corrections_dir))

        validation_dir = self._config_manager.get_path("default_validation_dir", "")
        self._validation_dir_edit.setText(str(validation_dir))

        # File extensions
        input_ext = self._config_manager.get_value("Files", "default_input_extension", "csv")
        for i in range(self._input_ext_combo.count()):
            if self._input_ext_combo.itemData(i) == input_ext:
                self._input_ext_combo.setCurrentIndex(i)
                break

        correction_ext = self._config_manager.get_value(
            "Files", "default_correction_extension", "csv"
        )
        for i in range(self._correction_ext_combo.count()):
            if self._correction_ext_combo.itemData(i) == correction_ext:
                self._correction_ext_combo.setCurrentIndex(i)
                break

        # Validation settings
        player_list_name = self._config_manager.get_value(
            "ValidationLists", "player_list_name", "Player List"
        )
        self._player_list_name_edit.setText(player_list_name)

        chest_list_name = self._config_manager.get_value(
            "ValidationLists", "chest_type_list_name", "Chest Type List"
        )
        self._chest_type_list_name_edit.setText(chest_list_name)

        source_list_name = self._config_manager.get_value(
            "ValidationLists", "source_list_name", "Source List"
        )
        self._source_list_name_edit.setText(source_list_name)

        # Fuzzy matching
        fuzzy_enabled = self._config_manager.get_bool(
            "ValidationSettings", "fuzzy_matching_enabled", True
        )
        self._fuzzy_enabled_checkbox.setChecked(fuzzy_enabled)

        fuzzy_threshold = self._config_manager.get_int("ValidationSettings", "fuzzy_threshold", 80)
        self._fuzzy_threshold_slider.setValue(fuzzy_threshold)
        self._threshold_value_label.setText(f"{fuzzy_threshold}%")
        self._fuzzy_threshold_slider.setEnabled(fuzzy_enabled)

        # UI settings
        show_grid = self._config_manager.get_bool("UI", "show_grid_lines", True)
        self._show_grid_checkbox.setChecked(show_grid)

        alternate_colors = self._config_manager.get_bool("UI", "alternate_row_colors", True)
        self._alternate_colors_checkbox.setChecked(alternate_colors)

        row_height = self._config_manager.get_int("UI", "table_row_height", 30)
        self._row_height_slider.setValue(row_height)
        self._row_height_label.setText(f"{row_height}px")

        font_size = self._config_manager.get_int("UI", "font_size", 10)
        self._font_size_slider.setValue(font_size)
        self._font_size_label.setText(f"{font_size}pt")

        # Reset tracking of changed settings
        self._reset_changed_settings()

    def _save_settings(self):
        """Save the changed settings to the config manager."""
        self._logger.info("Saving settings")

        # General settings
        if "App" in self._changed_settings:
            if "auto_save_settings" in self._changed_settings["App"]:
                self._config_manager.set_value(
                    "App", "auto_save_settings", str(self._auto_save_checkbox.isChecked())
                )

        if "UI" in self._changed_settings:
            if "theme" in self._changed_settings["UI"]:
                self._config_manager.set_value("UI", "theme", self._theme_combo.currentData())

            if "remember_window_size" in self._changed_settings["UI"]:
                self._config_manager.set_value(
                    "UI", "remember_window_size", str(self._remember_size_checkbox.isChecked())
                )

            if "show_grid_lines" in self._changed_settings["UI"]:
                self._config_manager.set_value(
                    "UI", "show_grid_lines", str(self._show_grid_checkbox.isChecked())
                )

            if "alternate_row_colors" in self._changed_settings["UI"]:
                self._config_manager.set_value(
                    "UI", "alternate_row_colors", str(self._alternate_colors_checkbox.isChecked())
                )

            if "table_row_height" in self._changed_settings["UI"]:
                self._config_manager.set_value(
                    "UI", "table_row_height", str(self._row_height_slider.value())
                )

            if "font_size" in self._changed_settings["UI"]:
                self._config_manager.set_value(
                    "UI", "font_size", str(self._font_size_slider.value())
                )

        # File paths
        if "Files" in self._changed_settings:
            if "default_input_dir" in self._changed_settings["Files"]:
                self._config_manager.set_path("default_input_dir", self._input_dir_edit.text())

            if "default_output_dir" in self._changed_settings["Files"]:
                self._config_manager.set_path("default_output_dir", self._output_dir_edit.text())

            if "default_corrections_dir" in self._changed_settings["Files"]:
                self._config_manager.set_path(
                    "default_corrections_dir", self._corrections_dir_edit.text()
                )

            if "default_validation_dir" in self._changed_settings["Files"]:
                self._config_manager.set_path(
                    "default_validation_dir", self._validation_dir_edit.text()
                )

            if "default_input_extension" in self._changed_settings["Files"]:
                self._config_manager.set_value(
                    "Files", "default_input_extension", self._input_ext_combo.currentData()
                )

            if "default_correction_extension" in self._changed_settings["Files"]:
                self._config_manager.set_value(
                    "Files",
                    "default_correction_extension",
                    self._correction_ext_combo.currentData(),
                )

        # Validation settings
        if "ValidationLists" in self._changed_settings:
            if "player_list_name" in self._changed_settings["ValidationLists"]:
                self._config_manager.set_value(
                    "ValidationLists", "player_list_name", self._player_list_name_edit.text()
                )

            if "chest_type_list_name" in self._changed_settings["ValidationLists"]:
                self._config_manager.set_value(
                    "ValidationLists",
                    "chest_type_list_name",
                    self._chest_type_list_name_edit.text(),
                )

            if "source_list_name" in self._changed_settings["ValidationLists"]:
                self._config_manager.set_value(
                    "ValidationLists", "source_list_name", self._source_list_name_edit.text()
                )

        if "ValidationSettings" in self._changed_settings:
            if "fuzzy_matching_enabled" in self._changed_settings["ValidationSettings"]:
                self._config_manager.set_value(
                    "ValidationSettings",
                    "fuzzy_matching_enabled",
                    str(self._fuzzy_enabled_checkbox.isChecked()),
                )

            if "fuzzy_threshold" in self._changed_settings["ValidationSettings"]:
                self._config_manager.set_value(
                    "ValidationSettings",
                    "fuzzy_threshold",
                    str(self._fuzzy_threshold_slider.value()),
                )

        # Emit signal to notify that settings have changed
        self.settings_changed.emit()

    def _mark_setting_changed(self, section, key):
        """
        Mark a setting as changed and handle auto-save functionality.

        Args:
            section (str): Configuration section
            key (str): Configuration key
        """
        if section not in self._changed_settings:
            self._changed_settings[section] = set()

        self._changed_settings[section].add(key)

        # Auto-save if enabled
        if self._auto_save_checkbox.isChecked():
            self._save_settings()
            self._reset_changed_settings()

    def _reset_changed_settings(self):
        """Reset the tracking of changed settings."""
        self._changed_settings = {}

    def _on_save_clicked(self):
        """Handle the save button click event."""
        self._save_settings()
        self._reset_changed_settings()
        self._show_message("Settings saved successfully.")

    def _on_reset_clicked(self):
        """Handle the reset button click event."""
        result = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result == QMessageBox.Yes:
            self._config_manager.reset_to_defaults()
            self._load_settings()
            self._show_message("Settings have been reset to defaults.")

    def _browse_directory(self, dir_type):
        """
        Open a directory browser dialog and update the corresponding text field.

        Args:
            dir_type (str): Type of directory to browse for (input, output, corrections, or validation)
        """
        if dir_type == "input":
            current_dir = self._input_dir_edit.text()
            title = "Select Input Directory"
        elif dir_type == "output":
            current_dir = self._output_dir_edit.text()
            title = "Select Output Directory"
        elif dir_type == "corrections":
            current_dir = self._corrections_dir_edit.text()
            title = "Select Corrections Directory"
        elif dir_type == "validation":
            current_dir = self._validation_dir_edit.text()
            title = "Select Validation Lists Directory"
        else:
            return

        directory = QFileDialog.getExistingDirectory(self, title, current_dir)

        if directory:
            if dir_type == "input":
                self._input_dir_edit.setText(directory)
                self._mark_setting_changed("Files", "default_input_dir")
            elif dir_type == "output":
                self._output_dir_edit.setText(directory)
                self._mark_setting_changed("Files", "default_output_dir")
            elif dir_type == "corrections":
                self._corrections_dir_edit.setText(directory)
                self._mark_setting_changed("Files", "default_corrections_dir")
            elif dir_type == "validation":
                self._validation_dir_edit.setText(directory)
                self._mark_setting_changed("Files", "default_validation_dir")

    def _on_fuzzy_enabled_changed(self, state):
        """
        Handle changes to the fuzzy matching enabled checkbox.

        Args:
            state (int): Checkbox state
        """
        enabled = state == Qt.Checked.value
        self._fuzzy_threshold_slider.setEnabled(enabled)
        self._mark_setting_changed("ValidationSettings", "fuzzy_matching_enabled")

    def _on_fuzzy_threshold_changed(self, value):
        """
        Handle changes to the fuzzy matching threshold slider.

        Args:
            value (int): New threshold value
        """
        self._threshold_value_label.setText(f"{value}%")
        self._mark_setting_changed("ValidationSettings", "fuzzy_threshold")

    def _on_row_height_changed(self, value):
        """
        Handle changes to the row height slider.

        Args:
            value (int): New row height value
        """
        self._row_height_label.setText(f"{value}px")
        self._mark_setting_changed("UI", "table_row_height")

    def _on_font_size_changed(self, value):
        """
        Handle changes to the font size slider.

        Args:
            value (int): New font size value
        """
        self._font_size_label.setText(f"{value}pt")
        self._mark_setting_changed("UI", "font_size")

    def _show_message(self, message, title="Settings"):
        """
        Show an information message dialog.

        Args:
            message (str): Message to display
            title (str, optional): Dialog title. Defaults to "Settings".
        """
        QMessageBox.information(self, title, message)

    def closeEvent(self, event):
        """
        Handle the close event, prompting to save unsaved changes.

        Args:
            event (QCloseEvent): Close event
        """
        if self._changed_settings:
            result = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Would you like to save them before closing?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes,
            )

            if result == QMessageBox.Yes:
                self._save_settings()
                event.accept()
            elif result == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
