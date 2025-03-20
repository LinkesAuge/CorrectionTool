"""
test_validation_list_filter.py

Description: Test for ValidationListFilter class
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from src.services.filters.validation_list_filter import ValidationListFilter
from src.interfaces.i_config_manager import IConfigManager


class TestValidationListFilter:
    """Tests for ValidationListFilter class."""

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        """Create a sample DataFrame for testing."""
        data = {
            "player": ["Player1", "Player2", "Player3", "Player1", "Player2"],
            "chest_type": ["Type1", "Type2", "Type1", "Type3", "Type2"],
            "source": ["Source1", "Source2", "Source3", "Source1", "Source2"],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def filter_obj(self) -> ValidationListFilter:
        """Create a ValidationListFilter for testing."""
        return ValidationListFilter("player_filter", "Player Filter", "player")

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """Create a mock ConfigManager."""
        mock = MagicMock(spec=IConfigManager)
        mock.get_value.return_value = ""
        return mock

    def test_initialization(self, filter_obj: ValidationListFilter):
        """Test initialization of ValidationListFilter."""
        assert filter_obj.filter_id == "player_filter"
        assert filter_obj.display_name == "Player Filter"
        assert filter_obj.column_name == "player"
        assert filter_obj.selected_values == []
        assert filter_obj.selection_type == "include"
        assert filter_obj.case_sensitive is False
        assert filter_obj.enabled is True
        assert filter_obj.is_active() is False  # No selected values yet

    def test_set_selected_values(self, filter_obj: ValidationListFilter):
        """Test setting selected values."""
        # Set selected values
        filter_obj.set_selected_values(["Player1", "Player2"])

        # Check that values were set correctly
        assert set(filter_obj.selected_values) == {"Player1", "Player2"}
        assert filter_obj.is_active() is True

    def test_add_remove_selected_value(self, filter_obj: ValidationListFilter):
        """Test adding and removing selected values."""
        # Add values one by one
        filter_obj.add_selected_value("Player1")
        filter_obj.add_selected_value("Player2")

        # Check that values were added correctly
        assert set(filter_obj.selected_values) == {"Player1", "Player2"}

        # Remove a value
        filter_obj.remove_selected_value("Player1")

        # Check that value was removed correctly
        assert filter_obj.selected_values == ["Player2"]

        # Try to remove a value that doesn't exist (should not raise an error)
        filter_obj.remove_selected_value("NonExistentPlayer")

    def test_clear(self, filter_obj: ValidationListFilter):
        """Test clearing the filter."""
        # Set selected values
        filter_obj.set_selected_values(["Player1", "Player2"])
        assert filter_obj.is_active() is True

        # Clear the filter
        filter_obj.clear()

        # Check that values were cleared
        assert filter_obj.selected_values == []
        assert filter_obj.is_active() is False

    def test_apply_include_case_insensitive(
        self, filter_obj: ValidationListFilter, sample_df: pd.DataFrame
    ):
        """Test applying the filter with include mode and case-insensitive matching."""
        # Set up filter
        filter_obj.set_selected_values(
            ["player1", "player2"]
        )  # Lowercase for testing case insensitivity
        filter_obj.selection_type = "include"
        filter_obj.case_sensitive = False

        # Apply filter
        result_df = filter_obj.apply(sample_df)

        # Check that only rows with Player1 or Player2 are included
        assert len(result_df) == 4
        assert set(result_df["player"].tolist()) == {"Player1", "Player2"}

    def test_apply_exclude_case_sensitive(
        self, filter_obj: ValidationListFilter, sample_df: pd.DataFrame
    ):
        """Test applying the filter with exclude mode and case-sensitive matching."""
        # Set up filter
        filter_obj.set_selected_values(["Player1"])
        filter_obj.selection_type = "exclude"
        filter_obj.case_sensitive = True

        # Apply filter
        result_df = filter_obj.apply(sample_df)

        # Check that rows with Player1 are excluded
        assert len(result_df) == 3
        assert "Player1" not in result_df["player"].tolist()
        assert set(result_df["player"].tolist()) == {"Player2", "Player3"}

    def test_apply_invalid_column(self, filter_obj: ValidationListFilter):
        """Test applying the filter with an invalid column name."""
        # Set up filter with a column that doesn't exist
        filter_obj = ValidationListFilter("invalid_filter", "Invalid Filter", "nonexistent_column")
        filter_obj.set_selected_values(["Value1"])

        # Create a sample DataFrame
        df = pd.DataFrame({"column1": ["Value1", "Value2"]})

        # Apply filter - should return the original DataFrame
        result_df = filter_obj.apply(df)

        # Check that the result is the same as the input
        pd.testing.assert_frame_equal(result_df, df)

    def test_enabled_property(self, filter_obj: ValidationListFilter, sample_df: pd.DataFrame):
        """Test the enabled property."""
        # Set up filter
        filter_obj.set_selected_values(["Player1"])
        assert filter_obj.is_active() is True

        # Disable the filter
        filter_obj.enabled = False
        assert filter_obj.is_active() is False

        # Apply filter - should return the original DataFrame when disabled
        result_df = filter_obj.apply(sample_df)
        pd.testing.assert_frame_equal(result_df, sample_df)

        # Re-enable the filter
        filter_obj.enabled = True
        assert filter_obj.is_active() is True

        # Apply filter - should now filter the DataFrame
        result_df = filter_obj.apply(sample_df)
        assert len(result_df) < len(sample_df)

    def test_save_load_state(self, filter_obj: ValidationListFilter, mock_config: MagicMock):
        """Test saving and loading filter state."""
        # Set up filter state
        filter_obj.set_selected_values(["Player1", "Player2"])
        filter_obj.selection_type = "exclude"
        filter_obj.case_sensitive = True

        # Save state
        filter_obj.save_state(mock_config)

        # Check that config.set_value was called with the correct values
        mock_config.set_value.assert_any_call("Filter_player_filter", "enabled", "True")
        mock_config.set_value.assert_any_call("Filter_player_filter", "selection_type", "exclude")
        mock_config.set_value.assert_any_call("Filter_player_filter", "case_sensitive", "True")

        # Check that selected_values was saved (order might vary)
        selected_values_calls = [
            call
            for call in mock_config.set_value.call_args_list
            if call[0][0] == "Filter_player_filter" and call[0][1] == "selected_values"
        ]
        assert len(selected_values_calls) == 1
        saved_values = selected_values_calls[0][0][2]
        assert "Player1" in saved_values
        assert "Player2" in saved_values

        # Create a new filter and load state
        mock_config.get_value = (
            lambda section, key, default=None: {
                "Filter_player_filter": {
                    "enabled": "True",
                    "selection_type": "exclude",
                    "case_sensitive": "True",
                    "selected_values": "Player1,Player2",
                }
            }.get(section, {}).get(key, default)
        )

        new_filter = ValidationListFilter("player_filter", "Player Filter", "player")
        new_filter.load_state(mock_config)

        # Check that state was loaded correctly
        assert new_filter.enabled is True
        assert new_filter.selection_type == "exclude"
        assert new_filter.case_sensitive is True
        assert set(new_filter.selected_values) == {"Player1", "Player2"}
