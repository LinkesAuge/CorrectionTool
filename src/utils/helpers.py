"""
helpers.py

Description: Helper functions used throughout the application
Usage:
    from src.utils.helpers import get_unique_entries, format_stats
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

from src.models.chest_entry import ChestEntry
from src.utils.constants import FILENAME_DATE_FORMAT


def get_unique_entries(entries: List[ChestEntry], field: str) -> List[str]:
    """
    Get a list of unique values for a specific field across all entries.
    
    Args:
        entries (List[ChestEntry]): The entries to process
        field (str): The field to extract ('chest_type', 'player', or 'source')
        
    Returns:
        List[str]: List of unique values, sorted alphabetically
        
    Raises:
        ValueError: If field is not valid
    """
    if field not in ['chest_type', 'player', 'source']:
        raise ValueError(f"Invalid field: {field}")
    
    unique_values = set()
    
    for entry in entries:
        unique_values.add(entry.get_field(field))
    
    return sorted(list(unique_values))


def format_stats(stats: Dict[str, int]) -> str:
    """
    Format statistics as a human-readable string.
    
    Args:
        stats (Dict[str, int]): Dictionary of statistics
        
    Returns:
        str: Formatted statistics text
    """
    lines = [
        f"Entries processed: {stats.get('entries_processed', 0)}",
        f"Entries corrected: {stats.get('entries_corrected', 0)}",
        f"Corrections made: {stats.get('corrections_made', 0)}",
    ]
    
    # Calculate percentage if possible
    if stats.get('entries_processed', 0) > 0:
        percentage = (stats.get('entries_corrected', 0) / stats.get('entries_processed', 0)) * 100
        lines.append(f"Correction rate: {percentage:.2f}%")
    
    return "\n".join(lines)


def extract_date_from_filename(filename: Union[str, Path]) -> Union[datetime, None]:
    """
    Extract date from a filename.
    
    Expected format: chests_YYYY-MM-DD.txt or similar
    
    Args:
        filename (Union[str, Path]): Filename or path
        
    Returns:
        Union[datetime, None]: Extracted date or None if not found
    """
    if isinstance(filename, Path):
        filename = filename.name
    
    # Look for date pattern YYYY-MM-DD
    import re
    pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(pattern, filename)
    
    if match:
        date_str = match.group(1)
        try:
            return datetime.strptime(date_str, FILENAME_DATE_FORMAT)
        except ValueError:
            return None
    
    return None


def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory (Union[str, Path]): Directory path
        
    Returns:
        Path: Path object for the directory
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def setup_logging(log_file: Union[str, Path] = None, level: int = logging.INFO) -> None:
    """
    Setup logging for the application.
    
    Args:
        log_file (Union[str, Path], optional): Path to log file
        level (int, optional): Logging level
    """
    handlers = []
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    handlers.append(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        handlers.append(file_handler)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    ) 