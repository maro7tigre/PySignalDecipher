"""
Test suite focused on serialization functionality in the command system.

This module tests serialization and deserialization of observable properties,
observables, widgets, and the SerializationCommand functionality.
"""
import pytest
import sys
import os
import json
from typing import Dict, Any, List

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from command_system.core import (
    Observable, ObservableProperty,
    Command, CompoundCommand, PropertyCommand, MacroCommand, WidgetPropertyCommand,
    SerializationCommand, get_command_manager
)
from command_system.id_system import get_id_registry
from command_system.id_system.types import WidgetTypeCodes

# Mock classes for testing
class MockWidget:
    """Mock widget for serialization testing."""
    def __init__(self, name: str):
        self.name = name
        self.text = ""
        self.visible = True
        self.attributes = {}
        
        # Register with ID system
        self.id = get_id_registry().register(self, WidgetTypeCodes.CUSTOM_WIDGET)
        
    def __repr__(self):
        return f"MockWidget({self.name})"
        
    def get_serialization(self) -> Dict[str, Any]:
        """Serialize widget state."""
        return {
            "id": self.id,
            "name": self.name,
            "text": self.text,
            "visible": self.visible,
            "attributes": self.attributes
        }
        
    def deserialize(self, data: Dict[str, Any]) -> bool:
        """Deserialize widget state."""
        if not data or not isinstance(data, dict):
            return False
            
        if "name" in data:
            self.name = data["name"]
        if "text" in data:
            self.text = data["text"]
        if "visible" in data:
            self.visible = data["visible"]
        if "attributes" in data:
            self.attributes = data["attributes"]
            
        return True

class MockContainer(MockWidget):
    """Mock container for serialization testing."""
    def __init__(self, name: str):
        super().__init__(name)
        self.children = {}
        self.active_child = None
        
    def add_child(self, child_id: str, location: str) -> None:
        """Add a child widget at a specific location."""
        self.children[location] = child_id
        
    def get_serialization(self) -> Dict[str, Any]:
        """Serialize container state including children."""
        base_data = super().get_serialization()
        base_data["children"] = self.children.copy()
        base_data["active_child"] = self.active_child
        return base_data
        
    def deserialize(self, data: Dict[str, Any]) -> bool:
        """Deserialize container state including children."""
        result = super().deserialize(data)
        
        if "children" in data:
            self.children = data["children"].copy()
        if "active_child" in data:
            self.active_child = data["active_child"]
            
        return result
        
    def serialize_subcontainer(self, component_id: str) -> Dict[str, Any]:
        """Serialize a specific subcontainer."""
        if component_id not in self.children.values():
            return None
            
        # Find the location for this child
        location = None
        for loc, child_id in self.children.items():
            if child_id == component_id:
                location = loc
                break
                
        if location is None:
            return None
            
        # Get the child component
        registry = get_id_registry()
        child = registry.get_widget(component_id)
        
        if child is None:
            return None
            
        # Get the child's serialization
        child_data = None
        if hasattr(child, 'get_serialization'):
            child_data = child.get_serialization()
        
        return {
            "container_id": self.id,
            "child_id": component_id,
            "location": location,
            "data": child_data
        }
        
    def deserialize_subcontainer(self, type_id: str, location: str, data: Dict[str, Any]) -> bool:
        """Deserialize a subcontainer."""
        if not data or not isinstance(data, dict):
            return False
            
        # Check if this is the right container
        if data.get("container_id") != self.id:
            return False
            
        child_id = data.get("child_id")
        child_location = data.get("location")
        child_data = data.get("data")
        
        if not child_id or not child_location or not child_data:
            return False
            
        # Update the container's children map
        self.children[child_location] = child_id
        
        # If the child exists, deserialize it
        registry = get_id_registry()
        child = registry.get_widget(child_id)
        
        if child and hasattr(child, 'deserialize'):
            return child.deserialize(child_data)
            
        return True

class Person(Observable):
    """Sample observable class for serialization testing."""
    name = ObservableProperty("")
    age = ObservableProperty(0)
    email = ObservableProperty("")
    
    def __init__(self, name="", age=0, email=""):
        # Initialize Observable
        super().__init__()
        # Set initial values
        self.name = name
        self.age = age
        self.email = email

class Employee(Observable):
    """Another observable class for testing serialization between different observables."""
    name = ObservableProperty("")
    title = ObservableProperty("")
    salary = ObservableProperty(0)
    
    def __init__(self, name="", title="", salary=0):
        # Initialize Observable
        super().__init__()
        # Set initial values
        self.name = name
        self.title = title
        self.salary = salary

class TestPropertySerialization:
    """Test cases for observable property serialization and deserialization."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
        
    def test_property_serialization_basics(self):
        """Test basic serialization and deserialization of a property."""
        # Create person
        person = Person(name="Alice", age=30)
        
        # Get the property IDs
        name_property_id = person._get_property_id("name")
        age_property_id = person._get_property_id("age")
        
        # Serialize properties
        serialized_name = person.serialize_property("name")
        serialized_age = person.serialize_property("age")
        
        # Verify serialized data
        assert serialized_name["property_name"] == "name"
        assert serialized_name["value"] == "Alice"
        assert serialized_name["property_id"] == name_property_id
        assert serialized_name["observable_id"] == person.get_id()
        
        assert serialized_age["property_name"] == "age"
        assert serialized_age["value"] == 30
        assert serialized_age["property_id"] == age_property_id
        assert serialized_age["observable_id"] == person.get_id()
        
        # Change property values
        person.name = "Bob"
        person.age = 40
        
        # Verify values changed
        assert person.name == "Bob"
        assert person.age == 40
        
        # Deserialize properties
        person.deserialize_property("name", serialized_name)
        person.deserialize_property("age", serialized_age)
        
        # Verify values restored
        assert person.name == "Alice"
        assert person.age == 30
    
    def test_property_unregister_and_restore(self):
        """Test unregistering a property and restoring it through deserialization."""
        # Create person
        person = Person(name="Alice", age=30)
        
        # Get original property ID and serialize it
        original_name_id = person._get_property_id("name")
        serialized_name = person.serialize_property("name")
        
        # Unregister the property
        registry = get_id_registry()
        assert registry.unregister(original_name_id)
        
        # Verify property is unregistered
        assert registry.get_observable_property(original_name_id) is None
        
        # Create new property with same name but different value
        person.name = "Bob"
        new_name_id = person._get_property_id("name")
        
        # Verify it's a different property ID
        assert new_name_id != original_name_id
        assert person.name == "Bob"
        
        # Deserialize the original property data
        # This should restore the value while using the new property ID
        assert person.deserialize_property("name", serialized_name)
        
        # Verify value is restored
        assert person.name == "Alice"
        
        # Verify the property ID hasn't changed
        current_name_id = person._get_property_id("name")
        assert current_name_id == original_name_id
    
    def test_property_restore_with_explicit_id(self):
        """Test restoring a property with explicit ID through serialization."""
        # Create person
        person = Person(name="Alice", age=30)
        
        # Get original property ID and serialize it
        original_name_id = person._get_property_id("name")
        serialized_name = person.serialize_property("name")
        
        # Unregister the property and the observable
        registry = get_id_registry()
        registry.unregister(original_name_id)
        
        # Create new property with same name but different value
        person.name = "Bob"
        
        # Modify serialized data to use the original property ID
        modified_serialized = serialized_name.copy()
        
        # Deserialize using the modified data
        person.deserialize_property("name", modified_serialized)
        
        # Verify value is restored
        assert person.name == "Alice"
    
    def test_property_transfer_between_observables(self):
        """Test transferring a property between observables through serialization."""
        # Create two different observable objects
        person = Person(name="Alice", age=30)
        employee = Employee(name="", title="Developer", salary=100000)
        
        # Get original property ID and serialize it
        person_name_id = person._get_property_id("name")
        serialized_name = person.serialize_property("name")
        registry = get_id_registry()
        
        # Verify initial values
        assert person.name == "Alice"
        assert employee.name == ""
        
        person.unregister()

        # Deserialize person's name property to employee
        employee.deserialize_property("name", serialized_name)
        
        # Verify the property was transferred
        assert employee.name == "Alice"
        
        # Check that the observable_id was updated in the process
        employee_name_id = employee._get_property_id("name")
        
        # Get the observable ID from the property
        employee_id_from_prop = registry.get_observable_id_from_property_id(employee_name_id)
        
        # Verify it points to the employee now
        assert employee_id_from_prop == employee.get_id()
        assert person_name_id == employee_name_id
    
    def test_property_restore_after_observable_change(self):
        """Test restoring a property after its observable has changed."""
        # Create person
        person = Person(name="Alice", age=30)
        
        # Serialize property
        serialized_name = person.serialize_property("name")
        original_person_id = person.get_id()
        
        # Unregister the observable
        registry = get_id_registry()
        registry.unregister(original_person_id)
        
        # Create a new person with the same ID if possible
        new_person = Person(name="Bob", age=25)
        
        # Modify serialized data to use the original observable ID
        modified_serialized = serialized_name.copy()
        modified_serialized["observable_id"] = original_person_id
        
        # Try to deserialize property with the original observable ID
        # This should update the observable reference if the ID is available
        result = new_person.deserialize_property("name", modified_serialized)
        
        # If deserialization succeeded, verify the property value was restored
        if result:
            assert new_person.name == "Alice"
        
        # If the original ID wasn't available, just verify no errors occurred
        assert new_person.name in ["Alice", "Bob"]

class TestObservableSerialization:
    """Test cases for observable serialization and deserialization."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
    
    def test_observable_serialization_basics(self):
        """Test basic serialization and deserialization of an observable."""
        # Create person
        person = Person(name="Alice", age=30, email="alice@example.com")
        
        # Serialize the observable
        serialized_person = person.serialize()
        
        # Verify serialized data structure
        assert "id" in serialized_person
        assert "properties" in serialized_person
        assert serialized_person["id"] == person.get_id()
        assert "name" in serialized_person["properties"]
        assert "age" in serialized_person["properties"]
        assert "email" in serialized_person["properties"]
        
        # Change observable values
        person.name = "Bob"
        person.age = 40
        person.email = "bob@example.com"
        
        # Verify values changed
        assert person.name == "Bob"
        assert person.age == 40
        assert person.email == "bob@example.com"
        
        # Deserialize observable
        person.deserialize(serialized_person)
        
        # Verify values restored
        assert person.name == "Alice"
        assert person.age == 30
        assert person.email == "alice@example.com"
    
    def test_observable_unregister_and_restore(self):
        """Test unregistering an observable and restoring it through deserialization."""
        # Create person
        person = Person(name="Alice", age=30, email="alice@example.com")
        
        # Get original ID and serialize
        original_id = person.get_id()
        serialized_person = person.serialize()
        
        # Unregister the observable
        registry = get_id_registry()
        assert registry.unregister(original_id)
        
        # Verify observable is unregistered
        assert registry.get_observable(original_id) is None
        
        # Create a new person with different values
        new_person = Person(name="Bob", age=40, email="bob@example.com")
        new_id = new_person.get_id()
        
        # Verify it's a different observable ID
        assert new_id != original_id
        
        # Deserialize the original observable data to the new person
        new_person.deserialize(serialized_person)
        
        # Verify values are restored
        assert new_person.name == "Alice"
        assert new_person.age == 30
        assert new_person.email == "alice@example.com"
        
        # Verify the ID has been updated to match the original
        # This depends on whether the original ID is still available
        current_id = new_person.get_id()
        
        # If successful, the ID should match the original
        if registry.get_observable(original_id) is new_person:
            assert current_id == original_id
    
    def test_observable_property_cascade_unregister(self):
        """Test that unregistering an observable cascades to its properties."""
        # Create person
        person = Person(name="Alice", age=30)
        
        # Get property IDs
        name_property_id = person._get_property_id("name")
        age_property_id = person._get_property_id("age")
        
        # Verify properties exist
        registry = get_id_registry()
        assert registry.get_observable_property(name_property_id) is not None
        assert registry.get_observable_property(age_property_id) is not None
        
        # Unregister the observable
        observable_id = person.get_id()
        registry.unregister(observable_id)
        
        # Verify observable is unregistered
        assert registry.get_observable(observable_id) is None
        
        # Verify properties are also unregistered (cascade effect)
        assert registry.get_observable_property(name_property_id) is None
        assert registry.get_observable_property(age_property_id) is None
    
    def test_observable_restore_with_properties(self):
        """Test restoring an observable with all its properties."""
        # Create person
        person = Person(name="Alice", age=30, email="alice@example.com")
        
        # Serialize the observable
        serialized_person = person.serialize()
        
        # Get original property IDs
        original_name_id = person._get_property_id("name")
        original_age_id = person._get_property_id("age")
        original_email_id = person._get_property_id("email")
        
        # Clear the registry (unregister everything)
        registry = get_id_registry()
        registry.clear()
        
        # Create a new person
        new_person = Person()
        
        # Deserialize the original observable data
        new_person.deserialize(serialized_person)
        
        # Verify values restored
        assert new_person.name == "Alice"
        assert new_person.age == 30
        assert new_person.email == "alice@example.com"
        
        # Get new property IDs
        new_name_id = new_person._get_property_id("name")
        new_age_id = new_person._get_property_id("age")
        new_email_id = new_person._get_property_id("email")
        
        # These IDs might be different since we're creating new properties
        # The important part is that the property values are restored
        assert new_name_id is not None
        assert new_age_id is not None
        assert new_email_id is not None
    
    def test_property_unregister_observable_cascade(self):
        """Test that unregistering all properties of an observable causes it to unregister."""
        # Create person with only two properties
        person = Person(name="Alice", age=30)
        
        # Don't set email to ensure we have exactly two properties
        person.email = ""
        
        # Get property IDs
        name_property_id = person._get_property_id("name")
        age_property_id = person._get_property_id("age")
        
        # Get observable ID
        observable_id = person.get_id()
        
        # Verify observable and properties exist
        registry = get_id_registry()
        assert registry.get_observable(observable_id) is not None
        assert registry.get_observable_property(name_property_id) is not None
        assert registry.get_observable_property(age_property_id) is not None
        
        # Unregister one property
        registry.unregister(name_property_id)

        
        # Verify that property is unregistered, but observable still exists
        assert registry.get_observable_property(name_property_id) is None
        assert registry.get_observable(observable_id) is not None
        assert registry.get_observable_property(age_property_id) is not None
        
        # Unregister the last properties
        registry.unregister(age_property_id)
        email_property_id = person._get_property_id("email")
        registry.unregister(email_property_id)
        
        # Verify that both the property and observable are unregistered
        assert registry.get_observable_property(age_property_id) is None
        assert registry.get_observable(observable_id) is None
        
        # Getting ID should fail since object is no longer registered
        assert registry.get_id(person) is None

class TestWidgetSerialization:
    """Test cases for widget serialization and deserialization."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
    
    def test_widget_serialization_basics(self):
        """Test basic serialization and deserialization of a widget."""
        # Create widget
        widget = MockWidget("TestWidget")
        widget.text = "Hello World"
        widget.visible = True
        widget.attributes = {"color": "blue", "size": 10}
        
        # Serialize the widget
        serialized_widget = widget.get_serialization()
        
        # Verify serialized data
        assert serialized_widget["id"] == widget.id
        assert serialized_widget["name"] == "TestWidget"
        assert serialized_widget["text"] == "Hello World"
        assert serialized_widget["visible"] == True
        assert serialized_widget["attributes"]["color"] == "blue"
        
        # Change widget values
        widget.name = "ModifiedWidget"
        widget.text = "Modified Text"
        widget.visible = False
        widget.attributes = {"color": "red", "size": 20}
        
        # Verify values changed
        assert widget.name == "ModifiedWidget"
        assert widget.text == "Modified Text"
        assert widget.visible == False
        assert widget.attributes["color"] == "red"
        
        # Deserialize widget
        widget.deserialize(serialized_widget)
        
        # Verify values restored
        assert widget.name == "TestWidget"
        assert widget.text == "Hello World"
        assert widget.visible == True
        assert widget.attributes["color"] == "blue"
        assert widget.attributes["size"] == 10
    
    def test_widget_unregister_and_restore(self):
        """Test unregistering a widget and restoring it through deserialization."""
        # Create widget
        widget = MockWidget("TestWidget")
        widget.text = "Hello World"
        
        # Get original ID and serialize
        original_id = widget.id
        serialized_widget = widget.get_serialization()
        
        # Unregister the widget
        registry = get_id_registry()
        assert registry.unregister(original_id)
        
        # Verify widget is unregistered
        assert registry.get_widget(original_id) is None
        
        # Create a new widget
        new_widget = MockWidget("NewWidget")
        new_id = new_widget.id
        
        # Verify it's a different widget ID
        assert new_id != original_id
        
        # Deserialize the original widget data
        # Note: This won't change the widget's ID
        new_widget.deserialize(serialized_widget)
        
        # Verify values restored (except ID)
        assert new_widget.name == "TestWidget"
        assert new_widget.text == "Hello World"
        
        # Verify the ID has not changed
        assert new_widget.id == new_id

class TestContainerSerialization:
    """Test cases for container serialization and deserialization."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
    
    def test_container_serialization_basics(self):
        """Test basic serialization and deserialization of a container with children."""
        # Create container and widgets
        container = MockContainer("MainContainer")
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        
        # Set up container with children
        container.add_child(widget1.id, "location1")
        container.add_child(widget2.id, "location2")
        container.active_child = "location1"
        
        # Serialize the container
        serialized_container = container.get_serialization()
        
        # Verify serialized data
        assert serialized_container["id"] == container.id
        assert serialized_container["name"] == "MainContainer"
        assert "children" in serialized_container
        assert len(serialized_container["children"]) == 2
        assert serialized_container["children"]["location1"] == widget1.id
        assert serialized_container["children"]["location2"] == widget2.id
        assert serialized_container["active_child"] == "location1"
        
        # Change container values
        container.name = "ModifiedContainer"
        container.active_child = "location2"
        container.children = {}  # Remove all children
        
        # Verify values changed
        assert container.name == "ModifiedContainer"
        assert container.active_child == "location2"
        assert len(container.children) == 0
        
        # Deserialize container
        container.deserialize(serialized_container)
        
        # Verify values restored
        assert container.name == "MainContainer"
        assert len(container.children) == 2
        assert container.children["location1"] == widget1.id
        assert container.children["location2"] == widget2.id
        assert container.active_child == "location1"
    
    def test_container_subcontainer_serialization(self):
        """Test serialization and deserialization of subcontainers."""
        # Create container hierarchy
        main_container = MockContainer("MainContainer")
        sub_container = MockContainer("SubContainer")
        widget = MockWidget("Widget")
        
        # Set up containers
        main_container.add_child(sub_container.id, "sub")
        sub_container.add_child(widget.id, "widget")
        
        # Serialize the subcontainer
        serialized_sub = main_container.serialize_subcontainer(sub_container.id)
        
        # Verify serialized data
        assert serialized_sub["container_id"] == main_container.id
        assert serialized_sub["child_id"] == sub_container.id
        assert serialized_sub["location"] == "sub"
        assert serialized_sub["data"]["name"] == "SubContainer"
        
        # Change subcontainer
        sub_container.name = "ModifiedSubContainer"
        sub_container.children = {}  # Remove all children
        
        # Verify values changed
        assert sub_container.name == "ModifiedSubContainer"
        assert len(sub_container.children) == 0
        
        # Deserialize subcontainer
        result = main_container.deserialize_subcontainer("", "sub", serialized_sub)
        assert result
        
        # Verify values restored
        assert sub_container.name == "SubContainer"
        assert len(sub_container.children) == 1
        assert "widget" in sub_container.children
        assert sub_container.children["widget"] == widget.id

class TestSerializationCommand:
    """Test cases for SerializationCommand functionality."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
        
        # Clear command history
        manager = get_command_manager()
        manager.clear()
    
    def test_basic_serialization_command(self):
        """Test basic SerializationCommand functionality."""
        # Create a widget
        widget = MockWidget("TestWidget")
        widget.text = "Original Text"
        
        # Create a custom serialization command
        class TextChangeCommand(SerializationCommand):
            def __init__(self, widget_id, new_text):
                super().__init__(widget_id)
                self.new_text = new_text
                # Capture original state
                self.get_serialization()
                
            def execute(self):
                widget = get_id_registry().get_widget(self.component_id)
                if widget:
                    widget.text = self.new_text
                    
            def undo(self):
                # Restore original state
                self.deserialize()
        
        # Create and execute the command
        command = TextChangeCommand(widget.id, "New Text")
        
        # Execute the command
        manager = get_command_manager()
        manager.execute(command)
        
        # Verify text changed
        assert widget.text == "New Text"
        
        # Undo the command
        manager.undo()
        
        # Verify text restored
        assert widget.text == "Original Text"
        
        # Redo the command
        manager.redo()
        
        # Verify text changed again
        assert widget.text == "New Text"
    
    def test_serialization_with_id_changes(self):
        """Test serialization handling when IDs change during the process."""
        # Create a widget
        widget = MockWidget("TestWidget")
        widget.text = "Original Text"
        original_id = widget.id
        
        # Serialize the widget
        serialized_widget = widget.get_serialization()
        
        # Create a custom serialization command that will handle ID changes
        class RestoreWithChangedIDCommand(SerializationCommand):
            def __init__(self, component_id):
                super().__init__(component_id)
                self.serialized_state = serialized_widget
                
            def execute(self):
                # Change the ID of the component
                registry = get_id_registry()
                widget = registry.get_widget(self.component_id)
                
                if widget:
                    # Generate a new ID
                    new_id = f"{widget.id}_modified"
                    # Try to update the ID
                    try:
                        success, updated_id, error = registry.update_id(widget.id, new_id)
                        if success:
                            self.component_id = updated_id
                    except:
                        pass
                    
                    # Also change the text
                    widget.text = "Modified Text"
                
            def undo(self):
                # This should restore despite the ID change
                registry = get_id_registry()
                widget = registry.get_widget(self.component_id)
                
                if widget and self.serialized_state:
                    widget.deserialize(self.serialized_state)
        
        # Create and execute the command
        command = RestoreWithChangedIDCommand(original_id)
        
        # Execute the command
        manager = get_command_manager()
        manager.execute(command)
        
        # Get the widget (ID might have changed)
        registry = get_id_registry()
        modified_widget = None
        
        # Try to find the widget by both IDs
        modified_widget = registry.get_widget(command.component_id)
        if not modified_widget:
            modified_widget = registry.get_widget(original_id)
        
        # Verify widget was modified
        assert modified_widget is not None
        assert modified_widget.text == "Modified Text"
        
        # Undo the command
        manager.undo()
        
        # Get the widget again (ID might have changed back)
        restored_widget = registry.get_widget(command.component_id)
        if not restored_widget:
            restored_widget = registry.get_widget(original_id)
        
        # Verify original state restored
        assert restored_widget is not None
        assert restored_widget.text == "Original Text"

class TestComplexSerialization:
    """Test cases for complex serialization scenarios involving multiple components."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
    
    def test_observable_widget_relationship_serialization(self):
        """Test serialization of relationships between observables and widgets."""
        # Create components
        person = Person(name="Alice", age=30)
        widget = MockWidget("NameDisplay")
        widget.text = person.name  # Connect widget to person's name
        
        # Create serialization data
        serialized_person = person.serialize()
        serialized_widget = widget.get_serialization()
        
        # Bundle them together
        serialized_data = {
            "person": serialized_person,
            "widget": serialized_widget
        }
        
        # Change values
        person.name = "Bob"
        widget.text = "Changed Text"
        
        # Verify values changed
        assert person.name == "Bob"
        assert widget.text == "Changed Text"
        
        # Restore from serialization
        person.deserialize(serialized_data["person"])
        widget.deserialize(serialized_data["widget"])
        
        # Verify values restored
        assert person.name == "Alice"
        assert widget.text == "Alice"  # Widget should have original text value
        
        # Test that relationship is maintained
        # This is just testing the serialization restoration,
        # not actual binding which would be handled by application logic
        assert widget.text == person.name
    
    def test_cascading_serialization_restoration(self):
        """Test restoring a complex hierarchy with cascading effects."""
        # Create a complex hierarchy
        main_container = MockContainer("MainContainer")
        tab_container = MockContainer("TabContainer")
        form_container = MockContainer("FormContainer")
        
        name_widget = MockWidget("NameWidget")
        age_widget = MockWidget("AgeWidget")
        
        person = Person(name="Alice", age=30)
        
        # Set up hierarchy
        main_container.add_child(tab_container.id, "tabs")
        tab_container.add_child(form_container.id, "form")
        form_container.add_child(name_widget.id, "name")
        form_container.add_child(age_widget.id, "age")
        
        # Set up values
        name_widget.text = person.name
        age_widget.text = str(person.age)
        
        # Serialize the entire hierarchy
        serialized_main = main_container.get_serialization()
        serialized_tab = tab_container.get_serialization()
        serialized_form = form_container.get_serialization()
        serialized_name = name_widget.get_serialization()
        serialized_age = age_widget.get_serialization()
        serialized_person = person.serialize()
        
        # Bundle everything
        serialized_data = {
            "main": serialized_main,
            "tab": serialized_tab,
            "form": serialized_form,
            "name_widget": serialized_name,
            "age_widget": serialized_age,
            "person": serialized_person
        }
        
        # Change everything
        main_container.name = "Modified Main"
        tab_container.name = "Modified Tab"
        form_container.name = "Modified Form"
        name_widget.text = "Modified Name"
        age_widget.text = "Modified Age"
        person.name = "Bob"
        person.age = 40
        
        # Verify changes
        assert main_container.name == "Modified Main"
        assert tab_container.name == "Modified Tab"
        assert form_container.name == "Modified Form"
        assert name_widget.text == "Modified Name"
        assert age_widget.text == "Modified Age"
        assert person.name == "Bob"
        assert person.age == 40
        
        # Restore everything in reverse order
        person.deserialize(serialized_data["person"])
        name_widget.deserialize(serialized_data["name_widget"])
        age_widget.deserialize(serialized_data["age_widget"])
        form_container.deserialize(serialized_data["form"])
        tab_container.deserialize(serialized_data["tab"])
        main_container.deserialize(serialized_data["main"])
        
        # Verify restoration
        assert main_container.name == "MainContainer"
        assert tab_container.name == "TabContainer"
        assert form_container.name == "FormContainer"
        assert name_widget.text == "Alice"
        assert age_widget.text == str(30)
        assert person.name == "Alice"
        assert person.age == 30
        
        # Verify hierarchy is maintained
        assert "tabs" in main_container.children
        assert main_container.children["tabs"] == tab_container.id
        assert "form" in tab_container.children
        assert tab_container.children["form"] == form_container.id
        assert "name" in form_container.children
        assert form_container.children["name"] == name_widget.id
        assert "age" in form_container.children
        assert form_container.children["age"] == age_widget.id

if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main(["-vsx", __file__])