"""
constants.py

Description: Constants used throughout the application
Usage:
    from src.utils.constants import FIELD_TYPES, DEFAULT_THRESHOLD
"""

from typing import Dict, List, Tuple

# Field types
FIELD_TYPES = ["chest_type", "player", "source"]

# Default threshold for fuzzy matching
DEFAULT_THRESHOLD = 0.85

# UI constants
UI_THEME_COLORS = {
    "dark": {
        "primary": "#2A2356",  # Dark blueish-purple
        "secondary": "#D4AF37",  # Gold
        "background": "#1A1A2E",  # Very dark blue
        "surface": "#242447",  # Dark blue
        "text_primary": "#FFFFFF",  # White
        "text_secondary": "#CCCCCC",  # Light gray
        "error": "#CF6679",  # Pinkish red
        "warning": "#FFC107",  # Amber
        "success": "#4CAF50",  # Green
    },
    "light": {
        "primary": "#5E35B1",  # Deep purple
        "secondary": "#D4AF37",  # Gold
        "background": "#F5F5F5",  # Light gray
        "surface": "#FFFFFF",  # White
        "text_primary": "#212121",  # Very dark gray
        "text_secondary": "#757575",  # Medium gray
        "error": "#B00020",  # Dark red
        "warning": "#FF8F00",  # Dark amber
        "success": "#388E3C",  # Dark green
    }
}

# Application constants
APP_NAME = "Chest Tracker Correction Tool"
APP_VERSION = "0.1.0"

# File extensions
TEXT_FILE_EXTENSION = ".txt"
CSV_FILE_EXTENSION = ".csv"

# Date format for filenames
FILENAME_DATE_FORMAT = "%Y-%m-%d"

# Default directory names
DEFAULT_DIRECTORIES = [
    "data",
    "data/input",
    "data/output",
    "data/corrections",
    "data/validation",
]

# Default validation list names
DEFAULT_VALIDATION_LISTS = {
    "player": "players",
    "chest_type": "chest_types",
    "source": "sources",
} 