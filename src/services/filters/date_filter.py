"""
date_filter.py

Description: Filter implementation for date ranges
Usage:
    from src.services.filters.date_filter import DateFilter

    filter = DateFilter("date_filter", "Date Filter", "date_column")
    filter.set_date_range("2023-01-01", "2023-12-31")
    filtered_df = filter.apply(df)
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, date

import pandas as pd

from src.interfaces.i_config_manager import IConfigManager
from src.services.filters.base_filter import BaseFilter


class DateFilter(BaseFilter):
    """
    Filter implementation for date ranges.

    Filters a DataFrame based on a date range.

    Attributes:
        _column_name (str): Name of the column to filter
        _start_date (Optional[datetime]): Start date of the range (inclusive)
        _end_date (Optional[datetime]): End date of the range (inclusive)
        _date_format (str): Format string for parsing date strings
    """

    def __init__(
        self, filter_id: str, display_name: str, column_name: str, date_format: str = "%Y-%m-%d"
    ):
        """
        Initialize the date filter.

        Args:
            filter_id: Unique identifier for the filter
            display_name: User-friendly name for display in UI
            column_name: Name of the column to filter
            date_format: Format string for parsing date strings
        """
        super().__init__(filter_id, display_name)
        self._column_name = column_name
        self._start_date: Optional[datetime] = None
        self._end_date: Optional[datetime] = None
        self._date_format = date_format
        self._logger = logging.getLogger(f"filters.date.{filter_id}")

    def set_date_range(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> None:
        """
        Set the date range for filtering.

        Args:
            start_date: Start date string in the format specified by date_format
            end_date: End date string in the format specified by date_format
        """
        try:
            # Parse start date if provided
            if start_date:
                self._start_date = datetime.strptime(start_date, self._date_format)
            else:
                self._start_date = None

            # Parse end date if provided
            if end_date:
                self._end_date = datetime.strptime(end_date, self._date_format)
            else:
                self._end_date = None

            self._logger.debug(f"Date range set: {self._start_date} to {self._end_date}")
        except ValueError as e:
            self._logger.error(f"Error parsing date: {e}")
            # Reset dates on error
            self._start_date = None
            self._end_date = None

    def set_date_objects(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> None:
        """
        Set the date range using datetime objects.

        Args:
            start_date: Start date as datetime object
            end_date: End date as datetime object
        """
        if start_date and isinstance(start_date, date):
            if isinstance(start_date, datetime):
                self._start_date = start_date
            else:
                # Convert date to datetime
                self._start_date = datetime.combine(start_date, datetime.min.time())
        else:
            self._start_date = None

        if end_date and isinstance(end_date, date):
            if isinstance(end_date, datetime):
                self._end_date = end_date
            else:
                # Convert date to datetime with max time
                self._end_date = datetime.combine(end_date, datetime.max.time())
        else:
            self._end_date = None

        self._logger.debug(f"Date range set: {self._start_date} to {self._end_date}")

    def is_active(self) -> bool:
        """
        Check if filter is currently active.

        A date filter is active if either start_date or end_date is set.

        Returns:
            True if filter has active criteria, False otherwise
        """
        return self._enabled and (self._start_date is not None or self._end_date is not None)

    def get_start_date(self) -> Optional[datetime]:
        """
        Get the current start date.

        Returns:
            The start date as a datetime object, or None if not set
        """
        return self._start_date

    def get_end_date(self) -> Optional[datetime]:
        """
        Get the current end date.

        Returns:
            The end date as a datetime object, or None if not set
        """
        return self._end_date

    def format_date(self, dt: Optional[datetime]) -> Optional[str]:
        """
        Format a datetime object according to the filter's date format.

        Args:
            dt: The datetime object to format

        Returns:
            The formatted date string, or None if dt is None
        """
        if dt is None:
            return None
        return dt.strftime(self._date_format)

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

            # Ensure the column is datetime
            if not pd.api.types.is_datetime64_any_dtype(result_df[self._column_name]):
                # Try to convert to datetime
                self._logger.debug(f"Converting column {self._column_name} to datetime")
                try:
                    result_df[self._column_name] = pd.to_datetime(result_df[self._column_name])
                except Exception as e:
                    self._logger.error(f"Error converting to datetime: {e}")
                    return df

            # Apply start date filter if set
            if self._start_date is not None:
                result_df = result_df[result_df[self._column_name] >= self._start_date]

            # Apply end date filter if set
            if self._end_date is not None:
                result_df = result_df[result_df[self._column_name] <= self._end_date]

            self._logger.debug(f"Filter applied: {len(result_df)} of {len(df)} rows remaining")

            return result_df
        except Exception as e:
            self._logger.error(f"Error applying filter: {e}")
            return df

    def clear(self) -> None:
        """Clear the date range."""
        self._start_date = None
        self._end_date = None
        self._logger.debug("Date filter cleared")

    def save_state(self, config: IConfigManager) -> None:
        """
        Save filter state to configuration.

        Args:
            config: Configuration manager to save state to
        """
        super().save_state(config)
        section = f"Filter_{self._filter_id}"

        # Save start date if set
        if self._start_date:
            config.set_value(section, "start_date", self.format_date(self._start_date))
        else:
            config.remove_key(section, "start_date")

        # Save end date if set
        if self._end_date:
            config.set_value(section, "end_date", self.format_date(self._end_date))
        else:
            config.remove_key(section, "end_date")

    def load_state(self, config: IConfigManager) -> None:
        """
        Load filter state from configuration.

        Args:
            config: Configuration manager to load state from
        """
        super().load_state(config)
        section = f"Filter_{self._filter_id}"

        # Load start date if available
        start_date_str = config.get_value(section, "start_date", None)

        # Load end date if available
        end_date_str = config.get_value(section, "end_date", None)

        # Set the date range
        if start_date_str or end_date_str:
            try:
                self.set_date_range(start_date_str, end_date_str)
                self._logger.debug(f"Loaded date range: {start_date_str} to {end_date_str}")
            except Exception as e:
                self._logger.error(f"Error loading date range: {e}")
                self.clear()

    def get_state(self) -> Dict[str, Any]:
        """
        Get the current filter state as a dictionary.

        Returns:
            Dictionary with the filter state
        """
        state = super().get_state()

        if self._start_date:
            state["start_date"] = self.format_date(self._start_date)

        if self._end_date:
            state["end_date"] = self.format_date(self._end_date)

        return state
