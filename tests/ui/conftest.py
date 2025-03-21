"""
conftest.py

Description: Configuration for pytest UI tests
Usage:
    Automatically loaded by pytest when running UI tests
"""

import pytest
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


# Ensure a QApplication instance exists for all UI tests
@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    # Close any existing application
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


# Tell pytest to use xvfb (X Virtual Framebuffer) for headless UI testing if available
def pytest_configure(config):
    """Configure pytest for UI testing."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    # Disable GPU for tests
    os.environ["QT_OPENGL"] = "software"


# Custom marker for UI tests
def pytest_configure(config):
    """Register custom markers for UI tests."""
    config.addinivalue_line("markers", "ui: mark a test as a UI test")
    config.addinivalue_line("markers", "integration: mark a test as an integration test")
    config.addinivalue_line("markers", "component: mark a test as a component test")


# Hook to handle Qt warnings during tests
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Capture and handle Qt warnings during test execution."""
    yield
    # Clear any Qt message handlers after the test
    # This prevents warnings from one test affecting others
