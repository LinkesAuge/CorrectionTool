#!/usr/bin/env python
"""
filter_test.py

Description: Test script to demonstrate the filtering system functionality
Usage:
    python -m scripts.filter_test
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import random

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.services.filters.text_filter import TextFilter
from src.services.filters.validation_list_filter import ValidationListFilter
from src.services.filters.date_filter import DateFilter
from src.services.filters.filter_manager import FilterManager


def create_sample_data(size=100):
    """Create a sample DataFrame with test data."""
    players = ["Player1", "Player2", "Player3", "Player4", "Player5"]
    chest_types = ["Golden", "Silver", "Bronze", "Diamond", "Platinum"]
    item_types = ["Weapon", "Shield", "Armor", "Potion", "Scroll", "Gem"]

    data = {
        "Player": [random.choice(players) for _ in range(size)],
        "ChestName": [f"Chest_{i}" for i in range(size)],
        "ChestType": [random.choice(chest_types) for _ in range(size)],
        "ItemName": [f"Item_{i}" for i in range(size)],
        "ItemType": [random.choice(item_types) for _ in range(size)],
        "Quantity": [random.randint(1, 100) for _ in range(size)],
        "Date": [
            (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
            for _ in range(size)
        ],
    }

    # Add some list-type data
    data["Tags"] = [
        [
            random.choice(["Rare", "Common", "Unique", "Legendary"])
            for _ in range(random.randint(0, 3))
        ]
        for _ in range(size)
    ]

    # Add some validation errors for demonstration
    data["ValidationErrors"] = [
        [
            random.choice(["NameError", "TypeMismatch", "InvalidQuantity", "DateError"])
            for _ in range(random.randint(0, 2))
        ]
        if random.random() < 0.3
        else []
        for _ in range(size)
    ]

    return pd.DataFrame(data)


def test_text_filter():
    """Test TextFilter functionality."""
    print("\n=== Testing TextFilter ===")
    df = create_sample_data()

    text_filter = TextFilter("text_filter", "Text Search")
    text_filter.set_target_columns(["Player", "ChestName", "ItemName"])

    # Test plain text search
    text_filter.set_search_text("Player1")
    filtered_df = text_filter.apply(df)
    print(f"Filtered by 'Player1': {len(filtered_df)} results")

    # Test regex search
    text_filter.set_search_text("Item_[0-9]$")
    text_filter.set_use_regex(True)
    filtered_df = text_filter.apply(df)
    print(f"Filtered by regex 'Item_[0-9]$': {len(filtered_df)} results")

    # Test clearing
    text_filter.clear()
    assert not text_filter.is_active()
    print("TextFilter cleared successfully")


def test_validation_list_filter():
    """Test ValidationListFilter functionality."""
    print("\n=== Testing ValidationListFilter ===")
    df = create_sample_data()

    # Create a validation list filter for ChestType
    chest_filter = ValidationListFilter("chest_filter", "Chest Type", "ChestType")

    # Test single selection
    chest_filter.set_selected_values(["Golden"])
    filtered_df = chest_filter.apply(df)
    print(f"Filtered by ChestType 'Golden': {len(filtered_df)} results")

    # Test multiple selection
    chest_filter.set_selected_values(["Golden", "Silver"])
    filtered_df = chest_filter.apply(df)
    print(f"Filtered by ChestType 'Golden' or 'Silver': {len(filtered_df)} results")

    # Test exclude selection
    chest_filter.set_selection_type(ValidationListFilter.SelectionType.EXCLUDE)
    filtered_df = chest_filter.apply(df)
    print(f"Excluded ChestType 'Golden' and 'Silver': {len(filtered_df)} results")

    # Test filtering on list column
    tags_filter = ValidationListFilter("tags_filter", "Tags", "Tags")
    tags_filter.set_selected_values(["Rare"])
    filtered_df = tags_filter.apply(df)
    print(f"Filtered by Tags containing 'Rare': {len(filtered_df)} results")

    # Test clearing
    chest_filter.clear()
    assert not chest_filter.is_active()
    print("ValidationListFilter cleared successfully")


def test_date_filter():
    """Test DateFilter functionality."""
    print("\n=== Testing DateFilter ===")
    df = create_sample_data()

    date_filter = DateFilter("date_filter", "Date Filter", "Date")

    # Test filtering by start date only
    start_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
    date_filter.set_date_range(start_date, None)
    filtered_df = date_filter.apply(df)
    print(f"Filtered by dates after {start_date}: {len(filtered_df)} results")

    # Test filtering by end date only
    end_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
    date_filter.set_date_range(None, end_date)
    filtered_df = date_filter.apply(df)
    print(f"Filtered by dates before {end_date}: {len(filtered_df)} results")

    # Test filtering by date range
    start_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    end_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    date_filter.set_date_range(start_date, end_date)
    filtered_df = date_filter.apply(df)
    print(f"Filtered by dates between {start_date} and {end_date}: {len(filtered_df)} results")

    # Test clearing
    date_filter.clear()
    assert not date_filter.is_active()
    print("DateFilter cleared successfully")


def test_filter_manager():
    """Test FilterManager functionality."""
    print("\n=== Testing FilterManager ===")
    df = create_sample_data()

    # Create filters
    text_filter = TextFilter("text_filter", "Text Search")
    text_filter.set_target_columns(["Player", "ChestName", "ItemName"])
    text_filter.set_search_text("Player1")

    chest_filter = ValidationListFilter("chest_filter", "Chest Type", "ChestType")
    chest_filter.set_selected_values(["Golden", "Silver"])

    date_filter = DateFilter("date_filter", "Date Filter", "Date")
    start_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    date_filter.set_date_range(start_date, None)

    # Create filter manager and register filters
    filter_manager = FilterManager()
    filter_manager.register_filter(text_filter)
    filter_manager.register_filter(chest_filter)
    filter_manager.register_filter(date_filter)

    # Apply all filters at once
    filtered_df = filter_manager.apply_filters(df)
    print(f"Applied all filters: {len(filtered_df)} results")

    # Test saving and loading filter state
    state = filter_manager.get_filter_state()
    print(f"Filter state: {state}")

    # Clear all filters
    filter_manager.clear_all_filters()
    filtered_df = filter_manager.apply_filters(df)
    print(f"All filters cleared: {len(filtered_df)} results")

    # Restore filter state
    filter_manager.load_filter_state(state)
    filtered_df = filter_manager.apply_filters(df)
    print(f"Filter state restored: {len(filtered_df)} results")


if __name__ == "__main__":
    test_text_filter()
    test_validation_list_filter()
    test_date_filter()
    test_filter_manager()
    print("\nAll filter tests completed successfully!")
