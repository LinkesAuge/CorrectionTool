"""
filter_manager.py

Description: Manager for filter implementations
Usage:
    from src.services.filters.filter_manager import FilterManager

    manager = FilterManager()
    manager.register_filter("search", search_filter)
    filtered_df = manager.apply_filters(df)
"""

import logging
from typing import Dict, List, Set, Any, Optional

import pandas as pd

from src.interfaces.i_config_manager import IConfigManager
from src.services.filters.base_filter import BaseFilter


class FilterManager:
    """
    Manager for filter implementations.

    Manages multiple filter implementations and applies them to a DataFrame.

    Attributes:
        _filters (Dict[str, BaseFilter]): Dictionary of registered filters
    """

    def __init__(self):
        """Initialize the filter manager."""
        self._filters: Dict[str, BaseFilter] = {}
        self._logger = logging.getLogger("filters.manager")

    def register_filter(self, filter_id: str, filter_obj: BaseFilter) -> None:
        """
        Register a filter with the manager.

        Args:
            filter_id: Unique identifier for the filter
            filter_obj: Filter implementation to register
        """
        if filter_id in self._filters:
            self._logger.warning(f"Filter with ID '{filter_id}' already registered, replacing")

        self._filters[filter_id] = filter_obj
        self._logger.debug(f"Registered filter '{filter_id}'")

    def unregister_filter(self, filter_id: str) -> None:
        """
        Unregister a filter from the manager.

        Args:
            filter_id: Identifier of the filter to unregister
        """
        if filter_id in self._filters:
            del self._filters[filter_id]
            self._logger.debug(f"Unregistered filter '{filter_id}'")
        else:
            self._logger.warning(f"No filter with ID '{filter_id}' found to unregister")

    def get_filter(self, filter_id: str) -> Optional[BaseFilter]:
        """
        Get a filter by its ID.

        Args:
            filter_id: Identifier of the filter to get

        Returns:
            The filter object if found, None otherwise
        """
        return self._filters.get(filter_id)

    def apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all active filters to a DataFrame.

        Filters are applied in the order they were registered.

        Args:
            df: DataFrame to filter

        Returns:
            Filtered DataFrame
        """
        if df is None or df.empty:
            return df

        result_df = df.copy()

        active_filters = 0

        # Apply each filter in the order they were registered
        for filter_id, filter_obj in self._filters.items():
            if filter_obj.is_active():
                active_filters += 1
                try:
                    result_df = filter_obj.apply(result_df)
                    self._logger.debug(
                        f"Applied filter '{filter_id}': {len(result_df)} of {len(df)} rows remaining"
                    )
                except Exception as e:
                    self._logger.error(f"Error applying filter '{filter_id}': {e}")

        self._logger.info(
            f"Applied {active_filters} active filters: {len(result_df)} of {len(df)} rows remaining"
        )

        return result_df

    def clear_all_filters(self) -> None:
        """Clear all filters in the manager."""
        for filter_id, filter_obj in self._filters.items():
            filter_obj.clear()

        self._logger.debug("All filters cleared")

    def get_active_filter_count(self) -> int:
        """
        Get the number of active filters.

        Returns:
            Number of active filters
        """
        return sum(1 for filter_obj in self._filters.values() if filter_obj.is_active())

    def get_active_filters(self) -> Dict[str, BaseFilter]:
        """
        Get all active filters.

        Returns:
            Dictionary of active filters by ID
        """
        return {
            filter_id: filter_obj
            for filter_id, filter_obj in self._filters.items()
            if filter_obj.is_active()
        }

    def save_filter_state(self, config: IConfigManager) -> None:
        """
        Save the state of all filters using the provided configuration manager.

        Args:
            config: Configuration manager to save state to
        """
        if not config:
            self._logger.warning("No configuration manager provided, filter state not saved")
            return

        try:
            # Save each filter's state
            for filter_id, filter_obj in self._filters.items():
                filter_obj.save_state(config)

            self._logger.debug(f"Saved state for {len(self._filters)} filters")
        except Exception as e:
            self._logger.error(f"Error saving filter state: {e}")

    def load_filter_state(self, config: IConfigManager) -> None:
        """
        Load the state of all filters using the provided configuration manager.

        Args:
            config: Configuration manager to load state from
        """
        if not config:
            self._logger.warning("No configuration manager provided, filter state not loaded")
            return

        try:
            # Load each filter's state
            for filter_id, filter_obj in self._filters.items():
                filter_obj.load_state(config)

            active_count = self.get_active_filter_count()
            self._logger.debug(
                f"Loaded state for {len(self._filters)} filters, {active_count} active"
            )
        except Exception as e:
            self._logger.error(f"Error loading filter state: {e}")
