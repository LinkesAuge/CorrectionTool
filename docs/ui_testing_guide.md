# UI Testing Guide for Correction Tool

## Introduction

This guide provides comprehensive information about testing UI components in the Correction Tool application. It explains the organization of UI tests, the testing framework used, and provides examples of how to test various UI components.

## Test Organization

UI tests are organized into the following directory structure:

```
tests/
├── ui/
│   ├── components/         # Tests for individual UI components
│   ├── integration/        # Tests for component interactions and workflows
│   ├── helpers/            # Helper classes for UI testing
│   └── fixtures/           # Test fixtures for UI testing
```

### UI Components Directory

The `components` directory contains tests for individual UI components, such as:

- `test_validation_list_widget.py` - Tests for the ValidationListWidget
- `test_correction_manager_interface.py` - Tests for the CorrectionManagerInterface
- `test_correction_rules_table.py` - Tests for the CorrectionRulesTable
- `test_validation_lists_control_panel.py` - Tests for the ValidationListsControlPanel

### Integration Directory

The `integration` directory contains tests for interactions between components and complete workflows:

- `test_correction_manager_workflow.py` - Tests for the complete correction workflow
- `test_validation_list_management.py` - Tests for validation list management workflows

### Helpers Directory

The `helpers` directory contains utility classes for UI testing:

- `ui_test_helper.py` - Helper methods for testing UI components
- `mock_services.py` - Mock implementations of application services

### Fixtures Directory

The `fixtures` directory contains pytest fixtures for UI testing:

- `base_test_fixtures.py` - Common fixtures for UI tests, including sample data and service setup

## Naming Conventions

- Test files should be named `test_<component_name>.py`
- Test classes should be named `Test<ComponentName>`
- Test methods should be named `test_<functionality_being_tested>`

For example:

```python
# test_validation_list_widget.py
class TestValidationListWidget:
    def test_initialization(self):
        # Test initialization of ValidationListWidget
        pass
    
    def test_add_item(self):
        # Test adding items to ValidationListWidget
        pass
```

## Testing Framework

The Correction Tool UI tests use pytest with the pytest-qt plugin. This allows for testing Qt widgets and signals in a Pythonic way.

### Installing pytest-qt

```bash
uv add pytest-qt
```

### Basic pytest-qt Example

```python
def test_button_click(qtbot):
    widget = MyWidget()
    qtbot.addWidget(widget)
    
    # Click a button
    with qtbot.waitSignal(widget.clicked, timeout=1000):
        qtbot.mouseClick(widget.button, Qt.LeftButton)
    
    # Check that the widget has been updated
    assert widget.label.text() == "Button clicked"
```

## Mock Services

For testing UI components in isolation, we use mock implementations of the application services. These are defined in `tests/ui/helpers/mock_services.py`.

### Example: MockDataStore

```python
class MockDataStore(IDataStore):
    def __init__(self, test_data=None):
        self._data = test_data or pd.DataFrame({
            "column1": ["value1", "value2", "value3"],
            "column2": ["value4", "value5", "value6"]
        })
        self._subscribers = {}
        
    def get_data(self):
        return self._data
        
    def set_data(self, data):
        self._data = data
        self._notify_subscribers(EventType.DATA_UPDATED)
```

### Using Mock Services in Tests

```python
def test_validation_list_widget_with_mock_services(qtbot):
    # Create mock services
    mock_data_store = MockDataStore()
    mock_validation_service = MockValidationService()
    
    # Create the widget with mock services
    widget = ValidationListWidget(mock_data_store, mock_validation_service)
    qtbot.addWidget(widget)
    
    # Test widget functionality
    widget.add_item("test_item")
    assert "test_item" in widget.get_items()
```

## UITestHelper

The `UITestHelper` class in `tests/ui/helpers/ui_test_helper.py` provides methods for common UI testing operations:

```python
class UITestHelper:
    def __init__(self, qtbot):
        self.qtbot = qtbot
        
    def click_button(self, button):
        self.qtbot.mouseClick(button, Qt.LeftButton)
        
    def enter_text(self, widget, text):
        self.qtbot.keyClicks(widget, text)
        
    def select_item(self, list_widget, index):
        list_widget.setCurrentRow(index)
        
    def get_selected_rows(self, table_view):
        return [index.row() for index in table_view.selectedIndexes() 
                if index.column() == 0]
                
    def find_widget_by_name(self, parent, name):
        """Find a child widget by its object name"""
        return parent.findChild(QWidget, name)
        
    def find_widget_by_class(self, parent, widget_class, name=None):
        """Find a child widget by its class and optional name"""
        widgets = parent.findChildren(widget_class)
        if name:
            return next((w for w in widgets if name in w.objectName()), None)
        return widgets[0] if widgets else None
        
    def get_list_item_text(self, list_widget, index):
        """Get the text of an item in a QListWidget"""
        item = list_widget.item(index)
        return item.text() if item else None
        
    def verify_widget_visibility(self, widget, should_be_visible):
        """Assert whether a widget is visible or hidden"""
        assert widget.isVisible() == should_be_visible
        
    def verify_widget_enabled(self, widget, should_be_enabled):
        """Assert whether a widget is enabled or disabled"""
        assert widget.isEnabled() == should_be_enabled
        
    def verify_button_text(self, button, expected_text):
        """Assert that a button has the expected text"""
        assert button.text() == expected_text
        
    def capture_signals(self, signal, timeout=1000):
        """Capture emissions of a signal within a timeout"""
        signal_catcher = SignalCatcher(signal)
        return signal_catcher
        
    def verify_widget_property(self, widget, property_name, expected_value):
        """Assert that a widget has the expected property value"""
        assert widget.property(property_name) == expected_value
```

### Using UITestHelper in Tests

```python
def test_correction_manager_interface(qtbot):
    # Create the helper
    helper = UITestHelper(qtbot)
    
    # Set up services
    mock_service_factory = MockServiceFactory()
    
    # Create the widget
    interface = CorrectionManagerInterface(mock_service_factory)
    qtbot.addWidget(interface)
    
    # Find a specific button by name
    add_button = helper.find_widget_by_name(interface, "addButton")
    assert add_button is not None
    
    # Verify button is enabled
    helper.verify_widget_enabled(add_button, True)
    
    # Click the button
    helper.click_button(add_button)
    
    # Verify result
    # ... additional assertions
```

## Testing Different Data Types with ValidationListWidget

The ValidationListWidget can accept different data types, and tests should verify correct handling:

```python
def test_validation_list_widget_with_list(qtbot):
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    
    # Test with a simple list
    test_list = ["item1", "item2", "item3"]
    widget.set_list(test_list)
    
    assert widget.count() == len(test_list)
    for i, item in enumerate(test_list):
        assert widget.item(i).text() == item

def test_validation_list_widget_with_dataframe(qtbot):
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    
    # Test with a DataFrame
    import pandas as pd
    test_df = pd.DataFrame({"column": ["item1", "item2", "item3"]})
    widget.set_list(test_df)
    
    assert widget.count() == len(test_df)
    for i, item in enumerate(test_df["column"]):
        assert widget.item(i).text() == item
```

## Headless Testing Compatibility

When testing UI components in a headless environment (like CI/CD pipelines or servers without a display), there are specific challenges and best practices to follow.

### Challenges with Headless UI Testing

1. **Widget Visibility**: In headless environments, widgets may report different visibility states compared to desktop environments.
2. **Signal Handling**: Signal propagation may behave differently in headless environments.
3. **Rendering Issues**: Components that depend on rendering or painting may not work as expected.
4. **Window Activation**: Tests that require window activation or focus may fail.

### Best Practices for Headless Testing

1. **Avoid Visibility Checks**: Instead of checking `isVisible()`, check for widget existence and enabled state:

   ```python
   # Not recommended for headless environments
   assert widget._button.isVisible() is True
   
   # Recommended approach
   assert hasattr(widget, "_button")
   assert widget._button is not None
   assert widget._button.isEnabled() is True
   ```

2. **Use Enabled State Over Visibility**: UI components should use `setEnabled()` instead of `setVisible()` when possible:

   ```python
   # Not recommended for headless tests
   self._clear_button.setVisible(bool(text))
   
   # Recommended approach
   self._clear_button.setEnabled(bool(text))
   ```

3. **Verify Underlying Data State**: Always check both the UI state and the underlying data/model state:

   ```python
   # Check both UI and model state
   assert widget.get_search_text() == search_text
   assert text_filter.search_text == search_text  # Verify model state too
   ```

4. **Avoid Unnecessary show() Calls**: Don't rely on widget.show() in tests unless absolutely necessary:

   ```python
   # Not needed for most tests
   widget = FilterSearchBar(text_filter)
   widget.show()  # This can cause issues in headless environments
   
   # Usually sufficient
   widget = FilterSearchBar(text_filter)
   ```

5. **Use Simplified Test Cases**: Create basic test cases to validate test infrastructure:

   ```python
   def test_simple_widget(self, qtbot):
       """Test a simple widget to verify test environment."""
       widget = QLabel("Test Label")
       qtbot.addWidget(widget)
       
       assert widget.text() == "Test Label"
       assert widget is not None
       assert widget.isEnabled() is True
   ```

### Examples of Headless-Compatible Tests

```python
# Test for FilterSearchBar compatible with headless environments
def test_search_text(self, app, text_filter):
    """Test setting and getting search text."""
    widget = FilterSearchBar(text_filter)

    # Test setting text
    search_text = "test search"
    widget.set_search_text(search_text)

    # Check text was set (both UI and model)
    assert widget.get_search_text() == search_text
    assert text_filter.search_text == search_text
    
    # Check button state (enabled instead of visible)
    assert widget._clear_button.isEnabled() is True
```

### Adapting Existing Tests for Headless Compatibility

When updating existing tests for headless compatibility:

1. Replace `isVisible()` checks with `isEnabled()` or existence checks
2. Add verification of the underlying data model state
3. Remove unnecessary `show()` calls
4. Use `addWidget(widget)` with qtbot to properly register widgets
5. Add timeout parameters to signal waiting operations

By following these guidelines, UI tests will be more reliable in both headed and headless environments, making them suitable for continuous integration pipelines.

## Test Fixtures

The `base_test_fixtures.py` file contains fixtures that can be used across multiple tests:

```python
@pytest.fixture
def mock_service_factory():
    factory = MockServiceFactory()
    return factory

@pytest.fixture
def sample_validation_list():
    return ["item1", "item2", "item3", "item4", "item5"]

@pytest.fixture
def sample_correction_rules():
    return [
        {"from": "item1", "to": "corrected1", "enabled": True},
        {"from": "item2", "to": "corrected2", "enabled": True},
        {"from": "item3", "to": "corrected3", "enabled": False},
    ]

@pytest.fixture
def ui_helper(qtbot):
    return UITestHelper(qtbot)
```

## Testing Button Functionality

Example test for button functionality in ValidationListWidget:

```python
def test_button_functionality(qtbot, ui_helper):
    # Create widget
    widget = ValidationListWidget()
    qtbot.addWidget(widget)
    
    # Find buttons
    add_button = ui_helper.find_widget_by_name(widget, "addButton")
    delete_button = ui_helper.find_widget_by_name(widget, "deleteButton")
    
    # Test add button
    # First, set up with initial data
    widget.set_list(["initial_item"])
    
    # Spy on the item_added signal
    with qtbot.waitSignal(widget.item_added, timeout=1000) as blocker:
        # Set text in the line edit and click add
        line_edit = ui_helper.find_widget_by_class(widget, QLineEdit)
        ui_helper.enter_text(line_edit, "new_item")
        ui_helper.click_button(add_button)
    
    # Verify signal emission and widget update
    assert blocker.args == ["new_item"]  # Check signal argument
    assert widget.count() == 2  # Check item count
    assert ui_helper.get_list_item_text(widget, 1) == "new_item"  # Check item added
    
    # Test delete button
    # Select the item to delete
    ui_helper.select_item(widget, 1)
    
    # Spy on the item_deleted signal
    with qtbot.waitSignal(widget.item_deleted, timeout=1000) as blocker:
        ui_helper.click_button(delete_button)
    
    # Verify signal emission and widget update
    assert blocker.args == ["new_item"]  # Check signal argument
    assert widget.count() == 1  # Check item count
```

## Integration Testing Example

Example test for integration between ValidationListWidget and CorrectionManagerInterface:

```python
def test_validation_list_widget_integration(qtbot, mock_service_factory, ui_helper):
    # Create correction manager interface
    interface = CorrectionManagerInterface(mock_service_factory)
    qtbot.addWidget(interface)
    
    # Find the validation list widget in the interface
    validation_list_widget = ui_helper.find_widget_by_class(
        interface, ValidationListWidget, "validationListWidget"
    )
    assert validation_list_widget is not None
    
    # Find the add button in the validation list widget
    add_button = ui_helper.find_widget_by_name(validation_list_widget, "addButton")
    assert add_button is not None
    
    # Test adding an item through the interface
    line_edit = ui_helper.find_widget_by_class(validation_list_widget, QLineEdit)
    ui_helper.enter_text(line_edit, "test_integration_item")
    ui_helper.click_button(add_button)
    
    # Verify that the item was added to the validation list
    assert "test_integration_item" in mock_service_factory.validation_service.validation_lists[0]
```

## Test Data Generation

For tests that require sample data, it's important to have consistent test data. The `test_data.py` module provides functions for generating test data:

```python
def create_sample_correction_rules(count=10):
    """Create a list of sample correction rules for testing."""
    return [
        {
            "from": f"from_value_{i}",
            "to": f"to_value_{i}",
            "enabled": i % 2 == 0
        }
        for i in range(count)
    ]

def create_sample_validation_list(count=10, prefix="item"):
    """Create a sample validation list for testing."""
    return [f"{prefix}_{i}" for i in range(count)]

def create_sample_dataframe(rows=10, cols=3):
    """Create a sample DataFrame for testing."""
    import pandas as pd
    import numpy as np
    
    data = {}
    for col in range(cols):
        col_name = f"column_{col}"
        data[col_name] = [f"value_{col}_{row}" for row in range(rows)]
    
    return pd.DataFrame(data)
```

## Test Runner Script

A dedicated script for running UI tests is available in `scripts/run_ui_tests.py`:

```python
#!/usr/bin/env python
"""
UI test runner script for the Correction Tool application.

This script sets up the proper environment for running UI tests and
executes pytest with the correct parameters.
"""

import os
import sys
import argparse
import pytest
from pathlib import Path

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Run UI tests for Correction Tool')
    parser.add_argument('--test', '-t', help='Pattern to match for test files')
    parser.add_argument('--verbose', '-v', action='count', default=0, 
                        help='Verbosity level (use multiple -v for more detail)')
    args = parser.parse_args()
    
    # Set environment variables for Qt
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # Use offscreen rendering for headless testing
    
    # Determine the project root directory
    project_root = Path(__file__).parent.parent
    
    # Build the pytest arguments
    pytest_args = [str(project_root / 'tests' / 'ui')]
    
    # Add verbosity flag
    if args.verbose > 0:
        pytest_args.extend(['-' + 'v' * args.verbose])
    
    # Add test filter if specified
    if args.test:
        pytest_args.extend(['-k', args.test])
    
    # Run pytest with the constructed arguments
    return pytest.main(pytest_args)

if __name__ == '__main__':
    sys.exit(main())
```

## Testing Components with File Dialogs

Testing UI components that use `QFileDialog` presents unique challenges in headless environments where file dialogs cannot be displayed or interacted with. This section outlines two recommended approaches for testing such components.

### Challenges:

1. `QFileDialog` methods like `getOpenFileName()` and `getSaveFileName()` require user interaction
2. In headless or automated testing environments, these dialogs cannot be displayed or interacted with
3. Components that rely on these dialogs become difficult to test without special handling

### Recommended Approaches:

#### 1. Test Mode Pattern

This approach involves modifying the component to include a "test mode" that bypasses the file dialog and uses pre-specified file paths instead.

**Implementation example:**

```python
class MyFileImportComponent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize test mode attributes
        self._test_mode = False
        self._test_file_path = None
        
    def set_test_mode(self, enabled=True):
        """Enable test mode for headless testing."""
        self._test_mode = enabled
        
    def set_test_file_path(self, file_path):
        """Set a test file path to use in test mode."""
        self._test_file_path = file_path
        
    def import_file(self):
        """Import a file, using test file path if in test mode."""
        file_path = None
        
        if self._test_mode and self._test_file_path:
            file_path = self._test_file_path
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open File", "", "All Files (*)"
            )
            
        if file_path:
            # Process the selected file
            self._process_file(file_path)
```

**Test case example:**

```python
def test_import_file_in_test_mode(self, file_component, qtbot, tmp_path):
    # Create a test file
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Test content")
    
    # Set up test mode
    file_component.set_test_mode(True)
    file_component.set_test_file_path(str(test_file))
    
    # Set up signal capture
    with qtbot.waitSignal(file_component.file_imported, timeout=1000):
        # Trigger import
        file_component.import_file()
        
    # Verify file was processed
    assert file_component.has_imported_file()
    assert file_component.get_file_content() == "Test content"
```

#### 2. Monkeypatching QFileDialog

This approach uses pytest's monkeypatch fixture to replace `QFileDialog` methods with mock implementations, without changing the component.

**Test case example:**

```python
def test_import_file_with_monkeypatch(self, file_component, qtbot, monkeypatch, tmp_path):
    # Create a test file
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Test content")
    
    # Mock QFileDialog.getOpenFileName
    def mock_get_open_filename(*args, **kwargs):
        return str(test_file), "All Files (*)"
        
    monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_get_open_filename)
    
    # Set up signal capture
    with qtbot.waitSignal(file_component.file_imported, timeout=1000):
        # Trigger import
        file_component.import_file()
        
    # Verify file was processed
    assert file_component.has_imported_file()
    assert file_component.get_file_content() == "Test content"
```

### Best Practices for File Dialog Testing

1. **Implement both approaches**: The test mode pattern is more flexible and explicit, but monkeypatching is useful for testing existing components without modification.

2. **Use temporary files**: Create test files in a temporary directory using `pytest`'s `tmp_path` fixture for clean test isolation.

3. **Mock file services**: If your component uses a service to process files, consider mocking that service instead of testing with real files.

4. **Test both file selection and cancellation**: Test what happens when a file is selected and when the dialog is cancelled (returning an empty string).

5. **Isolate file processing logic**: Keep the file dialog interaction separate from file processing logic to make testing easier.

### Example Implementation

The `FileImportWidget` class implements the test mode pattern and has comprehensive tests in `tests/ui/widgets/test_file_import_widget.py` demonstrating both approaches.

## Conclusion

This UI testing guide provides a comprehensive framework for testing UI components in the Correction Tool application. By following these guidelines and using the provided utilities, you can create robust tests that verify the functionality of UI components and their interactions.

Remember these key points:
- Use the pytest-qt plugin for testing Qt widgets
- Use mock services for isolating UI components during testing
- Use the UITestHelper for common UI testing operations
- Test each component with different data types
- Create integration tests to verify component interactions
- Use the provided test fixtures for common setup scenarios
- Run UI tests using the dedicated runner script

For more details on specific components, refer to the test examples in the `tests/ui/components` directory. 