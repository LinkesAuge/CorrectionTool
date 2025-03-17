"""
settings_panel.py

Description: Panel for application settings
Usage:
    from src.ui.settings_panel import SettingsPanel
    settings_panel = SettingsPanel(parent=self)
"""

from pathlib import Path
from typing import Dict, Optional, Set

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QScrollArea,
    QSlider,
)

from src.services.config_manager import ConfigManager


class SettingsPanel(QWidget):
    """
    Panel for application settings.

    Provides a tabbed interface for configuring application settings.

    Attributes:
        settings_changed (Signal): Signal emitted when settings are changed

    Implementation Notes:
        - Uses QTabWidget for organization
        - Settings are loaded from and saved to ConfigManager
        - Settings are grouped by category
    """

    settings_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the settings panel.

        Args:
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)

        # Initialize attributes
        self._config = ConfigManager()
        self._modified_settings: Dict[str, Set[str]] = {}
        self._changed_settings: Dict[str, Set[str]] = {}

        # Initialize UI
        self._setup_ui()

        # Load settings
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab widget
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Set up tabs
        self._setup_general_tab()
        self._setup_file_paths_tab()
        self._setup_validation_tab()
        self._setup_ui_settings()

        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(10, 10, 10, 10)

        # Save button
        self._save_button = QPushButton("Save Settings")
        self._save_button.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self._save_button)

        # Reset button
        self._reset_button = QPushButton("Reset to Defaults")
        self._reset_button.clicked.connect(self._on_reset_clicked)
        button_layout.addWidget(self._reset_button)

        # Add buttons to main layout
        layout.addWidget(button_container)

    def _setup_general_tab(self) -> None:
        """Set up general settings tab."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Application group
        app_group = QGroupBox("Application")
        app_layout = QFormLayout(app_group)

        # Auto-save settings
        self._auto_save_checkbox = QCheckBox("Auto-save settings on change")
        self._auto_save_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("App", "auto_save_settings")
        )
        app_layout.addRow("", self._auto_save_checkbox)

        # Theme selection
        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Light", "light")
        self._theme_combo.addItem("Dark", "dark")
        self._theme_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("UI", "theme")
        )
        app_layout.addRow("Theme:", self._theme_combo)

        # Remember window size
        self._remember_size_checkbox = QCheckBox("Remember window size and position")
        self._remember_size_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("UI", "remember_window_size")
        )
        app_layout.addRow("", self._remember_size_checkbox)

        # Add to layout
        layout.addWidget(app_group)

        # Add stretch to push everything to the top
        layout.addStretch()

        # Add to tab widget
        self._tabs.addTab(container, "General")

    def _setup_file_paths_tab(self) -> None:
        """Set up file paths settings tab."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Default directories group
        dir_group = QGroupBox("Default Directories")
        dir_layout = QFormLayout(dir_group)

        # Input directory
        input_dir_layout = QHBoxLayout()
        self._input_dir_edit = QLineEdit()
        self._input_dir_edit.textChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_input_dir")
        )
        input_dir_layout.addWidget(self._input_dir_edit)

        input_dir_button = QPushButton("Browse...")
        input_dir_button.clicked.connect(lambda: self._browse_directory("input"))
        input_dir_layout.addWidget(input_dir_button)

        dir_layout.addRow("Input Directory:", input_dir_layout)

        # Output directory
        output_dir_layout = QHBoxLayout()
        self._output_dir_edit = QLineEdit()
        self._output_dir_edit.textChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_output_dir")
        )
        output_dir_layout.addWidget(self._output_dir_edit)

        output_dir_button = QPushButton("Browse...")
        output_dir_button.clicked.connect(lambda: self._browse_directory("output"))
        output_dir_layout.addWidget(output_dir_button)

        dir_layout.addRow("Output Directory:", output_dir_layout)

        # Corrections directory
        corrections_dir_layout = QHBoxLayout()
        self._corrections_dir_edit = QLineEdit()
        self._corrections_dir_edit.textChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_corrections_dir")
        )
        corrections_dir_layout.addWidget(self._corrections_dir_edit)

        corrections_dir_button = QPushButton("Browse...")
        corrections_dir_button.clicked.connect(lambda: self._browse_directory("corrections"))
        corrections_dir_layout.addWidget(corrections_dir_button)

        dir_layout.addRow("Corrections Directory:", corrections_dir_layout)

        # Validation directory
        validation_dir_layout = QHBoxLayout()
        self._validation_dir_edit = QLineEdit()
        self._validation_dir_edit.textChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_validation_dir")
        )
        validation_dir_layout.addWidget(self._validation_dir_edit)

        validation_dir_button = QPushButton("Browse...")
        validation_dir_button.clicked.connect(lambda: self._browse_directory("validation"))
        validation_dir_layout.addWidget(validation_dir_button)

        dir_layout.addRow("Validation Lists Directory:", validation_dir_layout)

        # Add to layout
        layout.addWidget(dir_group)

        # File extension group
        ext_group = QGroupBox("Default File Extensions")
        ext_layout = QFormLayout(ext_group)

        # Input file extension
        self._input_ext_combo = QComboBox()
        self._input_ext_combo.addItem("CSV (.csv)", "csv")
        self._input_ext_combo.addItem("Text (.txt)", "txt")
        self._input_ext_combo.addItem("JSON (.json)", "json")
        self._input_ext_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_input_extension")
        )
        ext_layout.addRow("Input Files:", self._input_ext_combo)

        # Correction file extension
        self._correction_ext_combo = QComboBox()
        self._correction_ext_combo.addItem("CSV (.csv)", "csv")
        self._correction_ext_combo.addItem("Text (.txt)", "txt")
        self._correction_ext_combo.addItem("JSON (.json)", "json")
        self._correction_ext_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_correction_extension")
        )
        ext_layout.addRow("Correction Files:", self._correction_ext_combo)

        # Add to layout
        layout.addWidget(ext_group)

        # Add stretch to push everything to the top
        layout.addStretch()

        # Add to tab widget
        self._tabs.addTab(container, "File Paths")

    def _setup_validation_tab(self) -> None:
        """Set up validation settings tab."""
        # Create a scroll area to ensure all settings are accessible
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Validation settings group
        validation_group = QGroupBox("Validation Settings")
        validation_layout = QFormLayout(validation_group)

        # Auto-validate
        self._auto_validate_checkbox = QCheckBox("Automatically validate on load")
        self._auto_validate_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("Validation", "auto_validate")
        )
        validation_layout.addRow("", self._auto_validate_checkbox)

        # Validation strictness
        self._validation_strictness_combo = QComboBox()
        self._validation_strictness_combo.addItem("Strict", "strict")
        self._validation_strictness_combo.addItem("Normal", "normal")
        self._validation_strictness_combo.addItem("Lenient", "lenient")
        self._validation_strictness_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("Validation", "strictness")
        )
        validation_layout.addRow("Strictness:", self._validation_strictness_combo)

        # Add to layout
        layout.addWidget(validation_group)

        # Validation lists group
        lists_group = QGroupBox("Validation Lists")
        lists_layout = QFormLayout(lists_group)

        # Player list
        self._use_player_list_checkbox = QCheckBox("Validate player names")
        self._use_player_list_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("Validation", "validate_players")
        )
        lists_layout.addRow("", self._use_player_list_checkbox)

        # Chest type list
        self._use_chest_list_checkbox = QCheckBox("Validate chest types")
        self._use_chest_list_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("Validation", "validate_chest_types")
        )
        lists_layout.addRow("", self._use_chest_list_checkbox)

        # Source list
        self._use_source_list_checkbox = QCheckBox("Validate sources")
        self._use_source_list_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("Validation", "validate_sources")
        )
        lists_layout.addRow("", self._use_source_list_checkbox)

        # Add to layout
        layout.addWidget(lists_group)

        # Fuzzy matching group
        fuzzy_group = QGroupBox("Fuzzy Matching")
        fuzzy_layout = QFormLayout(fuzzy_group)

        # Enable fuzzy matching
        self._enable_fuzzy_checkbox = QCheckBox("Enable fuzzy matching")
        self._enable_fuzzy_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("Validation", "enable_fuzzy_matching")
        )
        fuzzy_layout.addRow("", self._enable_fuzzy_checkbox)

        # Fuzzy threshold
        self._fuzzy_threshold_slider = QSlider(Qt.Horizontal)
        self._fuzzy_threshold_slider.setMinimum(50)
        self._fuzzy_threshold_slider.setMaximum(100)
        self._fuzzy_threshold_slider.setValue(75)
        self._fuzzy_threshold_slider.setTickInterval(5)
        self._fuzzy_threshold_slider.setTickPosition(QSlider.TicksBelow)
        self._fuzzy_threshold_slider.valueChanged.connect(
            lambda: self._mark_setting_changed("Validation", "fuzzy_threshold")
        )

        # Threshold label
        self._fuzzy_threshold_label = QLabel("75%")
        self._fuzzy_threshold_slider.valueChanged.connect(
            lambda value: self._fuzzy_threshold_label.setText(f"{value}%")
        )

        # Threshold layout
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(self._fuzzy_threshold_slider)
        threshold_layout.addWidget(self._fuzzy_threshold_label)

        fuzzy_layout.addRow("Match Threshold:", threshold_layout)

        # Add to layout
        layout.addWidget(fuzzy_group)

        # Add stretch to push everything to the top
        layout.addStretch()

        # Set container as scroll area widget
        scroll_area.setWidget(container)

        # Add to tab widget
        self._tabs.addTab(scroll_area, "Validation")

    def _setup_ui_settings(self) -> None:
        """Set up UI settings tab."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)

        # Dark mode
        self._dark_mode_checkbox = QCheckBox("Use dark mode")
        self._dark_mode_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("UI", "dark_mode")
        )
        theme_layout.addRow("", self._dark_mode_checkbox)

        # Accent color
        self._accent_color_combo = QComboBox()
        self._accent_color_combo.addItem("Blue", "blue")
        self._accent_color_combo.addItem("Green", "green")
        self._accent_color_combo.addItem("Purple", "purple")
        self._accent_color_combo.addItem("Orange", "orange")
        self._accent_color_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("UI", "accent_color")
        )
        theme_layout.addRow("Accent Color:", self._accent_color_combo)

        layout.addWidget(theme_group)

        # Table group
        table_group = QGroupBox("Table Settings")
        table_layout = QFormLayout(table_group)

        # Show IDs
        self._show_ids_checkbox = QCheckBox("Show entry IDs")
        self._show_ids_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("Table", "show_ids")
        )
        table_layout.addRow("", self._show_ids_checkbox)

        # Font size
        self._font_size_combo = QComboBox()
        for size in range(8, 17):
            self._font_size_combo.addItem(f"{size}pt", size)
        self._font_size_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("Table", "font_size")
        )
        table_layout.addRow("Font Size:", self._font_size_combo)

        # Row height
        self._row_height_slider = QSlider(Qt.Horizontal)
        self._row_height_slider.setMinimum(20)
        self._row_height_slider.setMaximum(50)
        self._row_height_slider.setTickInterval(5)
        self._row_height_slider.setTickPosition(QSlider.TicksBelow)
        self._row_height_slider.valueChanged.connect(
            lambda: self._mark_setting_changed("Table", "row_height")
        )
        self._row_height_label = QLabel("30px")
        self._row_height_slider.valueChanged.connect(
            lambda value: self._row_height_label.setText(f"{value}px")
        )

        row_height_layout = QHBoxLayout()
        row_height_layout.addWidget(self._row_height_slider)
        row_height_layout.addWidget(self._row_height_label)

        table_layout.addRow("Row Height:", row_height_layout)

        layout.addWidget(table_group)

        # Layout group
        layout_group = QGroupBox("Layout")
        layout_group_layout = QFormLayout(layout_group)

        # Dashboard left panel ratio
        self._left_panel_slider = QSlider(Qt.Horizontal)
        self._left_panel_slider.setMinimum(10)
        self._left_panel_slider.setMaximum(90)
        self._left_panel_slider.setTickInterval(10)
        self._left_panel_slider.setTickPosition(QSlider.TicksBelow)
        self._left_panel_slider.valueChanged.connect(
            lambda: self._mark_setting_changed("Layout", "left_panel_ratio")
        )
        self._left_panel_label = QLabel("30%")
        self._left_panel_slider.valueChanged.connect(
            lambda value: self._left_panel_label.setText(f"{value}%")
        )

        left_panel_layout = QHBoxLayout()
        left_panel_layout.addWidget(self._left_panel_slider)
        left_panel_layout.addWidget(self._left_panel_label)

        layout_group_layout.addRow("Dashboard Left Panel Width:", left_panel_layout)

        layout.addWidget(layout_group)

        # Add to tab
        self._tabs.addTab(container, "UI Settings")

    def _browse_directory(self, dir_type: str) -> None:
        """
        Open a directory browser dialog.

        Args:
            dir_type (str): Type of directory to browse for
        """
        # Get current directory
        current_dir = ""
        if dir_type == "input":
            current_dir = self._input_dir_edit.text()
        elif dir_type == "output":
            current_dir = self._output_dir_edit.text()
        elif dir_type == "corrections":
            current_dir = self._corrections_dir_edit.text()
        elif dir_type == "validation":
            current_dir = self._validation_dir_edit.text()

        # Default to home directory if empty
        if not current_dir:
            current_dir = str(Path.home())

        # Open dialog
        dir_path = QFileDialog.getExistingDirectory(
            self, f"Select {dir_type.title()} Directory", current_dir
        )

        # Update text field if directory was selected
        if dir_path:
            if dir_type == "input":
                self._input_dir_edit.setText(dir_path)
            elif dir_type == "output":
                self._output_dir_edit.setText(dir_path)
            elif dir_type == "corrections":
                self._corrections_dir_edit.setText(dir_path)
            elif dir_type == "validation":
                self._validation_dir_edit.setText(dir_path)

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        self._save_settings()
        self.settings_changed.emit("settings")

    def _on_reset_clicked(self) -> None:
        """Handle reset button click."""
        # Reset to defaults
        self._config.reset_to_defaults()

        # Reload settings
        self._load_settings()

        # Emit settings changed signal
        self.settings_changed.emit("settings")

    def _load_settings(self) -> None:
        """Load settings from config."""
        # Load application settings
        auto_save = self._config.get_bool("App", "auto_save_settings", fallback=True)
        self._auto_save_checkbox.setChecked(auto_save)

        theme = self._config.get("UI", "theme", fallback="dark")
        theme_index = self._theme_combo.findData(theme)
        if theme_index >= 0:
            self._theme_combo.setCurrentIndex(theme_index)

        remember_size = self._config.get_bool("UI", "remember_window_size", fallback=True)
        self._remember_size_checkbox.setChecked(remember_size)

        # Load file paths
        input_dir = self._config.get("Files", "default_input_dir", fallback="")
        self._input_dir_edit.setText(input_dir)

        output_dir = self._config.get("Files", "default_output_dir", fallback="")
        self._output_dir_edit.setText(output_dir)

        corrections_dir = self._config.get("Files", "default_corrections_dir", fallback="")
        self._corrections_dir_edit.setText(corrections_dir)

        validation_dir = self._config.get("Files", "default_validation_dir", fallback="")
        self._validation_dir_edit.setText(validation_dir)

        input_ext = self._config.get("Files", "default_input_extension", fallback="csv")
        input_ext_index = self._input_ext_combo.findData(input_ext)
        if input_ext_index >= 0:
            self._input_ext_combo.setCurrentIndex(input_ext_index)

        correction_ext = self._config.get("Files", "default_correction_extension", fallback="csv")
        correction_ext_index = self._correction_ext_combo.findData(correction_ext)
        if correction_ext_index >= 0:
            self._correction_ext_combo.setCurrentIndex(correction_ext_index)

        # Load validation settings
        auto_validate = self._config.get_bool("Validation", "auto_validate", fallback=True)
        self._auto_validate_checkbox.setChecked(auto_validate)

        strictness = self._config.get("Validation", "strictness", fallback="normal")
        strictness_index = self._validation_strictness_combo.findData(strictness)
        if strictness_index >= 0:
            self._validation_strictness_combo.setCurrentIndex(strictness_index)

        validate_players = self._config.get_bool("Validation", "validate_players", fallback=True)
        self._use_player_list_checkbox.setChecked(validate_players)

        validate_chest_types = self._config.get_bool(
            "Validation", "validate_chest_types", fallback=True
        )
        self._use_chest_list_checkbox.setChecked(validate_chest_types)

        validate_sources = self._config.get_bool("Validation", "validate_sources", fallback=True)
        self._use_source_list_checkbox.setChecked(validate_sources)

        # Load fuzzy matching settings
        enable_fuzzy = self._config.get_bool("Validation", "enable_fuzzy_matching", fallback=False)
        self._enable_fuzzy_checkbox.setChecked(enable_fuzzy)

        fuzzy_threshold = self._config.get_int("Validation", "fuzzy_threshold", fallback=75)
        self._fuzzy_threshold_slider.setValue(fuzzy_threshold)
        self._fuzzy_threshold_label.setText(f"{fuzzy_threshold}%")

        # Load UI settings
        dark_mode = self._config.get_bool("UI", "dark_mode", fallback=True)
        self._dark_mode_checkbox.setChecked(dark_mode)

        accent_color = self._config.get("UI", "accent_color", fallback="blue")
        accent_color_index = self._accent_color_combo.findData(accent_color)
        if accent_color_index >= 0:
            self._accent_color_combo.setCurrentIndex(accent_color_index)

        # Load table settings
        show_ids = self._config.get_bool("Table", "show_ids", fallback=True)
        self._show_ids_checkbox.setChecked(show_ids)

        font_size = self._config.get_int("Table", "font_size", fallback=10)
        font_size_index = self._font_size_combo.findData(font_size)
        if font_size_index >= 0:
            self._font_size_combo.setCurrentIndex(font_size_index)

        row_height = self._config.get_int("Table", "row_height", fallback=30)
        self._row_height_slider.setValue(row_height)
        self._row_height_label.setText(f"{row_height}px")

        # Load layout settings
        left_panel_ratio = self._config.get_int("Layout", "left_panel_ratio", fallback=30)
        self._left_panel_slider.setValue(left_panel_ratio)
        self._left_panel_label.setText(f"{left_panel_ratio}%")

        # Reset changed flags
        self._reset_changed_settings()

    def _save_settings(self) -> None:
        """Save settings to config."""
        # Only save if there are changes
        if not self._changed_settings:
            return

        # Save application settings
        auto_save = self._auto_save_checkbox.isChecked()
        self._config.set("App", "auto_save_settings", auto_save)

        theme = self._theme_combo.currentData()
        self._config.set("UI", "theme", theme)

        remember_size = self._remember_size_checkbox.isChecked()
        self._config.set("UI", "remember_window_size", remember_size)

        # Save file paths
        input_dir = self._input_dir_edit.text()
        self._config.set("Files", "default_input_dir", input_dir)

        output_dir = self._output_dir_edit.text()
        self._config.set("Files", "default_output_dir", output_dir)

        corrections_dir = self._corrections_dir_edit.text()
        self._config.set("Files", "default_corrections_dir", corrections_dir)

        validation_dir = self._validation_dir_edit.text()
        self._config.set("Files", "default_validation_dir", validation_dir)

        input_ext = self._input_ext_combo.currentData()
        self._config.set("Files", "default_input_extension", input_ext)

        correction_ext = self._correction_ext_combo.currentData()
        self._config.set("Files", "default_correction_extension", correction_ext)

        # Save validation settings
        auto_validate = self._auto_validate_checkbox.isChecked()
        self._config.set("Validation", "auto_validate", auto_validate)

        strictness = self._validation_strictness_combo.currentData()
        self._config.set("Validation", "strictness", strictness)

        validate_players = self._use_player_list_checkbox.isChecked()
        self._config.set("Validation", "validate_players", validate_players)

        validate_chest_types = self._use_chest_list_checkbox.isChecked()
        self._config.set("Validation", "validate_chest_types", validate_chest_types)

        validate_sources = self._use_source_list_checkbox.isChecked()
        self._config.set("Validation", "validate_sources", validate_sources)

        # Save fuzzy matching settings
        enable_fuzzy = self._enable_fuzzy_checkbox.isChecked()
        self._config.set("Validation", "enable_fuzzy_matching", enable_fuzzy)

        fuzzy_threshold = self._fuzzy_threshold_slider.value()
        self._config.set("Validation", "fuzzy_threshold", fuzzy_threshold)

        # Emit signal to notify that fuzzy settings have changed
        self.settings_changed.emit("fuzzy_settings")

        # Save UI settings
        dark_mode = self._dark_mode_checkbox.isChecked()
        self._config.set("UI", "dark_mode", dark_mode)

        accent_color = self._accent_color_combo.currentData()
        self._config.set("UI", "accent_color", accent_color)

        # Save table settings
        show_ids = self._show_ids_checkbox.isChecked()
        self._config.set("Table", "show_ids", show_ids)

        font_size = self._font_size_combo.currentData()
        self._config.set("Table", "font_size", font_size)

        row_height = self._row_height_slider.value()
        self._config.set("Table", "row_height", row_height)

        # Save layout settings
        left_panel_ratio = self._left_panel_slider.value()
        self._config.set("Layout", "left_panel_ratio", left_panel_ratio)

        # Save to file
        self._config.save()

        # Reset changed flags
        self._reset_changed_settings()

        # Emit settings changed signal
        self.settings_changed.emit("settings")

    def _reset_changed_settings(self) -> None:
        """Reset the changed settings tracking."""
        self._changed_settings = {}

    def _mark_setting_changed(self, section: str, key: str) -> None:
        """
        Mark a setting as changed.

        Args:
            section (str): Settings section
            key (str): Setting key
        """
        if section not in self._changed_settings:
            self._changed_settings[section] = set()

        self._changed_settings[section].add(key)

        # No need to enable apply button as settings are applied immediately
