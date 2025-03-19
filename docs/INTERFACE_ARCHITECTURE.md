# Interface-Based Architecture

## Overview

We are implementing an interface-based architecture for the Chest Tracker Correction Tool to address circular dependencies and improve modularity. This document outlines the architecture, current progress, and next steps.

## Key Components

### Core Interfaces
- `IDataStore`: Interface for the central data store (DataFrameStore)
- `IFileService`: Interface for file operations (FileService)
- `ICorrectionService`: Interface for correction rule management (CorrectionService)
- `IValidationService`: Interface for validation operations (ValidationService)
- `IConfigManager`: Interface for configuration management (ConfigManager)
- `IServiceFactory`: Interface for service creation and management (ServiceFactory)

### UI Adapter Interfaces
- `IUiAdapter`: Base interface for all UI adapters
- `ITableAdapter`: Interface for table view adapters
- `IComboBoxAdapter`: Interface for combo box adapters
- `IStatusAdapter`: Interface for status bar adapters

### Bootstrapping
- `AppBootstrapper`: Class responsible for initializing services in the correct order

## Current Progress

### Completed
- Created all core interfaces in the `src/interfaces` package
- Updated the `ValidationList` class to accept an `IConfigManager` interface
- Updated `ServiceFactory` to implement `IServiceFactory` interface
- Added dependency injection support to `ServiceFactory`
- Created `AppBootstrapper` to handle application initialization
- Created a standalone demo script that showcases the interface architecture
- Developed `ValidationListComboAdapter` that implements `IComboBoxAdapter`

### In Progress
- Creating table adapters that implement `ITableAdapter`
- Updating entry point script to use `AppBootstrapper`
- Implementing remaining UI adapters

### Pending
- Restructuring package imports to avoid circular references
- Updating UI components to use interface implementations
- Creating a comprehensive test suite for the new architecture
- Adding proper error handling with user-friendly messages
- Optimizing performance for large datasets

## Implementation Strategy

1. **Define Interfaces**: Create interfaces for all major components (COMPLETED)
   - Core data components (data store, services)
   - UI adapters (tables, combo boxes, status bars)

2. **Update Components to Use Interfaces**: Modify existing components to depend on interfaces rather than concrete implementations (IN PROGRESS)
   - Update `ValidationList` to use `IConfigManager` (COMPLETED)
   - Update services to use `IDataStore` (COMPLETED)
   - Create UI adapters that implement adapter interfaces (IN PROGRESS)

3. **Implement Dependency Injection**: Provide a way to inject dependencies through interfaces (IN PROGRESS)
   - Enhance `ServiceFactory` with register/resolve methods (COMPLETED)
   - Create `AppBootstrapper` to handle initialization (COMPLETED)
   - Update entry point to use bootstrapper (PENDING)

4. **Break Circular Dependencies**: Separate interfaces from implementations (IN PROGRESS)
   - Create dedicated interface package (COMPLETED)
   - Use interface types in signatures (COMPLETED)
   - Use lazy loading when needed (COMPLETED)
   - Restructure package imports (PENDING)

## Resolving Circular Dependencies

The main circular dependency chain was:
1. `src/models/validation_list.py` imports `src/services/config_manager.py`
2. `src/services/__init__.py` imports `src/services/service_factory.py`
3. `src/services/service_factory.py` imports UI adapters from `src/ui/adapters/dataframe_adapter.py`
4. `src/ui/__init__.py` imports `src/ui/main_window.py`
5. `src/ui/main_window.py` imports `src/models/validation_list.py`

Our solution:
1. **Interface Extraction**: Created interfaces for all components in the chain
2. **Dependency Inversion**: Updated `ValidationList` to depend on `IConfigManager` interface
3. **Lazy Loading**: Added optional dependency injection with fallback lazy loading
4. **Service Factory Enhancement**: Implemented dependency registration and resolution
5. **Bootstrapper Creation**: Added `AppBootstrapper` to handle initialization order

## Benefits

- **Modularity**: Cleaner separation between components
- **Testability**: Easier to create mock implementations for testing
- **Flexibility**: Components can be swapped without modifying dependents
- **Clarity**: Component responsibilities are clearly defined
- **Maintainability**: Reduced coupling between components

## Example Usage

### Using the AppBootstrapper

```python
from src.app_bootstrapper import AppBootstrapper

# Initialize the application
bootstrapper = AppBootstrapper()
bootstrapper.initialize()

# Get services through interfaces
service_factory = bootstrapper.get_service_factory()
data_store = service_factory.get_data_store()
file_service = service_factory.get_file_service()
```

### Using ValidationList with IConfigManager

```python
from src.models.validation_list import ValidationList
from src.interfaces import IConfigManager
from src.services.config_manager import ConfigManager

# Create a config manager that implements IConfigManager
config: IConfigManager = ConfigManager()

# Create a ValidationList using the interface
player_list = ValidationList(
    list_type="player",
    entries=["Player1", "Player2"],
    config_manager=config  # Pass the interface
)
```

### Using a UI Adapter with Interfaces

```python
from PySide6.QtWidgets import QComboBox
from src.ui.adapters.validation_list_combo_adapter import ValidationListComboAdapter
from src.interfaces import IComboBoxAdapter

# Create a combo box
combo_box = QComboBox()

# Create an adapter that implements IComboBoxAdapter
adapter: IComboBoxAdapter = ValidationListComboAdapter(combo_box, "player")
adapter.connect()

# Use the adapter through the interface
adapter.add_item("New Player")
current_selection = adapter.get_selected_item()
```

## Next Steps

1. **Complete UI Adapter Implementation**:
   - Create `EntryTableAdapter` that implements `ITableAdapter`
   - Create `CorrectionRuleTableAdapter` that implements `ITableAdapter`

2. **Update Application Entry Point**:
   - Modify main script to use `AppBootstrapper`
   - Ensure proper initialization of all components

3. **Create Comprehensive Tests**:
   - Unit tests for all interface implementations
   - Integration tests for component communication
   - End-to-end tests for typical workflows

4. **Documentation and Examples**:
   - Add more detailed documentation for each interface
   - Create example code for common use cases
   - Add architecture diagrams

## Conclusion

The interface-based architecture is a significant improvement to the Chest Tracker Correction Tool's code organization. It addresses circular dependencies, improves modularity, and makes the code more maintainable and testable. The transition to this architecture will be gradual but will ultimately result in a more robust application. 