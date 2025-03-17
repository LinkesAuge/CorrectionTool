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

from PySide6.QtCore import Qt, Signal, Slot
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
from src.services.config_manager import ConfigManager
from src.services.corrector import Corrector
from src.services.file_parser import FileParser
from src.ui.action_button_group import ActionButtonGroup
from src.ui.enhanced_table_view import EnhancedTableView
from src.ui.file_import_widget import FileImportWidget
from src.ui.statistics_widget import StatisticsWidget
from src.ui.validation_status_indicator import ValidationStatusIndicator
from src.ui.correction_manager_panel import CorrectionManagerPanel


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

    def __init__(self, parent=None):
        """
        Initialize the dashboard.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize properties
        self._config = ConfigManager()
        self._file_parser = FileParser()
        self._corrector = Corrector()
        self._entries: List[ChestEntry] = []
        self._correction_rules: List[CorrectionRule] = []
        self._validation_lists = []
        self._corrections_applied_count = 0
        self._validation_errors_count = 0
        self._logger = logging.getLogger(__name__)

        # Add a flag to prevent signal loops
        # IMPORTANT: This flag prevents recursive signal processing which can cause app crashes.
        # All signal handler methods (_on_entries_loaded, _on_corrections_loaded, _on_corrections_applied)
        # must check this flag before processing and set it during processing with proper try/finally
        # blocks to ensure it is always reset. See bugfixing.mdc for details on why this is necessary.
        self._processing_signal = False

        # Set up UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

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
            self._correction_manager.correction_rules_updated.connect(
                self._on_correction_rules_updated
            )
            self._correction_manager.validation_lists_updated.connect(
                self._on_validation_lists_updated
            )
        else:
            self._logger.warning("Correction manager not available for signal connection")

        # Set up initial state
        self._load_saved_correction_rules()
        self._load_saved_validation_lists()

    def _load_saved_correction_rules(self):
        """Load saved correction rules."""
        # Get last correction file from config
        last_correction_file = self._config.get("General", "last_correction_file")
        if last_correction_file and Path(last_correction_file).exists():
            try:
                from src.services.file_parser import FileParser

                parser = FileParser()
                correction_rules = parser.parse_correction_rules(last_correction_file)

                # Set correction rules
                self._correction_manager.set_correction_rules(correction_rules)

                self._logger.info(f"Loaded {len(correction_rules)} saved correction rules")
            except Exception as e:
                self._logger.error(f"Error loading saved correction rules: {e}")
        else:
            self._logger.info("No saved correction rules found")

    def _load_saved_validation_lists(self):
        """Load saved validation lists."""
        # Try to load saved validation lists
        try:
            from src.models.validation_list import ValidationList

            validation_lists = {}

            # Look for default validation lists
            for list_type in ["player", "chest_type", "source"]:
                list_path = self._config.get("General", f"{list_type}_list_path")
                if list_path and Path(list_path).exists():
                    try:
                        validation_list = ValidationList.load_from_file(Path(list_path))
                        validation_lists[list_type] = validation_list
                        self._logger.info(f"Loaded saved {list_type} validation list")
                    except Exception as e:
                        self._logger.error(f"Error loading saved {list_type} validation list: {e}")

            # Set validation lists if any were loaded
            if validation_lists:
                self._correction_manager.set_validation_lists(validation_lists)
        except Exception as e:
            self._logger.error(f"Error loading saved validation lists: {e}")

    @Slot(list)
    def _on_correction_rules_updated(self, rules):
        """
        Handle correction rules updated.

        Args:
            rules: List of correction rules
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Dashboard received correction_rules_updated signal with {len(rules)} rules")

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

        # Make sure the correction manager has the updated rules
        if self._correction_manager is not None:
            # If the correction manager emitted this signal, don't send it back to avoid loops
            if not self._processing_signal:
                logger.info(f"Updating correction manager with {len(rules)} rules")
                self._correction_manager.set_correction_rules(rules)

            # Make the correction manager panel visible
            self._show_correction_rules()
        else:
            logger.warning("Correction manager not available for updating rules")

        # Make sure the file import widget is updated
        if hasattr(self, "_file_import_widget"):
            # If this signal didn't originate from the file import widget, update it
            if not self._processing_signal:
                logger.info(f"Updating file import widget with {len(rules)} rules")
                self._file_import_widget.set_correction_rules(rules)

        # Trigger correction if we have entries
        if hasattr(self, "_entries") and self._entries:
            self._apply_corrections()

    @Slot(dict)
    def _on_validation_lists_updated(self, lists):
        """
        Handle validation lists updated.

        Args:
            lists: Dictionary of validation lists
        """
        # Store the lists for use in validation process
        self._validation_lists = lists

        # Save the current file paths
        for list_type, validation_list in lists.items():
            if validation_list.file_path:
                self._config.set(
                    "General", f"{list_type}_list_path", str(validation_list.file_path)
                )

        # Show message
        self.statusBar().showMessage(f"Validation lists updated: {len(lists)} lists")

        # Trigger validation if we have entries
        if hasattr(self, "_entries") and self._entries:
            self._validate_entries()

    @Slot(list)
    def _on_entries_loaded(self, entries: List[ChestEntry]):
        """
        Handle entries loaded signal.

        Args:
            entries: List of loaded entries
        """
        # Prevent signal loops
        if self._processing_signal:
            return

        try:
            self._processing_signal = True
            self._logger.debug(
                f"Dashboard processing entries_loaded signal with {len(entries)} entries"
            )
            self._entries = entries

            # Update table view
            self._table_view.set_entries(entries)

            # Update statistics widget
            self._statistics_widget.set_entries(entries)

            # Update validation status
            self._validation_status.set_entries(entries)

            # Update action buttons
            self._action_buttons.set_entries_loaded(len(entries) > 0)

            # Forward the signal but only if we're not already processing a signal
            self.entries_loaded.emit(entries)

            # Auto-apply corrections if enabled
            if self._correction_rules:
                # Apply corrections without emitting signals to avoid loops
                self._apply_corrections()
        except Exception as e:
            self._logger.error(f"Error in _on_entries_loaded: {str(e)}")
            import traceback

            self._logger.error(traceback.format_exc())
        finally:
            self._processing_signal = False

    @Slot(list)
    def _on_corrections_loaded(self, rules: List[CorrectionRule]):
        """
        Handle corrections loaded signal.

        Args:
            rules: List of loaded correction rules
        """
        # Prevent signal loops
        if self._processing_signal:
            return

        try:
            self._processing_signal = True
            self._logger.debug(
                f"Dashboard processing corrections_loaded signal with {len(rules)} rules"
            )
            self._correction_rules = rules

            # Update statistics widget
            self._statistics_widget.set_correction_rules(rules)

            # Update action buttons
            self._action_buttons.set_corrections_loaded(len(rules) > 0)

            # Forward the signal
            self.corrections_loaded.emit(rules)

            # Auto-apply corrections if enabled and we have entries
            if self._entries:
                # Apply corrections without emitting signals to avoid loops
                self._apply_corrections()
        except Exception as e:
            self._logger.error(f"Error in _on_corrections_loaded: {str(e)}")
            import traceback

            self._logger.error(traceback.format_exc())
        finally:
            self._processing_signal = False

    @Slot(list)
    def _on_corrections_applied(self, entries: List[ChestEntry]):
        """
        Handle corrections applied signal.

        Args:
            entries: List of entries with corrections applied
        """
        # Prevent signal loops
        if self._processing_signal:
            return

        try:
            self._processing_signal = True
            self._logger.debug(
                f"Dashboard processing corrections_applied signal with {len(entries)} entries"
            )
            self._entries = entries

            # Count corrections applied
            correction_count = sum(
                len(entry.original_values) for entry in entries if entry.has_corrections()
            )
            self._corrections_applied_count = correction_count

            # Update statistics widget
            self._statistics_widget.set_corrections_applied(correction_count)

            # Update table view
            self._table_view.set_entries(entries)

            # Forward the signal
            self.corrections_applied.emit(entries)
            self.entries_updated.emit(entries)
        except Exception as e:
            self._logger.error(f"Error in _on_corrections_applied: {str(e)}")
            import traceback

            self._logger.error(traceback.format_exc())
        finally:
            self._processing_signal = False

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
        if not self._entries:
            QMessageBox.warning(self, "Apply Corrections", "No entries to correct")
            return

        if not self._correction_rules:
            QMessageBox.warning(self, "Apply Corrections", "No correction rules loaded")
            return

        try:
            # Apply corrections using the corrector service
            self._logger.info(
                f"Applying {len(self._correction_rules)} correction rules to {len(self._entries)} entries..."
            )

            # Apply the corrections
            corrected_entries = self._corrector.apply_corrections(
                self._entries, self._correction_rules
            )

            # Get the results
            results = self._corrector.get_last_results()

            # Update statistics
            self._corrections_applied_count = len(results)
            self._statistics_widget.set_corrections_applied(self._corrections_applied_count)

            # Update entries
            self._entries = corrected_entries

            # Update table view
            self._table_view.set_entries(self._entries)

            # Show success message
            correction_count = len(results)
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
            else:
                QMessageBox.information(self, "Apply Corrections", "No corrections were needed.")

            # Emit signals
            self.entries_updated.emit(self._entries)
            self.corrections_applied.emit(self._entries)

        except Exception as e:
            self._logger.error(f"Error applying corrections: {str(e)}")
            QMessageBox.critical(
                self,
                "Correction Error",
                f"An error occurred while applying corrections:\n\n{str(e)}",
            )

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

    def _on_load_correction_file(self, file_path=None):
        """
        Handle loading a correction file.

        Args:
            file_path: Either a path to a correction file, a list of CorrectionRule objects, or None to show a file dialog
        """
        import logging

        logger = logging.getLogger(__name__)

        # Set processing flag to avoid signal loops
        old_processing_signal = getattr(self, "_processing_signal", False)
        self._processing_signal = True

        try:
            # Check if file_path is actually a list of rules
            if isinstance(file_path, list):
                logger.info(f"Received {len(file_path)} correction rules directly")
                correction_rules = file_path
                # We don't have a file path in this case, so we can't update the last folder
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

                # Store current file path
                self._current_correction_file = file_path

                # Update config with last used folder and correction file
                # Make sure file_path is a string
                file_path_str = str(file_path)
                folder_path = str(Path(file_path_str).parent)

                self._config.set("General", "last_folder", folder_path)
                self._config.set("General", "last_correction_file", file_path_str)
                # Also update the FileImportWidget's last_correction_directory setting
                self._config.set("Files", "last_correction_directory", folder_path)
                # Update the default correction rules path
                self._config.set("Paths", "default_correction_rules", file_path_str)
                # Save changes to disk
                self._config.save()
            else:
                # Parse the correction file
                from src.services.file_parser import FileParser

                logger.info(f"Parsing correction file: {file_path}")
                parser = FileParser()
                correction_rules = parser.parse_correction_file(file_path)

                if not correction_rules:
                    logger.warning(f"No correction rules found in {file_path}")
                    return

                # Store current file path
                self._current_correction_file = file_path

                # Update config with last used folder and correction file
                # Make sure file_path is a string
                file_path_str = str(file_path)
                folder_path = str(Path(file_path_str).parent)

                self._config.set("General", "last_folder", folder_path)
                self._config.set("General", "last_correction_file", file_path_str)
                # Also update the FileImportWidget's last_correction_directory setting
                self._config.set("Files", "last_correction_directory", folder_path)
                # Update the default correction rules path
                self._config.set("Paths", "default_correction_rules", file_path_str)
                # Save changes to disk
                self._config.save()

            # Store correction rules locally
            self._correction_rules = correction_rules

            logger.info(f"Loaded {len(correction_rules)} correction rules")

            # Update UI
            self._action_buttons.set_corrections_loaded(len(correction_rules) > 0)

            # Update correction manager if available - use the _correction_manager property
            correction_manager = self._correction_manager
            if correction_manager is not None:
                logger.info(f"Setting {len(correction_rules)} rules in correction manager")
                # Force refresh of the correction rules UI
                correction_manager.set_correction_rules(correction_rules)
                # Ensure the correction manager is visible
                self._show_correction_manager_panel()
            else:
                logger.warning("Correction manager not available, can't update UI")

            # Update file import widget if available
            if hasattr(self, "_file_import_widget") and self._file_import_widget is not None:
                self._file_import_widget.set_correction_rules(correction_rules)

            # Show status message
            if self.statusBar():
                self.statusBar().showMessage(
                    f"Loaded {len(correction_rules)} correction rules", 3000
                )

            # Emit signal for other components to react
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
        finally:
            # Restore processing flag
            self._processing_signal = old_processing_signal

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
