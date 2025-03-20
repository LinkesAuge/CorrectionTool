"""
base_filter.py

Description: Base class for filter implementations
Usage:
    from src.services.filters.base_filter import BaseFilter

    class MyFilter(BaseFilter):
        def apply(self, df):
            # Filter implementation
"""

import logging
from abc import abstractmethod
from typing import Optional

import pandas as pd

from src.interfaces.i_filter import IFilter
from src.interfaces.i_config_manager import IConfigManager


class BaseFilter(IFilter):
    """
    Base class for all filter implementations.

    Provides common functionality for all filters, such as
    managing filter ID, display name, and logging.

    Attributes:
        _filter_id (str): Unique identifier for the filter
        _display_name (str): User-friendly name for display in UI
        _logger (logging.Logger): Logger for the filter
        _enabled (bool): Whether the filter is enabled
    """

    def __init__(self, filter_id: str, display_name: str):
        """
        Initialize the base filter.

        Args:
            filter_id: Unique identifier for the filter
            display_name: User-friendly name for display in UI
        """
        self._filter_id = filter_id
        self._display_name = display_name
        self._logger = logging.getLogger(f"filters.{filter_id}")
        self._enabled = True

    @property
    def filter_id(self) -> str:
        """
        Get the unique filter identifier.

        Returns:
            Filter ID
        """
        return self._filter_id

    @property
    def display_name(self) -> str:
        """
        Get the display name of the filter.

        Returns:
            Display name
        """
        return self._display_name

    @property
    def enabled(self) -> bool:
        """
        Check if the filter is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """
        Set whether the filter is enabled.

        Args:
            value: True to enable, False to disable
        """
        self._enabled = value

    @abstractmethod
    def is_active(self) -> bool:
        """
        Check if filter is currently active.

        Returns:
            True if filter has active criteria, False otherwise
        """
        pass

    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply filter to a DataFrame and return filtered result.

        Args:
            df: DataFrame to filter

        Returns:
            Filtered DataFrame
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the filter settings."""
        pass

    def save_state(self, config: IConfigManager) -> None:
        """
        Save filter state to configuration.

        Base implementation saves the enabled state.
        Subclasses should call super().save_state(config) and
        add their own state information.

        Args:
            config: Configuration manager to save state to
        """
        section = f"Filter_{self._filter_id}"
        config.set_value(section, "enabled", str(self._enabled))

    def load_state(self, config: IConfigManager) -> None:
        """
        Load filter state from configuration.

        Base implementation loads the enabled state.
        Subclasses should call super().load_state(config) and
        load their own state information.

        Args:
            config: Configuration manager to load state from
        """
        section = f"Filter_{self._filter_id}"
        enabled_str = config.get_value(section, "enabled", "True")
        self._enabled = enabled_str.lower() == "true"

    def __str__(self) -> str:
        """
        Get string representation of the filter.

        Returns:
            String representation
        """
        return f"{self.__class__.__name__}(id={self._filter_id}, name={self._display_name})"
