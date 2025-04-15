"""
Operations test suite for the PySignalDecipher ID system.

This test suite focuses on ID modification operations:
- Direct ID update operations with update_id()
- Container and location updates
- Observable and property reference updates
- Serialization scenarios (unregistering/recreating with same IDs)
- ID subscription behavior during operations
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


#MARK: - ID System Operations Tests

class TestIDSystemOperations:
    """Test cases focusing on ID operations and updates."""
    
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

    #MARK: - Container/Location Update Tests
    
    def test_update_container(self):
        """Test updating a widget's container."""
        # Create containers and widget
        container1 = MockContainer("Container1")
        container2 = MockContainer("Container2")
        button = MockWidget("Button")
        
        # Register components
        container1_id = self.registry.register(container1, "d")
        container2_id = self.registry.register(container2, "d")
        button_id = self.registry.register(button, "pb", None, container1_id, "custom_loc")
        
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
        expected_location = container2_components['container_location'] + "/" + container2_components['widget_location_id']
        assert updated_components['container_location'] == expected_location
        
        # Check relationship mappings
        container2_widgets = self.registry.get_widgets_by_container_id(container2_id)
        assert updated_id in container2_widgets
        
        container1_widgets = self.registry.get_widgets_by_container_id(container1_id)
        assert updated_id not in container1_widgets
    
    def test_update_container_with_collision(self):
        """Test updating a widget's container when there's a location ID collision."""
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
        
        # Container should be updated
        assert updated_components['container_unique_id'] == get_unique_id_from_id(container2_id)
        
        # Both widgets should now be in container2
        container2_widgets = self.registry.get_widgets_by_container_id(container2_id)
        assert updated_id in container2_widgets
        assert button2_id in container2_widgets
    
    def test_update_location(self):
        """Test updating a widget's location."""
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
    
    def test_update_id_subscription_continuation(self):
        """Test that subscriptions follow ID changes during updates."""
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

    #MARK: - Direct ID Update Tests
    
    def test_update_widget_id_location(self):
        """Test directly updating a widget's ID to change its location."""
        # Create and register a widget
        widget = MockWidget("Widget")
        widget_id = self.registry.register(widget, "pb", "widget1")
        
        # Track ID changes
        id_changes = []
        def on_id_change(old_id, new_id):
            id_changes.append((old_id, new_id))
        
        # Subscribe to ID changes
        subscribe_to_id(widget_id, on_id_change)
        
        # Original components
        original_components = parse_widget_id(widget_id)
        
        # Create a new ID with updated location
        new_location = "custom_location"
        new_widget_id = f"pb:widget1:{original_components['container_unique_id']}:{original_components['container_location']}-{new_location}"
        
        # Update the ID
        success, updated_id, error = self.registry.update_id(widget_id, new_widget_id)
        
        # Verify the update succeeded
        assert success, f"ID update failed: {error}"
        assert updated_id == new_widget_id
        assert error is None
        
        # Verify the widget is still accessible via the new ID
        assert self.registry.get_widget(updated_id) == widget
        assert self.registry.get_id(widget) == updated_id
        
        # Verify the old ID is no longer registered
        assert self.registry.get_widget(widget_id) is None
        
        # Verify the ID change was tracked
        assert (widget_id, updated_id) in self.id_changes
        
        # Verify subscriber was notified
        assert len(id_changes) == 1
        assert id_changes[0] == (widget_id, updated_id)
        
        # Verify the components were updated correctly
        updated_components = parse_widget_id(updated_id)
        assert updated_components['widget_location_id'] == new_location
        assert updated_components['type_code'] == original_components['type_code']
        assert updated_components['unique_id'] == original_components['unique_id']
        assert updated_components['container_unique_id'] == original_components['container_unique_id']
        assert updated_components['container_location'] == original_components['container_location']
    
    def test_update_widget_id_container(self):
        """Test directly updating a widget's ID to change its container."""
        # Create and register containers and widget
        container1 = MockContainer("Container1")
        container2 = MockContainer("Container2")
        widget = MockWidget("Widget")
        
        container1_id = self.registry.register(container1, "d", "cont1")
        container2_id = self.registry.register(container2, "d", "cont2")
        widget_id = self.registry.register(widget, "pb", "widget1", container1_id)
        
        # Original components
        original_components = parse_widget_id(widget_id)
        container2_components = parse_widget_id(container2_id)
        
        # Create a new ID with updated container
        new_container_unique_id = "cont2"
        new_container_location = container2_components['container_location'] + "/" + container2_components['widget_location_id']
        new_widget_id = f"pb:widget1:{new_container_unique_id}:{new_container_location}-{original_components['widget_location_id']}"
        
        # Update the ID
        success, updated_id, error = self.registry.update_id(widget_id, new_widget_id)
        
        # Verify the update succeeded
        assert success, f"ID update failed: {error}"
        assert updated_id == new_widget_id
        assert error is None
        
        # Verify the widget is still accessible via the new ID
        assert self.registry.get_widget(updated_id) == widget
        assert self.registry.get_id(widget) == updated_id
        
        # Verify the widget is now in container2's widget set
        container2_widgets = self.registry.get_widgets_by_container_id("cont2")
        assert updated_id in container2_widgets
        
        # Verify the widget is no longer in container1's widget set
        container1_widgets = self.registry.get_widgets_by_container_id("cont1")
        assert updated_id not in container1_widgets
        assert widget_id not in container1_widgets
    
    def test_update_widget_id_unique_id(self):
        """Test directly updating a widget's ID to change its unique ID."""
        # Create and register a widget
        widget = MockWidget("Widget")
        widget_id = self.registry.register(widget, "pb", "widget1")
        
        # Original components
        original_components = parse_widget_id(widget_id)
        
        # Create a new ID with updated unique ID
        new_unique_id = "custom_widget_id"
        new_widget_id = f"pb:{new_unique_id}:{original_components['container_unique_id']}:{original_components['location']}"
        
        # Update the ID
        success, updated_id, error = self.registry.update_id(widget_id, new_widget_id)
        
        # Verify the update succeeded
        assert success, f"ID update failed: {error}"
        assert updated_id == new_widget_id
        assert error is None
        
        # Verify the widget is still accessible via the new ID
        assert self.registry.get_widget(updated_id) == widget
        assert self.registry.get_id(widget) == updated_id
        
        # Verify the components were updated correctly
        updated_components = parse_widget_id(updated_id)
        assert updated_components['unique_id'] == new_unique_id
    
    def test_update_widget_id_type_code_error(self):
        """Test that attempting to change a widget's type code fails."""
        # Create and register a widget
        widget = MockWidget("Widget")
        widget_id = self.registry.register(widget, "pb", "widget1")
        
        # Original components
        original_components = parse_widget_id(widget_id)
        
        # Create a new ID with different type code
        new_widget_id = f"cb:{original_components['unique_id']}:{original_components['container_unique_id']}:{original_components['location']}"
        
        # Attempt to update the ID
        success, updated_id, error = self.registry.update_id(widget_id, new_widget_id)
        
        # Verify the update failed
        assert not success
        assert updated_id == widget_id  # ID should remain unchanged
        assert error is not None
        assert "type code" in error.lower()
    
    def test_update_widget_id_collision_error(self):
        """Test that attempting to use a unique ID that's already in use fails."""
        # Create and register two widgets
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        
        widget1_id = self.registry.register(widget1, "pb", "widget1")
        widget2_id = self.registry.register(widget2, "pb", "widget2")
        
        # Attempt to update widget1 to use widget2's unique ID
        original_components = parse_widget_id(widget1_id)
        new_widget_id = f"pb:widget2:{original_components['container_unique_id']}:{original_components['location']}"
        
        # Attempt to update the ID
        success, updated_id, error = self.registry.update_id(widget1_id, new_widget_id)
        
        # Verify the update failed
        assert not success
        assert updated_id == widget1_id  # ID should remain unchanged
        assert error is not None
        assert "already in use" in error.lower()
    
    def test_update_observable_id(self):
        """Test directly updating an observable's ID."""
        # Create and register an observable
        observable = MockObservable("Observable")
        observable_id = self.registry.register_observable(observable, "ob", "obs1")
        
        # Create a new ID with updated unique ID
        new_unique_id = "custom_observable_id"
        new_observable_id = f"ob:{new_unique_id}"
        
        # Update the ID
        success, updated_id, error = self.registry.update_id(observable_id, new_observable_id)
        
        # Verify the update succeeded
        assert success, f"ID update failed: {error}"
        assert updated_id == new_observable_id
        assert error is None
        
        # Verify the observable is still accessible via the new ID
        assert self.registry.get_observable(updated_id) == observable
        assert self.registry.get_id(observable) == updated_id
        
        # Verify the components were updated correctly
        updated_components = parse_observable_id(updated_id)
        assert updated_components['unique_id'] == new_unique_id
    
    def test_update_property_id(self):
        """Test directly updating a property's ID."""
        # Create and register components
        observable = MockObservable("Observable")
        property_obj = MockObservableProperty("Property")
        controller = MockWidget("Controller")
        
        observable_id = self.registry.register_observable(observable, "ob", "obs1")
        controller_id = self.registry.register(controller, "pb", "ctrl1")
        
        property_id = self.registry.register_observable_property(
            property_obj, "op", "prop1", "name", observable_id, controller_id
        )
        
        # Create a new ID with updated property name and unique ID
        new_property_name = "new_name"
        new_unique_id = "custom_property_id"
        original_components = parse_property_id(property_id)
        
        new_property_id = f"op:{new_unique_id}:{original_components['observable_unique_id']}:{new_property_name}:{original_components['controller_id']}"
        
        # Update the ID
        success, updated_id, error = self.registry.update_id(property_id, new_property_id)
        
        # Verify the update succeeded
        assert success, f"ID update failed: {error}"
        assert updated_id == new_property_id
        assert error is None
        
        # Verify the property is still accessible via the new ID
        assert self.registry.get_observable_property(updated_id) == property_obj
        assert self.registry.get_id(property_obj) == updated_id
        
        # Verify the components were updated correctly
        updated_components = parse_property_id(updated_id)
        assert updated_components['unique_id'] == new_unique_id
        assert updated_components['property_name'] == new_property_name
        
        # Verify relationships are maintained
        observable_properties = self.registry.get_observable_properties(observable_id)
        assert updated_id in observable_properties
        
        controller_properties = self.registry.get_controller_properties(controller_id)
        assert updated_id in controller_properties
    
    def test_update_property_with_observable_change(self):
        """Test directly updating a property to change its observable."""
        # Create and register components
        observable1 = MockObservable("Observable1")
        observable2 = MockObservable("Observable2")
        property_obj = MockObservableProperty("Property")
        
        observable1_id = self.registry.register_observable(observable1, "ob", "obs1")
        observable2_id = self.registry.register_observable(observable2, "ob", "obs2")
        
        property_id = self.registry.register_observable_property(
            property_obj, "op", "prop1", "name", observable1_id
        )
        
        # Create a new ID with updated observable reference
        original_components = parse_property_id(property_id)
        observable2_unique_id = get_unique_id_from_id(observable2_id)
        
        new_property_id = f"op:{original_components['unique_id']}:{observable2_unique_id}:{original_components['property_name']}:{original_components['controller_id']}"
        
        # Update the ID
        success, updated_id, error = self.registry.update_id(property_id, new_property_id)
        
        # Verify the update succeeded
        assert success, f"ID update failed: {error}"
        assert updated_id == new_property_id
        assert error is None
        
        # Verify the property is still accessible via the new ID
        assert self.registry.get_observable_property(updated_id) == property_obj
        assert self.registry.get_id(property_obj) == updated_id
        
        # Verify the components were updated correctly
        updated_components = parse_property_id(updated_id)
        assert updated_components['observable_unique_id'] == observable2_unique_id
        
        # Verify relationships are updated
        observable1_properties = self.registry.get_observable_properties(observable1_id)
        assert updated_id not in observable1_properties
        
        observable2_properties = self.registry.get_observable_properties(observable2_id)
        assert updated_id in observable2_properties
    
    #MARK: - Serialization Tests
    
    def test_recreate_with_same_ids(self):
        """Test unregistering and recreating components with the same IDs."""
        # Create and register a widget
        widget1 = MockWidget("Widget1")
        widget_id = self.registry.register(widget1, "pb", "custom_id", None, "custom_loc")
        
        # Verify registration
        assert self.registry.get_widget(widget_id) == widget1
        
        # Get original ID components
        original_components = parse_widget_id(widget_id)
        
        # Unregister the widget
        self.registry.unregister(widget_id)
        
        # Verify unregistration
        assert self.registry.get_widget(widget_id) is None
        
        # Create a new widget and register it with the same ID components
        widget2 = MockWidget("Widget2")
        new_widget_id = self.registry.register(
            widget2, 
            original_components['type_code'],
            original_components['unique_id'],
            original_components['container_unique_id'],
            original_components['widget_location_id']
        )
        
        # Verify the registration used the same ID
        assert new_widget_id == widget_id
        assert self.registry.get_widget(widget_id) == widget2
    
    def test_location_generator_cleanup_and_reuse(self):
        """Test location generators are cleaned up and reused properly."""
        # Create and register a container
        container1 = MockContainer("Container1")
        container_id = self.registry.register(container1, "d", "cont")

        # Register widgets to populate location generator
        for i in range(3):
            widget = MockWidget(f"Widget{i+1}")
            self.registry.register(widget, "pb", f"wid{i+1}", container_id)
        
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
    
    def test_container_with_custom_location_ids(self):
        """Test that containers can reuse custom location IDs after unregistration."""
        # Create and register a container
        container1 = MockContainer("Container1")
        container_id = self.registry.register(container1, "d", "cont")
        
        # Register widgets with custom location IDs
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        
        widget1_id = self.registry.register(widget1, "pb", "w1", container_id, "custom_loc_1")
        widget2_id = self.registry.register(widget2, "pb", "w2", container_id, "custom_loc_2")
        
        # Verify the custom location IDs were used
        widget1_components = parse_widget_id(widget1_id)
        widget2_components = parse_widget_id(widget2_id)
        
        assert widget1_components['widget_location_id'] == "custom_loc_1"
        assert widget2_components['widget_location_id'] == "custom_loc_2"
        
        # Unregister the container
        self.registry.unregister(container_id)
        
        # Create and register a new container with the same ID
        container2 = MockContainer("Container2")
        new_container_id = self.registry.register(container2, "d", "cont")
        
        # Register new widgets with the same custom location IDs
        new_widget1 = MockWidget("NewWidget1")
        new_widget2 = MockWidget("NewWidget2")
        
        new_widget1_id = self.registry.register(new_widget1, "pb", "new_w1", new_container_id, "custom_loc_1")
        new_widget2_id = self.registry.register(new_widget2, "pb", "new_w2", new_container_id, "custom_loc_2")
        
        # Verify the custom location IDs were reused
        new_widget1_components = parse_widget_id(new_widget1_id)
        new_widget2_components = parse_widget_id(new_widget2_id)
        
        assert new_widget1_components['widget_location_id'] == "custom_loc_1"
        assert new_widget2_components['widget_location_id'] == "custom_loc_2"
    
    def test_update_cascading_container_relationships(self):
        """Test that updating a container's ID cascades properly to all children."""
        # Create a nested container hierarchy
        root = MockContainer("Root")
        level1 = MockContainer("Level1")
        level2 = MockContainer("Level2")
        
        # Register the containers with explicit hierarchy
        root_id = self.registry.register(root, "d", "root")
        level1_id = self.registry.register(level1, "d", "level1", root_id)
        level2_id = self.registry.register(level2, "d", "level2", level1_id)
        
        # Register widgets at each level
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        widget3 = MockWidget("Widget3")
        
        widget1_id = self.registry.register(widget1, "pb", "w1", root_id)
        widget2_id = self.registry.register(widget2, "pb", "w2", level1_id)
        widget3_id = self.registry.register(widget3, "pb", "w3", level2_id)
        
        # Update root container's location using direct ID update
        original_components = parse_widget_id(root_id)
        new_root_id = f"d:root:{original_components['container_unique_id']}:{original_components['container_location']}-new_root_loc"
        
        # Update the ID
        success, updated_root_id, error = self.registry.update_id(root_id, new_root_id)
        assert success, f"ID update failed: {error}"
        
        # Get updated widget and container IDs
        updated_level1_id = self.registry.get_id(level1)
        updated_level2_id = self.registry.get_id(level2)
        updated_widget1_id = self.registry.get_id(widget1)
        updated_widget2_id = self.registry.get_id(widget2)
        updated_widget3_id = self.registry.get_id(widget3)
        
        # Verify all components were properly updated
        updated_root_components = parse_widget_id(updated_root_id)
        updated_level1_components = parse_widget_id(updated_level1_id)
        updated_level2_components = parse_widget_id(updated_level2_id)
        updated_widget1_components = parse_widget_id(updated_widget1_id)
        updated_widget2_components = parse_widget_id(updated_widget2_id)
        updated_widget3_components = parse_widget_id(updated_widget3_id)
        
        # Root widget location changed
        assert updated_root_components['widget_location_id'] == "new_root_loc"
        
        # Level1's container_location should reflect the updated root location
        expected_root_path = "0/" + updated_root_components['widget_location_id']
        assert updated_level1_components['container_location'] == expected_root_path
        
        # Widget1's container_location should reflect the updated root location
        assert updated_widget1_components['container_location'] == expected_root_path
        
        # Level2's container_location should reflect the updated level1 location
        expected_level1_path = expected_root_path + "/" + updated_level1_components['widget_location_id']
        assert updated_level2_components['container_location'] == expected_level1_path
        
        # Widget2's container_location should reflect the updated level1 location
        assert updated_widget2_components['container_location'] == expected_level1_path
        
        # Widget3's container_location should reflect the updated level2 location
        expected_level2_path = expected_level1_path + "/" + updated_level2_components['widget_location_id']
        assert updated_widget3_components['container_location'] == expected_level2_path
    
    def test_update_id_controller_property_relationship(self):
        """Test updating a controller's ID updates all controlled properties."""
        # Create and register components
        observable = MockObservable("Observable")
        property1 = MockObservableProperty("Property1")
        property2 = MockObservableProperty("Property2")
        controller = MockWidget("Controller")
        
        observable_id = self.registry.register_observable(observable, "ob", "obs1")
        controller_id = self.registry.register(controller, "pb", "ctrl1")
        
        property1_id = self.registry.register_observable_property(
            property1, "op", "prop1", "name1", observable_id, controller_id
        )
        
        property2_id = self.registry.register_observable_property(
            property2, "op", "prop2", "name2", observable_id, controller_id
        )
        
        # Update controller's unique ID directly
        original_components = parse_widget_id(controller_id)
        new_controller_id = f"pb:new_controller_id:{original_components['container_unique_id']}:{original_components['location']}"
        
        # Update the ID
        success, updated_controller_id, error = self.registry.update_id(controller_id, new_controller_id)
        assert success, f"ID update failed: {error}"
        
        # Get new property IDs
        updated_property1_id = self.registry.get_id(property1)
        updated_property2_id = self.registry.get_id(property2)
        
        # Verify properties still reference the controller
        controller_properties = self.registry.get_controller_properties(updated_controller_id)
        assert len(controller_properties) == 2
        assert updated_property1_id in controller_properties
        assert updated_property2_id in controller_properties
        
        # Verify property controller references were updated
        property1_components = parse_property_id(updated_property1_id)
        property2_components = parse_property_id(updated_property2_id)
        
        new_controller_unique_id = get_unique_id_from_id(updated_controller_id)
        assert property1_components['controller_id'] == new_controller_unique_id
        assert property2_components['controller_id'] == new_controller_unique_id


if __name__ == "__main__":
    # Run the tests directly if this script is executed
    pytest.main(["-vsx", __file__])