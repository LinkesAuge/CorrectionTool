"""
demo.py

Description: Demonstration script for the new data management system
Usage:
    python -m src.demo
"""

import logging
import pandas as pd
from pathlib import Path
import sys
import os

# Add the parent directory to the path so we can import the src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Import our services
from src.services.service_factory import ServiceFactory
from src.services.dataframe_store import DataFrameStore, EventType


def on_entries_updated(event_data):
    """Handler for entries updated event."""
    print(f"Entries updated event received: {event_data}")

    # Get the updated entries
    store = DataFrameStore.get_instance()
    entries = store.get_entries()

    print(f"Total entries: {len(entries)}")
    print(f"Sample entry:\n{entries.iloc[0] if not entries.empty else 'No entries'}")


def on_correction_applied(event_data):
    """Handler for correction applied event."""
    print(f"Correction applied event received: {event_data}")

    # Get statistics on corrections
    store = DataFrameStore.get_instance()
    stats = store.get_statistics()

    print(f"Correction statistics: {stats.get('corrections', {})}")


def demo_data_store():
    """Demonstrate the DataFrameStore functionality."""
    print("\n=== DataFrameStore Demo ===\n")

    # Get the data store instance
    store = DataFrameStore.get_instance()

    # Subscribe to events
    store.subscribe(EventType.ENTRIES_UPDATED, on_entries_updated)
    store.subscribe(EventType.CORRECTION_APPLIED, on_correction_applied)

    # Create some test entries
    entries_data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "chest_type": ["Gold", "Silver", "Bronze"],
        "player": ["Player1", "Player2", "Player3"],
        "source": ["Source1", "Source2", "Source3"],
        "status": ["Pending", "Pending", "Pending"],
        "validation_errors": [[], [], []],
        "original_values": [{}, {}, {}],
    }

    entries_df = pd.DataFrame(entries_data)

    # Start a transaction
    store.begin_transaction()

    # Set the entries
    store.set_entries(entries_df)

    # Commit the transaction
    store.commit_transaction()

    # Create validation lists
    chest_types_data = {"value": ["Gold", "Silver", "Bronze", "Platinum"]}
    player_names_data = {"value": ["Player1", "Player2", "Player3", "Player4"]}
    sources_data = {"value": ["Source1", "Source2", "Source3", "Source4"]}

    # Create DataFrames with the correct column name
    chest_types_df = pd.DataFrame(chest_types_data)
    player_names_df = pd.DataFrame(player_names_data)
    sources_df = pd.DataFrame(sources_data)

    # Set validation lists with the correct type names
    store.set_validation_list("players", player_names_df)
    store.set_validation_list("chest_types", chest_types_df)
    store.set_validation_list("sources", sources_df)

    # Create correction rules
    store.add_correction_rule(
        {
            "from_text": "Silver",
            "to_text": "Silver Chest",
            "category": "chest_type",
            "enabled": True,
        }
    )

    store.add_correction_rule(
        {"from_text": "Gold", "to_text": "Gold Chest", "category": "chest_type", "enabled": True}
    )

    # Display validation lists
    print("Chest Types:", store.get_validation_list("chest_types")["value"].tolist())
    print("Player Names:", store.get_validation_list("players")["value"].tolist())
    print("Sources:", store.get_validation_list("sources")["value"].tolist())

    # Display correction rules
    rules_df = store.get_correction_rules()
    print("\nCorrection Rules:")
    for rule_id, rule in rules_df.iterrows():
        print(f"  {rule_id}: {rule['from_text']} -> {rule['to_text']} ({rule['category']})")

    print("\nEntries before correction:")
    print(store.get_entries()[["chest_type", "player", "source", "status"]])

    return store


def demo_services():
    """Demonstrate the services functionality."""
    print("\n=== Services Demo ===\n")

    # Get the service factory
    factory = ServiceFactory.get_instance()

    # Initialize all services
    factory.initialize_all_services()

    # Get services
    file_service = factory.get_file_service()
    correction_service = factory.get_correction_service()
    validation_service = factory.get_validation_service()

    # Apply corrections
    print("\nApplying corrections...")
    applied_count = correction_service.apply_corrections()
    print(f"Applied {applied_count} corrections")

    # Get the data store and display entries after correction
    store = factory.get_dataframe_store()
    print("\nEntries after correction:")
    print(store.get_entries()[["chest_type", "player", "source", "status", "original_values"]])

    # Validate entries
    print("\nValidating entries...")
    validation_result = validation_service.validate_entries()
    print(f"Validation result: {validation_result}")

    # Display entries after validation
    print("\nEntries after validation:")
    print(store.get_entries()[["chest_type", "player", "source", "status", "validation_errors"]])

    # Get statistics
    stats = store.get_statistics()
    print("\nStatistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    return factory


def main():
    """Main demo function."""
    print("=== Data Management System Demo ===")

    # Demo DataFrameStore
    store = demo_data_store()

    # Demo services
    factory = demo_services()

    print("\nDemo completed successfully!")


if __name__ == "__main__":
    main()
