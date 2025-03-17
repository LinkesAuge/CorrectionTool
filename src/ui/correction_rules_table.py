"""
correction_rules_table.py

Description: Table for displaying and managing correction rules
Usage:
    from src.ui.correction_rules_table import CorrectionRulesTable
    table = CorrectionRulesTable()
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from PySide6.QtCore import Qt, Signal, Slot, QSortFilterProxyModel, QModelIndex
from PySide6.QtGui import QIntValidator, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.models.correction_rule import CorrectionRule
from src.services.config_manager import ConfigManager


class CorrectionRulesModel(QSortFilterProxyModel):
    """
    Model for correction rules.

    This model provides the data for the CorrectionRulesTable.

    Attributes:
        _rules: List of correction rules
        _enabled_rules: Set of enabled rule identifiers (from_text, to_text)
    """

    # Column definitions
    COLUMN_ENABLED = 0
    COLUMN_FROM = 1
    COLUMN_TO = 2
    COLUMN_CATEGORY = 3
    COLUMN_TYPE = 4
    COLUMN_PRIORITY = 5
    COLUMN_ACTIONS = 6

    # Columns
    _COLUMNS = ["Enabled", "From", "To", "Category", "Type", "Priority", "Actions"]

    def __init__(self, parent=None):
        """
        Initialize the model.

        Args:
            parent: Parent widget
        """
        import logging

        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing CorrectionRulesModel")

        super().__init__(parent)
        self._rules: List[CorrectionRule] = []
        self._enabled_rules: Set[Tuple[str, str]] = set()
        self._filter_text = ""

        # Create a dummy source model (required for QSortFilterProxyModel)
        self._source_model = QStandardItemModel(self)
        self.setSourceModel(self._source_model)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Get header data.

        Args:
            section: Section index
            orientation: Header orientation
            role: Data role

        Returns:
            Header data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self._COLUMNS):
                return self._COLUMNS[section]
        return None

    def rowCount(self, parent=QModelIndex()):
        """
        Get row count.

        Args:
            parent: Parent index

        Returns:
            Number of rows
        """
        count = len(self._rules)
        self.logger.debug(f"rowCount called, returning {count}")

        # Important: this is needed for QSortFilterProxyModel
        # We must override the source model's rowCount
        if parent.isValid():
            return 0

        return count

    def columnCount(self, parent=QModelIndex()):
        """
        Get column count.

        Args:
            parent: Parent index

        Returns:
            Number of columns
        """
        return len(self._COLUMNS)  # Include all columns, including Actions

    def data(self, index, role=Qt.DisplayRole):
        """
        Get data for the given role.

        Args:
            index: Model index
            role: Data role

        Returns:
            Data for the role
        """
        import logging

        logger = logging.getLogger(__name__)

        if not index.isValid():
            return None

        if index.row() >= len(self._rules):
            logger.warning(f"Invalid row index: {index.row()}, max: {len(self._rules) - 1}")
            return None

        # Get the rule at this index
        rule = self._rules[index.row()]

        if role == Qt.DisplayRole:
            if index.column() == self.COLUMN_FROM:
                return rule.from_text
            elif index.column() == self.COLUMN_TO:
                return rule.to_text
            elif index.column() == self.COLUMN_CATEGORY:
                return rule.category
            elif index.column() == self.COLUMN_TYPE:
                return rule.rule_type
            elif index.column() == self.COLUMN_PRIORITY:
                return str(rule.priority)  # Convert to string for display
            elif index.column() == self.COLUMN_ACTIONS:
                return "Edit/Delete"  # Placeholder for actions

        elif role == Qt.CheckStateRole:
            if index.column() == self.COLUMN_ENABLED:
                return (
                    Qt.Checked
                    if (rule.from_text, rule.to_text) in self._enabled_rules
                    else Qt.Unchecked
                )

        # Add support for text alignment
        elif role == Qt.TextAlignmentRole:
            if index.column() in [self.COLUMN_PRIORITY]:
                # Center numeric values
                return Qt.AlignCenter
            else:
                # Left align text
                return Qt.AlignLeft | Qt.AlignVCenter

        # Add support for tooltips
        elif role == Qt.ToolTipRole:
            if index.column() == self.COLUMN_FROM:
                return f"Original text: {rule.from_text}"
            elif index.column() == self.COLUMN_TO:
                return f"Corrected text: {rule.to_text}"
            elif index.column() == self.COLUMN_CATEGORY:
                return f"Category: {rule.category}"
            elif index.column() == self.COLUMN_TYPE:
                return f"Rule type: {rule.rule_type}"
            elif index.column() == self.COLUMN_PRIORITY:
                return f"Priority: {rule.priority}"
            elif index.column() == self.COLUMN_ACTIONS:
                return "Click to edit or delete this rule"

        return None

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        """
        Set data for the given role.

        Args:
            index: Model index
            value: New value
            role: Data role

        Returns:
            True if successful, False otherwise
        """
        if not index.isValid():
            return False

        if index.row() >= len(self._rules):
            return False

        if role == Qt.CheckStateRole and index.column() == self.COLUMN_ENABLED:
            rule = self._rules[index.row()]
            if value == Qt.Checked:
                self._enabled_rules.add((rule.from_text, rule.to_text))
            else:
                self._enabled_rules.discard((rule.from_text, rule.to_text))
            self.dataChanged.emit(index, index)
            return True

        # Other data changes are handled by the delegate
        return False

    def flags(self, index):
        """
        Get flags for index.

        Args:
            index: Model index

        Returns:
            Item flags
        """
        if not index.isValid():
            return Qt.NoItemFlags

        if index.column() == self.COLUMN_ENABLED:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def set_rules(self, rules: List[CorrectionRule]):
        """
        Set the rules.

        Args:
            rules: List of correction rules
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"CorrectionRulesModel.set_rules called with {len(rules)} rules")

        # Check for empty from_text or to_text
        invalid_rules = [
            i for i, r in enumerate(rules) if not r.from_text.strip() or not r.to_text.strip()
        ]
        if invalid_rules:
            logger.warning(
                f"Found {len(invalid_rules)} rules with empty from_text or to_text at indices: {invalid_rules}"
            )

        self.beginResetModel()
        self._rules = rules

        # Enable all rules by default
        # Create a unique identifier based on from_text and to_text since CorrectionRule doesn't have an id
        self._enabled_rules = set((rule.from_text, rule.to_text) for rule in rules)

        # Clear and reset the source model
        self._source_model.clear()
        self._source_model.setColumnCount(len(self._COLUMNS))
        self._source_model.setRowCount(len(rules))

        # Set column headers in source model
        for col, header in enumerate(self._COLUMNS):
            self._source_model.setHeaderData(col, Qt.Horizontal, header, Qt.DisplayRole)

        # Populate source model with data for better proxy integration
        from PySide6.QtGui import QStandardItem

        for row, rule in enumerate(rules):
            # Just need to create empty items to ensure proper row handling
            for col in range(len(self._COLUMNS)):
                self._source_model.setItem(row, col, QStandardItem())

        self.endResetModel()

        # Log some rules for debugging
        for i, rule in enumerate(rules[:5]):
            logger.info(
                f"Rule {i} after set: {rule.from_text} -> {rule.to_text} (category: {rule.category})"
            )

        # Notify view that data has changed
        self.layoutChanged.emit()

    def get_rules(self) -> List[CorrectionRule]:
        """
        Get the rules.

        Returns:
            List of correction rules
        """
        return self._rules

    def add_rule(self, rule: CorrectionRule):
        """
        Add a rule to the model.

        Args:
            rule: Correction rule to add
        """
        self.beginInsertRows(QModelIndex(), len(self._rules), len(self._rules))
        self._rules.append(rule)
        # Enable by default
        self._enabled_rules.add((rule.from_text, rule.to_text))
        self.endInsertRows()

    def update_rule(self, rule: CorrectionRule):
        """
        Update a rule.

        Args:
            rule: Correction rule to update
        """
        for i, existing_rule in enumerate(self._rules):
            # Compare based on from_text and to_text instead of id
            if (existing_rule.from_text, existing_rule.to_text) == (rule.from_text, rule.to_text):
                # Update the rule
                self._rules[i] = rule
                self.dataChanged.emit(self.index(i, 0), self.index(i, self.columnCount() - 1))
                break

    def delete_rule(self, index: int):
        """
        Delete a rule.

        Args:
            index: Index of rule to delete
        """
        if 0 <= index < len(self._rules):
            rule = self._rules[index]
            self.beginRemoveRows(QModelIndex(), index, index)
            self._rules.pop(index)
            self._enabled_rules.discard((rule.from_text, rule.to_text))
            self.endRemoveRows()

    def set_rule_enabled(self, rule_id: Tuple[str, str], enabled: bool):
        """
        Set whether a rule is enabled.

        Args:
            rule_id: Tuple of (from_text, to_text) identifying the rule
            enabled: Whether rule is enabled
        """
        if enabled:
            self._enabled_rules.add(rule_id)
        else:
            self._enabled_rules.discard(rule_id)

        # Update the view
        for i, rule in enumerate(self._rules):
            if (rule.from_text, rule.to_text) == rule_id:
                self.dataChanged.emit(self.index(i, 0), self.index(i, 0))
                break

    def set_all_rules_enabled(self, enabled: bool):
        """
        Set whether all rules are enabled.

        Args:
            enabled: Whether all rules are enabled
        """
        if enabled:
            self._enabled_rules = set((rule.from_text, rule.to_text) for rule in self._rules)
        else:
            self._enabled_rules.clear()

        # Update the view
        if self._rules:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self._rules) - 1, 0))

    def filterAcceptsRow(self, source_row, source_parent):
        """
        Check if a row should be included in filtered results.

        Args:
            source_row: Row index in source model
            source_parent: Parent index in source model

        Returns:
            Whether row should be included
        """
        if not self._filter_text:
            return True

        # Make sure we don't go out of bounds
        if source_row >= len(self._rules):
            return False

        rule = self._rules[source_row]

        # Check if filter matches any field
        return (
            self._filter_text.lower() in rule.from_text.lower()
            or self._filter_text.lower() in rule.to_text.lower()
            or self._filter_text.lower() in rule.category.lower()
            or self._filter_text.lower() in rule.rule_type.lower()
        )

    def filter_rules(self, text: str):
        """
        Filter rules by text.

        Args:
            text: Filter text
        """
        self._filter_text = text
        self.invalidateFilter()

    def remove_rule(self, index: int):
        """
        Remove a rule from the model.

        Args:
            index: Rule index
        """
        if index < 0 or index >= len(self._rules):
            return

        self.beginRemoveRows(QModelIndex(), index, index)
        rule = self._rules.pop(index)
        self._enabled_rules.discard((rule.from_text, rule.to_text))
        self.endRemoveRows()

    def toggle_rule(self, index: int):
        """
        Toggle a rule's enabled state.

        Args:
            index: Rule index
        """
        if index < 0 or index >= len(self._rules):
            return

        rule = self._rules[index]
        rule_id = (rule.from_text, rule.to_text)
        if rule_id in self._enabled_rules:
            self._enabled_rules.discard(rule_id)
        else:
            self._enabled_rules.add(rule_id)

        model_index = self.index(index, self.COLUMN_ENABLED)
        self.dataChanged.emit(model_index, model_index)

    def toggle_all_rules(self, enable: bool):
        """
        Toggle all rules' enabled state.

        Args:
            enable: Whether to enable or disable all rules
        """
        if enable:
            self._enabled_rules = set((rule.from_text, rule.to_text) for rule in self._rules)
        else:
            self._enabled_rules.clear()

        self.dataChanged.emit(
            self.index(0, self.COLUMN_ENABLED),
            self.index(len(self._rules) - 1, self.COLUMN_ENABLED),
        )

    def mapToSource(self, proxyIndex):
        """
        Map a proxy index to a source index.

        Args:
            proxyIndex: Index in the proxy model

        Returns:
            Corresponding index in the source model
        """
        if not proxyIndex.isValid():
            return QModelIndex()

        # Create source index with same row/column
        return self.sourceModel().index(proxyIndex.row(), proxyIndex.column())

    def mapFromSource(self, sourceIndex):
        """
        Map a source index to a proxy index.

        Args:
            sourceIndex: Index in the source model

        Returns:
            Corresponding index in the proxy model
        """
        if not sourceIndex.isValid():
            return QModelIndex()

        # Create proxy index with same row/column
        return self.createIndex(sourceIndex.row(), sourceIndex.column())

    def index(self, row, column, parent=QModelIndex()):
        """
        Create a model index for the given row and column.

        Args:
            row: Row index
            column: Column index
            parent: Parent index

        Returns:
            Model index
        """
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        return self.createIndex(row, column, None)


class RuleEditDialog(QDialog):
    """
    Dialog for editing a correction rule.
    """

    def __init__(self, rule: Optional[CorrectionRule] = None, parent=None):
        """
        Initialize the dialog.

        Args:
            rule: Rule to edit, or None for a new rule
            parent: Parent widget
        """
        import logging

        self.logger = logging.getLogger(__name__)

        super().__init__(parent)

        self.rule = rule or CorrectionRule(from_text="", to_text="")
        self.logger.info(f"Editing rule: {self.rule.from_text} -> {self.rule.to_text}")

        self.setWindowTitle("Edit Correction Rule" if rule else "New Correction Rule")
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Form layout for fields
        form_layout = QFormLayout()

        # Original text
        self._from_text_edit = QLineEdit(self.rule.from_text)
        form_layout.addRow("From:", self._from_text_edit)

        # Corrected text
        self._to_text_edit = QLineEdit(self.rule.to_text)
        form_layout.addRow("To:", self._to_text_edit)

        # Category
        self._category_combo = QComboBox()
        self._category_combo.addItems(["general", "chest", "player", "source"])
        self._category_combo.setCurrentText(self.rule.category)
        form_layout.addRow("Category:", self._category_combo)

        # Rule type
        self._rule_type_combo = QComboBox()
        self._rule_type_combo.addItems(
            [
                CorrectionRule.EXACT,
                CorrectionRule.EXACT_IGNORE_CASE,
                CorrectionRule.CONTAINS,
                CorrectionRule.CONTAINS_IGNORE_CASE,
                CorrectionRule.FUZZY,
            ]
        )
        self._rule_type_combo.setCurrentText(self.rule.rule_type)
        form_layout.addRow("Rule Type:", self._rule_type_combo)

        # Priority
        self._priority_edit = QLineEdit(str(self.rule.priority))
        self._priority_edit.setValidator(QIntValidator(0, 100))
        form_layout.addRow("Priority:", self._priority_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        """Handle dialog acceptance."""
        # Validate fields
        from_text = self._from_text_edit.text().strip()
        to_text = self._to_text_edit.text().strip()
        category = self._category_combo.currentText()
        rule_type = self._rule_type_combo.currentText()

        try:
            priority = int(self._priority_edit.text())
        except ValueError:
            priority = 0

        if not from_text:
            QMessageBox.warning(self, "Validation Error", "From text cannot be empty.")
            return

        # Update rule
        self.rule.from_text = from_text
        self.rule.to_text = to_text
        self.rule.category = category  # type: ignore
        self.rule.rule_type = rule_type  # type: ignore
        self.rule.priority = priority

        self.logger.info(
            f"Rule accepted: {self.rule.from_text} -> {self.rule.to_text} (category: {self.rule.category})"
        )

        super().accept()


class CorrectionRulesTable(QTableView):
    """
    Table for displaying and managing correction rules.

    Attributes:
        _model: Model for correction rules
        _config: ConfigManager instance
    """

    def __init__(self, parent=None):
        """
        Initialize the table.

        Args:
            parent: Parent widget
        """
        import logging

        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing CorrectionRulesTable")

        super().__init__(parent)

        self._model = CorrectionRulesModel()
        self.setModel(self._model)

        self._config = ConfigManager()

        # Track the current file path
        self._current_file_path = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Configure table
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setShowGrid(True)
        self.setWordWrap(True)

        # Make table cells more readable
        self.verticalHeader().setDefaultSectionSize(30)  # Height of rows

        # Configure header
        header = self.horizontalHeader()
        header.setStretchLastSection(True)

        # Set column widths
        self.setColumnWidth(0, 50)  # Enabled (checkbox)
        self.setColumnWidth(1, 150)  # From text
        self.setColumnWidth(2, 150)  # To text
        self.setColumnWidth(3, 80)  # Category
        self.setColumnWidth(4, 80)  # Rule type
        self.setColumnWidth(5, 50)  # Priority

        # Enable editing enabled column
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Connect model signals to refresh view
        self._model.dataChanged.connect(self._on_data_changed)
        self._model.modelReset.connect(self._on_model_reset)
        self._model.layoutChanged.connect(self._on_layout_changed)

    def _on_data_changed(self, topLeft, bottomRight, roles=None):
        """Handle model data changed."""
        self.logger.debug(
            f"Data changed from {topLeft.row()},{topLeft.column()} to {bottomRight.row()},{bottomRight.column()}"
        )
        self.viewport().update()

    def _on_model_reset(self):
        """Handle model reset."""
        self.logger.debug("Model reset")
        self.viewport().update()

    def _on_layout_changed(self):
        """Handle model layout changed."""
        self.logger.debug("Layout changed")
        self.viewport().update()

    def set_rules(self, rules: List[CorrectionRule]):
        """
        Set the rules.

        Args:
            rules: List of correction rules
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"CorrectionRulesTable.set_rules called with {len(rules)} rules")

        # Log a few rules for debugging
        for i, rule in enumerate(rules[:5]):
            logger.info(
                f"Table Rule {i}: {rule.from_text} -> {rule.to_text} (category: {rule.category})"
            )

        # Apply the rules to the model
        self._model.set_rules(rules)

        # Force update the view
        self.reset()
        # Use viewport update instead of self.update()
        self.viewport().update()

        # Update column widths and appearance
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

        # Log current model state
        logger.info(
            f"Model now has {self._model.rowCount()} rows and {self._model.columnCount()} columns"
        )

    def get_rules(self) -> List[CorrectionRule]:
        """
        Get the rules.

        Returns:
            List of correction rules
        """
        return self._model.get_rules()

    @Slot()
    def add_rule(self):
        """Add a new rule to the table."""
        dialog = RuleEditDialog(parent=self)
        if dialog.exec():
            rule = dialog.rule
            self.logger.info(f"Adding new rule: {rule.from_text} -> {rule.to_text}")
            self._model.add_rule(rule)
            # Update the display
            self.viewport().update()

    def edit_rule(self, row: int):
        """
        Edit a rule.

        Args:
            row: Index of rule to edit
        """
        if row < 0 or row >= len(self._model.get_rules()):
            return

        rule = self._model.get_rules()[row]
        dialog = RuleEditDialog(rule, parent=self)
        if dialog.exec():
            self.logger.info(f"Edited rule: {rule.from_text} -> {rule.to_text}")
            self._model.update_rule(rule)
            # Update the display
            self.viewport().update()

    def delete_rule(self, row: int):
        """
        Delete a rule.

        Args:
            row: Index of rule to delete
        """
        if row < 0 or row >= len(self._model.get_rules()):
            return

        # Confirm deletion
        response = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this rule?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if response == QMessageBox.Yes:
            self.logger.info(f"Deleting rule at row {row}")
            self._model.delete_rule(row)
            # Update the display
            self.viewport().update()

    def import_rules(self, file_path=None, skip_confirmation=False):
        """
        Import rules from a file.

        Args:
            file_path: Optional path to the file to import. If None, a file dialog will be shown.
            skip_confirmation: If True, skip the confirmation dialog and import directly.

        Returns:
            List of imported rules, or None if import was cancelled or failed.
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Starting import_rules process")

        # If no file path provided, show file dialog
        if file_path is None:
            from PySide6.QtWidgets import QFileDialog
            from pathlib import Path
            from src.services.config_manager import ConfigManager

            config = ConfigManager()
            last_dir = config.get("General", "last_folder", str(Path.home()))

            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Correction Rules",
                last_dir,
                "Correction Files (*.csv *.tsv *.txt);;All Files (*.*)",
            )

            if not file_path:
                logger.info("No file selected for import")
                return None

        try:
            # Parse the file
            from src.services.file_parser import FileParser

            parser = FileParser()
            imported_rules = parser.parse_correction_file(file_path)

            if not imported_rules:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self, "Import Error", "No valid correction rules found in the file."
                )
                logger.warning(f"No valid rules found in {file_path}")
                return None

            # Save the file path configuration
            from src.services.config_manager import ConfigManager
            from pathlib import Path

            config = ConfigManager()
            folder_path = str(Path(file_path).parent)
            config.set("General", "last_folder", folder_path)
            config.set("Files", "last_correction_directory", folder_path)
            config.set("General", "last_correction_file", file_path)
            config.set("Paths", "default_correction_rules", file_path)
            config.save()

            # Emit the signal with the file path
            self.file_path_changed.emit(file_path)

            # If skip_confirmation is True, skip confirmation and replace all rules
            if skip_confirmation:
                logger.info(f"Replacing all rules with {len(imported_rules)} imported rules")

                # Replace existing rules
                self._model.set_rules(imported_rules)

                # Show success message
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Successfully imported {len(imported_rules)} rules.",
                )

                logger.info(f"Successfully imported {len(imported_rules)} rules")
                return imported_rules

            # Skip confirmation if false, ask user what to do
            from PySide6.QtWidgets import QMessageBox

            # Get existing rules
            current_rules = self._model.get_rules()

            if current_rules:
                # Ask user if they want to replace or append
                response = QMessageBox.question(
                    self,
                    "Import Rules",
                    f"Found {len(imported_rules)} rules in the file. Do you want to replace existing rules or append?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes,
                )

                if response == QMessageBox.StandardButton.Cancel:
                    logger.info("Import cancelled by user")
                    return None

                if response == QMessageBox.StandardButton.Yes:
                    # Replace existing rules
                    logger.info(
                        f"Replacing {len(current_rules)} rules with {len(imported_rules)} imported rules"
                    )
                    all_rules = imported_rules
                else:
                    # Append to existing rules
                    logger.info(
                        f"Appending {len(imported_rules)} rules to {len(current_rules)} existing rules"
                    )
                    all_rules = current_rules + imported_rules
            else:
                # No existing rules, just set the imported rules
                logger.info(f"Setting {len(imported_rules)} imported rules (no existing rules)")
                all_rules = imported_rules

            # Set the rules in the model
            self._model.set_rules(all_rules)

            # Force update display
            logger.info("Forcing view update")
            self.reset()
            self.viewport().update()
            self.resizeColumnsToContents()
            self.resizeRowsToContents()

            # Show success message
            QMessageBox.information(
                self,
                "Import Successful",
                f"Successfully imported {len(imported_rules)} rules.",
            )

            logger.info(f"Successfully imported {len(imported_rules)} rules")
            return all_rules

        except FileNotFoundError:
            from PySide6.QtWidgets import QMessageBox

            logger.error(f"File not found: {file_path}")
            QMessageBox.critical(self, "Import Error", f"File not found: {file_path}")
            return None
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            logger.error(f"Error importing rules: {str(e)}")
            QMessageBox.critical(
                self, "Import Error", f"An error occurred while importing rules:\n\n{str(e)}"
            )
            return None

    def export_rules(self):
        """Export rules to a file."""
        # Get rules
        rules = self._model.get_rules()
        if not rules:
            QMessageBox.warning(self, "No Rules", "There are no rules to export.")
            return

        # Open file dialog
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Correction Rules",
            str(Path.home() / "correction_rules.csv"),
            "CSV Files (*.csv);;TSV Files (*.tsv);;Text Files (*.txt);;All Files (*.*)",
        )

        if not file_path:
            return

        # Ensure file has proper extension based on selected filter
        file_path = Path(file_path)
        if selected_filter == "CSV Files (*.csv)" and not str(file_path).lower().endswith(".csv"):
            file_path = Path(str(file_path) + ".csv")
        elif selected_filter == "TSV Files (*.tsv)" and not str(file_path).lower().endswith(".tsv"):
            file_path = Path(str(file_path) + ".tsv")
        elif selected_filter == "Text Files (*.txt)" and not str(file_path).lower().endswith(
            ".txt"
        ):
            file_path = Path(str(file_path) + ".txt")

        # Save rules to file
        from src.services.file_parser import FileParser
        import logging

        parser = FileParser()

        try:
            parser.save_rules_to_file(rules, file_path)

            # Show success message
            QMessageBox.information(
                self, "Export Successful", f"Exported {len(rules)} rules to {file_path.name}."
            )
        except Exception as e:
            logging.exception("Error exporting correction rules")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting rules: {str(e)}\n\n"
                f"Please try a different location or file format.",
            )

    def filter_rules(self, text: str):
        """
        Filter rules by text.

        Args:
            text: Filter text
        """
        self._model.filter_rules(text)

    def set_all_rules_enabled(self, enabled: bool):
        """
        Set whether all rules are enabled.

        Args:
            enabled: Whether all rules are enabled
        """
        self._model.set_all_rules_enabled(enabled)

    def create_rule_from_entry(self, original: str, corrected: str, category: str):
        """
        Create a new rule from entry data.

        Args:
            original: Original text
            corrected: Corrected text
            category: Rule category (chest, player, source, general)
        """
        # Create the rule
        new_rule = CorrectionRule(
            from_text=original,
            to_text=corrected,
            enabled=True,
            rule_type="simple",
            priority=10,
            category=category,
        )

        # Add to rules list
        self._model.add_rule(new_rule)

        # Update the model to reflect changes
        self._model.set_rules(self._model.get_rules())

        # Select the new rule
        last_row = len(self._model.get_rules()) - 1
        self.selectRow(last_row)

        # Emit the rules updated signal
        self.rules_updated.emit(self._model.get_rules())

    def update(self):
        """Override update to ensure viewport is updated properly."""
        self.viewport().update()
        # Don't call QTableView.update(self) as it requires arguments

    def reset(self):
        """Override reset to ensure the table is properly reset."""
        import logging

        logger = logging.getLogger(__name__)
        logger.debug("Resetting table view")
        super().reset()

        # Force a data refresh
        self.model().layoutChanged.emit()

        self.viewport().update()
        # Make sure headers are visible
        self.horizontalHeader().setVisible(True)
        self.verticalHeader().setVisible(True)

    # Add this signal definition to the class (under the existing signals at around line 648)
    file_path_changed = Signal(str)  # Signal to notify when a file path has been loaded/imported
