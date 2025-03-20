"""
validation_panel_interface.py

Description: Interface-based validation panel that uses dependency injection
Usage:
    from src.ui.validation_panel_interface import ValidationPanelInterface
    panel = ValidationPanelInterface(service_factory)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, cast

from PySide6.QtCore import QSize, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QSlider,
)

# Import interfaces
from src.interfaces import (
    IServiceFactory,
    IDataStore,
    IFileService,
    IValidationService,
    IConfigManager,
)
from src.interfaces.events import EventType, EventHandler, EventData


class ValidationPanelInterface(QWidget):
    """
    Interface-based validation panel that uses dependency injection.

    Provides UI for creating, editing, and saving validation lists for
    chest types, players, and sources.

    Signals:
        validation_lists_updated: Signal emitted when validation lists are updated
        validation_errors_updated: Signal emitted when validation errors are updated

    Attributes:
        _service_factory: IServiceFactory instance for accessing services
        _data_store: IDataStore instance for data access
        _file_service: IFileService instance for file operations
        _validation_service: IValidationService instance for validation operations
        _config_manager: IConfigManager instance for configuration management
    """

    # Signals
    validation_lists_updated = Signal(dict)  # Dict of validation lists
    validation_errors_updated = Signal(list)  # List of entries with validation errors

    def __init__(self, service_factory: IServiceFactory, parent=None):
        """
        Initialize the validation panel interface with dependency injection.

        Args:
            service_factory: IServiceFactory instance for accessing services
            parent: Parent widget
        """
        super().__init__(parent)

        # Store the service factory
        self._service_factory = service_factory

        # Get services from factory
        self._data_store = cast(IDataStore, self._service_factory.get_service(IDataStore))
        self._file_service = cast(IFileService, self._service_factory.get_service(IFileService))
        self._validation_service = cast(
            IValidationService, self._service_factory.get_service(IValidationService)
        )
        self._config_manager = cast(
            IConfigManager, self._service_factory.get_service(IConfigManager)
        )

        # Initialize logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("Initializing ValidationPanelInterface")

        # Initialize state variables
        self._processing_signal = False
        self._emitting_signal = False
        self._connected_events = set()  # Track connected events

        # Setup UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

        # Load any existing validation lists from config
        self._load_validation_lists_from_config()

        # Apply fuzzy matching settings
        self._apply_fuzzy_settings()

        self._logger.info("ValidationPanelInterface initialized")

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Add header with reduced size
        header_layout = QHBoxLayout()
        header_label = QLabel("Validation Lists")
        header_label.setObjectName("title")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Create tab widget
        self._tab_widget = QTabWidget()

        # Create tabs for each validation list type
        self._setup_player_tab()
        self._setup_chest_type_tab()
        self._setup_source_tab()

        # Add tab widget to layout
        main_layout.addWidget(self._tab_widget)

        # Add fuzzy matching controls
        self._setup_fuzzy_controls(main_layout)

    def _setup_player_tab(self):
        """Set up the player validation tab."""
        self._setup_validation_tab("player", "Player Validation")

    def _setup_chest_type_tab(self):
        """Set up the chest type validation tab."""
        self._setup_validation_tab("chest_type", "Chest Type Validation")

    def _setup_source_tab(self):
        """Set up the source validation tab."""
        self._setup_validation_tab("source", "Source Validation")

    def _setup_validation_tab(self, list_type: str, tab_title: str):
        """
        Set up a validation tab.

        Args:
            list_type: The validation list type
            tab_title: The tab title
        """
        # Create tab widget
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # List name group
        name_group = QGroupBox("List Name")
        name_layout = QHBoxLayout(name_group)

        name_edit = QLineEdit()
        name_edit.setObjectName(f"{list_type}_name_edit")

        # Get validation list name from config if available
        list_name = self._config_manager.get_value(
            "ValidationLists",
            f"{list_type}_list_name",
            fallback=f"Default {list_type.title()} List",
        )
        name_edit.setText(list_name)

        # Connect signal using lambda to pass list_type
        name_edit.textChanged.connect(lambda text: self._on_name_changed(list_type, text))

        # Store reference to name edit
        setattr(self, f"_{list_type}_name_edit", name_edit)

        name_layout.addWidget(name_edit)

        # Add to tab layout
        tab_layout.addWidget(name_group)

        # Create splitter for list and controls
        splitter = QSplitter(Qt.Horizontal)

        # Entries list
        list_widget = QListWidget()
        list_widget.setObjectName(f"{list_type}_list_widget")
        list_widget.setSelectionMode(QListWidget.ExtendedSelection)

        # Store reference to list widget
        setattr(self, f"_{list_type}_list_widget", list_widget)

        # Controls group
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)

        # Add entry group
        add_group = QGroupBox("Add Entry")
        add_layout = QVBoxLayout(add_group)

        # Entry input and add button
        entry_layout = QHBoxLayout()
        entry_edit = QLineEdit()
        entry_edit.setObjectName(f"{list_type}_entry_edit")
        entry_edit.setPlaceholderText("Enter new entry...")

        # Store reference to entry edit
        setattr(self, f"_{list_type}_entry_edit", entry_edit)

        add_button = QPushButton("Add")
        add_button.clicked.connect(lambda: self._add_entry(list_type))

        entry_layout.addWidget(entry_edit)
        entry_layout.addWidget(add_button)

        # Add to add group
        add_layout.addLayout(entry_layout)

        # Remove button
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(lambda: self._remove_selected_entries(list_type))

        # Clear button
        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(lambda: self._clear_entries(list_type))

        # Add to controls layout
        controls_layout.addWidget(add_group)
        controls_layout.addWidget(remove_button)
        controls_layout.addWidget(clear_button)

        # Import/Export group
        io_group = QGroupBox("Import/Export")
        io_layout = QVBoxLayout(io_group)

        # Import button
        import_button = QPushButton("Import from CSV...")
        import_button.clicked.connect(lambda: self._on_import_list(list_type))

        # Export button
        export_button = QPushButton("Export to CSV...")
        export_button.clicked.connect(lambda: self._export_list(list_type))

        # Add to IO layout
        io_layout.addWidget(import_button)
        io_layout.addWidget(export_button)

        # Add IO group to controls layout
        controls_layout.addWidget(io_group)

        # Spacer
        controls_layout.addStretch()

        # Add widgets to splitter
        splitter.addWidget(list_widget)
        splitter.addWidget(controls_widget)

        # Set initial splitter sizes
        splitter.setSizes([200, 100])

        # Add splitter to tab layout
        tab_layout.addWidget(splitter)

        # Add tab to tab widget
        self._tab_widget.addTab(tab, tab_title)

    def _connect_signals(self):
        """Connect signals between components."""
        # Subscribe to data store events
        self._data_store.subscribe(
            EventType.VALIDATION_LISTS_UPDATED, self._on_validation_lists_updated
        )
        self._data_store.subscribe(EventType.IMPORT_COMPLETED, self._on_entries_loaded)
        self._data_store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)

        # Add events to connected events set
        self._connected_events.add(EventType.VALIDATION_LISTS_UPDATED)
        self._connected_events.add(EventType.IMPORT_COMPLETED)
        self._connected_events.add(EventType.ENTRIES_UPDATED)

    def _on_validation_lists_updated(self, event_data: Dict[str, Any]):
        """
        Handle validation lists updated event.

        Args:
            event_data: Event data containing updated validation lists information
        """
        try:
            list_type = event_data.get("list_type", "")
            count = event_data.get("count", 0)

            if list_type:
                # Update the specific list widget
                validation_list = self._data_store.get_validation_list(list_type)
                if validation_list:
                    self._update_list_widget(list_type, validation_list)
                    self._logger.info(f"Updated {list_type} validation list with {count} entries")
            else:
                # Update all list widgets
                self._refresh_all_validation_lists()
                self._logger.info("Updated all validation lists")

        except Exception as e:
            self._logger.error(f"Error handling validation lists updated event: {e}")

    def _on_entries_loaded(self, event_data: Dict[str, Any]):
        """
        Handle entries loaded event.

        Args:
            event_data: Event data containing loaded entries information
        """
        try:
            # Analyze entries for potential validation list entries
            self._analyze_entries_for_validation_lists()
        except Exception as e:
            self._logger.error(f"Error handling entries loaded event: {e}")

    def _on_entries_updated(self, event_data: Dict[str, Any]):
        """
        Handle entries updated event.

        Args:
            event_data: Event data containing updated entries information
        """
        try:
            # Analyze entries for potential validation list entries
            self._analyze_entries_for_validation_lists()
        except Exception as e:
            self._logger.error(f"Error handling entries updated event: {e}")

    def _analyze_entries_for_validation_lists(self):
        """Analyze loaded entries for potential validation list entries."""
        # This method would extract unique values from entries for suggestion to validation lists
        # Implementation depends on how entries are structured in the data store
        pass

    def _on_name_changed(self, list_type: str, name: str):
        """
        Handle name changes.

        Args:
            list_type: The validation list type
            name: The new name
        """
        # Save the name to config
        self._config_manager.set_value("ValidationLists", f"{list_type}_list_name", name)

    def _add_entry(self, list_type: str):
        """
        Add a new entry to the validation list.

        Args:
            list_type: The validation list type
        """
        # Get entry from the line edit
        entry_edit = getattr(self, f"_{list_type}_entry_edit")
        entry = entry_edit.text().strip()

        if not entry:
            return

        try:
            # Get current validation list
            validation_list = self._data_store.get_validation_list(list_type)

            # Add the entry if it doesn't already exist
            if entry not in validation_list:
                # Start a transaction
                self._data_store.begin_transaction()

                # Add entry to the list
                validation_list.append(entry)

                # Update the list in the data store
                self._data_store.set_validation_list(list_type, validation_list)

                # Commit the transaction
                self._data_store.commit_transaction()

                # Update the UI
                self._update_list_widget(list_type, validation_list)

                # Clear the line edit
                entry_edit.clear()

                self._logger.info(f"Added entry '{entry}' to {list_type} validation list")
            else:
                QMessageBox.information(
                    self,
                    "Duplicate Entry",
                    f"The entry '{entry}' already exists in the {list_type} list.",
                    QMessageBox.Ok,
                )

        except Exception as e:
            self._logger.error(f"Error adding entry to {list_type} validation list: {e}")
            self._data_store.rollback_transaction()

            QMessageBox.warning(
                self,
                "Error Adding Entry",
                f"Failed to add entry to {list_type} list: {str(e)}",
                QMessageBox.Ok,
            )

    def _remove_selected_entries(self, list_type: str):
        """
        Remove selected entries from the validation list.

        Args:
            list_type: The validation list type
        """
        list_widget = getattr(self, f"_{list_type}_list_widget")
        selected_items = list_widget.selectedItems()

        if not selected_items:
            return

        try:
            # Get current validation list
            validation_list = self._data_store.get_validation_list(list_type)

            # Start a transaction
            self._data_store.begin_transaction()

            # Remove selected entries
            for item in selected_items:
                entry = item.text()
                if entry in validation_list:
                    validation_list.remove(entry)

            # Update the list in the data store
            self._data_store.set_validation_list(list_type, validation_list)

            # Commit the transaction
            self._data_store.commit_transaction()

            # Update the UI
            self._update_list_widget(list_type, validation_list)

            self._logger.info(
                f"Removed {len(selected_items)} entries from {list_type} validation list"
            )

        except Exception as e:
            self._logger.error(f"Error removing entries from {list_type} validation list: {e}")
            self._data_store.rollback_transaction()

            QMessageBox.warning(
                self,
                "Error Removing Entries",
                f"Failed to remove entries from {list_type} list: {str(e)}",
                QMessageBox.Ok,
            )

    def _clear_entries(self, list_type: str):
        """
        Clear all entries from the validation list.

        Args:
            list_type: The validation list type
        """
        result = QMessageBox.question(
            self,
            "Clear Entries",
            f"Are you sure you want to clear all entries from the {list_type} list?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        try:
            # Start a transaction
            self._data_store.begin_transaction()

            # Clear the list
            self._data_store.set_validation_list(list_type, [])

            # Commit the transaction
            self._data_store.commit_transaction()

            # Update the UI
            list_widget = getattr(self, f"_{list_type}_list_widget")
            list_widget.clear()

            self._logger.info(f"Cleared all entries from {list_type} validation list")

        except Exception as e:
            self._logger.error(f"Error clearing {list_type} validation list: {e}")
            self._data_store.rollback_transaction()

            QMessageBox.warning(
                self,
                "Error Clearing Entries",
                f"Failed to clear entries from {list_type} list: {str(e)}",
                QMessageBox.Ok,
            )

    def _on_import_list(self, list_type: str):
        """
        Import a validation list from a file.

        Args:
            list_type: The validation list type
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Import {list_type.title()} List",
            self._config_manager.get_path("input_dir", str(Path.home())),
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            # Remember the directory
            self._config_manager.set_path(
                "input_dir", str(Path(file_path).parent), create_if_missing=True
            )

            # Load the validation list
            self._file_service.load_validation_list(list_type, file_path)

            # Save the path to config
            self._config_manager.set_path(
                f"{list_type}_list_file", file_path, create_if_missing=True
            )

            self._logger.info(f"Imported {list_type} validation list from {file_path}")

            # The data store event handler will update the UI

        except Exception as e:
            self._logger.error(f"Error importing {list_type} validation list: {e}")

            QMessageBox.warning(
                self,
                "Import Error",
                f"Failed to import {list_type} list from {file_path}: {str(e)}",
                QMessageBox.Ok,
            )

    def _export_list(self, list_type: str):
        """
        Export a validation list to a file.

        Args:
            list_type: The validation list type
        """
        validation_list = self._data_store.get_validation_list(list_type)

        if not validation_list:
            QMessageBox.information(
                self,
                "Export Error",
                f"The {list_type} list is empty. Nothing to export.",
                QMessageBox.Ok,
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {list_type.title()} List",
            self._config_manager.get_path("output_dir", str(Path.home())),
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            # Remember the directory
            self._config_manager.set_path(
                "output_dir", str(Path(file_path).parent), create_if_missing=True
            )

            # Save the validation list
            self._file_service.save_validation_list(list_type, file_path)

            # Save the path to config
            self._config_manager.set_path(
                f"{list_type}_list_file", file_path, create_if_missing=True
            )

            self._logger.info(f"Exported {list_type} validation list to {file_path}")

            QMessageBox.information(
                self,
                "Export Successful",
                f"The {list_type} list has been exported to {file_path}.",
                QMessageBox.Ok,
            )

        except Exception as e:
            self._logger.error(f"Error exporting {list_type} validation list: {e}")

            QMessageBox.warning(
                self,
                "Export Error",
                f"Failed to export {list_type} list to {file_path}: {str(e)}",
                QMessageBox.Ok,
            )

    def _load_validation_lists_from_config(self):
        """Load validation lists from paths stored in config."""
        # This will load validation lists from config-defined paths
        for list_type in ["player", "chest_type", "source"]:
            file_path = self._config_manager.get_path(f"{list_type}_list_file")
            if file_path and Path(file_path).exists():
                try:
                    self._logger.info(f"Loading {list_type} validation list from {file_path}")
                    self._file_service.load_validation_list(list_type, file_path)
                except Exception as e:
                    self._logger.error(f"Error loading {list_type} validation list: {e}")

    def _setup_fuzzy_controls(self, layout: QVBoxLayout):
        """
        Set up fuzzy matching controls.

        Args:
            layout: Layout to add controls to
        """
        # Create group box
        fuzzy_group = QGroupBox("Fuzzy Matching")
        fuzzy_layout = QVBoxLayout(fuzzy_group)

        # Enable/disable checkbox
        enable_layout = QHBoxLayout()
        self._fuzzy_enabled_checkbox = QCheckBox("Enable Fuzzy Matching")
        self._fuzzy_enabled_checkbox.setChecked(
            self._config_manager.get_bool(
                "ValidationSettings", "fuzzy_matching_enabled", fallback=True
            )
        )
        self._fuzzy_enabled_checkbox.stateChanged.connect(self._on_fuzzy_enabled_changed)
        enable_layout.addWidget(self._fuzzy_enabled_checkbox)
        enable_layout.addStretch()

        # Threshold slider
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Match Threshold:")
        self._fuzzy_threshold_slider = QSlider(Qt.Horizontal)
        self._fuzzy_threshold_slider.setMinimum(0)
        self._fuzzy_threshold_slider.setMaximum(100)
        self._fuzzy_threshold_slider.setValue(
            self._config_manager.get_int("ValidationSettings", "fuzzy_threshold", fallback=80)
        )
        self._fuzzy_threshold_slider.setTickPosition(QSlider.TicksBelow)
        self._fuzzy_threshold_slider.setTickInterval(10)
        self._fuzzy_threshold_slider.valueChanged.connect(self._on_fuzzy_threshold_changed)

        self._threshold_value_label = QLabel(f"{self._fuzzy_threshold_slider.value()}%")

        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self._fuzzy_threshold_slider)
        threshold_layout.addWidget(self._threshold_value_label)

        # Add to fuzzy layout
        fuzzy_layout.addLayout(enable_layout)
        fuzzy_layout.addLayout(threshold_layout)

        # Add to main layout
        layout.addWidget(fuzzy_group)

    def _on_fuzzy_enabled_changed(self, state: int):
        """
        Handle fuzzy matching enabled state changes.

        Args:
            state: Checkbox state
        """
        enabled = state == Qt.Checked
        self._config_manager.set_value("ValidationSettings", "fuzzy_matching_enabled", str(enabled))
        self._fuzzy_threshold_slider.setEnabled(enabled)
        self._apply_fuzzy_settings()

    def _on_fuzzy_threshold_changed(self, value: int):
        """
        Handle fuzzy threshold slider changes.

        Args:
            value: Slider value
        """
        self._threshold_value_label.setText(f"{value}%")
        self._config_manager.set_value("ValidationSettings", "fuzzy_threshold", str(value))
        self._apply_fuzzy_settings()

    def _apply_fuzzy_settings(self):
        """Apply fuzzy matching settings to the validation service."""
        enabled = self._fuzzy_enabled_checkbox.isChecked()
        threshold = self._fuzzy_threshold_slider.value() / 100.0  # Convert to 0-1 range

        self._validation_service.set_fuzzy_matching(enabled, threshold)

    def _update_list_widget(self, list_type: str, validation_list: List[str]):
        """
        Update a list widget with validation list entries.

        Args:
            list_type: The validation list type
            validation_list: The validation list entries
        """
        list_widget = getattr(self, f"_{list_type}_list_widget")

        # Block signals to avoid triggering change events
        list_widget.blockSignals(True)

        # Clear and repopulate the list
        list_widget.clear()
        for entry in validation_list:
            list_widget.addItem(entry)

        # Unblock signals
        list_widget.blockSignals(False)

    def _refresh_all_validation_lists(self):
        """Refresh all validation list widgets."""
        for list_type in ["player", "chest_type", "source"]:
            validation_list = self._data_store.get_validation_list(list_type)
            self._update_list_widget(list_type, validation_list)

    def showEvent(self, event):
        """
        Handle show event.

        Args:
            event: Show event
        """
        super().showEvent(event)

        # Refresh UI when panel is shown
        self._refresh_all_validation_lists()

    def closeEvent(self, event):
        """
        Handle close event.

        Args:
            event: Close event
        """
        # Save validation lists to config
        for list_type in ["player", "chest_type", "source"]:
            file_path = self._config_manager.get_path(f"{list_type}_list_file")
            if file_path:
                try:
                    self._file_service.save_validation_list(list_type, file_path)
                except Exception as e:
                    self._logger.error(f"Error saving {list_type} validation list: {e}")

        super().closeEvent(event)
