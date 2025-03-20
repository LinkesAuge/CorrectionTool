# Filtering System Documentation

The Chest Tracker Correction Tool includes a comprehensive filtering system that allows users to filter entries based on various criteria. This document provides an overview of the filtering system, its components, and how to use it.

## Overview

The filtering system consists of several components:

1. **Filter Classes**: Core implementations for different types of filters (text, validation list, date)
2. **Filter Manager**: Manages and applies multiple filters to data
3. **UI Components**: User interface elements for interacting with filters
4. **Filter Adapter**: Connects UI components with filter implementations and data store

## Filter Types

### Text Filter

The `TextFilter` class allows filtering entries based on text searches across one or more columns.

Features:
- Search in multiple columns
- Case-sensitive or case-insensitive matching
- Whole word matching
- Regular expression support

### Validation List Filter

The `ValidationListFilter` class allows filtering entries based on specific values from a validation list.

Features:
- Multi-select support (select multiple values)
- Include or exclude selection types
- Case-sensitive or case-insensitive matching
- Special handling for list-type columns

### Date Filter

The `DateFilter` class allows filtering entries based on date ranges.

Features:
- Filter by start date, end date, or both
- Date range selection
- Automatic conversion of string dates to datetime objects
- Support for custom date formats

## UI Components

### Filter Panel

The `FilterPanel` widget organizes and manages all filter UI components. It includes:

- Text search bar for global searching
- Dropdown filters for validation lists
- Date range pickers for date columns
- Filter status indicator showing active filter count
- Clear all button to reset all filters

### Filter Search Bar

The `FilterSearchBar` widget provides a text input field with options for:

- Case sensitivity
- Whole word matching
- Regular expression usage

### Filter Dropdown

The `FilterDropdown` widget provides a dropdown list of values with:

- Multi-select capability
- Select all, clear, and invert selection buttons
- Include/exclude selection type
- Case sensitivity toggle
- Search within dropdown values

### Filter Date Range

The `FilterDateRange` widget provides date selection with:

- Start date and end date pickers
- Date range selection
- Clear and apply buttons

## Filter State Persistence

The filtering system supports saving and loading filter state through the configuration manager. This allows user filters to be preserved between application sessions.

When the application is closed, the current filter state is saved, including:
- Active filters
- Selected values in validation list filters
- Search text and options in text filters
- Date ranges in date filters

When the application is reopened, this state is automatically restored.

## Standard Filters

The system automatically registers standard filters for common columns, including:

- Player
- Chest Name
- Chest Type
- Item Name
- Item Type
- Validation Errors (if present)

Date columns are automatically detected and registered with date filters.

## Code Examples

### Using the Filter Adapter

```python
# Create a filter adapter
filter_adapter = FilterAdapter(data_store)

# Set configuration manager for state persistence
filter_adapter.set_config_manager(config_manager)

# Create and get filter panel
filter_panel = filter_adapter.create_filter_panel()

# Register custom validation filter
filter_adapter.register_validation_filter("custom_column", "Custom Column")

# Register custom date filter
filter_adapter.register_date_filter("date_column", "Date")

# Apply filters
filter_adapter.apply_filters()

# Save filter state
filter_adapter.save_filter_state()

# Load filter state
filter_adapter.load_filter_state()
```

### Creating a Custom Filter

```python
# Create a text filter
text_filter = TextFilter("search_filter", "Search")
text_filter.set_target_columns(["column1", "column2"])
text_filter.set_search_text("search term")
filtered_df = text_filter.apply(df)

# Create a validation list filter
validation_filter = ValidationListFilter("list_filter", "List Filter", "category")
validation_filter.set_selected_values(["Value1", "Value2"])
filtered_df = validation_filter.apply(df)

# Create a date filter
date_filter = DateFilter("date_filter", "Date Filter", "created_at")
date_filter.set_date_range("2023-01-01", "2023-12-31")
filtered_df = date_filter.apply(df)
```

## Best Practices

1. **Performance Considerations**: When working with large datasets, consider optimizing filter operations by:
   - Using the `FilterManager` to apply multiple filters in one pass
   - Creating indexes on frequently filtered columns

2. **Dynamic Filter Registration**: Register only the filters that make sense for your current dataset:
   - Check for column existence before registering filters
   - Consider column data types (text filters for strings, date filters for dates)

3. **Filter UI Integration**:
   - Connect filter UI signals to update data views
   - Provide visual feedback when filters are active
   - Show filter status (e.g., counts of filtered items) 