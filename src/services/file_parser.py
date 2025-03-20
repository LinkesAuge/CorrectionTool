"""
file_parser.py

Description: Parser services for text files and CSV files
Usage:
    from src.services.file_parser import FileParser
    parser = FileParser()
    entries = parser.parse_entry_file("data/input/chests_2023-01-01.txt")
    rules = parser.parse_correction_file("data/corrections/rules.csv")
"""

import csv
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import traceback

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule


class FileParser:
    """
    Unified parser for text and CSV files.

    Handles parsing of both chest entry text files and correction rule CSV files.
    Provides methods for saving entries and rules back to files.

    Implementation Notes:
        - Automatically detects file format based on extension
        - Supports multiple text encodings (utf-8, latin-1, etc.)
        - Handles malformed entries gracefully
        - Extracts metadata like dates from filenames
    """

    def __init__(self):
        """Initialize the file parser."""
        # Supported file formats
        self._entry_formats = {
            ".txt": self._parse_text_file,
        }

        self._correction_formats = {
            ".csv": self._parse_csv_file,
        }

        # Supported encodings
        self._encodings = ["utf-8", "latin-1", "utf-16", "cp1252"]

        # Set up logger
        self.logger = logging.getLogger(__name__)

    def parse_entry_file(self, file_path: Union[str, Path]) -> List[ChestEntry]:
        """
        Parse a file containing chest entries.

        Args:
            file_path: Path to the file

        Returns:
            List of parsed chest entries

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        file_path = Path(file_path)
        self.logger.info(f"Parsing entry file: {file_path}")

        # Check if file exists
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file extension
        extension = file_path.suffix.lower()

        # Check if format is supported
        if extension not in self._entry_formats:
            self.logger.error(f"Unsupported file format: {extension}")
            raise ValueError(
                f"Unsupported file format: {extension}. Supported formats: {', '.join(self._entry_formats.keys())}"
            )

        # Parse the file using the appropriate parser
        try:
            entries = self._entry_formats[extension](file_path)
            self.logger.info(f"Successfully parsed {len(entries)} entries from {file_path}")
            return entries
        except Exception as e:
            self.logger.error(f"Error parsing entry file {file_path}: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def parse_correction_file(self, file_path: Union[str, Path]) -> List[CorrectionRule]:
        """
        Parse a file containing correction rules.

        Args:
            file_path: Path to the file

        Returns:
            List of parsed correction rules

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        file_path = Path(file_path)
        self.logger.info(f"Parsing correction file: {file_path}")

        # Check if file exists
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get file extension
        extension = file_path.suffix.lower()

        # Check if format is supported
        if extension not in self._correction_formats:
            self.logger.error(f"Unsupported file format: {extension}")
            raise ValueError(
                f"Unsupported file format: {extension}. Supported formats: {', '.join(self._correction_formats.keys())}"
            )

        # Parse the file using the appropriate parser
        try:
            rules = self._correction_formats[extension](file_path)
            self.logger.info(f"Successfully parsed {len(rules)} rules from {file_path}")
            return rules
        except Exception as e:
            self.logger.error(f"Error parsing correction file {file_path}: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def parse_correction_rules(self, file_path: Union[str, Path]) -> List[CorrectionRule]:
        """
        Parse a file containing correction rules.

        This is an alias for parse_correction_file for backward compatibility.

        Args:
            file_path: Path to the file

        Returns:
            List of parsed correction rules

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        return self.parse_correction_file(file_path)

    def save_entries_to_file(self, entries: List[ChestEntry], file_path: Union[str, Path]) -> None:
        """
        Save chest entries to a file.

        Args:
            entries: List of chest entries
            file_path: Path to save the file

        Raises:
            ValueError: If the file format is not supported
        """
        file_path = Path(file_path)
        self.logger.info(f"Saving {len(entries)} entries to {file_path}")

        # Get file extension
        extension = file_path.suffix.lower()

        # Check if format is supported
        if extension not in self._entry_formats:
            self.logger.error(f"Unsupported file format: {extension}")
            raise ValueError(
                f"Unsupported file format: {extension}. Supported formats: {', '.join(self._entry_formats.keys())}"
            )

        # Save to text file
        try:
            if extension == ".txt":
                self._save_entries_to_text(entries, file_path)
                self.logger.info(f"Successfully saved entries to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving entries to {file_path}: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def save_rules_to_file(self, rules: List[CorrectionRule], file_path: Union[str, Path]) -> None:
        """
        Save correction rules to a file.

        Args:
            rules: List of correction rules
            file_path: Path to save the file

        Raises:
            ValueError: If the file format is not supported
        """
        file_path = Path(file_path)
        self.logger.info(f"Saving {len(rules)} rules to {file_path}")

        # Get file extension
        extension = file_path.suffix.lower()

        # Check if format is supported
        if extension not in self._correction_formats:
            self.logger.error(f"Unsupported file format: {extension}")
            raise ValueError(
                f"Unsupported file format: {extension}. Supported formats: {', '.join(self._correction_formats.keys())}"
            )

        # Save to CSV file
        try:
            if extension == ".csv":
                self._save_rules_to_csv(rules, file_path)
                self.logger.info(f"Successfully saved rules to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving rules to {file_path}: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def extract_date_from_filename(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Extract date from filename.

        Args:
            file_path: Path to the file

        Returns:
            The extracted date (YYYY-MM-DD) or None if not found
        """
        file_path = Path(file_path)
        filename = file_path.name

        # Regular expression to match date patterns
        date_pattern = r"(\d{4}-\d{2}-\d{2})"
        match = re.search(date_pattern, filename)

        if match:
            return match.group(1)
        return None

    def _parse_text_file(self, file_path: Path) -> List[ChestEntry]:
        """
        Parse a text file containing chest entries.

        Args:
            file_path: Path to the text file

        Returns:
            List of parsed chest entries

        Raises:
            ValueError: If the file encoding is not supported
        """
        # Try different encodings
        for encoding in self._encodings:
            try:
                self.logger.info(f"Attempting to parse text file with encoding: {encoding}")
                with open(file_path, "r", encoding=encoding) as f:
                    text = f.read()
                entries = self._parse_text_content(text)
                self.logger.info(f"Successfully parsed text file with encoding: {encoding}")
                return entries
            except UnicodeDecodeError:
                self.logger.warning(f"Failed to decode with {encoding} encoding, trying next...")
                continue
            except Exception as e:
                self.logger.error(f"Error parsing text file with {encoding} encoding: {str(e)}")
                self.logger.error(traceback.format_exc())
                raise

        error_msg = f"Could not decode file with any of the supported encodings: {', '.join(self._encodings)}"
        self.logger.error(error_msg)
        raise ValueError(error_msg)

    def _parse_text_content(self, text: str) -> List[ChestEntry]:
        """
        Parse text containing chest entries.

        Args:
            text: Text containing chest entries

        Returns:
            List of parsed chest entries
        """
        lines = text.splitlines()
        entries = []
        current_id = 1  # Counter for entry IDs
        self.logger.info(f"Parsing text content with {len(lines)} lines")

        # Group lines into 3-line entries
        i = 0
        while i < len(lines):
            # Skip empty lines
            if not lines[i].strip():
                i += 1
                continue

            # We need to detect a potential chest entry
            # A chest entry starts with a line that doesn't have "From:" or "Source:" prefix
            current_line = lines[i].strip()

            # If the line starts with "From:" or "Source:", it's probably not a chest type
            if current_line.lower().startswith("from:") or current_line.lower().startswith(
                "source:"
            ):
                self.logger.debug(f"Skipping line {i + 1} - not a chest type: {current_line}")
                i += 1
                continue

            # Ensure we have at least 2 more lines
            if i + 2 >= len(lines):
                self.logger.warning(
                    f"Not enough lines remaining for a complete entry at line {i + 1}"
                )
                break

            # Extract the 3 lines
            chest_type = current_line
            player_line = lines[i + 1].strip()
            source_line = lines[i + 2].strip()

            # Verify this is likely a valid entry (player line should start with "From:")
            if not player_line.lower().startswith("from:"):
                # This might not be a valid entry, try to recover or skip
                self.logger.warning(
                    f"Invalid entry format at line {i + 1} - player line doesn't start with 'From:'"
                )
                i += 1
                continue

            # Create a ChestEntry
            try:
                entry_text = f"{chest_type}\n{player_line}\n{source_line}"
                # Only log occasionally (first entry, every 100th entry)
                if current_id == 1 or current_id % 100 == 0:
                    self.logger.debug(f"Creating entry #{current_id} from text: {entry_text}")

                # IDs are now auto-generated in the ChestEntry class
                entry = ChestEntry.from_text(entry_text)
                entries.append(entry)

                # Only log occasionally (first entry, every 100th entry)
                if current_id == 1 or current_id % 100 == 0:
                    self.logger.debug(
                        f"Created entry #{current_id}: {entry.chest_type}, {entry.player}, {entry.source}"
                    )

                current_id += 1
            except ValueError as e:
                # Log the error or handle malformed entries
                self.logger.error(f"Error parsing entry at line {i + 1}: {e}")
                self.logger.error(f"Entry text: {chest_type}\n{player_line}\n{source_line}")

            # Move to the next entry (skip 3 lines)
            i += 3

        self.logger.info(f"Parsed {len(entries)} entries from text content")
        return entries

    def _save_entries_to_text(self, entries: List[ChestEntry], file_path: Path) -> None:
        """
        Save chest entries to a text file.

        Args:
            entries: List of chest entries
            file_path: Path to save the file
        """
        self.logger.info(f"Saving {len(entries)} entries to text file: {file_path}")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for i, entry in enumerate(entries):
                    # Add a blank line between entries (except for the first one)
                    if i > 0:
                        f.write("\n")

                    # Write the entry as text
                    f.write(entry.to_text())
            self.logger.info(f"Successfully saved {len(entries)} entries to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving entries to text file: {e}")
            self.logger.error(traceback.format_exc())
            raise

    def _parse_csv_file(self, file_path: Path) -> List[CorrectionRule]:
        """
        Parse a CSV file containing correction rules.

        Args:
            file_path: Path to the CSV file

        Returns:
            List of parsed correction rules

        Raises:
            ValueError: If the CSV file is missing required headers or cannot be parsed
        """
        rules = []
        self.logger.info(f"Parsing CSV file: {file_path}")

        # Check if file is empty
        if file_path.stat().st_size == 0:
            self.logger.warning(f"CSV file is empty: {file_path}")
            return []

        # Define possible delimiters to try
        delimiters = [";", ",", "\t"]

        # Try different encodings
        for encoding in self._encodings:
            try:
                self.logger.info(f"Attempting to parse CSV with encoding: {encoding}")

                # First, try to read the file to detect the delimiter
                with open(file_path, "r", encoding=encoding, newline="") as f:
                    # Read the first line to detect the delimiter
                    first_line = f.readline().strip()

                    # If file is empty or first line is empty, skip
                    if not first_line:
                        self.logger.warning(
                            f"CSV file has no content or first line is empty: {file_path}"
                        )
                        continue

                    # Try each delimiter and use the one that results in the most columns
                    best_delimiter = None
                    most_columns = 0

                    for delimiter in delimiters:
                        column_count = first_line.count(delimiter) + 1
                        self.logger.debug(f"Delimiter '{delimiter}' gives {column_count} columns")
                        if column_count > most_columns:
                            most_columns = column_count
                            best_delimiter = delimiter

                    # If we couldn't determine a delimiter, default to comma
                    if not best_delimiter or most_columns < 2:
                        self.logger.warning(f"Could not determine delimiter, defaulting to comma")
                        best_delimiter = ","

                    self.logger.info(
                        f"Using delimiter: '{best_delimiter}' with {most_columns} columns"
                    )

                # Now read the file with the detected delimiter
                with open(file_path, "r", encoding=encoding, newline="") as f:
                    # Try to read the CSV with the best delimiter
                    reader = csv.DictReader(f, delimiter=best_delimiter)

                    # Check if reader.fieldnames is None (empty file or no headers)
                    if not reader.fieldnames:
                        self.logger.warning(f"CSV file has no headers: {file_path}")
                        continue

                    self.logger.info(f"CSV headers: {reader.fieldnames}")

                    # Convert fieldnames to lowercase for case-insensitive comparison
                    lowercase_fieldnames = [
                        field.lower() if field else "" for field in (reader.fieldnames or [])
                    ]

                    # Standard header mapping (case-insensitive)
                    header_map = {
                        "from": "From",
                        "to": "To",
                        "category": "Category",
                        "enabled": "Enabled",
                    }

                    # Check if required headers are present (case-insensitive)
                    if "from" in lowercase_fieldnames and "to" in lowercase_fieldnames:
                        self.logger.info("Found required headers (case-insensitive)")

                        # Parse rules with lowercase header mapping
                        for row_num, row in enumerate(
                            reader, start=2
                        ):  # Start at 2 to account for header row
                            try:
                                # Skip empty rows
                                if not any(row.values()):
                                    self.logger.debug(f"Skipping empty row {row_num}")
                                    continue

                                # Map headers to standard case
                                mapped_row = {
                                    header_map.get(key.lower(), key): value
                                    for key, value in row.items()
                                }

                                # Log the row for debugging
                                self.logger.debug(f"Processing row {row_num}: {mapped_row}")

                                # Skip rows where From or To is empty
                                if not mapped_row.get("From") or not mapped_row.get("To"):
                                    self.logger.warning(
                                        f"Skipping row {row_num} - missing From or To value: {mapped_row}"
                                    )
                                    continue

                                # Create rule
                                try:
                                    rule = CorrectionRule.from_csv_row(mapped_row)
                                    rules.append(rule)
                                    self.logger.debug(
                                        f"Created rule: {rule.from_text} -> {rule.to_text} (category: {rule.category})"
                                    )
                                except Exception as rule_error:
                                    self.logger.error(
                                        f"Error creating rule from row {row_num}: {rule_error}"
                                    )
                                    self.logger.error(f"Row data: {mapped_row}")
                                    # Continue processing other rows
                            except Exception as row_error:
                                self.logger.error(f"Error processing row {row_num}: {row_error}")
                                self.logger.error(traceback.format_exc())
                                # Continue with next row
                                continue

                        # If we got here, we successfully read the file
                        self.logger.info(f"Successfully parsed {len(rules)} rules from CSV")
                        return rules
                    else:
                        # Log the missing headers
                        required_headers = set(["From", "To"])
                        found_headers = set(
                            [header_map.get(h.lower(), h) for h in lowercase_fieldnames if h]
                        )
                        missing = required_headers - found_headers
                        error_msg = f"CSV file is missing required headers: {', '.join(missing)}"
                        self.logger.error(error_msg)
                        self.logger.error(f"Found headers: {found_headers}")
                        raise ValueError(error_msg)

            except UnicodeDecodeError:
                self.logger.warning(f"Failed to decode with {encoding} encoding, trying next...")
                continue
            except Exception as e:
                self.logger.error(f"Error reading CSV with {encoding} encoding: {str(e)}")
                self.logger.error(traceback.format_exc())
                continue

        # If we got here, we couldn't decode the file with any encoding
        error_msg = f"Could not decode file with any of the supported encodings: {', '.join(self._encodings)}"
        self.logger.error(error_msg)
        raise ValueError(error_msg)

    def _save_rules_to_csv(self, rules: List[CorrectionRule], file_path: Path) -> None:
        """
        Save correction rules to a CSV file.

        Args:
            rules: List of correction rules
            file_path: Path to save the file
        """
        self.logger.info(f"Saving {len(rules)} rules to CSV file: {file_path}")

        try:
            # Determine the appropriate delimiter based on file extension or name
            delimiter = ","  # Default to comma for CSV
            file_str = str(file_path).lower()

            if file_str.endswith(".tsv") or file_str.endswith(".tab"):
                delimiter = "\t"
            elif ";" in file_str:  # If the filename contains a semicolon, use semicolon
                delimiter = ";"

            self.logger.info(f"Using delimiter: '{delimiter}' for file: {file_path}")

            with open(file_path, "w", encoding="utf-8", newline="") as f:
                # Create a CSV writer with the required headers
                writer = csv.DictWriter(
                    f, fieldnames=["From", "To", "Category", "Enabled"], delimiter=delimiter
                )

                # Write the header row
                writer.writeheader()
                self.logger.debug("Wrote CSV header row")

                # Write each rule as a row
                for rule in rules:
                    # Convert rule to a row dictionary using the to_csv_row method
                    row = rule.to_csv_row()
                    writer.writerow(row)
                    self.logger.debug(f"Wrote rule: {rule.from_text} -> {rule.to_text}")

                self.logger.info(f"Successfully saved {len(rules)} rules to CSV")
        except Exception as e:
            self.logger.error(f"Error saving rules to CSV: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    def parse_entry_file_debug(self, file_path: Union[str, Path]) -> List[ChestEntry]:
        """
        Parse a file containing chest entries with detailed debugging.
        This wraps parse_entry_file with additional logging.

        Args:
            file_path: Path to the file

        Returns:
            List of parsed chest entries
        """
        logger = logging.getLogger(__name__)
        logger.info(f"DEBUG: Starting entry file parsing with detailed logging: {file_path}")

        try:
            # Check if file exists
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"DEBUG: File not found: {file_path}")
                return []

            # Get file info
            file_size = file_path_obj.stat().st_size
            logger.info(f"DEBUG: File size: {file_size} bytes")

            # Parse the file
            entries = self.parse_entry_file(file_path)

            # Log details about entries
            logger.info(f"DEBUG: Successfully parsed {len(entries)} entries")
            if entries:
                # Log the first entry as an example
                first_entry = entries[0]
                logger.info(
                    f"DEBUG: First entry: {first_entry.chest_type} | {first_entry.player} | {first_entry.source}"
                )

                # Log the last entry as an example
                last_entry = entries[-1]
                logger.info(
                    f"DEBUG: Last entry: {last_entry.chest_type} | {last_entry.player} | {last_entry.source}"
                )

                # Check if entries have ID values
                has_ids = all(entry.id is not None for entry in entries)
                logger.info(f"DEBUG: All entries have IDs: {has_ids}")

            return entries

        except Exception as e:
            logger.error(f"DEBUG: Error in parse_entry_file_debug: {str(e)}")
            import traceback

            logger.error(f"DEBUG: Traceback: {traceback.format_exc()}")
            return []


# For backward compatibility
TextParser = FileParser
CSVParser = FileParser
