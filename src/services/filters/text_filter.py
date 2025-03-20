"""
text_filter.py

Description: Filter implementation for text search
Usage:
    from src.services.filters.text_filter import TextFilter

    filter = TextFilter("search", "Text Search")
    filter.set_search_text("keyword")
    filtered_df = filter.apply(df)
"""

import logging
import re
from typing import List, Set, Dict, Any, Optional

import pandas as pd

from src.interfaces.i_config_manager import IConfigManager
from src.services.filters.base_filter import BaseFilter


class TextFilter(BaseFilter):
    """
    Filter implementation for text search.

    Filters a DataFrame based on text search criteria.

    Attributes:
        _search_text (str): Text to search for
        _target_columns (List[str]): Columns to search in
        _case_sensitive (bool): Whether search is case-sensitive
        _whole_word (bool): Whether to match whole words only
        _regex_enabled (bool): Whether to use regex for matching
    """

    def __init__(
        self,
        filter_id: str,
        display_name: str,
        target_columns: Optional[List[str]] = None,
        case_sensitive: bool = False,
        whole_word: bool = False,
        regex_enabled: bool = False,
    ):
        """
        Initialize the text filter.

        Args:
            filter_id: Unique identifier for the filter
            display_name: User-friendly name for display in UI
            target_columns: Columns to search in (None for all columns)
            case_sensitive: Whether search is case-sensitive
            whole_word: Whether to match whole words only
            regex_enabled: Whether to use regex for matching
        """
        super().__init__(filter_id, display_name)
        self._search_text = ""
        self._target_columns = target_columns or []  # Empty list means all columns
        self._case_sensitive = case_sensitive
        self._whole_word = whole_word
        self._regex_enabled = regex_enabled
        self._logger = logging.getLogger(f"filters.text.{filter_id}")

    @property
    def search_text(self) -> str:
        """
        Get the search text.

        Returns:
            Search text
        """
        return self._search_text

    @search_text.setter
    def search_text(self, value: str) -> None:
        """
        Set the search text.

        Args:
            value: Text to search for
        """
        self._search_text = value
        self._logger.debug(f"Search text set to: {value}")

    @property
    def target_columns(self) -> List[str]:
        """
        Get the target columns.

        Returns:
            List of target columns (empty list for all columns)
        """
        return self._target_columns

    @target_columns.setter
    def target_columns(self, value: List[str]) -> None:
        """
        Set the target columns.

        Args:
            value: List of columns to search in (empty list for all columns)
        """
        self._target_columns = value
        self._logger.debug(f"Target columns set to: {value}")

    @property
    def case_sensitive(self) -> bool:
        """
        Check if search is case-sensitive.

        Returns:
            True if case-sensitive, False otherwise
        """
        return self._case_sensitive

    @case_sensitive.setter
    def case_sensitive(self, value: bool) -> None:
        """
        Set whether search is case-sensitive.

        Args:
            value: True for case-sensitive, False for case-insensitive
        """
        self._case_sensitive = value
        self._logger.debug(f"Case sensitive set to: {value}")

    @property
    def whole_word(self) -> bool:
        """
        Check if search matches whole words only.

        Returns:
            True if whole word matching, False otherwise
        """
        return self._whole_word

    @whole_word.setter
    def whole_word(self, value: bool) -> None:
        """
        Set whether search matches whole words only.

        Args:
            value: True for whole word matching, False otherwise
        """
        self._whole_word = value
        self._logger.debug(f"Whole word set to: {value}")

    @property
    def regex_enabled(self) -> bool:
        """
        Check if regex is enabled for search.

        Returns:
            True if regex enabled, False otherwise
        """
        return self._regex_enabled

    @regex_enabled.setter
    def regex_enabled(self, value: bool) -> None:
        """
        Set whether regex is enabled for search.

        Args:
            value: True to enable regex, False to disable
        """
        self._regex_enabled = value
        self._logger.debug(f"Regex enabled set to: {value}")

    def set_search_text(self, text: str) -> None:
        """
        Set the search text.

        Args:
            text: Text to search for
        """
        self._search_text = text
        self._logger.debug(f"Search text set to: {text}")

    def is_active(self) -> bool:
        """
        Check if filter is currently active.

        Returns:
            True if there is search text and the filter is enabled,
            False otherwise
        """
        return self._enabled and bool(self._search_text)

    def clear(self) -> None:
        """Clear the filter settings."""
        self._search_text = ""
        self._logger.debug("Filter cleared")

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply filter to a DataFrame and return filtered result.

        Args:
            df: DataFrame to filter

        Returns:
            Filtered DataFrame
        """
        if not self.is_active():
            return df

        try:
            # Create a copy of the DataFrame
            result_df = df.copy()

            # Determine which columns to search in
            columns_to_search = self._target_columns if self._target_columns else result_df.columns

            # Ensure all specified columns exist in the DataFrame
            columns_to_search = [col for col in columns_to_search if col in result_df.columns]

            if not columns_to_search:
                self._logger.warning("No valid columns to search in")
                return df

            # Prepare search pattern
            search_text = self._search_text

            if self._regex_enabled:
                try:
                    if not self._case_sensitive:
                        pattern = re.compile(search_text, re.IGNORECASE)
                    else:
                        pattern = re.compile(search_text)
                except re.error as e:
                    self._logger.error(f"Invalid regex pattern: {e}")
                    return df

                # Create a mask for regex matching
                mask = pd.Series(False, index=result_df.index)
                for column in columns_to_search:
                    if pd.api.types.is_string_dtype(result_df[column]):
                        column_mask = result_df[column].str.contains(pattern, regex=True, na=False)
                        mask = mask | column_mask

            else:  # Plain text search
                if self._whole_word:
                    # For whole word search, need to use regex with word boundaries
                    word_pattern = r"\b" + re.escape(search_text) + r"\b"
                    if not self._case_sensitive:
                        pattern = re.compile(word_pattern, re.IGNORECASE)
                    else:
                        pattern = re.compile(word_pattern)

                    # Create a mask for whole word matching
                    mask = pd.Series(False, index=result_df.index)
                    for column in columns_to_search:
                        if pd.api.types.is_string_dtype(result_df[column]):
                            column_mask = result_df[column].str.contains(
                                pattern, regex=True, na=False
                            )
                            mask = mask | column_mask

                else:  # Simple substring match
                    # Create a mask for substring matching
                    mask = pd.Series(False, index=result_df.index)
                    for column in columns_to_search:
                        if pd.api.types.is_string_dtype(result_df[column]):
                            if not self._case_sensitive:
                                column_mask = (
                                    result_df[column]
                                    .str.lower()
                                    .str.contains(search_text.lower(), na=False)
                                )
                            else:
                                column_mask = result_df[column].str.contains(search_text, na=False)
                            mask = mask | column_mask

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
        config.set_value(section, "search_text", self._search_text)
        config.set_value(section, "case_sensitive", str(self._case_sensitive))
        config.set_value(section, "whole_word", str(self._whole_word))
        config.set_value(section, "regex_enabled", str(self._regex_enabled))
        config.set_value(
            section,
            "target_columns",
            ",".join(self._target_columns) if self._target_columns else "all",
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
        self._search_text = config.get_value(section, "search_text", "")

        case_sensitive_str = config.get_value(section, "case_sensitive", "False")
        self._case_sensitive = case_sensitive_str.lower() == "true"

        whole_word_str = config.get_value(section, "whole_word", "False")
        self._whole_word = whole_word_str.lower() == "true"

        regex_enabled_str = config.get_value(section, "regex_enabled", "False")
        self._regex_enabled = regex_enabled_str.lower() == "true"

        target_columns_str = config.get_value(section, "target_columns", "all")
        self._target_columns = target_columns_str.split(",") if target_columns_str != "all" else []
