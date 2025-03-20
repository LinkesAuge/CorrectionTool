"""
ui_adapter_test.py

Description: Test script for UI adapters connecting DataFrameStore to QTableView
Usage: python ui_adapter_test.py
"""

import sys
import logging
import pandas as pd
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableView,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QHeaderView,
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from dataframe_store_test import DataFrameStore, EventType

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataFrameTableModel(QAbstractTableModel):
    """TableModel that connects to a DataFrame."""

    def __init__(self, data=None):
        super().__init__()
        self._data = pd.DataFrame() if data is None else data
        self._display_columns = self._data.columns.tolist()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._display_columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            col_name = self._display_columns[index.column()]
            value = self._data.iloc[index.row()][col_name]
            return str(value)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self._display_columns[section])
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(section + 1)
        return None

    def set_data(self, data):
        """Update the model data."""
        self.beginResetModel()
        self._data = data
        self._display_columns = self._data.columns.tolist()
        self.endResetModel()
        logger.info(f"DataFrameTableModel updated with {len(data)} rows")


class EntryTableAdapter:
    """Adapter to connect DataFrameStore to a table view for entries."""

    def __init__(self, table_view, store=None):
        """
        Initialize the adapter.

        Args:
            table_view: QTableView instance
            store: DataFrameStore instance (if None, gets singleton)
        """
        self._table_view = table_view
        self._store = store if store else DataFrameStore.get_instance()
        self._model = DataFrameTableModel()
        self._table_view.setModel(self._model)

        # Set up columns
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Connect to store events
        self._store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)

        # Initial data load
        self.refresh()

        logger.info("EntryTableAdapter initialized")

    def _on_entries_updated(self, data):
        """Handle entries updated event."""
        self.refresh()

    def refresh(self):
        """Refresh the table view from the store."""
        entries_df = self._store.get_entries()
        self._model.set_data(entries_df)
        logger.info(f"EntryTableAdapter refreshed with {len(entries_df)} entries")


class CorrectionRuleTableAdapter:
    """Adapter to connect DataFrameStore to a table view for correction rules."""

    def __init__(self, table_view, store=None):
        """
        Initialize the adapter.

        Args:
            table_view: QTableView instance
            store: DataFrameStore instance (if None, gets singleton)
        """
        self._table_view = table_view
        self._store = store if store else DataFrameStore.get_instance()
        self._model = DataFrameTableModel()
        self._table_view.setModel(self._model)

        # Set up columns
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Connect to store events
        self._store.subscribe(EventType.CORRECTION_RULES_UPDATED, self._on_rules_updated)

        # Initial data load
        self.refresh()

        logger.info("CorrectionRuleTableAdapter initialized")

    def _on_rules_updated(self, data):
        """Handle correction rules updated event."""
        self.refresh()

    def refresh(self):
        """Refresh the table view from the store."""
        rules_df = self._store.get_correction_rules()
        self._model.set_data(rules_df)
        logger.info(f"CorrectionRuleTableAdapter refreshed with {len(rules_df)} rules")


class AdapterTestWindow(QMainWindow):
    """Test window for data adapters."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI Adapter Test")
        self.resize(1000, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)

        # Create top row layout
        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)

        # Create entry table view
        self.entry_table = QTableView()
        top_layout.addWidget(self.entry_table)

        # Create correction rule table view
        self.correction_table = QTableView()
        top_layout.addWidget(self.correction_table)

        # Create button row
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        # Create load data button
        self.load_entries_btn = QPushButton("Load Test Entries")
        self.load_entries_btn.clicked.connect(self.load_test_entries)
        button_layout.addWidget(self.load_entries_btn)

        # Create load rules button
        self.load_rules_btn = QPushButton("Load Test Rules")
        self.load_rules_btn.clicked.connect(self.load_test_rules)
        button_layout.addWidget(self.load_rules_btn)

        # Create apply corrections button
        self.apply_corrections_btn = QPushButton("Apply Corrections")
        self.apply_corrections_btn.clicked.connect(self.apply_corrections)
        button_layout.addWidget(self.apply_corrections_btn)

        # Create status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Get the DataFrameStore instance
        self.store = DataFrameStore.get_instance()

        # Create adapters
        self.entry_adapter = EntryTableAdapter(self.entry_table, self.store)
        self.rule_adapter = CorrectionRuleTableAdapter(self.correction_table, self.store)

        # Initialize with data
        self.load_test_entries()
        self.load_test_rules()

        logger.info("AdapterTestWindow initialized")

    def load_test_entries(self):
        """Load test entries into the DataFrameStore."""
        entries_data = {
            "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "chest_type": ["Gold", "Silver", "Bronze"],
            "player": ["Player1", "Player2", "Player3"],
            "source": ["Source1", "Source2", "Source3"],
            "status": ["Pending", "Pending", "Pending"],
        }
        entries_df = pd.DataFrame(entries_data)

        self.store.set_entries(entries_df)
        self.status_label.setText(f"Loaded {len(entries_df)} test entries")
        logger.info(f"Loaded {len(entries_df)} test entries into DataFrameStore")

    def load_test_rules(self):
        """Load test correction rules into the DataFrameStore."""
        rules_data = {
            "from_text": ["Gold", "Silver", "Bronze"],
            "to_text": ["Gold Chest", "Silver Chest", "Bronze Chest"],
            "category": ["chest_type", "chest_type", "chest_type"],
            "enabled": [True, True, True],
        }
        rules_df = pd.DataFrame(rules_data)

        self.store.set_correction_rules(rules_df)
        self.status_label.setText(f"Loaded {len(rules_df)} test correction rules")
        logger.info(f"Loaded {len(rules_df)} test correction rules into DataFrameStore")

    def apply_corrections(self):
        """Apply corrections to entries based on rules."""
        # Get the data
        entries_df = self.store.get_entries()
        rules_df = self.store.get_correction_rules()

        # Apply corrections
        entries_df_modified = entries_df.copy()

        # Only apply rules where enabled is True
        active_rules = rules_df[rules_df["enabled"] == True]

        # Apply each rule
        for _, rule in active_rules.iterrows():
            if rule["category"] == "chest_type":
                # Apply to chest_type column
                entries_df_modified.loc[
                    entries_df_modified["chest_type"] == rule["from_text"], "chest_type"
                ] = rule["to_text"]
            elif rule["category"] == "player":
                # Apply to player column
                entries_df_modified.loc[
                    entries_df_modified["player"] == rule["from_text"], "player"
                ] = rule["to_text"]
            elif rule["category"] == "source":
                # Apply to source column
                entries_df_modified.loc[
                    entries_df_modified["source"] == rule["from_text"], "source"
                ] = rule["to_text"]

        # Mark all as valid
        entries_df_modified["status"] = "Valid"

        # Update the store
        self.store.set_entries(entries_df_modified)

        # Update status
        self.status_label.setText("Applied corrections")
        logger.info("Applied corrections to entries")


def main():
    """Main function."""
    app = QApplication(sys.argv)
    window = AdapterTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
