#!/usr/bin/env python
"""
update_pyqt_to_pyside.py

Description: Script to update PyQt5 imports to PySide6
Usage:
    python scripts/update_pyqt_to_pyside.py
"""

import os
import re
from pathlib import Path


def update_imports_in_file(file_path):
    """
    Update PyQt5 imports to PySide6 in a file.

    Args:
        file_path (Path): Path to the file to update

    Returns:
        bool: True if changes were made, False otherwise
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if file contains PyQt5 imports
    if "PyQt5" not in content:
        return False

    # Replace imports
    new_content = re.sub(r"from PyQt5\.(.*) import", r"from PySide6.\1 import", content)
    new_content = re.sub(r"import PyQt5\.", r"import PySide6.", new_content)

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    return False


def main():
    """Update all UI test files to use PySide6 instead of PyQt5."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    ui_tests_dir = project_root / "tests" / "ui"

    # Find all Python files in the UI tests directory
    python_files = list(ui_tests_dir.glob("**/*.py"))

    # Update each file
    updated_files = []
    for file_path in python_files:
        if update_imports_in_file(file_path):
            updated_files.append(file_path.relative_to(project_root))

    # Report results
    if updated_files:
        print(f"Updated {len(updated_files)} files:")
        for file_path in updated_files:
            print(f"  {file_path}")
    else:
        print("No files needed updating.")


if __name__ == "__main__":
    main()
