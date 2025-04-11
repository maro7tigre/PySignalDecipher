"""
Comprehensive test suite for the PySide6 widget integration with command system.

This test suite validates the functionality of the actual PySide6 command-enabled widgets:
- BaseCommandWidget and CommandLineEdit implementations
- Widget registration and ID management
- Property binding and change tracking
- Command generation and execution
- Widget serialization and deserialization
- Real-world usage scenarios and integration with both the command system and ID system

This test uses the actual widget implementations, testing from an end user's perspective.
"""
import pytest
import sys
import os
from typing import Dict, Any, List, Optional, Callable
from PySide6.QtWidgets import QApplication

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import required modules from command system
from command_system.core import (
    Observable, ObservableProperty,
    Command, PropertyCommand, get_command_manager, CompoundCommand,
    MacroCommand
)

from command_system.id_system import (
    get_id_registry, WidgetTypeCodes, ContainerTypeCodes, 
    parse_property_id
)

# Import the actual PySide6 widget implementations we want to test
from command_system.pyside6_widgets import (
    BaseCommandWidget, CommandTriggerMode, CommandLineEdit,
    BaseCommandContainer, CommandTabWidget
)



# MARK: - Test Models
class Person(Observable):
    """Sample observable class for testing."""
    name = ObservableProperty("")
    age = ObservableProperty(0)
    email = ObservableProperty("")
    is_active = ObservableProperty(True)
    
    def __init__(self, name="", age=0, email="", is_active=True):
        # Initialize Observable base
        super().__init__()
        # Set initial values
        self.name = name
        self.age = age
        self.email = email
        self.is_active = is_active

# MARK: - Tests
class TestPySide6Widgets:
    """Test cases for actual PySide6 widget implementations."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
        
        # Clear command manager
        manager = get_command_manager()
        manager.clear()
        
        # Create test objects
        self.person = Person(name="Alice", age=30, email="alice@example.com")
    
    def test_command_line_edit_creation(self):
        """Test basic CommandLineEdit creation and initialization."""
        # Create a command line edit
        line_edit = CommandLineEdit(text="Initial Text")
        
        # Verify widget is registered with ID system
        registry = get_id_registry()
        widget_id = registry.get_id(line_edit)
        
        # ID should be valid and follow the format
        assert widget_id is not None
        assert widget_id.startswith(f"{WidgetTypeCodes.LINE_EDIT}:")
        
        # Should be able to retrieve widget by ID
        retrieved_widget = registry.get_widget(widget_id)
        assert retrieved_widget is line_edit
        
        # Initial text should be set
        assert line_edit.text() == "Initial Text"
        
        # Default trigger mode should be ON_EDIT_FINISHED
        # This is an implementation detail we can verify using the internal state
        assert line_edit._command_trigger_mode == CommandTriggerMode.ON_EDIT_FINISHED
        
        # Clean up after test
        registry.unregister(widget_id)
    
    def test_property_binding(self):
        """Test property binding between CommandLineEdit and Observable."""
        # Create a command line edit
        line_edit = CommandLineEdit()
        
        # Bind to person's name property
        line_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Verify widget was initialized with observable's value
        assert line_edit.text() == "Alice"
        
        # Change observable property
        self.person.name = "Bob"
        
        # Verify widget was updated
        assert line_edit.text() == "Bob"
        
        # Change widget property
        line_edit.setText("Charlie")
        
        # Trigger editingFinished since we're using ON_EDIT_FINISHED mode
        line_edit.editingFinished.emit()
        
        # Verify observable was updated via command
        assert self.person.name == "Charlie"
        
        # Undo the command
        manager = get_command_manager()
        assert manager.can_undo()
        manager.undo()
        
        # Verify observable and widget were restored
        assert self.person.name == "Bob"
        assert line_edit.text() == "Bob"
        
        # Clean up
        line_edit.unbind_text_property()
        registry = get_id_registry()
        registry.unregister(line_edit.widget_id)
    
    def test_immediate_command_mode(self):
        """Test command generation with IMMEDIATE trigger mode."""
        # Create a command line edit with immediate trigger mode
        line_edit = CommandLineEdit()
        line_edit.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        
        # Bind to person's name property
        line_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Change widget text
        line_edit.setText("Bob")
        
        # Verify command was generated immediately
        manager = get_command_manager()
        assert manager.can_undo()
        
        # Undo the command
        manager.undo()
        
        # Verify observable and widget were restored
        assert self.person.name == "Alice"
        assert line_edit.text() == "Alice"
    
    def test_delayed_command_mode(self):
        """Test command generation with DELAYED trigger mode."""
        # Create a command line edit with delayed trigger mode
        line_edit = CommandLineEdit()
        line_edit.set_command_trigger_mode(CommandTriggerMode.DELAYED, 300)
        
        # Bind to person's name property
        line_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Change widget text
        line_edit.setText("Bob")
        
        # No command should be generated yet
        manager = get_command_manager()
        assert not manager.can_undo()
        
        # Manually trigger the timeout (simulating timer expiry)
        line_edit._on_change_timer_timeout()
        
        # Verify command was generated
        assert manager.can_undo()
        
        # Undo the command
        manager.undo()
        
        # Verify observable and widget were restored
        assert self.person.name == "Alice"
        assert line_edit.text() == "Alice"
    
    def test_multiple_value_changes(self):
        """Test behavior with multiple value changes in different modes."""
        # Create a command line edit with edit finished trigger mode
        line_edit = CommandLineEdit()
        line_edit.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
        
        # Bind to person's name property
        line_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Make multiple changes without finishing editing
        line_edit.setText("Bob")
        line_edit.setText("Charlie")
        line_edit.setText("Dave")
        
        # No command should be generated yet
        manager = get_command_manager()
        assert not manager.can_undo()
        
        # Finish editing
        line_edit.editingFinished.emit()
        
        # Verify command was generated (only one command for the final value)
        assert manager.can_undo()
        
        # Verify observable has the final value
        assert self.person.name == "Dave"
        
        # Undo the command
        manager.undo()
        
        # Verify observable and widget were restored
        assert self.person.name == "Alice"
        assert line_edit.text() == "Alice"
    
    def test_multiple_bound_widgets(self):
        """Test multiple widgets bound to the same observable property."""
        # Create multiple widgets
        line_edit1 = CommandLineEdit()
        line_edit2 = CommandLineEdit()
        
        # Set to immediate mode for easier testing
        line_edit1.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        line_edit2.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        
        # Bind both to the same property
        line_edit1.bind_to_text_property(self.person.get_id(), "name")
        line_edit2.bind_to_text_property(self.person.get_id(), "name")
        
        # Verify both have initial value
        assert line_edit1.text() == "Alice"
        assert line_edit2.text() == "Alice"
        
        # Change from first widget
        line_edit1.setText("Bob")
        
        # Verify both widgets and observable were updated
        assert self.person.name == "Bob"
        assert line_edit1.text() == "Bob"
        assert line_edit2.text() == "Bob"
        
        # Change from observable
        self.person.name = "Charlie"
        
        # Verify both widgets were updated
        assert line_edit1.text() == "Charlie"
        assert line_edit2.text() == "Charlie"
        
        # Clean up
        line_edit1.unbind_text_property()
        line_edit2.unbind_text_property()
    
    def test_widget_serialization(self):
        """Test serialization and deserialization of CommandLineEdit."""
        # Create and configure a command line edit
        line_edit = CommandLineEdit()
        line_edit.setPlaceholderText("Enter name")
        line_edit.setMaxLength(100)
        
        # Bind to person's name property
        line_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Capture widget ID
        original_id = line_edit.widget_id
        
        # Serialize widget
        serialized_data = line_edit.get_serialization()
        
        # Verify serialized data structure
        assert "id" in serialized_data
        assert serialized_data["id"] == original_id
        assert "properties" in serialized_data
        assert "text" in serialized_data["properties"]
        assert serialized_data["properties"]["text"]["value"] == "Alice"
        
        # Change observable and widget values
        self.person.name = "Bob"
        line_edit.setPlaceholderText("Modified placeholder")
        
        # Create a new line edit for deserialization
        new_line_edit = CommandLineEdit()
        
        # Bind to same observable first (needed to establish the property connection)
        new_line_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Deserialize to the new widget
        new_line_edit.deserialize(serialized_data)
        
        # Verify property was restored
        assert self.person.name == "Alice"  # Observable value should be restored
        assert new_line_edit.text() == "Alice"
        
        # Verify binding still works
        self.person.name = "Charlie"
        assert new_line_edit.text() == "Charlie"
    
    def test_unbind_property(self):
        """Test unbinding a property."""
        # Create a command line edit
        line_edit = CommandLineEdit()
        
        # Bind to person's name property
        line_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Verify binding works
        self.person.name = "Bob"
        assert line_edit.text() == "Bob"
        
        # Unbind property
        line_edit.unbind_text_property()
        
        # Change observable - should not update widget anymore
        self.person.name = "Charlie"
        assert line_edit.text() == "Bob"  # Still has old value
        
        # Change widget - should not update observable anymore
        line_edit.setText("Dave")
        line_edit.editingFinished.emit()
        assert self.person.name == "Charlie"  # Observable unchanged
    
    def test_container_hierarchy(self):
        """Test widget container hierarchy."""
        # Create tab container
        tab_container = CommandTabWidget()
        
        # Create line edit in container
        line_edit = CommandLineEdit(container_id=tab_container.widget_id, location="tab1")
        
        # Verify container relationship
        registry = get_id_registry()
        container_id = registry.get_container_id_from_widget_id(line_edit.widget_id)
        assert container_id == tab_container.widget_id
        
        # Verify container's widgets
        container_widgets = registry.get_widgets_by_container_id(tab_container.widget_id)
        assert line_edit.widget_id in container_widgets
        
        # Change container
        new_container = CommandTabWidget()
        updated_id = line_edit.update_container(new_container.widget_id)
        
        # Verify container was updated
        new_container_id = registry.get_container_id_from_widget_id(updated_id)
        assert new_container_id == new_container.widget_id
    
    def test_error_handling(self):
        """Test error handling in widget implementations."""
        # Create a command line edit
        line_edit = CommandLineEdit()
        
        # Try to bind to nonexistent property
        with pytest.raises(ValueError) as excinfo:
            line_edit.bind_to_text_property(self.person.get_id(), "nonexistent")
        
        # Verify error message
        assert "does not have property" in str(excinfo.value)
        
        # Try to bind to nonexistent observable
        with pytest.raises(ValueError) as excinfo:
            line_edit.bind_to_text_property("ob:999", "name")
        
        # Verify error message
        assert "not found" in str(excinfo.value)
        
        # Unbinding a property that was never bound (should not raise error)
        line_edit.unbind_text_property()
    
    def test_real_world_form_scenario(self):
        """Test a typical form editing scenario with multiple fields."""
        # Create form widgets
        name_widget = CommandLineEdit()
        age_widget = CommandLineEdit()
        email_widget = CommandLineEdit()
        
        # Set edit finished trigger mode (default, but being explicit)
        name_widget.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
        age_widget.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
        email_widget.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
        
        # Bind to model properties
        name_widget.bind_to_text_property(self.person.get_id(), "name")
        age_widget.bind_to_text_property(self.person.get_id(), "age")
        email_widget.bind_to_text_property(self.person.get_id(), "email")
        
        # Verify initial values
        assert name_widget.text() == "Alice"
        assert age_widget.text() == "30"
        assert email_widget.text() == "alice@example.com"
        
        # Edit all fields
        name_widget.setText("Bob")
        age_widget.setText("40")
        email_widget.setText("bob@example.com")
        
        # No commands should be generated yet
        manager = get_command_manager()
        assert not manager.can_undo()
        
        # Complete editing of each field
        name_widget.editingFinished.emit()
        age_widget.editingFinished.emit()
        email_widget.editingFinished.emit()
        
        # All changes should be applied
        assert self.person.name == "Bob"
        assert self.person.age == 40
        assert self.person.email == "bob@example.com"
        
        # Undo changes in reverse order
        manager.undo()  # Undo email
        manager.undo()  # Undo age
        manager.undo()  # Undo name
        
        # Verify all original values are restored
        assert self.person.name == "Alice"
        assert self.person.age == 30
        assert self.person.email == "alice@example.com"
        
        # Widgets should be updated too
        assert name_widget.text() == "Alice"
        assert age_widget.text() == "30"
        assert email_widget.text() == "alice@example.com"
    
    def test_command_navigation(self):
        """Test command navigation with trigger widget."""
        # Create tab container
        tab_container = CommandTabWidget()
        
        # Create widgets in container
        name_widget = CommandLineEdit(container_id=tab_container.widget_id, location="tab1")
        age_widget = CommandLineEdit(container_id=tab_container.widget_id, location="tab2")
        
        # Override navigate_to_widget to track navigation
        tab_container.navigation_history = []
        original_navigate = tab_container.navigate_to_widget
        
        def tracked_navigate(widget_id):
            tab_container.navigation_history.append(widget_id)
            return original_navigate(widget_id)
            
        tab_container.navigate_to_widget = tracked_navigate
        
        # Bind widgets to observable
        name_widget.bind_to_text_property(self.person.get_id(), "name")
        age_widget.bind_to_text_property(self.person.get_id(), "age")
        
        # Set immediate mode for testing
        name_widget.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        
        # Change property from widget
        name_widget.setText("Bob")
        
        # Get command manager and undo
        manager = get_command_manager()
        manager.undo()
        
        # Verify navigate_to_widget was called with trigger widget ID
        assert name_widget.widget_id in tab_container.navigation_history
    
    def test_compound_command(self):
        """Test compound commands with widget properties."""
        # Create widgets
        name_widget = CommandLineEdit()
        age_widget = CommandLineEdit()
        
        # Bind to model properties
        name_widget.bind_to_text_property(self.person.get_id(), "name")
        age_widget.bind_to_text_property(self.person.get_id(), "age")
        
        # Create a compound command
        compound = CompoundCommand("Update Person")
        
        # Get property IDs
        name_property_id = name_widget._controlled_properties["text"]
        age_property_id = age_widget._controlled_properties["text"]
        
        # Create property commands
        name_command = PropertyCommand(name_property_id, "Bob")
        age_command = PropertyCommand(age_property_id, "40")
        
        # Add commands to compound
        compound.add_command(name_command)
        compound.add_command(age_command)
        
        # Execute the compound command
        manager = get_command_manager()
        manager.execute(compound)
        
        # Verify both properties were updated
        assert self.person.name == "Bob"
        assert self.person.age == 40
        
        # Verify widgets were updated
        assert name_widget.text() == "Bob"
        assert age_widget.text() == "40"
        
        # Undo the compound command
        manager.undo()
        
        # Verify all properties were restored
        assert self.person.name == "Alice"
        assert self.person.age == 30
        
        # Verify widgets were restored
        assert name_widget.text() == "Alice"
        assert age_widget.text() == "30"
    
    def test_macro_command(self):
        """Test macro commands with user-level descriptions."""
        # Create widgets
        name_widget = CommandLineEdit()
        age_widget = CommandLineEdit()
        
        # Bind to model properties
        name_widget.bind_to_text_property(self.person.get_id(), "name")
        age_widget.bind_to_text_property(self.person.get_id(), "age")
        
        # Create a macro command
        macro = MacroCommand("Edit Person Information")
        macro.set_description("Change name to Bob and age to 40")
        
        # Get property IDs
        name_property_id = name_widget._controlled_properties["text"]
        age_property_id = age_widget._controlled_properties["text"]
        
        # Create property commands
        name_command = PropertyCommand(name_property_id, "Bob")
        age_command = PropertyCommand(age_property_id, "40")
        
        # Add commands to macro
        macro.add_command(name_command)
        macro.add_command(age_command)
        
        # Execute the macro command
        manager = get_command_manager()
        manager.execute(macro)
        
        # Verify description
        assert macro.get_description() == "Change name to Bob and age to 40"
        
        # Verify both properties were updated
        assert self.person.name == "Bob"
        assert self.person.age == 40
        
        # Undo the macro command
        manager.undo()
        
        # Verify all properties were restored
        assert self.person.name == "Alice"
        assert self.person.age == 30
    
    def test_context_information(self):
        """Test command context information storage and retrieval."""
        # Create widgets
        name_widget = CommandLineEdit()
        
        # Bind to model property
        name_widget.bind_to_text_property(self.person.get_id(), "name")
        name_widget.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        
        # Change widget value to generate command
        name_widget.setText("Bob")
        
        # Get the generated command
        manager = get_command_manager()
        history = manager._history
        commands = history.get_executed_commands()
        command = commands[0]
        
        # Set context information
        command.set_context_info("edit_type", "name_change")
        command.set_context_info("ui_section", "personal_info")
        
        # Verify context information
        assert command.get_context_info("edit_type") == "name_change"
        assert command.get_context_info("ui_section") == "personal_info"
        assert command.get_context_info("non_existent", "default") == "default"
        
        # Verify trigger widget is correctly stored
        assert command.trigger_widget_id == name_widget.widget_id
        assert command.get_trigger_widget() is name_widget
    
    def test_recursive_updates_prevention(self):
        """Test prevention of recursive updates between widget and observable."""
        # Create widget
        line_edit = CommandLineEdit()
        line_edit.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        
        # Create an observer to track update calls
        update_count = 0
        
        def on_name_changed(prop_name, old_val, new_val):
            nonlocal update_count
            update_count += 1
        
        # Add direct observer to person
        self.person.add_property_observer("name", on_name_changed)
        
        # Bind widget to observable property
        line_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Initial value should set update_count to 1
        assert update_count == 1
        
        # Reset counter
        update_count = 0
        
        # Change from widget
        line_edit.setText("Bob")
        
        # Should only trigger one update (not recursive)
        assert update_count == 1
        
        # Reset counter
        update_count = 0
        
        # Change from observable
        self.person.name = "Charlie"
        
        # Should only trigger one update (not recursive)
        assert update_count == 1
        
        # Verify final values
        assert self.person.name == "Charlie"
        assert line_edit.text() == "Charlie"


if __name__ == "__main__":
    # Run the tests directly if this script is executed
    app = QApplication(sys.argv)
    pytest.main(["-vs", __file__])