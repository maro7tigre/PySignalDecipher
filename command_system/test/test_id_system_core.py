"""
Core test suite for the PySignalDecipher ID system.

This test suite focuses on the basic functionality of the ID system:
- Component registration and retrieval
- ID format validation
- Basic ID parsing and generation
- Simple ID Registry
- ID Subscription basics
"""

import pytest
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from weakref import ref

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from command_system.id_system import (
    IDRegistry, get_id_registry,
    subscribe_to_id, unsubscribe_from_id, clear_subscriptions,
    SimpleIDRegistry, get_simple_id_registry,
    IDRegistrationError
)

from command_system.id_system.core.parser import (
    parse_widget_id, parse_observable_id, parse_property_id,
    get_unique_id_from_id, get_type_code_from_id
)

from command_system.id_system.types import (
    ID_SEPARATOR, LOCATION_SEPARATOR, PATH_SEPARATOR
)

#MARK: - Test Helper Classes

class MockWidget:
    """Mock widget for testing purposes."""
    def __init__(self, name: str):
        self.name = name
        
    def __repr__(self):
        return f"MockWidget({self.name})"

class MockContainer(MockWidget):
    """Mock container for testing purposes."""
    def __init__(self, name: str):
        super().__init__(name)
        
    def __repr__(self):
        return f"MockContainer({self.name})"

class MockObservable:
    """Mock observable for testing purposes."""
    def __init__(self, name: str):
        self.name = name
        
    def __repr__(self):
        return f"MockObservable({self.name})"

class MockObservableProperty:
    """Mock observable property for testing purposes."""
    def __init__(self, name: str):
        self.name = name
        
    def __repr__(self):
        return f"MockObservableProperty({self.name})"


#MARK: - Core ID System Tests

class TestIDSystemCore:
    """Test cases for core ID system functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset the global ID registry
        self.registry = get_id_registry()
        
        # Explicitly clear the registry to ensure a clean state
        self.registry.clear()
        
        # Set up callback tracking
        self.unregistered_widgets = []
        self.unregistered_observables = []
        self.unregistered_properties = []
        self.id_changes = []
        
        # Set up callbacks
        def on_widget_unregister(widget_id, widget):
            self.unregistered_widgets.append((widget_id, widget))
            
        def on_observable_unregister(observable_id, observable):
            self.unregistered_observables.append((observable_id, observable))
            
        def on_property_unregister(property_id, property_obj):
            self.unregistered_properties.append((property_id, property_obj))
            
        def on_id_changed(old_id, new_id):
            self.id_changes.append((old_id, new_id))
        
        self.registry.add_widget_unregister_callback(on_widget_unregister)
        self.registry.add_observable_unregister_callback(on_observable_unregister)
        self.registry.add_property_unregister_callback(on_property_unregister)
        self.registry.add_id_changed_callback(on_id_changed)

    #MARK: - Widget Registration Tests
    
    def test_widget_registration_basics(self):
        """Test basic widget registration and retrieval."""
        # Create widgets
        widget1 = MockWidget("Button1")
        widget2 = MockWidget("Slider1")
        
        # Register widgets with different type codes
        widget1_id = self.registry.register(widget1, "pb")  # Push button
        widget2_id = self.registry.register(widget2, "sl")  # Slider
        
        # Verify registration by checking ID lookup
        assert self.registry.get_id(widget1) == widget1_id
        assert self.registry.get_id(widget2) == widget2_id
        
        # Verify object retrieval by ID
        assert self.registry.get_widget(widget1_id) == widget1
        assert self.registry.get_widget(widget2_id) == widget2
        
        # Verify ID format and components
        widget1_components = parse_widget_id(widget1_id)
        assert widget1_components is not None
        assert widget1_components['type_code'] == "pb"
        assert widget1_components['container_unique_id'] == "0"  # Default is no container
        
        # Verify ID validation
        assert widget1_id.startswith("pb" + ID_SEPARATOR)
        assert widget2_id.startswith("sl" + ID_SEPARATOR)
    
    def test_custom_unique_id(self):
        """Test registering a widget with a custom unique ID."""
        # Create widget
        widget = MockWidget("CustomIDWidget")
        
        # Register with custom unique ID
        custom_id = "CustomUniqueID123"
        widget_id = self.registry.register(widget, "pb", custom_id)
        
        # Verify ID contains the custom unique ID
        assert get_unique_id_from_id(widget_id) == custom_id
        
        # Verify retrieval works with the custom ID
        assert self.registry.get_widget(widget_id) == widget
        
        # Register another widget to verify auto ID generation still works
        widget2 = MockWidget("RegularWidget")
        widget2_id = self.registry.register(widget2, "pb")
        
        # The auto-generated ID should be numeric, not based on the custom ID
        unique_id2 = get_unique_id_from_id(widget2_id)
        assert unique_id2 != "CustomUniqueID124"
        assert unique_id2.isalnum()
    
    def test_widget_id_parsing(self):
        """Test parsing widget IDs into their components."""
        # Create a widget with specific container and location
        container = MockContainer("Container")
        widget = MockWidget("Button")
        
        container_id = self.registry.register(container, "d", "cont1")
        widget_id = self.registry.register(widget, "pb", "wid1", container_id, "custom_loc")
        
        # Parse the widget ID
        components = parse_widget_id(widget_id)
        
        # Verify components
        assert components['type_code'] == "pb"
        assert components['unique_id'] == "wid1"
        assert components['container_unique_id'] == "cont1"
        assert components['widget_location_id'] == "custom_loc"
        
        # Get the container location path
        container_comp = parse_widget_id(container_id)
        expected_location = f"0/{container_comp['widget_location_id']}"
        assert components['container_location'] == expected_location
        
        # Test getting unique ID and type code
        assert get_unique_id_from_id(widget_id) == "wid1"
        assert get_type_code_from_id(widget_id) == "pb"

    #MARK: - Observable and Property Registration Tests
    
    def test_observable_registration(self):
        """Test observable registration and retrieval."""
        # Create observables
        observable1 = MockObservable("DataModel1")
        observable2 = MockObservable("DataModel2")
        
        # Register observables
        observable1_id = self.registry.register_observable(observable1, "ob")
        observable2_id = self.registry.register_observable(observable2, "ob")
        
        # Verify registration
        assert self.registry.get_id(observable1) == observable1_id
        assert self.registry.get_id(observable2) == observable2_id
        
        # Verify retrieval
        assert self.registry.get_observable(observable1_id) == observable1
        assert self.registry.get_observable(observable2_id) == observable2
        
        # Verify ID format
        observable1_components = parse_observable_id(observable1_id)
        assert observable1_components is not None
        assert observable1_components['type_code'] == "ob"
    
    def test_property_registration(self):
        """Test property registration with basic relationships."""
        # Create components
        observable = MockObservable("Person")
        property_obj = MockObservableProperty("Name")
        
        # Register components
        observable_id = self.registry.register_observable(observable, "ob")
        
        # Register property with observable relationship
        property_id = self.registry.register_observable_property(
            property_obj, "op", None, "name", observable_id, None
        )
        
        # Verify registration
        assert self.registry.get_id(property_obj) == property_id
        assert self.registry.get_observable_property(property_id) == property_obj
        
        # Verify ID format
        property_components = parse_property_id(property_id)
        assert property_components is not None
        assert property_components['type_code'] == "op"
        assert property_components['property_name'] == "name"
        assert property_components['observable_unique_id'] == get_unique_id_from_id(observable_id)
        assert property_components['controller_id'] == "0"  # No controller
        
        # Verify relationship query
        observable_properties = self.registry.get_observable_properties(observable_id)
        assert property_id in observable_properties
    
    def test_property_with_controller(self):
        """Test property registration with controller relationship."""
        # Create components
        observable = MockObservable("Person")
        property_obj = MockObservableProperty("Age")
        controller = MockWidget("AgeSpinner")
        
        # Register components
        observable_id = self.registry.register_observable(observable, "ob")
        controller_id = self.registry.register(controller, "sp")  # Spin box
        
        # Register property with controller relationship
        property_id = self.registry.register_observable_property(
            property_obj, "op", None, "age", observable_id, controller_id
        )
        
        # Verify property has controller reference
        property_components = parse_property_id(property_id)
        assert property_components['controller_id'] == get_unique_id_from_id(controller_id)
        
        # Verify controller relationship query
        controller_properties = self.registry.get_controller_properties(controller_id)
        assert property_id in controller_properties

    #MARK: - Unregistration Tests
    
    def test_widget_unregistration(self):
        """Test unregistering a widget."""
        # Create and register a widget
        widget = MockWidget("TestWidget")
        widget_id = self.registry.register(widget, "pb")
        
        # Verify registration
        assert self.registry.get_widget(widget_id) == widget
        
        # Unregister the widget
        result = self.registry.unregister(widget_id)
        assert result
        
        # Verify widget is no longer registered
        assert self.registry.get_widget(widget_id) is None
        assert self.registry.get_id(widget) is None
        
        # Verify unregister callback was called
        assert any(unregistered[0] == widget_id for unregistered in self.unregistered_widgets)
    
    def test_observable_unregistration(self):
        """Test unregistering an observable."""
        # Create and register an observable
        observable = MockObservable("TestObservable")
        observable_id = self.registry.register_observable(observable, "ob")
        
        # Verify registration
        assert self.registry.get_observable(observable_id) == observable
        
        # Unregister the observable
        result = self.registry.unregister(observable_id)
        assert result
        
        # Verify observable is no longer registered
        assert self.registry.get_observable(observable_id) is None
        assert self.registry.get_id(observable) is None
        
        # Verify unregister callback was called
        assert any(unregistered[0] == observable_id for unregistered in self.unregistered_observables)
    
    def test_property_unregistration(self):
        """Test unregistering a property."""
        # Create and register components
        observable = MockObservable("Person")
        property_obj = MockObservableProperty("Name")
        
        observable_id = self.registry.register_observable(observable, "ob")
        property_id = self.registry.register_observable_property(
            property_obj, "op", None, "name", observable_id
        )
        property2_id = self.registry.register_observable_property(
            property_obj, "op", None, "age", observable_id
        )
        
        # Verify registration
        assert self.registry.get_observable_property(property_id) == property_obj
        
        # Unregister the property
        result = self.registry.unregister(property_id)
        assert result
        
        # Verify property is no longer registered
        assert self.registry.get_observable_property(property_id) is None
        assert self.registry.get_id(property_obj) is None
        
        # Verify unregister callback was called
        assert any(unregistered[0] == property_id for unregistered in self.unregistered_properties)
        
        # Verify observable is still registered
        assert self.registry.get_observable(observable_id) == observable
        
        # Unregister the sercond property
        result = self.registry.unregister(property2_id)
        assert result
        
        # Verify observable is no longer registered
        assert self.registry.get_observable(observable_id) is None

    #MARK: - Simple ID Registry Tests
    
    def test_simple_id_registry(self):
        """Test SimpleIDRegistry for basic type-code based ID management."""
        # Get a new SimpleIDRegistry instance
        simple_registry = get_simple_id_registry()
        
        # Clear it to ensure we start fresh
        simple_registry.clear()
        
        # Register some IDs with type codes
        button_id = simple_registry.register("pb")
        slider_id = simple_registry.register("sl")
        custom_id = simple_registry.register("cw", "cw:special")
        
        # Verify auto-generated IDs follow the pattern "type_code:number"
        assert button_id.startswith("pb:")
        assert slider_id.startswith("sl:")
        
        # Verify custom ID is used as provided
        assert custom_id == "cw:special"
        
        # Verify registration check
        assert simple_registry.is_registered(button_id)
        assert simple_registry.is_registered(slider_id)
        assert simple_registry.is_registered(custom_id)
        assert not simple_registry.is_registered("unknown_id")
        
        # Unregister by ID
        result = simple_registry.unregister(button_id)
        assert result
        assert not simple_registry.is_registered(button_id)
        
        # Get all registrations
        assert len(simple_registry.get_all_ids()) == 2
        assert custom_id in simple_registry.get_all_ids()
        
        # Test ID collision handling with custom IDs
        collision_id = simple_registry.register("cw", "cw:special")
        assert collision_id == "cw:special_1"  # Should append _1 to avoid collision
        
        # Clear registry
        simple_registry.clear()
        assert len(simple_registry.get_all_ids()) == 0
    
    #MARK: - ID Subscription Tests
    
    def test_id_subscription_basics(self):
        """Test basic ID subscription functionality."""
        # Create and register a widget
        widget = MockWidget("TestWidget")
        widget_id = self.registry.register(widget, "pb")
        
        # Track subscription notifications
        notifications = []
        
        def on_id_changed(old_id, new_id):
            notifications.append((old_id, new_id))
        
        # Subscribe to widget ID changes
        result = subscribe_to_id(widget_id, on_id_changed)
        assert result
        
        # Update widget location to trigger ID change
        new_location = "new_loc"
        updated_id = self.registry.update_location(widget_id, new_location)
        
        # Verify notification was received
        assert len(notifications) == 1
        assert notifications[0] == (widget_id, updated_id)
    
    def test_id_subscription_unsubscribe(self):
        """Test unsubscribing from ID changes."""
        # Create and register a widget
        widget = MockWidget("TestWidget")
        widget_id = self.registry.register(widget, "pb")
        
        # Track subscription notifications
        notifications = []
        
        def on_id_changed(old_id, new_id):
            notifications.append((old_id, new_id))
        
        # Subscribe to widget ID changes
        subscribe_to_id(widget_id, on_id_changed)
        
        # First update - should receive notification
        first_updated_id = self.registry.update_location(widget_id, "loc1")
        assert len(notifications) == 1
        
        # Unsubscribe
        result = unsubscribe_from_id(first_updated_id, on_id_changed)
        assert result
        
        # Second update - should not receive notification
        self.registry.update_location(first_updated_id, "loc2")
        assert len(notifications) == 1  # Still only 1 notification
    
    def test_clear_subscriptions(self):
        """Test clearing all subscriptions."""
        # Create widgets
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        
        # Register widgets
        widget1_id = self.registry.register(widget1, "pb")
        widget2_id = self.registry.register(widget2, "pb")
        
        # Track subscription notifications
        notifications1 = []
        notifications2 = []
        
        def on_id_changed1(old_id, new_id):
            notifications1.append((old_id, new_id))
            
        def on_id_changed2(old_id, new_id):
            notifications2.append((old_id, new_id))
        
        # Subscribe to both widgets
        subscribe_to_id(widget1_id, on_id_changed1)
        subscribe_to_id(widget2_id, on_id_changed2)
        
        # Clear all subscriptions
        clear_subscriptions()
        
        # Update both widgets
        self.registry.update_location(widget1_id, "loc1")
        self.registry.update_location(widget2_id, "loc2")
        
        # Verify no notifications were received
        assert len(notifications1) == 0
        assert len(notifications2) == 0
        
    def test_multiple_subscriptions(self):
        """Test multiple subscribers to the same ID."""
        # Create and register a widget
        widget = MockWidget("TestWidget")
        widget_id = self.registry.register(widget, "pb")
        
        # Track notifications for two different subscribers
        notifications1 = []
        notifications2 = []
        
        def on_id_changed1(old_id, new_id):
            notifications1.append((old_id, new_id))
            
        def on_id_changed2(old_id, new_id):
            notifications2.append((old_id, new_id))
        
        # Subscribe both to widget ID changes
        subscribe_to_id(widget_id, on_id_changed1)
        subscribe_to_id(widget_id, on_id_changed2)
        
        # Update widget location to trigger ID change
        updated_id = self.registry.update_location(widget_id, "new_loc")
        
        # Verify both subscribers received notifications
        assert len(notifications1) == 1
        assert len(notifications2) == 1
        assert notifications1[0] == (widget_id, updated_id)
        assert notifications2[0] == (widget_id, updated_id)


if __name__ == "__main__":
    # Run the tests directly if this script is executed
    pytest.main(["-v", __file__])