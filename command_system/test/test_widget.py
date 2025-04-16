"""
Test suite for the PySide6 widget system.

This test suite validates the functionality of the PySide6 command-enabled widgets,
focusing on their integration with the core command system and ID system.
It tests property binding, command generation, and serialization.
"""
import pytest
import sys
import os
import time
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QEventLoop

from command_system.core import (
    Observable, ObservableProperty,
    Command, CompoundCommand, PropertyCommand, MacroCommand,
    get_command_manager
)
from command_system.id_system import get_id_registry, WidgetTypeCodes
from command_system.pyside6_widgets import (
    BaseCommandWidget,
    CommandTriggerMode,
    CommandLineEdit
)

# Initialize Qt Application
app = None

def setup_module():
    """Set up QApplication for the entire module."""
    global app
    app = QApplication.instance()
    if not app:
        app = QApplication([])

def teardown_module():
    """Clean up after all tests."""
    global app
    if app:
        app.quit()
        app = None

# Sample data model for testing
class PersonModel(Observable):
    """Sample observable model with various properties for testing."""
    name = ObservableProperty("")
    age = ObservableProperty(0)
    email = ObservableProperty("")
    address = ObservableProperty("")
    
    def __init__(self, name="", age=0, email="", address=""):
        # Initialize Observable
        super().__init__()
        
        # Set initial values
        self.name = name
        self.age = age
        self.email = email
        self.address = address

class TestCommandLineEdit:
    """Test suite for CommandLineEdit widget."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear registries
        get_id_registry().clear()
        get_command_manager().clear()
        
        # Create test objects
        self.person = PersonModel("John Doe", 30, "john@example.com")
        
        # Create form container
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.container_id = get_id_registry().register(self.container, "cw")
        
        # Create command widgets
        self.name_edit = CommandLineEdit(self.container_id)
        self.email_edit = CommandLineEdit(self.container_id)
        
        # Add to layout
        self.layout.addWidget(self.name_edit)
        self.layout.addWidget(self.email_edit)
    
    def teardown_method(self):
        """Clean up after each test method."""
        self.container.deleteLater()
    
    def test_widget_registration(self):
        """Test that widgets are properly registered with the ID system."""
        # Verify widgets are registered
        assert self.name_edit.get_id() is not None
        assert self.email_edit.get_id() is not None
        
        # Verify registry can retrieve widgets
        registry = get_id_registry()
        assert registry.get_widget(self.name_edit.get_id()) is self.name_edit
        assert registry.get_widget(self.email_edit.get_id()) is self.email_edit
        
        # Verify container relationship
        container_id = registry.get_container_id_from_widget_id(self.name_edit.get_id())
        assert container_id == self.container_id
    
    def test_basic_property_binding(self):
        """Test binding widget to observable property."""
        # Bind widgets to observable properties
        self.name_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Verify initial value set in widget
        assert self.name_edit.text() == "John Doe"
        
        # Modify the observable
        self.person.name = "Jane Smith"
        
        # Verify widget updates
        assert self.name_edit.text() == "Jane Smith"
    
    def test_command_generation_immediate(self):
        """Test command generation in IMMEDIATE mode."""
        # Set up observable tracking
        property_changes = []
        
        class NameObserver:
            def on_name_changed(self, property_name, old_value, new_value):
                property_changes.append((property_name, old_value, new_value))
        
        # Create observer object and register
        observer = NameObserver()
        self.person.add_property_observer("name", observer.on_name_changed, observer)
        
        # Bind widget with immediate updates
        self.name_edit.bind_to_text_property(self.person.get_id(), "name")
        self.name_edit.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        
        # Change text in widget
        self.name_edit.setText("New Name")
        
        # Process events to ensure commands are executed
        QApplication.processEvents()
        
        # Verify the observable was updated via command
        assert self.person.name == "New Name"
        assert len(property_changes) == 1
        assert property_changes[0] == ("name", "John Doe", "New Name")
        
        # Verify the command is in history
        command_manager = get_command_manager()
        assert command_manager.can_undo()
        
        # Undo the command
        command_manager.undo()
        
        # Verify value reverted
        assert self.person.name == "John Doe"
        assert self.name_edit.text() == "John Doe"
    
    def test_command_generation_on_edit_finished(self):
        """Test command generation in ON_EDIT_FINISHED mode."""
        # Bind widget with edit finished mode (default)
        self.name_edit.bind_to_text_property(self.person.get_id(), "name")
        self.name_edit.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
        
        # Change text but don't finish editing
        self.name_edit.setText("Intermediate")
        
        # Process events
        QApplication.processEvents()
        
        # Observable should not have changed yet
        assert self.person.name == "John Doe"
        
        # Simulate editing finished
        self.name_edit.editingFinished.emit()
        
        # Process events
        QApplication.processEvents()
        
        # Now observable should be updated
        assert self.person.name == "Intermediate"
        
        # Verify command in history
        command_manager = get_command_manager()
        assert command_manager.can_undo()
    
    def test_command_generation_delayed(self):
        """Test command generation in DELAYED mode."""
        # Bind widget with delayed updates - 100ms delay
        self.name_edit.bind_to_text_property(self.person.get_id(), "name")
        self.name_edit.set_command_trigger_mode(CommandTriggerMode.DELAYED, 100)
        
        # Change text
        self.name_edit.setText("First Change")
        
        # Verify the change hasn't happened yet
        QApplication.processEvents()
        assert self.person.name == "John Doe"
        
        # Change text again before timer expires
        self.name_edit.setText("Second Change")
        
        # Wait for timer - using direct approach
        loop = QEventLoop()
        QTimer.singleShot(150, loop.quit)  # Wait slightly longer than the delay
        loop.exec()
        
        # Observable should now have the latest change
        assert self.person.name == "Second Change"
        
        # Only one command should be in history (batched changes)
        command_manager = get_command_manager()
        assert command_manager.can_undo()
        
        # Undo the command
        command_manager.undo()
        
        # Verify the change was undone
        assert self.person.name == "John Doe"
        assert self.name_edit.text() == "John Doe"
    
    def test_widget_property_update_avoids_recursion(self):
        """Test that widget property updates don't cause command loops."""
        # Track command executions
        command_count = [0]
        
        # Hook into command manager
        def after_execute(command, success):
            command_count[0] += 1
        
        command_manager = get_command_manager()
        command_manager.add_after_execute_callback("test", after_execute)
        
        # Bind widget
        self.name_edit.bind_to_text_property(self.person.get_id(), "name")
        self.name_edit.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        
        # Change text in widget
        self.name_edit.setText("New Text")
        
        # Process events
        QApplication.processEvents()
        
        # Verify only one command was executed
        assert command_count[0] == 1
        
        # Remove callback
        command_manager.remove_callback("test")
    
    def test_multiple_widgets_same_property(self):
        """Test multiple widgets bound to the same property."""
        # Create second widget bound to name
        second_name_edit = CommandLineEdit(self.container_id)
        self.layout.addWidget(second_name_edit)
        
        # Bind both widgets to same property
        self.name_edit.bind_to_text_property(self.person.get_id(), "name")
        second_name_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Change text in first widget
        self.name_edit.setText("Changed in Widget 1")
        self.name_edit.editingFinished.emit()
        
        # Process events
        QApplication.processEvents()
        
        # Verify second widget was updated
        assert second_name_edit.text() == "Changed in Widget 1"
        
        # Change text in second widget
        second_name_edit.setText("Changed in Widget 2")
        second_name_edit.editingFinished.emit()
        
        # Process events
        QApplication.processEvents()
        
        # Verify first widget was updated
        assert self.name_edit.text() == "Changed in Widget 2"
        
        # Verify observable has latest value
        assert self.person.name == "Changed in Widget 2"
        
        # Clean up
        second_name_edit.deleteLater()
    
    def test_unbind_property(self):
        """Test unbinding a property from a widget."""
        # Bind widget to property
        self.name_edit.bind_to_text_property(self.person.get_id(), "name")
        
        # Verify initial binding works
        assert self.name_edit.text() == "John Doe"
        self.person.name = "Changed Name"
        assert self.name_edit.text() == "Changed Name"
        
        # Unbind the property
        self.name_edit.unbind_text_property()
        
        # Change the observable again
        self.person.name = "After Unbind"
        
        # Widget should not update
        assert self.name_edit.text() == "Changed Name"
        
        # Changing widget should not create commands
        command_manager = get_command_manager()
        history_length = len(command_manager._history._executed_commands)
        
        self.name_edit.setText("Widget Change")
        self.name_edit.editingFinished.emit()
        
        # Process events
        QApplication.processEvents()
        
        # Verify no new commands were created
        assert len(command_manager._history._executed_commands) == history_length
        
        # Observable should not have changed
        assert self.person.name == "After Unbind"
    
    def test_widget_serialization(self):
        """Test serialization and deserialization of command widgets."""
        # Bind widgets to properties
        self.name_edit.bind_to_text_property(self.person.get_id(), "name")
        self.email_edit.bind_to_text_property(self.person.get_id(), "email")
        
        # Modify values
        self.name_edit.setText("Serialization Test")
        self.name_edit.editingFinished.emit()
        self.email_edit.setText("serialization@example.com")
        self.email_edit.editingFinished.emit()
        
        # Process events
        QApplication.processEvents()
        
        # Serialize widgets
        name_edit_state = self.name_edit.get_serialization()
        email_edit_state = self.email_edit.get_serialization()
        
        # Verify serialized state contains proper data
        assert name_edit_state["id"] == self.name_edit.get_id()
        assert "properties" in name_edit_state
        assert "text" in name_edit_state["properties"]
        assert name_edit_state["properties"]["text"]["value"] == "Serialization Test"
        
        # Change values again
        self.name_edit.setText("Changed Again")
        self.name_edit.editingFinished.emit()
        self.email_edit.setText("changed@example.com")
        self.email_edit.editingFinished.emit()
        
        # Process events
        QApplication.processEvents()
        
        # Verify values changed
        assert self.person.name == "Changed Again"
        assert self.person.email == "changed@example.com"
        
        # Deserialize widgets back to original state
        self.name_edit.deserialize(name_edit_state)
        self.email_edit.deserialize(email_edit_state)
        
        # Process events
        QApplication.processEvents()
        
        # Verify widgets and observable restored to serialized state
        assert self.name_edit.text() == "Serialization Test"
        assert self.email_edit.text() == "serialization@example.com"
        assert self.person.name == "Serialization Test"
        assert self.person.email == "serialization@example.com"


if __name__ == "__main__":
    # Run tests when script is executed directly
    setup_module()
    pytest.main(["-vs", __file__])
    teardown_module()