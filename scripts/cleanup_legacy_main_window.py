#!/usr/bin/env python3
"""
cleanup_legacy_main_window.py

Description: Script to safely remove legacy main window implementations
Usage:
    python scripts/cleanup_legacy_main_window.py [--check-only]
"""

import os
import sys
import logging
import shutil
from pathlib import Path
import subprocess
import re
import argparse
from datetime import datetime
from typing import List, Optional

# Configure logging
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[logging.FileHandler("legacy_cleanup.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Define legacy files to remove
LEGACY_FILES = ["src/ui/main_window.py", "src/ui/main_window_refactor.py"]

# Define backup directory
BACKUP_DIR = Path("backups/legacy_main_window")


def find_references(file_path: Path) -> List[Path]:
    """
    Find references to a file in the codebase.

    Args:
        file_path: Path to the file to search for references to

    Returns:
        List of file paths that reference the file
    """
    file_name = file_path.name
    module_name = file_path.stem

    logger.info(f"Looking for references to {module_name}")

    # Get paths to search in
    search_paths = [
        Path("src"),
        Path("tests"),
        Path("scripts"),
        Path("run_app.py"),
        Path("run_interface_app.py"),
        Path("run_refactored_app.py"),
        Path("main.py"),
    ]

    references = []

    # Common import patterns to search for
    import_patterns = [
        f"from src.ui.{module_name} import",
        f"import src.ui.{module_name}",
        f"from src.ui import {module_name}",
        f"{module_name}.py",
    ]

    # Exclude the file itself, backups, and the cleanup script
    excluded_paths = [
        file_path,
        Path("backups"),
        Path("scripts/cleanup_legacy_main_window.py"),
        Path(__file__),  # Current script path
    ]

    for search_path in search_paths:
        if not search_path.exists():
            logger.warning(f"Search path {search_path} does not exist")
            continue

        if search_path.is_file():
            # Skip if the file is an excluded path
            if any(str(search_path) == str(excl) for excl in excluded_paths):
                logger.info(f"Skipping excluded file: {search_path}")
                continue
            files_to_check = [search_path]
        else:
            files_to_check = []
            for p in search_path.glob("**/*.py"):
                # Skip if the file is in excluded paths
                should_exclude = False
                for excl in excluded_paths:
                    if str(p) == str(excl):
                        logger.info(f"Skipping excluded file: {p}")
                        should_exclude = True
                        break
                if not should_exclude:
                    files_to_check.append(p)

        for check_file in files_to_check:
            try:
                with open(check_file, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Check if file contains any of the import patterns
                    if any(pattern in content for pattern in import_patterns):
                        logger.info(f"Found reference in: {check_file}")
                        references.append(check_file)
            except UnicodeDecodeError:
                logger.warning(f"Could not read {check_file} - not a text file")
            except Exception as e:
                logger.error(f"Error reading {check_file}: {e}")

    return references


def create_backup(file_path: Path) -> Optional[Path]:
    """
    Create a backup of a file.

    Args:
        file_path: Path to the file to backup

    Returns:
        Path to the backup file, or None if backup failed
    """
    if not file_path.exists():
        logger.warning(f"Cannot backup non-existent file: {file_path}")
        return None

    # Create backup directory if it doesn't exist
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Create backup file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"{file_path.stem}_{timestamp}{file_path.suffix}"

    try:
        # Copy file to backup
        shutil.copy2(file_path, backup_file)
        logger.info(f"Created backup: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None


def run_tests() -> bool:
    """
    Run tests to ensure the application still works.

    Returns:
        True if tests pass, False otherwise
    """
    logger.info("Running tests...")

    # Try different ways to run pytest based on the environment
    commands = [
        [sys.executable, "-m", "pytest"],  # Using the current Python interpreter
        ["pytest"],  # If pytest is in PATH
        [".venv/Scripts/pytest"],  # Using virtual environment on Windows
        [".venv/bin/pytest"],  # Using virtual environment on Unix
    ]

    for cmd in commands:
        try:
            logger.info(f"Trying to run tests with: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            # Check if tests passed
            if result.returncode == 0:
                logger.info("Tests passed")
                return True
            else:
                logger.warning(f"Tests failed with command {cmd}")
        except Exception as e:
            logger.warning(f"Error running tests with {cmd}: {e}")

    logger.error("All test run attempts failed")
    return False


def main() -> int:
    """
    Main function to handle file removal.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Safely remove legacy main window files")
    parser.add_argument(
        "--check-only", action="store_true", help="Check for references but don't delete files"
    )
    parser.add_argument(
        "--skip-tests", action="store_true", help="Skip running tests (use with caution)"
    )
    args = parser.parse_args()

    logger.info("Starting legacy main window cleanup")

    # Run tests first to ensure the application works
    if not args.skip_tests:
        if not run_tests():
            logger.error("Tests failed, aborting cleanup")
            logger.info("Use --skip-tests to bypass test verification (use with caution)")
            return 1
    else:
        logger.warning("Skipping test verification as requested")

    # Check for references to legacy files
    has_references = False
    for file_path_str in LEGACY_FILES:
        file_path = Path(file_path_str)
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue

        references = find_references(file_path)
        if references:
            has_references = True
            logger.warning(f"Found references to {file_path}:")
            for ref in references:
                logger.warning(f"  - {ref}")

    # Don't proceed with removal if there are references or in check-only mode
    if has_references:
        logger.error("Cannot safely remove files with existing references")
        return 1

    if args.check_only:
        logger.info("Check-only mode, not removing files")
        if not has_references:
            logger.info("No references found. Files can be safely removed.")
        return 0

    # Create backups and remove files
    for file_path_str in LEGACY_FILES:
        file_path = Path(file_path_str)
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue

        # Create backup
        backup_file = create_backup(file_path)
        if not backup_file:
            logger.error(f"Failed to create backup for {file_path}, skipping removal")
            continue

        # Remove file
        try:
            file_path.unlink()
            logger.info(f"Removed file: {file_path}")
        except Exception as e:
            logger.error(f"Error removing file {file_path}: {e}")
            return 1

    # Run tests again to ensure everything still works
    if not args.skip_tests:
        if not run_tests():
            logger.error("Tests failed after file removal, consider restoring from backups")
            return 1
    else:
        logger.warning("Skipping final test verification as requested")

    logger.info("Legacy main window cleanup completed successfully")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
