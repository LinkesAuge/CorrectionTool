"""
test_text_filter.py

Description: Test for TextFilter class
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from src.services.filters.text_filter import TextFilter
from src.interfaces.i_config_manager import IConfigManager


class TestTextFilter:
    """Tests for TextFilter class."""

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        """Create a sample DataFrame for testing."""
        data = {
            "player": ["Player1", "Player2", "Player3", "PlayerOne", "Player Two"],
            "chest_type": [
                "Rare Chest",
                "Epic Chest",
                "Common Chest",
                "Legendary Chest",
                "Unique Chest",
            ],
            "source": [
                "Level 10 Crypt",
                "Mercenary Exchange",
                "Daily Reward",
                "Event",
                "Shop Purchase",
            ],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def filter_obj(self) -> TextFilter:
        """Create a TextFilter for testing."""
        return TextFilter("text_filter", "Text Filter")

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """Create a mock ConfigManager."""
        mock = MagicMock(spec=IConfigManager)
        mock.get_value.return_value = ""
        return mock

    def test_initialization(self, filter_obj: TextFilter):
        """Test initialization of TextFilter."""
        assert filter_obj.filter_id == "text_filter"
        assert filter_obj.display_name == "Text Filter"
        assert filter_obj.search_text == ""
        assert filter_obj.target_columns == []
        assert filter_obj.case_sensitive is False
        assert filter_obj.whole_word is False
        assert filter_obj.regex_enabled is False
        assert filter_obj.enabled is True
        assert filter_obj.is_active() is False  # No search text yet

    def test_set_search_text(self, filter_obj: TextFilter):
        """Test setting search text."""
        # Set search text
        filter_obj.set_search_text("Player")

        # Check that search text was set correctly
        assert filter_obj.search_text == "Player"
        assert filter_obj.is_active() is True

    def test_clear(self, filter_obj: TextFilter):
        """Test clearing the filter."""
        # Set search text
        filter_obj.set_search_text("Player")
        assert filter_obj.is_active() is True

        # Clear the filter
        filter_obj.clear()

        # Check that search text was cleared
        assert filter_obj.search_text == ""
        assert filter_obj.is_active() is False

    def test_apply_all_columns(self, filter_obj: TextFilter, sample_df: pd.DataFrame):
        """Test applying the filter to all columns."""
        # Set up filter
        filter_obj.set_search_text("rare")

        # Apply filter
        result_df = filter_obj.apply(sample_df)

        # Check that only rows with 'rare' (case-insensitive) are included
        # In our sample data, only the first row has 'Rare Chest'
        assert len(result_df) == 1
        assert "Rare Chest" in result_df["chest_type"].tolist()

    def test_apply_specific_columns(self, filter_obj: TextFilter, sample_df: pd.DataFrame):
        """Test applying the filter to specific columns."""
        # Set up filter with specific target columns
        filter_obj.target_columns = ["chest_type"]
        filter_obj.set_search_text("Chest")

        # Apply filter
        result_df = filter_obj.apply(sample_df)

        # Check that all rows are included (all chest_type values contain 'Chest')
        assert len(result_df) == 5

        # Change target columns to only look in 'source'
        filter_obj.target_columns = ["source"]

        # Apply filter again
        result_df = filter_obj.apply(sample_df)

        # Check that no rows are included (no source values contain 'Chest')
        assert len(result_df) == 0

    def test_apply_case_sensitive(self, filter_obj: TextFilter, sample_df: pd.DataFrame):
        """Test applying the filter with case sensitivity."""
        # Set up filter with case sensitivity
        filter_obj.set_search_text("player")
        filter_obj.case_sensitive = True

        # Apply filter
        result_df = filter_obj.apply(sample_df)

        # Check that no rows are included (all 'Player' values are capitalized)
        assert len(result_df) == 0

        # Change case sensitivity
        filter_obj.case_sensitive = False

        # Apply filter again
        result_df = filter_obj.apply(sample_df)

        # Check that rows with 'Player' (case-insensitive) are included
        assert len(result_df) == 5

    def test_apply_whole_word(self, filter_obj: TextFilter, sample_df: pd.DataFrame):
        """Test applying the filter with whole word matching."""
        # Set up filter with whole word matching
        filter_obj.set_search_text("Player")
        filter_obj.whole_word = True

        # Apply filter
        result_df = filter_obj.apply(sample_df)

        # Check that only rows with exact 'Player' word are included
        # 'Player1', 'Player2', 'Player3', 'PlayerOne' don't match, only 'Player Two' matches
        assert len(result_df) == 1
        assert "Player Two" in result_df["player"].tolist()

    def test_apply_regex(self, filter_obj: TextFilter, sample_df: pd.DataFrame):
        """Test applying the filter with regex matching."""
        # Set up filter with regex
        filter_obj.set_search_text(r"Player\d")
        filter_obj.regex_enabled = True

        # Apply filter
        result_df = filter_obj.apply(sample_df)

        # Check that only rows with 'Player' followed by a digit are included
        assert len(result_df) == 3
        assert "Player1" in result_df["player"].tolist()
        assert "Player2" in result_df["player"].tolist()
        assert "Player3" in result_df["player"].tolist()
        assert "PlayerOne" not in result_df["player"].tolist()
        assert "Player Two" not in result_df["player"].tolist()

    def test_apply_invalid_regex(self, filter_obj: TextFilter, sample_df: pd.DataFrame):
        """Test applying the filter with invalid regex."""
        # Set up filter with invalid regex
        filter_obj.set_search_text(r"Player[")  # Unmatched bracket in regex
        filter_obj.regex_enabled = True

        # Apply filter - should return the original DataFrame for safety
        result_df = filter_obj.apply(sample_df)

        # Check that the result is the same as the input
        pd.testing.assert_frame_equal(result_df, sample_df)

    def test_enabled_property(self, filter_obj: TextFilter, sample_df: pd.DataFrame):
        """Test the enabled property."""
        # Set up filter
        filter_obj.set_search_text("Player")
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
        assert len(result_df) == 5  # All rows have 'Player' in the player column

    def test_save_load_state(self, filter_obj: TextFilter, mock_config: MagicMock):
        """Test saving and loading filter state."""
        # Set up filter state
        filter_obj.set_search_text("Player")
        filter_obj.target_columns = ["player", "chest_type"]
        filter_obj.case_sensitive = True
        filter_obj.whole_word = True
        filter_obj.regex_enabled = True

        # Save state
        filter_obj.save_state(mock_config)

        # Check that config.set_value was called with the correct values
        mock_config.set_value.assert_any_call("Filter_text_filter", "enabled", "True")
        mock_config.set_value.assert_any_call("Filter_text_filter", "search_text", "Player")
        mock_config.set_value.assert_any_call("Filter_text_filter", "case_sensitive", "True")
        mock_config.set_value.assert_any_call("Filter_text_filter", "whole_word", "True")
        mock_config.set_value.assert_any_call("Filter_text_filter", "regex_enabled", "True")
        mock_config.set_value.assert_any_call(
            "Filter_text_filter", "target_columns", "player,chest_type"
        )

        # Create a new filter and load state
        mock_config.get_value = (
            lambda section, key, default=None: {
                "Filter_text_filter": {
                    "enabled": "True",
                    "search_text": "Player",
                    "case_sensitive": "True",
                    "whole_word": "True",
                    "regex_enabled": "True",
                    "target_columns": "player,chest_type",
                }
            }.get(section, {}).get(key, default)
        )

        new_filter = TextFilter("text_filter", "Text Filter")
        new_filter.load_state(mock_config)

        # Check that state was loaded correctly
        assert new_filter.enabled is True
        assert new_filter.search_text == "Player"
        assert new_filter.case_sensitive is True
        assert new_filter.whole_word is True
        assert new_filter.regex_enabled is True
        assert set(new_filter.target_columns) == {"player", "chest_type"}
