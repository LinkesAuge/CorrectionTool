"""
dashboard.py

Description: Main dashboard widget that integrates all UI components
Usage:
    from src.ui.dashboard import Dashboard
    dashboard = Dashboard(parent=self)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

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
        """Initialize the dashboard widget."""
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._logger.info("Initializing Dashboard")

        # Prevent signal loops and cascading signals
        self._processing_signal = False
        self._processing_entries_loaded = False
        self._processing_corrections_loaded = False
        self._processing_corrections_applied = False

        # Initialize data
        self._entries = []
        self._correction_rules = []
        self._validation_lists = {}
        self._validation_errors = 0

        # Initialize components
        self._file_import_widget = None
        self._statistics_widget = None
        self._action_buttons = None
        self._validation_status = None
        self._table_view = None
        self._splitter = None
        self._sidebar = None
        self._main_content = None
        self._corrector = Corrector()

        # Setup UI components
        self._setup_ui()
        self._connect_signals()

        # Load saved correction rules
        QTimer.singleShot(500, self._load_saved_correction_rules)

        # Load saved validation lists
        QTimer.singleShot(1000, self._load_saved_validation_lists)

        # Status bar reference from parent (MainWindow)
        self._status_bar = None

        self._logger.info("Dashboard initialized")

    def statusBar(self):
        """
        Get the status bar from the parent window.

        Returns:
            QStatusBar: The status bar from the parent window
        """
        # Try to get status bar from parent (MainWindow)
        if self.parent() and hasattr(self.parent(), "statusBar"):
            return self.parent().statusBar()
        return None

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
        """
        Load the previously saved correction rules using DataManager.
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Dashboard: Using DataManager to load saved correction rules")

        # Get the DataManager instance
        data_manager = DataManager.get_instance()

        # Load rules through the data manager
        rules = data_manager.load_saved_correction_rules()

        if rules:
            logger.info(f"Successfully loaded {len(rules)} correction rules via DataManager")

            # Store the rules locally (redundant but harmless)
            self._correction_rules = rules

            # Set them in the corrector
            self._corrector.set_rules(rules)

            # Update UI elements
            self._action_buttons.set_corrections_loaded(len(rules) > 0)
            self._statistics_widget.set_correction_rules(rules)

            # DataManager will emit the signal to update all components
        else:
            logger.warning("No correction rules were loaded")

    def _on_load_correction_file(self, file_path=None):
        """
        Handle loading a correction file.

        Args:
            file_path: Either a path to a correction file, a list of CorrectionRule objects, or None to show a file dialog
        """
        import logging
        from pathlib import Path

        logger = logging.getLogger(__name__)
        logger.info("Dashboard: Loading correction file")

        # Set processing flag to avoid signal loops
        old_processing_signal = getattr(self, "_processing_signal", False)
        self._processing_signal = True

        try:
            # Get the DataManager instance
            data_manager = DataManager.get_instance()

            # Check if file_path is actually a list of rules
            if isinstance(file_path, list):
                logger.info(f"Received {len(file_path)} correction rules directly")
                correction_rules = file_path

                # Store the rules in the DataManager
                data_manager.set_correction_rules(correction_rules)

            elif file_path is None:
                # If no file path provided, show file dialog
                from PySide6.QtWidgets import QFileDialog
                from pathlib import Path

                # Get last used folder
                last_folder = self._config.get("General", "last_folder", str(Path.home()))

                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Open Correction File",
                    last_folder,
                    "Correction Files (*.csv *.tsv *.txt);;All Files (*.*)",
                )

                if not file_path:
                    logger.info("No correction file selected")
                    return

                # Parse the correction file
                from src.services.file_parser import FileParser

                logger.info(f"Parsing correction file: {file_path}")
                parser = FileParser()
                correction_rules = parser.parse_correction_file(file_path)

                if not correction_rules:
                    logger.warning(f"No correction rules found in {file_path}")
                    return

                # Store rules in the DataManager with file path
                data_manager.set_correction_rules(correction_rules, file_path)

            else:
                # Parse the correction file
                from src.services.file_parser import FileParser

                logger.info(f"Parsing correction file: {file_path}")
                parser = FileParser()
                correction_rules = parser.parse_correction_file(file_path)

                if not correction_rules:
                    logger.warning(f"No correction rules found in {file_path}")
                    return

                # Store rules in the DataManager with file path
                data_manager.set_correction_rules(correction_rules, file_path)

            # Store locally as well for redundancy
            self._correction_rules = correction_rules
            self._current_correction_file = file_path if not isinstance(file_path, list) else None

            # Update UI
            self._action_buttons.set_corrections_loaded(len(correction_rules) > 0)
            self._statistics_widget.set_correction_rules(correction_rules)

            # Show status message
            if self.statusBar():
                self.statusBar().showMessage(
                    f"Loaded {len(correction_rules)} correction rules", 3000
                )

            # Emit our own signal (which will be connected to DataManager)
            logger.info(f"Emitting corrections_loaded signal with {len(correction_rules)} rules")
            self.corrections_loaded.emit(correction_rules)

            # Apply correction rules to entries if available
            if hasattr(self, "_entries") and self._entries:
                self._apply_corrections()

            return correction_rules

        except Exception as e:
            logger.error(f"Error loading correction file: {str(e)}")
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self,
                "Error Loading Correction File",
                f"Failed to load correction file:\n\n{str(e)}",
            )
            return None
        finally:
            # Restore processing flag
            self._processing_signal = old_processing_signal

    def _load_saved_validation_lists(self):
        """
        Load the previously saved validation lists.
        """
        import logging
        import traceback
        from pathlib import Path

        logger = logging.getLogger(__name__)
        logger.info("Dashboard: Loading saved validation lists")

        # Check if we're visible
        logger.info(f"Dashboard widget is visible: {self.isVisible()}")

        lists = {}
        try:
            # Get configuration
            config = ConfigManager()

            # Try multiple config locations for each list type

            # Load player list
            for key in ["player_list", "player_list_path"]:
                for section in ["Validation", "General"]:
                    player_list_path = config.get(section, key, "")
                    if player_list_path:
                        player_path = Path(player_list_path)
                        logger.info(f"Loading player list from: {player_path}")

                        if player_path.exists():
                            logger.info(f"Player list file exists at: {player_path}")
                            try:
                                # Try direct loading method
                                player_list = ValidationList.load_from_file(player_path)
                                if player_list is not None:
                                    lists["player"] = player_list
                                    logger.info(
                                        f"Loaded player list with {len(player_list.items)} items"
                                    )
                                    # Break out of both loops
                                    break
                            except Exception as e:
                                logger.warning(f"Error loading player list: {str(e)}")
                                # Try alternate loading approach
                                with open(player_path, "r", encoding="utf-8") as f:
                                    items = [line.strip() for line in f if line.strip()]
                                    if items:
                                        player_list = ValidationList(
                                            list_type="player", entries=items
                                        )
                                        player_list.file_path = player_path
                                        lists["player"] = player_list
                                        logger.info(
                                            f"Loaded player list with {len(items)} items (alternate method)"
                                        )
                                        break
                if "player" in lists:
                    break

            # Load chest type list
            for key in ["chest_type_list", "chest_type_list_path"]:
                for section in ["Validation", "General"]:
                    chest_type_list_path = config.get(section, key, "")
                    if chest_type_list_path:
                        chest_path = Path(chest_type_list_path)
                        logger.info(f"Loading chest type list from: {chest_path}")

                        if chest_path.exists():
                            logger.info(f"Chest type list file exists at: {chest_path}")
                            try:
                                # Try direct loading method
                                chest_list = ValidationList.load_from_file(chest_path)
                                if chest_list is not None:
                                    lists["chest_type"] = chest_list
                                    logger.info(
                                        f"Loaded chest type list with {len(chest_list.items)} items"
                                    )
                                    # Break out of both loops
                                    break
                            except Exception as e:
                                logger.warning(f"Error loading chest type list: {str(e)}")
                                # Try alternate loading approach
                                with open(chest_path, "r", encoding="utf-8") as f:
                                    items = [line.strip() for line in f if line.strip()]
                                    if items:
                                        chest_list = ValidationList(
                                            list_type="chest_type", entries=items
                                        )
                                        chest_list.file_path = chest_path
                                        lists["chest_type"] = chest_list
                                        logger.info(
                                            f"Loaded chest type list with {len(items)} items (alternate method)"
                                        )
                                        break
                if "chest_type" in lists:
                    break

            # Load source list
            for key in ["source_list", "source_list_path"]:
                for section in ["Validation", "General"]:
                    source_list_path = config.get(section, key, "")
                    if source_list_path:
                        source_path = Path(source_list_path)
                        logger.info(f"Loading source list from: {source_path}")

                        if source_path.exists():
                            logger.info(f"Source list file exists at: {source_path}")
                            try:
                                # Try direct loading method
                                source_list = ValidationList.load_from_file(source_path)
                                if source_list is not None:
                                    lists["source"] = source_list
                                    logger.info(
                                        f"Loaded source list with {len(source_list.items)} items"
                                    )
                                    # Break out of both loops
                                    break
                            except Exception as e:
                                logger.warning(f"Error loading source list: {str(e)}")
                                # Try alternate loading approach
                                with open(source_path, "r", encoding="utf-8") as f:
                                    items = [line.strip() for line in f if line.strip()]
                                    if items:
                                        source_list = ValidationList(
                                            list_type="source", entries=items
                                        )
                                        source_list.file_path = source_path
                                        lists["source"] = source_list
                                        logger.info(
                                            f"Loaded source list with {len(items)} items (alternate method)"
                                        )
                                        break
                if "source" in lists:
                    break

            # Save loaded lists to config
            if lists:
                # Ensure paths are saved in all relevant config sections
                for list_type, validation_list in lists.items():
                    if hasattr(validation_list, "file_path") and validation_list.file_path:
                        file_path_str = str(validation_list.file_path)
                        logger.info(f"Saving {list_type} list path to config: {file_path_str}")
                        config.set("General", f"{list_type}_list_path", file_path_str)
                        config.set("Validation", f"{list_type}_list", file_path_str)

                # Save config changes
                config.save()
                logger.info("Saved validation list paths to config")

                # Store lists locally
                self._validation_lists = lists

                # Emit signal
                logger.info(f"Emitting validation_lists_updated signal with {len(lists)} lists")
                self.validation_lists_updated.emit(lists)

                # Also schedule a delayed re-emit to ensure all components are initialized
                QTimer.singleShot(1000, lambda: self._delayed_emit_validation_lists(lists))
            else:
                logger.warning("No validation lists were loaded")

        except Exception as e:
            logger.error(f"Error loading validation lists: {str(e)}")
            logger.error(traceback.format_exc())

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
            return

        try:
            self._processing_signal = True
            logger = logging.getLogger(__name__)
            logger.info(
                f"Dashboard received correction_rules_updated signal with {len(rules)} rules"
            )

            # Check if rules are already set and unchanged
            if self._correction_rules == rules:
                logger.info("Rules are unchanged, no need to update")
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

            # Make sure the correction manager has the updated rules
            if self._correction_manager is not None:
                logger.info(f"Updating correction manager with {len(rules)} rules")
                self._correction_manager.set_correction_rules(rules)

            # Make sure the file import widget is updated
            if hasattr(self, "_file_import_widget"):
                logger.info(f"Updating file import widget with {len(rules)} rules")
                self._file_import_widget.set_correction_rules(rules)

            # Emit the signal to notify other components
            self.corrections_loaded.emit(rules)

            # Trigger correction if we have entries
            if hasattr(self, "_entries") and self._entries:
                self._apply_corrections()
        except Exception as e:
            logger.error(f"Error in _on_correction_rules_updated: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
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
        # Prevent signal loops
        if self._processing_entries_loaded:
            self._logger.debug("Skipping _on_entries_loaded due to signal loop prevention")
            return

        try:
            self._processing_entries_loaded = True
            self._logger.info(f"Dashboard: Processing {len(entries)} loaded entries")

            # Store the entries
            self._entries = entries

            # Apply corrections if auto-apply is enabled
            config_manager = ConfigManager()
            if config_manager.get_bool("Correction", "auto_apply", fallback=True):
                self._apply_corrections()
            else:
                # Emit entry loaded signal
                self.entries_loaded.emit(entries)

                # Update table view with new entries
                self._table_view.set_entries(entries)

                # Update statistics
                self._statistics_widget.set_entries(entries)

                # Show status message
                if self._status_bar:
                    self._status_bar.showMessage(f"Loaded {len(entries)} entries", 3000)
        except Exception as e:
            self._logger.error(f"Error in _on_entries_loaded: {str(e)}")
            import traceback

            self._logger.error(traceback.format_exc())
        finally:
            self._processing_entries_loaded = False

    @Slot(list)
    def _on_corrections_loaded(self, rules: List[CorrectionRule]):
        """
        Handle corrections loaded event.

        Args:
            rules: List of loaded correction rules
        """
        # Prevent signal loops
        if self._processing_corrections_loaded:
            self._logger.debug("Skipping _on_corrections_loaded due to signal loop prevention")
            return

        try:
            self._processing_corrections_loaded = True
            self._logger.info(f"Dashboard: Processing {len(rules)} loaded correction rules")

            # Store the rules
            self._correction_rules = rules

            # Set them in the corrector
            self._corrector.set_rules(rules)

            # Update UI elements
            self._action_buttons.set_corrections_loaded(len(rules) > 0)
            self._statistics_widget.set_correction_rules(rules)

            # Apply corrections if auto-apply is enabled
            config_manager = ConfigManager()
            if len(self._entries) > 0 and config_manager.get_bool(
                "Correction", "auto_apply", fallback=True
            ):
                self._apply_corrections()

            # Emit corrections loaded signal
            self.corrections_loaded.emit(rules)

            # Show status message
            if self._status_bar:
                self._status_bar.showMessage(f"Loaded {len(rules)} correction rules", 3000)
        except Exception as e:
            self._logger.error(f"Error in _on_corrections_loaded: {str(e)}")
            import traceback

            self._logger.error(traceback.format_exc())
        finally:
            self._processing_corrections_loaded = False

    @Slot(list)
    def _on_corrections_applied(self, entries: List[ChestEntry]):
        """
        Handle corrections applied event.

        Args:
            entries: List of entries with corrections applied
        """
        # Prevent signal loops
        if self._processing_corrections_applied:
            self._logger.debug("Skipping _on_corrections_applied due to signal loop prevention")
            return

        try:
            self._processing_corrections_applied = True
            self._logger.info(
                f"Dashboard: Processing {len(entries)} entries with corrections applied"
            )

            # Store the entries
            self._entries = entries

            # Update table view with corrected entries
            self._table_view.set_entries(entries)

            # Update statistics
            self._statistics_widget.set_entries(entries)

            # Emit entries updated signal
            self.entries_updated.emit(entries)

            # Emit corrections applied signal
            self.corrections_applied.emit(entries)

            # Show status message
            if self._status_bar:
                correction_count = sum(entry.has_corrections for entry in entries)
                self._status_bar.showMessage(
                    f"Applied {correction_count} corrections to {len(entries)} entries", 3000
                )
        except Exception as e:
            self._logger.error(f"Error in _on_corrections_applied: {str(e)}")
            import traceback

            self._logger.error(traceback.format_exc())
        finally:
            self._processing_corrections_applied = False

    @Slot(bool)
    def _on_corrections_enabled_changed(self, enabled: bool):
        """
        Handle corrections enabled changed signal.

        Args:
            enabled: Whether corrections are enabled
        """
        # Update action buttons
        self._action_buttons.set_button_enabled(
            "apply_corrections", enabled and len(self._correction_rules) > 0
        )

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
            self._logger.error(f"Error saving entries: {str(e)}")
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
            self._logger.error(f"Error exporting entries: {str(e)}")
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

            # Apply corrections
            results = self._corrector.apply_corrections(self._entries, self._correction_rules)

            # Count corrections
            correction_count = sum(1 for result in results if result.was_corrected)

            # Only show message if corrections were actually needed and we're not in a signal loop
            if correction_count > 0:
                # Group results by entry for a more meaningful message
                entry_counts = {}
                for result in results:
                    entry_idx = result.entry_index
                    entry_counts[entry_idx] = entry_counts.get(entry_idx, 0) + 1

                entry_count = len(entry_counts)
                QMessageBox.information(
                    self,
                    "Apply Corrections",
                    f"Applied {correction_count} corrections to {entry_count} entries.",
                )

            # Emit signals only if corrections were made
            if correction_count > 0:
                self.entries_updated.emit(self._entries)
                self.corrections_applied.emit(self._entries)

        except Exception as e:
            logger.error(f"Error applying corrections: {str(e)}")
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

    def set_correction_rules(self, rules: List[CorrectionRule]):
        """
        Set the correction rules.

        Args:
            rules: List of correction rules
        """
        self._on_corrections_loaded(rules)

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
            List of entries
        """
        return self._entries

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
        self._correction_manager._tools_tabs.setCurrentIndex(1)

    def _show_correction_rules(self):
        """Show the correction rules tab in the correction manager."""
        # Show correction manager panel
        self._show_correction_manager_panel()

        # Switch to correction rules tab
        self._correction_manager._tools_tabs.setCurrentIndex(0)

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
            self._logger.info(f"Loaded {len(entries)} entries from {file_path}")

            # Show message in status bar
            status_bar = self.statusBar()
            if status_bar:
                status_bar.showMessage(f"Loaded {len(entries)} entries from {file_path}", 5000)

        except Exception as e:
            self._logger.error(f"Error loading text file: {e}")
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
            self._logger.error(f"Error saving output: {e}")
            QMessageBox.critical(self, "Error Saving Output", f"Error: {str(e)}")
