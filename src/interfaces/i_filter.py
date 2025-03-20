"""
i_filter.py

Description: Interfaces for the filter system
Usage:
    from src.interfaces.i_filter import IFilter, IFilterManager

    class MyFilter(IFilter):
        def apply(self, df):
            # Filter implementation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set, Union
import pandas as pd

from src.interfaces.i_config_manager import IConfigManager


class IFilter(ABC):
    """
    Interface for filter implementations.

    Defines the contract for all filter classes in the system.
    Each filter must be able to apply itself to a DataFrame,
    report whether it's active, clear its settings, and save/load state.

    Attributes:
        filter_id (str): Unique identifier for the filter
        display_name (str): User-friendly name for display in UI
    """

    @property
    @abstractmethod
    def filter_id(self) -> str:
        """Get the unique filter identifier."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Get the display name of the filter."""
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
    def is_active(self) -> bool:
        """
        Check if filter is currently active.

        Returns:
            True if filter has active criteria, False otherwise
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the filter settings."""
        pass

    @abstractmethod
    def save_state(self, config: IConfigManager) -> None:
        """
        Save filter state to configuration.

        Args:
            config: Configuration manager to save state to
        """
        pass

    @abstractmethod
    def load_state(self, config: IConfigManager) -> None:
        """
        Load filter state from configuration.

        Args:
            config: Configuration manager to load state from
        """
        pass


class IFilterManager(ABC):
    """
    Interface for managing multiple filters.

    Defines the contract for the filter manager class that orchestrates
    the application of multiple filters and handles their lifecycle.
    """

    @abstractmethod
    def register_filter(self, filter_obj: IFilter) -> None:
        """
        Register a new filter.

        Args:
            filter_obj: Filter to register
        """
        pass

    @abstractmethod
    def unregister_filter(self, filter_id: str) -> None:
        """
        Unregister a filter by ID.

        Args:
            filter_id: ID of filter to unregister
        """
        pass

    @abstractmethod
    def get_filter(self, filter_id: str) -> Optional[IFilter]:
        """
        Get a filter by ID.

        Args:
            filter_id: ID of filter to retrieve

        Returns:
            Filter object or None if not found
        """
        pass

    @abstractmethod
    def get_all_filters(self) -> List[IFilter]:
        """
        Get all registered filters.

        Returns:
            List of all filter objects
        """
        pass

    @abstractmethod
    def apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all active filters to a DataFrame.

        Args:
            df: DataFrame to filter

        Returns:
            Filtered DataFrame
        """
        pass

    @abstractmethod
    def clear_all_filters(self) -> None:
        """Clear all filters."""
        pass

    @abstractmethod
    def save_filter_state(self, config: IConfigManager) -> None:
        """
        Save all filter states to configuration.

        Args:
            config: Configuration manager to save state to
        """
        pass

    @abstractmethod
    def load_filter_state(self, config: IConfigManager) -> None:
        """
        Load all filter states from configuration.

        Args:
            config: Configuration manager to load state from
        """
        pass

    @abstractmethod
    def get_active_filter_count(self) -> int:
        """
        Get the number of active filters.

        Returns:
            Number of active filters
        """
        pass
