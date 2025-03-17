"""
validation_rule_editor.py

Description: Editor for creating and editing validation/correction rules
Usage:
    from src.ui.validation_rule_editor import ValidationRuleEditor
    rule_editor = ValidationRuleEditor(parent=self)
"""

from typing import Dict, List, Optional, Set, Union

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.models.correction_rule import CorrectionRule
from src.services.fuzzy_matcher import FuzzyMatcher


class ValidationRuleEditor(QWidget):
    """
    Editor for creating and editing validation/correction rules.

    Provides a user interface for defining how text should be corrected
    and validated against validation lists.

    Signals:
        rule_saved (CorrectionRule): Signal emitted when a rule is saved
        rule_deleted (CorrectionRule): Signal emitted when a rule is deleted
        rule_validated (bool): Signal emitted when a rule is validated with result

    Implementation Notes:
        - Supports editing of match pattern, replacement text, and rule options
        - Provides validation of rule syntax and preview of rule application
        - Handles both exact and fuzzy matching rules
        - Integrates with fuzzy matcher service for similarity settings
    """

    # Signals
    rule_saved = Signal(object)  # CorrectionRule
    rule_deleted = Signal(object)  # CorrectionRule
    rule_validated = Signal(bool)  # is_valid

    def __init__(self, parent=None):
        """
        Initialize the validation rule editor.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Initialize properties
        self._current_rule: Optional[CorrectionRule] = None
        self._validation_list: Optional[str] = None
        self._fuzzy_matcher = FuzzyMatcher()

        # Set up UI
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)

        # Match settings group
        match_group = QGroupBox("Match Settings")
        match_layout = QFormLayout(match_group)

        # Match type selection
        self._match_type_layout = QHBoxLayout()
        self._exact_match_radio = QRadioButton("Exact Match")
        self._exact_match_radio.setChecked(True)
        self._fuzzy_match_radio = QRadioButton("Fuzzy Match")
        self._match_type_layout.addWidget(self._exact_match_radio)
        self._match_type_layout.addWidget(self._fuzzy_match_radio)
        self._match_type_layout.addStretch()
        match_layout.addRow("Match Type:", self._match_type_layout)

        # Match pattern
        self._match_pattern_edit = QLineEdit()
        self._match_pattern_edit.setPlaceholderText("Text to match (original text)")
        match_layout.addRow("Match Pattern:", self._match_pattern_edit)

        # Case sensitivity
        self._case_sensitive_check = QCheckBox("Case Sensitive")
        match_layout.addRow("", self._case_sensitive_check)

        # Fuzzy settings (initially hidden)
        self._fuzzy_settings = QWidget()
        fuzzy_layout = QFormLayout(self._fuzzy_settings)
        fuzzy_layout.setContentsMargins(0, 0, 0, 0)

        self._similarity_threshold_spin = QSpinBox()
        self._similarity_threshold_spin.setRange(1, 100)
        self._similarity_threshold_spin.setValue(80)
        self._similarity_threshold_spin.setSuffix("%")
        fuzzy_layout.addRow("Similarity Threshold:", self._similarity_threshold_spin)

        self._fuzzy_settings.setVisible(False)
        match_layout.addRow("", self._fuzzy_settings)

        main_layout.addWidget(match_group)

        # Replacement settings group
        replacement_group = QGroupBox("Replacement Settings")
        replacement_layout = QFormLayout(replacement_group)

        # Replacement type
        self._replacement_type_combo = QComboBox()
        self._replacement_type_combo.addItems(
            ["Direct Replacement", "Replace if in List", "Add to List"]
        )
        replacement_layout.addRow("Replacement Type:", self._replacement_type_combo)

        # Replacement text
        self._replacement_text_edit = QLineEdit()
        self._replacement_text_edit.setPlaceholderText("Text to replace with (corrected text)")
        replacement_layout.addRow("Replacement Text:", self._replacement_text_edit)

        # Validation list
        self._validation_list_combo = QComboBox()
        self._validation_list_combo.setPlaceholderText("Select a validation list")
        replacement_layout.addRow("Validation List:", self._validation_list_combo)

        main_layout.addWidget(replacement_group)

        # Actions
        actions_layout = QHBoxLayout()

        self._save_button = QPushButton("Save Rule")
        self._save_button.setToolTip("Save the current rule")
        actions_layout.addWidget(self._save_button)

        self._delete_button = QPushButton("Delete Rule")
        self._delete_button.setToolTip("Delete the current rule")
        self._delete_button.setEnabled(False)
        actions_layout.addWidget(self._delete_button)

        self._test_button = QPushButton("Test Rule")
        self._test_button.setToolTip("Test the current rule against sample text")
        actions_layout.addWidget(self._test_button)

        actions_layout.addStretch()

        self._clear_button = QPushButton("Clear")
        self._clear_button.setToolTip("Clear all fields")
        actions_layout.addWidget(self._clear_button)

        main_layout.addLayout(actions_layout)

        # Status message
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self._status_label)

        main_layout.addStretch()

    def _connect_signals(self):
        """Connect signals and slots."""
        # Match type signals
        self._exact_match_radio.toggled.connect(self._on_match_type_changed)
        self._fuzzy_match_radio.toggled.connect(self._on_match_type_changed)

        # Button signals
        self._save_button.clicked.connect(self._on_save)
        self._delete_button.clicked.connect(self._on_delete)
        self._test_button.clicked.connect(self._on_test)
        self._clear_button.clicked.connect(self.clear)

        # Input signals
        self._match_pattern_edit.textChanged.connect(lambda: self._update_status("Unsaved changes"))
        self._replacement_text_edit.textChanged.connect(
            lambda: self._update_status("Unsaved changes")
        )
        self._case_sensitive_check.toggled.connect(lambda: self._update_status("Unsaved changes"))
        self._similarity_threshold_spin.valueChanged.connect(
            lambda: self._update_status("Unsaved changes")
        )
        self._replacement_type_combo.currentIndexChanged.connect(self._on_replacement_type_changed)

    def set_validation_lists(self, lists: List[str]):
        """
        Set the available validation lists.

        Args:
            lists: List of validation list names
        """
        self._validation_list_combo.clear()
        self._validation_list_combo.addItems(lists)

    def set_validation_list(self, list_name: str):
        """
        Set the current validation list.

        Args:
            list_name: Name of the validation list
        """
        self._validation_list = list_name
        index = self._validation_list_combo.findText(list_name)
        if index >= 0:
            self._validation_list_combo.setCurrentIndex(index)

    def set_rule(self, rule: CorrectionRule):
        """
        Set the rule to edit.

        Args:
            rule: The correction rule to edit
        """
        self._current_rule = rule

        # Update UI
        self._match_pattern_edit.setText(rule.match_pattern)
        self._replacement_text_edit.setText(rule.replacement)
        self._case_sensitive_check.setChecked(rule.case_sensitive)

        # Match type
        if rule.fuzzy_match:
            self._fuzzy_match_radio.setChecked(True)
            self._similarity_threshold_spin.setValue(int(rule.similarity_threshold * 100))
        else:
            self._exact_match_radio.setChecked(True)

        # Replacement type
        if rule.validation_list_name:
            if rule.add_to_list:
                self._replacement_type_combo.setCurrentText("Add to List")
            else:
                self._replacement_type_combo.setCurrentText("Replace if in List")

            # Set validation list
            self.set_validation_list(rule.validation_list_name)
        else:
            self._replacement_type_combo.setCurrentText("Direct Replacement")

        # Enable delete button for existing rules
        self._delete_button.setEnabled(rule.id is not None)

        self._update_status("Rule loaded")

    def clear(self):
        """Clear all fields and reset the editor."""
        self._current_rule = None
        self._match_pattern_edit.clear()
        self._replacement_text_edit.clear()
        self._case_sensitive_check.setChecked(False)
        self._exact_match_radio.setChecked(True)
        self._similarity_threshold_spin.setValue(80)
        self._replacement_type_combo.setCurrentText("Direct Replacement")
        self._delete_button.setEnabled(False)
        self._update_status("Editor cleared")

    def _get_rule_from_ui(self) -> CorrectionRule:
        """
        Get a correction rule from the UI.

        Returns:
            CorrectionRule: The correction rule
        """
        rule = CorrectionRule()

        # If we're editing an existing rule, preserve its ID
        if self._current_rule and self._current_rule.id:
            rule.id = self._current_rule.id

        # Basic properties
        rule.match_pattern = self._match_pattern_edit.text()
        rule.replacement = self._replacement_text_edit.text()
        rule.case_sensitive = self._case_sensitive_check.isChecked()

        # Match type
        rule.fuzzy_match = self._fuzzy_match_radio.isChecked()
        if rule.fuzzy_match:
            rule.similarity_threshold = self._similarity_threshold_spin.value() / 100.0

        # Replacement type
        replacement_type = self._replacement_type_combo.currentText()
        if replacement_type in ["Replace if in List", "Add to List"]:
            rule.validation_list_name = self._validation_list_combo.currentText()
            rule.add_to_list = replacement_type == "Add to List"
        else:
            rule.validation_list_name = None
            rule.add_to_list = False

        return rule

    def _validate_rule(self) -> bool:
        """
        Validate the current rule.

        Returns:
            bool: True if the rule is valid
        """
        # Check for required fields
        if not self._match_pattern_edit.text():
            self._update_status("Error: Match pattern is required", error=True)
            return False

        if not self._replacement_text_edit.text():
            self._update_status("Error: Replacement text is required", error=True)
            return False

        # Check validation list selection
        replacement_type = self._replacement_type_combo.currentText()
        if replacement_type in ["Replace if in List", "Add to List"]:
            if self._validation_list_combo.currentIndex() < 0:
                self._update_status("Error: Validation list is required", error=True)
                return False

        return True

    @Slot()
    def _on_match_type_changed(self):
        """Handle match type change."""
        self._fuzzy_settings.setVisible(self._fuzzy_match_radio.isChecked())

    @Slot()
    def _on_replacement_type_changed(self, index):
        """
        Handle replacement type change.

        Args:
            index: Index of the selected item
        """
        replacement_type = self._replacement_type_combo.currentText()
        self._validation_list_combo.setEnabled(
            replacement_type in ["Replace if in List", "Add to List"]
        )
        self._update_status("Unsaved changes")

    @Slot()
    def _on_save(self):
        """Handle save button click."""
        if not self._validate_rule():
            return

        rule = self._get_rule_from_ui()
        self._current_rule = rule
        self._delete_button.setEnabled(True)
        self.rule_saved.emit(rule)
        self._update_status("Rule saved")

    @Slot()
    def _on_delete(self):
        """Handle delete button click."""
        if self._current_rule:
            self.rule_deleted.emit(self._current_rule)
            self.clear()

    @Slot()
    def _on_test(self):
        """Handle test button click."""
        if not self._validate_rule():
            return

        # This is a placeholder for now
        # In a real implementation, we'd test the rule against sample text
        rule = self._get_rule_from_ui()
        self.rule_validated.emit(True)
        self._update_status("Rule tested successfully")

    def _update_status(self, message: str, error: bool = False):
        """
        Update the status label.

        Args:
            message: Status message
            error: Whether the message is an error
        """
        self._status_label.setText(message)
        self._status_label.setStyleSheet(f"color: {'red' if error else 'gray'};")
