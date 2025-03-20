"""
test_filter_manager.py

Description: Test for FilterManager class
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from src.services.filters.filter_manager import FilterManager
from src.services.filters.validation_list_filter import ValidationListFilter
from src.services.filters.text_filter import TextFilter
from src.interfaces.i_config_manager import IConfigManager


class TestFilterManager:
    """Tests for FilterManager class."""

    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        """Create a sample DataFrame for testing."""
        data = {
            "player": ["Player1", "Player2", "Player3", "Player1", "Player2"],
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
    def manager(self) -> FilterManager:
        """Create a FilterManager for testing."""
        return FilterManager()

    @pytest.fixture
    def player_filter(self) -> ValidationListFilter:
        """Create a player filter for testing."""
        filter_obj = ValidationListFilter("player", "Player Filter", "player")
        filter_obj.set_selected_values(["Player1"])
        return filter_obj

    @pytest.fixture
    def chest_filter(self) -> ValidationListFilter:
        """Create a chest type filter for testing."""
        filter_obj = ValidationListFilter("chest_type", "Chest Type Filter", "chest_type")
        filter_obj.set_selected_values(["Rare Chest", "Epic Chest"])
        return filter_obj

    @pytest.fixture
    def text_filter(self) -> TextFilter:
        """Create a text filter for testing."""
        filter_obj = TextFilter("text_search", "Text Search")
        filter_obj.set_search_text("Crypt")
        return filter_obj

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """Create a mock ConfigManager."""
        mock = MagicMock(spec=IConfigManager)
        mock.get_value.return_value = ""
        return mock

    def test_initialization(self, manager: FilterManager):
        """Test initialization of FilterManager."""
        assert manager._filters == {}
        assert manager._active_filters == set()

    def test_register_unregister_filter(
        self, manager: FilterManager, player_filter: ValidationListFilter
    ):
        """Test registering and unregistering filters."""
        # Register a filter
        manager.register_filter(player_filter)

        # Check that the filter was registered correctly
        assert len(manager._filters) == 1
        assert manager._filters.get("player") is player_filter
        assert manager._active_filters == {"player"}  # Should be active

        # Unregister the filter
        manager.unregister_filter("player")

        # Check that the filter was unregistered correctly
        assert len(manager._filters) == 0
        assert manager._active_filters == set()

    def test_get_filter(self, manager: FilterManager, player_filter: ValidationListFilter):
        """Test getting a filter by ID."""
        # Register a filter
        manager.register_filter(player_filter)

        # Get the filter by ID
        retrieved_filter = manager.get_filter("player")

        # Check that the correct filter was retrieved
        assert retrieved_filter is player_filter

        # Get a non-existent filter
        non_existent = manager.get_filter("non_existent")

        # Check that None is returned for non-existent filters
        assert non_existent is None

    def test_get_all_filters(
        self,
        manager: FilterManager,
        player_filter: ValidationListFilter,
        chest_filter: ValidationListFilter,
    ):
        """Test getting all registered filters."""
        # Register filters
        manager.register_filter(player_filter)
        manager.register_filter(chest_filter)

        # Get all filters
        all_filters = manager.get_all_filters()

        # Check that all filters were retrieved
        assert len(all_filters) == 2
        assert player_filter in all_filters
        assert chest_filter in all_filters

    def test_apply_filters_single(
        self, manager: FilterManager, player_filter: ValidationListFilter, sample_df: pd.DataFrame
    ):
        """Test applying a single filter."""
        # Register a filter
        manager.register_filter(player_filter)

        # Apply filters
        result_df = manager.apply_filters(sample_df)

        # Check that the filter was applied correctly
        assert len(result_df) == 2
        assert set(result_df["player"].tolist()) == {"Player1"}

    def test_apply_filters_multiple(
        self,
        manager: FilterManager,
        player_filter: ValidationListFilter,
        chest_filter: ValidationListFilter,
        sample_df: pd.DataFrame,
    ):
        """Test applying multiple filters."""
        # Register filters
        manager.register_filter(player_filter)
        manager.register_filter(chest_filter)

        # Apply filters
        result_df = manager.apply_filters(sample_df)

        # Check that both filters were applied correctly
        # Should keep rows where player is 'Player1' AND chest_type is 'Rare Chest' or 'Epic Chest'
        assert len(result_df) == 1
        assert result_df["player"].iloc[0] == "Player1"
        assert result_df["chest_type"].iloc[0] == "Rare Chest"

    def test_apply_filters_empty_result(
        self,
        manager: FilterManager,
        player_filter: ValidationListFilter,
        text_filter: TextFilter,
        sample_df: pd.DataFrame,
    ):
        """Test applying filters that result in an empty DataFrame."""
        # Configure filters to have no matching rows
        player_filter.set_selected_values(["NonExistentPlayer"])

        # Register filters
        manager.register_filter(player_filter)
        manager.register_filter(text_filter)

        # Apply filters
        result_df = manager.apply_filters(sample_df)

        # Check that the result is empty
        assert len(result_df) == 0

    def test_clear_all_filters(
        self,
        manager: FilterManager,
        player_filter: ValidationListFilter,
        chest_filter: ValidationListFilter,
    ):
        """Test clearing all filters."""
        # Register filters
        manager.register_filter(player_filter)
        manager.register_filter(chest_filter)

        # Verify filters are active
        assert manager._active_filters == {"player", "chest_type"}

        # Clear all filters
        manager.clear_all_filters()

        # Check that all filters were cleared
        assert manager._active_filters == set()
        assert player_filter.selected_values == []
        assert chest_filter.selected_values == []

    def test_get_active_filter_count(
        self,
        manager: FilterManager,
        player_filter: ValidationListFilter,
        chest_filter: ValidationListFilter,
    ):
        """Test getting the count of active filters."""
        # Register filters
        manager.register_filter(player_filter)
        manager.register_filter(chest_filter)

        # Check active count
        assert manager.get_active_filter_count() == 2

        # Clear one filter
        player_filter.clear()

        # Check active count again
        assert manager.get_active_filter_count() == 1

        # Clear the other filter
        chest_filter.clear()

        # Check active count again
        assert manager.get_active_filter_count() == 0

    def test_save_load_filter_state(
        self,
        manager: FilterManager,
        player_filter: ValidationListFilter,
        chest_filter: ValidationListFilter,
        mock_config: MagicMock,
    ):
        """Test saving and loading filter state."""
        # Register filters
        manager.register_filter(player_filter)
        manager.register_filter(chest_filter)

        # Save filter state
        manager.save_filter_state(mock_config)

        # Check that config.set_value was called with the correct values
        mock_config.set_value.assert_any_call("Filters", "active_filters", "player,chest_type")

        # Create a new manager and load state
        # First, set up mock to return filter states
        mock_config.get_value = (
            lambda section, key, default=None: {
                "Filters": {
                    "active_filters": "player,chest_type",
                },
                "Filter_player": {
                    "enabled": "True",
                    "selection_type": "include",
                    "case_sensitive": "False",
                    "selected_values": "Player1",
                },
                "Filter_chest_type": {
                    "enabled": "True",
                    "selection_type": "include",
                    "case_sensitive": "False",
                    "selected_values": "Rare Chest,Epic Chest",
                },
            }.get(section, {}).get(key, default)
        )

        # Create new filters and manager
        new_player_filter = ValidationListFilter("player", "Player Filter", "player")
        new_chest_filter = ValidationListFilter("chest_type", "Chest Type Filter", "chest_type")
        new_manager = FilterManager()
        new_manager.register_filter(new_player_filter)
        new_manager.register_filter(new_chest_filter)

        # Load filter state
        new_manager.load_filter_state(mock_config)

        # Check that state was loaded correctly
        assert new_player_filter.enabled is True
        assert new_player_filter.selection_type == "include"
        assert new_player_filter.case_sensitive is False
        assert set(new_player_filter.selected_values) == {"Player1"}

        assert new_chest_filter.enabled is True
        assert new_chest_filter.selection_type == "include"
        assert new_chest_filter.case_sensitive is False
        assert set(new_chest_filter.selected_values) == {"Rare Chest", "Epic Chest"}

        assert new_manager._active_filters == {"player", "chest_type"}
