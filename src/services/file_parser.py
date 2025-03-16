"""
file_parser.py

Description: Parser services for text files and CSV files
Usage:
    from src.services.file_parser import TextParser
    entries = TextParser.parse_file("data/input/chests_2023-01-01.txt")
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule


class TextParser:
    """
    Parser for text files containing chest entries.
    
    Parses text files with chest entries, each consisting of 3 lines:
    1. Chest type
    2. Player (usually prefixed with "From:")
    3. Source (usually prefixed with "Source:")
    
    Implementation Notes:
        - Handles various text encodings
        - Extracts date from filename
        - Handles malformed entries gracefully
    """
    
    @staticmethod
    def parse_file(file_path: Union[str, Path]) -> List[ChestEntry]:
        """
        Parse a text file containing chest entries.
        
        Args:
            file_path (Union[str, Path]): Path to the text file
            
        Returns:
            List[ChestEntry]: List of parsed chest entries
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'utf-16', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                return TextParser.parse_text(text)
            except UnicodeDecodeError:
                continue
                
        raise ValueError(f"Could not decode file with any of the supported encodings: {', '.join(encodings)}")
    
    @staticmethod
    def parse_text(text: str) -> List[ChestEntry]:
        """
        Parse text containing chest entries.
        
        Args:
            text (str): Text containing chest entries
            
        Returns:
            List[ChestEntry]: List of parsed chest entries
        """
        lines = text.splitlines()
        entries = []
        
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
            if current_line.lower().startswith("from:") or current_line.lower().startswith("source:"):
                i += 1
                continue
                
            # Ensure we have at least 2 more lines
            if i + 2 >= len(lines):
                break
                
            # Extract the 3 lines
            chest_type = current_line
            player_line = lines[i + 1].strip()
            source_line = lines[i + 2].strip()
            
            # Verify this is likely a valid entry (player line should start with "From:")
            if not player_line.lower().startswith("from:"):
                # This might not be a valid entry, try to recover or skip
                i += 1
                continue
                
            # Create a ChestEntry
            try:
                entry_text = f"{chest_type}\n{player_line}\n{source_line}"
                entry = ChestEntry.from_text(entry_text)
                entries.append(entry)
            except ValueError as e:
                # Log the error or handle malformed entries
                print(f"Error parsing entry: {e}")
            
            # Move to the next entry (skip 3 lines)
            i += 3
        
        return entries
    
    @staticmethod
    def extract_date_from_filename(file_path: Union[str, Path]) -> Optional[str]:
        """
        Extract date from filename.
        
        Args:
            file_path (Union[str, Path]): Path to the file
            
        Returns:
            Optional[str]: The extracted date (YYYY-MM-DD) or None if not found
        """
        file_path = Path(file_path)
        filename = file_path.name
        
        # Regular expression to match date patterns
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, filename)
        
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def save_entries_to_file(entries: List[ChestEntry], file_path: Union[str, Path]) -> None:
        """
        Save chest entries to a text file.
        
        Args:
            entries (List[ChestEntry]): The entries to save
            file_path (Union[str, Path]): Path to save to
        """
        file_path = Path(file_path)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for i, entry in enumerate(entries):
                # Add an empty line between entries (except before the first one)
                if i > 0:
                    f.write("\n")
                    
                # Write the entry
                f.write(entry.to_text())


class CSVParser:
    """
    Parser for CSV files containing correction rules.
    
    Parses CSV files with correction rules, each having at least 'From' and 'To' columns.
    
    Implementation Notes:
        - Handles various CSV formats
        - Supports quoted text with special characters
        - Case-sensitive parsing
    """
    
    @staticmethod
    def parse_file(file_path: Union[str, Path]) -> List[CorrectionRule]:
        """
        Parse a CSV file containing correction rules.
        
        Args:
            file_path (Union[str, Path]): Path to the CSV file
            
        Returns:
            List[CorrectionRule]: List of parsed correction rules
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        rules = []
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'utf-16', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', newline='', encoding=encoding) as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    # Validate required columns
                    if not reader.fieldnames or 'From' not in reader.fieldnames or 'To' not in reader.fieldnames:
                        raise ValueError("CSV file must have 'From' and 'To' columns")
                    
                    for row in reader:
                        try:
                            rule = CorrectionRule.from_csv_row(row)
                            rules.append(rule)
                        except ValueError as e:
                            # Log the error or handle malformed rows
                            print(f"Error parsing row: {e}")
                
                # If we got here, the file was successfully parsed
                return rules
            except UnicodeDecodeError:
                continue
                
        raise ValueError(f"Could not decode file with any of the supported encodings: {', '.join(encodings)}")
    
    @staticmethod
    def save_rules_to_file(rules: List[CorrectionRule], file_path: Union[str, Path]) -> None:
        """
        Save correction rules to a CSV file.
        
        Args:
            rules (List[CorrectionRule]): The rules to save
            file_path (Union[str, Path]): Path to save to
        """
        file_path = Path(file_path)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Define the fieldnames
            fieldnames = ['From', 'To']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write the header
            writer.writeheader()
            
            # Write the rules
            for rule in rules:
                writer.writerow(rule.to_csv_row()) 