#!/usr/bin/env python
"""
run_ui_tests.py

Description: Script to run UI tests with proper configuration
Usage:
    python scripts/run_ui_tests.py [options]

Options:
    --verbose, -v: Show detailed test output
    --component: Run only component tests
    --integration: Run only integration tests
    --all: Run all tests (default)
    --file=PATH: Run tests from a specific file
    --help, -h: Show this help message
"""

import sys
import subprocess
import argparse
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run UI tests for Correction Tool")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed test output")
    parser.add_argument("--component", action="store_true", help="Run only component tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--file", type=str, help="Run tests from a specific file")

    return parser.parse_args()


def build_pytest_command(args):
    """Build the pytest command based on arguments."""
    cmd = ["pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-v")

    # Add test selection
    if args.file:
        cmd.append(args.file)
    elif args.component:
        cmd.append("tests/ui/components/")
    elif args.integration:
        cmd.append("tests/ui/integration/")
    else:
        cmd.append("tests/ui/")

    # Add markers if needed
    if args.component:
        cmd.append("-m")
        cmd.append("component")
    elif args.integration:
        cmd.append("-m")
        cmd.append("integration")

    # Always show summary
    cmd.append("-v")

    return cmd


def main():
    """Run the UI tests."""
    args = parse_args()

    print("Starting UI tests...")
    print("==========================================")

    cmd = build_pytest_command(args)
    print(f"Running command: {' '.join(cmd)}")
    print("==========================================")

    result = subprocess.run(cmd)

    print("==========================================")
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with return code {result.returncode}")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
