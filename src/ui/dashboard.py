"""
dashboard.py

Description: Main dashboard widget that integrates all UI components
Usage:
    from src.ui.dashboard import Dashboard
    dashboard = Dashboard(parent=self)
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QMessageBox,
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

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

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

        # Set initial sizes (30% left, 70% right)
        self._splitter.setSizes([300, 700])

        # Add splitter to main layout
        main_layout.addWidget(self._splitter)

    def _connect_signals(self):
        """Connect signals to slots."""
        # Connect file import widget signals
        self._file_import_widget.entries_loaded.connect(self._on_entries_loaded)
        self._file_import_widget.corrections_loaded.connect(self._on_corrections_loaded)
        self._file_import_widget.corrections_applied.connect(self._on_corrections_applied)
        self._file_import_widget.corrections_enabled_changed.connect(
            self._on_corrections_enabled_changed
        )

        # Connect action button signals
        self._action_buttons.save_requested.connect(self._on_save_requested)
        self._action_buttons.export_requested.connect(self._on_export_requested)
        self._action_buttons.apply_corrections_requested.connect(self._apply_corrections)
        self._action_buttons.settings_requested.connect(self._on_settings_requested)

        # Connect table view signals
        self._table_view.entry_selected.connect(self._on_entry_selected)
        self._table_view.entry_edited.connect(self._on_entry_edited)

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
