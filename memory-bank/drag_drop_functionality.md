# Drag and Drop Functionality

## Overview
The drag and drop functionality allows for efficient data entry by enabling users to drag items from validation lists directly into correction rules. This simplifies the process of creating new correction rules and reduces data entry errors.

## Components

### DragDropManager
- Central coordinator for all drag-drop operations
- Manages adapters for different UI components
- Handles setup and cleanup of drag-drop functionality

### ValidationListDragDropAdapter
- Enables drag operations from validation list widgets
- Handles drop operations when items are dragged between validation lists
- Serializes validation list items to MIME data for transfer

### CorrectionRulesDragDropAdapter
- Accepts drops from validation lists onto the correction rules table
- Creates new correction rules from dropped validation items
- Updates existing rules when items are dropped onto them

## Feature Flag
The drag and drop functionality can be enabled or disabled via a feature flag in the configuration:

```ini
[Features]
enable_drag_drop = True
```

This allows for graceful degradation if issues are encountered with the drag-drop system.

## Implementation Notes
- Drag operations use Qt's built-in drag-drop framework
- Custom MIME type (application/x-validation-item) is used for data transfer
- Event filters are used to intercept drag and drop events
- The system utilizes the data store for persistence of changes

## Testing

### Unit Tests
The drag-drop system includes comprehensive unit tests for each component:

1. `test_drag_drop_manager.py`: Tests the DragDropManager functionality
   - Verifies adapter management
   - Tests setup and cleanup operations
   - Ensures proper integration with validation lists and correction rules

2. `test_validation_list_drag_drop_adapter.py`: Tests the ValidationListDragDropAdapter
   - Verifies drag enablement
   - Tests MIME data creation
   - Validates drop handling between validation lists

3. `test_correction_rules_drag_drop_adapter.py`: Tests the CorrectionRulesDragDropAdapter
   - Validates acceptance of validation items
   - Tests creation of new correction rules
   - Verifies updating of existing rules

### Integration Tests
The integration tests in `test_drag_drop_integration.py` verify the complete system:
   - Tests end-to-end drag-drop operations
   - Validates data persistence across the system
   - Ensures proper cleanup of all components

## Future Enhancements
- Multi-item drag and drop support
- Enhanced visual feedback during drag operations
- Drag-drop between validation lists
- Customizable drag-drop behavior

## Known Issues
- The ValidationListWidget must have a table_view attribute for the adapter to connect to it
- The CorrectionRulesTable must properly implement the required methods for drag-drop (setAcceptDrops, setDragDropMode, etc.)
- When testing, mock objects must implement all required methods that the adapters will use

## Testing Implementation
When implementing tests for the drag-drop functionality:

1. Ensure that mock objects fully implement all methods used by adapters:
   - `setAcceptDrops`, `setDragDropMode`, `installEventFilter`, `removeEventFilter` for UI components
   - Appropriate data store methods like `update_validation_list` and `update_correction_rules`

2. Use the provided mock event classes to simulate drag and drop operations:
   - `MockDragEnterEvent` for drag enter events
   - `MockDropEvent` for drop events with proper position information

3. Verify both the visual state changes and the data persistence:
   - Check that UI components are updated correctly
   - Ensure that the data store receives the correct updates

4. Test integration between components to verify end-to-end functionality

## Usage for Developers
To enable drag-drop in new components:
1. Create a new adapter that extends the base adapter class
2. Implement the required event handlers
3. Register the adapter with the DragDropManager

See existing adapters for reference implementations.

## Next Steps After Drag-Drop Implementation

Now that the basic drag-drop functionality has been implemented and tested, the next priorities are:

1. **Main Window Cleanup**: Remove redundant main_window.py, main_window_refactor.py, and bridge classes as part of the interface system implementation plan.
2. **Enhanced Drag-Drop Features**: 
   - Implement drag-drop between validation lists
   - Add multi-item drag-drop support
   - Improve visual feedback during drag operations
3. **Documentation Updates**:
   - Create user guides for drag-drop functionality
   - Add developer documentation for extending the drag-drop system
4. **Integration with Other Features**:
   - Link drag-drop with clipboard operations
   - Enhance interaction with filter components

These improvements will build on the solid foundation of the current drag-drop implementation while addressing other important architectural needs of the application. 