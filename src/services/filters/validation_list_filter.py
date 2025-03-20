"""
validation_list_filter.py

Description: Filter implementation for validation lists
Usage:
    from src.services.filters.validation_list_filter import ValidationListFilter

    filter = ValidationListFilter("player", "Player")
    filter.set_selected_values(["Player1", "Player2"])
    filtered_df = filter.apply(df)
"""

import logging
from typing import List, Set, Dict, Any, Optional

import pandas as pd

from src.interfaces.i_config_manager import IConfigManager
from src.services.filters.base_filter import BaseFilter


class ValidationListFilter(BaseFilter):
    """
    Filter implementation for validation lists.

    Filters a DataFrame based on a validation list with multi-select support.

    Attributes:
        _column_name (str): Name of the column to filter
        _selected_values (Set[str]): Set of selected values
        _selection_type (str): Type of selection ('include' or 'exclude')
        _case_sensitive (bool): Whether filtering is case-sensitive
    """

    def __init__(
        self, filter_id: str, display_name: str, column_name: str, case_sensitive: bool = False
    ):
        """
        Initialize the validation list filter.

        Args:
            filter_id: Unique identifier for the filter
            display_name: User-friendly name for display in UI
            column_name: Name of the column to filter
            case_sensitive: Whether filtering is case-sensitive
        """
        super().__init__(filter_id, display_name)
        self._column_name = column_name
        self._selected_values: Set[str] = set()
        self._selection_type = "include"  # 'include' or 'exclude'
        self._case_sensitive = case_sensitive
        self._logger = logging.getLogger(f"filters.validation_list.{filter_id}")

    @property
    def column_name(self) -> str:
        """
        Get the column name this filter operates on.

        Returns:
            Column name
        """
        return self._column_name

    @property
    def selected_values(self) -> List[str]:
        """
        Get the list of selected values.

        Returns:
            List of selected values
        """
        return list(self._selected_values)

    @property
    def selection_type(self) -> str:
        """
        Get the selection type.

        Returns:
            'include' or 'exclude'
        """
        return self._selection_type

    @selection_type.setter
    def selection_type(self, value: str) -> None:
        """
        Set the selection type.

        Args:
            value: 'include' or 'exclude'

        Raises:
            ValueError: If value is not 'include' or 'exclude'
        """
        if value not in ("include", "exclude"):
            raise ValueError("Selection type must be 'include' or 'exclude'")
        self._selection_type = value

    @property
    def case_sensitive(self) -> bool:
        """
        Check if filtering is case-sensitive.

        Returns:
            True if case-sensitive, False otherwise
        """
        return self._case_sensitive

    @case_sensitive.setter
    def case_sensitive(self, value: bool) -> None:
        """
        Set whether filtering is case-sensitive.

        Args:
            value: True for case-sensitive, False for case-insensitive
        """
        self._case_sensitive = value

    def set_selected_values(self, values: List[str]) -> None:
        """
        Set the selected values.

        Args:
            values: List of values to select
        """
        self._selected_values = set(values)
        self._logger.debug(f"Selected values set to: {self._selected_values}")

    def add_selected_value(self, value: str) -> None:
        """
        Add a value to the selected values.

        Args:
            value: Value to add
        """
        self._selected_values.add(value)
        self._logger.debug(f"Added value: {value}")

    def remove_selected_value(self, value: str) -> None:
        """
        Remove a value from the selected values.

        Args:
            value: Value to remove
        """
        if value in self._selected_values:
            self._selected_values.remove(value)
            self._logger.debug(f"Removed value: {value}")

    def is_active(self) -> bool:
        """
        Check if filter is currently active.

        Returns:
            True if there are selected values and the filter is enabled,
            False otherwise
        """
        return self._enabled and len(self._selected_values) > 0

    def clear(self) -> None:
        """Clear the filter settings."""
        self._selected_values.clear()
        self._logger.debug("Filter cleared")

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply filter to a DataFrame and return filtered result.

        Args:
            df: DataFrame to filter

        Returns:
            Filtered DataFrame
        """
        if not self.is_active() or self._column_name not in df.columns:
            return df

        try:
            # Create a copy of the DataFrame
            result_df = df.copy()

            # Handle case sensitivity
            if not self._case_sensitive:
                # Convert selected values to lowercase
                lowercase_selected = {value.lower() for value in self._selected_values}

                # Create a mask based on case-insensitive matching
                if self._selection_type == "include":
                    mask = result_df[self._column_name].str.lower().isin(lowercase_selected)
                else:  # exclude
                    mask = ~result_df[self._column_name].str.lower().isin(lowercase_selected)
            else:
                # Case-sensitive matching
                if self._selection_type == "include":
                    mask = result_df[self._column_name].isin(self._selected_values)
                else:  # exclude
                    mask = ~result_df[self._column_name].isin(self._selected_values)

            # Apply the mask
            result_df = result_df[mask]

            self._logger.debug(f"Filter applied: {len(result_df)} of {len(df)} rows remaining")

            return result_df
        except Exception as e:
            self._logger.error(f"Error applying filter: {e}")
            return df

    def save_state(self, config: IConfigManager) -> None:
        """
        Save filter state to configuration.

        Args:
            config: Configuration manager to save state to
        """
        # Call base implementation to save enabled state
        super().save_state(config)

        # Save filter-specific state
        section = f"Filter_{self._filter_id}"
        config.set_value(section, "selection_type", self._selection_type)
        config.set_value(section, "case_sensitive", str(self._case_sensitive))
        config.set_value(
            section,
            "selected_values",
            ",".join(self._selected_values) if self._selected_values else "",
        )

    def load_state(self, config: IConfigManager) -> None:
        """
        Load filter state from configuration.

        Args:
            config: Configuration manager to load state from
        """
        # Call base implementation to load enabled state
        super().load_state(config)

        # Load filter-specific state
        section = f"Filter_{self._filter_id}"
        self._selection_type = config.get_value(section, "selection_type", "include")

        case_sensitive_str = config.get_value(section, "case_sensitive", "False")
        self._case_sensitive = case_sensitive_str.lower() == "true"

        selected_values_str = config.get_value(section, "selected_values", "")
        self._selected_values = set(selected_values_str.split(",") if selected_values_str else [])
