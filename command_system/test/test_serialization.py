"""
Serialization test suite for the PySignalDecipher ID system.

This test suite focuses on validating the ID system's behavior in serialization
scenarios, where components might be unregistered and recreated with the same IDs.
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

#MARK: - Serialization Test Cases

class TestIDSystemSerialization:
    """
    Test cases focusing on serialization scenarios for the ID system.
    
    These tests verify the system's behavior when components are unregistered
    and recreated with the same IDs, which is important for serialization.
    """
    
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
    
    def test_container_id_update_propagation(self):
        """
        Test that when a container's ID is updated, all child widgets have their
        container references updated correctly.
        """
        # Create a container hierarchy with widgets
        root_container = MockContainer("Root")
        sub_container = MockContainer("SubContainer")
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        widget3 = MockWidget("Widget3")
        
        # Register components
        root_id = self.registry.register(root_container, "w", "root")
        sub_id = self.registry.register(sub_container, "d", "sub", root_id)
        
        # Register widgets at different levels
        widget1_id = self.registry.register(widget1, "pb", "w1", root_id)
        widget2_id = self.registry.register(widget2, "pb", "w2", sub_id)
        widget3_id = self.registry.register(widget3, "pb", "w3", sub_id)
        
        # Update the subcontainer's ID
        updated_sub_id = self.registry.update_location(sub_id, "new_location")
        
        # Verify that children's container references are updated
        widget2_updated = self.registry.get_id(widget2)
        widget3_updated = self.registry.get_id(widget3)
        
        # Check updated widget IDs
        widget2_components = parse_widget_id(widget2_updated)
        widget3_components = parse_widget_id(widget3_updated)
        
        # Verify container references are correct
        assert widget2_components['container_unique_id'] == "sub"  # Container unique ID shouldn't change
        
        # Verify container location paths are updated
        sub_components = parse_widget_id(updated_sub_id)
        expected_location = sub_components['container_location'] + "/" + sub_components['widget_location_id']
        assert widget2_components['container_location'] == expected_location
        assert widget3_components['container_location'] == expected_location
        
        # Register a new widget to the updated container
        widget4 = MockWidget("Widget4")
        widget4_id = self.registry.register(widget4, "pb", "w4", updated_sub_id)
        
        # Verify it has the correct container location
        widget4_components = parse_widget_id(widget4_id)
        assert widget4_components['container_location'] == expected_location
    
    def test_controlled_property_id_updates(self):
        """
        Test that property IDs with controller references don't change when controller location changes.
        
        When a controller widget's location changes, its unique ID remains the same,
        so the property ID should also remain unchanged.
        """
        # Create components
        observable = MockObservable("Observable")
        controller = MockWidget("Controller")
        property_obj = MockObservableProperty("Property")
        
        # Register components
        observable_id = self.registry.register_observable(observable, "o")
        controller_id = self.registry.register(controller, "pb")
        
        # Register property with observable and controller
        property_id = self.registry.register_observable_property(
            property_obj, "op", None, "prop", observable_id, controller_id)
        
        # Get the controller's unique ID
        controller_unique_id = get_unique_id_from_id(controller_id)
        
        # Update the controller's location
        updated_controller_id = self.registry.update_location(controller_id, "new_loc")
        
        # Verify controller's full ID changed
        assert updated_controller_id != controller_id
        
        # Verify controller's unique ID did NOT change
        assert get_unique_id_from_id(updated_controller_id) == controller_unique_id
        
        # Get current property ID from registry
        current_property_id = self.registry.get_id(property_obj)
        
        # Verify property ID remained unchanged since it references the controller's unique ID
        assert current_property_id == property_id
        
        # Verify the property still references the same controller unique ID
        property_components = parse_property_id(property_id)
        assert property_components['controller_id'] == controller_unique_id
    
    def test_container_unregister_cascade_to_properties(self):
        """
        Test that when a container is unregistered, all controlled properties
        of its child widgets are properly unregistered.
        """
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
        observable_id = self.registry.register_observable(observable, "o", "obs")
        
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

        assert self.registry.unregister(container_id)
        
        # Verify properties are unregistered
        assert self.registry.get_observable_property(property1_id) is None
        assert self.registry.get_observable_property(property2_id) is None
        
        # Verify unregister callbacks were called for all components
        assert len(self.unregistered_widgets) >= 3  # Container + 2 widgets
        assert len(self.unregistered_properties) >= 2  # 2 properties
        
        # Verify specific unregistrations
        assert any(item[0] == container_id for item in self.unregistered_widgets)
        assert any(item[0] == widget1_id for item in self.unregistered_widgets)
        assert any(item[0] == widget2_id for item in self.unregistered_widgets)
        assert any(item[0] == property1_id for item in self.unregistered_properties)
        assert any(item[0] == property2_id for item in self.unregistered_properties)
    
    def test_location_generator_cleanup(self):
        """
        Test that when a container is unregistered, its location generators
        are properly cleaned up, so a new container with the same ID starts
        with a clean state.
        """
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
        
        self.registry.unregister(new_widget_id)
        
        # Try to register widgets with the same location IDs as before
        for loc_id in location_ids:
            test_widget = MockWidget(f"TestWidget_{loc_id}")
            test_id = self.registry.register(test_widget, "pb", f"test_{loc_id}", new_container_id, loc_id)
            test_components = parse_widget_id(test_id)
            assert test_components['widget_location_id'] == loc_id
    
    def test_container_with_custom_location_ids(self):
        """
        Test that containers can use custom location IDs, and when recreated
        after unregistration, can reuse the same custom IDs.
        """
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
    
    def test_nested_container_id_update(self):
        """
        Test that when a container's ID is updated, the container_location in
        all widgets in subcontainers is correctly updated.
        """
        # Create a deep container hierarchy
        root = MockContainer("Root")
        level1 = MockContainer("Level1")
        level2 = MockContainer("Level2")
        
        # Register the containers with explicit hierarchy
        root_id = self.registry.register(root, "w", "root")
        level1_id = self.registry.register(level1, "d", "level1", root_id)
        level2_id = self.registry.register(level2, "d", "level2", level1_id)
        
        # Register widgets at each level
        root_widget = MockWidget("RootWidget")
        level1_widget = MockWidget("Level1Widget")
        level2_widget = MockWidget("Level2Widget")
        
        root_widget_id = self.registry.register(root_widget, "pb", "rw", root_id)
        level1_widget_id = self.registry.register(level1_widget, "pb", "l1w", level1_id)
        level2_widget_id = self.registry.register(level2_widget, "pb", "l2w", level2_id)
        
        # Extract initial container paths
        level1_comp = parse_widget_id(level1_id)
        level2_comp = parse_widget_id(level2_id)
        level1_widget_comp = parse_widget_id(level1_widget_id)
        level2_widget_comp = parse_widget_id(level2_widget_id)
        
        initial_level1_path = level1_comp['container_location']
        initial_level2_path = level2_comp['container_location']
        
        # Update the root container's location
        updated_root_id = self.registry.update_location(root_id, "new_root_loc")
        
        # Get updated widget IDs
        updated_level1_id = self.registry.get_id(level1)
        updated_level2_id = self.registry.get_id(level2)
        updated_root_widget_id = self.registry.get_id(root_widget)
        updated_level1_widget_id = self.registry.get_id(level1_widget)
        updated_level2_widget_id = self.registry.get_id(level2_widget)
        
        # Parse updated components
        updated_root_comp = parse_widget_id(updated_root_id)
        updated_level1_comp = parse_widget_id(updated_level1_id)
        updated_level2_comp = parse_widget_id(updated_level2_id)
        updated_root_widget_comp = parse_widget_id(updated_root_widget_id)
        updated_level1_widget_comp = parse_widget_id(updated_level1_widget_id)
        updated_level2_widget_comp = parse_widget_id(updated_level2_widget_id)
        
        # Verify container locations are updated correctly
        # Root widget's container_location should reflect the updated root location
        expected_root_widget_location = "0/" + updated_root_comp['widget_location_id']
        assert updated_root_widget_comp['container_location'] == expected_root_widget_location
        
        # Level1's container_location should reflect the updated root location
        assert updated_level1_comp['container_location'] == expected_root_widget_location
        
        # Level1 widget's container_location should reflect the updated level1 location
        expected_level1_widget_location = expected_root_widget_location + "/" + updated_level1_comp['widget_location_id']
        assert updated_level1_widget_comp['container_location'] == expected_level1_widget_location
        
        # Level2's container_location should reflect the updated level1 location
        assert updated_level2_comp['container_location'] == expected_level1_widget_location
        
        # Level2 widget's container_location should reflect the updated level2 location
        expected_level2_widget_location = expected_level1_widget_location + "/" + updated_level2_comp['widget_location_id']
        assert updated_level2_widget_comp['container_location'] == expected_level2_widget_location
    
    def test_container_locations_map(self):
        """
        Test that the container's locations map is correctly managed when
        containers are registered, updated, and unregistered.
        """
        # Create a container with subcontainers
        main_container = MockContainer("MainContainer")
        sub1 = MockContainer("SubContainer1")
        sub2 = MockContainer("SubContainer2")
        
        # Register the containers
        main_id = self.registry.register(main_container, "w", "main")
        sub1_id = self.registry.register(sub1, "d", "sub1", main_id)
        sub2_id = self.registry.register(sub2, "d", "sub2", main_id)
        
        # Set up a locations map for the main container
        locations_map = {
            "tab1": sub1_id,
            "tab2": sub2_id
        }
        self.registry.set_locations_map(main_id, locations_map)
        
        # Verify the locations map was set correctly
        retrieved_map = self.registry.get_locations_map(main_id)
        assert retrieved_map == locations_map
        
        # Update sub1's ID
        updated_sub1_id = self.registry.update_location(sub1_id, "new_sub1_loc")
        
        # Verify the locations map is updated automatically
        updated_map = self.registry.get_locations_map(main_id)
        assert updated_map["tab1"] == updated_sub1_id
        assert updated_map["tab2"] == sub2_id
        
        # Unregister sub2
        self.registry.unregister(sub2_id)
        
        # Verify sub2 is removed from the locations map
        final_map = self.registry.get_locations_map(main_id)
        assert "tab1" in final_map
        assert final_map["tab1"] == updated_sub1_id
        assert "tab2" not in final_map
        
        # Unregister the main container
        self.registry.unregister(main_id)
        
        # Verify the locations map is empty
        assert self.registry.get_locations_map("main") == {}
        
        # Register a new main container with the same ID
        new_main = MockContainer("NewMainContainer")
        new_main_id = self.registry.register(new_main, "w", "main")
        
        # Verify it starts with an empty locations map
        assert self.registry.get_locations_map(new_main_id) == {}

    #MARK: - Enhanced Cleanup and Update Tests

    def test_widget_location_update_registry_cleanup(self):
        """
        Test that when a widget's location is updated, the old location ID is properly
        unregistered from the generator and the new one is registered.
        """
        # Create container and widget
        container = MockContainer("Container")
        widget = MockWidget("Widget")
        
        # Register components
        container_id = self.registry.register(container, "d", "cont")
        widget_id = self.registry.register(widget, "pb", "wid", container_id, "loc1")
        
        # Update widget location
        updated_id = self.registry.update_location(widget_id, "loc2")
        
        # Verify the update
        components = parse_widget_id(updated_id)
        assert components['widget_location_id'] == "loc2"
        
        # Try to register a new widget with the old location ID
        new_widget = MockWidget("NewWidget")
        new_id = self.registry.register(new_widget, "pb", "new_wid", container_id, "loc1")
        
        # Verify the old location ID was freed and can be reused
        components = parse_widget_id(new_id)
        assert components['widget_location_id'] == "loc1"
        
        # Try to register another widget with the new location ID - should get a different location ID
        another_widget = MockWidget("AnotherWidget")
        another_id = self.registry.register(another_widget, "pb", "another_wid", container_id, "loc2")
        another_components = parse_widget_id(another_id)
        assert another_components['widget_location_id'] != "loc2"  # Should be different
    
    def test_widget_container_update_registry_cleanup(self):
        """
        Test that when a widget's container is updated, the location ID is properly
        unregistered from the old container and registered with the new one.
        """
        # Create two containers and a widget
        container1 = MockContainer("Container1")
        container2 = MockContainer("Container2")
        widget = MockWidget("Widget")
        
        # Register components
        container1_id = self.registry.register(container1, "d", "cont1")
        container2_id = self.registry.register(container2, "d", "cont2")
        widget_id = self.registry.register(widget, "pb", "wid", container1_id, "loc1")
        
        # Update widget's container
        updated_id = self.registry.update_container(widget_id, container2_id)
        
        # Verify the update
        components = parse_widget_id(updated_id)
        assert components['container_unique_id'] == "cont2"
        assert components['widget_location_id'] == "loc1"  # Location ID should be preserved
        
        # Try to register a new widget in the first container with the same location ID
        new_widget = MockWidget("NewWidget")
        new_id = self.registry.register(new_widget, "pb", "new_wid", container1_id, "loc1")
        
        # Verify the location ID was freed in the first container
        components = parse_widget_id(new_id)
        assert components['widget_location_id'] == "loc1"
        
        # Try to register another widget in the second container with the same location ID - should get a different ID
        another_widget = MockWidget("AnotherWidget")
        another_id = self.registry.register(another_widget, "pb", "another_wid", container2_id, "loc1")
        another_components = parse_widget_id(another_id)
        assert another_components['widget_location_id'] != "loc1"  # Should be different
    
    def test_container_location_generators_cleanup(self):
        """
        Test that the _container_location_generators mapping is properly cleaned up
        when containers are unregistered.
        """
        # Create and register a container
        container = MockContainer("Container")
        container_id = self.registry.register(container, "d", "cont")
        
        # Parse the container ID to get components
        container_components = parse_widget_id(container_id)
        
        # Get the container location path
        container_location = container_components['container_location']
        container_location_id = container_components['widget_location_id']
        full_container_path = f"{container_location}/{container_location_id}"
        
        # Add a widget to ensure the location generator is created
        widget = MockWidget("Widget")
        self.registry.register(widget, "pb", "wid", container_id)
        
        # Verify the container's location has an entry in the location generators dictionary
        assert full_container_path in self.registry._widget_manager._container_location_generators
        
        # Unregister the container
        self.registry.unregister(container_id)
        
        # Verify the container's location is removed from the location generators dictionary
        assert full_container_path not in self.registry._widget_manager._container_location_generators
        
        # Register a new container with the same ID
        new_container = MockContainer("NewContainer")
        new_container_id = self.registry.register(new_container, "d", "cont")
        
        # Parse the new container ID
        new_container_components = parse_widget_id(new_container_id)
        
        # Get the new container location path
        new_container_location = new_container_components['container_location']
        new_container_location_id = new_container_components['widget_location_id']
        new_full_container_path = f"{new_container_location}/{new_container_location_id}"
        
        # Add a widget to ensure the location generator is created
        new_widget = MockWidget("NewWidget")
        self.registry.register(new_widget, "pb", "new_wid", new_container_id)
        
        # Verify a new entry is created for the container's location
        assert new_full_container_path in self.registry._widget_manager._container_location_generators
    
    def test_nested_cleanup_and_recreation(self):
        """
        Test that when a complex container hierarchy is unregistered and recreated,
        all location generators are properly cleaned up at all levels.
        """
        # Create a nested container hierarchy
        root = MockContainer("Root")
        mid = MockContainer("Middle")
        leaf = MockContainer("Leaf")
        
        # Register the hierarchy
        root_id = self.registry.register(root, "d", "root")
        mid_id = self.registry.register(mid, "d", "mid", root_id, "midloc")
        leaf_id = self.registry.register(leaf, "d", "leaf", mid_id, "leafloc")
        
        # Add widgets at each level with specific location IDs
        root_widget = MockWidget("RootWidget")
        mid_widget = MockWidget("MidWidget")
        leaf_widget = MockWidget("LeafWidget")
        
        root_widget_id = self.registry.register(root_widget, "pb", "rwid", root_id, "rwloc")
        mid_widget_id = self.registry.register(mid_widget, "pb", "mwid", mid_id, "mwloc")
        leaf_widget_id = self.registry.register(leaf_widget, "pb", "lwid", leaf_id, "lwloc")
        
        # Store unique IDs and location IDs for later verification
        root_unique_id = get_unique_id_from_id(root_id)
        mid_unique_id = get_unique_id_from_id(mid_id)
        leaf_unique_id = get_unique_id_from_id(leaf_id)
        
        # Unregister the entire hierarchy by unregistering the root
        self.registry.unregister(root_id)
        
        # Recreate the hierarchy with the same IDs
        new_root = MockContainer("NewRoot")
        new_mid = MockContainer("NewMiddle")
        new_leaf = MockContainer("NewLeaf")
        
        new_root_id = self.registry.register(new_root, "d", "root")
        new_mid_id = self.registry.register(new_mid, "d", "mid", new_root_id, "midloc")
        new_leaf_id = self.registry.register(new_leaf, "d", "leaf", new_mid_id, "leafloc")
        
        # Add new widgets with the same location IDs
        new_root_widget = MockWidget("NewRootWidget")
        new_mid_widget = MockWidget("NewMidWidget")
        new_leaf_widget = MockWidget("NewLeafWidget")
        
        new_root_widget_id = self.registry.register(new_root_widget, "pb", "new_rwid", new_root_id, "rwloc")
        new_mid_widget_id = self.registry.register(new_mid_widget, "pb", "new_mwid", new_mid_id, "mwloc")
        new_leaf_widget_id = self.registry.register(new_leaf_widget, "pb", "new_lwid", new_leaf_id, "lwloc")
        
        # Verify the location IDs were successfully reused at all levels
        assert parse_widget_id(new_root_widget_id)['widget_location_id'] == "rwloc"
        assert parse_widget_id(new_mid_widget_id)['widget_location_id'] == "mwloc"
        assert parse_widget_id(new_leaf_widget_id)['widget_location_id'] == "lwloc"


if __name__ == "__main__":
    # Run the tests directly if this script is executed
    pytest.main(["-v", __file__])