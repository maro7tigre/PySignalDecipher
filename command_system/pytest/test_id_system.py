"""
Test suite for the ID system.

This test file should be placed in the auto_test directory at the same level as the id_system directory.
Run with: python -m pytest auto_test/test_id_system.py -v

This comprehensive test suite validates all aspects of the ID system:
1. IDGenerator - Tests ID generation and updating
2. ID Utilities - Tests ID parsing and validation functions
3. IDRegistry - Tests the core registry functionality
   - Widget registration and queries
   - Observable registration and queries
   - Property registration and queries
   - Binding management
   - Container relationships
"""
#!/usr/bin/env python3
"""
Test suite for the ID system.

This test file should be placed in the auto_test directory at the same level as the id_system directory.
Run with: python -m pytest auto_test/test_id_system.py -v

This comprehensive test suite validates all aspects of the ID system:
1. IDGenerator - Tests ID generation and updating
2. ID Utilities - Tests ID parsing and validation functions
3. IDRegistry - Tests the core registry functionality
   - Widget registration and queries
   - Observable registration and queries
   - Property registration and queries
   - Binding management
   - Container relationships
"""
import sys
import os
import pytest
from unittest.mock import MagicMock

# Add parent directory to path so we can import id_system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from command_system.id_system import (
    get_id_registry, IDGenerator, TypeCodes,
    extract_type_code, extract_unique_id, extract_container_unique_id, extract_location,
    extract_widget_unique_id, extract_property_name, extract_observable_id_from_property_id,
    is_observable_id, is_widget_id, is_property_id, get_full_id, get_unique_id
)

class TestIDGenerator:
    """Tests for the IDGenerator class."""
    
    def test_generate_widget_id(self):
        """Test generating widget IDs."""
        generator = IDGenerator()
        
        # Test basic ID generation
        widget_id = generator.generate_widget_id(TypeCodes.PUSH_BUTTON)
        assert widget_id.startswith(f"{TypeCodes.PUSH_BUTTON}:")
        parts = widget_id.split(":")
        assert len(parts) == 4
        assert parts[2] == "0"  # No container
        assert parts[3] == "0"  # No location
        
        # Test with container and location
        widget_id = generator.generate_widget_id(TypeCodes.LINE_EDIT, "AB", "2")
        assert widget_id.startswith(f"{TypeCodes.LINE_EDIT}:")
        parts = widget_id.split(":")
        assert parts[2] == "AB"  # Container
        assert parts[3] == "2"  # Location
    
    def test_generate_observable_id(self):
        """Test generating observable IDs."""
        generator = IDGenerator()
        
        # Test basic ID generation
        obs_id = generator.generate_observable_id()
        assert obs_id.startswith("obs:")
        parts = obs_id.split(":")
        assert len(parts) == 4
        assert parts[2] == "0"  # No widget
        assert parts[3] == ""   # No property
        
        # Test with widget and property
        obs_id = generator.generate_observable_id("XY", "count")
        assert obs_id.startswith("obs:")
        parts = obs_id.split(":")
        assert parts[2] == "XY"     # Widget
        assert parts[3] == "count"  # Property
    
    def test_update_widget_id(self):
        """Test updating widget IDs."""
        generator = IDGenerator()
        
        # Create initial ID
        widget_id = generator.generate_widget_id(TypeCodes.PUSH_BUTTON, "AB", "2")
        
        # Update container
        updated_id = generator.update_widget_id(widget_id, "CD")
        parts = updated_id.split(":")
        assert parts[0] == TypeCodes.PUSH_BUTTON
        assert parts[1] == widget_id.split(":")[1]  # Unique ID unchanged
        assert parts[2] == "CD"  # Updated container
        assert parts[3] == "2"   # Location unchanged
        
        # Update location
        updated_id = generator.update_widget_id(widget_id, None, "3")
        parts = updated_id.split(":")
        assert parts[0] == TypeCodes.PUSH_BUTTON
        assert parts[1] == widget_id.split(":")[1]  # Unique ID unchanged
        assert parts[2] == "AB"  # Container unchanged
        assert parts[3] == "3"   # Updated location
        
        # Update both
        updated_id = generator.update_widget_id(widget_id, "CD", "3")
        parts = updated_id.split(":")
        assert parts[0] == TypeCodes.PUSH_BUTTON
        assert parts[1] == widget_id.split(":")[1]  # Unique ID unchanged
        assert parts[2] == "CD"  # Updated container
        assert parts[3] == "3"   # Updated location
    
    def test_update_observable_id(self):
        """Test updating observable IDs."""
        generator = IDGenerator()
        
        # Create initial ID
        obs_id = generator.generate_observable_id("XY", "count")
        
        # Update widget
        updated_id = generator.update_observable_id(obs_id, "ZZ")
        parts = updated_id.split(":")
        assert parts[0] == "obs"
        assert parts[1] == obs_id.split(":")[1]  # Unique ID unchanged
        assert parts[2] == "ZZ"     # Updated widget
        assert parts[3] == "count"  # Property unchanged
        
        # Update property
        updated_id = generator.update_observable_id(obs_id, None, "total")
        parts = updated_id.split(":")
        assert parts[0] == "obs"
        assert parts[1] == obs_id.split(":")[1]  # Unique ID unchanged
        assert parts[2] == "XY"     # Widget unchanged
        assert parts[3] == "total"  # Updated property
        
        # Update both
        updated_id = generator.update_observable_id(obs_id, "ZZ", "total")
        parts = updated_id.split(":")
        assert parts[0] == "obs"
        assert parts[1] == obs_id.split(":")[1]  # Unique ID unchanged
        assert parts[2] == "ZZ"     # Updated widget
        assert parts[3] == "total"  # Updated property

    def test_base62_encoding(self):
        """Test base62 encoding and decoding."""
        generator = IDGenerator()
        
        # Test various numbers
        for num in [0, 1, 10, 61, 62, 100, 1000, 999999]:
            encoded = generator._encode_to_base62(num)
            decoded = generator.decode_from_base62(encoded)
            assert decoded == num, f"Failed for number {num}"

class TestIDUtils:
    """Tests for the ID utility functions."""
    
    def test_is_widget_id(self):
        """Test widget ID detection."""
        assert is_widget_id("pb:3a:2J:2") == True
        assert is_widget_id("le:1Z:0:0") == True
        assert is_widget_id("obs:5C:1Z:name") == False
        assert is_widget_id("not_an_id") == False
        assert is_widget_id("pb:3a") == False  # Too few parts
    
    def test_is_observable_id(self):
        """Test observable ID detection."""
        assert is_observable_id("obs:5C:1Z:name") == True
        assert is_observable_id("obs:4a:0:") == True
        assert is_observable_id("pb:3a:2J:2") == False
        assert is_observable_id("not_an_id") == False
        assert is_observable_id("obs:5C") == False  # Too few parts
    
    def test_is_property_id(self):
        """Test property ID detection."""
        assert is_property_id("obs:5C:1Z:name:name") == True
        assert is_property_id("obs:4a:0::value") == True
        assert is_property_id("pb:3a:2J:2") == False
        assert is_property_id("obs:5C:1Z:name") == False  # Not a property ID
        assert is_property_id("not_an_id") == False
    
    def test_extract_type_code(self):
        """Test type code extraction."""
        assert extract_type_code("pb:3a:2J:2") == "pb"
        assert extract_type_code("obs:5C:1Z:name") == "obs"
        assert extract_type_code("t:2J:0:1") == "t"
    
    def test_extract_unique_id(self):
        """Test unique ID extraction."""
        assert extract_unique_id("pb:3a:2J:2") == "3a"
        assert extract_unique_id("obs:5C:1Z:name") == "5C"
        assert extract_unique_id("t:2J:0:1") == "2J"
    
    def test_extract_container_unique_id(self):
        """Test container unique ID extraction."""
        assert extract_container_unique_id("pb:3a:2J:2") == "2J"
        assert extract_container_unique_id("le:1Z:0:0") == "0"
        
        # Should raise error for non-widget IDs
        with pytest.raises(ValueError):
            extract_container_unique_id("obs:5C:1Z:name")
    
    def test_extract_location(self):
        """Test location extraction."""
        assert extract_location("pb:3a:2J:2") == "2"
        assert extract_location("le:1Z:0:0") == "0"
        
        # Should raise error for non-widget IDs
        with pytest.raises(ValueError):
            extract_location("obs:5C:1Z:name")
    
    def test_extract_widget_unique_id(self):
        """Test widget unique ID extraction from observable."""
        assert extract_widget_unique_id("obs:5C:1Z:name") == "1Z"
        assert extract_widget_unique_id("obs:4a:0:") == "0"
        
        # Should raise error for non-observable IDs
        with pytest.raises(ValueError):
            extract_widget_unique_id("pb:3a:2J:2")
    
    def test_extract_property_name(self):
        """Test property name extraction."""
        assert extract_property_name("obs:5C:1Z:name") == "name"
        assert extract_property_name("obs:4a:0:") == ""
        
        # Should raise error for non-observable IDs
        with pytest.raises(ValueError):
            extract_property_name("pb:3a:2J:2")
    
    def test_extract_observable_id_from_property_id(self):
        """Test extracting observable ID from property ID."""
        assert extract_observable_id_from_property_id("obs:5C:1Z:name:name") == "obs:5C:1Z:name"
        assert extract_observable_id_from_property_id("obs:4a:0::value") == "obs:4a:0:"
        assert extract_observable_id_from_property_id("not_a_property_id") is None
    
    def test_get_full_id(self):
        """Test reconstructing full IDs."""
        # Widget ID
        widget_id = get_full_id("3a", "widget", type_code="pb", container_unique_id="2J", location="2")
        assert widget_id == "pb:3a:2J:2"
        
        # Observable ID
        obs_id = get_full_id("5C", "observable", widget_unique_id="1Z", property_name="name")
        assert obs_id == "obs:5C:1Z:name"
        
        # Invalid type
        with pytest.raises(ValueError):
            get_full_id("X", "invalid_type")
    
    def test_get_unique_id(self):
        """Test extracting unique ID part."""
        assert get_unique_id("pb:3a:2J:2") == "3a"
        assert get_unique_id("obs:5C:1Z:name") == "5C"


class TestIDRegistry:
    """Tests for the IDRegistry class."""
    
    @pytest.fixture
    def registry(self):
        """Set up a fresh registry for each test."""
        registry = get_id_registry()
        registry.clear()
        return registry
    
    @pytest.fixture
    def widgets(self):
        """Create mock widgets for testing."""
        return {
            "button": MagicMock(),
            "text": MagicMock(),
            "container": MagicMock(),
        }
    
    @pytest.fixture
    def observables(self):
        """Create mock observables for testing."""
        return {
            "person": MagicMock(),
            "counter": MagicMock(),
            "name_prop": MagicMock(observable=MagicMock(), name="name")
        }
    
    def test_register_widget(self, registry, widgets):
        """Test registering widgets."""
        # Register basic widget
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        assert is_widget_id(button_id)
        assert extract_type_code(button_id) == TypeCodes.PUSH_BUTTON
        
        # Register with container
        container_id = registry.register_widget(widgets["container"], TypeCodes.TAB_CONTAINER)
        text_id = registry.register_widget(widgets["text"], TypeCodes.TEXT_EDIT, None, container_id, "1")
        
        assert is_widget_id(text_id)
        assert extract_type_code(text_id) == TypeCodes.TEXT_EDIT
        assert extract_container_unique_id(text_id) == extract_unique_id(container_id)
        assert extract_location(text_id) == "1"
        
        # Test lookup
        assert registry.get_widget(button_id) == widgets["button"]
        assert registry.get_widget(text_id) == widgets["text"]
        assert registry.get_widget(container_id) == widgets["container"]
        
        # Test ID lookup
        assert registry.get_widget_id(widgets["button"]) == button_id
        assert registry.get_widget_id(widgets["text"]) == text_id
        assert registry.get_widget_id(widgets["container"]) == container_id
    
    def test_get_widget_flexible(self, registry, widgets):
        """Test flexible widget retrieval."""
        # Register widgets
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        container_id = registry.register_widget(widgets["container"], TypeCodes.TAB_CONTAINER)
        text_id = registry.register_widget(widgets["text"], TypeCodes.TEXT_EDIT, None, container_id, "1")
        
        # Test different parameter combinations
        # By ID
        assert registry.get_widget(button_id) == widgets["button"]
        assert registry.get_widget(widget_id=button_id) == widgets["button"]
        
        # By container
        container_widgets = registry.get_widget(container_id=container_id)
        assert len(container_widgets) == 1
        assert widgets["text"] in container_widgets
        
        # By type
        button_widgets = registry.get_widget(type_code=TypeCodes.PUSH_BUTTON)
        assert len(button_widgets) == 1
        assert widgets["button"] in button_widgets
        
        # By location
        location_widgets = registry.get_widget(location="1")
        assert len(location_widgets) == 1
        assert widgets["text"] in location_widgets
        
        # Combine parameters
        combined_widgets = registry.get_widget(container_id=container_id, location="1")
        assert len(combined_widgets) == 1
        assert widgets["text"] in combined_widgets
    
    def test_get_widget_id_flexible(self, registry, widgets):
        """Test flexible widget ID retrieval."""
        # Register widgets
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        container_id = registry.register_widget(widgets["container"], TypeCodes.TAB_CONTAINER)
        text_id = registry.register_widget(widgets["text"], TypeCodes.TEXT_EDIT, None, container_id, "1")
        
        # Test different parameter combinations
        # By widget
        assert registry.get_widget_id(widgets["button"]) == button_id
        assert registry.get_widget_id(widget=widgets["button"]) == button_id
        
        # By container
        container_widget_ids = registry.get_widget_id(container_id=container_id)
        assert len(container_widget_ids) == 1
        assert text_id in container_widget_ids
        
        # By type
        button_widget_ids = registry.get_widget_id(type_code=TypeCodes.PUSH_BUTTON)
        assert len(button_widget_ids) == 1
        assert button_id in button_widget_ids
        
        # By location
        location_widget_ids = registry.get_widget_id(location="1")
        assert len(location_widget_ids) == 1
        assert text_id in location_widget_ids
        
        # Combine parameters
        combined_widget_ids = registry.get_widget_id(container_id=container_id, location="1")
        assert len(combined_widget_ids) == 1
        assert text_id in combined_widget_ids
    
    def test_update_widget(self, registry, widgets):
        """Test updating widget properties."""
        # Register widgets
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        container_id = registry.register_widget(widgets["container"], TypeCodes.TAB_CONTAINER)
        
        # Update container
        assert registry.update_widget(button_id, container_id=container_id)
        updated_button_id = registry.get_widget_id(widgets["button"])
        assert extract_container_unique_id(updated_button_id) == extract_unique_id(container_id)
        
        # Update location
        assert registry.update_widget(updated_button_id, location="2")
        final_button_id = registry.get_widget_id(widgets["button"])
        assert extract_location(final_button_id) == "2"
        
        # Verify container is still correct
        assert extract_container_unique_id(final_button_id) == extract_unique_id(container_id)
    
    def test_unregister_widget(self, registry, widgets):
        """Test unregistering widgets."""
        # Register widget
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        
        # Verify registered
        assert registry.get_widget(button_id) == widgets["button"]
        
        # Unregister
        assert registry.unregister_widget(widgets["button"])
        assert registry.get_widget(button_id) is None
        assert registry.get_widget_id(widgets["button"]) is None
        
        # Test unregister by ID
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        assert registry.unregister_widget(button_id)
        assert registry.get_widget(button_id) is None
    
    def test_container_methods(self, registry, widgets):
        """Test container-related methods."""
        # Register widgets
        container_id = registry.register_widget(widgets["container"], TypeCodes.TAB_CONTAINER)
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON, None, container_id, "1")
        
        # Test get_container
        assert registry.get_container(widget_id=button_id) == widgets["container"]
        assert registry.get_container(container_id=container_id) == widgets["container"]
        
        # Test get_container_id
        assert registry.get_container_id(widget_id=button_id) == container_id
        assert registry.get_container_id(container=widgets["container"]) == container_id
        
        # Legacy methods
        assert registry.get_container_from_widget_id(button_id) == widgets["container"]
        assert registry.get_container_id_from_widget_id(button_id) == container_id
    
    def test_register_observable(self, registry, observables, widgets):
        """Test registering observables."""
        # Register basic observable
        person_id = registry.register_observable(observables["person"])
        assert is_observable_id(person_id)
        
        # Register with parent widget
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        counter_id = registry.register_observable(observables["counter"], None, button_id)
        
        assert is_observable_id(counter_id)
        assert extract_widget_unique_id(counter_id) == extract_unique_id(button_id)
        
        # Test lookup
        assert registry.get_observable(person_id) == observables["person"]
        assert registry.get_observable(counter_id) == observables["counter"]
        
        # Test ID lookup
        assert registry.get_observable_id(observables["person"]) == person_id
        assert registry.get_observable_id(observables["counter"]) == counter_id
    
    def test_get_observable_flexible(self, registry, observables, widgets):
        """Test flexible observable retrieval."""
        # Register objects
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        person_id = registry.register_observable(observables["person"])
        counter_id = registry.register_observable(observables["counter"], None, button_id)
        
        # Register property
        name_prop_id = registry.register_property("name", person_id, observables["name_prop"])
        
        # Test different parameter combinations
        # By ID
        assert registry.get_observable(person_id) == observables["person"]
        assert registry.get_observable(observable_id=person_id) == observables["person"]
        
        # By parent
        parent_observables = registry.get_observable(parent_id=button_id)
        assert len(parent_observables) == 1
        assert observables["counter"] in parent_observables
        
        # By property
        prop_observable = registry.get_observable(property_id=name_prop_id)
        assert prop_observable == observables["person"]
    
    def test_get_observable_id_flexible(self, registry, observables, widgets):
        """Test flexible observable ID retrieval."""
        # Register objects
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        person_id = registry.register_observable(observables["person"])
        counter_id = registry.register_observable(observables["counter"], None, button_id)
        
        # Test different parameter combinations
        # By observable
        assert registry.get_observable_id(observables["person"]) == person_id
        assert registry.get_observable_id(observable=observables["person"]) == person_id
        
        # By parent
        parent_observable_ids = registry.get_observable_id(parent_id=button_id)
        assert len(parent_observable_ids) == 1
        assert counter_id in parent_observable_ids
        
        # By property name
        # We would need to set up an observable with a property name in its ID for this
    
    def test_update_observable(self, registry, observables, widgets):
        """Test updating observable properties."""
        # Register objects
        person_id = registry.register_observable(observables["person"])
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        
        # Update parent
        assert registry.update_observable(person_id, parent_id=button_id)
        updated_person_id = registry.get_observable_id(observables["person"])
        assert extract_widget_unique_id(updated_person_id) == extract_unique_id(button_id)
        
        # Alternative method
        text_id = registry.register_widget(widgets["text"], TypeCodes.TEXT_EDIT)
        assert registry.update_observable_widget(updated_person_id, text_id)
        final_person_id = registry.get_observable_id(observables["person"])
        assert extract_widget_unique_id(final_person_id) == extract_unique_id(text_id)
    
    def test_unregister_observable(self, registry, observables):
        """Test unregistering observables."""
        # Register observable
        person_id = registry.register_observable(observables["person"])
        
        # Verify registered
        assert registry.get_observable(person_id) == observables["person"]
        
        # Unregister
        assert registry.unregister_observable(observables["person"])
        assert registry.get_observable(person_id) is None
        assert registry.get_observable_id(observables["person"]) is None
        
        # Test unregister by ID
        person_id = registry.register_observable(observables["person"])
        assert registry.unregister_observable(person_id)
        assert registry.get_observable(person_id) is None
    
    def test_register_property(self, registry, observables, widgets):
        """Test registering properties."""
        # Register objects
        person_id = registry.register_observable(observables["person"])
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        
        # Register property with observable ID
        name_prop_id = registry.register_property("name", person_id)
        assert is_property_id(name_prop_id)
        assert name_prop_id == f"{person_id}:name"
        
        # Register with property object
        email_prop_id = registry.register_property("email", None, observables["name_prop"])
        assert is_property_id(email_prop_id)
        
        # Register with widget binding
        age_prop_id = registry.register_property("age", person_id, None, button_id)
        assert is_property_id(age_prop_id)
        
        # Verify bindings
        prop_info = registry.get_property(age_prop_id)
        assert button_id in prop_info["bound_widgets"]
    
    def test_get_property(self, registry, observables, widgets):
        """Test getting property information."""
        # Register objects
        person_id = registry.register_observable(observables["person"])
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        text_id = registry.register_widget(widgets["text"], TypeCodes.TEXT_EDIT)
        
        # Register properties and bind widgets
        name_prop_id = registry.register_property("name", person_id, None, button_id)
        email_prop_id = registry.register_property("email", person_id, None, text_id)
        
        # Test getting by ID
        name_info = registry.get_property(name_prop_id)
        assert name_info["property_name"] == "name"
        assert name_info["observable_id"] == person_id
        assert button_id in name_info["bound_widgets"]
        
        # Test getting by observable + name
        email_info = registry.get_property(observable_id=person_id, property_name="email")
        assert email_info["property_name"] == "email"
        assert email_info["observable_id"] == person_id
        assert text_id in email_info["bound_widgets"]
        
        # Test getting all for observable
        all_props = registry.get_property(observable_id=person_id)
        assert len(all_props) == 2
        prop_names = [p["property_name"] for p in all_props]
        assert "name" in prop_names
        assert "email" in prop_names
        
        # Test getting all for widget
        button_props = registry.get_property(widget_id=button_id)
        assert len(button_props) == 1
        assert button_props[0]["property_name"] == "name"
        
        text_props = registry.get_property(widget_id=text_id)
        assert len(text_props) == 1
        assert text_props[0]["property_name"] == "email"
    
    def test_get_property_id(self, registry, observables):
        """Test getting property ID."""
        # Register objects
        person_id = registry.register_observable(observables["person"])
        
        # Register property
        name_prop_id = registry.register_property("name", person_id)
        
        # Test getting by observable + name
        prop_id = registry.get_property_id(person_id, "name")
        assert prop_id == name_prop_id
        
        # Test getting by property object
        # This would require proper setup of the property object
    
    def test_bind_unbind_widget(self, registry, observables, widgets):
        """Test binding and unbinding widgets to properties."""
        # Register objects
        person_id = registry.register_observable(observables["person"])
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        text_id = registry.register_widget(widgets["text"], TypeCodes.TEXT_EDIT)
        
        # Register property
        name_prop_id = registry.register_property("name", person_id)
        
        # Bind widget
        assert registry.bind_widget(name_prop_id, button_id)
        
        # Verify binding
        prop_info = registry.get_property(name_prop_id)
        assert button_id in prop_info["bound_widgets"]
        assert prop_info["is_controller"].get(button_id) == False
        
        # Bind as controller
        assert registry.bind_widget(name_prop_id, text_id, is_controller=True)
        
        # Verify binding
        prop_info = registry.get_property(name_prop_id)
        assert text_id in prop_info["bound_widgets"]
        assert prop_info["is_controller"].get(text_id) == True
        
        # Unbind widget
        assert registry.unbind_widget(name_prop_id, button_id)
        
        # Verify unbinding
        prop_info = registry.get_property(name_prop_id)
        assert button_id not in prop_info["bound_widgets"]
        assert text_id in prop_info["bound_widgets"]
    
    def test_update_property(self, registry, observables, widgets):
        """Test updating property attributes."""
        # Register objects
        person_id = registry.register_observable(observables["person"])
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        text_id = registry.register_widget(widgets["text"], TypeCodes.TEXT_EDIT)
        
        # Register property and bind widgets
        name_prop_id = registry.register_property("name", person_id)
        registry.bind_widget(name_prop_id, button_id)
        registry.bind_widget(name_prop_id, text_id)
        
        # Update controller
        assert registry.update_property(name_prop_id, text_id)
        
        # Verify update
        prop_info = registry.get_property(name_prop_id)
        assert prop_info["is_controller"].get(text_id) == True
        assert prop_info["is_controller"].get(button_id) == False
    
    def test_unregister_property(self, registry, observables, widgets):
        """Test unregistering properties."""
        # Register objects
        person_id = registry.register_observable(observables["person"])
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        
        # Register property and bind widget
        name_prop_id = registry.register_property("name", person_id, None, button_id)
        
        # Verify registered
        assert registry.get_property(name_prop_id) is not None
        
        # Unregister
        assert registry.unregister_property(name_prop_id)
        assert registry.get_property(name_prop_id) is None
        
        # Verify widget binding removed
        widget_props = registry.get_property(widget_id=button_id)
        assert len(widget_props) == 0
    
    def test_bind_widget_to_observable(self, registry, observables, widgets):
        """Test direct widget-observable binding."""
        # Register objects
        person_id = registry.register_observable(observables["person"])
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        
        # Bind widget to observable
        registry.bind_widget_to_observable(button_id, person_id)
        
        # Verify binding
        widget_obs_ids = registry.get_bound_observable_ids(button_id)
        assert person_id in widget_obs_ids
        
        obs_widget_ids = registry.get_bound_widget_ids(person_id)
        assert button_id in obs_widget_ids
        
        # Test get_bound_observables and get_bound_widgets
        bound_observables = registry.get_bound_observables(button_id)
        assert observables["person"] in bound_observables
        
        bound_widgets = registry.get_bound_widgets(person_id)
        assert widgets["button"] in bound_widgets
        
        # Unbind widget from observable
        registry.unbind_widget_from_observable(button_id, person_id)
        
        # Verify unbinding
        widget_obs_ids = registry.get_bound_observable_ids(button_id)
        assert person_id not in widget_obs_ids
        
        obs_widget_ids = registry.get_bound_widget_ids(person_id)
        assert button_id not in obs_widget_ids
    
    def test_get_bindings(self, registry, observables, widgets):
        """Test getting binding information."""
        # Register objects
        person_id = registry.register_observable(observables["person"])
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        text_id = registry.register_widget(widgets["text"], TypeCodes.TEXT_EDIT)
        
        # Direct binding
        registry.bind_widget_to_observable(button_id, person_id)
        
        # Property binding
        name_prop_id = registry.register_property("name", person_id, None, text_id)
        
        # Get bindings by widget
        button_bindings = registry.get_bindings(widget_id=button_id)
        assert len(button_bindings) == 1
        assert button_bindings[0]["observable_id"] == person_id
        assert button_bindings[0]["widget_id"] == button_id
        assert button_bindings[0]["property_id"] is None
        
        text_bindings = registry.get_bindings(widget_id=text_id)
        assert len(text_bindings) == 1
        assert text_bindings[0]["observable_id"] == person_id
        assert text_bindings[0]["widget_id"] == text_id
        assert text_bindings[0]["property_id"] == name_prop_id
        
        # Get bindings by observable
        person_bindings = registry.get_bindings(observable_id=person_id)
        assert len(person_bindings) == 2
        
        widget_ids = [b["widget_id"] for b in person_bindings]
        assert button_id in widget_ids
        assert text_id in widget_ids
        
        # Get bindings by property
        prop_bindings = registry.get_bindings(property_id=name_prop_id)
        assert len(prop_bindings) == 1
        assert prop_bindings[0]["observable_id"] == person_id
        assert prop_bindings[0]["widget_id"] == text_id
        assert prop_bindings[0]["property_id"] == name_prop_id
    
    def test_controlling_widget(self, registry, observables, widgets):
        """Test controlling widget methods."""
        # Register objects
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        
        # Create observable with controlling widget
        counter_id = registry.register_observable(observables["counter"], None, button_id)
        
        # Test get_controlling_widget_id
        ctrl_id = registry.get_controlling_widget_id(counter_id)
        assert ctrl_id == button_id
        
        # Test get_controlling_widget
        ctrl = registry.get_controlling_widget(counter_id)
        assert ctrl == widgets["button"]
    
    def test_clear(self, registry, observables, widgets):
        """Test clearing the registry."""
        # Register objects
        button_id = registry.register_widget(widgets["button"], TypeCodes.PUSH_BUTTON)
        person_id = registry.register_observable(observables["person"])
        name_prop_id = registry.register_property("name", person_id, None, button_id)
        
        # Verify registrations
        assert registry.get_widget(button_id) == widgets["button"]
        assert registry.get_observable(person_id) == observables["person"]
        assert registry.get_property(name_prop_id) is not None
        
        # Clear registry
        registry.clear()
        
        # Verify all cleared
        assert registry.get_widget(button_id) is None
        assert registry.get_observable(person_id) is None
        assert registry.get_property(name_prop_id) is None

if __name__ == "__main__":
    """
    Allow running the test file directly.
    
    Usage:
        python auto_test/test_id_system.py
    """
    pytest.main([__file__, "-v"])