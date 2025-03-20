# Interface Documentation

This document provides an overview of the interface-based architecture used in the Chest Tracker Correction Tool. The application is built around a set of core interfaces that define the contract between different components, promoting loose coupling and enabling easier testing and maintenance.

## Core Interfaces

The application is structured around the following core interfaces:

1. **IDataStore**: Responsible for data management and persistence
2. **IFileService**: Handles file operations (import/export)
3. **ICorrectionService**: Manages the correction rules and their application
4. **IValidationService**: Manages validation lists and entry validation
5. **IConfigManager**: Handles application configuration
6. **IServiceFactory**: Provides access to service implementations

## UI Adapter Interfaces

The UI components use adapter interfaces to interact with the underlying UI framework:

1. **IUiAdapter**: Base interface for UI adapters
2. **ITableAdapter**: Handles table data display and interaction
3. **IComboBoxAdapter**: Manages dropdown/combobox components
4. **IStatusAdapter**: Updates status messages and indicators

## Diagrams

### Class Diagrams

The application's interface structure is documented in PlantUML diagrams located in the `docs/diagrams/class` directory. These diagrams show the methods and relationships of the interfaces.

- `core.puml`: Contains the core service interfaces (IDataStore, IFileService, etc.)
- `ui.puml`: Contains the UI adapter interfaces

### Sequence Diagrams

Sequence diagrams in the `docs/diagrams/sequence` directory show how the components interact during key operations:

- `import.puml`: The file import process
- `validation.puml`: The validation process
- `correction.puml`: The correction application process

### Component Diagram

The component diagram in `docs/diagrams/component` shows the high-level structure of the application:

- `main_components.puml`: Overview of main components and their relationships

### Dependency Injection Diagram

The dependency injection diagram in `docs/diagrams/di` illustrates how dependencies are managed:

- `dependency_injection.puml`: Shows how the ServiceFactory creates and provides services to components

### Event System Diagram

The event system diagram in `docs/diagrams/events` illustrates the publish-subscribe architecture:

- `event_system.puml`: Shows how components communicate through events

## Updating the Diagrams

When making changes to the interfaces, follow these steps to ensure the diagrams stay in sync:

1. Update the interface definition in the code
2. Update the corresponding diagram in the `docs/diagrams` directory
3. Run the validation script to verify accuracy:
   ```
   python scripts/validate_interface_diagrams.py
   ```
4. Generate updated diagrams (requires Java):
   ```
   python scripts/generate_puml_diagrams.py
   ```

## Validation Script

The `scripts/validate_interface_diagrams.py` script checks that all interface methods defined in the code are correctly represented in the diagrams. It reports any missing or extra methods. Run this script after making changes to ensure the documentation remains accurate.

## Working with the Interface System

### Using the ServiceFactory

Components should request dependencies through the ServiceFactory:

```python
class DashboardInterface:
    def __init__(self, service_factory: IServiceFactory):
        self._service_factory = service_factory
        self._data_store = service_factory.get_service(IDataStore)
        self._file_service = service_factory.get_service(IFileService)
        self._validation_service = service_factory.get_service(IValidationService)
```

### Adding a New Service

To add a new service:

1. Define the interface in `src/interfaces/`
2. Create the implementation class
3. Update the diagrams
4. Register the service in the AppBootstrapper:
   ```python
   def _setup_services(self):
       # Register existing services
       # ...
       
       # Register new service
       self._service_factory.register_service(INewService, NewServiceImplementation)
   ```

### Implementing UI Adapters

UI adapters should implement the appropriate interface:

```python
class ConcreteTableAdapter(ITableAdapter):
    def __init__(self, table_widget):
        self._table_widget = table_widget
        
    def set_data(self, data):
        # Implementation
        
    def get_selected_item(self):
        # Implementation
```

### Working with the Event System

Components can communicate with each other through the event system:

```python
# Subscribe to events
self._event_manager.subscribe(EventType.DATA_CHANGED, self._on_data_changed)

# Handle events
def _on_data_changed(self, event_data):
    # Update UI or state based on the event data
    
# Publish events
self._event_manager.publish(EventType.VALIDATION_COMPLETED, validation_results)
```

## Viewing Diagrams

To view the UML diagrams:

1. If Java is installed, use `scripts/generate_puml_diagrams.py` to create PNG files
2. Otherwise:
   1. Copy the content of a `.puml` file
   2. Paste it into the [PlantUML online server](https://www.plantuml.com/plantuml/uml/)

## Diagram Validation

The validation script helps ensure the diagrams stay in sync with the code:

```
python scripts/validate_interface_diagrams.py
```

This will:
- Check each interface in the code against its corresponding diagram
- Report any missing methods (methods in code not in diagram)
- Report any extra methods (methods in diagram not in code)
- Tell you which diagrams need to be updated

## Understanding the Diagrams

### Core Interface Diagram
The core interface diagram shows all service interfaces and their relationships:
- Interfaces are shown with their methods
- Relationships between interfaces are indicated with arrows
- Dependencies are clearly marked

### UI Interface Diagram
The UI interface diagram illustrates:
- The adapter interface hierarchy
- UI component relationships
- Implementation relationships

### Sequence Diagrams
Sequence diagrams show the flow of control between components:
- Time flows from top to bottom
- Interactions between components are shown as arrows
- Activations indicate when a component is active
- Notes provide additional context

### Component and DI Diagrams
These diagrams provide a high-level overview of the system:
- Components and their dependencies
- Service factory patterns
- Initialization sequences

## Interface Design Principles

When working with or extending interfaces, follow these principles:

1. **Interface Segregation**: Keep interfaces focused on specific responsibilities
2. **Dependency Inversion**: Depend on abstractions, not implementations
3. **Single Responsibility**: Each interface should have a clear purpose
4. **Explicit Dependencies**: Make dependencies explicit through constructor injection

## Example: Understanding the IDataStore Interface

The `IDataStore` interface in `core.puml` shows:
- Methods for managing entries (get_entries, set_entries)
- Methods for validation lists (get_validation_list, set_validation_list)
- Methods for correction rules (get_correction_rules, set_correction_rules)
- Transaction management methods (begin_transaction, commit_transaction, rollback_transaction)
- Event subscription methods (subscribe, unsubscribe)

This gives a clear picture of the `IDataStore`'s responsibilities and dependencies.

## Further Resources

For more detailed information on the interface-based architecture:
- [Interface Architecture Document](INTERFACE_ARCHITECTURE.md) - Complete architecture overview
- [Interface Usage Guide](interface_usage_guide.md) - Practical examples for developers
- [Dependency Injection Guide](dependency_injection_guide.md) - How DI works in the application 