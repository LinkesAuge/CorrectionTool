# Dependency Injection Guide

This document provides guidance on how to properly use the dependency injection system in the application.

## Core Principles

1. **Interface-Based Access**: Always access services through their interfaces, not concrete implementations
2. **Singleton Services**: Core services are singletons, managed by ServiceFactory
3. **ServiceFactory as Registry**: All services are registered with and accessed through ServiceFactory
4. **Helper Functions**: Use the helper functions in `src.services` for cleaner access to services

## Accessing Services

### Preferred Method: Helper Functions

The simplest and most readable way to access services is through the helper functions:

```python
from src.services import get_data_store, get_file_service

# Get services by type
data_store = get_data_store()
file_service = get_file_service()

# Use services
entries = data_store.get_entries()
file_service.load_file('path/to/file.txt')
```

### Alternative: Generic Service Resolution

For more flexibility or when working with custom services, use the generic `get_service` function:

```python
from src.services import get_service
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService

# Get services by interface
data_store = get_service(IDataStore)
file_service = get_service(IFileService)
```

### Direct ServiceFactory Access (Not Recommended for Regular Use)

While possible, direct ServiceFactory access should generally be avoided except in bootstrapping code:

```python
from src.services.service_factory import ServiceFactory
from src.interfaces.i_data_store import IDataStore

# Get ServiceFactory singleton
factory = ServiceFactory.get_instance()

# Get services by interface
data_store = factory.get_service(IDataStore)
```

## Dependency Injection in Classes

When creating a class that depends on services, use constructor injection:

```python
from src.interfaces.i_data_store import IDataStore
from src.interfaces.i_file_service import IFileService

class MyComponent:
    def __init__(self, data_store: IDataStore, file_service: IFileService):
        self._data_store = data_store
        self._file_service = file_service
        
    def do_something(self):
        entries = self._data_store.get_entries()
        # Process entries...
```

Then instantiate the class with resolved dependencies:

```python
from src.services import get_data_store, get_file_service
from my_module import MyComponent

# Resolve dependencies
data_store = get_data_store()
file_service = get_file_service()

# Create component with injected dependencies
my_component = MyComponent(data_store, file_service)
```

## Registering New Services

Custom services should be registered with the ServiceFactory during bootstrapping:

```python
from src.services.service_factory import ServiceFactory
from src.interfaces.i_custom_service import ICustomService
from src.services.custom_service import CustomService

# Create service instance
custom_service = CustomService()

# Register with factory
factory = ServiceFactory.get_instance()
factory.register_service(ICustomService, custom_service)
```

## Testing with Dependency Injection

For unit tests, create mock implementations of interfaces:

```python
import pytest
from unittest.mock import MagicMock
from src.interfaces.i_data_store import IDataStore

class MockDataStore(IDataStore):
    # Implement interface methods as needed
    def get_entries(self):
        return pd.DataFrame({"test": [1, 2, 3]})
    
    # Implement other methods...

@pytest.fixture
def mock_data_store():
    return MockDataStore()

def test_my_component(mock_data_store):
    # Create component with mock dependency
    my_component = MyComponent(mock_data_store)
    
    # Test component...
``` 