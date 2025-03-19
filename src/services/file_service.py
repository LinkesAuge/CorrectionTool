"""
file_service.py

Description: Service for handling all file operations with integrated DataStore support
Usage:
    from src.services.file_service import FileService
    from src.interfaces.i_file_service import IFileService
    file_service = service_factory.get_service(IFileService)
    file_service.load_entries(Path('path/to/file.txt'))
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union
import re
import pandas as pd

from src.interfaces.i_file_service import IFileService
from src.interfaces.i_data_store import IDataStore
from src.enums.event_type import EventType


class FileService(IFileService):
    """
    Service for handling all file operations.

    This class provides a clean interface for loading and saving files,
    with direct integration to the DataStore for data management.

    Attributes:
        _store: IDataStore instance
        _logger: Logger instance

    Implementation Notes:
        - Loads files directly into DataStore
        - Provides robust error handling for file operations
    """

    def __init__(self, data_store: IDataStore):
        """
        Initialize the FileService with dependency injection.

        Args:
            data_store: Data store service
        """
        # Store injected dependencies
        self._store = data_store

        # Setup logging
        self._logger = logging.getLogger(__name__)
        self._logger.info("FileService initialized")

    def load_entries(self, file_path: Path) -> bool:
        """
        Load entries from a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        if not file_path.exists():
            self._logger.error(f"File not found: {file_path}")
            return False

        try:
            entries_data = []
            current_entry = None

            # Read file and parse entries
            with open(file_path, "r", encoding="utf-8") as file:
                line_count = 0
                for line in file:
                    line = line.strip()
                    line_count += 1

                    # Skip empty lines
                    if not line:
                        continue

                    # First line of entry is the chest type
                    if current_entry is None:
                        current_entry = {"chest_type": line}

                    # Second line is the player (prefixed with "From: ")
                    elif "player" not in current_entry:
                        # Extract player name from "From: Player" format
                        if line.startswith("From:"):
                            player = line[5:].strip()
                            current_entry["player"] = player
                        else:
                            # Handle case where "From:" prefix is missing
                            current_entry["player"] = line

                    # Third line is the source (prefixed with "Source: ")
                    elif "source" not in current_entry:
                        # Extract source from "Source: Location" format
                        if line.startswith("Source:"):
                            source = line[7:].strip()
                            current_entry["source"] = source
                        else:
                            # Handle case where "Source:" prefix is missing
                            current_entry["source"] = line

                        # Complete entry, add to list and reset
                        entries_data.append(current_entry)
                        current_entry = None

            # Convert to DataFrame
            if entries_data:
                entries_df = pd.DataFrame(entries_data)

                # Add status column
                entries_df["status"] = "Pending"

                # Add empty columns for validation data
                entries_df["validation_errors"] = [[] for _ in range(len(entries_df))]
                entries_df["original_values"] = [{} for _ in range(len(entries_df))]

                # Generate IDs
                entries_df["id"] = entries_df.apply(
                    lambda row: abs(hash((row["chest_type"], row["player"], row["source"])))
                    % (10**8),
                    axis=1,
                )

                # Set index
                entries_df.set_index("id", inplace=True)

                # Add timestamp
                import datetime

                entries_df["modified_at"] = pd.Timestamp(datetime.datetime.now())

                # Store in DataStore
                self._store.set_entries(entries_df)

                self._logger.info(f"Loaded {len(entries_df)} entries from {file_path}")
                return True
            else:
                self._logger.warning(f"No entries found in {file_path}")
                return False

        except Exception as e:
            self._logger.error(f"Error loading entries from {file_path}: {e}")
            return False

    def save_entries(self, file_path: Path) -> bool:
        """
        Save entries to a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get entries from DataStore
            entries_df = self._store.get_entries()

            if entries_df.empty:
                self._logger.warning("No entries to save")
                return False

            # Convert to original format and write to file
            with open(file_path, "w", encoding="utf-8") as file:
                for _, row in entries_df.iterrows():
                    file.write(f"{row['chest_type']}\n")
                    file.write(f"From: {row['player']}\n")
                    file.write(f"Source: {row['source']}\n")
                    file.write("\n")  # Add blank line between entries

            self._logger.info(f"Saved {len(entries_df)} entries to {file_path}")
            return True

        except Exception as e:
            self._logger.error(f"Error saving entries to {file_path}: {e}")
            return False

    def load_validation_list(self, list_type: str, file_path: Path) -> bool:
        """
        Load a validation list from a file.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        if not file_path.exists():
            self._logger.error(f"Validation list file not found: {file_path}")
            return False

        try:
            # Determine file type and parse accordingly
            if file_path.suffix.lower() == ".csv":
                # Read CSV file
                entries_df = pd.read_csv(file_path)

                # Rename first column to 'entry' if not already named
                if "entry" not in entries_df.columns and len(entries_df.columns) > 0:
                    entries_df.rename(columns={entries_df.columns[0]: "entry"}, inplace=True)

                # Set validation list
                self._store.set_validation_list(list_type, entries_df)

            else:
                # Read text file - one entry per line
                entries = []
                with open(file_path, "r", encoding="utf-8") as file:
                    for line in file:
                        entry = line.strip()
                        if entry:
                            entries.append(entry)

                # Create DataFrame
                entries_df = pd.DataFrame({"entry": entries})

                # Set validation list
                self._store.set_validation_list(list_type, entries_df)

            self._logger.info(
                f"Loaded {len(entries_df)} entries for '{list_type}' validation list from {file_path}"
            )
            return True

        except Exception as e:
            self._logger.error(f"Error loading validation list from {file_path}: {e}")
            return False

    def save_validation_list(self, list_type: str, file_path: Path) -> bool:
        """
        Save a validation list to a file.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get validation list from DataStore
            validation_df = self._store.get_validation_list(list_type)

            if validation_df.empty:
                self._logger.warning(f"No entries in '{list_type}' validation list to save")
                return False

            # Determine file type and save accordingly
            if file_path.suffix.lower() == ".csv":
                # Save as CSV
                validation_df.to_csv(file_path, index=False)
            else:
                # Save as text file - one entry per line
                with open(file_path, "w", encoding="utf-8") as file:
                    for entry in validation_df.index:
                        file.write(f"{entry}\n")

            self._logger.info(
                f"Saved {len(validation_df)} entries for '{list_type}' validation list to {file_path}"
            )
            return True

        except Exception as e:
            self._logger.error(f"Error saving validation list to {file_path}: {e}")
            return False

    def load_correction_rules(self, file_path: Path) -> bool:
        """
        Load correction rules from a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        if not file_path.exists():
            self._logger.error(f"Correction rules file not found: {file_path}")
            return False

        try:
            # Read CSV file
            rules_df = pd.read_csv(file_path)

            # Ensure required columns exist
            required_columns = ["field", "pattern", "replacement"]
            missing_columns = [col for col in required_columns if col not in rules_df.columns]

            if missing_columns:
                self._logger.error(
                    f"Missing required columns in correction rules file: {missing_columns}"
                )
                return False

            # Store correction rules
            self._store.set_correction_rules(rules_df)

            self._logger.info(f"Loaded {len(rules_df)} correction rules from {file_path}")
            return True

        except Exception as e:
            self._logger.error(f"Error loading correction rules from {file_path}: {e}")
            return False

    def save_correction_rules(self, file_path: Path) -> bool:
        """
        Save correction rules to a file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get correction rules from DataStore
            rules_df = self._store.get_correction_rules()

            if rules_df.empty:
                self._logger.warning("No correction rules to save")
                return False

            # Save as CSV
            rules_df.to_csv(file_path, index=False)

            self._logger.info(f"Saved {len(rules_df)} correction rules to {file_path}")
            return True

        except Exception as e:
            self._logger.error(f"Error saving correction rules to {file_path}: {e}")
            return False
