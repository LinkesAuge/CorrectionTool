"""
test_config_manager_fixes.py

Description: Tests for ConfigManager's handling of missing sections and keys
Usage:
    python -m pytest tests/test_config_manager_fixes.py -v
"""

import tempfile
import os
from pathlib import Path
import pytest
from unittest.mock import patch

from src.services.config_manager import ConfigManager


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".ini", delete=False) as temp:
        temp_path = Path(temp.name)

    yield temp_path

    # Clean up after test
    if temp_path.exists():
        os.unlink(temp_path)


def test_missing_section_creation(temp_config_file):
    """Test that missing sections are created when accessed."""
    # Create a config manager with our temporary file
    config_manager = ConfigManager(temp_config_file)

    # Try to get a value from a non-existent section/key
    test_section = "TestSection"
    test_key = "test_key"
    default_value = "default_value"

    # Before our fix, this would just return the default value without creating the section
    value = config_manager.get_value(test_section, test_key, default_value)

    # Value should be the default since it doesn't exist yet
    assert value == default_value

    # But now the section and key should have been created
    assert config_manager.has_section(test_section)
    assert config_manager.has_option(test_section, test_key)

    # The value should be stored
    assert config_manager.get_value(test_section, test_key) == default_value


def test_ensure_core_sections_exist(temp_config_file):
    """Test that core sections are properly created."""
    # Create a config manager with our temporary file
    config_manager = ConfigManager(temp_config_file)

    # Core sections that should exist
    core_sections = [
        "Dashboard",
        "CorrectionManager",
        "Window",
        "ValidationPanel",
        "ReportPanel",
        "UI",
    ]

    # Check that all core sections exist
    for section in core_sections:
        assert config_manager.has_section(section), f"Section {section} should exist"

        # Each section should have at least one option
        options = config_manager.get_options(section)
        assert len(options) > 0, f"Section {section} should have options"


def test_get_missing_value_creates_it(temp_config_file):
    """Test that getting a missing value creates it with the default."""
    # Create a config manager with our temporary file
    config_manager = ConfigManager(temp_config_file)

    # Create a new section
    test_section = "TestSection2"

    # Try to get values with different defaults
    string_key = "string_key"
    int_key = "int_key"
    bool_key = "bool_key"

    # Get the values with defaults
    string_value = config_manager.get_value(test_section, string_key, "string_default")
    int_value = config_manager.get_value(test_section, int_key, 42)
    bool_value = config_manager.get_value(test_section, bool_key, True)

    # Values should be the defaults
    assert string_value == "string_default"
    assert int_value == 42
    assert bool_value is True

    # The section and keys should exist
    assert config_manager.has_section(test_section)
    assert config_manager.has_option(test_section, string_key)
    assert config_manager.has_option(test_section, int_key)
    assert config_manager.has_option(test_section, bool_key)

    # Values should be stored as strings
    assert config_manager.config.get(test_section, string_key) == "string_default"
    assert config_manager.config.get(test_section, int_key) == "42"
    assert config_manager.config.get(test_section, bool_key) == "True"


def test_nested_get_value_calls(temp_config_file):
    """Test that nested get_value calls work correctly."""
    # Create a config manager with our temporary file
    with patch("logging.Logger.info") as mock_info:
        config_manager = ConfigManager(temp_config_file)

        # Clear the mock calls from initialization
        mock_info.reset_mock()

        # Get a value from a section that doesn't exist
        non_existent_section = "NonExistentSection"
        key = "some_key"
        value = config_manager.get_value(non_existent_section, key, "default")

        # Section should be created
        assert config_manager.has_section(non_existent_section)

        # Log message should indicate section creation
        mock_info.assert_any_call(f"Creating missing section {non_existent_section} in config")


def test_performance_optimization(temp_config_file):
    """Test that the config manager doesn't save for every get_value call."""
    with patch("src.services.config_manager.ConfigManager.save_config") as mock_save:
        config_manager = ConfigManager(temp_config_file)

        # Clear the mock calls from initialization
        mock_save.reset_mock()

        # First call should create the section and key and save
        config_manager.get_value("TestSection3", "key1", "value1")
        assert mock_save.call_count > 0

        # Reset the mock
        mock_save.reset_mock()

        # Subsequent calls to the same section/key shouldn't save again
        config_manager.get_value("TestSection3", "key1", "value1")
        assert mock_save.call_count == 0
