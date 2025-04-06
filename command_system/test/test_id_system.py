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
    SimpleIDRegistry, get_simple_id_registry
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
    
    def test_container_hierarchy_basics(self):
        """
        Test basic container-widget relationships.
        
        Verifies that widgets can be placed in containers and that the container
        hierarchy is correctly maintained and can be queried.
        """
        # Create container and widgets
        container = MockContainer("MainWindow")
        widget1 = MockWidget("Button1")
        widget2 = MockWidget("Button2")
        
        # Register components
        container_id = self.registry.register(container, "w")  # Window container
        widget1_id = self.registry.register(widget1, "pb", None, container_id, "0")  # At root location
        widget2_id = self.registry.register(widget2, "pb", None, container_id, "1")  # At location 1
        
        # Verify container relationships
        assert parse_widget_id(widget1_id)['container_unique_id'] == get_unique_id_from_id(container_id)
        assert parse_widget_id(widget2_id)['container_unique_id'] == get_unique_id_from_id(container_id)
        
        # Get widgets in container directly using full ID
        container_widgets = self.registry.get_container_widgets(container_id)
        assert len(container_widgets) == 2
        assert widget1_id in container_widgets
        assert widget2_id in container_widgets
        
        # Verify widgets by container and location
        widgets_at_location1 = self.registry.get_container_widgets_at_location(container_id, "1")
        assert len(widgets_at_location1) == 1
        assert widget2_id in widgets_at_location1
    
    def test_nested_container_hierarchy(self):
        """
        Test nested container hierarchy with deep nesting.
        
        Verifies that containers can be nested to arbitrary depth and that
        location paths are correctly maintained.
        """
        # Create a deep container hierarchy
        main_container = MockContainer("MainApp")
        tab_container = MockContainer("TabContainer")
        dock_container = MockContainer("DockContainer")
        
        # Register components with hierarchy
        main_id = self.registry.register(main_container, "w")  # Window container
        
        # Create a tab container within the main container
        tab_id = self.registry.register(tab_container, "t", None, main_id, "0")
        
        # Create a dock container within the tab container
        dock_id = self.registry.register(dock_container, "d", None, tab_id, "0/1")
        
        # Create widgets at different levels
        button1 = MockWidget("Button1")
        button2 = MockWidget("Button2")
        button3 = MockWidget("Button3")
        
        button1_id = self.registry.register(button1, "pb", None, main_id, "1")
        button2_id = self.registry.register(button2, "pb", None, tab_id, "0/2")
        button3_id = self.registry.register(button3, "pb", None, dock_id, "0/1/3")
        
        # Verify container relationships by parsing
        button1_components = parse_widget_id(button1_id)
        tab_components = parse_widget_id(tab_id)
        dock_components = parse_widget_id(dock_id)
        
        assert button1_components['container_unique_id'] == get_unique_id_from_id(main_id)
        assert tab_components['container_unique_id'] == get_unique_id_from_id(main_id)
        assert dock_components['container_unique_id'] == get_unique_id_from_id(tab_id)
        
        # Verify widget locations have the correct prefix
        assert tab_components['container_location'] == "0"
        assert dock_components['container_location'] == "0/1"
        assert parse_widget_id(button3_id)['container_location'] == "0/1/3"
        
        # Verify that widgets are found at the correct containers
        main_widgets = self.registry.get_container_widgets(main_id)
        tab_widgets = self.registry.get_container_widgets(tab_id)
        dock_widgets = self.registry.get_container_widgets(dock_id)
        
        assert len(main_widgets) == 2  # tab container and button1
        assert len(tab_widgets) == 2   # dock container and button2
        assert len(dock_widgets) == 1  # button3
        
        assert tab_id in main_widgets
        assert button1_id in main_widgets
        assert dock_id in tab_widgets
        assert button2_id in tab_widgets
        assert button3_id in dock_widgets
    
    def test_container_locations_map(self):
        """
        Test the container locations map functionality.
        
        Verifies that the system correctly maintains maps of subcontainer
        locations and can retrieve widgets at specific locations.
        """
        # Create a container with subcontainers
        main_container = MockContainer("MainWindow")
        tab1_container = MockContainer("Tab1")
        tab2_container = MockContainer("Tab2")
        
        # Register components
        main_id = self.registry.register(main_container, "w")  # Window container
        
        tab1_id = self.registry.register(tab1_container, "t", None, main_id, "0")
        tab2_id = self.registry.register(tab2_container, "t", None, main_id, "1")
        
        # Set up location maps
        locations_map = {
            "0": tab1_id,
            "1": tab2_id
        }
        self.registry.set_locations_map(main_id, locations_map)
        
        # Get and verify location maps
        main_locations = self.registry.get_locations_map(main_id)
        assert main_locations == locations_map
    
    #MARK: - Location Management Tests
    
    def test_location_id_generation(self):
        """
        Test location ID generation.
        
        Verifies that each container location has its own generator and
        produces unique widget location IDs.
        """
        # Create containers
        container1 = MockContainer("Container1")
        container2 = MockContainer("Container2")
        
        # Register containers
        container1_id = self.registry.register(container1, "d")  # Dock container
        container2_id = self.registry.register(container2, "d")  # Dock container
        
        # Create widgets in each container at the same location path
        button1 = MockWidget("Button1")
        button2 = MockWidget("Button2")
        button3 = MockWidget("Button3")
        button4 = MockWidget("Button4")
        
        # Register widgets without specifying widget_location_id to have them generated
        button1_id = self.registry.register(button1, "pb", None, container1_id, "0")
        button2_id = self.registry.register(button2, "pb", None, container1_id, "0")
        button3_id = self.registry.register(button3, "pb", None, container2_id, "0")
        button4_id = self.registry.register(button4, "pb", None, container2_id, "0")
        
        # Parse widget IDs to extract location components
        button1_components = parse_widget_id(button1_id)
        button2_components = parse_widget_id(button2_id)
        button3_components = parse_widget_id(button3_id)
        button4_components = parse_widget_id(button4_id)
        
        # Verify locations were generated and are unique within each container
        assert button1_components['widget_location_id'] != button2_components['widget_location_id']
        assert button3_components['widget_location_id'] != button4_components['widget_location_id']
        
        # Each container should have its own sequence starting from 1
        # First widgets in each container should have ID "1"
        assert button1_components['widget_location_id'] == "1"
        assert button3_components['widget_location_id'] == "1"
        
        # Second widgets should have ID "2"
        assert button2_components['widget_location_id'] == "2"
        assert button4_components['widget_location_id'] == "2"
    
    def test_location_id_collision_handling(self):
        """
        Test handling of location ID collisions.
        
        Verifies that when registering a widget with a location ID that already
        exists, the system finds the next available ID.
        """
        # Create a container
        container = MockContainer("Container")
        container_id = self.registry.register(container, "d")  # Dock container
        
        # Create widgets
        button1 = MockWidget("Button1")
        button2 = MockWidget("Button2")
        button3 = MockWidget("Button3")
        
        # Register first widget with specific location ID
        button1_id = self.registry.register(button1, "pb", None, container_id, "custom_loc")
        
        # Try to register second widget with the same location ID - it should get incremented
        button2_id = self.registry.register(button2, "pb", None, container_id, "custom_loc")
        
        # Parse components to check location IDs
        button1_components = parse_widget_id(button1_id)
        button2_components = parse_widget_id(button2_id)
        
        # The system should have assigned a different location ID
        assert button2_components['widget_location_id'] != button1_components['widget_location_id']
        assert button2_components['widget_location_id'] == "custom_loc1"
        
        # Try registering a third widget with a numeric ID
        button3_id = self.registry.register(button3, "pb", None, container_id, "5")
        
        # Register another widget with same numeric ID
        button4 = MockWidget("Button4")
        button4_id = self.registry.register(button4, "pb", None, container_id, "5")
        
        # Parse components to check location IDs
        button3_components = parse_widget_id(button3_id)
        button4_components = parse_widget_id(button4_id)
        
        # Numeric IDs should be properly incremented
        assert button3_components['widget_location_id'] == "5"
        assert button4_components['widget_location_id'] == "6"
    
    def test_update_widget_location(self):
        """
        Test updating a widget's location.
        
        Verifies that a widget can be moved to a different location within
        its container and that its ID is updated accordingly.
        """
        # Create a container and a widget
        container = MockContainer("Container")
        button = MockWidget("Button")
        
        # Register the container and widget
        container_id = self.registry.register(container, "d")  # Dock container
        button_id = self.registry.register(button, "pb", None, container_id, "0")
        
        # Get the original location components
        button_components = parse_widget_id(button_id)
        original_widget_location_id = button_components['widget_location_id']
        
        # Update the widget location to a new widget_location_id
        new_widget_location_id = "new_location"
        updated_id = self.registry.update_location(button_id, new_widget_location_id)
        
        # Verify ID changed
        assert updated_id != button_id
        
        # Get the updated location components
        updated_components = parse_widget_id(updated_id)
        
        # Verify only the widget_location_id changed
        assert updated_components['type_code'] == button_components['type_code']
        assert updated_components['unique_id'] == button_components['unique_id']
        assert updated_components['container_unique_id'] == button_components['container_unique_id']
        assert updated_components['widget_location_id'] == new_widget_location_id
        
        # Verify the widget can be retrieved with the new ID
        assert self.registry.get_widget(updated_id) == button
        
        # Verify the ID change was tracked
        assert (button_id, updated_id) in self.id_changes
        
        # Try updating with a full location (container_location-widget_location_id)
        new_full_location = "new_container_loc-widget_loc_xyz"
        updated_id2 = self.registry.update_location(updated_id, new_full_location)
        
        # Verify both parts changed
        updated_components2 = parse_widget_id(updated_id2)
        assert updated_components2['container_location'] == "new_container_loc"
        assert updated_components2['widget_location_id'] == "widget_loc_xyz"

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
    
    def test_update_container_id(self):
        """
        Test updating a widget's container.
        
        Verifies that a widget can be moved to a different container and
        that its ID is updated accordingly.
        """
        # Create components
        container1 = MockContainer("Container1")
        container2 = MockContainer("Container2")
        button = MockWidget("Button")
        
        # Register components
        container1_id = self.registry.register(container1, "d")
        container2_id = self.registry.register(container2, "d")
        
        # Register button in container1
        button_id = self.registry.register(button, "pb", None, container1_id, "0")
        
        # Verify initial container
        button_components = parse_widget_id(button_id)
        assert button_components['container_unique_id'] == get_unique_id_from_id(container1_id)
        
        # Update container using full container ID
        updated_id = self.registry.update_container(button_id, container2_id)
        
        # Verify the ID changed
        assert updated_id != button_id
        
        # Verify new container reference
        updated_components = parse_widget_id(updated_id)
        assert updated_components['container_unique_id'] == get_unique_id_from_id(container2_id)
        
        # Verify the button is in container2's widget list
        container2_widgets = self.registry.get_container_widgets(container2_id)
        assert updated_id in container2_widgets
        
        # Verify the button is not in container1's widget list anymore
        container1_widgets = self.registry.get_container_widgets(container1_id)
        assert updated_id not in container1_widgets
        assert button_id not in container1_widgets
    
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
        
        widget1_id = self.registry.register(widget1, "pb", None, container_id, "0")
        widget2_id = self.registry.register(widget2, "pb", None, container_id, "1")
        
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
        widget_id = self.registry.register(widget, "pb", None, container_id, "0")
        
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