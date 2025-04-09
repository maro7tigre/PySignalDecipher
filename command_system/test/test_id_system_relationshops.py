"""
Relationship test suite for the PySignalDecipher ID system.

This test suite focuses on validating complex relationships in the ID system:
- Container hierarchies and nesting
- Cascading effects of container updates
- Observable-property relationships
- Controller-property relationships
- Relationship maintenance during updates
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


#MARK: - ID System Relationship Tests

class TestIDSystemRelationships:
    """Test cases focusing on relationship management in the ID system."""
    
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

    #MARK: - Container Hierarchy Tests
    
    def test_basic_container_relationships(self):
        """Test basic container-widget relationships."""
        # Create container and widgets
        container = MockContainer("Container")
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        
        # Register container and widgets
        container_id = self.registry.register(container, "d")
        widget1_id = self.registry.register(widget1, "pb", None, container_id)
        widget2_id = self.registry.register(widget2, "pb", None, container_id)
        
        # Verify container references
        widget1_components = parse_widget_id(widget1_id)
        widget2_components = parse_widget_id(widget2_id)
        
        assert widget1_components['container_unique_id'] == get_unique_id_from_id(container_id)
        assert widget2_components['container_unique_id'] == get_unique_id_from_id(container_id)
        
        # Verify container location formatting
        container_components = parse_widget_id(container_id)
        expected_location = container_components['container_location'] + "/" + container_components['widget_location_id']
        
        assert widget1_components['container_location'] == expected_location
        assert widget2_components['container_location'] == expected_location
        
        # Verify container query methods
        container_widgets = self.registry.get_container_widgets(container_id)
        assert len(container_widgets) == 2
        assert widget1_id in container_widgets
        assert widget2_id in container_widgets
    
    def test_nested_container_hierarchy(self):
        """Test deep container hierarchy with multiple levels."""
        # Create a deep container hierarchy
        main_container = MockContainer("MainApp")
        tab_container = MockContainer("TabContainer")
        dock_container = MockContainer("DockContainer")
        
        # Register components with hierarchy
        main_id = self.registry.register(main_container, "w")  # Window container
        tab_id = self.registry.register(tab_container, "t", None, main_id)
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
        
        # Tab container's container_location includes main container's widget_location_id
        assert tab_components['container_location'] == f"0/{main_components['widget_location_id']}"
        
        # Dock container's container_location includes both main and tab container paths
        assert dock_components['container_location'] == f"0/{main_components['widget_location_id']}/{tab_components['widget_location_id']}"
        
        # Widget container locations reflect their parent containers
        assert button1_components['container_location'] == f"0/{main_components['widget_location_id']}"
        assert button2_components['container_location'] == f"0/{main_components['widget_location_id']}/{tab_components['widget_location_id']}"
        assert button3_components['container_location'] == f"0/{main_components['widget_location_id']}/{tab_components['widget_location_id']}/{dock_components['widget_location_id']}"
    
    def test_container_location_update_propagation(self):
        """Test container location updates propagate to child widgets."""
        # Create a container hierarchy
        root_container = MockContainer("Root")
        sub_container = MockContainer("SubContainer")
        
        # Register containers
        root_id = self.registry.register(root_container, "w", "root")
        sub_id = self.registry.register(sub_container, "d", "sub", root_id)
        
        # Add widgets to the containers
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        
        widget1_id = self.registry.register(widget1, "pb", "w1", root_id)
        widget2_id = self.registry.register(widget2, "pb", "w2", sub_id)
        
        # Update root container's location
        updated_root_id = self.registry.update_location(root_id, "new_loc")
        
        # Get updated IDs
        updated_sub_id = self.registry.get_id(sub_container)
        updated_widget1_id = self.registry.get_id(widget1)
        updated_widget2_id = self.registry.get_id(widget2)
        
        # Verify container references remain unchanged
        updated_sub_components = parse_widget_id(updated_sub_id)
        updated_widget1_components = parse_widget_id(updated_widget1_id)
        updated_widget2_components = parse_widget_id(updated_widget2_id)
        
        assert updated_sub_components['container_unique_id'] == "root"
        assert updated_widget1_components['container_unique_id'] == "root"
        assert updated_widget2_components['container_unique_id'] == "sub"
        
        # Verify location paths are updated throughout the hierarchy
        updated_root_components = parse_widget_id(updated_root_id)
        
        # Root container's new location path
        expected_root_path = f"0/{updated_root_components['widget_location_id']}"
        
        # Root widgets should have updated location path
        assert updated_widget1_components['container_location'] == expected_root_path
        
        # Subcontainer should have updated location path
        assert updated_sub_components['container_location'] == expected_root_path
        
        # Subcontainer's widgets should have cascaded updated location path
        expected_sub_path = f"{expected_root_path}/{updated_sub_components['widget_location_id']}"
        assert updated_widget2_components['container_location'] == expected_sub_path
    
    def test_container_change_location_cleanup(self):
        """Test location generators are properly cleaned up when container changes."""
        # Create container and widget
        container = MockContainer("Container")
        widget = MockWidget("Widget")
        
        # Register components
        container_id = self.registry.register(container, "d", "cont")
        widget_id = self.registry.register(widget, "pb", "wid", container_id, "loc1")
        
        # Update widget location
        updated_id = self.registry.update_location(widget_id, "loc2")
        
        # Try to register a new widget with the old location ID (should succeed)
        new_widget = MockWidget("NewWidget")
        new_id = self.registry.register(new_widget, "pb", "new_wid", container_id, "loc1")
        
        # Verify the old location ID was freed and can be reused
        components = parse_widget_id(new_id)
        assert components['widget_location_id'] == "loc1"
    
    def test_container_unregister_cleanup(self):
        """Test location generators are properly cleaned when container is unregistered."""
        # Create and register a container
        container1 = MockContainer("Container1")
        container_id = self.registry.register(container1, "d", "cont")

        # Register widgets to populate location generator
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        widget3 = MockWidget("Widget3")
        
        widget1_id = self.registry.register(widget1, "pb", "w1", container_id)
        widget2_id = self.registry.register(widget2, "pb", "w2", container_id)
        widget3_id = self.registry.register(widget3, "pb", "w3", container_id)

        # Parse widget IDs to get their location IDs
        widget1_components = parse_widget_id(widget1_id)
        widget2_components = parse_widget_id(widget2_id)
        widget3_components = parse_widget_id(widget3_id)
        
        # Typically, auto-generated locations would be "1", "2", "3"
        location_ids = [
            widget1_components['widget_location_id'],
            widget2_components['widget_location_id'],
            widget3_components['widget_location_id']
        ]
        
        # Unregister the container (should clean up location generators)
        self.registry.unregister(container_id)
        
        # Create and register a new container with the same ID
        container2 = MockContainer("Container2")
        new_container_id = self.registry.register(container2, "d", "cont")

        # Register a new widget - should get the first location ID again
        new_widget = MockWidget("NewWidget")
        new_widget_id = self.registry.register(new_widget, "pb", "new_w", new_container_id)

        # Parse the new widget ID
        new_widget_components = parse_widget_id(new_widget_id)
        
        # The location ID should be "1" again, not "4"
        assert new_widget_components['widget_location_id'] == "1"
    
    def test_container_unregister_cascade(self):
        """Test container unregistration cascades to child widgets."""
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
    
    #MARK: - Observable-Property Relationship Tests
    
    def test_observable_property_relationships(self):
        """Test complex relationships between observables and properties."""
        # Create components
        observable1 = MockObservable("Person")
        observable2 = MockObservable("Employee")
        property1 = MockObservableProperty("Name")
        property2 = MockObservableProperty("Age")
        property3 = MockObservableProperty("Salary")
        
        # Register components
        observable1_id = self.registry.register_observable(observable1, "ob")
        observable2_id = self.registry.register_observable(observable2, "ob")
        
        # Register properties with relationships
        property1_id = self.registry.register_observable_property(
            property1, "op", None, "name", observable1_id
        )
        
        property2_id = self.registry.register_observable_property(
            property2, "op", None, "age", observable1_id
        )
        
        property3_id = self.registry.register_observable_property(
            property3, "op", None, "salary", observable2_id
        )
        
        # Test getting properties by observable
        observable1_properties = self.registry.get_observable_properties(observable1_id)
        assert len(observable1_properties) == 2
        assert property1_id in observable1_properties
        assert property2_id in observable1_properties
        
        observable2_properties = self.registry.get_observable_properties(observable2_id)
        assert len(observable2_properties) == 1
        assert property3_id in observable2_properties
        
        # Test getting properties by name
        observable1_name_properties = self.registry.get_property_ids_by_observable_id_and_property_name(
            observable1_id, "name"
        )
        assert len(observable1_name_properties) == 1
        assert property1_id in observable1_name_properties
    
    def test_observable_unregister_cascade(self):
        """Test observable unregistration cascades to properties."""
        # Create an observable with properties
        observable = MockObservable("Observable")
        property1 = MockObservableProperty("Property1")
        property2 = MockObservableProperty("Property2")
        
        # Register the components
        observable_id = self.registry.register_observable(observable, "ob")
        
        property1_id = self.registry.register_observable_property(
            property1, "op", None, "prop1", observable_id
        )
        
        property2_id = self.registry.register_observable_property(
            property2, "op", None, "prop2", observable_id
        )
        
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
    
    def test_update_property_references(self):
        """Test updating a property's references."""
        # Create components
        observable1 = MockObservable("Person")
        observable2 = MockObservable("Employee")
        controller1 = MockWidget("AgeSpinner")
        controller2 = MockWidget("SalarySpinner")
        property_obj = MockObservableProperty("Property")
        
        # Register components
        observable1_id = self.registry.register_observable(observable1, "ob")
        observable2_id = self.registry.register_observable(observable2, "ob")
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
        
        # Verify the property is not in observable1's property list
        observable1_properties = self.registry.get_observable_properties(observable1_id)
        assert updated_id not in observable1_properties
        
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
        
        # Verify the property is not in controller1's property list
        controller1_properties = self.registry.get_controller_properties(controller1_id)
        assert updated_id not in controller1_properties
    
    #MARK: - Property-Controller Relationship Tests
    
    def test_controller_property_relationships(self):
        """Test relationships between controllers and properties."""
        # Create components
        observable = MockObservable("DataModel")
        controller1 = MockWidget("Controller1")
        controller2 = MockWidget("Controller2")
        property1 = MockObservableProperty("Property1")
        property2 = MockObservableProperty("Property2")
        property3 = MockObservableProperty("Property3")
        
        # Register components
        observable_id = self.registry.register_observable(observable, "ob")
        controller1_id = self.registry.register(controller1, "pb")
        controller2_id = self.registry.register(controller2, "pb")
        
        # Register properties with controllers
        property1_id = self.registry.register_observable_property(
            property1, "op", None, "prop1", observable_id, controller1_id
        )
        
        property2_id = self.registry.register_observable_property(
            property2, "op", None, "prop2", observable_id, controller1_id
        )
        
        property3_id = self.registry.register_observable_property(
            property3, "op", None, "prop3", observable_id, controller2_id
        )
        
        # Test getting properties by controller
        controller1_properties = self.registry.get_controller_properties(controller1_id)
        assert len(controller1_properties) == 2
        assert property1_id in controller1_properties
        assert property2_id in controller1_properties
        
        controller2_properties = self.registry.get_controller_properties(controller2_id)
        assert len(controller2_properties) == 1
        assert property3_id in controller2_properties
        
        # Test getting controller from property
        assert self.registry.get_controller_id_from_property_id(property1_id) == get_unique_id_from_id(controller1_id)
        assert self.registry.get_controller_id_from_property_id(property3_id) == get_unique_id_from_id(controller2_id)
    
    def test_controller_unregister_effect_on_properties(self):
        """Test effect of controller unregistration on properties."""
        # Create components
        observable = MockObservable("Observable")
        controller = MockWidget("Controller")
        property_obj = MockObservableProperty("Property")
        
        # Register components
        observable_id = self.registry.register_observable(observable, "ob")
        controller_id = self.registry.register(controller, "pb")
        
        property_id = self.registry.register_observable_property(
            property_obj, "op", None, "prop", observable_id, controller_id
        )
        
        # Verify initial controller reference
        property_components = parse_property_id(property_id)
        assert property_components['controller_id'] == get_unique_id_from_id(controller_id)
        
        # Unregister the controller
        self.registry.unregister(controller_id)
        
        # The property should be unregistered (cascade)
        assert self.registry.get_observable_property(property_id) is None
        
        # Verify unregister callbacks were called
        assert any(unregistered[0] == controller_id for unregistered in self.unregistered_widgets)
        assert any(unregistered[0] == property_id for unregistered in self.unregistered_properties)
    
    def test_container_unregister_cascades_to_properties(self):
        """Test that unregistering a container cascades to controlled properties."""
        # Create a container with widgets that control properties
        container = MockContainer("Container")
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        observable = MockObservable("Observable")
        property1 = MockObservableProperty("Property1")
        property2 = MockObservableProperty("Property2")
        
        # Register components
        container_id = self.registry.register(container, "d", "cont")
        widget1_id = self.registry.register(widget1, "pb", "w1", container_id)
        widget2_id = self.registry.register(widget2, "pb", "w2", container_id)
        observable_id = self.registry.register_observable(observable, "ob", "obs")
        
        # Register properties controlled by the widgets
        property1_id = self.registry.register_observable_property(
            property1, "op", "prop1", "name", observable_id, widget1_id
        )
        property2_id = self.registry.register_observable_property(
            property2, "op", "prop2", "age", observable_id, widget2_id
        )
        
        # Verify initial registration
        assert self.registry.get_observable_property(property1_id) == property1
        assert self.registry.get_observable_property(property2_id) == property2

        # Unregister the container
        assert self.registry.unregister(container_id)
        
        # Verify widgets are unregistered
        assert self.registry.get_widget(widget1_id) is None
        assert self.registry.get_widget(widget2_id) is None
        
        # Verify properties are unregistered
        assert self.registry.get_observable_property(property1_id) is None
        assert self.registry.get_observable_property(property2_id) is None
        
        # Verify unregister callbacks were called for all components
        assert any(item[0] == container_id for item in self.unregistered_widgets)
        assert any(item[0] == widget1_id for item in self.unregistered_widgets)
        assert any(item[0] == widget2_id for item in self.unregistered_widgets)
        assert any(item[0] == property1_id for item in self.unregistered_properties)
        assert any(item[0] == property2_id for item in self.unregistered_properties)
    
    def test_remove_references(self):
        """Test removing references without unregistering components."""
        # Create components
        container = MockContainer("Container")
        observable = MockObservable("Observable")
        controller = MockWidget("Controller")
        widget = MockWidget("Widget")
        property_obj = MockObservableProperty("Property")
        
        # Register components
        container_id = self.registry.register(container, "d")
        observable_id = self.registry.register_observable(observable, "ob")
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


if __name__ == "__main__":
    # Run the tests directly if this script is executed
    pytest.main(["-v", __file__])