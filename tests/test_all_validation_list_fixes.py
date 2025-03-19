#!/usr/bin/env python
"""
Test All Validation List Fixes

Description: Comprehensive test of validation list functionality including CSV and TXT imports
"""

import sys
import os
import logging
import traceback
from pathlib import Path

# Add the parent directory to the Python path so we can import the src module
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging - but set level to WARNING to reduce noisy output during tests
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def test_csv_import():
    """Test importing validation lists from CSV files."""
    try:
        print("\n===== Testing CSV file import =====")
        from src.models.validation_list import ValidationList

        # Test standard corrections CSV file
        corrections_file = "data/corrections/standard_corrections.csv"
        assert Path(corrections_file).exists(), (
            f"ERROR: Corrections file {corrections_file} not found"
        )

        print(f"Importing corrections list from {corrections_file}")
        corrections_list = ValidationList.load_from_file(corrections_file, list_type="corrections")

        print(f"Loaded corrections list with {len(corrections_list.entries)} entries")
        print(f"List type: {corrections_list.list_type}")
        print(f"List name: {corrections_list.name}")

        # Verify the list
        assert corrections_list.list_type == "corrections", (
            f"List type should be corrections, got {corrections_list.list_type}"
        )
        assert len(corrections_list.entries) > 0, "Corrections list should have entries"

        print("CSV import test PASSED")
    except Exception as e:
        print(f"Test failed: {str(e)}")
        print(traceback.format_exc())
        assert False, f"Test failed: {str(e)}"


def test_text_import():
    """Test importing player lists from plain text files."""
    try:
        print("\n===== Testing text file import =====")
        from src.models.validation_list import ValidationList

        # Test each type of validation list
        test_types = [
            ("player", "data/validation/players.txt"),
            ("chest_type", "data/validation/chest_types.txt"),
            ("source", "data/validation/sources.txt"),
        ]

        for list_type, file_path in test_types:
            assert Path(file_path).exists(), f"ERROR: Test file {file_path} not found"

            print(f"\nCase: Importing {list_type} from {file_path}")
            validation_list = ValidationList.load_from_file(file_path, list_type=list_type)

            print(f"Loaded {list_type} list with {len(validation_list.entries)} entries")
            print(f"List type: {validation_list.list_type}")
            print(f"List name: {validation_list.name}")

            # Display first few entries for verification
            # Convert set to list for display since sets are not subscriptable
            if validation_list.entries:
                entries_list = list(validation_list.entries)
                print(f"First 5 entries: {entries_list[:5]}")

            # Verify the list
            assert validation_list.list_type == list_type, (
                f"List type should be {list_type}, got {validation_list.list_type}"
            )
            assert len(validation_list.entries) > 0, f"List should have entries"

        print("\nText import test PASSED")
    except Exception as e:
        print(f"Test failed: {str(e)}")
        print(traceback.format_exc())
        assert False, f"Test failed: {str(e)}"


def test_input_data():
    """Test loading and processing input data."""
    temp_file = Path("data/input/chests_test.txt")
    try:
        print("\n===== Testing input data loading =====")
        assert temp_file.exists(), f"ERROR: Input file {temp_file} not found"

        # Read the input file to verify it exists and can be read
        with open(temp_file, "r") as f:
            content = f.read()
            lines = content.splitlines()
            print(f"Input file has {len(lines)} lines")

            # Check if the file has content
            assert len(lines) > 0, "ERROR: Input file is empty"

            # Display a sample of the content
            print("Sample content:")
            for i in range(min(6, len(lines))):
                print(f"  Line {i + 1}: {lines[i]}")

        print("Input data test PASSED")
    except Exception as e:
        print(f"Test failed: {str(e)}")
        print(traceback.format_exc())
        assert False, f"Test failed: {str(e)}"


def main():
    """Run all tests and report results."""
    csv_success = True
    text_success = True
    input_success = True

    try:
        # Run each test
        test_csv_import()
    except AssertionError:
        csv_success = False

    try:
        test_text_import()
    except AssertionError:
        text_success = False

    try:
        test_input_data()
    except AssertionError:
        input_success = False

    success = csv_success and text_success and input_success

    if success:
        print("\n===== All tests PASSED =====")
        return 0
    else:
        print("\n===== Some tests FAILED =====")
        if not csv_success:
            print("- CSV import test failed")
        if not text_success:
            print("- Text import test failed")
        if not input_success:
            print("- Input data test failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    print(f"Exiting with code: {exit_code}")
    sys.exit(exit_code)
