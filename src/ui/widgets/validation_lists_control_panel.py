"""
validation_lists_control_panel.py

Description: A unified control panel for managing validation lists
Usage:
    from src.ui.widgets.validation_lists_control_panel import ValidationListsControlPanel
    control_panel = ValidationListsControlPanel(validation_lists_dict, config_manager, data_store)
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models.validation_list import ValidationList
from src.ui.validation_list_widget import ValidationListWidget
from src.interfaces import IConfigManager, IDataStore


class ValidationListsControlPanel(QWidget):
    """
    A unified control panel for managing validation lists.

    This panel provides controls for performing operations on multiple validation lists
    at once, such as importing/exporting all lists, finding duplicates, etc.

    Signals:
        lists_updated: Emitted when any list is updated through this control panel

    Attributes:
        _validation_lists: Dictionary of validation list widgets
        _config_manager: Configuration manager
        _data_store: Data store
    """

    # Signal emitted when any list is updated
    lists_updated = Signal(dict)  # Dict of validation lists

    def __init__(
        self,
        validation_lists: Dict[str, ValidationListWidget],
        config_manager: IConfigManager,
        data_store: IDataStore,
        parent: Optional[QWidget] = None,
    ):
        """
        Initialize the control panel.

        Args:
            validation_lists: Dictionary of validation list widgets
            config_manager: Configuration manager
            data_store: Data store
            parent: Parent widget
        """
        super().__init__(parent)

        self._validation_lists = validation_lists
        self._config_manager = config_manager
        self._data_store = data_store

        self._setup_ui()
        self._connect_signals()
        self._update_statistics()

    def _setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)

        # Control buttons layout
        buttons_layout = QHBoxLayout()

        # Import/Export group
        import_export_group = QGroupBox("Import/Export")
        import_export_layout = QHBoxLayout(import_export_group)

        self._import_all_button = QPushButton("Import All")
        self._export_all_button = QPushButton("Export All")

        import_export_layout.addWidget(self._import_all_button)
        import_export_layout.addWidget(self._export_all_button)

        # Tools group
        tools_group = QGroupBox("Tools")
        tools_layout = QHBoxLayout(tools_group)

        self._find_duplicates_button = QPushButton("Find Duplicates")
        self._normalize_case_button = QPushButton("Normalize Case")

        tools_layout.addWidget(self._find_duplicates_button)
        tools_layout.addWidget(self._normalize_case_button)

        # Search group
        search_group = QGroupBox("Search")
        search_layout = QHBoxLayout(search_group)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search in all lists...")
        self._search_button = QPushButton("Search")
        self._clear_search_button = QPushButton("Clear")

        search_layout.addWidget(self._search_edit)
        search_layout.addWidget(self._search_button)
        search_layout.addWidget(self._clear_search_button)

        # Add groups to buttons layout
        buttons_layout.addWidget(import_export_group, 1)
        buttons_layout.addWidget(tools_group, 1)
        buttons_layout.addWidget(search_group, 2)

        # Checkboxes for selecting which lists to operate on
        selection_layout = QHBoxLayout()

        self._player_checkbox = QCheckBox("Players")
        self._player_checkbox.setChecked(True)
        self._player_count_label = QLabel("Players: 0")

        self._chest_type_checkbox = QCheckBox("Chest Types")
        self._chest_type_checkbox.setChecked(True)
        self._chest_type_count_label = QLabel("Chest Types: 0")

        self._source_checkbox = QCheckBox("Sources")
        self._source_checkbox.setChecked(True)
        self._source_count_label = QLabel("Sources: 0")

        self._total_count_label = QLabel("Total Items: 0")
        self._total_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        selection_layout.addWidget(self._player_checkbox)
        selection_layout.addWidget(self._player_count_label)
        selection_layout.addSpacing(20)
        selection_layout.addWidget(self._chest_type_checkbox)
        selection_layout.addWidget(self._chest_type_count_label)
        selection_layout.addSpacing(20)
        selection_layout.addWidget(self._source_checkbox)
        selection_layout.addWidget(self._source_count_label)
        selection_layout.addStretch(1)
        selection_layout.addWidget(self._total_count_label)

        # Add all layouts to main layout
        main_layout.addLayout(buttons_layout)
        main_layout.addLayout(selection_layout)

    def _connect_signals(self):
        """Connect signals to slots."""
        # Button signals
        self._import_all_button.clicked.connect(self._on_import_all)
        self._export_all_button.clicked.connect(self._on_export_all)
        self._find_duplicates_button.clicked.connect(self._on_find_duplicates)
        self._normalize_case_button.clicked.connect(self._on_normalize_case)
        self._search_button.clicked.connect(self._on_search)
        self._clear_search_button.clicked.connect(self._on_clear_search)

        # Connect validation list widget signals
        for name, widget in self._validation_lists.items():
            widget.list_updated.connect(self._on_list_updated)

        # Checkbox signals for count updates
        self._player_checkbox.toggled.connect(self._update_statistics)
        self._chest_type_checkbox.toggled.connect(self._update_statistics)
        self._source_checkbox.toggled.connect(self._update_statistics)

        # Search box return key
        self._search_edit.returnPressed.connect(self._on_search)

    def _update_statistics(self):
        """Update the statistics labels with counts from the validation lists."""
        total_count = 0

        # Player count
        player_count = 0
        if "player" in self._validation_lists:
            validation_list = self._validation_lists["player"].get_list()
            if hasattr(validation_list, "entries"):
                # It's a ValidationList object
                player_count = len(validation_list.entries)
            elif hasattr(validation_list, "shape"):
                # It's a DataFrame
                player_count = validation_list.shape[0]
            else:
                # Try basic length calculation
                try:
                    player_count = len(validation_list)
                except (TypeError, ValueError):
                    logging.getLogger(__name__).error(
                        f"Couldn't get count of validation list of type {type(validation_list)}"
                    )
                    player_count = 0

            self._player_count_label.setText(f"Players: {player_count}")
            if self._player_checkbox.isChecked():
                total_count += player_count

        # Chest type count
        chest_type_count = 0
        if "chest_type" in self._validation_lists:
            validation_list = self._validation_lists["chest_type"].get_list()
            if hasattr(validation_list, "entries"):
                # It's a ValidationList object
                chest_type_count = len(validation_list.entries)
            elif hasattr(validation_list, "shape"):
                # It's a DataFrame
                chest_type_count = validation_list.shape[0]
            else:
                # Try basic length calculation
                try:
                    chest_type_count = len(validation_list)
                except (TypeError, ValueError):
                    logging.getLogger(__name__).error(
                        f"Couldn't get count of validation list of type {type(validation_list)}"
                    )
                    chest_type_count = 0

            self._chest_type_count_label.setText(f"Chest Types: {chest_type_count}")
            if self._chest_type_checkbox.isChecked():
                total_count += chest_type_count

        # Source count
        source_count = 0
        if "source" in self._validation_lists:
            validation_list = self._validation_lists["source"].get_list()
            if hasattr(validation_list, "entries"):
                # It's a ValidationList object
                source_count = len(validation_list.entries)
            elif hasattr(validation_list, "shape"):
                # It's a DataFrame
                source_count = validation_list.shape[0]
            else:
                # Try basic length calculation
                try:
                    source_count = len(validation_list)
                except (TypeError, ValueError):
                    logging.getLogger(__name__).error(
                        f"Couldn't get count of validation list of type {type(validation_list)}"
                    )
                    source_count = 0

            self._source_count_label.setText(f"Sources: {source_count}")
            if self._source_checkbox.isChecked():
                total_count += source_count

        # Total count
        self._total_count_label.setText(f"Total Items: {total_count}")

    def _get_selected_lists(self) -> Dict[str, ValidationListWidget]:
        """
        Get the currently selected validation lists.

        Returns:
            Dictionary of selected validation list widgets
        """
        selected_lists = {}

        if self._player_checkbox.isChecked() and "player" in self._validation_lists:
            selected_lists["player"] = self._validation_lists["player"]

        if self._chest_type_checkbox.isChecked() and "chest_type" in self._validation_lists:
            selected_lists["chest_type"] = self._validation_lists["chest_type"]

        if self._source_checkbox.isChecked() and "source" in self._validation_lists:
            selected_lists["source"] = self._validation_lists["source"]

        return selected_lists

    @Slot()
    def _on_import_all(self):
        """Handle import all button click."""
        # Get the selected lists
        selected_lists = self._get_selected_lists()

        if not selected_lists:
            QMessageBox.warning(
                self, "No Lists Selected", "Please select at least one list to import."
            )
            return

        # Get the directory containing the validation list files
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Validation Lists Directory",
            self._config_manager.get_path("validation_dir") or str(Path.home()),
            QFileDialog.ShowDirsOnly,
        )

        if not directory:
            return

        # Keep track of imported lists
        imported_count = 0
        success_messages = []
        error_messages = []

        try:
            # Import each selected list
            for list_type, widget in selected_lists.items():
                file_path = os.path.join(directory, f"{list_type}_list.txt")

                if not os.path.exists(file_path):
                    error_messages.append(f"File not found: {file_path}")
                    continue

                try:
                    # Load the list
                    imported_list = ValidationList.load_from_file(file_path, list_type=list_type)

                    if imported_list.entries:
                        # Update the widget with the imported list
                        widget.set_list(imported_list)

                        # Update success messages
                        imported_count += 1
                        success_messages.append(
                            f"Imported {len(imported_list.entries)} items into {list_type} list."
                        )
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error importing {list_type} list: {str(e)}", exc_info=True)
                    error_messages.append(f"Error importing {list_type} list: {str(e)}")

            # Update config with the validation directory
            self._config_manager.set_path("validation_dir", directory)

            # Show results
            message = "\n".join(success_messages)
            if error_messages:
                message += "\n\nErrors:\n" + "\n".join(error_messages)

            if imported_count > 0:
                QMessageBox.information(self, "Import Results", message)
            else:
                QMessageBox.warning(self, "Import Failed", message or "No lists were imported.")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in import all: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Import Error", f"An unexpected error occurred: {str(e)}")

    @Slot()
    def _on_export_all(self):
        """Handle export all button click."""
        # Get the selected lists
        selected_lists = self._get_selected_lists()

        if not selected_lists:
            QMessageBox.warning(
                self, "No Lists Selected", "Please select at least one list to export."
            )
            return

        # Check if any lists are empty
        empty_lists = [
            list_type
            for list_type, widget in selected_lists.items()
            if not widget.get_list().entries
        ]

        if empty_lists:
            empty_names = ", ".join(empty_lists)
            response = QMessageBox.question(
                self,
                "Empty Lists",
                f"The following lists are empty: {empty_names}\n\nDo you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if response == QMessageBox.No:
                return

        # Get the directory to export to
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            self._config_manager.get_path("validation_dir") or str(Path.home()),
            QFileDialog.ShowDirsOnly,
        )

        if not directory:
            return

        # Keep track of exported lists
        exported_count = 0
        success_messages = []
        error_messages = []

        try:
            # Export each selected list
            for list_type, widget in selected_lists.items():
                validation_list = widget.get_list()

                if not validation_list.entries:
                    success_messages.append(f"Skipped empty {list_type} list.")
                    continue

                file_path = os.path.join(directory, f"{list_type}_list.txt")

                try:
                    # Save the list
                    with open(file_path, "w", encoding="utf-8") as f:
                        for item in validation_list.entries:
                            f.write(f"{item}\n")

                    # Update success messages
                    exported_count += 1
                    success_messages.append(
                        f"Exported {len(validation_list.entries)} items from {list_type} list."
                    )
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error exporting {list_type} list: {str(e)}", exc_info=True)
                    error_messages.append(f"Error exporting {list_type} list: {str(e)}")

            # Show results
            message = "\n".join(success_messages)
            if error_messages:
                message += "\n\nErrors:\n" + "\n".join(error_messages)

            if exported_count > 0:
                QMessageBox.information(self, "Export Results", message)
            else:
                QMessageBox.warning(self, "Export Failed", message or "No lists were exported.")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error in export all: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"An unexpected error occurred: {str(e)}")

    @Slot()
    def _on_find_duplicates(self):
        """Find duplicate entries within and across validation lists."""
        # Get the selected lists
        selected_lists = self._get_selected_lists()

        if not selected_lists:
            QMessageBox.warning(
                self,
                "No Lists Selected",
                "Please select at least one list to check for duplicates.",
            )
            return

        # Check for duplicates
        within_duplicates = {}  # Duplicates within a list
        cross_duplicates = set()  # Duplicates across lists
        all_entries = {}  # All entries across all lists for cross-duplicate checking

        # First pass: find duplicates within each list
        for list_type, widget in selected_lists.items():
            entries = widget.get_list().entries
            seen = set()
            duplicates = set()

            for entry in entries:
                if entry in seen:
                    duplicates.add(entry)
                else:
                    seen.add(entry)

                # Track entry for cross-list duplicate checking
                if entry not in all_entries:
                    all_entries[entry] = [list_type]
                else:
                    all_entries[entry].append(list_type)
                    cross_duplicates.add(entry)

            if duplicates:
                within_duplicates[list_type] = sorted(duplicates)

        # Create results message
        if not within_duplicates and not cross_duplicates:
            QMessageBox.information(self, "No Duplicates", "No duplicate entries were found.")
            return

        # Build detailed message
        message = ""

        # Duplicates within lists
        if within_duplicates:
            message += "Duplicates within lists:\n\n"
            for list_type, duplicates in within_duplicates.items():
                message += f"{list_type.capitalize()} list: {', '.join(duplicates)}\n"

        # Duplicates across lists
        if cross_duplicates:
            if message:
                message += "\n"
            message += "Entries appearing in multiple lists:\n\n"
            for entry in sorted(cross_duplicates):
                list_types = all_entries[entry]
                message += f"{entry}: {', '.join(list_types)}\n"

        QMessageBox.information(self, "Duplicate Entries", message)

    @Slot()
    def _on_normalize_case(self):
        """Normalize the case of entries in validation lists."""
        # Get the selected lists
        selected_lists = self._get_selected_lists()

        if not selected_lists:
            QMessageBox.warning(
                self, "No Lists Selected", "Please select at least one list to normalize case."
            )
            return

        # Confirm action
        response = QMessageBox.question(
            self,
            "Confirm Normalize Case",
            "This will capitalize the first letter of each word in all selected lists.\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if response == QMessageBox.No:
            return

        # Normalize case
        total_changed = 0
        changes_by_list = {}

        for list_type, widget in selected_lists.items():
            validation_list = widget.get_list()
            original_entries = validation_list.entries.copy()
            changed_count = 0

            # Create new normalized entries
            normalized_entries = []
            for entry in original_entries:
                normalized = entry.title()
                normalized_entries.append(normalized)
                if normalized != entry:
                    changed_count += 1

            # Update validation list
            validation_list.entries = normalized_entries
            widget.set_list(validation_list)

            # Track changes
            if changed_count > 0:
                total_changed += changed_count
                changes_by_list[list_type] = changed_count

        # Show results
        if total_changed > 0:
            message = "Case normalization completed:\n\n"
            for list_type, count in changes_by_list.items():
                message += f"{list_type.capitalize()} list: {count} entries changed\n"

            QMessageBox.information(self, "Case Normalization Complete", message)
        else:
            QMessageBox.information(
                self, "No Changes", "All entries already had proper capitalization."
            )

    @Slot()
    def _on_search(self):
        """Search for entries in validation lists."""
        # Get the search term
        search_term = self._search_edit.text().strip()

        if not search_term:
            QMessageBox.warning(self, "Empty Search", "Please enter a search term.")
            return

        # Get the selected lists
        selected_lists = self._get_selected_lists()

        if not selected_lists:
            QMessageBox.warning(
                self, "No Lists Selected", "Please select at least one list to search."
            )
            return

        # Search for matches
        matches = {}
        total_matches = 0

        for list_type, widget in selected_lists.items():
            entries = widget.get_list().entries
            list_matches = []

            for entry in entries:
                if search_term.lower() in entry.lower():
                    list_matches.append(entry)

            if list_matches:
                matches[list_type] = list_matches
                total_matches += len(list_matches)

        # Show results
        if matches:
            message = f"Found {total_matches} matches for '{search_term}':\n\n"
            for list_type, list_matches in matches.items():
                message += f"{list_type.capitalize()} list ({len(list_matches)} matches):\n"
                message += ", ".join(list_matches) + "\n\n"

            QMessageBox.information(self, "Search Results", message)
        else:
            QMessageBox.information(self, "No Matches", f"No matches found for '{search_term}'.")

    @Slot()
    def _on_clear_search(self):
        """Clear the search field."""
        self._search_edit.clear()

    @Slot(object)
    def _on_list_updated(self, validation_list):
        """
        Handle updates to validation lists.

        Args:
            validation_list: The updated ValidationList
        """
        # Update statistics
        self._update_statistics()

        # Emit lists_updated signal with dictionary of all lists
        lists_dict = {}
        for name, widget in self._validation_lists.items():
            lists_dict[name] = widget.get_list()

        self.lists_updated.emit(lists_dict)
