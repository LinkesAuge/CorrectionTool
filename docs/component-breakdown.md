# Component Breakdown for Chest Tracker Correction Tool Rework

This document provides a detailed breakdown of the components needed for the rework implementation.

## UI Components

### Main Window (`main_window_interface.py`)
- **Purpose**: Main application container
- **Key Features**:
  - Tab navigation (Dashboard, Correction Manager)
  - Status bar for app-wide messages
  - Menu bar (File, Edit, View, Help)
- **Implementation Notes**:
  - Uses QTabWidget for main navigation
  - Preserves existing app icon and title
  - Manages state sharing between tabs
  - Uses interface-based architecture
  - Receives dependencies through constructor injection
  - Directly interacts with service interfaces

### Dashboard Components

#### `DashboardPanel` (`dashboard_panel.py`)
- **Purpose**: Main workspace for viewing and correcting entries
- **Key Features**:
  - QSplitter for layout division
  - Connects all sub-components
- **Implementation Notes**:
  - Replaces multiple existing panels (FilePanels, CorrectorPanel)
  - Manages state between sub-components

#### `SidebarWidget` (`sidebar_widget.py`)
- **Purpose**: Compact control panel for dashboard
- **Key Features**:
  - File import section
  - Statistics display
  - Action buttons
  - Filter controls
  - Auto-apply toggle
  - Fuzzy matching controls
- **Implementation Notes**:
  - Fixed width (25-30% of dashboard)
  - Vertical layout with sections

#### `FileImportSection` (`file_import_section.py`)
- **Purpose**: Controls for loading input and correction files
- **Key Features**:
  - Input file selection
  - Correction list selection
  - Recently used files dropdown
- **Implementation Notes**:
  - Compact layout with minimal wasted space
  - File type validation

#### `StatisticsSection` (`statistics_section.py`)
- **Purpose**: Display entry and validation statistics
- **Key Features**:
  - Entry count (total, valid, invalid)
  - Correction count
  - Fields with validation errors
  - Fuzzy match statistics
- **Implementation Notes**:
  - Updates in real-time
  - Visual indicators for status

#### `ActionButtonGroup` (`action_button_group.py`)
- **Purpose**: Vertical group of main action buttons
- **Key Features**:
  - Apply Corrections
  - Validate
  - Export
  - Clear All
- **Implementation Notes**:
  - Consistent button sizing
  - Icons with text
  - Tooltip descriptions

#### `FilterControls` (`filter_controls.py`)
- **Purpose**: Filter entries in the table
- **Key Features**:
  - Dropdown selectors from validation lists
  - Search field
  - Reset filters button
- **Implementation Notes**:
  - Multi-select capability
  - Updates when validation lists change

#### `FuzzyMatchControls` (`fuzzy_match_controls.py`)
- **Purpose**: Controls for fuzzy matching
- **Key Features**:
  - Enable/disable toggle
  - Threshold slider
  - Preset buttons (Low, Medium, High matching)
  - Visual feedback for current setting
- **Implementation Notes**:
  - Real-time updates to match threshold
  - Saves preferences to config
  - Visual cues for enabled state

#### `EnhancedTableView` (`enhanced_table_view.py`)
- **Purpose**: Display entries with advanced features
- **Key Features**:
  - Color-coded validation errors
  - In-place editing
  - Context menu for corrections
  - Field-specific indicators
  - Fuzzy match highlighting
- **Implementation Notes**:
  - Custom delegates for styling and editing
  - Custom model for data management

#### `TableContextMenu` (`table_context_menu.py`)
- **Purpose**: Right-click menu for table entries
- **Key Features**:
  - Edit entry option
  - Add to correction list
  - Apply validation
  - Quick correction options
  - Apply fuzzy match suggestions
- **Implementation Notes**:
  - Dynamic based on selected cell
  - Supports batch operations on multiple selections

### Correction Manager Components

#### `CorrectionManagerPanel` (`correction_manager_panel.py`)
- **Purpose**: Manage validation lists and correction rules
- **Key Features**:
  - QSplitter for layout division
  - Connects all sub-components
- **Implementation Notes**:
  - Replaces existing ValidationPanel
  - Manages state between sub-components

#### `CorrectionRulesSection` (`correction_rules_section.py`)
- **Purpose**: Manage correction rules
- **Key Features**:
  - Two-column table (From → To)
  - Add/Edit/Delete buttons
  - Import/Export controls
  - Search functionality
  - Drop target for drag operations
- **Implementation Notes**:
  - 50% width of correction manager
  - Custom model for data
  - Edit dialog with validation

#### `FuzzySuggestionSection` (`fuzzy_suggestion_section.py`)
- **Purpose**: Display and apply fuzzy match suggestions
- **Key Features**:
  - List of potential corrections
  - Confidence score display
  - Apply suggestion buttons
  - Add to rules option
- **Implementation Notes**:
  - Located below correction rules table
  - Updates based on selected entries
  - Visual ranking of suggestions

#### `ValidationListsContainer` (`validation_lists_container.py`)
- **Purpose**: Container for all validation list sections
- **Key Features**:
  - Stacked layout for three validation sections
  - Common controls
- **Implementation Notes**:
  - 50% width of correction manager
  - Manages common functionality between lists

#### `ValidationListSection` (`validation_list_section.py`)
- **Purpose**: Manage a specific validation list
- **Key Features**:
  - Compact table view
  - Direct editing
  - Import/Export buttons
  - Drag source for drag operations
- **Implementation Notes**:
  - Instantiated for each list type (player, chest type, source)
  - Custom styling based on list type

#### `ValidationControlsSection` (`validation_controls_section.py`)
- **Purpose**: Common controls for all validation lists
- **Key Features**:
  - Import all
  - Export all
  - Clear all
  - Settings
- **Implementation Notes**:
  - Located at bottom of ValidationListsContainer
  - Operates on all lists simultaneously

## Custom Delegates and Models

### `HighlightingDelegate` (`highlighting_delegate.py`)
- **Purpose**: Highlight cells with validation errors
- **Key Features**:
  - Color-coding by field type
  - Visual indicators for errors
  - Distinct styling for fuzzy matches
- **Implementation Notes**:
  - Custom paint method
  - Configuration for colors

### `EditableItemDelegate` (`editable_item_delegate.py`)
- **Purpose**: Enable in-place editing with validation
- **Key Features**:
  - Custom editor with validation
  - Dropdown selection from validation lists
- **Implementation Notes**:
  - Creates appropriate editor based on column

### `FuzzyMatchDelegate` (`fuzzy_match_delegate.py`)
- **Purpose**: Display fuzzy match information
- **Key Features**:
  - Confidence score visualization
  - Match type indicators
  - Suggestion preview
- **Implementation Notes**:
  - Custom paint method
  - Tooltip with match details

### `EnhancedTableModel` (`enhanced_table_model.py`)
- **Purpose**: Model for entry data with enhanced features
- **Key Features**:
  - Field-specific validation
  - Support for in-place editing
  - Detailed error information
  - Fuzzy match data
- **Implementation Notes**:
  - Extends existing TableModel
  - Adds metadata for validation status

### `CorrectionRulesModel` (`correction_rules_model.py`)
- **Purpose**: Model for correction rules table
- **Key Features**:
  - Two columns (From → To)
  - Support for sorting and filtering
  - Validation for duplicates
- **Implementation Notes**:
  - Custom data structure
  - Export/import capability

### `ValidationListModel` (`validation_list_model.py`)
- **Purpose**: Model for validation list tables
- **Key Features**:
  - Single column for entries
  - Support for direct editing
  - Drag source implementation
- **Implementation Notes**:
  - Different instances for each list type
  - Export/import capability

### `FuzzySuggestionModel` (`fuzzy_suggestion_model.py`)
- **Purpose**: Model for fuzzy match suggestions
- **Key Features**:
  - Displays entries and suggested corrections
  - Shows confidence scores
  - Sorting by score
- **Implementation Notes**:
  - Updates based on selected entries
  - Integrates with FuzzyMatcher service

## Drag and Drop Implementation

### `DragSource` (`drag_source.py`)
- **Purpose**: Base class for drag operations
- **Key Features**:
  - MIME data formatting
  - Drag start visualization
- **Implementation Notes**:
  - Implemented in ValidationListSection

### `DropTarget` (`drop_target.py`)
- **Purpose**: Base class for drop operations
- **Key Features**:
  - MIME data handling
  - Drop visualization
  - Validation of dropped data
- **Implementation Notes**:
  - Implemented in CorrectionRulesSection
  - Confirmation dialogs for new entries

## Business Logic Components

### `ValidationManager` (`validation_manager.py`)
- **Purpose**: Manage validation of entries
- **Key Features**:
  - Field-specific validation
  - Detailed error reporting
  - Support for validation lists
  - Fuzzy matching integration
- **Implementation Notes**:
  - Improved from existing validation logic
  - Real-time validation as data changes

### `CorrectionManager` (`correction_manager.py`)
- **Purpose**: Manage corrections of entries
- **Key Features**:
  - Apply correction rules
  - Track changes
  - Support for auto-apply
  - Fuzzy match correction suggestions
- **Implementation Notes**:
  - Improved from existing correction logic
  - Better feedback for applied corrections

### `FuzzyMatcher` (existing, to be enhanced)
- **Purpose**: Provide fuzzy text matching capabilities
- **Key Features**:
  - Similarity scoring
  - Configurable threshold
  - Multiple matching algorithms
  - Batch processing
  - Caching for performance
- **Implementation Notes**:
  - Enhanced from existing implementation
  - Tighter integration with ValidationList
  - Support for different validation strictness levels

### `ConfigManager` (existing)
- **Purpose**: Manage application configuration
- **Key Features**:
  - Save/load preferences
  - Remember recent files
  - Store validation lists
  - Fuzzy matching settings
- **Implementation Notes**:
  - Expanded for new UI settings
  - Improved state persistence

## Style and Theme

### `StyleManager` (`style_manager.py`)
- **Purpose**: Manage application styling
- **Key Features**:
  - Custom QSS stylesheets
  - Color themes
  - Widget-specific styling
- **Implementation Notes**:
  - Modern dark theme with gold accents
  - Consistent spacing and sizing

### `ThemeColors` (`theme_colors.py`)
- **Purpose**: Define color constants
- **Key Features**:
  - Main colors
  - Accent colors
  - Validation error colors
  - Fuzzy match colors
  - Text colors
- **Implementation Notes**:
  - Accessible color combinations
  - Support for future theme switching

## Implementation Dependencies

This implementation requires:

1. **Existing Components to Modify**:
   - `main_window_interface.py`
   - `models/chest_entry.py`