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
from PySide6.QtGui import QIntValidator
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
        super().__init__(parent)
        self._rules: List[CorrectionRule] = []
        self._enabled_rules: Set[Tuple[str, str]] = set()
        self._filter_text = ""

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
        return len(self._rules)

    def columnCount(self, parent=QModelIndex()):
        """
        Get column count.

        Args:
            parent: Parent index

        Returns:
            Number of columns
        """
        return len(self._COLUMNS) - 1  # Exclude Actions column which is handled separately

    def data(self, index, role=Qt.DisplayRole):
        """
        Get data for the given role.

        Args:
            index: Model index
            role: Data role

        Returns:
            Data for the role
        """
        if not index.isValid():
            return None

        rule = self._rules[index.row()]

        if role == Qt.DisplayRole:
            if index.column() == self.COLUMN_FROM:
                return rule.from_text
            if index.column() == self.COLUMN_TO:
                return rule.to_text
            if index.column() == self.COLUMN_CATEGORY:
                return rule.category
            if index.column() == self.COLUMN_TYPE:
                return rule.rule_type
            if index.column() == self.COLUMN_PRIORITY:
                return rule.priority

        elif role == Qt.CheckStateRole:
            if index.column() == self.COLUMN_ENABLED:
                return (
                    Qt.Checked
                    if (rule.from_text, rule.to_text) in self._enabled_rules
                    else Qt.Unchecked
                )

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
        self.beginResetModel()
        self._rules = rules

        # Enable all rules by default
        # Create a unique identifier based on from_text and to_text since CorrectionRule doesn't have an id
        self._enabled_rules = set((rule.from_text, rule.to_text) for rule in rules)

        self.endResetModel()

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
        super().__init__(parent)

        self.rule = rule or CorrectionRule(from_text="", to_text="")

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
        super().__init__(parent)

        self._model = CorrectionRulesModel()
        self.setModel(self._model)

        self._config = ConfigManager()

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Configure table
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)

        # Configure header
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        # Enable editing enabled column
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def set_rules(self, rules: List[CorrectionRule]):
        """
        Set the rules.

        Args:
            rules: List of correction rules
        """
        self._model.set_rules(rules)

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
        dialog = RuleEditDialog(self)
        if dialog.exec():
            category, from_text, to_text, use_regex, priority = dialog.get_values()
            new_rule = CorrectionRule(
                from_text=from_text,
                to_text=to_text,
                enabled=True,
                rule_type="regex" if use_regex else "simple",
                priority=priority,
                category=category,
            )
            self._model.add_rule(new_rule)

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
            self._model.update_rule(rule)

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
            self._model.delete_rule(row)

    def import_rules(self):
        """Import rules from a file."""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Correction Rules",
            str(Path.home()),
            "CSV Files (*.csv);;TSV Files (*.tsv);;Text Files (*.txt);;All Files (*.*)",
        )

        if not file_path:
            return

        # Load rules from file
        from src.services.file_parser import FileParser
        import logging

        parser = FileParser()

        try:
            rules = parser.parse_correction_rules(file_path)
            if rules:
                # Confirm import
                response = QMessageBox.question(
                    self,
                    "Confirm Import",
                    f"Import {len(rules)} rules from {Path(file_path).name}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if response == QMessageBox.Yes:
                    # Add to existing rules
                    current_rules = self._model.get_rules()
                    all_rules = current_rules + rules
                    self._model.set_rules(all_rules)

                    # Show success message
                    QMessageBox.information(
                        self,
                        "Import Successful",
                        f"Imported {len(rules)} rules from {Path(file_path).name}.",
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Import Failed",
                    f"No valid rules found in {Path(file_path).name}. "
                    f"Ensure the file has 'From' and 'To' columns with proper values.",
                )
        except FileNotFoundError:
            QMessageBox.critical(
                self, "File Not Found", f"The file '{Path(file_path).name}' could not be found."
            )
        except ValueError as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Error importing rules: {str(e)}\n\n"
                f"Ensure the file has 'From' and 'To' columns and is properly formatted.",
            )
        except Exception as e:
            logging.exception("Error importing correction rules")
            QMessageBox.critical(
                self,
                "Import Error",
                f"Unexpected error importing rules: {str(e)}\n\n"
                f"The file might be corrupted or in an unsupported format.",
            )

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
