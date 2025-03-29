"""
Comprehensive test suite for the ID system.

This tests the functionality of the ID system including widgets, containers,
observables, and observable properties from an end-user perspective.
"""
import pytest
import sys
import os
from typing import Dict, Any, List

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from command_system.id_system import (
    IDRegistry, get_id_registry, TypeCodes,
    extract_type_code, extract_unique_id, 
    extract_container_unique_id, extract_location,
    extract_observable_unique_id, extract_property_name,
    extract_controller_unique_id, is_widget_id,
    is_observable_id, is_observable_property_id
)

# Mock classes for testing
class MockWidget:
    def __init__(self, name: str):
        self.name = name
        
    def __repr__(self):
        return f"MockWidget({self.name})"

class MockContainer(MockWidget):
    def __init__(self, name: str):
        super().__init__(name)
        
    def __repr__(self):
        return f"MockContainer({self.name})"

class MockObservable:
    def __init__(self, name: str):
        self.name = name
        
    def __repr__(self):
        return f"MockObservable({self.name})"

class MockObservableProperty:
    def __init__(self, name: str):
        self.name = name
        
    def __repr__(self):
        return f"MockObservableProperty({self.name})"


class TestIDSystem:
    """Test cases for the ID system."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset the IDRegistry
        IDRegistry._instance = None
        self.registry = get_id_registry()
        
        # Set up callback tracking
        self.unregistered_widgets = []
        self.unregistered_observables = []
        self.unregistered_properties = []
        
        self.registry.set_on_widget_unregister(
            lambda widget_id: self.unregistered_widgets.append(widget_id)
        )
        self.registry.set_on_observable_unregister(
            lambda observable_id: self.unregistered_observables.append(observable_id)
        )
        self.registry.set_on_property_unregister(
            lambda property_id: self.unregistered_properties.append(property_id)
        )
    
    def test_widget_registration(self):
        """Test basic widget registration and retrieval."""
        # Create widgets
        widget1 = MockWidget("Button1")
        widget2 = MockWidget("Slider1")
        
        # Register widgets
        widget1_id = self.registry.register(widget1, TypeCodes.PUSH_BUTTON)
        widget2_id = self.registry.register(widget2, TypeCodes.SLIDER)
        
        # Verify registration
        assert self.registry.get_id(widget1) == widget1_id
        assert self.registry.get_id(widget2) == widget2_id
        
        # Verify retrieval
        assert self.registry.get_widget(widget1_id) == widget1
        assert self.registry.get_widget(widget2_id) == widget2
        
        # Verify ID format
        assert is_widget_id(widget1_id)
        assert extract_type_code(widget1_id) == TypeCodes.PUSH_BUTTON
        assert extract_container_unique_id(widget1_id) == "0"  # No container
        assert extract_location(widget1_id) == "0"  # No location
    
    def test_container_hierarchy(self):
        """Test container-widget relationships."""
        # Create container and widgets
        container = MockContainer("MainWindow")
        widget1 = MockWidget("Button1")
        widget2 = MockWidget("Button2")
        nested_container = MockContainer("ToolBar")
        nested_widget = MockWidget("SaveButton")
        
        # Register components
        container_id = self.registry.register(container, TypeCodes.WINDOW_CONTAINER)
        widget1_id = self.registry.register(widget1, TypeCodes.PUSH_BUTTON, None, container_id, "1")
        widget2_id = self.registry.register(widget2, TypeCodes.PUSH_BUTTON, None, container_id, "2")
        nested_container_id = self.registry.register(nested_container, TypeCodes.CUSTOM_CONTAINER, None, container_id, "3")
        nested_widget_id = self.registry.register(nested_widget, TypeCodes.PUSH_BUTTON, None, nested_container_id, "1")
        
        # Verify container relationships
        assert self.registry.get_container_id_from_widget_id(widget1_id) == container_id
        assert self.registry.get_container_id_from_widget_id(widget2_id) == container_id
        assert self.registry.get_container_id_from_widget_id(nested_container_id) == container_id
        assert self.registry.get_container_id_from_widget_id(nested_widget_id) == nested_container_id
        
        # Verify widget location
        assert extract_location(widget1_id) == "1"
        assert extract_location(widget2_id) == "2"
        
        # Test getting widgets by container
        container_widgets = self.registry.get_widget_ids_by_container_id(container_id)
        assert len(container_widgets) == 3
        assert widget1_id in container_widgets
        assert widget2_id in container_widgets
        assert nested_container_id in container_widgets
        
        # Test getting widgets by container and location
        location1_widgets = self.registry.get_widget_ids_by_container_id_and_location(container_id, "1")
        assert len(location1_widgets) == 1
        assert widget1_id in location1_widgets
        
        location3_widgets = self.registry.get_widget_ids_by_container_id_and_location(container_id, "3")
        assert len(location3_widgets) == 1
        assert nested_container_id in location3_widgets
        
        # Test nested container
        nested_widgets = self.registry.get_widget_ids_by_container_id(nested_container_id)
        assert len(nested_widgets) == 1
        assert nested_widget_id in nested_widgets
    
    def test_observable_registration(self):
        """Test observable registration and retrieval."""
        # Create observables
        observable1 = MockObservable("DataModel1")
        observable2 = MockObservable("DataModel2")
        
        # Register observables
        observable1_id = self.registry.register_observable(observable1, TypeCodes.OBSERVABLE)
        observable2_id = self.registry.register_observable(observable2, TypeCodes.OBSERVABLE)
        
        # Verify registration
        assert self.registry.get_id(observable1) == observable1_id
        assert self.registry.get_id(observable2) == observable2_id
        
        # Verify retrieval
        assert self.registry.get_observable(observable1_id) == observable1
        assert self.registry.get_observable(observable2_id) == observable2
        
        # Verify ID format
        assert is_observable_id(observable1_id)
        assert extract_type_code(observable1_id) == TypeCodes.OBSERVABLE
    
    def test_observable_property_registration(self):
        """Test observable property registration and relationships."""
        # Create components
        observable = MockObservable("Person")
        property1 = MockObservableProperty("Name")
        property2 = MockObservableProperty("Age")
        controller = MockWidget("AgeSpinner")
        
        # Register components
        observable_id = self.registry.register_observable(observable, TypeCodes.OBSERVABLE)
        controller_id = self.registry.register(controller, TypeCodes.SPIN_BOX)
        
        # Register properties with relationships
        property1_id = self.registry.register_observable_property(
            property1, TypeCodes.OBSERVABLE_PROPERTY,
            None, "name", observable_id, None
        )
        
        property2_id = self.registry.register_observable_property(
            property2, TypeCodes.OBSERVABLE_PROPERTY,
            None, "age", observable_id, controller_id
        )
        
        # Verify ID format
        assert is_observable_property_id(property1_id)
        assert extract_type_code(property1_id) == TypeCodes.OBSERVABLE_PROPERTY
        assert extract_observable_unique_id(property1_id) == extract_unique_id(observable_id)
        assert extract_property_name(property1_id) == "name"
        assert extract_controller_unique_id(property1_id) == "0"  # No controller
        
        assert extract_controller_unique_id(property2_id) == extract_unique_id(controller_id)
        
        # Test relationships
        assert self.registry.get_observable_id_from_property_id(property1_id) == observable_id
        assert self.registry.get_controller_id_from_property_id(property2_id) == controller_id
        
        # Test getting properties by observable
        observable_properties = self.registry.get_property_ids_by_observable_id(observable_id)
        assert len(observable_properties) == 2
        assert property1_id in observable_properties
        assert property2_id in observable_properties
        
        # Test getting properties by name
        name_properties = self.registry.get_property_ids_by_observable_id_and_property_name(observable_id, "name")
        assert len(name_properties) == 1
        assert property1_id in name_properties
        
        # Test getting properties by controller
        controller_properties = self.registry.get_property_ids_by_controller_id(controller_id)
        assert len(controller_properties) == 1
        assert property2_id in controller_properties
    
    def test_unique_id_operations(self):
        """Test unique ID extraction and full ID lookup."""
        # Create and register widgets
        widget = MockWidget("Button")
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON)
        
        # Extract unique ID
        unique_id = self.registry.get_unique_id_from_id(widget_id)
        
        # Lookup by unique ID
        assert self.registry.get_full_id_from_unique_id(unique_id) == widget_id
    
    def test_update_widget_container(self):
        """Test updating a widget's container."""
        # Create components
        container1 = MockContainer("Panel1")
        container2 = MockContainer("Panel2")
        widget = MockWidget("Button")
        
        # Register components
        container1_id = self.registry.register(container1, TypeCodes.CUSTOM_CONTAINER)
        container2_id = self.registry.register(container2, TypeCodes.CUSTOM_CONTAINER)
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON, None, container1_id, "1")
        
        # Verify initial container
        assert self.registry.get_container_id_from_widget_id(widget_id) == container1_id
        
        # Update container
        success = self.registry.update_container_id(widget_id, container2_id)
        assert success
        
        # Get updated widget ID
        updated_widget_id = self.registry.get_id(widget)
        
        # Verify new container
        assert self.registry.get_container_id_from_widget_id(updated_widget_id) == container2_id
        
        # Remove container reference
        updated_id = self.registry.remove_container_reference(updated_widget_id)
        final_widget_id = self.registry.get_id(widget)
        
        # Verify container removed
        assert self.registry.get_container_id_from_widget_id(final_widget_id) is None
    
    def test_update_widget_location(self):
        """Test updating a widget's location."""
        # Create components
        container = MockContainer("Panel")
        widget = MockWidget("Button")
        
        # Register components
        container_id = self.registry.register(container, TypeCodes.CUSTOM_CONTAINER)
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON, None, container_id, "1")
        
        # Verify initial location
        assert extract_location(widget_id) == "1"
        
        # Update location
        success = self.registry.update_location(widget_id, "2")
        assert success
        
        # Get updated widget ID
        updated_widget_id = self.registry.get_id(widget)
        
        # Verify new location
        assert extract_location(updated_widget_id) == "2"
    
    def test_update_observable_property_relationships(self):
        """Test updating observable property relationships."""
        # Create components
        observable1 = MockObservable("Model1")
        observable2 = MockObservable("Model2")
        controller1 = MockWidget("Spinner1")
        controller2 = MockWidget("Spinner2")
        property = MockObservableProperty("Counter")
        
        # Register components
        observable1_id = self.registry.register_observable(observable1, TypeCodes.OBSERVABLE)
        observable2_id = self.registry.register_observable(observable2, TypeCodes.OBSERVABLE)
        controller1_id = self.registry.register(controller1, TypeCodes.SPIN_BOX)
        controller2_id = self.registry.register(controller2, TypeCodes.SPIN_BOX)
        
        property_id = self.registry.register_observable_property(
            property, TypeCodes.OBSERVABLE_PROPERTY,
            None, "counter", observable1_id, controller1_id
        )
        
        # Verify initial relationships
        assert self.registry.get_observable_id_from_property_id(property_id) == observable1_id
        assert self.registry.get_controller_id_from_property_id(property_id) == controller1_id
        
        # Update observable
        success = self.registry.update_observable_id(property_id, observable2_id)
        assert success
        updated_property_id = self.registry.get_id(property)
        assert self.registry.get_observable_id_from_property_id(updated_property_id) == observable2_id
        
        # Update controller
        success = self.registry.update_controller_id(updated_property_id, controller2_id)
        assert success
        updated_property_id = self.registry.get_id(property)
        assert self.registry.get_controller_id_from_property_id(updated_property_id) == controller2_id
        
        # Update property name
        success = self.registry.update_property_name(updated_property_id, "count")
        assert success
        updated_property_id = self.registry.get_id(property)
        assert extract_property_name(updated_property_id) == "count"
        
        # Remove relationships
        self.registry.remove_observable_reference(updated_property_id)
        updated_property_id = self.registry.get_id(property)
        assert self.registry.get_observable_id_from_property_id(updated_property_id) is None
        
        self.registry.remove_controller_reference(updated_property_id)
        updated_property_id = self.registry.get_id(property)
        assert self.registry.get_controller_id_from_property_id(updated_property_id) is None
    
    def test_unregister_widget(self):
        """Test unregistering a widget."""
        # Create widget
        widget = MockWidget("Button")
        
        # Register widget
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON)
        
        # Unregister widget
        success = self.registry.unregister(widget_id)
        assert success
        
        # Verify widget is unregistered
        assert self.registry.get_widget(widget_id) is None
        assert self.registry.get_id(widget) is None
        
        # Verify callback was called
        assert widget_id in self.unregistered_widgets
    
    def test_unregister_container_cascade(self):
        """Test unregistering a container with cascade."""
        # Create components
        container = MockContainer("Panel")
        widget1 = MockWidget("Button1")
        widget2 = MockWidget("Button2")
        
        # Register components
        container_id = self.registry.register(container, TypeCodes.CUSTOM_CONTAINER)
        widget1_id = self.registry.register(widget1, TypeCodes.PUSH_BUTTON, None, container_id, "1")
        widget2_id = self.registry.register(widget2, TypeCodes.PUSH_BUTTON, None, container_id, "2")
        
        # Unregister container with cascade
        success = self.registry.unregister(container_id)
        assert success
        
        # Verify container and widgets are unregistered
        assert self.registry.get_widget(container_id) is None
        assert self.registry.get_widget(widget1_id) is None
        assert self.registry.get_widget(widget2_id) is None
        
        # Verify callbacks were called
        assert container_id in self.unregistered_widgets
        assert widget1_id in self.unregistered_widgets
        assert widget2_id in self.unregistered_widgets
    
    def test_unregister_container_reparent(self):
        """Test unregistering a container with reparenting."""
        # Create components
        container1 = MockContainer("Panel1")
        container2 = MockContainer("Panel2")
        widget1 = MockWidget("Button1")
        widget2 = MockWidget("Button2")
        
        # Register components
        container1_id = self.registry.register(container1, TypeCodes.CUSTOM_CONTAINER)
        container2_id = self.registry.register(container2, TypeCodes.CUSTOM_CONTAINER)
        widget1_id = self.registry.register(widget1, TypeCodes.PUSH_BUTTON, None, container1_id, "1")
        widget2_id = self.registry.register(widget2, TypeCodes.PUSH_BUTTON, None, container1_id, "2")
        
        # Unregister container1 with reparenting to container2
        success = self.registry.unregister(container1_id, container2_id)
        assert success
        
        # Verify container1 is unregistered
        assert self.registry.get_widget(container1_id) is None
        
        # Verify widgets are reparented
        updated_widget1_id = self.registry.get_id(widget1)
        updated_widget2_id = self.registry.get_id(widget2)
        
        assert self.registry.get_container_id_from_widget_id(updated_widget1_id) == container2_id
        assert self.registry.get_container_id_from_widget_id(updated_widget2_id) == container2_id
    
    def test_unregister_observable_cascade(self):
        """Test unregistering an observable with cascade."""
        # Create components
        observable = MockObservable("Model")
        property1 = MockObservableProperty("Prop1")
        property2 = MockObservableProperty("Prop2")
        
        # Register components
        observable_id = self.registry.register_observable(observable, TypeCodes.OBSERVABLE)
        property1_id = self.registry.register_observable_property(
            property1, TypeCodes.OBSERVABLE_PROPERTY, None, "prop1", observable_id
        )
        property2_id = self.registry.register_observable_property(
            property2, TypeCodes.OBSERVABLE_PROPERTY, None, "prop2", observable_id
        )
        
        # Unregister observable with cascade
        success = self.registry.unregister(observable_id)
        assert success
        
        # Verify observable and properties are unregistered
        assert self.registry.get_observable(observable_id) is None
        assert self.registry.get_observable_property(property1_id) is None
        assert self.registry.get_observable_property(property2_id) is None
        
        # Verify callbacks were called
        assert observable_id in self.unregistered_observables
        assert property1_id in self.unregistered_properties
        assert property2_id in self.unregistered_properties
    
    def test_unregister_controller_widget(self):
        """Test unregistering a widget that controls observable properties."""
        # Create components
        observable = MockObservable("Model")
        property = MockObservableProperty("Value")
        controller = MockWidget("Slider")
        
        # Register components
        observable_id = self.registry.register_observable(observable, TypeCodes.OBSERVABLE)
        controller_id = self.registry.register(controller, TypeCodes.SLIDER)
        property_id = self.registry.register_observable_property(
            property, TypeCodes.OBSERVABLE_PROPERTY,
            None, "value", observable_id, controller_id
        )
        
        # Verify initial relationship
        assert self.registry.get_controller_id_from_property_id(property_id) == controller_id
        
        # Unregister controller
        success = self.registry.unregister(controller_id)
        assert success
        
        # Verify controller is unregistered but property remains with no controller
        assert self.registry.get_widget(controller_id) is None
        updated_property_id = self.registry.get_id(property)
        assert updated_property_id is not None
        assert self.registry.get_controller_id_from_property_id(updated_property_id) is None


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main(["-v", __file__])