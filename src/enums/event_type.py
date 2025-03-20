"""
event_type.py

Description: Re-exports the standardized EventType enum from interfaces/events.py
Usage:
    from src.enums.event_type import EventType
    event_type = EventType.ENTRIES_UPDATED
"""

from src.interfaces.events import EventType, EventHandler, EventData

# This module re-exports the standardized EventType from interfaces/events.py
# for backward compatibility with existing code.
#
# NOTE: New code should import directly from src.interfaces.events
