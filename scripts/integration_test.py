"""
integration_test.py

Description: Integration test for the refactored MainWindow with real data
Usage: python integration_test.py [sample_data.txt]
"""

import sys
import logging
import os
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import dataframe_store components to avoid circular imports
from dataframe_store_test import DataFrameStore, EventType

# Import UI adapter components
from ui_adapter_test import DataFrameTableModel, EntryTableAdapter, CorrectionRuleTableAdapter

# Import PySide6
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableView,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QFileDialog,
    QDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, Slot


class FileService:
    """Mock FileService for loading and saving data files."""

    def __init__(self, store):
        """
        Initialize the FileService.

        Args:
            store: DataFrameStore instance
        """
        self._store = store
        self._logger = logging.getLogger(__name__ + ".FileService")

    def load_entries_from_file(self, file_path):
        """
        Load entries from a file.

        Args:
            file_path: Path to the file to load

        Returns:
            Number of entries loaded
        """
        try:
            self._logger.info(f"Loading entries from {file_path}")

            # Read the file
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Process the file content
            entries = []
            current_entry = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                if line.startswith("From:"):
                    # Player line - if we have an active entry, add the player
                    if current_entry:
                        current_entry["player"] = line[5:].strip()
                elif line.startswith("Source:"):
                    # Source line - if we have an active entry, add the source
                    if current_entry:
                        current_entry["source"] = line[7:].strip()
                else:
                    # This is a chest type line, which means it's the start of a new entry
                    # If we have an active entry, add it to our entries list
                    if current_entry:
                        entries.append(current_entry)

                    # Start a new entry
                    current_entry = {
                        "chest_type": line,
                        "player": "",
                        "source": "",
                        "status": "Pending",
                        "date": pd.Timestamp.now().strftime("%Y-%m-%d"),
                        "validation_errors": [],
                        "original_values": {},
                    }

            # Add the last entry if there is one
            if current_entry:
                entries.append(current_entry)

            # Convert to DataFrame
            if entries:
                entries_df = pd.DataFrame(entries)

                # Ensure object columns are properly initialized
                if "validation_errors" not in entries_df.columns:
                    entries_df["validation_errors"] = [[] for _ in range(len(entries_df))]
                if "original_values" not in entries_df.columns:
                    entries_df["original_values"] = [{} for _ in range(len(entries_df))]
            else:
                # Create an empty DataFrame with the expected columns
                entries_df = pd.DataFrame(
                    columns=[
                        "chest_type",
                        "player",
                        "source",
                        "status",
                        "date",
                        "validation_errors",
                        "original_values",
                    ]
                )

            # Set in the store
            self._store.set_entries(entries_df, "file_load")

            self._logger.info(f"Loaded {len(entries)} entries from {file_path}")
            return len(entries)

        except Exception as e:
            self._logger.error(f"Error loading entries from {file_path}: {str(e)}")
            raise

    def save_entries_to_file(self, file_path):
        """
        Save entries to a file.

        Args:
            file_path: Path to save the file to

        Returns:
            Number of entries saved
        """
        try:
            self._logger.info(f"Saving entries to {file_path}")

            # Get entries from the store
            entries_df = self._store.get_entries()

            # Skip if no entries
            if entries_df.empty:
                self._logger.info("No entries to save")
                return 0

            # Convert to the required format
            with open(file_path, "w", encoding="utf-8") as f:
                for _, entry in entries_df.iterrows():
                    f.write(f"{entry['chest_type']}\n")
                    f.write(f"From: {entry['player']}\n")
                    if entry["source"]:
                        f.write(f"Source: {entry['source']}\n")

            self._logger.info(f"Saved {len(entries_df)} entries to {file_path}")
            return len(entries_df)

        except Exception as e:
            self._logger.error(f"Error saving entries to {file_path}: {str(e)}")
            raise

    def load_correction_rules_from_csv(self, file_path):
        """
        Load correction rules from a CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            Number of rules loaded
        """
        try:
            self._logger.info(f"Loading correction rules from {file_path}")

            # Read the raw file first to inspect the format
            with open(file_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                # Check if file has headers
                has_header = "From" in first_line or "from_text" in first_line

            # Try to detect the separator
            if "," in first_line and ";" in first_line:
                # Complex case, possibly mixed separators or quoted values with commas
                sep = ";"  # Default to semicolon
            elif "," in first_line:
                sep = ","
            elif ";" in first_line:
                sep = ";"
            else:
                # If no obvious separator, default to comma
                sep = ","

            # First try standard parsing
            try:
                rules_df = pd.read_csv(file_path, sep=sep)
            except Exception as e1:
                self._logger.warning(f"Standard parsing failed: {str(e1)}")
                try:
                    # Try with alternative separator
                    alt_sep = "," if sep == ";" else ";"
                    rules_df = pd.read_csv(file_path, sep=alt_sep)
                except Exception as e2:
                    self._logger.warning(f"Alternative separator parsing failed: {str(e2)}")

                    # If all fails, try manual parsing
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    # Try to manually parse the file
                    data = []
                    for i, line in enumerate(lines):
                        if i == 0 and has_header:
                            # This is the header line, skip it
                            continue

                        line = line.strip()
                        if not line:
                            continue

                        # Check for different possible separators
                        if ";" in line:
                            parts = line.split(";")
                        elif "," in line:
                            parts = line.split(",")
                        else:
                            # No obvious separator, just use the whole line as from_text
                            parts = [line, line, "general"]

                        # Ensure we have at least from_text and to_text
                        if len(parts) >= 2:
                            row = {
                                "from_text": parts[0].strip(),
                                "to_text": parts[1].strip(),
                                "category": parts[2].strip() if len(parts) > 2 else "general",
                                "enabled": True,
                                "timestamp": pd.Timestamp.now(),
                            }
                            data.append(row)

                    # Create DataFrame from parsed data
                    if data:
                        rules_df = pd.DataFrame(data)
                    else:
                        # If still no data, create empty DataFrame with required columns
                        rules_df = pd.DataFrame(
                            columns=["from_text", "to_text", "category", "enabled", "timestamp"]
                        )

            # Handle column renaming if the standard names aren't found
            if "from_text" not in rules_df.columns:
                # Look for alternative column names
                if "From" in rules_df.columns:
                    rules_df = rules_df.rename(columns={"From": "from_text"})
                elif any("from" in col.lower() for col in rules_df.columns):
                    # Find the column that contains 'from' in its name
                    from_col = next(col for col in rules_df.columns if "from" in col.lower())
                    rules_df = rules_df.rename(columns={from_col: "from_text"})
                elif len(rules_df.columns) > 0:
                    # If no matching column found, use the first column
                    rules_df = rules_df.rename(columns={rules_df.columns[0]: "from_text"})

            if "to_text" not in rules_df.columns:
                # Look for alternative column names
                if "To" in rules_df.columns:
                    rules_df = rules_df.rename(columns={"To": "to_text"})
                elif any("to" in col.lower() for col in rules_df.columns):
                    # Find the column that contains 'to' in its name
                    to_col = next(col for col in rules_df.columns if "to" in col.lower())
                    rules_df = rules_df.rename(columns={to_col: "to_text"})
                elif len(rules_df.columns) > 1:
                    # If no matching column found, use the second column
                    rules_df = rules_df.rename(columns={rules_df.columns[1]: "to_text"})

            # Check if we have the required columns
            if "from_text" not in rules_df.columns or "to_text" not in rules_df.columns:
                if len(rules_df.columns) >= 1:
                    # Check if first column name contains multiple parts
                    first_col = rules_df.columns[0]
                    if isinstance(first_col, str) and ("," in first_col or ";" in first_col):
                        # The column name might actually be a concatenation of all headers
                        # Try to split it into separate columns
                        sep_in_header = "," if "," in first_col else ";"
                        headers = first_col.split(sep_in_header)

                        if len(headers) >= 2:
                            # Extract data from the first column and split it
                            data = []
                            for value in rules_df[first_col]:
                                if isinstance(value, str) and sep_in_header in value:
                                    parts = value.split(sep_in_header)
                                    row = {
                                        "from_text": parts[0].strip() if len(parts) > 0 else "",
                                        "to_text": parts[1].strip() if len(parts) > 1 else "",
                                        "category": parts[2].strip()
                                        if len(parts) > 2
                                        else "general",
                                        "enabled": True,
                                        "timestamp": pd.Timestamp.now(),
                                    }
                                    data.append(row)

                            # Create new DataFrame with proper columns
                            if data:
                                rules_df = pd.DataFrame(data)
                            else:
                                raise ValueError(
                                    f"Failed to extract data from malformed CSV. Headers: {headers}"
                                )
                        else:
                            raise ValueError(
                                f"Unable to identify required columns. Available: {rules_df.columns}"
                            )
                    else:
                        raise ValueError(
                            f"Required columns 'from_text' and 'to_text' not found. Available: {rules_df.columns}"
                        )
                else:
                    raise ValueError(f"Failed to parse CSV file. No columns found.")

            # Add default values for missing columns
            if "category" not in rules_df.columns:
                rules_df["category"] = "general"

            if "enabled" not in rules_df.columns:
                rules_df["enabled"] = True

            # Add timestamp if not present
            if "timestamp" not in rules_df.columns:
                rules_df["timestamp"] = pd.Timestamp.now()

            # Remove any rows with missing from_text or to_text
            rules_df = rules_df.dropna(subset=["from_text", "to_text"])

            # Filter out empty strings
            rules_df = rules_df[rules_df["from_text"].astype(str).str.strip() != ""]
            rules_df = rules_df[rules_df["to_text"].astype(str).str.strip() != ""]

            # Convert from_text and to_text to strings
            rules_df["from_text"] = rules_df["from_text"].astype(str)
            rules_df["to_text"] = rules_df["to_text"].astype(str)

            # Set in the store
            self._store.set_correction_rules(rules_df)

            self._logger.info(f"Loaded {len(rules_df)} correction rules from {file_path}")
            return len(rules_df)

        except Exception as e:
            self._logger.error(f"Error loading correction rules from {file_path}: {str(e)}")
            raise


class CorrectionService:
    """Service for applying corrections to entries."""

    def __init__(self, store):
        """
        Initialize the CorrectionService.

        Args:
            store: DataFrameStore instance
        """
        self._store = store
        self._logger = logging.getLogger(__name__ + ".CorrectionService")

    def apply_corrections(self):
        """
        Apply all enabled correction rules to entries.

        Returns:
            Dict with stats about the corrections applied
        """
        try:
            self._logger.info("Applying corrections to entries")

            # Get data from the store
            entries_df = self._store.get_entries()
            rules_df = self._store.get_correction_rules()

            # Skip if no entries or rules
            if entries_df.empty or rules_df.empty:
                self._logger.info("No entries or rules to apply corrections")
                return {"entries_affected": 0, "corrections_applied": 0}

            # Start a transaction
            self._store.begin_transaction()

            # Track stats
            entries_affected = 0
            corrections_applied = 0

            # Make a copy of the entries
            entries_df_modified = entries_df.copy()

            # Get only enabled rules
            active_rules = rules_df[rules_df["enabled"] == True]

            # Initialize original_values if it doesn't exist
            if "original_values" not in entries_df_modified.columns:
                entries_df_modified["original_values"] = [
                    {} for _ in range(len(entries_df_modified))
                ]
            else:
                # Convert NaN values to empty dicts
                entries_df_modified["original_values"] = entries_df_modified[
                    "original_values"
                ].apply(
                    lambda x: {}
                    if isinstance(x, float) and pd.isna(x)
                    else ({} if x is None else x)
                )

            # Apply each rule
            for _, rule in active_rules.iterrows():
                # Make sure we have the necessary columns with default values if missing
                category = rule.get("category", "general")

                # Get from_text and to_text from the appropriate columns
                if "from_text" in rule and "to_text" in rule:
                    from_text = rule["from_text"]
                    to_text = rule["to_text"]
                elif "From" in rule and "To" in rule:
                    from_text = rule["From"]
                    to_text = rule["To"]
                else:
                    self._logger.warning(f"Skipping rule with missing from/to text: {rule}")
                    continue

                # Skip if from_text or to_text is empty
                if not from_text or not to_text or pd.isna(from_text) or pd.isna(to_text):
                    continue

                # Apply to the appropriate column
                if category == "general" or category == "all":
                    # Apply to all text columns
                    for col in ["chest_type", "player", "source"]:
                        # Find rows that match
                        matches = entries_df_modified[col] == from_text
                        match_count = matches.sum()

                        if match_count > 0:
                            # Back up original values
                            for idx in entries_df_modified.index[matches]:
                                original = entries_df_modified.at[idx, "original_values"]
                                if not col in original:
                                    original[col] = entries_df_modified.at[idx, col]
                                entries_df_modified.at[idx, "original_values"] = original

                            # Apply correction
                            entries_df_modified.loc[matches, col] = to_text

                            # Update stats
                            corrections_applied += match_count
                            entries_affected += match_count
                else:
                    # Apply to specific column
                    col = category
                    if col in entries_df_modified.columns:
                        # Find rows that match
                        matches = entries_df_modified[col] == from_text
                        match_count = matches.sum()

                        if match_count > 0:
                            # Back up original values
                            for idx in entries_df_modified.index[matches]:
                                original = entries_df_modified.at[idx, "original_values"]
                                if not col in original:
                                    original[col] = entries_df_modified.at[idx, col]
                                entries_df_modified.at[idx, "original_values"] = original

                            # Apply correction
                            entries_df_modified.loc[matches, col] = to_text

                            # Update stats
                            corrections_applied += match_count
                            entries_affected += match_count

            # Update the entries in the store
            self._store.set_entries(entries_df_modified, "correction_applied")

            # Commit the transaction
            self._store.commit_transaction()

            # Emit event with stats
            self._store._emit_event(
                EventType.CORRECTION_APPLIED,
                {"entries_affected": entries_affected, "corrections_applied": corrections_applied},
            )

            self._logger.info(
                f"Applied {corrections_applied} corrections to {entries_affected} entries"
            )

            return {
                "entries_affected": entries_affected,
                "corrections_applied": corrections_applied,
            }

        except Exception as e:
            # Rollback transaction on error
            self._store.rollback_transaction()
            self._logger.error(f"Error applying corrections: {str(e)}")
            self._store._emit_event(
                EventType.ERROR_OCCURRED, {"type": "correction", "error": str(e)}
            )
            raise


class ValidationService:
    """Service for validating entries against validation lists."""

    def __init__(self, store):
        """
        Initialize the ValidationService.

        Args:
            store: DataFrameStore instance
        """
        self._store = store
        self._logger = logging.getLogger(__name__ + ".ValidationService")

    def validate_entries(self):
        """
        Validate all entries against validation lists.

        Returns:
            Dict with validation stats
        """
        try:
            self._logger.info("Validating entries")

            # Get data from the store
            entries_df = self._store.get_entries()

            # Skip if no entries
            if entries_df.empty:
                self._logger.info("No entries to validate")
                return {"valid": 0, "invalid": 0, "total": 0}

            # Start a transaction
            self._store.begin_transaction()

            # Make a copy of the entries
            entries_df_modified = entries_df.copy()

            # Get validation lists
            chest_types_df = self._store.get_validation_list("chest_types")
            players_df = self._store.get_validation_list("players")
            sources_df = self._store.get_validation_list("sources")

            # Initialize validation errors array if it doesn't exist
            if "validation_errors" not in entries_df_modified.columns:
                entries_df_modified["validation_errors"] = [
                    [] for _ in range(len(entries_df_modified))
                ]
            else:
                # Convert NaN values to empty lists
                entries_df_modified["validation_errors"] = entries_df_modified[
                    "validation_errors"
                ].apply(
                    lambda x: []
                    if isinstance(x, float) and pd.isna(x)
                    else ([] if x is None else x)
                )

            # Validate each entry
            for idx, entry in entries_df_modified.iterrows():
                # Clear previous validation errors
                entries_df_modified.at[idx, "validation_errors"] = []

                # Validate chest_type
                if not chest_types_df.empty and "value" in chest_types_df.columns:
                    if entry["chest_type"] not in chest_types_df["value"].values:
                        entries_df_modified.at[idx, "validation_errors"].append(
                            {
                                "field": "chest_type",
                                "error": f"Invalid chest type: {entry['chest_type']}",
                            }
                        )

                # Validate player
                if not players_df.empty and "value" in players_df.columns:
                    if entry["player"] not in players_df["value"].values:
                        entries_df_modified.at[idx, "validation_errors"].append(
                            {"field": "player", "error": f"Invalid player: {entry['player']}"}
                        )

                # Validate source (if not empty)
                if entry["source"] and not sources_df.empty and "value" in sources_df.columns:
                    if entry["source"] not in sources_df["value"].values:
                        entries_df_modified.at[idx, "validation_errors"].append(
                            {"field": "source", "error": f"Invalid source: {entry['source']}"}
                        )

                # Update status based on validation errors
                if len(entries_df_modified.at[idx, "validation_errors"]) > 0:
                    entries_df_modified.at[idx, "status"] = "Invalid"
                else:
                    entries_df_modified.at[idx, "status"] = "Valid"

            # Update the entries in the store
            self._store.set_entries(entries_df_modified, "validation")

            # Commit the transaction
            self._store.commit_transaction()

            # Calculate stats
            valid_count = (entries_df_modified["status"] == "Valid").sum()
            invalid_count = (entries_df_modified["status"] == "Invalid").sum()
            total_count = len(entries_df_modified)

            # Emit event with stats
            self._store._emit_event(
                EventType.VALIDATION_COMPLETED,
                {"valid": valid_count, "invalid": invalid_count, "total": total_count},
            )

            self._logger.info(
                f"Validated {total_count} entries: {valid_count} valid, {invalid_count} invalid"
            )

            return {"valid": valid_count, "invalid": invalid_count, "total": total_count}

        except Exception as e:
            # Rollback transaction on error
            self._store.rollback_transaction()
            self._logger.error(f"Error validating entries: {str(e)}")
            self._store._emit_event(
                EventType.ERROR_OCCURRED, {"type": "validation", "error": str(e)}
            )
            raise


class ServiceFactory:
    """Factory for creating and accessing services."""

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = ServiceFactory()
        return cls._instance

    def __init__(self):
        """Initialize the ServiceFactory."""
        self._services = {}
        self._adapters = {}
        self._logger = logging.getLogger(__name__ + ".ServiceFactory")

    def get_dataframe_store(self):
        """Get the DataFrameStore instance."""
        if "dataframe_store" not in self._services:
            self._services["dataframe_store"] = DataFrameStore.get_instance()
        return self._services["dataframe_store"]

    def get_file_service(self):
        """Get the FileService instance."""
        if "file_service" not in self._services:
            self._services["file_service"] = FileService(self.get_dataframe_store())
        return self._services["file_service"]

    def get_correction_service(self):
        """Get the CorrectionService instance."""
        if "correction_service" not in self._services:
            self._services["correction_service"] = CorrectionService(self.get_dataframe_store())
        return self._services["correction_service"]

    def get_validation_service(self):
        """Get the ValidationService instance."""
        if "validation_service" not in self._services:
            self._services["validation_service"] = ValidationService(self.get_dataframe_store())
        return self._services["validation_service"]

    def initialize_all_services(self):
        """Initialize all services."""
        self.get_dataframe_store()
        self.get_file_service()
        self.get_correction_service()
        self.get_validation_service()
        self._logger.info("All services initialized")

    def get_entry_table_adapter(self, table_view):
        """Get an EntryTableAdapter for a table view."""
        adapter_key = f"entry_adapter_{id(table_view)}"
        if adapter_key not in self._adapters:
            self._adapters[adapter_key] = EntryTableAdapter(table_view, self.get_dataframe_store())
        return self._adapters[adapter_key]

    def get_correction_rule_table_adapter(self, table_view):
        """Get a CorrectionRuleTableAdapter for a table view."""
        adapter_key = f"rule_adapter_{id(table_view)}"
        if adapter_key not in self._adapters:
            self._adapters[adapter_key] = CorrectionRuleTableAdapter(
                table_view, self.get_dataframe_store()
            )
        return self._adapters[adapter_key]


class IntegrationTestWindow(QMainWindow):
    """Integration test window for the refactored MainWindow."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integration Test")
        self.resize(1024, 768)

        # Initialize service factory and services
        self._service_factory = ServiceFactory.get_instance()
        self._service_factory.initialize_all_services()

        # Get service instances
        self._store = self._service_factory.get_dataframe_store()
        self._file_service = self._service_factory.get_file_service()
        self._correction_service = self._service_factory.get_correction_service()
        self._validation_service = self._service_factory.get_validation_service()

        # Setup logging
        self._logger = logging.getLogger(__name__ + ".IntegrationTestWindow")

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Create left panel (entries)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("<h3>Entries</h3>"))

        # Add entry table
        self.entry_table = QTableView()
        left_layout.addWidget(self.entry_table)

        # Connect entry table to store
        self.entry_adapter = self._service_factory.get_entry_table_adapter(self.entry_table)

        # Create right panel (correction rules)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("<h3>Correction Rules</h3>"))

        # Add correction rule table
        self.correction_table = QTableView()
        right_layout.addWidget(self.correction_table)

        # Connect correction table to store
        self.rule_adapter = self._service_factory.get_correction_rule_table_adapter(
            self.correction_table
        )

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 500])

        # Add button panel
        button_panel = QWidget()
        button_layout = QHBoxLayout(button_panel)
        main_layout.addWidget(button_panel)

        # Add buttons
        self.load_entries_btn = QPushButton("Load Entries")
        self.load_entries_btn.clicked.connect(self.load_entries)
        button_layout.addWidget(self.load_entries_btn)

        self.load_rules_btn = QPushButton("Load Rules")
        self.load_rules_btn.clicked.connect(self.load_rules)
        button_layout.addWidget(self.load_rules_btn)

        self.validate_btn = QPushButton("Validate Entries")
        self.validate_btn.clicked.connect(self.validate_entries)
        button_layout.addWidget(self.validate_btn)

        self.apply_corrections_btn = QPushButton("Apply Corrections")
        self.apply_corrections_btn.clicked.connect(self.apply_corrections)
        button_layout.addWidget(self.apply_corrections_btn)

        self.save_entries_btn = QPushButton("Save Entries")
        self.save_entries_btn.clicked.connect(self.save_entries)
        button_layout.addWidget(self.save_entries_btn)

        # Add status bar
        self.statusBar().showMessage("Ready")

        # Subscribe to events
        self._store.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
        self._store.subscribe(EventType.CORRECTION_RULES_UPDATED, self._on_rules_updated)
        self._store.subscribe(EventType.CORRECTION_APPLIED, self._on_correction_applied)
        self._store.subscribe(EventType.VALIDATION_COMPLETED, self._on_validation_completed)
        self._store.subscribe(EventType.ERROR_OCCURRED, self._on_error_occurred)

        # Initialize with validation lists
        self._setup_validation_lists()

        self._logger.info("IntegrationTestWindow initialized")

    def _setup_validation_lists(self):
        """Set up default validation lists."""
        # Create chest types list
        chest_types_data = {
            "value": [
                "Gold Chest",
                "Silver Chest",
                "Bronze Chest",
                "Rare Dragon Chest",
                "Barbarian Chest",
                "Scarab Chest",
                "White Wood Chest",
                "Elegant Chest",
                "Chest of the Cursed",
                "Bone Chest",
                "Merchant's Chest",
                "Cobra Chest",
                "Infernal Chest",
                "Orc Chest",
            ]
        }
        chest_types_df = pd.DataFrame(chest_types_data)
        self._store.set_validation_list("chest_types", chest_types_df)

        # Create players list
        players_data = {
            "value": [
                "Engelchen",
                "Darkhammer",
                "Sir Met",
                "Moony",
                "nobe",
                "GUARDIENofTHUNDER",
                "Cordaginn",
                "Tyroler Bua",
                "Bruno",
            ]
        }
        players_df = pd.DataFrame(players_data)
        self._store.set_validation_list("players", players_df)

        # Create sources list
        sources_data = {
            "value": [
                "Level 15 Crypt",
                "Level 15 rare Crypt",
                "Level 25 epic Crypt",
                "Level 25 Crypt",
                "Level 10 Crypt",
                "Mercenary Exchange",
                "Level 20 epic Crypt",
                "Level 15 epic Crypt",
            ]
        }
        sources_df = pd.DataFrame(sources_data)
        self._store.set_validation_list("sources", sources_df)

        self._logger.info("Default validation lists created")

    def _on_entries_updated(self, data):
        """Handle entries updated event."""
        entries_df = self._store.get_entries()
        self.statusBar().showMessage(f"Entries updated: {len(entries_df)} total entries")
        self._logger.info(f"Entries updated: {len(entries_df)} entries")

    def _on_rules_updated(self, data):
        """Handle correction rules updated event."""
        rules_df = self._store.get_correction_rules()
        self.statusBar().showMessage(f"Correction rules updated: {len(rules_df)} rules")
        self._logger.info(f"Correction rules updated: {len(rules_df)} rules")

    def _on_correction_applied(self, data):
        """Handle correction applied event."""
        entries_affected = data.get("entries_affected", 0)
        corrections_applied = data.get("corrections_applied", 0)
        self.statusBar().showMessage(
            f"Applied {corrections_applied} corrections to {entries_affected} entries"
        )
        self._logger.info(
            f"Applied {corrections_applied} corrections to {entries_affected} entries"
        )

    def _on_validation_completed(self, data):
        """Handle validation completed event."""
        valid = data.get("valid", 0)
        invalid = data.get("invalid", 0)
        total = data.get("total", 0)
        self.statusBar().showMessage(
            f"Validation completed: {valid} valid, {invalid} invalid, {total} total"
        )
        self._logger.info(f"Validation completed: {valid} valid, {invalid} invalid, {total} total")

    def _on_error_occurred(self, data):
        """Handle error occurred event."""
        error_type = data.get("type", "unknown")
        error_message = data.get("error", "Unknown error")
        self.statusBar().showMessage(f"Error: {error_message}")
        self._logger.error(f"Error occurred ({error_type}): {error_message}")

        # Show error message box
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}", QMessageBox.Ok)

    def load_entries(self):
        """Load entries from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Entries", "", "Text Files (*.txt);;All Files (*.*)"
        )

        if file_path:
            try:
                count = self._file_service.load_entries_from_file(file_path)
                self.statusBar().showMessage(f"Loaded {count} entries from {file_path}")

                # Automatically validate entries
                self.validate_entries()
            except Exception as e:
                self._logger.error(f"Error loading entries: {str(e)}")
                QMessageBox.critical(
                    self, "Error", f"Failed to load entries: {str(e)}", QMessageBox.Ok
                )

    def load_rules(self):
        """Load correction rules from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Correction Rules", "", "CSV Files (*.csv);;All Files (*.*)"
        )

        if file_path:
            try:
                count = self._file_service.load_correction_rules_from_csv(file_path)
                self.statusBar().showMessage(f"Loaded {count} correction rules from {file_path}")
            except Exception as e:
                self._logger.error(f"Error loading correction rules: {str(e)}")
                QMessageBox.critical(
                    self, "Error", f"Failed to load correction rules: {str(e)}", QMessageBox.Ok
                )

    def validate_entries(self):
        """Validate entries against validation lists."""
        try:
            stats = self._validation_service.validate_entries()
            valid = stats.get("valid", 0)
            invalid = stats.get("invalid", 0)
            total = stats.get("total", 0)
            self.statusBar().showMessage(
                f"Validation completed: {valid} valid, {invalid} invalid, {total} total"
            )
        except Exception as e:
            self._logger.error(f"Error validating entries: {str(e)}")
            QMessageBox.critical(
                self, "Error", f"Failed to validate entries: {str(e)}", QMessageBox.Ok
            )

    def apply_corrections(self):
        """Apply correction rules to entries."""
        try:
            stats = self._correction_service.apply_corrections()
            entries_affected = stats.get("entries_affected", 0)
            corrections_applied = stats.get("corrections_applied", 0)
            self.statusBar().showMessage(
                f"Applied {corrections_applied} corrections to {entries_affected} entries"
            )

            # Revalidate entries after applying corrections
            self.validate_entries()
        except Exception as e:
            self._logger.error(f"Error applying corrections: {str(e)}")
            QMessageBox.critical(
                self, "Error", f"Failed to apply corrections: {str(e)}", QMessageBox.Ok
            )

    def save_entries(self):
        """Save entries to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Entries", "", "Text Files (*.txt);;All Files (*.*)"
        )

        if file_path:
            try:
                count = self._file_service.save_entries_to_file(file_path)
                self.statusBar().showMessage(f"Saved {count} entries to {file_path}")
            except Exception as e:
                self._logger.error(f"Error saving entries: {str(e)}")
                QMessageBox.critical(
                    self, "Error", f"Failed to save entries: {str(e)}", QMessageBox.Ok
                )


def create_sample_data(output_path):
    """Create a sample data file for testing."""
    sample_data = """Forgotten Chest
From: Engelchen
Source: Level 15 Crypt

Rare Dragon Chest
From: Engelchen
Source: Level 15 rare Crypt

Barbarian Chest
From: Darkhammer

Scarab Chest
From: Engelchen
Source: Level 15 epic Crypt

White Wood Chest
From: Sir Met
Source: Level 25 epic Crypt

Elegant Chest
From: Moony
Source: Level 25 Crypt

Chest of the Cursed
From: Sir Met
Source: Level 25 epic Crypt

Elegant Chest
From: Moony
Source: Level 25 Crypt

Bone Chest
From: Darkhammer
Source: Level 10 Crypt

Merchant's Chest
From: nobe
Source: Mercenary Exchange

White Wood Chest
From: nobe
Source: Level 20 epic Crypt

White Wood Chest
From: GUARDIENofTHUNDER
Source: Level 20 epic Crypt

Cobra Chest
From: Cordaginn
Source: Level 25 Crypt

Infernal Chest
From: Cordaginn
Source: Level 25 Crypt

Orc Chest
From: Tyroler Bua
Source: Level 15 Crypt

Cobra Chest
From: Tyroler Bua
Source: Level 15 Crypt

Merchant's Chest
From: Bruno
Source: Mercenary Exchange
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sample_data)

    logger.info(f"Created sample data file at {output_path}")


def create_sample_rules(output_path):
    """Create a sample correction rules file for testing."""
    sample_rules = """From;To
Forgotten Chest;Forgotten Ancient Chest
Scarab Chest;Golden Scarab Chest
White Wood;Whitewood
Elegant Chest;Royal Elegant Chest
Level 15 epic;Level 15 Epic
Level 20 epic;Level 20 Epic
Level 25 epic;Level 25 Epic
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sample_rules)

    logger.info(f"Created sample rules file at {output_path}")


def main():
    """Main function."""
    # Create sample data files if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--create-samples":
        create_sample_data("sample_data.txt")
        create_sample_rules("sample_rules.csv")
        logger.info(
            "Sample files created. Run the program again without arguments to start the integration test."
        )
        return

    # Create the application
    app = QApplication(sys.argv)

    # Create and show the main window
    window = IntegrationTestWindow()
    window.show()

    # Auto-load sample files if they exist
    if os.path.exists("sample_data.txt"):
        window._file_service.load_entries_from_file("sample_data.txt")
        window.validate_entries()

    if os.path.exists("sample_rules.csv"):
        window._file_service.load_correction_rules_from_csv("sample_rules.csv")

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
