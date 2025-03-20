# Drag and Drop Functionality

## Overview

The Chest Tracker Correction Tool now supports drag and drop functionality between validation lists and correction rules. This feature allows users to:

1. Drag items from validation lists to the correction rules table to create new rules
2. Quickly set up correction rules based on validated values

## Architecture

The drag and drop functionality is implemented using a modular, component-based architecture:

### Core Components

- **DragDropManager**: Central manager that coordinates all drag-drop operations
  - Creates and manages adapters for UI components
  - Handles cleanup of adapters when components are closed

- **IDragDropAdapter**: Interface for all drag-drop adapters
  - Defines methods for connecting and disconnecting components
  - Handles event filtering for drag-drop events

- **ValidationListDragDropAdapter**: Adapter for ValidationListWidget
  - Enables dragging items from validation lists
  - Processes drop events for validation lists

- **CorrectionRulesDragDropAdapter**: Adapter for CorrectionRulesTable
  - Enables dropping items onto the correction rules table
  - Creates new correction rules from dropped validation items

### Integration

The drag-drop functionality is integrated into the `CorrectionManagerInterface`, which:
- Creates and initializes the `DragDropManager`
- Sets up connections between validation lists and the correction rules table
- Handles cleanup when the interface is closed

## Usage

To use the drag-drop functionality:

1. Navigate to the Correction Manager tab
2. Select an item from any validation list (Players, Chest Types, Sources)
3. Drag the item to the Correction Rules table
4. A new rule will be created with the selected item as the "to" value
5. Fill in the "from" value to complete the rule

## Technical Details

- Uses Qt's built-in drag-drop framework
- Custom MIME types for data transfer:
  - `application/x-validationitem` for validation list items
  - `application/x-correctionrule` for correction rules
- Adapters handle event filtering and data processing
- Event-based communication between components through the data store

## Implementation Notes

### Widget Access Patterns

- **ValidationListDragDropAdapter**: Accesses the `_table_view` property of the `ValidationListWidget`
  - ValidationListWidget uses a QTableView for displaying list items
  - The adapter applies drag-drop capabilities to this table view

- **CorrectionRulesDragDropAdapter**: Uses the `CorrectionRulesTable` widget directly
  - CorrectionRulesTable inherits from QTableView and implements the table interface directly
  - No separate table widget is needed - the class itself serves as the table view

### Qt Event Handling

- Event types in PySide6 are accessed via the QEvent class: `QEvent.DragEnter`, `QEvent.DragMove`, `QEvent.Drop`
- Event filters check the event type and delegate to appropriate handler methods
- Each event type has a specific event class (QDragEnterEvent, QDragMoveEvent, QDropEvent)

### Compatibility Notes

To ensure compatibility across different versions of PySide6:

- Import QEvent directly from PySide6.QtCore
- Use QEvent.DragEnter rather than Qt.QEvent.Type.DragEnter or Qt.DragEnter
- Use proper casting for event objects to their specific event classes

## Recent Fixes (March 2025)

1. **Widget Access Pattern Fixes**:
   - Fixed ValidationListDragDropAdapter to use `_table_view` instead of non-existent `list_view` attribute
   - Updated CorrectionRulesDragDropAdapter to use the widget directly instead of looking for a `table_widget` property

2. **Event Handling Fixes**:
   - Corrected event type references to use QEvent.DragEnter instead of Qt.QEvent.Type.DragEnter
   - Added proper QEvent import to both adapters
   - Fixed event type constants for all drag-drop related events

3. **Rule Creation**:
   - Ensured new rules created via drag-drop use the correct format
   - Updated add_rule method calls to match CorrectionRulesTable expectation

## Testing

The drag-drop functionality is tested with:
- Unit tests for individual adapters
- Integration tests for the complete drag-drop system
- Tests verify both setup and cleanup of resources

## Future Enhancements

Planned enhancements to the drag-drop functionality include:
- Drag and drop between validation lists
- Multi-item drag and drop operations
- Custom drag visual feedback
- Undo/redo support for drag-drop operations 