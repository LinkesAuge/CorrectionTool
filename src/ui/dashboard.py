"""
dashboard.py

Description: Main dashboard widget that integrates all UI components
Usage:
    from src.ui.dashboard import Dashboard
    dashboard = Dashboard(parent=self)
"""

import logging
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import os
import csv

from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QColor, QIcon, QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QFileDialog,
    QMenuBar,
)

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.models.validation_list import ValidationList
from src.services.config_manager import ConfigManager
from src.services.corrector import Corrector
from src.services.file_parser import FileParser
from src.ui.action_button_group import ActionButtonGroup
from src.ui.enhanced_table_view import EnhancedTableView
from src.ui.file_import_widget import FileImportWidget
from src.ui.statistics_widget import StatisticsWidget
from src.ui.validation_status_indicator import ValidationStatusIndicator
from src.ui.correction_manager_panel import CorrectionManagerPanel
from src.services.data_manager import DataManager
from src.utils.constants import DEFAULT_VALIDATION_LISTS, DEFAULT_DIRECTORIES


class Dashboard(QWidget):
    """
    Main dashboard widget that integrates all UI components.

    This is the central widget of the application, providing a unified
    interface for all chest tracking and correction features.

    Signals:
        entries_loaded (list): Signal emitted when entries are loaded
        entries_updated (list): Signal emitted when entries are updated
        corrections_loaded (list): Signal emitted when corrections are loaded
        corrections_applied (list): Signal emitted when corrections are applied
        validation_lists_updated (list): Signal emitted when validation lists are updated
        correction_rules_updated (list): Signal emitted when correction rules are updated

    Implementation Notes:
        - Uses QSplitter for flexible layout
        - Integrates components like FileImportWidget, StatisticsWidget, etc.
        - Manages data flow between components
        - Handles state persistence via ConfigManager
    """

    # Signals
    entries_loaded = Signal(list)  # List[ChestEntry]
    entries_updated = Signal(list)  # List[ChestEntry]
    corrections_loaded = Signal(list)  # List[CorrectionRule]
    corrections_applied = Signal(list)  # List[ChestEntry]
    validation_lists_updated = Signal(list)  # List of validation lists
    correction_rules_updated = Signal(list)  # List of correction rules

    def __init__(self, parent=None):
        """
        Initialize the dashboard.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Dashboard")

        # Initialize data manager
        self._data_manager = DataManager.get_instance()

        # Initialize config manager
        self._config = ConfigManager()

        # Initialize file parser
        self._file_parser = FileParser()

        # Initialize signal processing flags
        self._processing_signal = False
        self._processing_entries_loaded = False
        self._processing_corrections_applied = False
        self._entries = []
        self._correction_rules = []
        self._validation_lists = {}
        self._validation_errors_count = 0
        self._emitting_signal = False

        # Set up main widget
        self._setup_ui()

        # Connect signals
        self._connect_signals()

        # Initialize status bar reference - will be populated later
        self._status_bar = None
        if self.parent() and hasattr(self.parent(), "statusBar"):
            self._status_bar = self.parent().statusBar()
            self.logger.info("Status bar initialized from parent")
        else:
            self.logger.warning("No parent statusBar available, status_bar will be None")

        # Load saved rules
        self._load_saved_correction_rules()

        # Load saved validation lists
        self._load_saved_validation_lists()

        self.logger.info("Dashboard initialized")

    def statusBar(self):
        """
        Get the status bar from the parent window.

        Returns:
            QStatusBar: The status bar from the parent window
        """
        # Try to get status bar from parent (MainWindow) if not already set
        if self._status_bar is None and self.parent() and hasattr(self.parent(), "statusBar"):
            self._status_bar = self.parent().statusBar()
            self.logger.info("Status bar initialized from parent in statusBar method")

        return self._status_bar

    @property
    def _correction_manager(self):
        """
        Get the correction manager from the parent window.

        Returns:
            CorrectionManagerPanel: The correction manager panel from the parent window
        """
        # Try to get correction manager from parent (MainWindow)
        if self.parent() and hasattr(self.parent(), "_correction_manager"):
            return self.parent()._correction_manager
        return None

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # Create splitter for flexible layout
        self._splitter = QSplitter(Qt.Horizontal)

        # Left panel (sidebar)
        self._left_panel = QWidget()
        left_layout = QVBoxLayout(self._left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Add file import widget
        self._file_import_widget = FileImportWidget()
        left_layout.addWidget(self._file_import_widget)

        # Add statistics widget
        self._statistics_widget = StatisticsWidget()
        left_layout.addWidget(self._statistics_widget)

        # Add validation status indicator
        self._validation_status = ValidationStatusIndicator()
        left_layout.addWidget(self._validation_status)

        # Add action button group
        self._action_buttons = ActionButtonGroup()
        left_layout.addWidget(self._action_buttons)

        # Add stretch to push everything to the top
        left_layout.addStretch()

        # Right panel (main content)
        self._right_panel = QWidget()
        right_layout = QVBoxLayout(self._right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Add enhanced table view
        self._table_view = EnhancedTableView()
        right_layout.addWidget(self._table_view)

        # Add panels to splitter
        self._splitter.addWidget(self._left_panel)
        self._splitter.addWidget(self._right_panel)

        # Add splitter to main layout
        self._main_layout.addWidget(self._splitter)

        # Add menu bar
        self._setup_menu_bar()

    def _setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = QMenuBar(self)
        self._main_layout.setMenuBar(menubar)

        # File menu
        file_menu = menubar.addMenu("&File")

        # Load text file action
        load_text_action = QAction("Load &Text File", self)
        load_text_action.setShortcut("Ctrl+T")
        load_text_action.triggered.connect(self._on_load_text)
        file_menu.addAction(load_text_action)

        # Load correction file action
        load_correction_action = QAction("Load &Correction File", self)
        load_correction_action.setShortcut("Ctrl+C")
        load_correction_action.triggered.connect(self._on_load_correction_file)
        file_menu.addAction(load_correction_action)

        # Save output action
        save_action = QAction("&Save Output", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_output)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Validation lists action
        validation_lists_action = QAction("&Validation Lists", self)
        validation_lists_action.triggered.connect(self._show_validation_lists)
        tools_menu.addAction(validation_lists_action)

        # Correction rules action
        correction_rules_action = QAction("&Correction Rules", self)
        correction_rules_action.triggered.connect(self._show_correction_rules)
        tools_menu.addAction(correction_rules_action)

    def _connect_signals(self):
        """Connect signals to slots."""
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Connecting Dashboard signals")

        # Connect file import widget signals
        self._file_import_widget.entries_loaded.connect(self._on_entries_loaded)
        self._file_import_widget.corrections_loaded.connect(self._on_load_correction_file)
        self._file_import_widget.corrections_applied.connect(self._on_corrections_applied)

        # Connect action button signals
        self._action_buttons.save_requested.connect(self._on_save_requested)
        self._action_buttons.export_requested.connect(self._on_export_requested)
        self._action_buttons.apply_corrections_requested.connect(self._apply_corrections)
        self._action_buttons.validate_requested.connect(self._validate_entries)
        self._action_buttons.settings_requested.connect(self._on_settings_requested)

        # Connect table view signals
        self._table_view.entry_selected.connect(self._on_entry_selected)
        self._table_view.entry_edited.connect(self._on_entry_edited)

        # Connect correction manager signals if available
        if self._correction_manager is not None:
            logger.info("Connecting correction manager signals")
            self._correction_manager.correction_rules_updated.connect(
                self._on_correction_rules_updated
            )
            self._correction_manager.validation_lists_updated.connect(
                self._on_validation_lists_updated
            )
        else:
            logger.warning("Correction manager not available for signal connection")

        logger.info("Dashboard signals connected successfully")

    def _load_saved_correction_rules(self):
        """Load saved correction rules from config."""
        try:
            # Get the correction rules path from config using the new path method
            correction_rules_path = self._config.get_path("correction_rules_file")

            # Get the absolute path
            absolute_path = self._config.get_absolute_path(correction_rules_path)

            if absolute_path.exists():
                self.logger.info(f"Loading correction rules from {absolute_path}")

                # Load correction rules using the file parser
                correction_rules = self._file_parser.parse_correction_file(str(absolute_path))

                if correction_rules:
                    # Update correction rules in data manager
                    self._data_manager.set_correction_rules(correction_rules)

                    # Update the status for the user
                    self.logger.info(f"Loaded {len(correction_rules)} correction rules")
                    if hasattr(self, "_status_bar") and self._status_bar:
                        self._status_bar.showMessage(
                            f"Loaded {len(correction_rules)} correction rules", 3000
                        )

                    # Emit signal
                    self.corrections_loaded.emit(correction_rules)

                    # Update last used path
                    self._config.set_last_used_path("last_correction_file", str(absolute_path))
                    self._config.set_last_used_path(
                        "last_correction_directory", str(absolute_path.parent)
                    )

                    return True
                else:
                    self.logger.warning("No correction rules loaded from file")
            else:
                self.logger.info(f"Correction rules file not found: {absolute_path}")

            return False
        except Exception as e:
            self.logger.error(f"Error loading correction rules: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return False

    def _on_load_correction_file(self, file_path=None):
        """
        Load a correction file.

        Args:
            file_path (str or list, optional): Path to correction file or list of rules. Defaults to None.
        """
        import logging
        import traceback
        from pathlib import Path
        from src.services.file_parser import FileParser

        logger = logging.getLogger(__name__)

        # If file_path is a list of rules, treat it directly as rules
        if isinstance(file_path, list):
            logger.info(
                f"Loading correction file: directly provided list of {len(file_path)} rules"
            )
            rules = file_path
        else:
            # Handle string file path
            if not file_path:
                # Get default directory
                default_dir = self._config.get_path("corrections_dir", "data/corrections")

                # Create it if it doesn't exist
                os.makedirs(default_dir, exist_ok=True)

                # Open file dialog
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Open Correction List",
                    default_dir,
                    "CSV Files (*.csv);;All Files (*)",
                )

            if file_path:
                logger.info(f"Loading correction file: {file_path}")
                try:
                    # Parse the correction file
                    parser = FileParser()
                    rules = parser.parse_correction_file(file_path)
                except Exception as e:
                    logger.error(f"Error loading correction file: {str(e)}")
                    logger.debug(traceback.format_exc())
                    if self._status_bar:
                        self._status_bar.showMessage(f"Error loading correction file: {str(e)}")
                    return False
            else:
                return False

        # Process the rules
        if rules:
            logger.info(f"Loaded {len(rules)} correction rules")

            # Set the rules in DataManager to prevent signal loops
            if isinstance(file_path, str):
                self._data_manager.set_correction_rules(rules, file_path)
            else:
                self._data_manager.set_correction_rules(rules)

            # Set rules in the correction manager panel
            if self._correction_manager:
                logger.info("Setting rules in correction manager panel")
                self._correction_manager.set_rules(rules)

            # Update file import widget if we have a file path
            if isinstance(file_path, str):
                self._file_import_widget.set_correction_file_path(file_path)

                # Store file path in config using consolidated paths
                self._config.set_path("correction_rules_file", file_path)
                self._config.set_path("last_folder", str(Path(file_path).parent))

            # Update status bar
            if self._status_bar:
                self._status_bar.showMessage(
                    f"Loaded {len(rules)} correction rules"
                    + (f" from {file_path}" if isinstance(file_path, str) else "")
                )

            # Emit signal
            logger.info(f"Emitting corrections_loaded signal with {len(rules)} rules")
            self.corrections_loaded.emit(rules)

            # Also emit correction_rules_updated signal for other components
            logger.info(f"Emitting correction_rules_updated signal with {len(rules)} rules")
            self.correction_rules_updated.emit(rules)

            return True
        else:
            logger.warning(
                f"No correction rules found"
                + (f" in file: {file_path}" if isinstance(file_path, str) else "")
            )
            if self._status_bar:
                self._status_bar.showMessage("No correction rules found")
            return False

    def _load_saved_validation_lists(self):
        """Load saved validation lists from config."""
        try:
            # Initialize validation lists dictionary
            validation_lists = {}
            lists_loaded = False

            # List of validation types and their corresponding path keys
            validation_types = [
                ("player", "player_list_file"),
                ("chest_type", "chest_type_list_file"),
                ("source", "source_list_file"),
            ]

            # Load each validation list
            for list_type, path_key in validation_types:
                try:
                    # Get the path from config using the new path method
                    list_path = self._config.get_path(path_key)

                    # Get the absolute path
                    absolute_path = self._config.get_absolute_path(list_path)

                    if absolute_path.exists():
                        self.logger.info(f"Loading {list_type} list from {absolute_path}")

                        # Load validation list using appropriate method
                        try:
                            # First try using the data manager
                            if hasattr(self._data_manager, "load_validation_list"):
                                validation_list = self._data_manager.load_validation_list(
                                    list_type, str(absolute_path)
                                )
                            else:
                                # If not available, try direct loading
                                from src.models.validation_list import ValidationList

                                validation_list = ValidationList(list_type)
                                validation_list.load_from_file(str(absolute_path))

                            if validation_list and len(validation_list.entries) > 0:
                                validation_lists[list_type] = validation_list
                                self.logger.info(
                                    f"Loaded {len(validation_list.entries)} {list_type} entries"
                                )
                                lists_loaded = True
                            else:
                                self.logger.warning(f"No {list_type} entries loaded from file")
                        except Exception as list_error:
                            self.logger.error(f"Error loading {list_type} list: {list_error}")
                    else:
                        self.logger.info(
                            f"{list_type.capitalize()} list file not found: {absolute_path}"
                        )
                except Exception as e:
                    self.logger.error(f"Error processing {list_type} list: {e}")

            # If any lists were loaded, update validation lists in data manager
            if lists_loaded:
                if validation_lists:
                    self._data_manager.set_validation_lists(validation_lists)

                    # Emit signal with delayed execution
                    self._delayed_emit_validation_lists(validation_lists)

                    return True

            # If no lists were loaded, try loading default lists
            self.logger.info("No validation lists loaded from config, trying defaults...")
            return self._load_default_validation_lists()

        except Exception as e:
            self.logger.error(f"Error loading validation lists: {e}")
            import traceback

            self.logger.error(traceback.format_exc())

            # Try loading default lists as fallback
            try:
                return self._load_default_validation_lists()
            except Exception as default_error:
                self.logger.error(f"Error loading default validation lists: {default_error}")
                return False

    def _delayed_emit_validation_lists(self, lists):
        """
        Re-emit the validation lists after a delay.
        This ensures all components are fully initialized.

        Args:
            lists: Dictionary of validation lists
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Re-emitting {len(lists)} validation lists")

        # Check if we're visible
        logger.info(f"Dashboard widget is visible: {self.isVisible()}")

        # Make sure the correction manager is available
        if self._correction_manager is not None:
            logger.info("Correction manager is available")
            # Re-emit the signal
            logger.info("Re-emitting validation_lists_updated signal")
            self.validation_lists_updated.emit(lists)

            # Force the correction manager to be visible
            if hasattr(self.parent(), "_validation_btn"):
                logger.info("Making correction manager panel visible via button click")
                self.parent()._validation_btn.click()

                # Give UI time to update and then re-emit
                QTimer.singleShot(500, lambda: self.validation_lists_updated.emit(lists))

                # Force the validation lists tab to be active
                QTimer.singleShot(
                    750, lambda: self._correction_manager._tools_tabs.setCurrentIndex(1)
                )

                # Go back to dashboard
                QTimer.singleShot(1000, lambda: self.parent()._dashboard_btn.click())
        else:
            logger.warning("Correction manager not available for delayed emit")

    @Slot(list)
    def _on_correction_rules_updated(self, rules):
        """
        Handle correction rules updated.

        Args:
            rules: List of correction rules
        """
        # Prevent signal loops
        if self._processing_signal:
            self.logger.warning("Skipping due to signal loop prevention")
            return

        try:
            self._processing_signal = True
            self.logger.info(
                f"Dashboard: _on_correction_rules_updated called with {len(rules)} rules"
            )

            # Check if rules are already set and unchanged
            if self._correction_rules == rules:
                self.logger.info("Rules are unchanged, no need to update")
                return

            # Store the rules for use in correction process
            self._correction_rules = rules

            # Save the current file path
            if hasattr(self, "_current_correction_file") and self._current_correction_file:
                file_path = str(self._current_correction_file)
                self._config.set("General", "last_correction_file", file_path)

                # Ensure file paths are consistent between Dashboard and FileImportWidget
                folder_path = str(Path(file_path).parent)
                self._config.set("General", "last_folder", folder_path)
                self._config.set("Files", "last_correction_directory", folder_path)
                self._config.set("Paths", "default_correction_rules", file_path)
                # Save changes to disk
                self._config.save()

            # Show message
            self.statusBar().showMessage(f"Correction rules updated: {len(rules)} rules")

            # Update action buttons
            self._action_buttons.set_corrections_loaded(len(rules) > 0)

            # Update statistics widget
            self._statistics_widget.set_correction_rules(rules)

            # Update the file import widget without triggering signals - direct update
            if hasattr(self, "_file_import_widget"):
                self.logger.info(f"Updating file import widget with correction rules")
                # Update widget UI state without emitting signal
                self._file_import_widget._correction_rules = rules
                self._file_import_widget._corrections_status_label.setText(
                    f"{len(rules)} correction rules loaded"
                )
                self._file_import_widget._corrections_status_label.setStyleSheet("color: #007700;")

            # Emit a targeted signal only for UI components that need to display the rules
            # NOT components that will re-process or re-emit them
            self.logger.info(f"Emitting correction_rules_updated signal with {len(rules)} rules")
            self.correction_rules_updated.emit(rules)

            # We no longer emit corrections_loaded signal here to prevent loops
            # self.corrections_loaded.emit(rules)

            # Trigger correction if we have entries - only when directly
            # requested, not triggered automatically on rule updates
            if self._config.get_boolean("Correction", "auto_apply_corrections", fallback=True):
                if hasattr(self, "_entries") and self._entries:
                    self._apply_corrections()
        except Exception as e:
            self.logger.error(f"Error in _on_correction_rules_updated: {str(e)}")
            import traceback

            self.logger.error(traceback.format_exc())
        finally:
            self._processing_signal = False

    @Slot(dict)
    def _on_validation_lists_updated(self, lists):
        """
        Handle validation lists updated.

        Args:
            lists: Dictionary of validation lists
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Received validation_lists_updated signal with {len(lists)} lists")

        # More robust signal loop prevention
        if self._processing_signal:
            logger.warning("Skipping due to signal loop prevention")
            return

        try:
            self._processing_signal = True

            # Store the lists for use in validation process
            self._validation_lists = lists

            # Log the lists we received
            for list_type, validation_list in lists.items():
                logger.info(
                    f"Received {list_type} validation list with {len(validation_list.items)} items"
                )

                # Save the current file paths
                if validation_list.file_path:
                    list_path_str = str(validation_list.file_path)
                    logger.info(f"Saving {list_type} validation list path: {list_path_str}")
                    self._config.set("General", f"{list_type}_list_path", list_path_str)

                    # Also save in other config locations for consistency
                    if list_type == "player":
                        self._config.set("Validation", "player_list", list_path_str)
                    elif list_type == "chest_type":
                        self._config.set("Validation", "chest_type_list", list_path_str)
                    elif list_type == "source":
                        self._config.set("Validation", "source_list", list_path_str)

            # Save changes to disk
            self._config.save()
            logger.info("Saved validation list paths to config")

            # Show message
            if self.statusBar():
                self.statusBar().showMessage(f"Validation lists updated: {len(lists)} lists", 3000)

            # Update other components only if not already processing signals elsewhere
            # This is the key change to prevent infinite signal loops
            if self._correction_manager is not None:
                # Check if correction manager is already processing signals
                correction_manager_processing = getattr(
                    self._correction_manager, "_processing_signal", False
                )
                if not correction_manager_processing:
                    logger.info(f"Updating correction manager with {len(lists)} validation lists")
                    # We don't need to emit signals since we're directly setting the lists
                    self._correction_manager._validation_lists = lists
                    # Don't call set_validation_lists as it will emit signals causing loops
                else:
                    logger.warning("Correction manager already processing signals, skipping update")

            # Trigger validation if we have entries
            if hasattr(self, "_entries") and self._entries:
                logger.info("Triggering validation for entries")
                self._validate_entries()

        except Exception as e:
            logger.error(f"Error in _on_validation_lists_updated: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
        finally:
            self._processing_signal = False

    @Slot(list)
    def _on_entries_loaded(self, entries: List[ChestEntry]):
        """
        Handle entries loaded event.

        Args:
            entries: List of loaded chest entries
        """
        # Add more detailed logging
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Dashboard: _on_entries_loaded called with {len(entries)} entries")

        # Log an example entry
        if entries:
            first_entry = entries[0]
            logger.info(
                f"First entry: {first_entry.chest_type} | {first_entry.player} | {first_entry.source}"
            )
        else:
            logger.warning("No entries received in _on_entries_loaded!")
            return

        # Prevent signal loops
        if self._processing_entries_loaded:
            logger.warning("Skipping _on_entries_loaded due to signal loop prevention")
            return

        try:
            self._processing_entries_loaded = True
            logger.info(f"Dashboard: Processing {len(entries)} loaded entries")

            # Store the entries
            self._entries = entries
            logger.info(f"Dashboard: Stored {len(self._entries)} entries in self._entries")

            # Apply corrections if auto-apply is enabled
            config_manager = ConfigManager()
            if config_manager.get_bool("Correction", "auto_apply", fallback=True):
                logger.info("Auto-apply is enabled, applying corrections")
                self._apply_corrections()
            else:
                logger.info("Auto-apply is disabled, updating UI directly")

                # Emit entry loaded signal
                logger.info("Emitting entries_loaded signal")
                self.entries_loaded.emit(entries)

                # Update table view with new entries
                logger.info("Updating table view with entries")
                if hasattr(self, "_table_view") and self._table_view:
                    self._table_view.set_entries(entries)
                    logger.info("Table view updated successfully")
                else:
                    logger.error("Dashboard: _table_view not initialized or not available!")

                # Update statistics
                if hasattr(self, "_statistics_widget") and self._statistics_widget:
                    self._statistics_widget.set_entries(entries)
                    logger.info("Statistics widget updated successfully")

                # Show status message
                if hasattr(self, "_status_bar") and self._status_bar:
                    self._status_bar.showMessage(f"Loaded {len(entries)} entries", 3000)
                    logger.info("Status bar message updated")

                # Update action buttons for validation
                if hasattr(self, "_action_buttons") and self._action_buttons:
                    self._action_buttons.set_entries_loaded(True)
                    logger.info("Action buttons updated")
        except Exception as e:
            logger.error(f"Error in _on_entries_loaded: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
        finally:
            self._processing_entries_loaded = False
            logger.info("_on_entries_loaded processing completed")

    @Slot(list)
    def _on_corrections_applied(self, results):
        """
        Handle when corrections are applied.

        Args:
            results: Correction results
        """
        try:
            self.logger.debug("Handling corrections applied signal")
            if self._processing_corrections_applied:
                self.logger.warning(
                    "Skipping _on_corrections_applied due to signal loop prevention"
                )
                return

            self._processing_corrections_applied = True
            self.logger.info(
                f"Dashboard: Received {len(results)} applied corrections from DataManager"
            )

            # Update the entries with corrected values
            self._update_entries_with_corrections(results)

            # Update statistics
            if self._statistics_widget:
                self.logger.info("Updating statistics after corrections")
                self._statistics_widget._update_statistics(self._entries)

            # Update table view with corrected entries
            if self._table_view:
                self.logger.info("Updating table view with corrected entries")
                self._table_view.set_entries(self._entries)

            # Update status bar
            if self._status_bar:
                self.logger.info(f"Setting status bar message: {len(results)} corrections applied")
                self._status_bar.showMessage(f"{len(results)} corrections applied", 5000)

            self._processing_corrections_applied = False
        except Exception as e:
            self.logger.error(f"Error in _on_corrections_applied: {str(e)}")
            self.logger.error(traceback.format_exc())
            self._processing_corrections_applied = False

    @Slot(list)
    def _update_entries_with_corrections(self, correction_results):
        """
        Update entries with the applied corrections.

        Args:
            correction_results (List[CorrectionResult]): List of correction results
        """
        try:
            if not correction_results:
                self.logger.info("No corrections to apply")
                return

            self.logger.info(f"Updating entries with {len(correction_results)} corrections")

            # Check if the results are actually entries
            if correction_results and isinstance(correction_results[0], ChestEntry):
                self.logger.info("Received list of ChestEntry objects, replacing entries")
                self._entries = correction_results
                return

            # If we have CorrectionResult objects, process them
            # Group corrections by entry ID for efficient processing
            corrections_by_entry = {}
            for result in correction_results:
                if not hasattr(result, "entry"):
                    self.logger.warning(
                        f"Correction result object does not have 'entry' attribute: {result}"
                    )
                    continue

                entry_id = result.entry
                if entry_id not in corrections_by_entry:
                    corrections_by_entry[entry_id] = []
                corrections_by_entry[entry_id].append(result)

            # Apply corrections to entries
            updated_count = 0
            for entry_id, entry_corrections in corrections_by_entry.items():
                # Find the entry with this ID
                matching_entries = [e for e in self._entries if e.id == entry_id]
                if not matching_entries:
                    self.logger.warning(f"No entry found with ID {entry_id}")
                    continue

                entry = matching_entries[0]

                # Apply each correction
                for correction in entry_corrections:
                    field_name = correction.field
                    corrected_value = correction.corrected

                    self.logger.debug(
                        f"Applying correction to entry {entry_id}: {field_name} -> {corrected_value}"
                    )

                    # Apply the correction using the entry's method
                    entry.apply_correction(field_name, corrected_value)
                    updated_count += 1

            self.logger.info(f"Updated {updated_count} fields in entries")

        except Exception as e:
            self.logger.error(f"Error updating entries with corrections: {str(e)}")
            self.logger.error(traceback.format_exc())

    @Slot()
    def _on_save_requested(self):
        """Handle save requested signal."""
        if not self._entries:
            QMessageBox.warning(self, "Save", "No entries to save")
            return

        try:
            # TODO: Implement file selection dialog and saving
            # For now, just show a message
            QMessageBox.information(self, "Save", "Saving entries is not yet implemented")
        except Exception as e:
            self.logger.error(f"Error saving entries: {str(e)}")
            QMessageBox.critical(
                self, "Save Error", f"An error occurred while saving entries:\n\n{str(e)}"
            )

    @Slot()
    def _on_export_requested(self):
        """Handle export requested signal."""
        if not self._entries:
            QMessageBox.warning(self, "Export", "No entries to export")
            return

        try:
            # TODO: Implement file selection dialog and exporting
            # For now, just show a message
            QMessageBox.information(self, "Export", "Exporting entries is not yet implemented")
        except Exception as e:
            self.logger.error(f"Error exporting entries: {str(e)}")
            QMessageBox.critical(
                self, "Export Error", f"An error occurred while exporting entries:\n\n{str(e)}"
            )

    @Slot()
    def _apply_corrections(self):
        """Apply corrections to the loaded entries."""
        # Prevent signal loops
        if self._processing_signal:
            return

        try:
            self._processing_signal = True
            logger = logging.getLogger(__name__)
            logger.info("Applying corrections to entries")

            if not self._entries:
                logger.info("No entries to correct")
                return

            if not self._correction_rules:
                logger.info("No correction rules to apply")
                return

            # Create corrector if needed
            if not hasattr(self, "_corrector"):
                from src.services.corrector import Corrector

                self._corrector = Corrector()

            # Set rules in the corrector
            self._corrector.set_rules(self._correction_rules)

            # Apply corrections with defensive error handling
            try:
                results = self._corrector.apply_corrections(self._entries, self._correction_rules)
            except Exception as e:
                logger.error(f"Error in corrector.apply_corrections: {str(e)}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "Correction Error",
                    f"An error occurred while applying corrections:\n\n{str(e)}",
                )
                return

            # Count corrections that were actually applied
            correction_count = sum(1 for result in results if result.was_corrected)

            # Only show message if corrections were actually needed and we're not in a signal loop
            if correction_count > 0:
                # Group results by entry for a more meaningful message
                entry_counts = {}
                for result in results:
                    if result.was_corrected:  # Only count actual corrections
                        entry_idx = result.entry_index
                        entry_counts[entry_idx] = entry_counts.get(entry_idx, 0) + 1

                entry_count = len(entry_counts)
                QMessageBox.information(
                    self,
                    "Apply Corrections",
                    f"Applied {correction_count} corrections to {entry_count} entries.",
                )

                # Emit signals only if corrections were made
                self.entries_updated.emit(self._entries)
                self.corrections_applied.emit(self._entries)

            # Update the table view regardless of corrections
            if hasattr(self, "_table_view"):
                self._table_view.set_entries(self._entries)

            # Validate entries after corrections are applied to update status
            self._validate_entries()

        except Exception as e:
            logger.error(f"Error applying corrections: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Correction Error",
                f"An error occurred while applying corrections:\n\n{str(e)}",
            )
        finally:
            self._processing_signal = False

    @Slot()
    def _on_settings_requested(self):
        """Handle settings requested signal."""
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog is not yet implemented")

    @Slot(object)
    def _on_entry_selected(self, entry: ChestEntry):
        """
        Handle entry selected signal.

        Args:
            entry: Selected entry
        """
        # TODO: Implement entry selection handling
        pass

    @Slot(object)
    def _on_entry_edited(self, entry: ChestEntry):
        """
        Handle entry edited signal.

        Args:
            entry: Edited entry
        """
        # Update entries list with edited entry
        for i, existing_entry in enumerate(self._entries):
            if existing_entry is entry:
                self._entries[i] = entry
                break

        # Update statistics
        self._statistics_widget.set_entries(self._entries)

        # Update validation status
        self._validation_status.set_entries(self._entries)

        # Forward the signal
        self.entries_updated.emit(self._entries)

    def set_validation_lists(self, validation_lists: list):
        """
        Set the validation lists.

        Args:
            validation_lists: List of validation lists
        """
        self._validation_lists = validation_lists

        # Forward the signal
        self.validation_lists_updated.emit(validation_lists)

    def set_entries(self, entries: List[ChestEntry]):
        """
        Set the entries.

        Args:
            entries: List of entries
        """
        self._on_entries_loaded(entries)

    def set_validation_errors(self, count: int):
        """
        Set the validation error count.

        Args:
            count: Number of validation errors
        """
        self._validation_errors_count = count

        # Update statistics widget
        self._statistics_widget.set_validation_errors(count)

        # Update validation status
        self._validation_status.set_validation_status(count, 0)

    def get_entries(self) -> List[ChestEntry]:
        """
        Get the current entries.

        Returns:
            List[ChestEntry]: List of entries
        """
        return self._data_manager.get_entries() if self._data_manager else []

    def get_entry_table_view(self):
        """
        Get the entry table view for connecting adapters.

        Returns:
            EnhancedTableView: The table view for entries
        """
        return self._table_view

    def showEvent(self, event):
        """
        Handle the show event.

        This ensures the splitter is properly sized after the widget is shown.

        Args:
            event: Show event
        """
        super().showEvent(event)

        # Set splitter sizes to equal width when shown (50% left, 50% right)
        total_width = self.width()
        self._splitter.setSizes([total_width // 4, total_width // 2])

    def _show_correction_manager_panel(self):
        """Show the correction manager panel tab and ensure it's visible."""
        # Switch to the correction manager tab in the parent window
        if self.parent() and hasattr(self.parent(), "_content_widget"):
            # Find the index of the correction manager panel
            for i in range(self.parent()._content_widget.count()):
                widget = self.parent()._content_widget.widget(i)
                if hasattr(widget, "_tools_tabs") and isinstance(widget, CorrectionManagerPanel):
                    # Switch to the correction manager tab
                    self.parent()._content_widget.setCurrentIndex(i)
                    break

    def _show_validation_lists(self):
        """Show the validation lists tab in the correction manager."""
        # Show correction manager panel
        self._show_correction_manager_panel()

        # Switch to validation lists tab
        if hasattr(self, "_correction_manager") and self._correction_manager is not None:
            if hasattr(self._correction_manager, "_tools_tabs"):
                self._correction_manager._tools_tabs.setCurrentIndex(1)
            else:
                logging.warning("CorrectionManagerPanel does not have _tools_tabs attribute")
        else:
            logging.warning("Dashboard does not have _correction_manager attribute or it is None")

    def _show_correction_rules(self):
        """Show the correction rules tab in the correction manager."""
        # Show correction manager panel
        self._show_correction_manager_panel()

        # Switch to correction rules tab
        if hasattr(self, "_correction_manager") and self._correction_manager is not None:
            if hasattr(self._correction_manager, "_tools_tabs"):
                self._correction_manager._tools_tabs.setCurrentIndex(0)
            else:
                logging.warning("CorrectionManagerPanel does not have _tools_tabs attribute")
        else:
            logging.warning("Dashboard does not have _correction_manager attribute or it is None")

    def _on_load_text(self, file_path=None):
        """
        Handle loading text from a file.

        Args:
            file_path (str, optional): Path to the text file. If None, a file dialog will be shown.
        """
        if file_path is None:
            # Get file path
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Load Text File",
                str(self._config.get("General", "last_folder", str(Path.home()))),
                "Text Files (*.txt);;All Files (*.*)",
            )

            if not file_path:
                return

            # Save folder for next time
            self._config.set("General", "last_folder", str(Path(file_path).parent))

        try:
            # Parse the text file
            entries = self._file_parser.parse_text_file(file_path)

            # Store the entries
            self._entries = entries

            # Update the table view
            self._table_view.set_entries(entries)

            # Log some info
            self.logger.info(f"Loaded {len(entries)} entries from {file_path}")

            # Show message in status bar
            status_bar = self.statusBar()
            if status_bar:
                status_bar.showMessage(f"Loaded {len(entries)} entries from {file_path}", 5000)

        except Exception as e:
            self.logger.error(f"Error loading text file: {e}")
            QMessageBox.critical(self, "Error Loading Text File", f"Error: {str(e)}")

    def _on_save_output(self):
        """Handle save output button click."""
        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Output",
            str(self._config.get("General", "last_folder", str(Path.home()))),
            "Text Files (*.txt);;All Files (*.*)",
        )

        if not file_path:
            return

        # Save folder for next time
        self._config.set("General", "last_folder", str(Path(file_path).parent))

        # Get entries from output panel
        entries = self._output_panel.get_entries()

        # Save to file
        try:
            from src.services.file_parser import FileParser

            parser = FileParser()
            parser.save_entries_to_text_file(entries, file_path)

            # Show message
            self.statusBar().showMessage(f"Saved {len(entries)} entries to {file_path}")

        except Exception as e:
            self.logger.error(f"Error saving output: {e}")
            QMessageBox.critical(self, "Error Saving Output", f"Error: {str(e)}")

    def _validate_entries(self):
        """
        Validate all entries against validation lists.

        This method validates all entries against the validation lists
        and updates their validation status.
        """
        try:
            self.logger.info("Validating entries in Dashboard")

            # Get validation lists from DataManager
            validation_lists = {}
            if self._data_manager:
                validation_lists = self._data_manager.get_validation_lists()

            # Extract individual lists
            player_list = validation_lists.get("player", None)
            chest_type_list = validation_lists.get("chest_type", None)
            source_list = validation_lists.get("source", None)

            # Log validation lists status
            self.logger.info(
                f"Validation lists: Players={len(player_list.items) if player_list else 0}, "
                f"Chest Types={len(chest_type_list.items) if chest_type_list else 0}, "
                f"Sources={len(source_list.items) if source_list else 0}"
            )

            # Reset validation counters
            error_count = 0
            warning_count = 0

            # Validate entries
            for entry in self._entries:
                # Reset existing validation
                entry.reset_validation()

                # Validate player
                if player_list:
                    player_valid = player_list.is_valid(entry.player)
                    fuzzy_match = None
                    confidence = 1.0

                    if not player_valid:
                        fuzzy_match, confidence = player_list.find_fuzzy_match(entry.player)
                        player_valid = fuzzy_match is not None

                    entry.set_field_validation("player", player_valid, confidence, fuzzy_match)
                    if not player_valid:
                        error_count += 1
                    elif fuzzy_match and fuzzy_match != entry.player:
                        warning_count += 1

                # Validate chest type
                if chest_type_list:
                    chest_valid = chest_type_list.is_valid(entry.chest_type)
                    fuzzy_match = None
                    confidence = 1.0

                    if not chest_valid:
                        fuzzy_match, confidence = chest_type_list.find_fuzzy_match(entry.chest_type)
                        chest_valid = fuzzy_match is not None

                    entry.set_field_validation("chest_type", chest_valid, confidence, fuzzy_match)
                    if not chest_valid:
                        error_count += 1
                    elif fuzzy_match and fuzzy_match != entry.chest_type:
                        warning_count += 1

                # Validate source
                if source_list:
                    source_valid = source_list.is_valid(entry.source)
                    fuzzy_match = None
                    confidence = 1.0

                    if not source_valid:
                        fuzzy_match, confidence = source_list.find_fuzzy_match(entry.source)
                        source_valid = fuzzy_match is not None

                    entry.set_field_validation("source", source_valid, confidence, fuzzy_match)
                    if not source_valid:
                        error_count += 1
                    elif fuzzy_match and fuzzy_match != entry.source:
                        warning_count += 1

                # Update entry status
                if entry.has_validation_errors():
                    entry.status = "Invalid"
                elif entry.has_corrections():
                    entry.status = "Corrected"
                else:
                    entry.status = "Valid"

            # Update validation errors count
            self._validation_errors_count = error_count

            # Update statistics widget
            if self._statistics_widget:
                self._statistics_widget._update_statistics(self._entries)

            # Update table view
            if self._table_view:
                self._table_view.set_entries(self._entries)

            # Update status bar
            if self._status_bar:
                self._status_bar.showMessage(
                    f"Validation complete: {error_count} errors, {warning_count} warnings", 5000
                )

            self.logger.info(
                f"Validation completed: {error_count} errors, {warning_count} warnings"
            )
            return error_count, warning_count
        except Exception as e:
            self.logger.error(f"Error validating entries: {str(e)}")
            self.logger.error(traceback.format_exc())
            return 0, 0

    def _load_input_file(self, file_path):
        """
        Load an input file with chest entries.

        Args:
            file_path (str): Path to the file to load
        """
        try:
            if not file_path:
                self.logger.warning("No file path provided to _load_input_file")
                return False

            # Load entries from file
            entries = self._file_parser.parse_entry_file(file_path)
            if not entries:
                self.logger.warning(f"No entries loaded from {file_path}")
                return False

            # Store entries and update UI
            self._entries = entries
            self.logger.info(f"Loaded {len(entries)} entries from {file_path}")

            # Update data manager
            if self._data_manager:
                self._data_manager.set_entries(entries)

            # Update table view
            if self._table_view:
                self._table_view.set_entries(entries)

            # Apply corrections if configured to do so
            if self._config.get("Correction", "auto_apply_corrections", fallback=True):
                self.logger.info("Auto-applying corrections to loaded entries")
                self._apply_corrections()

            # Update statistics
            if self._statistics_widget:
                self._statistics_widget.update_statistics(entries)

            # Validate entries
            self._validate_entries()

            return True
        except Exception as e:
            self.logger.error(f"Error loading input file: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False

    def set_correction_rules(self, rules):
        """
        Set the correction rules.

        This method receives correction rules from outside components
        and updates the internal state and UI components.

        Args:
            rules (List[CorrectionRule]): The correction rules to set
        """
        try:
            self.logger.info(f"Dashboard: set_correction_rules called with {len(rules)} rules")
            self._correction_rules = rules

            # Update the file import widget if it exists
            if self._file_import_widget:
                self.logger.info("Updating file import widget with correction rules")
                self._file_import_widget.set_correction_rules(rules)

            # Apply corrections to current entries if any
            if (
                hasattr(self, "_entries")
                and self._entries
                and self._config.get("Correction", "auto_apply_corrections", fallback=True)
            ):
                self.logger.info("Auto-applying new correction rules to existing entries")
                self._apply_corrections()

        except Exception as e:
            self.logger.error(f"Error in set_correction_rules: {str(e)}")
            self.logger.error(traceback.format_exc())

    def _export_entries(self):
        """
        Export the entries to a file.

        This method implements the export logic for the entries.
        """
        try:
            # Implement export logic here
            pass
        except Exception as e:
            self.logger.error(f"Error exporting entries: {str(e)}")

    def _load_default_validation_lists(self):
        """
        Load default validation lists from predefined locations.
        This is used as a fallback when no validation lists are found in the config.
        """
        logger = logging.getLogger(__name__)
        logger.info("Loading default validation lists")

        lists = {}

        try:
            # Determine the validation directory
            validation_dir = Path(self._config.get_path("validation_dir", "data/validation"))

            # Make sure the directory exists
            validation_dir.mkdir(parents=True, exist_ok=True)

            # Default file paths based on type
            default_files = {
                "player": validation_dir
                / f"{DEFAULT_VALIDATION_LISTS.get('player', 'players')}.txt",
                "chest_type": validation_dir
                / f"{DEFAULT_VALIDATION_LISTS.get('chest_type', 'chest_types')}.txt",
                "source": validation_dir
                / f"{DEFAULT_VALIDATION_LISTS.get('source', 'sources')}.txt",
            }

            # Load default lists if they exist
            for list_type, file_path in default_files.items():
                if file_path.exists():
                    logger.info(f"Loading default {list_type} list from {file_path}")
                    try:
                        validation_list = ValidationList.load_from_file(file_path, list_type)
                        if validation_list and validation_list.items:
                            lists[list_type] = validation_list
                            logger.info(
                                f"Loaded default {list_type} list with {len(validation_list.items)} items"
                            )

                            # Update the config with the file path
                            if list_type == "player":
                                self._config.set_path("player_list_file", str(file_path))
                            elif list_type == "chest_type":
                                self._config.set_path("chest_type_list_file", str(file_path))
                            elif list_type == "source":
                                self._config.set_path("source_list_file", str(file_path))
                    except Exception as e:
                        logger.warning(f"Error loading default {list_type} list: {str(e)}")
                        logger.debug(traceback.format_exc())

            # If we have validation lists, update data manager and emit signal
            if lists:
                # Save to data manager
                self._data_manager.set_validation_lists(lists)

                # Emit signal with delay to ensure components are ready
                self._delayed_emit_validation_lists(lists)

                logger.info(f"Loaded {len(lists)} default validation lists")
            else:
                logger.warning("No default validation lists found")

        except Exception as e:
            logger.error(f"Error loading default validation lists: {str(e)}")
            logger.debug(traceback.format_exc())
