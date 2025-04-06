"""
Comprehensive test suite for the PySignalDecipher ID system.

This test suite thoroughly validates the functionality of the ID system,
focusing on its hierarchical design, relationship management, and event handling.
Each test case is designed to validate specific aspects of the system.
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
    WIDGET_TYPE_CODES, CONTAINER_TYPE_CODES, OBSERVABLE_TYPE_CODES, PROPERTY_TYPE_CODES,
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

class TestIDSystem:
    """Comprehensive test cases for the ID system."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset the global ID registry
        global _id_registry
        _id_registry = None
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
        
        self.registry.set_on_widget_unregister(on_widget_unregister)
        self.registry.set_on_observable_unregister(on_observable_unregister)
        self.registry.set_on_property_unregister(on_property_unregister)
        self.registry.set_on_id_changed(on_id_changed)

    #MARK: - Basic Widget Registration Tests
    
    def test_widget_registration_basics(self):
        """
        Test basic widget registration and retrieval.
        
        This test verifies that widgets can be registered with the ID system
        and that their IDs are correctly generated and can be retrieved.
        """
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
        """
        Test registering a widget with a custom unique ID.
        
        Verifies that the system accepts custom IDs and correctly uses them.
        """
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

    #MARK: - Container Hierarchy Tests
    
    def test_register_no_container_no_location(self):
        """
        Test registering a widget without a container or location.
        
        Expects:
        - Generate a unique ID
        - Use "0" as container_unique_id
        - Use "0" as container_location
        - Generate a new widget_location_id (usually "1" for first widget)
        """
        # Create widget
        button = MockWidget("Button")
        
        # Register without container or location
        button_id = self.registry.register(button, "pb")
        
        # Verify components
        components = parse_widget_id(button_id)
        assert components is not None
        assert components['type_code'] == "pb"
        assert components['container_unique_id'] == "0"
        assert components['container_location'] == "0"
        
        # Usually "1" for first widget at this location
        assert components['widget_location_id'] == "1"
    
    def test_register_with_container_no_location(self):
        """
        Test registering a widget with a container but no location.
        
        Expects:
        - Generate a unique ID
        - Use container's unique_id
        - Use container's location path
        - Generate a new widget_location_id
        """
        # Create container and widget
        container = MockContainer("MainContainer")
        button = MockWidget("Button")
        
        # Register container first
        container_id = self.registry.register(container, "d")  # Dock container
        
        # Register button with container but no location
        button_id = self.registry.register(button, "pb", None, container_id)
        
        # Verify components
        components = parse_widget_id(button_id)
        assert components is not None
        
        # Should use container's unique ID
        container_unique_id = get_unique_id_from_id(container_id)
        assert components['container_unique_id'] == container_unique_id
        
        # Container location should be the container's widget_location_id
        container_components = parse_widget_id(container_id)
        expected_location = container_components['container_location']+"/"+container_components['widget_location_id']
        assert components['container_location'] == expected_location
        
        # Should generate a new widget_location_id (usually "1" for first widget)
        assert components['widget_location_id'] == "1"
    
    def test_register_with_container_and_location(self):
        """
        Test registering a widget with a container and location.
        
        Expects:
        - Generate a unique ID
        - Use container's unique_id
        - Use container's location path
        - Use provided widget_location_id if not in use
        - Raise error if widget_location_id is already in use
        """
        # Create container and widgets
        container = MockContainer("MainContainer")
        button1 = MockWidget("Button1")
        button2 = MockWidget("Button2")
        
        # Register container first
        container_id = self.registry.register(container, "d")  # Dock container
        
        # Register button1 with container and specific location ID
        button1_id = self.registry.register(button1, "pb", None, container_id, "custom_loc")
        
        # Verify components
        button1_components = parse_widget_id(button1_id)
        assert button1_components is not None
        assert button1_components['widget_location_id'] == "custom_loc"
        
        # Try to register button2 with same location ID - should raise error
        with pytest.raises(IDRegistrationError):
            self.registry.register(button2, "pb", None, container_id, "custom_loc")
    
    def test_update_container(self):
        """
        Test updating a widget's container.
        
        Expects:
        - Update container_unique_id
        - Update container_location to new container's path
        - Keep the same widget_location_id if not in use in new container
        - Generate new widget_location_id if there's a collision
        """
        # Create containers and widget
        container1 = MockContainer("Container1")
        container2 = MockContainer("Container2")
        button = MockWidget("Button")
        
        # Register components
        container1_id = self.registry.register(container1, "d")
        container2_id = self.registry.register(container2, "d")
        button_id = self.registry.register(button, "pb", None, container1_id, "custom_loc")
        
        # Verify original container
        button_components = parse_widget_id(button_id)
        container1_unique_id = get_unique_id_from_id(container1_id)
        assert button_components['container_unique_id'] == container1_unique_id
        
        # Update container
        updated_id = self.registry.update_container(button_id, container2_id)
        
        # Verify updated container reference
        updated_components = parse_widget_id(updated_id)
        container2_unique_id = get_unique_id_from_id(container2_id)
        assert updated_components['container_unique_id'] == container2_unique_id
        
        # Widget location ID should be preserved
        assert updated_components['widget_location_id'] == "custom_loc"
        
        # Container location should be updated to match container2's path
        container2_components = parse_widget_id(container2_id)
        expected_location = container2_components['container_unique_id']+"/"+container2_components['widget_location_id']
        assert updated_components['container_location'] == expected_location
    
    def test_update_container_with_collision(self):
        """
        Test updating a widget's container when there's a location ID collision.
        
        Expects:
        - Generate a new widget_location_id if there's a collision
        """
        # Create containers and widgets
        container1 = MockContainer("Container1")
        container2 = MockContainer("Container2")
        button1 = MockWidget("Button1")
        button2 = MockWidget("Button2")
        
        # Register components
        container1_id = self.registry.register(container1, "d")
        container2_id = self.registry.register(container2, "d")
        button1_id = self.registry.register(button1, "pb", None, container1_id, "custom_loc")
        
        # Create a widget in container2 with the same location ID
        button2_id = self.registry.register(button2, "pb", None, container2_id, "custom_loc")
        
        # Update button1's container - should generate new location ID due to collision
        updated_id = self.registry.update_container(button1_id, container2_id)
        
        # Verify updated components
        updated_components = parse_widget_id(updated_id)
        
        # Widget location ID should be different (auto-generated)
        assert updated_components['widget_location_id'] != "custom_loc"
    
    def test_update_location(self):
        """
        Test updating a widget's location.
        
        Expects:
        - Only update widget_location_id
        - Raise error if new widget_location_id already exists in container
        """
        # Create container and widget
        container = MockContainer("Container")
        button1 = MockWidget("Button1")
        button2 = MockWidget("Button2")
        
        # Register components
        container_id = self.registry.register(container, "d")
        button1_id = self.registry.register(button1, "pb", None, container_id, "loc1")
        button2_id = self.registry.register(button2, "pb", None, container_id, "loc2")
        
        # Update button1's location to a new location ID
        new_location = "new_loc"
        updated_id = self.registry.update_location(button1_id, new_location)
        
        # Verify updated components
        updated_components = parse_widget_id(updated_id)
        
        # Only widget_location_id should change
        assert updated_components['widget_location_id'] == new_location
        assert updated_components['container_unique_id'] == parse_widget_id(button1_id)['container_unique_id']
        assert updated_components['container_location'] == parse_widget_id(button1_id)['container_location']
        
        # Try to update button1 to button2's location - should raise error
        with pytest.raises(IDRegistrationError):
            self.registry.update_location(updated_id, "loc2")
    
    def test_nested_container_hierarchy(self):
        """
        Test nested container hierarchy with the updated system.
        """
        # Create a deep container hierarchy
        main_container = MockContainer("MainApp")
        tab_container = MockContainer("TabContainer")
        dock_container = MockContainer("DockContainer")
        
        # Register components with hierarchy
        main_id = self.registry.register(main_container, "w")  # Window container
        
        # Create a tab container within the main container
        tab_id = self.registry.register(tab_container, "t", None, main_id)
        
        # Create a dock container within the tab container
        dock_id = self.registry.register(dock_container, "d", None, tab_id)
        
        # Create widgets at different levels
        button1 = MockWidget("Button1")
        button2 = MockWidget("Button2")
        button3 = MockWidget("Button3")
        
        button1_id = self.registry.register(button1, "pb", None, main_id)
        button2_id = self.registry.register(button2, "pb", None, tab_id)
        button3_id = self.registry.register(button3, "pb", None, dock_id)
        
        # Verify container path nesting
        main_components = parse_widget_id(main_id)
        tab_components = parse_widget_id(tab_id)
        dock_components = parse_widget_id(dock_id)
        button1_components = parse_widget_id(button1_id)
        button2_components = parse_widget_id(button2_id)
        button3_components = parse_widget_id(button3_id)
        
        # Main container is at root
        assert main_components['container_location'] == "0"
        
        # Tab container's container_location is main container's widget_location_id
        assert tab_components['container_location'] == main_components['container_location']+"/"+main_components['widget_location_id']
        
        # Dock container's container_location is tab container's widget_location_id
        assert dock_components['container_location'] == tab_components['container_location']+"/"+tab_components['widget_location_id']
        
        # Button1's container_location is the same as main_id's widget_location_id
        assert button1_components['container_location'] == main_components['container_location']+"/"+main_components['widget_location_id']
        
        # Button2's container_location is the same as tab_id's widget_location_id
        assert button2_components['container_location'] == tab_components['container_location']+"/"+tab_components['widget_location_id']
        
        # Button3's container_location is the same as dock_id's widget_location_id
        assert button3_components['container_location'] == dock_components['container_location']+"/"+dock_components['widget_location_id']

    #MARK: - Observable and Property Tests
    
    def test_observable_registration(self):
        """
        Test observable registration and retrieval.
        
        Verifies that observables can be registered with the ID system,
        their IDs are correctly generated, and they can be retrieved.
        """
        # Create observables
        observable1 = MockObservable("DataModel1")
        observable2 = MockObservable("DataModel2")
        
        # Register observables
        observable1_id = self.registry.register_observable(observable1, "o")
        observable2_id = self.registry.register_observable(observable2, "o")
        
        # Verify registration
        assert self.registry.get_id(observable1) == observable1_id
        assert self.registry.get_id(observable2) == observable2_id
        
        # Verify retrieval
        assert self.registry.get_observable(observable1_id) == observable1
        assert self.registry.get_observable(observable2_id) == observable2
        
        # Verify ID format
        observable1_components = parse_observable_id(observable1_id)
        assert observable1_components is not None
        assert observable1_components['type_code'] == "o"
    
    def test_observable_property_registration(self):
        """
        Test observable property registration and relationships.
        
        Verifies that properties can be registered with the system and
        associated with observables and controllers, and that these
        relationships can be queried.
        """
        # Create components
        observable = MockObservable("Person")
        property1 = MockObservableProperty("Name")
        property2 = MockObservableProperty("Age")
        controller = MockWidget("AgeSpinner")
        
        # Register components
        observable_id = self.registry.register_observable(observable, "o")
        controller_id = self.registry.register(controller, "sp")  # Spin box
        
        # Register properties with relationships using full IDs
        property1_id = self.registry.register_observable_property(
            property1, "op", None, "name", observable_id, None
        )
        
        property2_id = self.registry.register_observable_property(
            property2, "op", None, "age", observable_id, controller_id
        )
        
        # Verify ID format
        property1_components = parse_property_id(property1_id)
        assert property1_components is not None
        assert property1_components['type_code'] == "op"
        assert property1_components['observable_unique_id'] == get_unique_id_from_id(observable_id)
        assert property1_components['property_name'] == "name"
        assert property1_components['controller_id'] == "0"  # No controller
        
        property2_components = parse_property_id(property2_id)
        assert property2_components['controller_id'] == get_unique_id_from_id(controller_id)
        
        # Test getting properties by observable using the full observable ID
        observable_properties = self.registry.get_observable_properties(observable_id)
        assert len(observable_properties) == 2
        assert property1_id in observable_properties
        assert property2_id in observable_properties
        
        # Test getting properties by controller using the full controller ID
        controller_properties = self.registry.get_controller_properties(controller_id)
        assert len(controller_properties) == 1
        assert property2_id in controller_properties
    
    def test_update_property_references(self):
        """
        Test updating a property's references.
        
        Verifies that a property's observable, name, and controller references
        can be updated, and that these changes are reflected in its ID and
        in the system's relationship tracking.
        """
        # Create components
        observable1 = MockObservable("Person")
        observable2 = MockObservable("Employee")
        controller1 = MockWidget("AgeSpinner")
        controller2 = MockWidget("SalarySpinner")
        property_obj = MockObservableProperty("Property")
        
        # Register components
        observable1_id = self.registry.register_observable(observable1, "o")
        observable2_id = self.registry.register_observable(observable2, "o")
        controller1_id = self.registry.register(controller1, "sp")
        controller2_id = self.registry.register(controller2, "sp")
        
        # Register property with initial references using full IDs
        property_id = self.registry.register_observable_property(
            property_obj, "op", None, "age", observable1_id, controller1_id
        )
        
        # Update observable reference using full observable ID
        updated_id = self.registry.update_observable_reference(property_id, observable2_id)
        
        # Verify the ID changed
        assert updated_id != property_id
        
        # Verify the property is in observable2's property list
        observable2_properties = self.registry.get_observable_properties(observable2_id)
        assert updated_id in observable2_properties
        
        # Update property name
        property_id = updated_id
        updated_id = self.registry.update_property_name(property_id, "salary")
        
        # Verify the ID changed
        assert updated_id != property_id
        
        # Verify the property name was updated
        property_components = parse_property_id(updated_id)
        assert property_components['property_name'] == "salary"
        
        # Update controller reference using full controller ID
        property_id = updated_id
        updated_id = self.registry.update_controller_reference(property_id, controller2_id)
        
        # Verify the ID changed
        assert updated_id != property_id
        
        # Verify the property is in controller2's property list
        controller2_properties = self.registry.get_controller_properties(controller2_id)
        assert updated_id in controller2_properties
        
        # Verify the ID change was tracked
        assert (property_id, updated_id) in self.id_changes

    #MARK: - ID Update and Unregistration Tests
    
    def test_unregister_widget(self):
        """
        Test unregistering a widget.
        
        Verifies that a widget can be unregistered from the system and that
        all references to it are removed.
        """
        # Create a widget
        widget = MockWidget("TestWidget")
        
        # Register the widget
        widget_id = self.registry.register(widget, "pb")
        
        # Ensure the widget is registered
        assert self.registry.get_widget(widget_id) == widget
        assert self.registry.get_id(widget) == widget_id
        
        # Unregister the widget
        result = self.registry.unregister(widget_id)
        assert result
        
        # Verify the widget is no longer registered
        assert self.registry.get_widget(widget_id) is None
        assert self.registry.get_id(widget) is None
        
        # Verify unregister callback was called
        assert any(unregistered[0] == widget_id for unregistered in self.unregistered_widgets)
    
    def test_unregister_container_cascade(self):
        """
        Test unregistering a container with cascade effects.
        
        Verifies that when a container is unregistered, all its child widgets
        are also unregistered automatically.
        """
        # Create a container with widgets
        container = MockContainer("Container")
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        
        # Register the components
        container_id = self.registry.register(container, "d")
        
        widget1_id = self.registry.register(widget1, "pb", None, container_id)
        widget2_id = self.registry.register(widget2, "pb", None, container_id)
        
        # Verify initial registration
        assert self.registry.get_widget(container_id) == container
        assert self.registry.get_widget(widget1_id) == widget1
        assert self.registry.get_widget(widget2_id) == widget2
        
        # Unregister the container
        result = self.registry.unregister(container_id)
        assert result
        
        # Verify the container is unregistered
        assert self.registry.get_widget(container_id) is None
        assert self.registry.get_id(container) is None
        
        # Verify all child widgets are also unregistered (cascade effect)
        assert self.registry.get_widget(widget1_id) is None
        assert self.registry.get_widget(widget2_id) is None
        assert self.registry.get_id(widget1) is None
        assert self.registry.get_id(widget2) is None
        
        # Verify unregister callbacks were called for all components
        assert any(unregistered[0] == container_id for unregistered in self.unregistered_widgets)
        assert any(unregistered[0] == widget1_id for unregistered in self.unregistered_widgets)
        assert any(unregistered[0] == widget2_id for unregistered in self.unregistered_widgets)
    
    def test_unregister_observable_cascade(self):
        """
        Test unregistering an observable with cascade effects.
        
        Verifies that when an observable is unregistered, all its properties
        are also unregistered automatically.
        """
        # Create an observable with properties
        observable = MockObservable("Observable")
        property1 = MockObservableProperty("Property1")
        property2 = MockObservableProperty("Property2")
        
        # Register the components
        observable_id = self.registry.register_observable(observable, "o")
        
        property1_id = self.registry.register_observable_property(
            property1, "op", None, "prop1", observable_id)
        property2_id = self.registry.register_observable_property(
            property2, "op", None, "prop2", observable_id)
        
        # Verify initial registration
        assert self.registry.get_observable(observable_id) == observable
        assert self.registry.get_observable_property(property1_id) == property1
        assert self.registry.get_observable_property(property2_id) == property2
        
        # Unregister the observable
        result = self.registry.unregister(observable_id)
        assert result
        
        # Verify the observable is unregistered
        assert self.registry.get_observable(observable_id) is None
        assert self.registry.get_id(observable) is None
        
        # Verify all properties are also unregistered (cascade effect)
        assert self.registry.get_observable_property(property1_id) is None
        assert self.registry.get_observable_property(property2_id) is None
        assert self.registry.get_id(property1) is None
        assert self.registry.get_id(property2) is None
        
        # Verify unregister callbacks were called for all components
        assert any(unregistered[0] == observable_id for unregistered in self.unregistered_observables)
        assert any(unregistered[0] == property1_id for unregistered in self.unregistered_properties)
        assert any(unregistered[0] == property2_id for unregistered in self.unregistered_properties)
    
    def test_remove_references(self):
        """
        Test removing references without unregistering components.
        
        Verifies that container, observable, and controller references
        can be removed while keeping the components registered.
        """
        # Create components
        container = MockContainer("Container")
        observable = MockObservable("Observable")
        controller = MockWidget("Controller")
        widget = MockWidget("Widget")
        property_obj = MockObservableProperty("Property")
        
        # Register components
        container_id = self.registry.register(container, "d")
        observable_id = self.registry.register_observable(observable, "o")
        controller_id = self.registry.register(controller, "pb")
        
        # Register widget with container
        widget_id = self.registry.register(widget, "pb", None, container_id)
        
        # Register property with observable and controller
        property_id = self.registry.register_observable_property(
            property_obj, "op", None, "prop", observable_id, controller_id)
        
        # Verify initial references
        widget_components = parse_widget_id(widget_id)
        property_components = parse_property_id(property_id)
        
        assert widget_components['container_unique_id'] == get_unique_id_from_id(container_id)
        assert property_components['observable_unique_id'] == get_unique_id_from_id(observable_id)
        assert property_components['controller_id'] == get_unique_id_from_id(controller_id)
        
        # Remove container reference
        updated_widget_id = self.registry.remove_container_reference(widget_id)
        updated_widget_components = parse_widget_id(updated_widget_id)
        
        # Verify container reference is removed (set to "0")
        assert updated_widget_components['container_unique_id'] == "0"
        
        # Remove observable reference
        updated_property_id = self.registry.remove_observable_reference(property_id)
        updated_property_components = parse_property_id(updated_property_id)
        
        # Verify observable reference is removed (set to "0")
        assert updated_property_components['observable_unique_id'] == "0"
        
        # Remove controller reference
        final_property_id = self.registry.remove_controller_reference(updated_property_id)
        final_property_components = parse_property_id(final_property_id)
        
        # Verify controller reference is removed (set to "0")
        assert final_property_components['controller_id'] == "0"
        
        # Verify components are still registered
        assert self.registry.get_widget(updated_widget_id) == widget
        assert self.registry.get_observable_property(final_property_id) == property_obj
    
    #MARK: - ID Subscription Tests
    
    def test_id_subscription_basics(self):
        """
        Test basic ID subscription functionality.
        
        Verifies that clients can subscribe to ID changes and receive
        notifications when IDs change.
        """
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
    
    def test_id_subscription_multiple_subscribers(self):
        """
        Test multiple subscribers to the same ID.
        
        Verifies that multiple clients can subscribe to the same ID and
        all receive notifications when the ID changes.
        """
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
    
    def test_id_subscription_follows_id_change(self):
        """
        Test that subscriptions follow ID changes.
        
        Verifies that when a component's ID changes, subscriptions
        automatically follow the new ID.
        """
        # Create and register a widget
        widget = MockWidget("TestWidget")
        widget_id = self.registry.register(widget, "pb")
        
        # Track subscription notifications
        notifications = []
        
        def on_id_changed(old_id, new_id):
            notifications.append((old_id, new_id))
        
        # Subscribe to widget ID changes
        subscribe_to_id(widget_id, on_id_changed)
        
        # First ID change
        first_updated_id = self.registry.update_location(widget_id, "loc1")
        
        # Second ID change - subscription should automatically follow
        second_updated_id = self.registry.update_location(first_updated_id, "loc2")
        
        # Verify both changes were notified
        assert len(notifications) == 2
        assert notifications[0] == (widget_id, first_updated_id)
        assert notifications[1] == (first_updated_id, second_updated_id)
    
    def test_id_subscription_unsubscribe(self):
        """
        Test unsubscribing from ID changes.
        
        Verifies that clients can unsubscribe from ID changes and stop
        receiving notifications.
        """
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
    
    def test_id_subscription_unregister_cleanup(self):
        """
        Test that subscriptions are cleaned up when components are unregistered.
        
        Verifies that when a component is unregistered, all subscriptions
        to its ID are automatically removed.
        """
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
        
        # Unregister widget1
        self.registry.unregister(widget1_id)
        
        # Update widget2 - should still receive notifications
        updated_id = self.registry.update_location(widget2_id, "new_loc")
        
        # Verify widget2 subscription still works
        assert len(notifications2) == 1
        assert notifications2[0] == (widget2_id, updated_id)
        
        # Verify no notifications for widget1 (subscription should be cleaned up)
        assert len(notifications1) == 0
    
    def test_clear_subscriptions(self):
        """
        Test clearing all subscriptions.
        
        Verifies that all subscriptions can be cleared at once.
        """
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
    
    #MARK: - Simple ID Registry Tests
    
    def test_simple_id_registry(self):
        """
        Test the SimpleIDRegistry functionality.
        
        Verifies that the SimpleIDRegistry works correctly for basic
        name-to-ID mapping without the full hierarchy.
        """
        # Get a new SimpleIDRegistry instance
        simple_registry = get_simple_id_registry()
        
        # Clear it to ensure we start fresh
        simple_registry.clear()
        
        # Register some names with type codes
        button_id = simple_registry.register("main_button", "pb")
        slider_id = simple_registry.register("volume_slider", "sl")
        custom_id = simple_registry.register("special_widget", "cw", "cw:special")
        
        # Verify auto-generated IDs follow the pattern "type_code:number"
        assert button_id.startswith("pb:")
        assert slider_id.startswith("sl:")
        
        # Verify custom ID is used as provided
        assert custom_id == "cw:special"
        
        # Verify ID lookup by name
        assert simple_registry.get_id("main_button") == button_id
        assert simple_registry.get_id("volume_slider") == slider_id
        assert simple_registry.get_id("special_widget") == custom_id
        
        # Verify name lookup by ID
        assert simple_registry.get_name(button_id) == "main_button"
        assert simple_registry.get_name(slider_id) == "volume_slider"
        assert simple_registry.get_name(custom_id) == "special_widget"
        
        # Verify registration check
        assert simple_registry.is_registered("main_button")
        assert simple_registry.is_registered(button_id)
        assert simple_registry.is_registered("special_widget")
        assert simple_registry.is_registered("cw:special")
        assert not simple_registry.is_registered("unknown_name")
        
        # Unregister by name
        result = simple_registry.unregister("main_button")
        assert result
        assert not simple_registry.is_registered("main_button")
        assert not simple_registry.is_registered(button_id)
        
        # Unregister by ID
        result = simple_registry.unregister(slider_id)
        assert result
        assert not simple_registry.is_registered("volume_slider")
        assert not simple_registry.is_registered(slider_id)
        
        # Get all registrations
        assert len(simple_registry.get_all_ids()) == 1
        assert custom_id in simple_registry.get_all_ids()
        assert "special_widget" in simple_registry.get_all_names()
        
        # Clear registry
        simple_registry.clear()
        assert len(simple_registry.get_all_ids()) == 0


if __name__ == "__main__":
    # Run the tests directly if this script is executed
    pytest.main(["-v", __file__])