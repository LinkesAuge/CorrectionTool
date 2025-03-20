# Technical Context: Chest Tracker Correction Tool

## Technology Stack

### Core Technologies
- **Python 3.12+**: Main development language
- **PySide6**: Qt-based GUI framework for Python
- **pandas**: Data manipulation and analysis library
- **UV**: Modern Python package manager and environment manager

### Key Libraries
- **fuzzywuzzy**: Fuzzy string matching implementation
- **python-Levenshtein**: Faster implementation of Levenshtein distance for fuzzy matching
- **pathlib**: Object-oriented filesystem path manipulation
- **configparser**: Configuration file parser
- **dataclasses**: Data classes for clean model definitions
- **typing**: Type hints for improved code clarity

### Development Tools
- **pytest**: Testing framework
- **ruff**: Python linter and formatter
- **pyproject.toml**: Project definition and configuration

## Development Environment

### Environment Setup
The project uses UV for dependency management and virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

### Project Configuration
The project is configured through `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "chest-tracker-correction-tool"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pyside6>=6.5.0",
    "pandas>=2.0.0",
    "fuzzywuzzy>=0.18.0",
    "python-Levenshtein>=0.21.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
]
```

## File Management

### Directory Structure
- `src/`: Source code
- `tests/`: Test files
- `data/`: Sample data files and defaults
- `docs/`: Documentation
- `logs/`: Application logs

### Configuration Storage
User configuration is stored in `config.ini`:

```ini
[General]
last_file_path = data/input
last_correction_list_path = data/correction_lists
last_validation_list_path = data/validation_lists

[Paths]
input_directory = data/input
correction_lists_directory = data/correction_lists
validation_lists_directory = data/validation_lists
output_directory = data/output
default_correction_list = data/correction_lists/default.csv
players_validation_list = data/validation_lists/players.txt
chest_types_validation_list = data/validation_lists/chest_types.txt
sources_validation_list = data/validation_lists/sources.txt

[FuzzyMatching]
enabled = true
threshold = 85
use_for_corrections = true
use_for_validation = true
```

## Technical Constraints

### UI Constraints
- Must use PySide6 (Qt) for all GUI components
- Should maintain consistent look and feel across platforms
- Must support dark mode
- Must be responsive to window resizing

### Data Processing Constraints
- Must handle large input files efficiently (1000+ entries)
- Must support CSV format for correction lists
- Must support plain text for validation lists
- Should preserve original file format when exporting

### Performance Requirements
- Input file parsing: < 2 seconds for 1000 entries
- Correction application: < 1 second for 1000 entries
- UI responsiveness: No blocking operations in the UI thread

## External Interfaces

### File Formats

#### Input Text File
The application expects a specific format for input files:
```
Chest Type
From: Player Name
Source: Location
```

Each entry consists of exactly 3 lines.

#### Correction List CSV
Correction lists are CSV files with two columns:
```
From,To
"Error text","Corrected text"
```

#### Validation List TXT
Validation lists are plain text files with one entry per line:
```
ValidEntry1
ValidEntry2
```

### API Integration Points
Currently, the application does not integrate with external APIs. All data is processed locally through files.

## Deployment

### Distribution
The application is intended to be distributed as:
1. Source code (for developers)
2. Standalone executable (for end users)

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux with compatible GUI libraries
- **Processor**: Any modern CPU (2GHz+)
- **Memory**: 4GB RAM minimum
- **Disk Space**: 100MB for installation + space for user data
- **Python**: 3.12+ (if running from source)

## Testing Framework

### Test Strategy
- Unit tests for individual components
- Integration tests for service interactions
- UI tests for critical user workflows
- Performance tests for large dataset handling

### Test Structure
Tests are organized in the `tests/` directory, with a structure mirroring the `src/` directory.

Example test file organization:
```
tests/
├── conftest.py                  # pytest fixtures
├── models/
│   └── test_dataframe_store.py
├── services/
│   ├── test_correction_service.py
│   └── test_validation_service.py
└── ui/
    └── test_dashboard.py
```

### Sample Test Data
The `tests/sample_data/` directory contains test data files:
- Sample input text
- Sample correction lists
- Sample validation lists
- Expected output for test cases 