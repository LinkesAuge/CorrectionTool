"""
events.py

Description: Event types and related classes for the application events system
Usage:
    from src.interfaces.events import EventType
    if event_type == EventType.ENTRIES_UPDATED:
        # Handle entries updated event
"""

from enum import Enum, auto
from typing import Dict, Any, Callable, List, Optional, Union, Set


class EventType(Enum):
    """
    Event types used throughout the application.

    These event types are used by the event system to notify subscribers
    about changes to the application state.
    """

    # Data events
    ENTRIES_UPDATED = auto()
    CORRECTION_RULES_UPDATED = auto()
    VALIDATION_LISTS_UPDATED = auto()

    # Operation events
    IMPORT_COMPLETED = auto()
    EXPORT_COMPLETED = auto()
    CORRECTION_APPLIED = auto()
    VALIDATION_COMPLETED = auto()

    # Error events
    ERROR_OCCURRED = auto()


# Type definitions
EventHandler = Callable[[Dict[str, Any]], None]
EventData = Dict[str, Any]
