"""
settings_panel.py

Description: Panel for application settings
Usage:
    from src.ui.settings_panel import SettingsPanel
    settings_panel = SettingsPanel(parent=self)
"""

from pathlib import Path
from typing import Dict, Optional, List

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QTabWidget,
    QScrollArea
)

from src.services.config_manager import ConfigManager
from src.ui.styles import ThemeColors


class SettingsPanel(QWidget):
    """
    Panel for application settings.
    
    Provides controls for configuring application preferences.
    
    Attributes:
        settings_changed (Signal): Signal emitted when settings are changed
        
    Implementation Notes:
        - Divided into sections for different setting categories
        - Uses QTabWidget for organization
        - Connects directly to ConfigManager
    """
    
    settings_changed = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the settings panel.
        
        Args:
            parent (Optional[QWidget]): Parent widget
        """
        super().__init__(parent)
        
        # Initialize data
        self._config = ConfigManager()
        self._theme_colors = ThemeColors()
        self._modified_settings = {}
        
        # Setup UI
        self._setup_ui()
        
        # Load settings
        self._load_settings()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(10, 10, 10, 10)
        self._main_layout.setSpacing(10)
        
        # Create tab widget for settings categories
        self._tab_widget = QTabWidget()
        
        # General settings tab
        self._general_tab = QWidget()
        self._setup_general_tab()
        self._tab_widget.addTab(self._general_tab, "General")
        
        # File paths tab
        self._file_paths_tab = QWidget()
        self._setup_file_paths_tab()
        self._tab_widget.addTab(self._file_paths_tab, "File Paths")
        
        # Validation tab
        self._validation_tab = QWidget()
        self._setup_validation_tab()
        self._tab_widget.addTab(self._validation_tab, "Validation")
        
        # UI tab
        self._ui_tab = QWidget()
        self._setup_ui_tab()
        self._tab_widget.addTab(self._ui_tab, "User Interface")
        
        # Add tab widget to main layout
        self._main_layout.addWidget(self._tab_widget)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Save button
        self._save_button = QPushButton("Save Settings")
        self._save_button.clicked.connect(self._save_settings)
        buttons_layout.addWidget(self._save_button)
        
        # Reset button
        self._reset_button = QPushButton("Reset to Defaults")
        self._reset_button.clicked.connect(self._reset_to_defaults)
        buttons_layout.addWidget(self._reset_button)
        
        # Add buttons layout to main layout
        self._main_layout.addLayout(buttons_layout)
    
    def _setup_general_tab(self) -> None:
        """Set up the general settings tab."""
        layout = QVBoxLayout(self._general_tab)
        
        # Application settings group
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)
        
        # Theme selection
        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Dark Theme", "dark")
        self._theme_combo.addItem("Light Theme", "light")
        self._theme_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("UI", "theme")
        )
        app_layout.addRow("Theme:", self._theme_combo)
        
        # Language selection (for future)
        self._language_combo = QComboBox()
        self._language_combo.addItem("English", "en")
        self._language_combo.addItem("German", "de")
        self._language_combo.setEnabled(False)  # Disabled for now
        app_layout.addRow("Language (Coming Soon):", self._language_combo)
        
        # Add to layout
        layout.addWidget(app_group)
        
        # Behavior settings group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QFormLayout(behavior_group)
        
        # Auto-save settings
        self._auto_save_checkbox = QCheckBox("Auto-save settings on exit")
        self._auto_save_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("App", "auto_save_settings")
        )
        behavior_layout.addRow("", self._auto_save_checkbox)
        
        # Remember window size
        self._remember_size_checkbox = QCheckBox("Remember window size and position")
        self._remember_size_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("UI", "remember_window_size")
        )
        behavior_layout.addRow("", self._remember_size_checkbox)
        
        # Add to layout
        layout.addWidget(behavior_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def _setup_file_paths_tab(self) -> None:
        """Set up the file paths tab."""
        layout = QVBoxLayout(self._file_paths_tab)
        
        # Default directories group
        dirs_group = QGroupBox("Default Directories")
        dirs_layout = QFormLayout(dirs_group)
        
        # Input directory
        input_layout = QHBoxLayout()
        self._input_dir_edit = QLineEdit()
        self._input_dir_edit.setReadOnly(True)
        self._input_dir_edit.textChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_input_dir")
        )
        input_layout.addWidget(self._input_dir_edit)
        
        input_browse_button = QPushButton("Browse...")
        input_browse_button.clicked.connect(lambda: self._browse_directory("input"))
        input_layout.addWidget(input_browse_button)
        
        dirs_layout.addRow("Input Files:", input_layout)
        
        # Output directory
        output_layout = QHBoxLayout()
        self._output_dir_edit = QLineEdit()
        self._output_dir_edit.setReadOnly(True)
        self._output_dir_edit.textChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_output_dir")
        )
        output_layout.addWidget(self._output_dir_edit)
        
        output_browse_button = QPushButton("Browse...")
        output_browse_button.clicked.connect(lambda: self._browse_directory("output"))
        output_layout.addWidget(output_browse_button)
        
        dirs_layout.addRow("Output Files:", output_layout)
        
        # Corrections directory
        corrections_layout = QHBoxLayout()
        self._corrections_dir_edit = QLineEdit()
        self._corrections_dir_edit.setReadOnly(True)
        self._corrections_dir_edit.textChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_corrections_dir")
        )
        corrections_layout.addWidget(self._corrections_dir_edit)
        
        corrections_browse_button = QPushButton("Browse...")
        corrections_browse_button.clicked.connect(lambda: self._browse_directory("corrections"))
        corrections_layout.addWidget(corrections_browse_button)
        
        dirs_layout.addRow("Correction Lists:", corrections_layout)
        
        # Validation lists directory
        validation_layout = QHBoxLayout()
        self._validation_dir_edit = QLineEdit()
        self._validation_dir_edit.setReadOnly(True)
        self._validation_dir_edit.textChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_validation_dir")
        )
        validation_layout.addWidget(self._validation_dir_edit)
        
        validation_browse_button = QPushButton("Browse...")
        validation_browse_button.clicked.connect(lambda: self._browse_directory("validation"))
        validation_layout.addWidget(validation_browse_button)
        
        dirs_layout.addRow("Validation Lists:", validation_layout)
        
        # Add to layout
        layout.addWidget(dirs_group)
        
        # File options group
        file_options_group = QGroupBox("File Options")
        file_options_layout = QFormLayout(file_options_group)
        
        # Default input file extension
        self._input_ext_combo = QComboBox()
        self._input_ext_combo.addItem(".txt", "txt")
        self._input_ext_combo.addItem(".csv", "csv")
        self._input_ext_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_input_extension")
        )
        file_options_layout.addRow("Default Input Extension:", self._input_ext_combo)
        
        # Default correction file extension
        self._correction_ext_combo = QComboBox()
        self._correction_ext_combo.addItem(".csv", "csv")
        self._correction_ext_combo.addItem(".txt", "txt")
        self._correction_ext_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("Files", "default_correction_extension")
        )
        file_options_layout.addRow("Default Correction Extension:", self._correction_ext_combo)
        
        # Add to layout
        layout.addWidget(file_options_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def _setup_validation_tab(self) -> None:
        """Set up the validation tab."""
        layout = QVBoxLayout(self._validation_tab)
        
        # Validation behavior group
        validation_group = QGroupBox("Validation Behavior")
        validation_layout = QFormLayout(validation_group)
        
        # Auto-validate checkbox
        self._auto_validate_checkbox = QCheckBox("Automatically validate on load")
        self._auto_validate_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("Validation", "auto_validate")
        )
        validation_layout.addRow("", self._auto_validate_checkbox)
        
        # Validation strictness
        self._validation_strictness_combo = QComboBox()
        self._validation_strictness_combo.addItem("Strict (Exact match)", "strict")
        self._validation_strictness_combo.addItem("Moderate (Case insensitive)", "moderate")
        self._validation_strictness_combo.addItem("Relaxed (Fuzzy match)", "relaxed")
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
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def _setup_ui_tab(self) -> None:
        """Set up the UI tab."""
        layout = QVBoxLayout(self._ui_tab)
        
        # Table view group
        table_group = QGroupBox("Table View")
        table_layout = QFormLayout(table_group)
        
        # Row height
        self._row_height_combo = QComboBox()
        self._row_height_combo.addItem("Compact", "compact")
        self._row_height_combo.addItem("Normal", "normal")
        self._row_height_combo.addItem("Relaxed", "relaxed")
        self._row_height_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("UI", "table_row_height")
        )
        table_layout.addRow("Row Height:", self._row_height_combo)
        
        # Font size
        self._font_size_combo = QComboBox()
        self._font_size_combo.addItem("Small", "small")
        self._font_size_combo.addItem("Medium", "medium")
        self._font_size_combo.addItem("Large", "large")
        self._font_size_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("UI", "font_size")
        )
        table_layout.addRow("Font Size:", self._font_size_combo)
        
        # Alternating row colors
        self._alt_row_colors_checkbox = QCheckBox("Use alternating row colors")
        self._alt_row_colors_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("UI", "use_alt_row_colors")
        )
        table_layout.addRow("", self._alt_row_colors_checkbox)
        
        # Add to layout
        layout.addWidget(table_group)
        
        # Preview group
        preview_group = QGroupBox("Preview Panel")
        preview_layout = QFormLayout(preview_group)
        
        # Show preview by default
        self._show_preview_checkbox = QCheckBox("Show preview panel by default")
        self._show_preview_checkbox.stateChanged.connect(
            lambda: self._mark_setting_changed("UI", "show_preview")
        )
        preview_layout.addRow("", self._show_preview_checkbox)
        
        # Preview panel size
        self._preview_size_combo = QComboBox()
        self._preview_size_combo.addItem("Small (25%)", "small")
        self._preview_size_combo.addItem("Medium (50%)", "medium")
        self._preview_size_combo.addItem("Large (75%)", "large")
        self._preview_size_combo.currentIndexChanged.connect(
            lambda: self._mark_setting_changed("UI", "preview_panel_size")
        )
        preview_layout.addRow("Default Size:", self._preview_size_combo)
        
        # Add to layout
        layout.addWidget(preview_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def _browse_directory(self, dir_type: str) -> None:
        """
        Open a directory browser dialog.
        
        Args:
            dir_type (str): Type of directory to browse for
        """
        # Get the current directory as a starting point
        if dir_type == "input":
            current_dir = self._input_dir_edit.text()
        elif dir_type == "output":
            current_dir = self._output_dir_edit.text()
        elif dir_type == "corrections":
            current_dir = self._corrections_dir_edit.text()
        elif dir_type == "validation":
            current_dir = self._validation_dir_edit.text()
        else:
            current_dir = ""
        
        # Open directory dialog
        directory = QFileDialog.getExistingDirectory(
            self, f"Select {dir_type.capitalize()} Directory", current_dir
        )
        
        if not directory:
            return
        
        # Update the appropriate field
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
    
    def _load_settings(self) -> None:
        """Load settings from the configuration."""
        # General tab
        theme = self._config.get("UI", "theme", fallback="dark")
        theme_index = self._theme_combo.findData(theme)
        if theme_index >= 0:
            self._theme_combo.setCurrentIndex(theme_index)
        
        auto_save = self._config.get_bool("App", "auto_save_settings", fallback=True)
        self._auto_save_checkbox.setChecked(auto_save)
        
        remember_size = self._config.get_bool("UI", "remember_window_size", fallback=True)
        self._remember_size_checkbox.setChecked(remember_size)
        
        # File paths tab
        input_dir = self._config.get("Files", "default_input_dir", fallback="data/input")
        self._input_dir_edit.setText(input_dir)
        
        output_dir = self._config.get("Files", "default_output_dir", fallback="data/output")
        self._output_dir_edit.setText(output_dir)
        
        corrections_dir = self._config.get("Files", "default_corrections_dir", fallback="data/corrections")
        self._corrections_dir_edit.setText(corrections_dir)
        
        validation_dir = self._config.get("Files", "default_validation_dir", fallback="data/validation")
        self._validation_dir_edit.setText(validation_dir)
        
        input_ext = self._config.get("Files", "default_input_extension", fallback="txt")
        input_ext_index = self._input_ext_combo.findData(input_ext)
        if input_ext_index >= 0:
            self._input_ext_combo.setCurrentIndex(input_ext_index)
        
        correction_ext = self._config.get("Files", "default_correction_extension", fallback="csv")
        correction_ext_index = self._correction_ext_combo.findData(correction_ext)
        if correction_ext_index >= 0:
            self._correction_ext_combo.setCurrentIndex(correction_ext_index)
        
        # Validation tab
        auto_validate = self._config.get_bool("Validation", "auto_validate", fallback=True)
        self._auto_validate_checkbox.setChecked(auto_validate)
        
        strictness = self._config.get("Validation", "strictness", fallback="strict")
        strictness_index = self._validation_strictness_combo.findData(strictness)
        if strictness_index >= 0:
            self._validation_strictness_combo.setCurrentIndex(strictness_index)
        
        validate_players = self._config.get_bool("Validation", "validate_players", fallback=True)
        self._use_player_list_checkbox.setChecked(validate_players)
        
        validate_chest_types = self._config.get_bool("Validation", "validate_chest_types", fallback=True)
        self._use_chest_list_checkbox.setChecked(validate_chest_types)
        
        validate_sources = self._config.get_bool("Validation", "validate_sources", fallback=True)
        self._use_source_list_checkbox.setChecked(validate_sources)
        
        # UI tab
        row_height = self._config.get("UI", "table_row_height", fallback="normal")
        row_height_index = self._row_height_combo.findData(row_height)
        if row_height_index >= 0:
            self._row_height_combo.setCurrentIndex(row_height_index)
        
        font_size = self._config.get("UI", "font_size", fallback="medium")
        font_size_index = self._font_size_combo.findData(font_size)
        if font_size_index >= 0:
            self._font_size_combo.setCurrentIndex(font_size_index)
        
        alt_row_colors = self._config.get_bool("UI", "use_alt_row_colors", fallback=True)
        self._alt_row_colors_checkbox.setChecked(alt_row_colors)
        
        show_preview = self._config.get_bool("UI", "show_preview", fallback=False)
        self._show_preview_checkbox.setChecked(show_preview)
        
        preview_size = self._config.get("UI", "preview_panel_size", fallback="medium")
        preview_size_index = self._preview_size_combo.findData(preview_size)
        if preview_size_index >= 0:
            self._preview_size_combo.setCurrentIndex(preview_size_index)
        
        # Clear modified settings after load
        self._modified_settings = {}
    
    def _mark_setting_changed(self, section: str, setting: str) -> None:
        """
        Mark a setting as modified.
        
        Args:
            section (str): Config section
            setting (str): Setting name
        """
        if section not in self._modified_settings:
            self._modified_settings[section] = set()
        
        self._modified_settings[section].add(setting)
    
    def _save_settings(self) -> None:
        """Save settings to the configuration."""
        # General tab
        theme = self._theme_combo.currentData()
        self._config.set("UI", "theme", theme)
        
        auto_save = self._auto_save_checkbox.isChecked()
        self._config.set("App", "auto_save_settings", auto_save)
        
        remember_size = self._remember_size_checkbox.isChecked()
        self._config.set("UI", "remember_window_size", remember_size)
        
        # File paths tab
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
        
        # Validation tab
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
        
        # UI tab
        row_height = self._row_height_combo.currentData()
        self._config.set("UI", "table_row_height", row_height)
        
        font_size = self._font_size_combo.currentData()
        self._config.set("UI", "font_size", font_size)
        
        alt_row_colors = self._alt_row_colors_checkbox.isChecked()
        self._config.set("UI", "use_alt_row_colors", alt_row_colors)
        
        show_preview = self._show_preview_checkbox.isChecked()
        self._config.set("UI", "show_preview", show_preview)
        
        preview_size = self._preview_size_combo.currentData()
        self._config.set("UI", "preview_panel_size", preview_size)
        
        # Save configuration
        self._config.save()
        
        # Emit signal about settings changed
        self.settings_changed.emit()
        
        # Clear modified settings
        self._modified_settings = {}
    
    def _reset_to_defaults(self) -> None:
        """Reset settings to defaults."""
        # Reset configuration
        self._config.reset_to_defaults()
        
        # Reload settings
        self._load_settings()
        
        # Emit signal about settings changed
        self.settings_changed.emit() 