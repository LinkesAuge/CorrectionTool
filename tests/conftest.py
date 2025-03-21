"""
conftest.py

Description: Global pytest fixtures for the correction tool tests
Usage:
    This file is automatically loaded by pytest
"""

import pytest


# pytest-qt provides qtbot fixture automatically
# We don't need to define our own QApplication since pytest-qt handles it
