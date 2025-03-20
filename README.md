# Chest Tracker Correction Tool

A Python application for correcting and managing OCR-generated text data from the Total Battle game. The tool helps fix errors in text extraction, specifically for chest entries data.

## Features

- Load and process OCR-generated text files containing chest entries
- Apply corrections based on a CSV template
- Use fuzzy matching to detect and correct similar but not identical errors
- Manage validation lists for players, chest types, and sources
- Process multiple files while maintaining date-based organization
- Generate statistics and reports on corrections
- Advanced filtering system with:
  - Text search across multiple columns
  - Multi-select dropdown filters
  - Date range filters
  - Filter state persistence between sessions

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
  - `src/services/filters`: Filtering implementations for data manipulation
- `src/ui`: User interface components
  - `src/ui/widgets/filters`: UI components for filtering
- `src/utils`: Utility functions and constants
- `docs`: Documentation, including the filtering system guide

## Documentation

For more details on specific components:
- [Filtering System](docs/filtering_system.md): Advanced filtering capabilities
- [Data Models](docs/data_models.md): Data structures and relationships

## License

[MIT License](LICENSE)
