"""
simple_test_case.py

Description: Simple test file to verify that the testing infrastructure works
Usage:
    pytest tests/ui/simple_test_case.py
"""

import pytest
from PySide6.QtWidgets import QLabel, QApplication


# Simple test case that doesn't depend on complex components
class TestSimpleWidget:
    """Tests for a simple widget."""

    def test_simple_widget(self, qtbot):
        """Test a simple widget."""
        # Create a simple widget
        widget = QLabel("Test Label")
        qtbot.addWidget(widget)

        # Check that the widget has the right text
        assert widget.text() == "Test Label"

        # Check that the widget exists and is initialized
        assert widget is not None
        assert widget.isEnabled() is True


# Another test function to verify we can run multiple tests
def test_simple_function():
    """Test a simple function."""
    assert 1 + 1 == 2
    assert "test" == "test"
    assert len([1, 2, 3]) == 3
