"""
test_data_display_issue.py

Description: Test script to diagnose issues with data display and correction application
Usage:
    python tests/test_data_display_issue.py
"""

import sys
import os
import logging
from pathlib import Path
import pandas as pd
import traceback
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTableView,
    QSplitter,
    QHeaderView,
)
from PySide6.QtCore import Qt, Signal, Slot, QAbstractTableModel, QModelIndex

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from the project
from src.app_bootstrapper import AppBootstrapper
from src.interfaces.events import EventType, EventHandler, EventData
from src.services.dataframe_store import DataFrameStore
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_correction_service import ICorrectionService
from src.interfaces.i_validation_service import IValidationService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


# Simple table model for debugging
class SimpleTableModel(QAbstractTableModel):
    """A simple table model for displaying DataFrames."""

    def __init__(self, data=None):
        super().__init__()
        self._data = data if data is not None else pd.DataFrame()
        self._columns = self._data.columns.tolist() if not self._data.empty else []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if row < 0 or row >= len(self._data) or col < 0 or col >= len(self._columns):
                return None

            value = self._data.iloc[row, col]
            return str(value)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal and section < len(self._columns):
            return self._columns[section]

        return str(section + 1)

    def set_data(self, data):
        self.beginResetModel()
        self._data = data if data is not None else pd.DataFrame()
        self._columns = self._data.columns.tolist() if not self._data.empty else []
        self.endResetModel()


# Custom entry table model
class EntryTableModel(QAbstractTableModel):
    """Model for displaying entries from the DataStore."""

    def __init__(self, data_store, parent=None):
        """
        Initialize the EntryTableModel with an explicit data store.

        Args:
            data_store: Data store to use
            parent: Parent QObject
        """
        super().__init__(parent)

        # Set up the model with our injected data store
        self._store = data_store
        self._entries_df = pd.DataFrame()
        self._logger = logging.getLogger(__name__)

        # Define which columns to display and in what order
        self._displayed_columns = ["id", "chest_type", "player", "source", "status"]

        # Define human-readable column labels
        self._column_labels = {
            "id": "ID",
            "chest_type": "Chest Type",
            "player": "Player",
            "source": "Source",
            "status": "Status",
        }

        # Subscribe to events
        self._store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)

        # Load initial data
        self.refresh_data()

    def _on_entries_updated(self, event_data):
        """Handle entries updated event."""
        self._logger.debug(f"Model received entries_updated event: {event_data}")
        self.refresh_data()

    def refresh_data(self):
        """Refresh the model data from DataFrameStore."""
        self.beginResetModel()
        self._entries_df = self._store.get_entries()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Return number of rows in the model."""
        if parent.isValid():
            return 0
        return len(self._entries_df)

    def columnCount(self, parent=QModelIndex()):
        """Return number of columns in the model."""
        if parent.isValid():
            return 0
        return len(self._displayed_columns)

    def data(self, index, role=Qt.DisplayRole):
        """Return data for the given index and role."""
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()

            if (
                row < 0
                or row >= len(self._entries_df)
                or col < 0
                or col >= len(self._displayed_columns)
            ):
                return None

            column_name = self._displayed_columns[col]

            if column_name == "id":
                # Get the index value instead of a column value
                return str(self._entries_df.index[row])

            # Handle case where column doesn't exist
            if column_name not in self._entries_df.columns:
                return "N/A"

            value = self._entries_df.iloc[row][column_name]

            # Convert various data types to string
            if pd.isna(value):
                return ""
            elif isinstance(value, list):
                return ", ".join(map(str, value))
            elif isinstance(value, dict):
                return ", ".join(f"{k}={v}" for k, v in value.items())
            else:
                return str(value)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data for the given section, orientation and role."""
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal and section < len(self._displayed_columns):
            column_name = self._displayed_columns[section]
            return self._column_labels.get(column_name, column_name)

        if orientation == Qt.Vertical:
            return str(section + 1)

        return None


# Custom correction rule table model
class CorrectionRuleTableModel(QAbstractTableModel):
    """Model for displaying correction rules from the DataStore."""

    def __init__(self, data_store, parent=None):
        """
        Initialize the CorrectionRuleTableModel with an explicit data store.

        Args:
            data_store: Data store to use
            parent: Parent QObject
        """
        super().__init__(parent)

        # Set up the model with our injected data store
        self._store = data_store
        self._rules_df = pd.DataFrame()
        self._logger = logging.getLogger(__name__)

        # Define which columns to display and in what order
        self._displayed_columns = ["id", "field", "from_text", "to_text", "enabled"]

        # Define human-readable column labels
        self._column_labels = {
            "id": "ID",
            "field": "Field",
            "from_text": "From",
            "to_text": "To",
            "enabled": "Enabled",
        }

        # Subscribe to events
        self._store.subscribe(EventType.CORRECTION_RULES_UPDATED, self._on_rules_updated)

        # Load initial data
        self.refresh_data()

    def _on_rules_updated(self, event_data):
        """Handle correction rules updated event."""
        self._logger.debug(f"Model received correction_rules_updated event: {event_data}")
        self.refresh_data()

    def refresh_data(self):
        """Refresh the model data from DataFrameStore."""
        self.beginResetModel()
        self._rules_df = self._store.get_correction_rules()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Return number of rows in the model."""
        if parent.isValid():
            return 0
        return len(self._rules_df)

    def columnCount(self, parent=QModelIndex()):
        """Return number of columns in the model."""
        if parent.isValid():
            return 0
        return len(self._displayed_columns)

    def data(self, index, role=Qt.DisplayRole):
        """Return data for the given index and role."""
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()

            if (
                row < 0
                or row >= len(self._rules_df)
                or col < 0
                or col >= len(self._displayed_columns)
            ):
                return None

            column_name = self._displayed_columns[col]

            if column_name == "id":
                # Get the index value instead of a column value
                return str(self._rules_df.index[row])

            # Handle case where column doesn't exist
            if column_name not in self._rules_df.columns:
                return "N/A"

            value = self._rules_df.iloc[row][column_name]

            # Convert various data types to string
            if pd.isna(value):
                return ""
            elif isinstance(value, bool):
                return "Yes" if value else "No"
            else:
                return str(value)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data for the given section, orientation and role."""
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal and section < len(self._displayed_columns):
            column_name = self._displayed_columns[section]
            return self._column_labels.get(column_name, column_name)

        if orientation == Qt.Vertical:
            return str(section + 1)

        return None


class TestWindow(QMainWindow):
    """Test window to verify data display and correction application."""

    def __init__(self, service_factory):
        super().__init__()
        self.setWindowTitle("Data Display Test")
        self.setGeometry(100, 100, 1000, 800)

        # Store dependencies
        self._service_factory = service_factory
        self._data_store = service_factory.get_service(IDataStore)
        self._file_service = service_factory.get_service(IFileService)
        self._correction_service = service_factory.get_service(ICorrectionService)
        self._logger = logging.getLogger(__name__)

        self._logger.debug("Services retrieved successfully")
        self._logger.debug(f"DataStore: {self._data_store}")
        self._logger.debug(f"FileService: {self._file_service}")
        self._logger.debug(f"CorrectionService: {self._correction_service}")

        # Setup UI
        self._setup_ui()

        # Connect event handlers
        self._connect_events()

        self._logger.debug("TestWindow initialized successfully")

    def _setup_ui(self):
        """Setup the test window UI components."""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create a splitter for better layout
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)

        # Top panel for controls
        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)
        splitter.addWidget(top_panel)

        # Load Data section
        load_label = QLabel("1. Load Test Data")
        load_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        top_layout.addWidget(load_label)

        self._load_entries_btn = QPushButton("Load Test Entries")
        self._load_rules_btn = QPushButton("Load Test Correction Rules")
        top_layout.addWidget(self._load_entries_btn)
        top_layout.addWidget(self._load_rules_btn)

        # Apply corrections
        apply_label = QLabel("4. Apply Corrections")
        apply_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        top_layout.addWidget(apply_label)

        self._apply_corrections_btn = QPushButton("Apply Corrections")
        top_layout.addWidget(self._apply_corrections_btn)

        # Results
        results_label = QLabel("5. Results")
        results_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        top_layout.addWidget(results_label)

        self._results_label = QLabel("No results yet")
        top_layout.addWidget(self._results_label)

        # Tables panel
        tables_panel = QWidget()
        tables_layout = QVBoxLayout(tables_panel)
        splitter.addWidget(tables_panel)

        # Create internal splitter for tables
        tables_splitter = QSplitter(Qt.Vertical)
        tables_layout.addWidget(tables_splitter)

        # Entries Table
        entries_widget = QWidget()
        entries_layout = QVBoxLayout(entries_widget)
        entries_label = QLabel("2. Entries Table")
        entries_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        entries_layout.addWidget(entries_label)

        self._entries_table = QTableView()
        self._entries_table.setMinimumHeight(200)
        entries_layout.addWidget(self._entries_table)
        tables_splitter.addWidget(entries_widget)

        # Rules Table
        rules_widget = QWidget()
        rules_layout = QVBoxLayout(rules_widget)
        rules_label = QLabel("3. Correction Rules Table")
        rules_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        rules_layout.addWidget(rules_label)

        self._rules_table = QTableView()
        self._rules_table.setMinimumHeight(200)
        rules_layout.addWidget(self._rules_table)
        tables_splitter.addWidget(rules_widget)

        # Set splitter sizes
        splitter.setSizes([200, 600])
        tables_splitter.setSizes([300, 300])

        # Status bar
        self.statusBar().showMessage("Ready")

        # Debug section to show raw data
        debug_label = QLabel("Debug Information")
        debug_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(debug_label)

        self._debug_label = QLabel("No debug information yet")
        self._debug_label.setWordWrap(True)
        layout.addWidget(self._debug_label)

        # Create custom models for visualization
        try:
            # Create models that use our injected data store
            self._entries_model = EntryTableModel(self._data_store)
            self._rules_model = CorrectionRuleTableModel(self._data_store)

            # Set models on tables
            self._entries_table.setModel(self._entries_model)
            self._rules_table.setModel(self._rules_model)

            # Configure table appearance
            for table in [self._entries_table, self._rules_table]:
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                table.verticalHeader().setVisible(True)
                table.setAlternatingRowColors(True)

            self._logger.debug("Custom table models created and connected")

        except Exception as e:
            self._logger.error(f"Error creating table models: {e}")
            self._logger.error(traceback.format_exc())
            self._debug_label.setText(f"Error creating table models: {str(e)}")

            # Fallback to simple models
            self._entries_simple_model = SimpleTableModel()
            self._rules_simple_model = SimpleTableModel()

            # Set the simple models
            self._entries_table.setModel(self._entries_simple_model)
            self._rules_table.setModel(self._rules_simple_model)
            self._logger.debug("Using simple table models as fallback")

    def _connect_events(self):
        """Connect event handlers."""
        try:
            # Button events
            self._load_entries_btn.clicked.connect(self._load_test_entries)
            self._load_rules_btn.clicked.connect(self._load_test_rules)
            self._apply_corrections_btn.clicked.connect(self._apply_corrections)

            # DataStore events
            self._logger.debug("Subscribing to DataStore events...")
            self._data_store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
            self._data_store.subscribe(EventType.CORRECTION_RULES_UPDATED, self._on_rules_updated)
            self._data_store.subscribe(EventType.CORRECTION_APPLIED, self._on_correction_applied)

            self._logger.debug("Events connected successfully")
        except Exception as e:
            self._logger.error(f"Error connecting events: {e}")
            self._logger.error(traceback.format_exc())
            self._debug_label.setText(f"Error connecting events: {str(e)}")

    def _load_test_entries(self):
        """Load test entries into the DataFrameStore."""
        try:
            self._logger.debug("Creating test entries DataFrame...")

            # Create test entries
            entries_data = {
                "chest_type": ["Gold", "Silver", "Bronze", "Rare Dragon Chest", "Elegant Chest"],
                "player": ["Player1", "Player2", "Player3", "Moony", "Sir Met"],
                "source": [
                    "Source1",
                    "Source2",
                    "Source3",
                    "Level 15 epic Crypt",
                    "Level 25 Crypt",
                ],
                "status": ["Pending"] * 5,
                "validation_errors": [[] for _ in range(5)],
                "original_values": [{} for _ in range(5)],
            }
            entries_df = pd.DataFrame(entries_data)

            # Generate IDs
            entries_df["id"] = entries_df.apply(
                lambda row: abs(hash((row["chest_type"], row["player"], row["source"]))) % (10**8),
                axis=1,
            )
            entries_df.set_index("id", inplace=True)

            # Add timestamp
            import datetime

            entries_df["modified_at"] = pd.Timestamp(datetime.datetime.now())

            self._logger.debug(f"Created entries DataFrame with {len(entries_df)} rows")
            self._logger.debug(f"DataFrame columns: {entries_df.columns.tolist()}")
            self._logger.debug(f"First row: {entries_df.iloc[0].to_dict()}")

            # Set entries in the store
            self._logger.debug("Setting entries in DataStore...")
            self._data_store.set_entries(entries_df)
            self.statusBar().showMessage(f"Loaded {len(entries_df)} test entries")
            self._logger.info(f"Loaded {len(entries_df)} test entries")

            # Update debug info
            self._debug_label.setText(
                f"Loaded {len(entries_df)} entries with columns: {entries_df.columns.tolist()}"
            )

        except Exception as e:
            self._logger.error(f"Error loading test entries: {e}")
            self._logger.error(traceback.format_exc())
            self.statusBar().showMessage(f"Error: {str(e)}")
            self._debug_label.setText(f"Error loading entries: {str(e)}\n{traceback.format_exc()}")

    def _load_test_rules(self):
        """Load test correction rules into the DataFrameStore."""
        try:
            self._logger.debug("Creating test correction rules DataFrame...")

            # Create test rules
            rules_data = {
                "field": ["chest_type", "chest_type", "player", "source"],
                "from_text": ["Gold", "Silver", "Moony", "Level 15 epic Crypt"],
                "to_text": ["Gold Chest", "Silver Chest", "MoonLight", "Level 15 Epic Crypt"],
                "enabled": [True, True, True, True],
            }
            rules_df = pd.DataFrame(rules_data)

            self._logger.debug(f"Created rules DataFrame with columns: {rules_df.columns.tolist()}")

            # Generate IDs
            rules_df["id"] = rules_df.apply(
                lambda row: abs(hash((row["from_text"], row["to_text"]))) % (10**8), axis=1
            )
            rules_df.set_index("id", inplace=True)

            # Add timestamp
            import datetime

            rules_df["created_at"] = pd.Timestamp(datetime.datetime.now())
            rules_df["modified_at"] = pd.Timestamp(datetime.datetime.now())

            self._logger.debug(f"Final rules DataFrame with {len(rules_df)} rows")
            self._logger.debug(f"DataFrame columns: {rules_df.columns.tolist()}")
            self._logger.debug(f"First rule: {rules_df.iloc[0].to_dict()}")

            # Set rules in the store
            self._logger.debug("Setting correction rules in DataStore...")
            self._data_store.set_correction_rules(rules_df)
            self.statusBar().showMessage(f"Loaded {len(rules_df)} test correction rules")
            self._logger.info(f"Loaded {len(rules_df)} test correction rules")

            # Update debug info
            self._debug_label.setText(
                f"Loaded {len(rules_df)} rules with columns: {rules_df.columns.tolist()}"
            )

        except Exception as e:
            self._logger.error(f"Error loading test rules: {e}")
            self._logger.error(traceback.format_exc())
            self.statusBar().showMessage(f"Error: {str(e)}")
            self._debug_label.setText(f"Error loading rules: {str(e)}\n{traceback.format_exc()}")

    def _apply_corrections(self):
        """Apply correction rules to entries."""
        try:
            self._logger.debug("Applying corrections...")

            # Log the current state
            entries_df = self._data_store.get_entries()
            rules_df = self._data_store.get_correction_rules()

            self._logger.debug(
                f"Before correction - Entries: {len(entries_df)}, Rules: {len(rules_df)}"
            )
            self._logger.debug(f"Entries columns: {entries_df.columns.tolist()}")
            self._logger.debug(f"Rules columns: {rules_df.columns.tolist()}")

            # Check rule-entry matches before correction
            for _, rule in rules_df.iterrows():
                field = rule["field"]
                from_text = rule["from_text"]
                to_text = rule["to_text"]

                if field in entries_df.columns:
                    matches = (entries_df[field] == from_text).sum()
                    self._logger.debug(
                        f"Before correction - Rule '{from_text}' -> '{to_text}' for field '{field}' matches {matches} entries"
                    )

            # Call the correction service to apply corrections
            self._logger.debug("Calling correction service apply_corrections()...")
            result = self._correction_service.apply_corrections()

            # Log the result
            self._logger.info(f"Correction result: {result}")

            # Check the entries after correction
            entries_after = self._data_store.get_entries()
            self._logger.debug(f"After correction - Entries: {len(entries_after)}")

            # Create a comparison string to show changes
            comparison = []
            for field in ["chest_type", "player", "source"]:
                if field in entries_df.columns and field in entries_after.columns:
                    before_values = entries_df[field].tolist()
                    after_values = entries_after[field].tolist()

                    if before_values != after_values:
                        comparison.append(f"{field}: {before_values} -> {after_values}")

            comparison_text = "\n".join(comparison)

            if "applied" in result and result["applied"] > 0:
                self.statusBar().showMessage(f"Applied {result['applied']} corrections")
                self._results_label.setText(f"Applied {result['applied']} corrections to entries")

                # Update debug info
                self._debug_label.setText(
                    f"Applied {result['applied']} corrections. Changes:\n{comparison_text}"
                )
            else:
                self.statusBar().showMessage("No corrections applied")
                self._results_label.setText("No corrections were applied")

                # Update debug info with detailed information
                details = []
                for _, rule in rules_df.iterrows():
                    field = rule["field"]
                    from_text = rule["from_text"]
                    to_text = rule["to_text"]

                    if field in entries_df.columns:
                        matches = (entries_df[field] == from_text).sum()
                        details.append(
                            f"Rule '{from_text}' -> '{to_text}' for field '{field}' matches {matches} entries"
                        )
                    else:
                        details.append(f"Field '{field}' not found in entries DataFrame")

                details_text = "\n".join(details)
                self._debug_label.setText(f"No corrections applied. Rule details:\n{details_text}")

        except Exception as e:
            self._logger.error(f"Error applying corrections: {e}")
            self._logger.error(traceback.format_exc())
            self.statusBar().showMessage(f"Error: {str(e)}")
            self._debug_label.setText(
                f"Error applying corrections: {str(e)}\n{traceback.format_exc()}"
            )

    def _on_entries_updated(self, event_data):
        """Handle entries updated event."""
        try:
            self._logger.debug(f"Entries updated event received: {event_data}")

            # Refresh the entries model
            try:
                self._entries_model.refresh_data()
                self._logger.debug("Entries model refreshed successfully")
            except Exception as model_error:
                self._logger.error(f"Error refreshing entries model: {model_error}")

                # Fallback to simple model
                entries_df = self._data_store.get_entries()
                if hasattr(self, "_entries_simple_model"):
                    self._entries_simple_model.set_data(entries_df)
                    self._logger.debug("Used simple model fallback for entries table")

            # Get entries from the store
            entries_df = self._data_store.get_entries()
            count = len(entries_df)

            # Update status
            self._logger.info(f"Entries updated: {count} entries")
            self.statusBar().showMessage(f"Entries updated: {count} entries")

            # Update debug info
            self._debug_label.setText(
                f"Entries updated event: {count} entries with columns: {entries_df.columns.tolist()}"
            )

        except Exception as e:
            self._logger.error(f"Error handling entries updated event: {e}")
            self._logger.error(traceback.format_exc())
            self._debug_label.setText(f"Error handling entries update: {str(e)}")

    def _on_rules_updated(self, event_data):
        """Handle correction rules updated event."""
        try:
            self._logger.debug(f"Correction rules updated event received: {event_data}")

            # Refresh the rules model
            try:
                self._rules_model.refresh_data()
                self._logger.debug("Rules model refreshed successfully")
            except Exception as model_error:
                self._logger.error(f"Error refreshing rules model: {model_error}")

                # Fallback to simple model
                rules_df = self._data_store.get_correction_rules()
                if hasattr(self, "_rules_simple_model"):
                    self._rules_simple_model.set_data(rules_df)
                    self._logger.debug("Used simple model fallback for rules table")

            # Get rules from the store
            rules_df = self._data_store.get_correction_rules()
            count = len(rules_df)

            # Update status
            self._logger.info(f"Correction rules updated: {count} rules")
            self.statusBar().showMessage(f"Correction rules updated: {count} rules")

            # Update debug info
            self._debug_label.setText(
                f"Rules updated event: {count} rules with columns: {rules_df.columns.tolist()}"
            )

        except Exception as e:
            self._logger.error(f"Error handling rules updated event: {e}")
            self._logger.error(traceback.format_exc())
            self._debug_label.setText(f"Error handling rules update: {str(e)}")

    def _on_correction_applied(self, event_data):
        """Handle correction applied event."""
        try:
            self._logger.debug(f"Correction applied event received: {event_data}")

            # Extract statistics from event data
            entries_affected = event_data.get("entries_affected", 0)
            count = event_data.get("count", 0)

            # Log the correction
            self._logger.info(
                f"Correction applied: {count} corrections to {entries_affected} entries"
            )

            # Update status
            self.statusBar().showMessage(
                f"Applied {count} corrections to {entries_affected} entries"
            )
            self._results_label.setText(
                f"Applied {count} corrections to {entries_affected} entries"
            )

            # Refresh entries model
            try:
                self._entries_model.refresh_data()
            except Exception:
                # Fallback to simple model
                entries_df = self._data_store.get_entries()
                if hasattr(self, "_entries_simple_model"):
                    self._entries_simple_model.set_data(entries_df)

            # Update debug info
            entries_df = self._data_store.get_entries()
            self._debug_label.setText(
                f"Correction applied event: {count} corrections to {entries_affected} entries\n"
                f"Updated entries: {len(entries_df)} with columns: {entries_df.columns.tolist()}"
            )

        except Exception as e:
            self._logger.error(f"Error handling correction applied event: {e}")
            self._logger.error(traceback.format_exc())
            self._debug_label.setText(f"Error handling correction applied: {str(e)}")


def main():
    """Run the data display test."""
    try:
        logger.info("Starting data display test application")

        # Initialize the application
        app = QApplication.instance() or QApplication(sys.argv)

        # Initialize the bootstrapper
        logger.info("Initializing AppBootstrapper")
        bootstrapper = AppBootstrapper()
        bootstrapper.initialize()

        # Get the service factory
        service_factory = bootstrapper.service_factory
        logger.info("ServiceFactory retrieved from bootstrapper")

        # Create and show the test window
        logger.info("Creating TestWindow")
        window = TestWindow(service_factory)

        logger.info("Showing TestWindow")
        window.show()

        logger.info("Starting application event loop")
        sys.exit(app.exec())

    except Exception as e:
        logger.error(f"Error in main: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    main()
