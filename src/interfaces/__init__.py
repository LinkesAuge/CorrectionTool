"""
interfaces package for the Chest Tracker Correction Tool.

This package contains interface classes that define contracts for various components,
helping to break circular dependencies and provide a clean architecture.

Usage:
    from src.interfaces import IDataStore, IServiceFactory, IValidationService
"""

# Events
from src.interfaces.events import EventType, EventHandler, EventData

# Data Store
from src.interfaces.i_data_store import IDataStore

# Services
from src.interfaces.i_file_service import IFileService
from src.interfaces.i_correction_service import ICorrectionService
from src.interfaces.i_validation_service import IValidationService
from src.interfaces.i_service_factory import IServiceFactory

# Config
from src.interfaces.i_config_manager import IConfigManager

# Filters
from src.interfaces.i_filter import IFilter, IFilterManager

# UI Adapters
from src.interfaces.ui_adapters import IUiAdapter, ITableAdapter, IComboBoxAdapter, IStatusAdapter

__all__ = [
    # Events
    "EventType",
    "EventHandler",
    "EventData",
    # Data Store
    "IDataStore",
    # Services
    "IFileService",
    "ICorrectionService",
    "IValidationService",
    "IServiceFactory",
    # Config
    "IConfigManager",
    # Filters
    "IFilter",
    "IFilterManager",
    # UI Adapters
    "IUiAdapter",
    "ITableAdapter",
    "IComboBoxAdapter",
    "IStatusAdapter",
]
