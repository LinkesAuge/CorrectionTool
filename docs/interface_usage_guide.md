# Interface Usage Guide

## Overview

This guide provides comprehensive documentation for developers working with the interface-based architecture in the Chest Tracker Correction Tool. It covers best practices, usage patterns, and examples for implementing and consuming interfaces.

## Core Principles

### Dependency Injection

Our application follows a strict dependency injection pattern:

1. **Constructor Injection**: Dependencies are provided through constructor parameters
2. **Interface-Based Dependencies**: Components depend on interfaces, not concrete implementations
3. **Service Factory**: The `ServiceFactory` handles creation and resolution of services

Example:
```python
# Good practice
class MyComponent:
    def __init__(self, data_store: IDataStore, config_manager: IConfigManager):
        self._data_store = data_store
        self._config_manager = config_manager
        
# Avoid
class BadComponent:
    def __init__(self):
        self._data_store = DataFrameStore.get_instance()  # Avoid singletons
        self._config_manager = ConfigManager()  # Avoid direct instantiation
```

### Interface Compliance

All implementations must fully comply with their interfaces:

1. **Complete Implementation**: All methods defined in the interface must be implemented
2. **Signature Compatibility**: Parameter and return types must match the interface definition
3. **Behavior Compliance**: Implementation behavior must satisfy the interface contract
4. **Clear Documentation**: Interface contracts should be documented with docstrings

## Core Interfaces

### IDataStore

The central data repository for the application.

```python
from src.interfaces.i_data_store import IDataStore

# Using IDataStore
def process_data(data_store: IDataStore):
    # Get validation list
    validation_list = data_store.get_validation_list("player")
    
    # Set a new validation list
    new_list = pd.DataFrame({"entry": ["Player1", "Player2"], "enabled": [True, True]})
    data_store.set_validation_list("player", new_list)
    
    # Add a single validation entry
    data_store.add_validation_entry("player", "Player3", enabled=True)
    
    # Check validation status
    is_valid = data_store.check_entry_valid("player", "Player1")
```

### IConfigManager

Handles application configuration storage and retrieval.

```python
from src.interfaces.i_config_manager import IConfigManager

# Using IConfigManager
def configure_component(config_manager: IConfigManager):
    # Get specific values with type conversion
    window_width = config_manager.get_int("UI", "window_width", fallback=800)
    use_dark_mode = config_manager.get_bool("UI", "dark_mode", fallback=True)
    
    # Set values
    config_manager.set_value("UI", "last_directory", "/path/to/files")
    
    # Get file paths
    data_dir = config_manager.get_path("data_directory")
    
    # Save configuration
    config_manager.save_config()
```

### IServiceFactory

Provides access to application services.

```python
from src.interfaces.i_service_factory import IServiceFactory

# Using IServiceFactory
def initialize_component(service_factory: IServiceFactory):
    # Get required services
    data_store = service_factory.get_service(IDataStore)
    validation_service = service_factory.get_service(IValidationService)
    correction_service = service_factory.get_service(ICorrectionService)
    
    # Check if a service is registered
    if service_factory.has_service(IExportService):
        export_service = service_factory.get_service(IExportService)
```

### IValidationService

Handles validation of entries against validation lists.

```python
from src.interfaces.i_validation_service import IValidationService

# Using IValidationService
def validate_entries(validation_service: IValidationService, entries: list):
    # Validate a batch of entries
    validation_results = validation_service.validate_entries(entries)
    
    # Get invalid entries
    invalid_entries = validation_service.get_invalid_entries()
    
    # Process results
    for entry, is_valid in validation_results.items():
        print(f"Entry {entry} is {'valid' if is_valid else 'invalid'}")
```

## Event System

Our application uses a standardized event system for communication between components:

### Event Types

All event types are defined in `src.interfaces.events.EventType` enum:

```python
from src.interfaces.events import EventType

# Event types
data_changed_event = EventType.DATA_CHANGED
validation_completed_event = EventType.VALIDATION_COMPLETED
correction_applied_event = EventType.CORRECTION_APPLIED
```

### Event Subscription

Components can subscribe to events using the event manager:

```python
from src.interfaces.events import EventType
from src.services.event_manager import EventManager

# Subscribing to events
def on_data_changed(event_data):
    print(f"Data changed: {event_data}")

EventManager.subscribe(EventType.DATA_CHANGED, on_data_changed)

# Unsubscribing
EventManager.unsubscribe(EventType.DATA_CHANGED, on_data_changed)
```

### Event Emission

Components can emit events to notify subscribers:

```python
from src.interfaces.events import EventType
from src.services.event_manager import EventManager

# Emitting events
event_data = {"source": "validation_service", "type": "player_list"}
EventManager.emit(EventType.DATA_CHANGED, event_data)
```

## Best Practices

### Interface Design

1. **Single Responsibility**: Each interface should define a single responsibility
2. **Minimal Surface Area**: Keep interfaces focused with only necessary methods
3. **Consistent Naming**: Use consistent naming patterns (I-prefix for interfaces)
4. **Clear Contracts**: Document method contracts with detailed docstrings

### Implementation

1. **Complete Implementation**: Implement all methods defined in the interface
2. **Type Consistency**: Maintain parameter and return type compatibility
3. **Error Handling**: Handle errors consistently as defined in the interface contract
4. **Behavioral Consistency**: Ensure behavior matches the interface contract

### Testing

1. **Interface Compliance Tests**: Create tests that verify interface compliance
2. **Mock Dependencies**: Use mock implementations for testing dependent interfaces
3. **Behavior Verification**: Test that implementations behave according to the contract
4. **Edge Cases**: Test edge cases defined in the interface contract

## Common Patterns

### Adapter Pattern

We use adapters to connect UI components with the core services:

```python
from src.interfaces.i_ui_adapter import ITableAdapter
from src.interfaces.i_data_store import IDataStore

class EntryTableAdapter(ITableAdapter):
    def __init__(self, data_store: IDataStore):
        self._data_store = data_store
        
    def get_data(self):
        return self._data_store.get_entries()
        
    def update_data(self, new_data):
        self._data_store.set_entries(new_data)
```

### Factory Pattern

The `ServiceFactory` implements the factory pattern for creating services:

```python
from src.interfaces.i_service_factory import IServiceFactory

# Using the factory
def use_factory(factory: IServiceFactory):
    # Get a service by interface
    data_store = factory.get_service(IDataStore)
    
    # Register a service implementation
    factory.register_service(IExportService, ExportService())
```

## Main Application Components

### MainWindowInterface

The primary UI component that integrates all other UI elements:

```python
from src.interfaces.i_service_factory import IServiceFactory
from src.ui.main_window_interface import MainWindowInterface

# Creating the main window
def create_application(service_factory: IServiceFactory):
    # Create the main window with injected services
    main_window = MainWindowInterface(service_factory)
    
    # Configure and show the main window
    main_window.resize(1280, 800)
    main_window.show()
    
    return main_window
```

### Using AppBootstrapper

The AppBootstrapper initializes all application services:

```python
from src.app_bootstrapper import AppBootstrapper
from src.ui.main_window_interface import MainWindowInterface

# Initialize the application
def initialize_application():
    # Create and initialize the bootstrapper
    bootstrapper = AppBootstrapper()
    bootstrapper.initialize()
    
    # Get the service factory
    service_factory = bootstrapper.service_factory
    
    # Create the main window
    main_window = MainWindowInterface(service_factory)
    main_window.show()
    
    return main_window
```

## Interface Evolution

Guidelines for evolving interfaces:

1. **Backward Compatibility**: Avoid breaking changes to existing methods
2. **Extension Methods**: Add new methods for new functionality
3. **Default Implementations**: Consider using abstract base classes with default implementations
4. **Versioning**: Create new interfaces for major changes rather than breaking existing ones

## Troubleshooting

Common issues and solutions:

1. **Missing Implementation**: Ensure all interface methods are implemented
2. **Type Mismatch**: Check parameter and return types match the interface
3. **Service Resolution**: Verify services are registered with the ServiceFactory
4. **Circular Dependencies**: Identify and break circular dependencies through interfaces

## Further Resources

- [Python Abstract Base Classes](https://docs.python.org/3/library/abc.html)
- [PEP 544 - Protocols](https://peps.python.org/pep-0544/)
- [Interface Architecture Document](INTERFACE_ARCHITECTURE.md)
- [Dependency Injection Guide](dependency_injection_guide.md) 