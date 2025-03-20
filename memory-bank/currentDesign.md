# Current Design Document

## Application Architecture

The Chest Tracker Correction Tool follows a layered architecture with a focus on separation of concerns and interface-based design:

### Architecture Layers

1. **UI Layer**
   - Qt-based UI components (MainWindow, TabWidgets, custom widgets)
   - UI adapters that implement standard interfaces
   - Visual components for data display and interaction

2. **Service Layer**
   - Business logic encapsulated in service classes
   - Services implement defined interfaces
   - Manages data processing, validation, and corrections

3. **Data Layer**
   - DataFrameStore as the central data repository
   - File handling and persistence
   - Data transformation and manipulation

4. **Configuration Layer**
   - ConfigManager for centralized configuration
   - Path management and file location services
   - User preferences and settings

### Core Design Patterns

1. **Interface-Based Design**
   - Components depend on interfaces rather than concrete implementations
   - Interfaces defined in the `src/interfaces` package
   - Enables testing, modularity, and alternative implementations

2. **Dependency Injection**
   - Components receive dependencies through constructors
   - ServiceFactory provides registered implementations
   - Reduces direct coupling between components

3. **Observer Pattern**
   - Events/signals used for inter-component communication
   - Components subscribe to events they're interested in
   - *Currently being standardized to address inconsistencies*

4. **Adapter Pattern**
   - UI adapters for Qt components
   - Standardized interfaces for UI interactions
   - Separates UI from business logic

5. **Factory Pattern**
   - ServiceFactory creates and manages service instances
   - Provides dependency injection mechanism
   - Supports registering test doubles for testing

## Core Components

### Data Management

#### DataFrameStore
- Central data repository for the application
- Manages entries and correction rules
- Provides event notifications for data changes
- *Currently being refactored to use standardized event system and dependency injection*

#### ValidationList
- Manages lists of valid values for validation
- Supports fuzzy matching with confidence scoring
- Implements IValidationList interface

### Service Layer

#### CorrectionService
- Applies correction rules to data entries
- Supports different correction types
- Validates potential corrections
- Implements ICorrectionService interface

#### FileService
- Handles file I/O operations
- Supports different file formats
- Provides asynchronous file operations
- Implements IFileService interface

#### ServiceFactory
- Creates and manages service instances
- Provides dependency injection
- Registers services by interface
- Implements IServiceFactory interface

### UI Layer

#### MainWindow
- Primary application window
- Manages the overall UI layout
- Coordinates between UI components
- Handles application-level events

#### Dashboard
- Main workspace for data viewing and editing
- Combines sidebar and main content area
- Provides access to primary functionality
- Uses composition of specialized UI components

#### UI Adapters
- TableAdapters for data display
- ComboBoxAdapters for selection widgets
- Implement standard adapter interfaces (ITableAdapter, etc.)
- *Some adapters still using direct DataFrameStore access, to be updated*

## Interface Architecture

The application has transitioned to an interface-based architecture to improve modularity, testability, and maintainability.

### Core Interfaces

1. **IDataStore**
   - Central interface for data access
   - Methods for managing entries and rules
   - Event notification for data changes

2. **IFileService**
   - File operations interface
   - Methods for loading/saving different file types
   - Path resolution and validation

3. **ICorrectionService**
   - Interface for applying corrections
   - Methods for validating and applying rules
   - Support for different correction types

4. **IValidationList**
   - Interface for validation list management
   - Methods for checking validity
   - Support for different matching algorithms

5. **IServiceFactory**
   - Interface for service management
   - Methods for registering and retrieving services
   - Support for dependency injection

6. **IConfigManager**
   - Interface for configuration management
   - Methods for accessing settings
   - Path resolution and management

### UI Adapter Interfaces

1. **IUiAdapter**
   - Base interface for all UI adapters
   - Common methods for UI components

2. **ITableAdapter**
   - Interface for table-based displays
   - Methods for data binding and manipulation
   - Selection and editing support

3. **IComboBoxAdapter**
   - Interface for dropdown components
   - Methods for item management
   - Selection handling

## Current Implementation Status

The interface architecture implementation is mostly complete, but with some identified issues:

### Working Features
- Core interfaces defined and implemented
- Service Factory with dependency injection
- Most UI components updated to use interfaces
- Configuration system using interfaces
- Basic validation and correction features

### Implementation Issues
1. **Event System Inconsistency**:
   - Two competing EventType implementations causing event subscription mismatches
   - Plan to standardize on a single EventType enum in src/interfaces/events.py

2. **Dependency Injection Issues**:
   - Some components still using direct singleton access via get_instance()
   - Needs refactoring to use consistent constructor injection

3. **Interface Implementation Gaps**:
   - Some implementations don't fully satisfy their interfaces
   - Need verification and compliance checking

## Interface System Implementation Plan

To address the identified issues with the interface architecture:

### Phase 1: Event System Standardization
- Move EventType enum to a single location in src/interfaces/events.py
- Remove duplicate EventType from dataframe_store.py
- Update all imports to use the standardized version
- Add proper type hints for event handlers and event data
- Create centralized event handling system (EventBus)

### Phase 2: Dependency Injection Refinement
- Refactor DataFrameStore to fully support dependency injection
- Remove get_instance() calls from all components
- Update all UI adapters to accept injected dependencies
- Enhance service registration and validation
- Prevent missing dependencies in components

### Phase 3: Interface Compliance Verification
- Add interface validation tests for each service
- Ensure all implementations satisfy their interfaces
- Create common base classes for shared behavior
- Document interface contracts with clear docstrings

### Phase 4: Documentation Update
- Update INTERFACE_ARCHITECTURE.md with refined architecture
- Document the event system standardization
- Create interface usage examples for developers
- Update bugfixing.mdc with lessons learned

## UI Design

### Visual Design Principles

1. **Minimalism**
   - Clean, focused interfaces
   - Remove visual clutter
   - Emphasize data content

2. **Consistency**
   - Uniform controls and behaviors
   - Standardized color schemes
   - Consistent spacing and alignment

3. **Feedback**
   - Clear visual feedback for actions
   - Status indicators
   - Progress visualization

4. **Accessibility**
   - High contrast options
   - Keyboard navigation
   - Screen reader support

### Layout Structure

1. **Dashboard Layout**
   - Split panel with sidebar (~30%) and main content area (~70%)
   - Sidebar contains file import, statistics, and action buttons
   - Main content area contains data tables and detail panels

2. **Detail Panel Layout**
   - Collapsible panels for additional information
   - Tab-based organization for different detail types
   - Context-sensitive controls

3. **Modal Dialogs**
   - Focused interaction for specific tasks
   - Minimal option set
   - Clear action buttons

### Color Scheme

1. **Primary Colors**
   - Dark blue-purple base (#2C3E50)
   - Gold accent (#F1C40F) for primary actions
   - Light gray (#ECF0F1) for content areas
   - Dark gray (#34495E) for headers and footers

2. **Semantic Colors**
   - Green (#2ECC71) for success/valid
   - Red (#E74C3C) for errors/invalid
   - Yellow (#F39C12) for warnings
   - Blue (#3498DB) for information

### Typography

1. **Font Families**
   - System default sans-serif for content
   - Monospace for code and data values
   - System default serif for headings

2. **Font Sizes**
   - 12px base size
   - 14px for headers
   - 11px for supporting text
   - 16px for main titles

## Data Flow

The application's data flow is being standardized with the event system updates:

### Current Flow

1. **Data Loading**
   - FileService loads data file
   - DataFrameStore processes and stores data
   - UI components update via events/signals
   - *Event mismatches occur here*

2. **Data Editing**
   - UI captures user edits
   - Changes sent to DataFrameStore
   - DataFrameStore emits change events
   - UI components update via events/signals
   - *Components using different EventType implementations miss updates*

3. **Correction Application**
   - CorrectionService gets data from DataFrameStore
   - CorrectionService applies rules
   - Updated data written back to DataFrameStore
   - DataFrameStore emits change events
   - UI components update via events/signals

### Standardized Flow (In Progress)

1. **Data Loading**
   - FileService loads data file
   - DataFrameStore processes and stores data
   - DataFrameStore emits standardized events via EventBus
   - UI components subscribe and update via standardized events

2. **Data Editing**
   - UI captures user edits
   - Changes sent to DataFrameStore
   - DataFrameStore emits standardized events via EventBus
   - All components receive updates consistently

3. **Correction Application**
   - CorrectionService gets data from DataFrameStore
   - CorrectionService applies rules
   - Updated data written back to DataFrameStore
   - DataFrameStore emits standardized events via EventBus
   - All components receive updates consistently

## Component Interactions

### Current Interactions

```
User → MainWindow → Dashboard → TableAdapter → DataFrameStore
                                             ↓
User ← MainWindow ← Dashboard ← TableAdapter ← DataFrameStore
```

With direct singleton access:
```
TableAdapter → DataFrameStore.get_instance() ← OtherComponent
```

### Standardized Interactions (In Progress)

```
User → MainWindow → Dashboard → TableAdapter → IDataStore → DataFrameStore
                                                         ↓
User ← MainWindow ← Dashboard ← TableAdapter ← EventBus ← DataFrameStore
```

With dependency injection:
```
TableAdapter(IDataStore) ← ServiceFactory → OtherComponent(IDataStore)
```

## Technical Constraints

1. **Qt Framework**
   - Application built on PySide6
   - Qt styling and layout constraints
   - Signal/slot mechanism integration

2. **Python Compatibility**
   - Compatible with Python 3.8+
   - Package dependencies management
   - Type hinting for improved development experience

3. **Performance Considerations**
   - Large dataset handling
   - Asynchronous file operations
   - UI responsiveness during processing

4. **Deployment Requirements**
   - Standalone executable package
   - Configuration file portability
   - User file access permissions

## Development Roadmap

### Short-term Focus
1. Standardize event system to fix event propagation issues
2. Refine dependency injection to eliminate singleton references
3. Verify interface compliance across all implementations
4. Update documentation with architecture improvements
5. Enhance file import/export functionality
6. Improve validation list management

### Medium-term Goals
1. Implement drag-and-drop functionality
2. Enhance filtering and search capabilities
3. Improve visual design and UX
4. Add user customization options
5. Enhance performance with large datasets

### Long-term Vision
1. Plugin system for extensibility
2. Enhanced reporting capabilities
3. Advanced correction algorithms
4. Cloud integration options
5. Multi-user collaboration features 