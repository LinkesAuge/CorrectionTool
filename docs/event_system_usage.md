# Event System Usage Guide

The event system in the CorrectionTool application provides a way for different components to communicate with each other without direct coupling. This document explains how to use the event system in your code.

## Overview

The event system consists of:

1. **EventType Enum**: Defines the types of events that can be emitted
2. **EventManager Class**: Handles subscription, unsubscription, and emitting of events
3. **EventHandler Type**: Function type that handles events (Callable[[Dict[str, Any]], None])
4. **EventData Type**: Dictionary containing event data (Dict[str, Any])

## Basic Usage

### Importing Required Components

```python
from src.interfaces.events import EventType, EventHandler, EventData
from src.services.event_manager import EventManager
```

### Subscribing to Events

To receive notifications when a specific event occurs:

```python
def on_entries_updated(event_data):
    # Handle the event
    print(f"Entries updated: {event_data}")

# Subscribe to the event
EventManager.subscribe(EventType.ENTRIES_UPDATED, on_entries_updated)
```

### Emitting Events

To send notifications to all subscribers of a specific event:

```python
# Emit an event with data
EventManager.emit(
    EventType.ENTRIES_UPDATED,
    {
        "source": "DataImporter",
        "count": 10,
        "timestamp": datetime.now()
    }
)
```

### Unsubscribing from Events

To stop receiving notifications for an event:

```python
# Unsubscribe from the event
EventManager.unsubscribe(EventType.ENTRIES_UPDATED, on_entries_updated)
```

## Advanced Usage

### Class-Based Event Handling

When working with classes, you can use instance methods as event handlers:

```python
class DataProcessor:
    def __init__(self):
        # Subscribe to events
        EventManager.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
        
    def _on_entries_updated(self, event_data):
        # Handle the event
        print(f"Processing updated entries: {event_data}")
        
    def cleanup(self):
        # Important: Unsubscribe when the object is no longer needed
        EventManager.unsubscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
```

### Managing Event Loops and Recursion

Be careful when emitting events in response to other events, as this can lead to infinite recursion:

```python
def bad_handler(event_data):
    # This will cause infinite recursion!
    EventManager.emit(EventType.ENTRIES_UPDATED, {"recursive": True})

# Don't do this without a stopping condition
EventManager.subscribe(EventType.ENTRIES_UPDATED, bad_handler)
```

A better approach:

```python
class SafeHandler:
    def __init__(self):
        self._is_processing = False
        EventManager.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
        
    def _on_entries_updated(self, event_data):
        # Prevent recursive processing
        if self._is_processing:
            return
            
        self._is_processing = True
        try:
            # Process the event safely
            # You can emit other events here
            EventManager.emit(EventType.STATUS_CHANGED, {"status": "Processing"})
        finally:
            # Always clear the flag
            self._is_processing = False
```

### Thread Safety

The EventManager is thread-safe, but ensure your event handlers are also thread-safe if they might be called from different threads.

## Event Flow Patterns

### Observer Pattern

The event system implements the Observer pattern, allowing components to observe changes without being directly coupled:

```python
# Component that makes changes (Observable)
class DataStore:
    def set_entries(self, entries):
        # Update internal state
        self._entries = entries
        
        # Notify observers
        EventManager.emit(EventType.ENTRIES_UPDATED, {"entries": entries})

# Component that observes changes (Observer)
class UIComponent:
    def __init__(self):
        EventManager.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
        
    def _on_entries_updated(self, event_data):
        # Update UI based on the changes
        self._refresh_display(event_data["entries"])
```

### Chain of Responsibility

Events can trigger a chain of operations:

```python
# Component 1: Validates data
class Validator:
    def __init__(self):
        EventManager.subscribe(EventType.ENTRIES_UPDATED, self._on_entries_updated)
        
    def _on_entries_updated(self, event_data):
        # Validate entries
        validation_result = self._validate(event_data["entries"])
        
        # Emit validation result
        EventManager.emit(
            EventType.VALIDATION_COMPLETED, 
            {"result": validation_result}
        )

# Component 2: Corrects data based on validation
class Corrector:
    def __init__(self):
        EventManager.subscribe(EventType.VALIDATION_COMPLETED, self._on_validation_completed)
        
    def _on_validation_completed(self, event_data):
        # Apply corrections based on validation results
        corrections = self._apply_corrections(event_data["result"])
        
        # Emit correction result
        EventManager.emit(
            EventType.CORRECTION_APPLIED,
            {"corrections": corrections}
        )

# Component 3: Updates UI based on corrections
class UIUpdater:
    def __init__(self):
        EventManager.subscribe(EventType.CORRECTION_APPLIED, self._on_correction_applied)
        
    def _on_correction_applied(self, event_data):
        # Update UI with corrections
        self._update_ui(event_data["corrections"])
```

## Best Practices

1. **Use Specific Event Types**: Choose the most specific event type for your needs
2. **Include Essential Data**: Include all necessary data in the event, but avoid large objects
3. **Handle Exceptions**: Always handle exceptions in event handlers to prevent disruption
4. **Unsubscribe When Done**: Always unsubscribe event handlers when objects are destroyed
5. **Avoid Tight Coupling**: Don't rely on specific event ordering; each handler should be independent
6. **Document Events**: Document which events your component emits and subscribes to
7. **Keep Handlers Focused**: Each handler should do one specific job
8. **Be Mindful of Performance**: Keep event handlers efficient, as they may be called frequently

## Available Event Types

The following event types are defined in `src.interfaces.events.EventType`:

### Data Events
- `ENTRIES_UPDATED`: Entries data has changed
- `CORRECTION_RULES_UPDATED`: Correction rules have changed
- `VALIDATION_LISTS_UPDATED`: Validation lists have changed
- `VALIDATION_LIST_UPDATED`: A specific validation list has changed

### Process Events
- `VALIDATION_STARTED`: Validation process has started
- `VALIDATION_COMPLETED`: Validation process has completed
- `CORRECTION_STARTED`: Correction process has started
- `CORRECTION_APPLIED`: Corrections have been applied
- `CORRECTIONS_RESET`: Corrections have been reset
- `IMPORT_STARTED`: Import process has started
- `IMPORT_COMPLETED`: Import process has completed
- `EXPORT_STARTED`: Export process has started
- `EXPORT_COMPLETED`: Export process has completed

### Status Events
- `ERROR_OCCURRED`: An error has occurred
- `WARNING_ISSUED`: A warning has been issued
- `INFO_MESSAGE`: An informational message

### UI Events
- `UI_REFRESH_NEEDED`: UI needs to be refreshed
- `SELECTION_CHANGED`: Selection has changed
- `FILTER_CHANGED`: Filter has changed 