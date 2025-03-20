"""
event_manager.py

Description: Centralized event handling system for the application
Usage:
    from src.services.event_manager import EventManager
    from src.interfaces.events import EventType

    # Subscribe to an event
    def on_entries_updated(event_data):
        print(f"Entries updated: {event_data}")

    EventManager.subscribe(EventType.ENTRIES_UPDATED, on_entries_updated)

    # Emit an event
    EventManager.emit(EventType.ENTRIES_UPDATED, {"source": "validation_service"})

    # Unsubscribe from an event
    EventManager.unsubscribe(EventType.ENTRIES_UPDATED, on_entries_updated)
"""

import logging
import threading
from typing import Dict, Set, Any, Callable

from src.interfaces.events import EventType, EventHandler, EventData


class EventManager:
    """
    Centralized event handling system for the application.

    This class provides a single point for subscribing to events and emitting events,
    ensuring consistent event handling throughout the application.

    Attributes:
        _event_handlers: Dictionary mapping event types to sets of handler functions
        _logger: Logger instance for event management

    Implementation Notes:
        - Uses a class-level dictionary to store event handlers
        - Provides thread-safe event handling
        - Handles exceptions in event handlers to prevent event propagation failures
    """

    # Class-level event handlers dictionary
    _event_handlers: Dict[EventType, Set[EventHandler]] = {
        event_type: set() for event_type in EventType
    }

    # Thread safety lock
    _lock = threading.RLock()

    # Logger
    _logger = logging.getLogger(__name__)

    @classmethod
    def subscribe(cls, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe to an event type with the given handler function.

        Args:
            event_type: The type of event to subscribe to
            handler: The function to call when the event is emitted

        Raises:
            ValueError: If the event_type is not a valid EventType or handler is not callable
        """
        if not isinstance(event_type, EventType):
            raise ValueError(f"Event type must be an EventType enum value, got {type(event_type)}")

        if not callable(handler):
            raise ValueError(f"Event handler must be callable, got {type(handler)}")

        with cls._lock:
            cls._event_handlers[event_type].add(handler)
            cls._logger.debug(f"Subscribed handler {handler.__name__} to event {event_type.name}")

    @classmethod
    def unsubscribe(cls, event_type: EventType, handler: EventHandler) -> bool:
        """
        Unsubscribe a handler from an event type.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler function to remove

        Returns:
            bool: True if the handler was removed, False if it wasn't subscribed

        Raises:
            ValueError: If the event_type is not a valid EventType
        """
        if not isinstance(event_type, EventType):
            raise ValueError(f"Event type must be an EventType enum value, got {type(event_type)}")

        with cls._lock:
            if handler in cls._event_handlers[event_type]:
                cls._event_handlers[event_type].remove(handler)
                cls._logger.debug(
                    f"Unsubscribed handler {handler.__name__} from event {event_type.name}"
                )
                return True
            return False

    @classmethod
    def emit(cls, event_type: EventType, event_data: EventData = None) -> int:
        """
        Emit an event to all subscribed handlers.

        Args:
            event_type: The type of event to emit
            event_data: Optional data to pass to the event handlers

        Returns:
            int: The number of handlers that were notified

        Raises:
            ValueError: If the event_type is not a valid EventType
        """
        if not isinstance(event_type, EventType):
            raise ValueError(f"Event type must be an EventType enum value, got {type(event_type)}")

        if event_data is None:
            event_data = {}

        # Add event type to the data for reference
        event_data["event_type"] = event_type

        # Make a copy of the handlers set to avoid issues if handlers are added/removed during emission
        with cls._lock:
            handlers = cls._event_handlers[event_type].copy()

        handler_count = len(handlers)
        if handler_count > 0:
            cls._logger.debug(f"Emitting event {event_type.name} to {handler_count} handlers")

        # Call each handler with the event data
        for handler in handlers:
            try:
                handler(event_data)
            except Exception as e:
                cls._logger.error(
                    f"Error in event handler {handler.__name__} for event {event_type.name}: {e}"
                )
                # Don't re-raise the exception to avoid breaking event propagation

        return handler_count

    @classmethod
    def get_subscriber_count(cls, event_type: EventType) -> int:
        """
        Get the number of subscribers for an event type.

        Args:
            event_type: The event type to check

        Returns:
            int: The number of subscribers

        Raises:
            ValueError: If the event_type is not a valid EventType
        """
        if not isinstance(event_type, EventType):
            raise ValueError(f"Event type must be an EventType enum value, got {type(event_type)}")

        with cls._lock:
            return len(cls._event_handlers[event_type])

    @classmethod
    def clear_subscribers(cls, event_type: EventType = None) -> int:
        """
        Clear all subscribers for an event type or all event types.

        Args:
            event_type: Optional event type to clear. If None, clears all subscribers.

        Returns:
            int: The number of subscribers that were cleared

        Raises:
            ValueError: If the event_type is not a valid EventType
        """
        with cls._lock:
            if event_type is None:
                # Clear all subscribers
                count = sum(len(handlers) for handlers in cls._event_handlers.values())
                cls._event_handlers = {event_type: set() for event_type in EventType}
                cls._logger.debug(f"Cleared all subscribers ({count} total)")
                return count

            if not isinstance(event_type, EventType):
                raise ValueError(
                    f"Event type must be an EventType enum value, got {type(event_type)}"
                )

            count = len(cls._event_handlers[event_type])
            cls._event_handlers[event_type] = set()
            cls._logger.debug(f"Cleared {count} subscribers for event {event_type.name}")
            return count
