"""
event_type.py

Description: Enum defining event types for the application
Usage:
    from src.enums.event_type import EventType
    event_type = EventType.ENTRIES_UPDATED
"""

from enum import Enum, auto


class EventType(Enum):
    """Enum defining types of events that can be emitted by the application."""

    # Data events
    ENTRIES_UPDATED = auto()
    VALIDATION_LIST_UPDATED = auto()
    CORRECTION_RULES_UPDATED = auto()

    # Process events
    VALIDATION_STARTED = auto()
    VALIDATION_COMPLETED = auto()
    CORRECTION_STARTED = auto()
    CORRECTION_APPLIED = auto()
    CORRECTIONS_RESET = auto()
    IMPORT_STARTED = auto()
    IMPORT_COMPLETED = auto()
    EXPORT_STARTED = auto()
    EXPORT_COMPLETED = auto()

    # Status events
    ERROR_OCCURRED = auto()
    WARNING_ISSUED = auto()
    INFO_MESSAGE = auto()

    # UI events
    UI_REFRESH_NEEDED = auto()
    SELECTION_CHANGED = auto()
    FILTER_CHANGED = auto()
