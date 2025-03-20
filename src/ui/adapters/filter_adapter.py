"""
filter_adapter.py

Description: Adapter to connect filter UI with filter manager and data store
"""

import logging
from typing import Dict, List, Set, Any, Optional

from PySide6.QtCore import QObject, Signal

from src.interfaces import IDataStore, IConfigManager
from src.services.filters import (
    FilterManager,
    TextFilter,
    ValidationListFilter,
    DateFilter,
)
from src.ui.widgets.filters.filter_panel import FilterPanel
from src.ui.widgets.filters.filter_search_bar import FilterSearchBar


class FilterAdapter(QObject):
    """
    Adapter to connect filter UI with filter manager and data store.

    This class handles the creation of filter UI components and manages
    the interactions between the UI, filter manager, and data store.

    Attributes:
        filtered_data (Signal): Signal emitted when data is filtered
    """

    filtered_data = Signal(dict)

    def __init__(self, data_store: IDataStore):
        """
        Initialize the filter adapter.

        Args:
            data_store: Data store containing the data to filter
        """
        super().__init__()
        self._data_store = data_store
        self._filter_manager = FilterManager()
        self._filter_panel: Optional[FilterPanel] = None
        self._unique_values: Dict[str, Set[str]] = {}
        self._config_manager: Optional[IConfigManager] = None
        self._logger = logging.getLogger("ui.filter_adapter")

    def set_config_manager(self, config_manager: IConfigManager) -> None:
        """
        Set the configuration manager for filter state persistence.

        Args:
            config_manager: The configuration manager to use
        """
        self._config_manager = config_manager
        self._logger.debug("Configuration manager set")

    def create_filter_panel(self) -> FilterPanel:
        """
        Create and return a filter panel widget.

        This panel contains UI components for all available filters.

        Returns:
            The filter panel widget
        """
        if self._filter_panel:
            return self._filter_panel

        # Create the filter panel
        self._filter_panel = FilterPanel(self._filter_manager, self._data_store)

        # Create text search filter
        self._create_search_filter()

        # Register standard validation filters
        try:
            self._register_standard_filters()
        except Exception as e:
            self._logger.error(f"Error registering standard filters: {e}")

        # Connect signals
        self._filter_panel.filter_applied.connect(self._on_filter_applied)
        self._logger.debug("Filter panel created")

        # Load saved filter state if available
        if self._config_manager:
            self._filter_panel.load_filter_state(self._config_manager)
            self._logger.debug("Filter state loaded from configuration")

        return self._filter_panel

    def _create_search_filter(self) -> None:
        """Create and set up the text search filter."""
        # Create text filter
        search_filter = TextFilter("global_search", "Global Search")
        self._filter_manager.register_filter("global_search", search_filter)

        # Create search bar
        search_bar = FilterSearchBar(search_filter)

        # Add to filter panel
        if self._filter_panel:
            self._filter_panel.set_search_bar(search_bar)

    def _on_filter_applied(self) -> None:
        """Handle filter application."""
        df = self._data_store.get_entries()
        if df is None or df.empty:
            self._logger.warning("No data available for filtering")
            return

        # Apply filters
        filtered_df = self._filter_manager.apply_filters(df)

        # Emit filtered data
        result = {
            "filtered_df": filtered_df,
            "total_rows": len(df),
            "filtered_rows": len(filtered_df),
            "active_filters": self._filter_manager.get_active_filter_count(),
        }

        self.filtered_data.emit(result)

        # Save filter state if configured
        if self._config_manager:
            self._filter_panel.save_filter_state(self._config_manager)
            self._logger.debug("Filter state saved to configuration")

    def on_data_changed(self) -> None:
        """Handle data change events from the data store."""
        self._update_searchable_columns()
        self._update_filter_values()

        # Apply filters to get updated filtered data
        self._on_filter_applied()

    def _update_searchable_columns(self) -> None:
        """Update the list of searchable columns."""
        if not self._filter_panel:
            return

        df = self._data_store.get_entries()
        if df is None or df.empty:
            return

        # Get text columns suitable for searching
        text_columns = [col for col in df.columns if df[col].dtype == "object"]

        # Get global search filter and update columns
        text_filter = self._filter_manager.get_filter("global_search")
        if text_filter and isinstance(text_filter, TextFilter):
            text_filter.set_target_columns(text_columns)
            self._logger.debug(f"Updated searchable columns: {len(text_columns)} columns available")

    def _register_standard_filters(self) -> None:
        """Register standard validation filters for common columns."""
        if not self._filter_panel:
            return

        df = self._data_store.get_entries()
        if df is None or df.empty:
            return

        # Common columns that should have validation filters
        standard_columns = [
            {"column": "player", "title": "Player"},
            {"column": "chest_name", "title": "Chest Name"},
            {"column": "chest_type", "title": "Chest Type"},
            {"column": "item_name", "title": "Item Name"},
            {"column": "item_type", "title": "Item Type"},
        ]

        # Check for validation_errors column
        if "validation_errors" in df.columns:
            standard_columns.append({"column": "validation_errors", "title": "Validation Errors"})

        # Register each standard filter
        for col_info in standard_columns:
            column = col_info["column"]
            title = col_info["title"]

            if column in df.columns:
                self.register_validation_filter(column, title)

        # Check for date columns
        date_columns = []
        for column in df.columns:
            if "date" in column.lower() or "time" in column.lower():
                # Check if it's a date column
                try:
                    if pd.api.types.is_datetime64_any_dtype(df[column]):
                        date_columns.append(
                            {"column": column, "title": column.replace("_", " ").title()}
                        )
                except:
                    continue

        # Register date filters
        for col_info in date_columns:
            column = col_info["column"]
            title = col_info["title"]
            self.register_date_filter(column, title)

    def _update_filter_values(self) -> None:
        """Update validation filter values based on the current data."""
        if not self._filter_panel:
            return

        df = self._data_store.get_entries()
        if df is None or df.empty:
            return

        # Process each column for unique values
        for column in df.columns:
            # Skip non-string columns
            if df[column].dtype != "object":
                continue

            try:
                # Get unique values - handle both string and non-string types
                unique_values_array = df[column].dropna().unique()

                # Convert unhashable types to strings if needed
                unique_values = set()
                for val in unique_values_array:
                    if isinstance(val, (list, dict, set)):
                        # Special handling for lists (like validation_errors)
                        if isinstance(val, list):
                            self._process_validation_errors_column(val, unique_values)
                        else:
                            # Convert complex types to string representation
                            unique_values.add(str(val))
                    else:
                        unique_values.add(val)

                # If we have a filter for this column, update it
                filter_id = f"{column}_filter"
                if self._filter_panel and filter_id in self._filter_panel.get_dropdown_filters():
                    self._filter_panel.update_filter_values(filter_id, sorted(unique_values))

                # Store for future reference
                self._unique_values[column] = unique_values
            except Exception as e:
                self._logger.error(f"Error processing column {column}: {e}")

    def _process_validation_errors_column(
        self, error_list: List[Any], unique_values: Set[str]
    ) -> None:
        """
        Process validation errors column to extract unique error types.

        Args:
            error_list: List of validation errors
            unique_values: Set to add unique values to
        """
        for item in error_list:
            # Extract error type
            if isinstance(item, dict) and "type" in item:
                unique_values.add(item["type"])
            elif isinstance(item, str):
                unique_values.add(item)
            else:
                unique_values.add(str(item))

        # Add special "<Has Items>" entry if there are any errors
        if error_list and len(error_list) > 0:
            unique_values.add("<Has Items>")

    def register_validation_filter(
        self, column_name: str, display_name: Optional[str] = None
    ) -> None:
        """
        Register a validation filter for a column.

        Args:
            column_name: Name of the column to filter
            display_name: Optional display name, defaults to column name
        """
        if not self._filter_panel:
            return

        filter_id = f"{column_name}_filter"
        title = display_name if display_name else column_name.replace("_", " ").title()

        # Check if filter already exists
        if self._filter_manager.get_filter(filter_id):
            self._logger.debug(f"Filter {filter_id} already registered")
            return

        # Create filter object
        filter_obj = ValidationListFilter(filter_id, title, column_name)

        # Add to filter panel
        self._filter_panel.add_validation_filter(filter_id, filter_obj, title)
        self._logger.debug(f"Registered validation filter for column {column_name}")

        # Update with current values
        self._update_filter_values()

        # Load filter state if available
        if self._config_manager:
            filter_obj.load_state(self._config_manager)
            self._logger.debug(f"Loaded state for filter {filter_id}")

    def register_date_filter(self, column_name: str, display_name: Optional[str] = None) -> None:
        """
        Register a date filter for a column.

        Args:
            column_name: Name of the column to filter
            display_name: Optional display name, defaults to column name
        """
        if not self._filter_panel:
            return

        filter_id = f"{column_name}_date_filter"
        title = display_name if display_name else column_name.replace("_", " ").title()

        # Check if filter already exists
        if self._filter_manager.get_filter(filter_id):
            self._logger.debug(f"Filter {filter_id} already registered")
            return

        # Create filter object
        filter_obj = DateFilter(filter_id, title, column_name)

        # Add to filter panel
        self._filter_panel.add_date_filter(filter_id, filter_obj, title)
        self._logger.debug(f"Registered date filter for column {column_name}")

        # Load filter state if available
        if self._config_manager:
            filter_obj.load_state(self._config_manager)
            self._logger.debug(f"Loaded state for filter {filter_id}")

    def apply_filters(self) -> None:
        """Apply all current filters to the data."""
        self._on_filter_applied()

    def save_filter_state(self) -> None:
        """Save the current filter state to configuration."""
        if self._config_manager and self._filter_panel:
            self._filter_panel.save_filter_state(self._config_manager)
            self._logger.debug("Filter state saved")

    def load_filter_state(self) -> None:
        """Load filter state from configuration."""
        if self._config_manager and self._filter_panel:
            self._filter_panel.load_filter_state(self._config_manager)
            self._logger.debug("Filter state loaded")

    def get_active_filter_count(self) -> int:
        """
        Get the number of active filters.

        Returns:
            Number of active filters
        """
        return self._filter_manager.get_active_filter_count()

    def clear_all_filters(self) -> None:
        """Clear all filters."""
        if self._filter_panel:
            self._filter_panel.clear_all_filters()
            self._logger.debug("All filters cleared")
