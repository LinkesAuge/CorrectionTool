"""
ui.adapters package for the Chest Tracker Correction Tool.

This package contains adapter classes that connect the data layer with UI components.
"""

# Import key classes for easier access
from src.ui.adapters.entry_table_adapter import EntryTableAdapter, EntryTableModel
from src.ui.adapters.validation_list_combo_adapter import ValidationListComboAdapter
from src.ui.adapters.correction_rule_table_adapter import CorrectionRuleTableAdapter
from src.ui.adapters.filter_adapter import FilterAdapter

__all__ = [
    "EntryTableAdapter",
    "ValidationListComboAdapter",
    "CorrectionRuleTableAdapter",
    "EntryTableModel",
    "FilterAdapter",
]
