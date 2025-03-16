# Chest Tracker Correction Tool

A Python application for correcting and managing OCR-generated text data from the Total Battle game. The tool helps fix errors in text extraction, specifically for chest entries data.

## Features

- Load and process OCR-generated text files containing chest entries
- Apply corrections based on a CSV template
- Use fuzzy matching to detect and correct similar but not identical errors
- Manage validation lists for players, chest types, and sources
- Process multiple files while maintaining date-based organization
- Generate statistics and reports on corrections

## Requirements

- Python 3.12+
- PySide6
- Additional dependencies listed in pyproject.toml

## Getting Started

1. Clone this repository
2. Install dependencies:
   ```
   uv pip install -e .
   ```
3. Run the application:
   ```
   python main.py
   ```

## Project Structure

The application follows a modular structure:
- `src/models`: Data models for chest entries, correction rules, etc.
- `src/services`: Business logic for file parsing, correction, etc.
- `src/ui`: User interface components
- `src/utils`: Utility functions and constants

## License

[MIT License](LICENSE)
