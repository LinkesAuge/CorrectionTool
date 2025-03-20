"""Test for DateFilter class."""

import pandas as pd
import pytest
from datetime import datetime, timedelta

from src.services.filters.date_filter import DateFilter


def test_date_filter_init():
    """Test DateFilter initialization."""
    filter_obj = DateFilter("test_filter", "Test Filter", "date_column")
    assert filter_obj.filter_id == "test_filter"
    assert filter_obj.display_name == "Test Filter"
    assert filter_obj.is_active() is False


def test_date_filter_set_date_range():
    """Test setting date range with strings."""
    filter_obj = DateFilter("test_filter", "Test Filter", "date_column")

    # Set only start date
    filter_obj.set_date_range("2023-01-01", None)
    assert filter_obj.is_active() is True
    assert filter_obj.get_start_date() == datetime(2023, 1, 1)
    assert filter_obj.get_end_date() is None

    # Set only end date
    filter_obj.set_date_range(None, "2023-12-31")
    assert filter_obj.is_active() is True
    assert filter_obj.get_start_date() is None
    assert filter_obj.get_end_date() == datetime(2023, 12, 31)

    # Set both dates
    filter_obj.set_date_range("2023-01-01", "2023-12-31")
    assert filter_obj.is_active() is True
    assert filter_obj.get_start_date() == datetime(2023, 1, 1)
    assert filter_obj.get_end_date() == datetime(2023, 12, 31)

    # Clear dates
    filter_obj.set_date_range(None, None)
    assert filter_obj.is_active() is False
    assert filter_obj.get_start_date() is None
    assert filter_obj.get_end_date() is None


def test_date_filter_set_date_objects():
    """Test setting date range with date objects."""
    filter_obj = DateFilter("test_filter", "Test Filter", "date_column")

    today = datetime.now().date()
    tomorrow = (datetime.now() + timedelta(days=1)).date()

    # Set both dates
    filter_obj.set_date_objects(today, tomorrow)
    assert filter_obj.is_active() is True
    assert filter_obj.get_start_date().date() == today
    assert filter_obj.get_end_date().date() == tomorrow


def test_date_filter_apply():
    """Test applying date filter to a DataFrame."""
    # Create test DataFrame with date column
    data = {
        "id": [1, 2, 3, 4, 5],
        "date_column": pd.to_datetime(
            ["2023-01-01", "2023-02-15", "2023-05-20", "2023-08-10", "2023-12-31"]
        ),
    }
    df = pd.DataFrame(data)

    # Create filter
    filter_obj = DateFilter("test_filter", "Test Filter", "date_column")

    # No filter active
    filtered_df = filter_obj.apply(df)
    assert len(filtered_df) == 5

    # Filter with start date only
    filter_obj.set_date_range("2023-05-01", None)
    filtered_df = filter_obj.apply(df)
    assert len(filtered_df) == 3
    assert list(filtered_df["id"]) == [3, 4, 5]

    # Filter with end date only
    filter_obj.set_date_range(None, "2023-03-01")
    filtered_df = filter_obj.apply(df)
    assert len(filtered_df) == 2
    assert list(filtered_df["id"]) == [1, 2]

    # Filter with both dates
    filter_obj.set_date_range("2023-02-01", "2023-08-31")
    filtered_df = filter_obj.apply(df)
    assert len(filtered_df) == 3
    assert list(filtered_df["id"]) == [2, 3, 4]

    # Filter with no matches
    filter_obj.set_date_range("2024-01-01", "2024-12-31")
    filtered_df = filter_obj.apply(df)
    assert len(filtered_df) == 0


def test_date_filter_format_date():
    """Test date formatting."""
    filter_obj = DateFilter("test_filter", "Test Filter", "date_column")

    # Format a date
    date_obj = datetime(2023, 1, 15)
    formatted = filter_obj.format_date(date_obj)
    assert formatted == "2023-01-15"

    # Format None
    assert filter_obj.format_date(None) is None

    # Custom date format
    filter_obj = DateFilter("test_filter", "Test Filter", "date_column", "%d/%m/%Y")
    formatted = filter_obj.format_date(date_obj)
    assert formatted == "15/01/2023"


def test_date_filter_clear():
    """Test clearing the filter."""
    filter_obj = DateFilter("test_filter", "Test Filter", "date_column")

    # Set dates
    filter_obj.set_date_range("2023-01-01", "2023-12-31")
    assert filter_obj.is_active() is True

    # Clear filter
    filter_obj.clear()
    assert filter_obj.is_active() is False
    assert filter_obj.get_start_date() is None
    assert filter_obj.get_end_date() is None
