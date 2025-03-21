#!/usr/bin/env python
"""
run_ui_tests.py

Description: Script to run UI tests with proper environment setup
Usage:
    python scripts/run_ui_tests.py
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def setup_environment():
    """Set up the environment for Qt-based UI testing."""
    # Get project root
    project_root = str(Path(__file__).parent.parent.absolute())

    # Set Qt environment variables to ensure proper testing environment
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QT_QPA_FONTDIR"] = str(Path(project_root) / "resources" / "fonts")

    # Set PYTHONPATH to include the project root directory
    os.environ["PYTHONPATH"] = project_root
    print(f"Setting PYTHONPATH to {project_root}")

    # Make sure we're using python from the same environment
    python = sys.executable

    # Return the configured python path
    return python


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run UI tests for the Correction Tool")
    parser.add_argument(
        "-k", "--keyword", help="Only run tests which match the given substring expression"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase verbosity")
    parser.add_argument("-m", "--markers", help="Only run tests matching given marker expression")
    parser.add_argument("--component", action="store_true", help="Run only component tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument(
        "--collect-only", action="store_true", help="Only collect tests, don't execute them"
    )

    return parser.parse_args()


def run_ui_tests(args):
    """
    Run the UI tests with the given arguments.

    Args:
        args: Command line arguments
    """
    python = setup_environment()

    # Build pytest command
    cmd = [python, "-m", "pytest"]

    # Add verbosity
    if args.verbose:
        cmd.append("-v")

    # Add test collection only
    if args.collect_only:
        cmd.append("--collect-only")

    # Add keyword filtering
    if args.keyword:
        cmd.extend(["-k", args.keyword])

    # Add marker filtering
    if args.markers:
        cmd.extend(["-m", args.markers])
    elif args.component:
        cmd.extend(["-m", "component"])
    elif args.integration:
        cmd.extend(["-m", "integration"])

    # Always provide some basic test information
    cmd.append("-v")

    # Target UI tests directory
    cmd.append("tests/ui/")

    # Add colored output for better readability
    cmd.append("--color=yes")

    # Print the command for debugging
    print(f"Running: {' '.join(cmd)}")

    # Run the tests
    process = subprocess.run(cmd)

    return process.returncode


def main():
    """Run the UI tests."""
    args = parse_args()
    return run_ui_tests(args)


if __name__ == "__main__":
    sys.exit(main())
