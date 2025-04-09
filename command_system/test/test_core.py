"""
Comprehensive test suite for the command system.

This tests the functionality of the core command system from an end-user perspective,
focusing on observable pattern and command pattern usage.
"""
import pytest
import sys
import os
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
    def __init__(self, name: str):
        self.name = name
        self.text = ""
        self.visible = True
        
        # Register with ID system
        self.id = get_id_registry().register(self, WidgetTypeCodes.CUSTOM_WIDGET)
        
    def __repr__(self):
        return f"MockWidget({self.name})"

class Person(Observable):
    """Sample observable class for testing."""
    name = ObservableProperty("")
    age = ObservableProperty(0)
    
    def __init__(self, name="", age=0):
        # Initialize Observable
        super().__init__()
        # Set initial values
        self.name = name
        self.age = age

class TestObservablePattern:
    """Test cases for the observable pattern."""
    
    def test_observable_property_change(self):
        """Test property change and notification."""
        # Create person
        person = Person()
        
        # Track changes
        changes = []
        
        # Create observer object
        class Observer:
            def __init__(self):
                self.called = False
                
            def on_name_changed(self, property_name, old_value, new_value):
                self.called = True
                changes.append((property_name, old_value, new_value))
        
        observer = Observer()
        
        # Add observer with object
        observer_id = person.add_property_observer("name", observer.on_name_changed, observer)
        
        # Change property
        person.name = "Alice"
        
        # Verify notification
        assert len(changes) == 1
        assert changes[0] == ("name", "", "Alice")
        
        # Change property again
        person.name = "Bob"
        
        print(changes)
        # Verify second notification
        assert len(changes) == 2
        assert changes[1] == ("name", "Alice", "Bob")
        
        # Remove observer
        print(person.remove_property_observer("name", observer_id))
        
        # Change property after removing observer
        person.name = "Charlie"
        
        # Verify no additional notification
        assert len(changes) == 2
    
    def test_observable_multiple_properties(self):
        """Test multiple properties on same observable."""
        # Create person
        person = Person()
        
        # Track changes for name and age
        name_changes = []
        age_changes = []
        
        # Create observer objects
        class NameObserver:
            def on_changed(self, property_name, old_value, new_value):
                name_changes.append((old_value, new_value))
                
        class AgeObserver:
            def on_changed(self, property_name, old_value, new_value):
                age_changes.append((old_value, new_value))
        
        name_observer = NameObserver()
        age_observer = AgeObserver()
        
        # Add observers
        person.add_property_observer("name", name_observer.on_changed, name_observer)
        person.add_property_observer("age", age_observer.on_changed, age_observer)
        
        # Change properties
        person.name = "Alice"
        person.age = 30
        
        # Verify notifications
        assert len(name_changes) == 1
        assert name_changes[0] == ("", "Alice")
        
        assert len(age_changes) == 1
        assert age_changes[0] == (0, 30)
    
    def test_observable_no_notification_if_unchanged(self):
        """Test that no notification is sent if value doesn't change."""
        # Create person
        person = Person(name="Alice")
        
        # Track changes
        changes = []
        
        # Create observer object
        class Observer:
            def on_changed(self, property_name, old_value, new_value):
                changes.append((property_name, old_value, new_value))
        
        observer = Observer()
        
        # Add observer
        person.add_property_observer("name", observer.on_changed, observer)
        
        # "Change" property to same value
        person.name = "Alice"
        
        # Verify no notification
        assert len(changes) == 0
    
    def test_observable_id_lookup(self):
        """Test retrieving observable by ID."""
        # Create person
        person = Person(name="Alice", age=30)
        
        # Get ID
        person_id = person.get_id()
        
        # Look up by ID
        registry = get_id_registry()
        retrieved_person = registry.get_observable(person_id)
        
        # Verify same object
        assert retrieved_person is person
        assert retrieved_person.name == "Alice"
        assert retrieved_person.age == 30

    def test_observable_property_serialization(self):
        """Test serializing and deserializing property values."""
        # Create person
        person = Person(name="Alice", age=30)
        
        # Serialize properties
        serialized_name = person.serialize_property("name")
        serialized_age = person.serialize_property("age")
        
        # Verify serialized data
        assert serialized_name["property_name"] == "name"
        assert serialized_name["value"] == "Alice"
        assert serialized_name["observable_id"] == person.get_id()
        
        assert serialized_age["property_name"] == "age"
        assert serialized_age["value"] == 30
        assert serialized_age["observable_id"] == person.get_id()
        
        # Change property values
        person.name = "Bob"
        person.age = 40
        
        # Deserialize properties
        person.deserialize_property("name", serialized_name)
        person.deserialize_property("age", serialized_age)
        
        # Verify values restored
        assert person.name == "Alice"
        assert person.age == 30
    
    def test_observable_id_change_handling(self):
        """Test handling of observable ID changes during deserialization."""
        # Create person
        person = Person(name="Alice", age=30)
        original_id = person.get_id()
        
        # Create new ID using the system's ID creation method
        id_registry = get_id_registry()
        new_id = id_registry.register_observable(None, "ob")
        
        # Create serialized data with new ID
        serialized_name = {
            "property_id": person._get_property_id("name"),
            "property_name": "name",
            "value": "Charlie",
            "observable_id": new_id
        }
        
        # Deserialize with new ID
        person.deserialize_property("name", serialized_name)
        
        # Verify ID updated
        assert person.get_id() == new_id
        assert person.get_id() != original_id
        
        # Verify value updated
        assert person.name == "Charlie"

    def test_observable_property_unregistration(self):
        """Test unregistering properties from an observable."""
        # Create person
        person = Person(name="Alice", age=30)
        
        # Get property IDs
        name_property_id = person._get_property_id("name")
        age_property_id = person._get_property_id("age")
        
        # Unregister name property
        success = person.unregister_property("name")
        assert success
        
        # Verify property is unregistered
        id_registry = get_id_registry()
        assert id_registry.get_observable_property(name_property_id) is None
        
        # Verify observable still exists
        assert id_registry.get_observable(person.get_id()) is not None
        
        # Unregister observable
        success = person.unregister()
        assert success
        
        # Verify observable is unregistered
        assert id_registry.get_observable(person.get_id()) is None


class SimpleCommand(Command):
    """Simple command for testing."""
    
    def __init__(self, value: str):
        super().__init__()
        self.value = value
        self.executed = False
        self.undone = False
    
    def execute(self):
        self.executed = True
        self.undone = False
    
    def undo(self):
        self.undone = True
        self.executed = False


class TestCommandPattern:
    """Test cases for the command pattern."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Get fresh command manager
        self.manager = get_command_manager()
        self.manager.clear()
        
        # Create test objects
        self.person = Person()
        self.widget = MockWidget("TestWidget")
    
    def test_simple_command(self):
        """Test basic command execution and undo."""
        # Create command
        cmd = SimpleCommand("test")
        
        # Execute
        self.manager.execute(cmd)
        
        # Verify execution
        assert cmd.executed
        assert not cmd.undone
        assert self.manager.can_undo()
        assert not self.manager.can_redo()
        
        # Undo
        self.manager.undo()
        
        # Verify undo
        assert not cmd.executed
        assert cmd.undone
        assert not self.manager.can_undo()
        assert self.manager.can_redo()
        
        # Redo
        self.manager.redo()
        
        # Verify redo
        assert cmd.executed
        assert not cmd.undone
        assert self.manager.can_undo()
        assert not self.manager.can_redo()
    
    def test_property_command(self):
        """Test property change command."""
        # Get the property ID
        property_id = self.person._get_property_id("name")
        
        # Create command with property_id
        cmd = PropertyCommand(property_id, "Alice")
        
        # Execute
        self.manager.execute(cmd)
        
        # Verify property changed
        assert self.person.name == "Alice"
        
        # Undo
        self.manager.undo()
        
        # Verify property restored
        assert self.person.name == ""
        
        # Redo
        self.manager.redo()
        
        # Verify property changed again
        assert self.person.name == "Alice"
    
    def test_widget_property_command(self):
        """Test widget property command."""
        # Create command
        widget_id = self.widget.id
        cmd = WidgetPropertyCommand(widget_id, "text", "New Text")
        
        # Execute
        self.manager.execute(cmd)
        
        # Verify property changed
        assert self.widget.text == "New Text"
        
        # Undo
        self.manager.undo()
        
        # Verify property restored
        assert self.widget.text == ""
    
    def test_compound_command(self):
        """Test compound command with multiple nested commands."""
        # Create compound command
        compound = CompoundCommand("Update Person")
        
        # Get property IDs
        name_property_id = self.person._get_property_id("name")
        age_property_id = self.person._get_property_id("age")
        
        # Add subcommands with property IDs
        compound.add_command(PropertyCommand(name_property_id, "Alice"))
        compound.add_command(PropertyCommand(age_property_id, 30))
        
        # Execute compound
        self.manager.execute(compound)
        
        # Verify all properties changed
        assert self.person.name == "Alice"
        assert self.person.age == 30
        
        # Undo compound
        self.manager.undo()
        
        # Verify all properties restored
        assert self.person.name == ""
        assert self.person.age == 0
    
    def test_macro_command(self):
        """Test macro command with description."""
        # Create macro command
        macro = MacroCommand("Create Person")
        macro.set_description("Create a new person named Alice")
        
        # Get property IDs
        name_property_id = self.person._get_property_id("name")
        age_property_id = self.person._get_property_id("age")
        
        # Add subcommands with property IDs
        macro.add_command(PropertyCommand(name_property_id, "Alice"))
        macro.add_command(PropertyCommand(age_property_id, 30))
        
        # Execute macro
        self.manager.execute(macro)
        
        # Verify description and execution
        assert macro.get_description() == "Create a new person named Alice"
        assert self.person.name == "Alice"
        assert self.person.age == 30
    
    def test_command_with_trigger_widget(self):
        """Test command with trigger widget context."""
        # Create command
        cmd = SimpleCommand("test")
        
        # Execute with trigger widget
        self.manager.execute(cmd, self.widget.id)
        
        # Verify trigger widget stored
        assert cmd.trigger_widget_id == self.widget.id
        assert cmd.get_trigger_widget() is self.widget
    
    def test_command_context_info(self):
        """Test storing and retrieving context info with commands."""
        # Create command
        cmd = SimpleCommand("test")
        
        # Set context info
        cmd.set_context_info("key1", "value1")
        cmd.set_context_info("key2", {"nested": "data"})
        
        # Retrieve context info
        assert cmd.get_context_info("key1") == "value1"
        assert cmd.get_context_info("key2") == {"nested": "data"}
        assert cmd.get_context_info("non_existent") is None
        assert cmd.get_context_info("non_existent", "default") == "default"
    
    def test_command_lifecycle_callbacks(self):
        """Test command lifecycle callbacks."""
        # Track callbacks
        before_execute_called = False
        after_execute_called = False
        before_undo_called = False
        after_undo_called = False
        
        # Define callbacks
        def before_execute(command):
            nonlocal before_execute_called
            before_execute_called = True
        
        def after_execute(command, success):
            nonlocal after_execute_called
            after_execute_called = True
            assert success
        
        def before_undo(command):
            nonlocal before_undo_called
            before_undo_called = True
        
        def after_undo(command, success):
            nonlocal after_undo_called
            after_undo_called = True
            assert success
        
        # Register callbacks
        self.manager.add_before_execute_callback("test", before_execute)
        self.manager.add_after_execute_callback("test", after_execute)
        self.manager.add_before_undo_callback("test", before_undo)
        self.manager.add_after_undo_callback("test", after_undo)
        
        # Create and execute command
        cmd = SimpleCommand("test")
        self.manager.execute(cmd)
        
        # Verify execute callbacks
        assert before_execute_called
        assert after_execute_called
        
        # Reset flags
        before_execute_called = False
        after_execute_called = False
        
        # Undo command
        self.manager.undo()
        
        # Verify undo callbacks
        assert before_undo_called
        assert after_undo_called
        
        # Remove callbacks
        self.manager.remove_callback("test")
    
    def test_initialization_mode(self):
        """Test initialization mode that doesn't add to history."""
        # Enter initialization mode
        self.manager.begin_init()
        
        # Execute commands
        cmd1 = SimpleCommand("init1")
        cmd2 = SimpleCommand("init2")
        self.manager.execute(cmd1)
        self.manager.execute(cmd2)
        
        # End initialization mode
        self.manager.end_init()
        
        # Verify commands executed but not in history
        assert cmd1.executed
        assert cmd2.executed
        assert not self.manager.can_undo()

    def test_serialization_command(self):
        """Test serialization command basics."""
        # Create a simple custom serialization command
        class TestSerializationCommand(SerializationCommand):
            def __init__(self, widget_id):
                super().__init__(widget_id)
                self.original_text = None
                self.new_text = "Serialization Test"
            
            def execute(self):
                widget = get_id_registry().get_widget(self.component_id)
                if widget:
                    self.original_text = widget.text
                    widget.text = self.new_text
            
            def undo(self):
                widget = get_id_registry().get_widget(self.component_id)
                if widget:
                    widget.text = self.original_text
        
        # Create and execute the command
        cmd = TestSerializationCommand(self.widget.id)
        self.manager.execute(cmd)
        
        # Verify widget property changed
        assert self.widget.text == "Serialization Test"
        
        # Undo
        self.manager.undo()
        
        # Verify widget property restored
        assert self.widget.text == ""


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main(["-v", __file__])