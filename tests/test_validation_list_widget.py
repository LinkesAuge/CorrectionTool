import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.ui.validation_list_widget import ValidationListWidget
from src.models.validation_list import ValidationList
from src.services.config_manager import ConfigManager


@pytest.fixture
def config_manager():
    """Create a config manager for testing."""
    return ConfigManager(config_file="test_config.ini")


@pytest.fixture
def validation_list_widget(config_manager):
    """Create a validation list widget for testing."""
    widget = ValidationListWidget(
        list_type="player",
        validation_list=None,
        config_manager=config_manager,
    )
    return widget


def test_validation_list_widget_init(validation_list_widget):
    """Test that ValidationListWidget initializes correctly."""
    assert validation_list_widget is not None
    assert validation_list_widget._list_type == "player"
    assert validation_list_widget._list is None
    assert validation_list_widget._config_manager is not None


def test_validation_list_widget_populate(validation_list_widget):
    """Test that ValidationListWidget populates correctly."""
    test_list = ValidationList(name="player")
    test_list.items = ["Player1", "Player2", "Player3"]
    validation_list_widget._list = test_list
    validation_list_widget.populate()

    # Check that the model was populated
    assert validation_list_widget._model.rowCount() == 3
    assert validation_list_widget._model.data(
        validation_list_widget._model.index(0, 0)
    ) == "Player1"


def test_validation_list_widget_filter(validation_list_widget):
    """Test that ValidationListWidget filters correctly."""
    test_list = ValidationList(name="player")
    test_list.items = ["Player1", "Player2", "Player3"]
    validation_list_widget._list = test_list
    validation_list_widget.populate()

    # Filter for Player1
    validation_list_widget._search_input.setText("Player1")

    # Check that only Player1 is shown
    assert validation_list_widget._filtered_model.rowCount() == 1
    assert validation_list_widget._filtered_model.data(
        validation_list_widget._filtered_model.index(0, 0)
    ) == "Player1"


def test_validation_list_widget_set_validation_list(validation_list_widget):
    """Test that ValidationListWidget has a set_validation_list method that works properly."""
    # Create a test ValidationList
    test_list = ValidationList(name="player")
    test_list.items = ["Player1", "Player2", "Player3"]

    # Check that the method exists
    assert hasattr(validation_list_widget, "set_validation_list")

    # Use the method
    validation_list_widget.set_validation_list(test_list)

    # Verify the list was set
    model = validation_list_widget.model()
    assert model.rowCount() == 3


def test_validation_list_widget_set_list(validation_list_widget):
    """Test that ValidationListWidget has a set_list method that works properly as an alias for set_validation_list."""
    # Create a test ValidationList
    test_list = ValidationList(name="player")
    test_list.items = ["Player1", "Player2", "Player3"]

    # Check that both methods exist
    assert hasattr(validation_list_widget, "set_list")
    assert hasattr(validation_list_widget, "set_validation_list")

    # Spy on the set_validation_list method to verify it gets called
    original_method = validation_list_widget.set_validation_list
    called_with = None
    
    def spy_method(val_list):
        nonlocal called_with
        called_with = val_list
        return original_method(val_list)
    
    validation_list_widget.set_validation_list = spy_method
    
    # Use the set_list method
    result = validation_list_widget.set_list(test_list)

    # Verify set_list called set_validation_list with the same argument
    assert called_with is test_list
    
    # Verify method returns True
    assert result is True

    # Verify the list was set
    model = validation_list_widget._filtered_model
    assert model.rowCount() == 3
    assert model.data(model.index(0, 0)) == "Player1"
    assert model.data(model.index(1, 0)) == "Player2"
    assert model.data(model.index(2, 0)) == "Player3"

    # Verify the actual list object was stored
    assert validation_list_widget._list is test_list
    
    # Test with a different list to make sure updates work properly
    new_test_list = ValidationList(name="updated")
    new_test_list.items = ["Item1", "Item2", "Item3", "Item4"]
    
    result = validation_list_widget.set_list(new_test_list)
    assert result is True
    
    # Verify the list was updated
    model = validation_list_widget._filtered_model
    assert model.rowCount() == 4
    assert validation_list_widget._list is new_test_list


def test_validation_list_widget_get_items(validation_list_widget):
    """Test that ValidationListWidget can return items."""
    # Set up some test items
    test_list = ValidationList(name="player")
    test_list.items = ["Player1", "Player2", "Player3"]
    validation_list_widget.set_list(test_list)

    # Check if get_items method exists and works
    assert hasattr(validation_list_widget, "get_items")
    items = validation_list_widget.get_items()
    assert len(items) == 3
    assert "Player1" in items
    assert "Player2" in items
    assert "Player3" in items
