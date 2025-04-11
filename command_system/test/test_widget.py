"""
Comprehensive test suite for the PySide6 widget system.

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
from PySide6.QtCore import Qt, QTimer

from command_system.core import (
    Observable, ObservableProperty,
    Command, CompoundCommand, PropertyCommand, MacroCommand,
    get_command_manager
)
from command_system.id_system import get_id_registry, WidgetTypeCodes
from command_system.pyside6_widgets import (
    BaseCommandWidget,
    CommandTriggerMode,
    CommandLineEdit,
    CommandTabWidget,
    BaseCommandContainer
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
        assert self.name_edit.widget_id is not None
        assert self.email_edit.widget_id is not None
        
        # Verify registry can retrieve widgets
        registry = get_id_registry()
        assert registry.get_widget(self.name_edit.widget_id) is self.name_edit
        assert registry.get_widget(self.email_edit.widget_id) is self.email_edit
        
        # Verify container relationship
        container_id = registry.get_container_id_from_widget_id(self.name_edit.widget_id)
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
        
        # Wait a bit, but not enough for timer
        QTimer.singleShot(50, QApplication.processEvents)
        
        # Observable should not have changed yet
        assert self.person.name == "John Doe"
        
        # Change text again before timer expires
        self.name_edit.setText("Second Change")
        
        # Now wait for timer to definitely expire
        QTimer.singleShot(200, QApplication.processEvents)
        
        # Process events to ensure timer signals are processed
        QApplication.processEvents()
        
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
        assert name_edit_state["id"] == self.name_edit.widget_id
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


class TestCommandTabWidget:
    """Test suite for CommandTabWidget."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear registries
        get_id_registry().clear()
        get_command_manager().clear()
        
        # Create container
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.container_id = get_id_registry().register(self.container, "cw")
        
        # Create tab widget
        self.tab_widget = CommandTabWidget(container_id=self.container_id, parent=self.container)
        self.layout.addWidget(self.tab_widget)
        
        # Create tab pages
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        
        # Add tabs
        self.tab_widget.addTab(self.tab1, "Tab 1")
        self.tab_widget.addTab(self.tab2, "Tab 2")
        self.tab_widget.addTab(self.tab3, "Tab 3")
    
    def teardown_method(self):
        """Clean up after each test method."""
        self.container.deleteLater()
    
    def test_tab_widget_registration(self):
        """Test that the tab widget is properly registered."""
        # Verify widget is registered
        assert self.tab_widget.widget_id is not None
        
        # Verify registry can retrieve widget
        registry = get_id_registry()
        assert registry.get_widget(self.tab_widget.widget_id) is self.tab_widget
        
        # Verify container relationship
        container_id = registry.get_container_id_from_widget_id(self.tab_widget.widget_id)
        assert container_id == self.container_id
    
    def test_tab_change_command(self):
        """Test that changing tabs generates commands."""
        # Make sure we start on tab 0
        self.tab_widget.setCurrentIndex(0)
        
        # Set up command manager to track commands
        command_manager = get_command_manager()
        command_count = len(command_manager._history._executed_commands)
        
        # Change tab
        self.tab_widget.setCurrentIndex(1)
        
        # Process events
        QApplication.processEvents()
        
        # Verify command was created
        assert len(command_manager._history._executed_commands) > command_count
        assert command_manager.can_undo()
        
        # Undo the command
        command_manager.undo()
        
        # Verify tab selection is back to original
        assert self.tab_widget.currentIndex() == 0
        
        # Redo the command
        command_manager.redo()
        
        # Verify tab selection is changed again
        assert self.tab_widget.currentIndex() == 1
    
    def test_tab_widget_serialization(self):
        """Test serialization and deserialization of tab widget."""
        # Set to a specific tab
        self.tab_widget.setCurrentIndex(2)
        
        # Serialize the tab widget
        state = self.tab_widget.get_serialization()
        
        # Verify serialized state
        assert state["id"] == self.tab_widget.widget_id
        assert "current_index" in state
        assert state["current_index"] == 2
        
        # Change the current tab
        self.tab_widget.setCurrentIndex(0)
        assert self.tab_widget.currentIndex() == 0
        
        # Deserialize the tab widget
        self.tab_widget.deserialize(state)
        
        # Verify tab state is restored
        assert self.tab_widget.currentIndex() == 2


class TestComplexWidgetScenarios:
    """Test suite for complex widget scenarios."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear registries
        get_id_registry().clear()
        get_command_manager().clear()
        
        # Create test model
        self.person = PersonModel("John Doe", 30, "john@example.com", "123 Main St")
        
        # Create main container
        self.main_window = QWidget()
        self.main_layout = QVBoxLayout(self.main_window)
        self.main_id = get_id_registry().register(self.main_window, "w")
        
        # Create tab widget
        self.tab_widget = CommandTabWidget(container_id=self.main_id, parent=self.main_window)
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tab pages
        self.personal_tab = QWidget()
        self.personal_layout = QVBoxLayout(self.personal_tab)
        self.contact_tab = QWidget()
        self.contact_layout = QVBoxLayout(self.contact_tab)
        
        # Add tabs
        self.tab_widget.addTab(self.personal_tab, "Personal")
        self.tab_widget.addTab(self.contact_tab, "Contact")
        
        # Create form fields on personal tab
        self.name_edit = CommandLineEdit(self.tab_widget.widget_id)
        self.personal_layout.addWidget(self.name_edit)
        
        # Create form fields on contact tab
        self.email_edit = CommandLineEdit(self.tab_widget.widget_id)
        self.address_edit = CommandLineEdit(self.tab_widget.widget_id)
        self.contact_layout.addWidget(self.email_edit)
        self.contact_layout.addWidget(self.address_edit)
        
        # Bind widgets to model
        self.name_edit.bind_to_text_property(self.person.get_id(), "name")
        self.email_edit.bind_to_text_property(self.person.get_id(), "email")
        self.address_edit.bind_to_text_property(self.person.get_id(), "address")
    
    def teardown_method(self):
        """Clean up after each test method."""
        self.main_window.deleteLater()
    
    def test_form_data_binding(self):
        """Test form data binding across multiple tabs."""
        # Verify initial values
        assert self.name_edit.text() == "John Doe"
        assert self.email_edit.text() == "john@example.com"
        assert self.address_edit.text() == "123 Main St"
        
        # Modify values and verify commands
        command_manager = get_command_manager()
        
        # Switch to personal tab
        self.tab_widget.setCurrentIndex(0)
        QApplication.processEvents()
        
        # Change name
        self.name_edit.setText("Jane Smith")
        self.name_edit.editingFinished.emit()
        QApplication.processEvents()
        
        # Verify name updated
        assert self.person.name == "Jane Smith"
        
        # Switch to contact tab
        self.tab_widget.setCurrentIndex(1)
        QApplication.processEvents()
        
        # Change email and address
        self.email_edit.setText("jane@example.com")
        self.email_edit.editingFinished.emit()
        self.address_edit.setText("456 Oak Ave")
        self.address_edit.editingFinished.emit()
        QApplication.processEvents()
        
        # Verify contact info updated
        assert self.person.email == "jane@example.com"
        assert self.person.address == "456 Oak Ave"
        
        # Undo operations in reverse order
        assert command_manager.can_undo()
        command_manager.undo()  # Undo address change
        assert self.person.address == "123 Main St"
        assert self.address_edit.text() == "123 Main St"
        
        command_manager.undo()  # Undo email change
        assert self.person.email == "john@example.com"
        assert self.email_edit.text() == "john@example.com"
        
        command_manager.undo()  # Undo tab switch
        assert self.tab_widget.currentIndex() == 0
        
        command_manager.undo()  # Undo name change
        assert self.person.name == "John Doe"
        assert self.name_edit.text() == "John Doe"
    
    def test_recursive_container_serialization(self):
        """Test recursive serialization of container hierarchy."""
        # Modify form data
        self.name_edit.setText("Serialization Test")
        self.name_edit.editingFinished.emit()
        self.email_edit.setText("serialization@example.com")
        self.email_edit.editingFinished.emit()
        self.address_edit.setText("Serialization Address")
        self.address_edit.editingFinished.emit()
        
        # Switch to tab 1
        self.tab_widget.setCurrentIndex(1)
        
        # Process events
        QApplication.processEvents()
        
        # Serialize the main window (should recursively serialize all widgets)
        main_state = {}
        main_state["main_window"] = self.main_window
        main_state["tab_widget"] = self.tab_widget.get_serialization()
        main_state["name_edit"] = self.name_edit.get_serialization()
        main_state["email_edit"] = self.email_edit.get_serialization()
        main_state["address_edit"] = self.address_edit.get_serialization()
        main_state["person"] = self.person.serialize()
        
        # Change everything
        self.name_edit.setText("Changed Again")
        self.name_edit.editingFinished.emit()
        self.email_edit.setText("changed@example.com")
        self.email_edit.editingFinished.emit()
        self.address_edit.setText("Changed Address")
        self.address_edit.editingFinished.emit()
        self.tab_widget.setCurrentIndex(0)
        
        # Process events
        QApplication.processEvents()
        
        # Verify changes
        assert self.person.name == "Changed Again"
        assert self.person.email == "changed@example.com"
        assert self.person.address == "Changed Address"
        assert self.tab_widget.currentIndex() == 0
        
        # Deserialize everything
        self.person.deserialize(main_state["person"])
        self.tab_widget.deserialize(main_state["tab_widget"])
        self.name_edit.deserialize(main_state["name_edit"])
        self.email_edit.deserialize(main_state["email_edit"])
        self.address_edit.deserialize(main_state["address_edit"])
        
        # Process events
        QApplication.processEvents()
        
        # Verify everything restored
        assert self.person.name == "Serialization Test"
        assert self.person.email == "serialization@example.com"
        assert self.person.address == "Serialization Address"
        assert self.tab_widget.currentIndex() == 1
        assert self.name_edit.text() == "Serialization Test"
        assert self.email_edit.text() == "serialization@example.com"
        assert self.address_edit.text() == "Serialization Address"
    
    def test_complex_undo_redo_sequence(self):
        """Test complex sequence of commands with undo/redo."""
        # Get command manager
        command_manager = get_command_manager()
        
        # Clear any previous commands
        command_manager.clear()
        
        # Sequence of operations:
        # 1. Change name on personal tab
        # 2. Switch to contact tab
        # 3. Change email
        # 4. Change address
        # 5. Switch back to personal tab
        
        # Operation 1: Change name
        self.tab_widget.setCurrentIndex(0)
        QApplication.processEvents()
        self.name_edit.setText("Operation 1")
        self.name_edit.editingFinished.emit()
        QApplication.processEvents()
        
        # Operation 2: Switch to contact tab
        self.tab_widget.setCurrentIndex(1)
        QApplication.processEvents()
        
        # Operation 3: Change email
        self.email_edit.setText("operation3@example.com")
        self.email_edit.editingFinished.emit()
        QApplication.processEvents()
        
        # Operation 4: Change address
        self.address_edit.setText("Operation 4 Address")
        self.address_edit.editingFinished.emit()
        QApplication.processEvents()
        
        # Operation 5: Switch back to personal tab
        self.tab_widget.setCurrentIndex(0)
        QApplication.processEvents()
        
        # Verify final state
        assert self.person.name == "Operation 1"
        assert self.person.email == "operation3@example.com"
        assert self.person.address == "Operation 4 Address"
        assert self.tab_widget.currentIndex() == 0
        
        # Undo operations in reverse order
        
        # Undo operation 5
        command_manager.undo()
        QApplication.processEvents()
        assert self.tab_widget.currentIndex() == 1
        
        # Undo operation 4
        command_manager.undo()
        QApplication.processEvents()
        assert self.person.address == "123 Main St"
        assert self.address_edit.text() == "123 Main St"
        
        # Undo operation 3
        command_manager.undo()
        QApplication.processEvents()
        assert self.person.email == "john@example.com"
        assert self.email_edit.text() == "john@example.com"
        
        # Undo operation 2
        command_manager.undo()
        QApplication.processEvents()
        assert self.tab_widget.currentIndex() == 0
        
        # Undo operation 1
        command_manager.undo()
        QApplication.processEvents()
        assert self.person.name == "John Doe"
        assert self.name_edit.text() == "John Doe"
        
        # Verify we're back to initial state
        assert not command_manager.can_undo()
        assert command_manager.can_redo()
        
        # Now redo operations in forward order
        
        # Redo operation 1
        command_manager.redo()
        QApplication.processEvents()
        assert self.person.name == "Operation 1"
        assert self.name_edit.text() == "Operation 1"
        
        # Redo operation 2
        command_manager.redo()
        QApplication.processEvents()
        assert self.tab_widget.currentIndex() == 1
        
        # Redo operation 3
        command_manager.redo()
        QApplication.processEvents()
        assert self.person.email == "operation3@example.com"
        assert self.email_edit.text() == "operation3@example.com"
        
        # Redo operation 4
        command_manager.redo()
        QApplication.processEvents()
        assert self.person.address == "Operation 4 Address"
        assert self.address_edit.text() == "Operation 4 Address"
        
        # Redo operation 5
        command_manager.redo()
        QApplication.processEvents()
        assert self.tab_widget.currentIndex() == 0
        
        # Verify we're back to final state
        assert command_manager.can_undo()
        assert not command_manager.can_redo()


if __name__ == "__main__":
    # Run tests when script is executed directly
    setup_module()
    pytest.main(["-vs", __file__])
    teardown_module()