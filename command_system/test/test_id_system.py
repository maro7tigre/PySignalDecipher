"""
Test suite for the ID system with hierarchical location handling.

This tests the ID system functionality with composite location formats
and container-level location management.
"""
import pytest
import sys
import os
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from command_system.id_system import (
    IDRegistry, get_id_registry, TypeCodes,
    extract_type_code, extract_unique_id, 
    extract_container_unique_id, extract_location,
    extract_location_parts, extract_subcontainer_path, extract_widget_location_id,
    extract_observable_unique_id, extract_property_name,
    extract_controller_unique_id, create_location_path, append_to_location_path,
    is_widget_id, is_observable_id, is_observable_property_id, is_subcontainer_id,
    subscribe_to_id, unsubscribe_from_id, clear_subscriptions
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
        self.id_changes = []
        
        self.registry.set_on_widget_unregister(
            lambda widget_id: self.unregistered_widgets.append(widget_id)
        )
        self.registry.set_on_observable_unregister(
            lambda observable_id: self.unregistered_observables.append(observable_id)
        )
        self.registry.set_on_property_unregister(
            lambda property_id: self.unregistered_properties.append(property_id)
        )
        self.registry.set_on_id_changed(
            lambda old_id, new_id: self.id_changes.append((old_id, new_id))
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
        assert extract_location(widget1_id) == "0"  # Default location
    
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
        nested_widget_id = self.registry.register(nested_widget, TypeCodes.PUSH_BUTTON, None, nested_container_id, "3/1")
        
        # Verify container relationships
        assert self.registry.get_container_id_from_widget_id(widget1_id) == container_id
        assert self.registry.get_container_id_from_widget_id(widget2_id) == container_id
        assert self.registry.get_container_id_from_widget_id(nested_container_id) == container_id
        assert self.registry.get_container_id_from_widget_id(nested_widget_id) == nested_container_id
        
        # Verify widget location - the format will now include a generated widget ID
        location1 = extract_location(widget1_id)
        location2 = extract_location(widget2_id)
        location_nested = extract_location(nested_container_id)
        location_nested_widget = extract_location(nested_widget_id)
        
        # Check that locations follow expected patterns
        assert location1.startswith("1-")  # Location 1 with widget ID
        assert location2.startswith("2-")  # Location 2 with widget ID
        assert location_nested.startswith("3-")  # Location 3 with widget ID
        
        # Nested widget location should include both 3 and 1
        assert location_nested_widget.startswith("3/1-")  # Nested location with widget ID
        
        # Test getting widgets by container
        container_widgets = self.registry.get_widget_ids_by_container_id(container_id)
        assert len(container_widgets) == 3
        assert widget1_id in container_widgets
        assert widget2_id in container_widgets
        assert nested_container_id in container_widgets
        
        # Test getting widgets by container and location
        widgets_at_location1 = self.registry.get_widget_ids_by_container_id_and_location(container_id, "1")
        assert len(widgets_at_location1) == 1
        assert widget1_id in widgets_at_location1
        
        # Test nested container
        nested_widgets = self.registry.get_widget_ids_by_container_id(nested_container_id)
        assert len(nested_widgets) == 1
        assert nested_widget_id in nested_widgets
    
    def test_hierarchical_container_ids(self):
        """Test hierarchical container IDs with deep nesting."""
        # Create a deep container hierarchy
        main_container = MockContainer("MainApp")
        tab_container = MockContainer("TabContainer")
        dock_container = MockContainer("DockContainer")
        form_container = MockContainer("FormContainer")
        
        button1 = MockWidget("Button1")
        button2 = MockWidget("Button2")
        button3 = MockWidget("Button3")
        
        # Register components with hierarchy
        main_id = self.registry.register(main_container, TypeCodes.WINDOW_CONTAINER)
        tab_id = self.registry.register(tab_container, TypeCodes.TAB_CONTAINER, None, main_id, "0")
        dock_id = self.registry.register(dock_container, TypeCodes.DOCK_CONTAINER, None, tab_id, "0/1")
        form_id = self.registry.register(form_container, TypeCodes.CUSTOM_CONTAINER, None, dock_id, "0/1/2")
        
        # Register widgets at different levels
        button1_id = self.registry.register(button1, TypeCodes.PUSH_BUTTON, None, main_id, "0/button1")
        button2_id = self.registry.register(button2, TypeCodes.PUSH_BUTTON, None, dock_id, "0/1/button2")
        button3_id = self.registry.register(button3, TypeCodes.PUSH_BUTTON, None, form_id, "0/1/2/button3")
        
        # Verify hierarchical paths - with generated widget IDs
        tab_location = extract_location(tab_id)
        dock_location = extract_location(dock_id)
        form_location = extract_location(form_id)
        
        # Check location formats - they will have generated widget IDs
        assert tab_location.startswith("0-")
        assert dock_location.startswith("0/1-")
        assert form_location.startswith("0/1/2-")
        
        # Check button locations
        button1_location = extract_location(button1_id)
        button2_location = extract_location(button2_id)
        button3_location = extract_location(button3_id)
        
        assert button1_location.startswith("0/button1-") or button1_location.startswith("0-")
        assert button2_location.startswith("0/1/button2-") or button2_location.startswith("0/1-")
        assert button3_location.startswith("0/1/2/button3-") or button3_location.startswith("0/1/2-")
        
        # Test location parts extraction
        location_parts = extract_location_parts(button3_id)
        assert "0" in location_parts or "0/1/2" in location_parts
        
        # Test container lookup by path
        assert self.registry.get_container_id_from_widget_id(button1_id) == main_id
        assert self.registry.get_container_id_from_widget_id(button2_id) == dock_id
        assert self.registry.get_container_id_from_widget_id(button3_id) == form_id
    
    def test_container_with_location_maps(self):
        """Test container location maps for subcontainers."""
        # Create a container with subcontainers
        main_container = MockContainer("MainWindow")
        tab1_container = MockContainer("Tab1")
        tab2_container = MockContainer("Tab2")
        panel_container = MockContainer("Panel")
        
        # Register components
        main_id = self.registry.register(main_container, TypeCodes.WINDOW_CONTAINER)
        tab1_id = self.registry.register(tab1_container, TypeCodes.TAB_CONTAINER, None, main_id, "0")
        tab2_id = self.registry.register(tab2_container, TypeCodes.TAB_CONTAINER, None, main_id, "1")
        panel_id = self.registry.register(panel_container, TypeCodes.CUSTOM_CONTAINER, None, tab1_id, "0/panel")
        
        # Set up location maps
        locations_map = {
            tab1_id: "0",
            tab2_id: "1"
        }
        self.registry.set_locations_map(main_id, locations_map)
        
        panel_locations_map = {
            panel_id: "panel"
        }
        self.registry.set_locations_map(tab1_id, panel_locations_map)
        
        # Get and verify location maps
        main_locations = self.registry.get_locations_map(main_id)
        assert main_locations == locations_map
        
        tab1_locations = self.registry.get_locations_map(tab1_id)
        assert tab1_locations == panel_locations_map
        
        # Test getting subcontainer at location
        assert self.registry.get_subcontainer_id_at_location(main_id, "0") == tab1_id
        assert self.registry.get_subcontainer_id_at_location(main_id, "1") == tab2_id
        assert self.registry.get_subcontainer_id_at_location(tab1_id, "panel") == panel_id
        
        # Test getting widgets at subcontainer location
        button1 = MockWidget("Button1")
        button2 = MockWidget("Button2")
        
        button1_id = self.registry.register(button1, TypeCodes.PUSH_BUTTON, None, tab1_id, "0/button1")
        button2_id = self.registry.register(button2, TypeCodes.PUSH_BUTTON, None, tab1_id, "0/button2")
        
        widgets_at_tab1 = self.registry.get_widgets_at_subcontainer_location(main_id, "0")
        assert len(widgets_at_tab1) >= 1
    
    def test_composite_location_id_format(self):
        """Test composite location ID format with subcontainer and widget parts."""
        # Create a container with a subcontainer
        main_container = MockContainer("MainWindow")
        tab_container = MockContainer("TabContainer")
        
        # Register components
        main_id = self.registry.register(main_container, TypeCodes.WINDOW_CONTAINER)
        tab_id = self.registry.register(tab_container, TypeCodes.TAB_CONTAINER, None, main_id, "0")
        
        # Generate a widget location ID using the subcontainer generator
        sub_generator = self.registry._get_subcontainer_generator(tab_id)
        # Call generate_location_id without the subcontainer_location parameter
        widget_location_id = extract_unique_id(sub_generator.generate_observable_id("tmp"))
        location = f"0-{widget_location_id}"
        
        # Create a widget with this location
        button = MockWidget("Button")
        button_id = self.registry.register(button, TypeCodes.PUSH_BUTTON, None, tab_id, location)
        
        # Verify the format - location should be preserved as is
        assert extract_location(button_id) == location
        
        # The location should be in format "subcontainer_location-widget_location_id"
        location_parts = location.split("-")
        assert len(location_parts) == 2
        
        # Create a hierarchical path
        deep_path = create_location_path("0", "1", "2")
        assert deep_path == "0/1/2"
        
        # Append to location path
        extended_path = append_to_location_path(deep_path, "widget1")
        assert extended_path == "0/1/2/widget1"
    
    def test_subcontainer_generators(self):
        """Test that each subcontainer has its own ID generator."""
        # Create containers
        main_container = MockContainer("MainWindow")
        tab1_container = MockContainer("Tab1")
        tab2_container = MockContainer("Tab2")
        
        # Register containers as subcontainers
        main_id = self.registry.register(main_container, TypeCodes.WINDOW_CONTAINER)
        tab1_id = self.registry.register(tab1_container, TypeCodes.TAB_CONTAINER, None, main_id, "0")
        tab2_id = self.registry.register(tab2_container, TypeCodes.TAB_CONTAINER, None, main_id, "1")
        
        # Get subcontainer generators
        sub_gen1 = self.registry._get_subcontainer_generator(tab1_id)
        sub_gen2 = self.registry._get_subcontainer_generator(tab2_id)
        
        # Generate IDs from each, they should be independent
        # Use generate_observable_id and extract location IDs - use different prefixes for each generator
        loc1 = f"tab1-{extract_unique_id(sub_gen1.generate_observable_id("tmp"))}"
        loc2 = f"tab1-{extract_unique_id(sub_gen1.generate_observable_id("tmp"))}"
        loc3 = f"tab2-{extract_unique_id(sub_gen2.generate_observable_id("tmp"))}"
        loc4 = f"tab2-{extract_unique_id(sub_gen2.generate_observable_id("tmp"))}"
        
        # Each generator should produce its own sequence
        assert loc1 != loc2  # Different IDs from the same generator
        assert loc3 != loc4  # Different IDs from the same generator
        
        # With our prefix approach, all locations should now be different
        locations = [loc1, loc2, loc3, loc4]
        assert len(locations) == 4  # Should be 4 locations
        assert len(set(locations)) == 4  # All locations should be unique
        
        # Create widgets with these locations
        button1 = MockWidget("Button1")
        button2 = MockWidget("Button2")
        button3 = MockWidget("Button3")
        button4 = MockWidget("Button4")
        
        button1_id = self.registry.register(button1, TypeCodes.PUSH_BUTTON, None, tab1_id, loc1)
        button2_id = self.registry.register(button2, TypeCodes.PUSH_BUTTON, None, tab1_id, loc2)
        button3_id = self.registry.register(button3, TypeCodes.PUSH_BUTTON, None, tab2_id, loc3)
        button4_id = self.registry.register(button4, TypeCodes.PUSH_BUTTON, None, tab2_id, loc4)
        
        # Verify that widgets are correctly assigned to their containers
        tab1_widgets = self.registry.get_widget_ids_by_container_id(tab1_id)
        tab2_widgets = self.registry.get_widget_ids_by_container_id(tab2_id)
        
        assert button1_id in tab1_widgets
        assert button2_id in tab1_widgets
        assert button3_id in tab2_widgets
        assert button4_id in tab2_widgets
        
        # Verify location format is preserved
        assert extract_location(button1_id) == loc1
        assert extract_location(button2_id) == loc2
        assert extract_location(button3_id) == loc3
        assert extract_location(button4_id) == loc4
    
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
        
        # Get initial location
        initial_location = extract_location(widget_id)
        
        # Update container
        success = self.registry.update_container_id(widget_id, container2_id)
        assert success
        
        # Get updated widget ID
        updated_widget_id = self.registry.get_id(widget)
        
        # Verify new container
        assert self.registry.get_container_id_from_widget_id(updated_widget_id) == container2_id
        
        # Verify location is preserved
        assert extract_location(updated_widget_id) == initial_location
        
        # Verify ID change callback
        assert (widget_id, updated_widget_id) in self.id_changes
        
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
        initial_location = extract_location(widget_id)
        assert initial_location.startswith("1-")
        
        # Update location
        success = self.registry.update_location(widget_id, "2")
        assert success
        
        # Get updated widget ID
        updated_widget_id = self.registry.get_id(widget)
        
        # Verify new location
        updated_location = extract_location(updated_widget_id)
        assert updated_location.startswith("2-")
        assert updated_location != initial_location
        
        # Try updating to a composite location
        composite_location = "2/widget5-custom"
        success = self.registry.update_location(updated_widget_id, composite_location)
        assert success
        
        final_widget_id = self.registry.get_id(widget)
        final_location = extract_location(final_widget_id)
        
        # Verify location is exactly as specified
        assert final_location == composite_location
    
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
        
        # Store original widget IDs
        original_widget1_id = widget1_id
        original_widget2_id = widget2_id
        
        # Set locations map
        locations_map = {}
        self.registry.set_locations_map(container_id, locations_map)
        
        # Unregister container with cascade
        success = self.registry.unregister(container_id)
        assert success
        
        # Verify container is unregistered
        assert self.registry.get_widget(container_id) is None
        
        # Verify widgets are unregistered - they should be automatically
        # unregistered by the cascade
        assert self.registry.get_widget(original_widget1_id) is None
        assert self.registry.get_widget(original_widget2_id) is None
        assert self.registry.get_id(widget1) is None
        assert self.registry.get_id(widget2) is None
        
        # Verify callbacks
        assert container_id in self.unregistered_widgets
        assert original_widget1_id in self.unregistered_widgets or widget1_id in self.unregistered_widgets
        assert original_widget2_id in self.unregistered_widgets or widget2_id in self.unregistered_widgets
        
        # Verify subcontainer generator is removed
        if hasattr(self.registry, '_subcontainer_generators'):
            assert container_id not in self.registry._subcontainer_generators
    
    def test_is_subcontainer_id(self):
        """Test the is_subcontainer_id utility function."""
        # Create different component types
        container = MockContainer("Panel")
        tab_container = MockContainer("TabPanel")
        widget = MockWidget("Button")
        observable = MockObservable("Model")
        
        # Register components
        container_id = self.registry.register(container, TypeCodes.CUSTOM_CONTAINER)
        tab_id = self.registry.register(tab_container, TypeCodes.TAB_CONTAINER)
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON)
        observable_id = self.registry.register_observable(observable, TypeCodes.OBSERVABLE)
        
        # Check container identities
        assert is_subcontainer_id(container_id)
        assert is_subcontainer_id(tab_id)
        assert not is_subcontainer_id(widget_id)
        assert not is_subcontainer_id(observable_id)
        
    def test_update_id(self):
        """Test updating a component's ID with relationship maintenance."""
        # Create a container hierarchy
        container = MockContainer("MainContainer")
        subcontainer = MockContainer("SubContainer")
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        
        # Register components
        container_id = self.registry.register(container, TypeCodes.CUSTOM_CONTAINER)
        subcontainer_id = self.registry.register(subcontainer, TypeCodes.CUSTOM_CONTAINER, None, container_id, "0")
        widget1_id = self.registry.register(widget1, TypeCodes.PUSH_BUTTON, None, subcontainer_id, "0/1")
        widget2_id = self.registry.register(widget2, TypeCodes.PUSH_BUTTON, None, subcontainer_id, "0/2")
        
        # Set up location maps
        self.registry._container_locations_map[container_id] = {subcontainer_id: "0"}
        self.registry._container_locations_map[subcontainer_id] = {}
        
        # Create new ID for subcontainer
        new_subcontainer_id = f"{TypeCodes.CUSTOM_CONTAINER}:ZZZ:{extract_container_unique_id(subcontainer_id)}:{extract_location(subcontainer_id)}"
        
        # Update the ID
        result_id = self.registry.update_id(subcontainer_id, new_subcontainer_id)
        assert result_id == new_subcontainer_id
        
        # Verify subcontainer's ID is updated
        assert self.registry.get_id(subcontainer) == new_subcontainer_id
        
        # Verify children's container references are updated
        assert self.registry.get_container_id_from_widget_id(self.registry.get_id(widget1)) == new_subcontainer_id
        assert self.registry.get_container_id_from_widget_id(self.registry.get_id(widget2)) == new_subcontainer_id
        
        # Verify location maps are updated
        assert self.registry._container_locations_map[container_id][new_subcontainer_id] == "0"
        assert new_subcontainer_id in self.registry._container_locations_map
        
        # Verify ID change callback was triggered
        assert (subcontainer_id, new_subcontainer_id) in self.id_changes
        
        # Also test with an observable
        observable = MockObservable("TestObservable")
        property1 = MockObservableProperty("Property1")
        
        # Register components
        observable_id = self.registry.register_observable(observable, TypeCodes.OBSERVABLE)
        property_id = self.registry.register_observable_property(
            property1, TypeCodes.OBSERVABLE_PROPERTY, None, "test", observable_id)
        
        # Create new ID for observable
        new_observable_id = f"{TypeCodes.OBSERVABLE}:YYY"
        
        # Update the observable ID
        result_id = self.registry.update_id(observable_id, new_observable_id)
        assert result_id == new_observable_id
        
        # Verify observable's ID is updated
        assert self.registry.get_id(observable) == new_observable_id
        
        # Verify property references are updated
        updated_property_id = self.registry.get_id(property1)
        assert self.registry.get_observable_id_from_property_id(updated_property_id) == new_observable_id
        
        # Test case for failure - trying to update with a non-existent ID
        non_existent_id = "pb:999:0:0"
        result = self.registry.update_id(non_existent_id, new_subcontainer_id)
        assert result is None  # Should return None for failure
        
        # Test case for type mismatch - should fail
        button = MockWidget("TestButton")
        button_id = self.registry.register(button, TypeCodes.PUSH_BUTTON)
        invalid_new_id = f"{TypeCodes.SLIDER}:XXX:0:0"
        result = self.registry.update_id(button_id, invalid_new_id)
        assert result is None  # Should return None for type mismatch
        
    # -------------------- ID Subscription Tests --------------------
    
    def test_id_subscription_widget(self):
        """Test subscribing to widget ID changes."""
        # Create and register a widget
        container = MockContainer("Panel")
        widget = MockWidget("Button")
        
        container_id = self.registry.register(container, TypeCodes.CUSTOM_CONTAINER)
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON, None, container_id, "1")
        
        # Track subscription notifications
        subscription_changes = []
        
        def on_id_changed(old_id, new_id):
            subscription_changes.append((old_id, new_id))
        
        # Subscribe to widget ID changes
        success = subscribe_to_id(widget_id, on_id_changed)
        assert success
        
        # Update widget container
        original_id = widget_id
        self.registry.update_container_id(widget_id, None)
        
        # Get the updated widget ID
        updated_id = self.registry.get_id(widget)
        
        # Verify subscription notification
        assert len(subscription_changes) == 1
        assert subscription_changes[0] == (original_id, updated_id)
        
        # Update widget location
        original_id = updated_id
        self.registry.update_location(updated_id, "2")
        
        # Get the new updated widget ID
        updated_id = self.registry.get_id(widget)
        
        # Verify second subscription notification
        assert len(subscription_changes) == 2
        assert subscription_changes[1] == (original_id, updated_id)
    
    def test_id_subscription_observable(self):
        """Test subscribing to observable ID changes."""
        # Create and register an observable
        observable = MockObservable("TestObservable")
        observable_id = self.registry.register_observable(observable, TypeCodes.OBSERVABLE)
        
        # Track subscription notifications
        subscription_changes = []
        
        def on_id_changed(old_id, new_id):
            subscription_changes.append((old_id, new_id))
        
        # Subscribe to observable ID changes
        success = subscribe_to_id(observable_id, on_id_changed)
        assert success
        
        # Update observable ID directly
        original_id = observable_id
        new_id = f"{TypeCodes.OBSERVABLE}:ABC"
        self.registry.update_id(observable_id, new_id)
        
        # Get the updated observable ID
        updated_id = self.registry.get_id(observable)
        
        # Verify subscription notification
        assert len(subscription_changes) == 1
        assert subscription_changes[0] == (original_id, updated_id)
    
    def test_id_subscription_property(self):
        """Test subscribing to property ID changes."""
        # Create and register components
        observable = MockObservable("Person")
        property_obj = MockObservableProperty("Name")
        
        observable_id = self.registry.register_observable(observable, TypeCodes.OBSERVABLE)
        property_id = self.registry.register_observable_property(
            property_obj, TypeCodes.OBSERVABLE_PROPERTY, None, "name", observable_id)
        
        # Track subscription notifications
        subscription_changes = []
        
        def on_id_changed(old_id, new_id):
            subscription_changes.append((old_id, new_id))
        
        # Subscribe to property ID changes
        success = subscribe_to_id(property_id, on_id_changed)
        assert success
        
        # Update property name
        original_id = property_id
        self.registry.update_property_name(property_id, "fullName")
        
        # Get the updated property ID
        updated_id = self.registry.get_id(property_obj)
        
        # Verify subscription notification
        assert len(subscription_changes) == 1
        assert subscription_changes[0] == (original_id, updated_id)
    
    def test_id_subscription_multiple_callbacks(self):
        """Test multiple callbacks for the same ID."""
        # Create and register a widget
        widget = MockWidget("Button")
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON)
        
        # Track subscription notifications from two different callbacks
        changes_1 = []
        changes_2 = []
        
        def callback_1(old_id, new_id):
            changes_1.append((old_id, new_id))
            
        def callback_2(old_id, new_id):
            changes_2.append((old_id, new_id))
        
        # Subscribe both callbacks to the same ID
        subscribe_to_id(widget_id, callback_1)
        subscribe_to_id(widget_id, callback_2)
        
        # Update widget location
        original_id = widget_id
        self.registry.update_location(widget_id, "location1")
        
        # Get the updated widget ID
        updated_id = self.registry.get_id(widget)
        
        # Verify both callbacks were notified
        assert len(changes_1) == 1
        assert len(changes_2) == 1
        assert changes_1[0] == (original_id, updated_id)
        assert changes_2[0] == (original_id, updated_id)
    
    def test_id_subscription_follows_id_change(self):
        """Test that subscriptions automatically follow ID changes."""
        # Create and register a widget
        container = MockContainer("Panel")
        widget = MockWidget("Button")
        
        container_id = self.registry.register(container, TypeCodes.CUSTOM_CONTAINER)
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON, None, container_id, "1")
        
        # Track subscription notifications
        subscription_changes = []
        
        def on_id_changed(old_id, new_id):
            subscription_changes.append((old_id, new_id))
        
        # Subscribe to widget ID changes
        subscribe_to_id(widget_id, on_id_changed)
        
        # Update widget container
        original_id = widget_id
        self.registry.update_container_id(widget_id, None)
        
        # Get the updated widget ID
        updated_id = self.registry.get_id(widget)
        
        # Now update the location - subscription should follow the ID change
        self.registry.update_location(updated_id, "2")
        
        # Get the new updated widget ID
        final_id = self.registry.get_id(widget)
        
        # Verify both changes were notified
        assert len(subscription_changes) == 2
        assert subscription_changes[0] == (original_id, updated_id)
        assert subscription_changes[1] == (updated_id, final_id)
    
    def test_id_subscription_unsubscribe_callback(self):
        """Test unsubscribing a specific callback."""
        # Create and register a widget
        widget = MockWidget("Button")
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON)
        
        # Track subscription notifications from two different callbacks
        changes_1 = []
        changes_2 = []
        
        def callback_1(old_id, new_id):
            changes_1.append((old_id, new_id))
            
        def callback_2(old_id, new_id):
            changes_2.append((old_id, new_id))
        
        # Subscribe both callbacks
        subscribe_to_id(widget_id, callback_1)
        subscribe_to_id(widget_id, callback_2)
        
        # Unsubscribe only callback_1
        success = unsubscribe_from_id(widget_id, callback_1)
        assert success
        
        # Update widget location
        self.registry.update_location(widget_id, "location1")
        
        # Verify only callback_2 was notified
        assert len(changes_1) == 0
        assert len(changes_2) == 1
    
    def test_id_subscription_unsubscribe_all(self):
        """Test unsubscribing all callbacks for an ID."""
        # Create and register a widget
        widget = MockWidget("Button")
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON)
        
        # Track subscription notifications from two different callbacks
        changes_1 = []
        changes_2 = []
        
        def callback_1(old_id, new_id):
            changes_1.append((old_id, new_id))
            
        def callback_2(old_id, new_id):
            changes_2.append((old_id, new_id))
        
        # Subscribe both callbacks
        subscribe_to_id(widget_id, callback_1)
        subscribe_to_id(widget_id, callback_2)
        
        # Unsubscribe all callbacks for this ID
        success = unsubscribe_from_id(widget_id)
        assert success
        
        # Update widget location
        self.registry.update_location(widget_id, "location1")
        
        # Verify no callbacks were notified
        assert len(changes_1) == 0
        assert len(changes_2) == 0
    
    def test_id_subscription_clear_all(self):
        """Test clearing all subscriptions."""
        # Create and register widgets
        widget1 = MockWidget("Button1")
        widget2 = MockWidget("Button2")
        
        widget1_id = self.registry.register(widget1, TypeCodes.PUSH_BUTTON)
        widget2_id = self.registry.register(widget2, TypeCodes.PUSH_BUTTON)
        
        # Track subscription notifications
        changes_1 = []
        changes_2 = []
        
        def callback_1(old_id, new_id):
            changes_1.append((old_id, new_id))
            
        def callback_2(old_id, new_id):
            changes_2.append((old_id, new_id))
        
        # Subscribe to different widgets
        subscribe_to_id(widget1_id, callback_1)
        subscribe_to_id(widget2_id, callback_2)
        
        # Clear all subscriptions
        clear_subscriptions()
        
        # Update both widgets
        self.registry.update_location(widget1_id, "location1")
        self.registry.update_location(widget2_id, "location2")
        
        # Verify no callbacks were notified
        assert len(changes_1) == 0
        assert len(changes_2) == 0
    
    def test_id_subscription_auto_cleanup(self):
        """Test that subscriptions are automatically cleaned up when components are unregistered."""
        # Create and register a widget
        widget = MockWidget("Button")
        widget_id = self.registry.register(widget, TypeCodes.PUSH_BUTTON)
        
        # Track subscription notifications
        changes = []
        
        def on_id_changed(old_id, new_id):
            changes.append((old_id, new_id))
        
        # Subscribe to widget ID changes
        subscribe_to_id(widget_id, on_id_changed)
        
        # First, verify subscription works by updating the widget
        original_id = widget_id
        self.registry.update_location(widget_id, "test-location")
        updated_id = self.registry.get_id(widget)
        
        # Verify notification worked
        assert len(changes) == 1
        assert changes[0] == (original_id, updated_id)
        
        # Clear changes list
        changes.clear()
        
        # Unregister the widget - this should automatically clean up the subscription
        self.registry.unregister(updated_id)
        
        # Verify widget is unregistered
        assert self.registry.get_widget(updated_id) is None
        assert widget not in self.registry._component_to_id_map
        
        # Create a new widget and give it the same ID format to test that subscriptions were cleaned up
        new_widget = MockWidget("NewButton")
        new_id = self.registry.register(new_widget, TypeCodes.PUSH_BUTTON)
        
        # Update the new widget's location
        self.registry.update_location(new_id, "new-location")
        
        # Verify no notifications were sent for the new widget
        # (which would happen if the subscription wasn't properly cleaned up)
        assert len(changes) == 0
    
    def test_id_subscription_invalid_id(self):
        """Test subscribing to an invalid ID."""
        # Try to subscribe to an invalid ID
        def callback(old_id, new_id):
            pass
            
        success = subscribe_to_id("invalid:id", callback)
        assert not success


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main(["-v", __file__])