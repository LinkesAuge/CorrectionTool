"""
i_data_store.py

Description: Interface for the data store
Usage:
    from src.interfaces.i_data_store import IDataStore
    data_store = service_factory.get_service(IDataStore)
    entries = data_store.get_entries()
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from pathlib import Path

# Import standardized event types
from src.interfaces.events import EventType, EventHandler, EventData


class IDataStore(ABC):
    """
    Interface for the data store.

    This interface defines methods for managing application data, including entries,
    validation lists, and correction rules.
    """

    @abstractmethod
    def get_entries(self) -> pd.DataFrame:
        """
        Get all entries as a DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing all entries
        """
        pass

    @abstractmethod
    def set_entries(self, entries_df: pd.DataFrame, source: str = "") -> bool:
        """
        Set the entries DataFrame.

        Args:
            entries_df: DataFrame containing entries
            source: Optional source identifier for the update

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_validation_list(self, list_type: str) -> pd.DataFrame:
        """
        Get a validation list by type.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')

        Returns:
            pd.DataFrame: DataFrame containing the validation list
        """
        pass

    @abstractmethod
    def set_validation_list(self, list_type: str, entries_df: pd.DataFrame) -> bool:
        """
        Set a validation list.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            entries_df: DataFrame containing the validation list

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def add_validation_entry(self, list_type: str, entry: str) -> bool:
        """
        Add an entry to a validation list.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            entry: Entry to add

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def remove_validation_entry(self, list_type: str, entry: str) -> bool:
        """
        Remove an entry from a validation list.

        Args:
            list_type: Type of validation list ('player', 'chest_type', 'source')
            entry: Entry to remove

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_correction_rules(self) -> pd.DataFrame:
        """
        Get all correction rules.

        Returns:
            pd.DataFrame: DataFrame containing all correction rules
        """
        pass

    @abstractmethod
    def set_correction_rules(self, rules_df: pd.DataFrame) -> bool:
        """
        Set the correction rules DataFrame.

        Args:
            rules_df: DataFrame containing correction rules

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def begin_transaction(self) -> bool:
        """
        Begin a transaction.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def commit_transaction(self) -> bool:
        """
        Commit the current transaction.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def rollback_transaction(self) -> bool:
        """
        Rollback the current transaction.

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to be called when the event occurs
        """
        pass

    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Callback function to remove
        """
        pass
