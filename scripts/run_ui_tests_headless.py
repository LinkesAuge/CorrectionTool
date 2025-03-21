#!/usr/bin/env python3
"""
run_ui_tests_headless.py

Description: Script for running UI tests in headless environments
Usage:
    python scripts/run_ui_tests_headless.py [test_path] [options]
"""

import os
import sys
import argparse
import subprocess
import pytest
from pathlib import Path


def setup_headless_environment():
    """
    Set up the environment for headless testing.
    This sets the necessary environment variables for Qt to run in headless mode.
    """
    # Use offscreen platform for Qt
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    # Disable GPU acceleration
    os.environ["QT_OPENGL"] = "software"

    # Disable accessibility features which might cause issues
    os.environ["QT_ACCESSIBILITY"] = "0"

    # Use a consistent locale for testing
    os.environ["LC_ALL"] = "C"

    print("[INFO] Headless environment variables set")


def run_tests(test_path=None, verbose=False, xvs=False, capture="no"):
    """
    Run the specified UI tests with appropriate options for headless mode.

    Args:
        test_path: Path to test file or directory (runs all UI tests if None)
        verbose: Whether to show verbose output
        xvs: Whether to run with -xvs flags (no capture, verbose, stop on first failure)
        capture: pytest capture method (no/sys/fd)

    Returns:
        int: The pytest exit code
    """
    # Default to all UI tests if no path specified
    if not test_path:
        test_path = "tests/ui"

    # Build pytest arguments
    pytest_args = [test_path]

    if verbose:
        pytest_args.append("-v")

    if xvs:
        pytest_args.extend(["-x", "-v", "-s"])
    else:
        # Set capture mode
        pytest_args.append(f"--capture={capture}")

    # Add headless testing marker
    pytest_args.append("-m")
    pytest_args.append("not requires_display")

    print(f"[INFO] Running tests: {' '.join(pytest_args)}")

    try:
        # Run pytest with the arguments
        result = pytest.main(pytest_args)
        return result
    except Exception as e:
        print(f"[ERROR] Failed to run tests: {e}")
        return 1


def parse_args():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run UI tests in headless mode")
    parser.add_argument(
        "test_path",
        nargs="?",
        default=None,
        help="Path to test file or directory (runs all UI tests if not specified)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    parser.add_argument(
        "-xvs",
        action="store_true",
        help="Run with -xvs flags (no capture, verbose, stop on first failure)",
    )
    parser.add_argument(
        "--capture", choices=["no", "sys", "fd"], default="no", help="pytest capture method"
    )
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_args()

    print("[INFO] Setting up headless environment for UI testing")
    setup_headless_environment()

    print("[INFO] Starting UI tests in headless mode")
    result = run_tests(
        test_path=args.test_path, verbose=args.verbose, xvs=args.xvs, capture=args.capture
    )

    return result


if __name__ == "__main__":
    sys.exit(main())
