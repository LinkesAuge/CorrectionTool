# UI Testing Guide for Correction Tool

## Introduction

This guide provides comprehensive information about testing the UI components of the Correction Tool application. It covers test setup, common testing patterns, and best practices for ensuring UI component quality and reliability.

## Test Organization

### Directory Structure

```
tests/
├── ui/                       # UI-specific tests
│   ├── components/           # Tests for individual UI components
│   ├── integration/          # Tests for component integration
│   ├── helpers/              # Helper classes and utilities for UI testing
│   └── fixtures/             # pytest fixtures for UI tests
├── conftest.py               # Global test fixtures
└── ...                       # Other test directories
```

### Naming Conventions

- Test files should be named with the prefix `test_` followed by the name of the module/component being tested (e.g., `test_validation_list_widget.py`)
- Test classes should be named with the prefix `Test` followed by the component name (e.g., `TestValidationListWidget`)
- Test methods should start with `test_` followed by a descriptive name of what's being tested (e.g., `test_populate_with_dataframe`)

## Testing Framework

### pytest-qt

The UI testing framework uses pytest-qt, which provides Qt-specific fixtures for testing Qt applications:

```python
def test_button_click(qtbot):
    widget = ValidationListWidget()
    
    # Add widget to qtbot for automatic cleanup
    qtbot.addWidget(widget)
    
    # Test interaction
    qtbot.mouseClick(widget.add_button, Qt.LeftButton)
    
    # Assert expected result
    assert widget.count() == 1
```

### UITestHelper Class

The `UITestHelper` class provides utility methods for common UI testing tasks:

```python
from tests.ui.helpers.ui_test_helper import UITestHelper

def test_validation_list_display(qtbot):
    helper = UITestHelper(qtbot)
    widget = helper.create_validation_list_widget()
    
    # Test with different data sources
    helper.populate_widget_with_list(widget, ["Item1", "Item2"])
    assert widget.count() == 2
    
    # Test signals
    with helper.wait_signal(widget.item_added):
        helper.click_add_button(widget)
```

## Mock Services

### Creating Mock Services

Create mock implementations of required interfaces for isolated testing:

```python
from src.interfaces.data_store import IDataStore

class MockDataStore(IDataStore):
    def __init__(self):
        self.data = {}
        self.validation_lists = {}
        
    def get_validation_list(self, list_name):
        return self.validation_lists.get(list_name, [])
        
    def update_validation_list(self, list_name, items):
        self.validation_lists[list_name] = items
        return True
```

### Using Mock Services

Inject mock services into UI components for testing:

```python
def test_component_with_mocks(qtbot):
    # Create mock services
    mock_data_store = MockDataStore()
    mock_config = MockConfigManager()
    
    # Configure the mocks
    mock_data_store.validation_lists["players"] = ["Player1", "Player2"]
    
    # Create widget with mocks
    widget = ValidationListWidget()
    widget.set_services(mock_data_store, mock_config)
    qtbot.addWidget(widget)
    
    # Test
    widget.populate()
    assert widget.count() == 2
```

## Testing Different Data Types

ValidationListWidget needs special handling for different data types:

### Testing with List Data

```python
def test_with_list_data(qtbot):
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    
    # Test with a simple list
    data = ["Item1", "Item2", "Item3"]
    widget.set_validation_list(data)
    
    assert widget.count() == 3
    assert widget.item(0).text() == "Item1"
```

### Testing with DataFrame Data

```python
def test_with_dataframe(qtbot):
    import pandas as pd
    
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    
    # Test with a DataFrame
    df = pd.DataFrame({"col1": ["Item1", "Item2", "Item3"]})
    widget.set_validation_list(df)
    
    assert widget.count() == 3
    assert widget.item(0).text() == "Item1"
```

### Testing with Method or Attribute

```python
def test_with_callable_items(qtbot):
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    
    # Test with a class that has items as a method
    class TestList:
        def items(self):
            return ["Item1", "Item2"]
    
    test_list = TestList()
    widget.set_validation_list(test_list)
    
    assert widget.count() == 2
    assert widget.item(0).text() == "Item1"
```

## Testing Button Functionality

Test button clicks and other interactions:

```python
def test_add_button(qtbot):
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    
    # Prepare for the dialog
    qtbot.keyClicks(widget.input_dialog, "New Item")
    qtbot.mouseClick(widget.input_dialog.buttons()[0], Qt.LeftButton)
    
    # Click the add button
    qtbot.mouseClick(widget.add_button, Qt.LeftButton)
    
    assert widget.count() == 1
    assert widget.item(0).text() == "New Item"
```

## Testing Signal Emissions

Verify signals are emitted correctly:

```python
def test_signal_emission(qtbot):
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    
    # Set up signal tracking
    signals_caught = []
    widget.item_added.connect(lambda item: signals_caught.append(item))
    
    # Trigger the signal
    with qtbot.waitSignal(widget.item_added, timeout=1000):
        widget._add_item("New Item")
    
    assert len(signals_caught) == 1
    assert signals_caught[0] == "New Item"
```

## Integration Testing

Test the interaction between components:

```python
def test_correction_manager_with_validation_lists(qtbot):
    # Set up mock services
    mock_services = create_mock_services()
    
    # Create both components
    validation_widget = ValidationListWidget()
    correction_manager = CorrectionManagerInterface(mock_services)
    
    qtbot.addWidget(validation_widget)
    qtbot.addWidget(correction_manager)
    
    # Test interaction
    correction_manager.add_validation_list("players", validation_widget)
    
    # Trigger an update
    validation_widget._add_item("New Player")
    
    # Verify correction manager updated
    assert "New Player" in correction_manager.get_validation_list("players")
```

## Test Data Generation

Use consistent test data generators:

```python
from tests.ui.helpers.test_data_generator import TestDataGenerator

def test_with_generated_data(qtbot):
    generator = TestDataGenerator()
    
    # Generate test data
    players = generator.create_player_list(10)
    chest_types = generator.create_chest_types()
    
    # Test with generated data
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    widget.set_validation_list(players)
    
    assert widget.count() == 10
```

## Test Synchronization

Handle asynchronous UI updates:

```python
def test_async_operations(qtbot):
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    
    # Start async operation and wait for it to complete
    with qtbot.waitSignal(widget.operation_completed, timeout=5000):
        widget.start_async_operation()
    
    # Now check the results
    assert widget.count() > 0
```

## Debugging Strategies

### Visual Debugging

Enable visual inspection during tests:

```python
def test_with_visual_inspection(qtbot, monkeypatch):
    # Only enable in development
    monkeypatch.setenv("VISUAL_DEBUG", "1")
    
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    widget.show()
    
    # Add visual delay for inspection
    qtbot.wait(1000)
    
    # Continue with test...
```

### Enhanced Logging

Add detailed logging for test runs:

```python
def test_with_enhanced_logging(qtbot, caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    
    # Perform test actions
    widget._add_item("Test Item")
    
    # Check logs
    assert "Adding item: Test Item" in caplog.text
```

## Best Practices

1. **Test in Isolation**: Test widgets in isolation before testing integrations
2. **Mock External Dependencies**: Use mock services to isolate UI testing
3. **Check Signal Connections**: Verify signals are connected and emit correctly
4. **Test Edge Cases**: Test empty lists, large datasets, and error conditions
5. **Verify Visual State**: Check that UI elements are visible, enabled, and correctly styled
6. **Test User Interactions**: Simulate actual user actions rather than directly calling methods
7. **Clean Up Resources**: Ensure all resources are cleaned up after tests
8. **Use Consistent Test Data**: Reuse test data generators for consistent test cases
9. **Add Detailed Assertions**: Include meaningful assertion messages
10. **Maintain Test Independence**: Each test should run independently of others

## Troubleshooting Common Test Issues

1. **QApplication Already Created**: Ensure only one QApplication instance exists
2. **Widget Not Showing**: Remember to call widget.show() for visual tests
3. **Signal Timeout**: Increase timeout duration for slow operations
4. **Mock Services Not Used**: Verify your component is using the mock services
5. **Inconsistent State**: Reset state between tests
6. **Event Loop Issues**: Use qWait() to allow the event loop to process
7. **Widget Clean-up**: Use qtbot.addWidget() to ensure proper cleanup

## Example Test Cases

### ValidationListWidget Tests

```python
class TestValidationListWidget:
    def test_initialization(self, qtbot):
        widget = ValidationListWidget()
        qtbot.addWidget(widget)
        assert widget is not None
        
    def test_populate_with_list(self, qtbot):
        widget = ValidationListWidget()
        qtbot.addWidget(widget)
        widget.set_validation_list(["Item1", "Item2"])
        assert widget.count() == 2
        
    def test_add_item(self, qtbot):
        widget = ValidationListWidget()
        qtbot.addWidget(widget)
        widget._add_item("New Item")
        assert widget.count() == 1
        
    def test_filter_functionality(self, qtbot):
        widget = ValidationListWidget()
        qtbot.addWidget(widget)
        widget.set_validation_list(["Apple", "Banana", "Cherry"])
        
        # Test filtering
        widget.filter_edit.setText("an")
        qtbot.keyClick(widget.filter_edit, Qt.Key_Enter)
        
        # Only "Banana" should be visible
        visible_count = 0
        for i in range(widget.count()):
            if not widget.item(i).isHidden():
                visible_count += 1
                assert "an" in widget.item(i).text().lower()
        
        assert visible_count == 1
```

### CorrectionManagerInterface Tests

```python
class TestCorrectionManagerInterface:
    def test_initialization(self, qtbot, mock_services):
        manager = CorrectionManagerInterface(mock_services)
        qtbot.addWidget(manager)
        assert manager is not None
        
    def test_validation_list_integration(self, qtbot, mock_services):
        manager = CorrectionManagerInterface(mock_services)
        qtbot.addWidget(manager)
        
        # Check if validation lists are loaded
        assert manager.player_list is not None
        assert manager.chest_type_list is not None
        assert manager.source_list is not None
```

## Conclusion

Effective UI testing is crucial for maintaining the stability and usability of the Correction Tool application. By following the guidelines in this document, you can create robust tests that verify the functionality, performance, and visual appearance of UI components.

For additional assistance, consult the UI testing reference implementations in the `tests/ui/` directory. 