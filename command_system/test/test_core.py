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
    get_command_manager
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
        
    def setFocus(self):
        """Mock focus method for testing trigger widget navigation."""
        pass

class MockContainer(MockWidget):
    """Mock container for testing complex scenarios."""
    def __init__(self, name: str):
        super().__init__(name)
        self.widgets = {}
        
    def add_widget(self, widget_id: str, location: str):
        """Add a widget at a specific location."""
        self.widgets[location] = widget_id
        
    def navigate_to_widget(self, widget_id: str):
        """Mock navigation method for testing CommandManager navigate_to_command_context."""
        for location, wid in self.widgets.items():
            if wid == widget_id:
                # In a real scenario, this would activate the widget
                return True
        return False

class Person(Observable):
    """Sample observable class for testing."""
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

class TestObservablePattern:
    """Test cases for the observable pattern."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
    
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
        
        # Verify second notification
        assert len(changes) == 2
        assert changes[1] == ("name", "Alice", "Bob")
        
        # Remove observer
        person.remove_property_observer("name", observer_id)
        
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
    
    def test_observable_property_id_lookup(self):
        """Test retrieving property by ID."""
        # Create person
        person = Person(name="Alice", age=30)
        
        # Get property IDs
        name_property_id = person._get_property_id("name")
        age_property_id = person._get_property_id("age")
        
        # Verify properties can be looked up by various methods
        registry = get_id_registry()
        
        # Get properties by observable ID
        properties = registry.get_observable_properties(person.get_id())
        assert name_property_id in properties
        assert age_property_id in properties
        
        # Get properties by observable ID and property name
        name_properties = registry.get_property_ids_by_observable_id_and_property_name(
            person.get_id(), "name")
        assert name_property_id in name_properties
        
        # Get observable ID from property
        observable_id = registry.get_observable_id_from_property_id(name_property_id)
        assert observable_id == person.get_id()

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
        
        # Verify all properties are automatically unregistered
        assert id_registry.get_observable_property(age_property_id) is None


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
        
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
        
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
    
    def test_command_navigation(self):
        """Test command navigation to context."""
        # Create a container with widgets
        container = MockContainer("Container")
        widget1 = MockWidget("Widget1")
        widget2 = MockWidget("Widget2")
        
        # Set up container
        container.add_widget(widget1.id, "location1")
        container.add_widget(widget2.id, "location2")
        
        # Create a command triggered by widget1
        cmd = SimpleCommand("test")
        
        # Execute with trigger widget
        self.manager.execute(cmd, widget1.id)
        
        # Test navigation
        # This is normally done by the command manager during undo/redo
        assert self.manager._navigate_to_command_context(cmd)
    
    def test_command_error_handling(self):
        """Test command error handling during execution and undo."""
        # Create a command that will raise an exception
        class ErrorCommand(Command):
            def __init__(self, raise_on_execute=False, raise_on_undo=False):
                super().__init__()
                self.raise_on_execute = raise_on_execute
                self.raise_on_undo = raise_on_undo
                self.executed = False
                self.undone = False
                
            def execute(self):
                if self.raise_on_execute:
                    raise ValueError("Test execution error")
                self.executed = True
                self.undone = False
                
            def undo(self):
                if self.raise_on_undo:
                    raise ValueError("Test undo error")
                self.undone = True
                self.executed = False
        
        print(self.manager._history.get_executed_commands())
        # Test execution error
        error_cmd1 = ErrorCommand(raise_on_execute=True)
        result = self.manager.execute(error_cmd1)
        print(self.manager._history.get_executed_commands())
        # Verify execution failed
        assert not result
        assert not error_cmd1.executed
        assert not self.manager.can_undo()
        
        # Test undo error
        error_cmd2 = ErrorCommand(raise_on_undo=True)
        self.manager.execute(error_cmd2)
        
        # Verify execution succeeded
        assert error_cmd2.executed
        assert self.manager.can_undo()
        
        # Attempt to undo (should fail)
        result = self.manager.undo()
        
        # Command should remain in history even though undo failed
        assert not result
        assert error_cmd2.executed  # Should still be in executed state
        assert self.manager.can_undo()  # Should still be undoable
    
    def test_redo_error_handling(self):
        """Test command error handling during redo."""
        # Create a command that will raise an exception on redo
        class RedoErrorCommand(Command):
            def __init__(self):
                super().__init__()
                self.executed = False
                self.undone = False
                self.redo_count = 0
                
            def execute(self):
                self.executed = True
                self.undone = False
                
            def undo(self):
                self.undone = True
                self.executed = False
                
            def redo(self):
                self.redo_count += 1
                if self.redo_count > 1:
                    raise ValueError("Test redo error")
                self.execute()
        
        # Execute and undo to prepare for redo
        cmd = RedoErrorCommand()
        self.manager.execute(cmd)
        self.manager.undo()
        
        # First redo should succeed
        result = self.manager.redo()
        assert result
        assert cmd.executed
        
        # Undo again to prepare for second redo
        self.manager.undo()
        
        # Second redo should fail
        result = self.manager.redo()
        
        # Verify redo failed but command remains in the undone state
        assert not result
        assert not cmd.executed
        assert cmd.undone
        assert not self.manager.can_undo()
        assert self.manager.can_redo()
    
    def test_is_updating_flag(self):
        """Test is_updating flag for preventing recursive command execution."""
        # Create a command that checks is_updating flag
        executed_in_is_updating = False
        
        class CheckIsUpdatingCommand(Command):
            def execute(self):
                nonlocal executed_in_is_updating
                # Store the state of is_updating
                executed_in_is_updating = self.manager.is_updating()
                
            def undo(self):
                pass
        
        # Add the command manager to the command class
        CheckIsUpdatingCommand.manager = self.manager
        
        # Execute the command
        cmd = CheckIsUpdatingCommand()
        self.manager.execute(cmd)
        
        # Verify is_updating was True during execution
        assert executed_in_is_updating
        
        # Verify is_updating is False after execution
        assert not self.manager.is_updating()

class TestAdvancedUsage:
    """Test cases for advanced command system usage."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Get fresh command manager
        self.manager = get_command_manager()
        self.manager.clear()
        
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
    
    def test_property_change_notifications_with_commands(self):
        """Test property change notifications when changes are made via commands."""
        # Create person
        person = Person()
        
        # Track changes
        changes = []
        
        # Create observer object
        class Observer:
            def on_changed(self, property_name, old_value, new_value):
                changes.append((property_name, old_value, new_value))
        
        observer = Observer()
        
        # Add observer
        person.add_property_observer("name", observer.on_changed, observer)
        
        # Get property ID
        property_id = person._get_property_id("name")
        
        # Create and execute command
        cmd = PropertyCommand(property_id, "Alice")
        self.manager.execute(cmd)
        
        # Verify notification was sent
        assert len(changes) == 1
        assert changes[0] == ("name", "", "Alice")
        
        # Undo command
        self.manager.undo()
        
        # Verify notification for undo
        assert len(changes) == 2
        assert changes[1] == ("name", "Alice", "")
        
        # Redo command
        self.manager.redo()
        
        # Verify notification for redo
        assert len(changes) == 3
        assert changes[2] == ("name", "", "Alice")
    
    def test_container_hierarchy_operations(self):
        """Test commands for container hierarchy operations."""
        # Create container hierarchy
        main_container = MockContainer("MainContainer")
        tab_container = MockContainer("TabContainer")
        form_container = MockContainer("FormContainer")
        
        # Register with ID system
        main_id = main_container.id
        tab_id = tab_container.id
        form_id = form_container.id
        
        # Create widget
        widget = MockWidget("TestWidget")
        widget_id = widget.id
        
        # Create commands for setting up hierarchy
        class AddWidgetCommand(Command):
            def __init__(self, container_id, widget_id, location):
                super().__init__()
                self.container_id = container_id
                self.widget_id = widget_id
                self.location = location
                self.old_container_id = None
                self.old_location = None
                
            def execute(self):
                registry = get_id_registry()
                container = registry.get_widget(self.container_id)
                widget = registry.get_widget(self.widget_id)
                
                # Store old container if there is one
                if hasattr(widget, "container_id") and widget.container_id:
                    self.old_container_id = widget.container_id
                    old_container = registry.get_widget(self.old_container_id)
                    if old_container and hasattr(old_container, "widgets"):
                        for loc, wid in old_container.widgets.items():
                            if wid == self.widget_id:
                                self.old_location = loc
                                break
                
                # Add to new container
                if container and hasattr(container, "add_widget"):
                    container.add_widget(self.widget_id, self.location)
                    # Update widget's container reference
                    widget.container_id = self.container_id
                
            def undo(self):
                registry = get_id_registry()
                container = registry.get_widget(self.container_id)
                widget = registry.get_widget(self.widget_id)
                
                # Remove from current container
                if container and hasattr(container, "widgets"):
                    container.widgets.pop(self.location, None)
                
                # Restore to old container if there was one
                if self.old_container_id and self.old_location:
                    old_container = registry.get_widget(self.old_container_id)
                    if old_container and hasattr(old_container, "add_widget"):
                        old_container.add_widget(self.widget_id, self.old_location)
                        # Update widget's container reference
                        widget.container_id = self.old_container_id
                else:
                    # Clear widget's container reference
                    if hasattr(widget, "container_id"):
                        widget.container_id = None
        
        # Execute commands to build hierarchy
        cmd1 = AddWidgetCommand(main_id, tab_id, "tab")
        cmd2 = AddWidgetCommand(tab_id, form_id, "form")
        cmd3 = AddWidgetCommand(form_id, widget_id, "widget")
        
        self.manager.execute(cmd1)
        self.manager.execute(cmd2)
        self.manager.execute(cmd3)
        
        # Verify hierarchy was created
        assert main_container.widgets.get("tab") == tab_id
        assert tab_container.widgets.get("form") == form_id
        assert form_container.widgets.get("widget") == widget_id
        
        # Undo commands in reverse order
        self.manager.undo()  # Undo adding widget to form
        self.manager.undo()  # Undo adding form to tab
        self.manager.undo()  # Undo adding tab to main
        
        # Verify hierarchy was dismantled
        assert main_container.widgets.get("tab") is None
        assert tab_container.widgets.get("form") is None
        assert form_container.widgets.get("widget") is None
    
    def test_command_chaining(self):
        """Test chaining commands with dependencies on previous command results."""
        # Create person
        person = Person()
        
        # Create a chain of commands where each depends on the previous
        class ChainedCommand(Command):
            def __init__(self, person, property_name, base_value, chain_index):
                super().__init__()
                self.person = person
                self.property_name = property_name
                self.base_value = base_value
                self.chain_index = chain_index
                self.old_value = None
                
            def execute(self):
                # Get current property value
                property_value = getattr(self.person, self.property_name)
                self.old_value = property_value
                
                # Update with a value based on chain index
                new_value = f"{self.base_value}_{self.chain_index}"
                setattr(self.person, self.property_name, new_value)
                
            def undo(self):
                # Restore old value
                setattr(self.person, self.property_name, self.old_value)
        
        # Create and execute a chain of commands
        cmds = []
        for i in range(5):
            cmd = ChainedCommand(person, "name", "Alice", i)
            cmds.append(cmd)
            self.manager.execute(cmd)
        
        # Verify final result
        assert person.name == "Alice_4"
        
        # Undo commands one by one
        for i in range(5):
            self.manager.undo()
            if i < 4:
                assert person.name == f"Alice_{3-i}"
            else:
                assert person.name == ""  # Back to initial value
        
        # Redo all commands
        for i in range(5):
            self.manager.redo()
            assert person.name == f"Alice_{i}"

    def test_command_reexecution_consistency(self):
        """Test that command execution and re-execution through redo produce consistent results."""
        # Create person
        person = Person()
        
        # Create a command that depends on current state
        class IncrementCommand(Command):
            def __init__(self, person, property_name, increment):
                super().__init__()
                self.person = person
                self.property_name = property_name
                self.increment = increment
                self.old_value = None
                
            def execute(self):
                # Get current property value
                property_value = getattr(self.person, self.property_name)
                self.old_value = property_value
                
                # Calculate new value
                try:
                    if isinstance(property_value, int):
                        new_value = property_value + self.increment
                    else:
                        new_value = 0 + self.increment
                except:
                    new_value = self.increment
                
                # Update property
                setattr(self.person, self.property_name, new_value)
                
            def undo(self):
                # Restore old value
                setattr(self.person, self.property_name, self.old_value)
        
        # Create and execute command
        cmd = IncrementCommand(person, "age", 10)
        self.manager.execute(cmd)
        
        # Verify result
        assert person.age == 10
        
        # Undo
        self.manager.undo()
        assert person.age == 0
        
        # Change property before redo
        person.age = 5
        
        # Redo - should still increment by 10 from the captured old_value
        self.manager.redo()
        
        # Verify consistent increment of 10 from original value
        assert person.age == 10  # Not 15
        
        # Create another command that depends on current state
        cmd2 = IncrementCommand(person, "age", 20)
        self.manager.execute(cmd2)
        
        # Verify accumulated result
        assert person.age == 30
        
        # Undo both commands
        self.manager.undo()
        self.manager.undo()
        
        # Verify back to initial state
        assert person.age == 0

if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main(["-v", __file__])