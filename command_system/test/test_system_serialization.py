"""
Comprehensive test suite for the serialization system.

This test suite focuses on verifying the correct functioning of the serialization system
across multiple levels:
- Subcontainer serialization and restoration
- Cascading unregistration effects
- Command-based serialization for undo/redo operations
- Tab widget specific serialization tests
"""
import pytest
import sys
import os
import time
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QTabWidget
from PySide6.QtCore import Qt, QTimer, QEventLoop

from command_system.core import (
    Observable, ObservableProperty,
    Command, CompoundCommand, PropertyCommand, MacroCommand, SerializationCommand,
    get_command_manager
)
from command_system.id_system import get_id_registry, WidgetTypeCodes, ContainerTypeCodes
from command_system.id_system.core.parser import (
    parse_widget_id, parse_observable_id, parse_property_id,
    get_unique_id_from_id, get_type_code_from_id
)
from command_system.pyside6_widgets import (
    BaseCommandWidget,
    CommandTriggerMode,
    CommandLineEdit,
    BaseCommandContainer,
    CommandTabWidget
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

# Sample data models for testing
class FormDataModel(Observable):
    """Sample observable model for form data."""
    name = ObservableProperty("")
    email = ObservableProperty("")
    
    def __init__(self, name="", email=""):
        super().__init__()
        self.name = name
        self.email = email

class TabDataModel(Observable):
    """Sample observable model for tab content."""
    title = ObservableProperty("")
    content = ObservableProperty("")
    
    def __init__(self, title="", content=""):
        super().__init__()
        self.title = title
        self.content = content

# Helper function to create content widgets
def create_content_widget(model: Optional[Observable] = None) -> QWidget:
    """Create a basic content widget for tabs."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # Add some content
    label = QLabel("Basic Content Widget")
    layout.addWidget(label)
    
    # If model provided, add bound fields
    if model and isinstance(model, TabDataModel):
        title_edit = CommandLineEdit()
        title_edit.bind_to_text_property(model.get_id(), "title")
        
        content_edit = CommandLineEdit()
        content_edit.bind_to_text_property(model.get_id(), "content")
        
        layout.addWidget(QLabel("Title:"))
        layout.addWidget(title_edit)
        layout.addWidget(QLabel("Content:"))
        layout.addWidget(content_edit)
    
    return widget

def create_form_widget(model: Optional[FormDataModel] = None) -> QWidget:
    """Create a form widget with input fields bound to a model."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # Add form fields
    layout.addWidget(QLabel("Form Widget"))
    
    # If model provided, add bound fields
    if model:
        name_edit = CommandLineEdit()
        name_edit.bind_to_text_property(model.get_id(), "name")
        name_edit.setObjectName("name_edit")  # For easier lookup
        
        email_edit = CommandLineEdit()
        email_edit.bind_to_text_property(model.get_id(), "email")
        email_edit.setObjectName("email_edit")  # For easier lookup
        
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(name_edit)
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(email_edit)
    
    return widget

# Process Qt events and wait for a specified time
def process_events_and_wait(ms=50):
    """Process events and wait for specified milliseconds."""
    QApplication.processEvents()
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()

# Diagnostic function to print ID system state
def print_id_system_state(prefix="", container_widget_ids=[], observable_ids=[], property_ids=[]):
    """Print the current state of the ID system for diagnostic purposes."""
    registry = get_id_registry()
    
    # Get all widget IDs - there's no direct method to get all widgets,
    # so we'll estimate using container queries
    existing_container_widgets_ids = []
    for widget in container_widget_ids:
        if registry.is_id_registered(widget):
            existing_container_widgets_ids.append(widget)
    
    # For observables, we can check the registry's internal state if available
    existing_observable_ids = []
    for observable in observable_ids:
        if registry.is_id_registered(observable):
            existing_observable_ids.append(observable)
    
    # For properties, we can check observables and collect their properties
    existing_property_ids = []
    for property in property_ids:
        if registry.is_id_registered(property):
            existing_property_ids.append(property)
    
    print(f"===== {prefix} ID SYSTEM STATE =====")
    print(f"widgets: {len(existing_container_widgets_ids)}")
    for wid in existing_container_widgets_ids:
        widget = registry.get_widget(wid)
        print(f"  {wid} -> {widget}")
    
    print(f"Observables: {len(existing_observable_ids)}")
    for oid in existing_observable_ids:
        obs = registry.get_observable(oid)
        print(f"  {oid} -> {obs}")
    
    print(f"Properties: {len(existing_property_ids)}")
    for pid in existing_property_ids:
        prop = registry.get_observable_property(pid)
        print(f"  {pid} -> {prop}")
    print("===============================")

class TestSystemSerialization:
    """Comprehensive test suite for serialization system."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Clear registries
        get_id_registry().clear()
        get_command_manager().clear()
        
        # Create main container
        self.main_container = QWidget()
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_container_id = get_id_registry().register(self.main_container, "cw")
        
        # Create tab widget
        self.tab_widget = CommandTabWidget(container_id=self.main_container_id)
        self.main_layout.addWidget(self.tab_widget)
        
        # Track created observables for cleanup
        self.observables = []
        
        # Track command execution
        self.command_executions = []
        
        # Set up command tracking
        def after_execute(command, success):
            self.command_executions.append((command, success))
        
        get_command_manager().add_after_execute_callback("test", after_execute)
    
    def teardown_method(self):
        """Clean up after each test method."""
        # Remove command tracking
        get_command_manager().remove_callback("test")
        
        # Clean up container
        self.main_container.deleteLater()
        
        # Process events before ending test
        process_events_and_wait()
    
    def test_subcontainer_unregister_cascade_effect(self):
        """Test cascading effects when unregistering a subcontainer."""
        print("\n===== STARTING test_subcontainer_unregister_cascade_effect =====")
        
        container_widget_ids = []
        observable_ids = []
        property_ids = []
        
        # Create a model for tab content
        form_model = FormDataModel("Test User", "test@example.com")
        
        self.observables.append(form_model)
        observable_ids.append(form_model.get_id())
        
        # Register tab type with model
        form_tab_type = self.tab_widget.register_tab(
            factory_func=create_form_widget,
            tab_name="Form Tab",
            observables=[form_model.get_id()]  # Pass existing model ID
        )
        
        # Add tab
        tab_id = self.tab_widget.add_tab(form_tab_type)
        container_widget_ids.append(tab_id)
        process_events_and_wait()
        
        print("Tab added to tab widget")
        print(f"Tab ID: {tab_id}")
        print(f"Form Model ID: {form_model.get_id()}")
        
        # Verify tab was added
        assert self.tab_widget.count() == 1
        
        # Find the form widget and its LineEdit controls
        tab_widget = self.tab_widget.widget(0)
        name_edit = tab_widget.findChild(CommandLineEdit, "name_edit")
        email_edit = tab_widget.findChild(CommandLineEdit, "email_edit")
        
        assert name_edit is not None, "Could not find name_edit"
        assert email_edit is not None, "Could not find email_edit"
        
        # Get LineEdit IDs and their controlled property IDs
        name_edit_id = get_id_registry().get_id(name_edit)
        email_edit_id = get_id_registry().get_id(email_edit)
        
        name_property_id = name_edit._controlled_properties.get("text")
        email_property_id = email_edit._controlled_properties.get("text")
        
        print(f"Name Edit ID: {name_edit_id}")
        print(f"Email Edit ID: {email_edit_id}")
        print(f"Name Property ID: {name_property_id}")
        print(f"Email Property ID: {email_property_id}")
        container_widget_ids.append(name_edit_id)
        container_widget_ids.append(email_edit_id)
        property_ids.append(name_property_id)
        property_ids.append(email_property_id)
        
        
        # Print initial state
        print_id_system_state("BEFORE CLOSING TAB", container_widget_ids, observable_ids, property_ids)
        
        # Attempt to count components before closing
        registry = get_id_registry()
        # Store references to widgets and their ids for later comparison
        all_widgets_before = set()
        for w in [self.tab_widget.widget(i) for i in range(self.tab_widget.count())]:
            all_widgets_before.add(registry.get_id(w))
            for child in w.findChildren(QWidget):
                widget_id = registry.get_id(child)
                if widget_id:
                    all_widgets_before.add(widget_id)
        
        # Get observable IDs
        all_observable_ids_before = []
        if hasattr(registry, '_observables'):
            all_observable_ids_before = list(registry._observables.keys())
        
        # Collect property IDs
        all_property_ids_before = []
        for obs_id in all_observable_ids_before:
            props = registry.get_observable_properties(obs_id) or []
            all_property_ids_before.extend(props)
        
        # Serialize the subcontainer before closing
        serialized_state = self.tab_widget.serialize_subcontainer(tab_id)
        
        # Verify we have a valid serialization
        assert serialized_state is not None
        assert "id" in serialized_state
        assert "type" in serialized_state
        assert "location" in serialized_state
        assert "children" in serialized_state
        
        print("Serialized subcontainer before closing")
        
        # Close the tab and verify it closes
        self.tab_widget.close_tab(0)
        process_events_and_wait()
        
        assert self.tab_widget.count() == 0, "Tab was not closed"
        
        # Print state after closing
        print_id_system_state("AFTER CLOSING TAB", container_widget_ids, observable_ids, property_ids)
        
        # Collect components after closing to verify cascade
        all_widgets_after = set()
        for w in [self.tab_widget.widget(i) for i in range(self.tab_widget.count())]:
            all_widgets_after.add(registry.get_id(w))
            for child in w.findChildren(QWidget):
                widget_id = registry.get_id(child)
                if widget_id:
                    all_widgets_after.add(widget_id)
        
        # Get observable IDs after closing
        all_observable_ids_after = []
        if hasattr(registry, '_observables'):
            all_observable_ids_after = list(registry._observables.keys())
            
        # Collect property IDs after closing
        all_property_ids_after = []
        for obs_id in all_observable_ids_after:
            props = registry.get_observable_properties(obs_id) or []
            all_property_ids_after.extend(props)
    
        # Verify that closure caused unregistration
        assert len(all_widgets_after) < len(all_widgets_before), "Widgets were not unregistered"
        
        # Deleted widgets should no longer be in registry
        for widget_id in all_widgets_before - all_widgets_after:
            assert registry.get_widget(widget_id) is None, f"Widget {widget_id} still in registry"
        
        # Check if specific components are unregistered
        assert registry.get_widget(name_edit_id) is None, "Name edit was not unregistered"
        assert registry.get_widget(email_edit_id) is None, "Email edit was not unregistered"
        assert registry.get_observable_property(name_property_id) is None, "Name property was not unregistered"
        assert registry.get_observable_property(email_property_id) is None, "Email property was not unregistered"
        
        print("All components properly unregistered")
        
        # Deserialize the subcontainer
        result = self.tab_widget.deserialize_subcontainer(
            serialized_state["type"],
            serialized_state["location"],
            serialized_state
        )
        
        assert result
        assert result in container_widget_ids
        process_events_and_wait(100)  # Longer wait for complex restoration
        
        # Verify tab was restored
        assert self.tab_widget.count() == 1, "Tab was not restored"
        
        # Print state after restoration
        print_id_system_state("AFTER RESTORING TAB", container_widget_ids, observable_ids, property_ids)
        
        # Find the restored widgets and verify they have new IDs (different from originals)
        restored_tab_widget = self.tab_widget.widget(0)
        restored_name_edit = restored_tab_widget.findChild(CommandLineEdit, "name_edit")
        restored_email_edit = restored_tab_widget.findChild(CommandLineEdit, "email_edit")
        
        assert restored_name_edit is not None, "Could not find restored name_edit"
        assert restored_email_edit is not None, "Could not find restored email_edit"
        
        restored_name_edit_id = get_id_registry().get_id(restored_name_edit)
        restored_email_edit_id = get_id_registry().get_id(restored_email_edit)
        
        print(f"Restored Name Edit ID: {restored_name_edit_id}")
        print(f"Restored Email Edit ID: {restored_email_edit_id}")
        
        # Verify the IDs are different (new instances)
        assert restored_name_edit_id != name_edit_id, "Name edit has same ID after restoration"
        assert restored_email_edit_id != email_edit_id, "Email edit has same ID after restoration"
        
        # Verify bound controls work with the model
        assert restored_name_edit.text() == form_model.name, "Name edit not correctly bound"
        assert restored_email_edit.text() == form_model.email, "Email edit not correctly bound"
        
        # Modify the model and verify controls update
        form_model.name = "Updated User"
        form_model.email = "updated@example.com"
        process_events_and_wait()
        
        assert restored_name_edit.text() == "Updated User", "Name edit not updating"
        assert restored_email_edit.text() == "updated@example.com", "Email edit not updating"
        
        # Modify the controls and verify model updates
        restored_name_edit.setText("Control Updated")
        restored_name_edit.editingFinished.emit()
        process_events_and_wait()
        
        assert form_model.name == "Control Updated", "Model not updating from edit"
        
        print("Serialization and deserialization successful")
        print("===== COMPLETED test_subcontainer_unregister_cascade_effect =====")
    
    def test_tab_serialization_with_undo_redo(self):
        """Test tab serialization with undo/redo operations."""
        print("\n===== STARTING test_tab_serialization_with_undo_redo =====")
        # Create a model for tabs
        tab_model = TabDataModel("Original Title", "Original Content")
        self.observables.append(tab_model)
        
        # Register tab type with model
        content_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Content Tab",
            observables=[tab_model.get_id()]
        )
        
        # Print initial state
        print_id_system_state("BEFORE ADDING TAB")
        
        # Reset command tracking
        self.command_executions = []
        
        # Add tab - this should generate a command
        tab_id = self.tab_widget.add_tab(content_tab_type)
        process_events_and_wait()
        
        print(f"Added tab with ID: {tab_id}")
        print(f"Tab Model ID: {tab_model.get_id()}")
        
        # Verify command was created
        assert len(self.command_executions) == 1, "No command created for adding tab"
        assert isinstance(self.command_executions[0][0], SerializationCommand), "Wrong command type"
        
        # Find title edit field in tab
        tab_widget = self.tab_widget.widget(0)
        title_edits = [w for w in tab_widget.findChildren(CommandLineEdit) 
                      if hasattr(w, '_controlled_properties') and 'text' in w._controlled_properties]
        
        assert len(title_edits) > 0, "Could not find title edit"
        title_edit = title_edits[0]
        
        # Get edit ID and property ID for verification
        title_edit_id = get_id_registry().get_id(title_edit)
        title_property_id = title_edit._controlled_properties.get("text")
        
        print(f"Title Edit ID: {title_edit_id}")
        print(f"Title Property ID: {title_property_id}")
        
        # Verify initial value
        assert title_edit.text() == "Original Title", "Initial title not set"
        
        # Change title - this should generate another command
        title_edit.setText("Modified Title")
        title_edit.editingFinished.emit()
        process_events_and_wait()
        
        print("Modified title - should create a property command")
        
        # Verify property command was created
        assert len(self.command_executions) == 2, "No command created for property change"
        
        # Print state after modification
        print_id_system_state("AFTER MODIFYING TITLE")
        
        # Get command manager
        cmd_manager = get_command_manager()
        
        # Undo title change
        assert cmd_manager.can_undo(), "Cannot undo property change"
        cmd_manager.undo()
        process_events_and_wait()
        
        print("Undid title change")
        
        # Verify title was restored
        assert tab_model.title == "Original Title", "Title not restored in model"
        assert title_edit.text() == "Original Title", "Title not restored in edit"
        
        # Undo tab addition - this should unregister all components
        assert cmd_manager.can_undo(), "Cannot undo tab addition"
        cmd_manager.undo()
        process_events_and_wait(100)  # Longer wait for complex operation
        
        print("Undid tab addition - should unregister all components")
        
        # Verify tab was removed
        assert self.tab_widget.count() == 0, "Tab not removed"
        
        # Print state after undo
        print_id_system_state("AFTER UNDO TAB ADDITION")
        
        # Verify components were unregistered
        registry = get_id_registry()
        assert registry.get_widget(title_edit_id) is None, "Title edit still registered"
        
        # The observable should still exist since we kept a reference
        assert registry.get_observable(tab_model.get_id()) is tab_model, "Observable incorrectly unregistered"
        
        # Redo tab addition - should restore tab and all components
        assert cmd_manager.can_redo(), "Cannot redo tab addition"
        cmd_manager.redo()
        process_events_and_wait(100)
        
        print("Redid tab addition - should restore all components")
        
        # Verify tab was restored
        assert self.tab_widget.count() == 1, "Tab not restored"
        
        # Find restored title edit
        restored_tab_widget = self.tab_widget.widget(0)
        restored_title_edits = [w for w in restored_tab_widget.findChildren(CommandLineEdit) 
                             if hasattr(w, '_controlled_properties') and 'text' in w._controlled_properties]
        
        assert len(restored_title_edits) > 0, "Could not find restored title edit"
        restored_title_edit = restored_title_edits[0]
        
        # Get restored edit ID
        restored_title_edit_id = get_id_registry().get_id(restored_title_edit)
        
        print(f"Restored Title Edit ID: {restored_title_edit_id}")
        
        # Verify it's a new instance
        assert restored_title_edit_id != title_edit_id, "Title edit has same ID after restoration"
        
        # Verify value is original (pre-modification)
        assert restored_title_edit.text() == "Original Title", "Title not restored to original value"
        
        # Redo title modification
        assert cmd_manager.can_redo(), "Cannot redo title modification"
        cmd_manager.redo()
        process_events_and_wait()
        
        print("Redid title modification")
        
        # Verify title was modified
        assert tab_model.title == "Modified Title", "Title not modified in model after redo"
        assert restored_title_edit.text() == "Modified Title", "Title not modified in edit after redo"
        
        # Print final state
        print_id_system_state("FINAL STATE")
        
        print("Undo/redo serialization test completed successfully")
        print("===== COMPLETED test_tab_serialization_with_undo_redo =====")
    
    def test_close_tab_undo_redo(self):
        """Test closing a tab and undoing/redoing the operation."""
        print("\n===== STARTING test_close_tab_undo_redo =====")
        # Create form models for two tabs
        form_model1 = FormDataModel("User One", "one@example.com")
        form_model2 = FormDataModel("User Two", "two@example.com")
        self.observables.extend([form_model1, form_model2])
        
        # Register tab type with model class
        form_tab_type = self.tab_widget.register_tab(
            factory_func=create_form_widget,
            tab_name="Form Tab",
            observables=[FormDataModel]  # Use class to create new instances
        )
        
        # Add two tabs with separate instances
        tab1_id = self.tab_widget.add_tab(form_tab_type)
        tab2_id = self.tab_widget.add_tab(form_tab_type)
        process_events_and_wait()
        
        # Verify tabs were added
        assert self.tab_widget.count() == 2, "Failed to add two tabs"
        
        print(f"Added Tab 1 ID: {tab1_id}")
        print(f"Added Tab 2 ID: {tab2_id}")
        
        # Find the form widgets and their LineEdit controls
        tab1_widget = self.tab_widget.widget(0)
        tab2_widget = self.tab_widget.widget(1)
        
        name_edit1 = tab1_widget.findChild(CommandLineEdit, "name_edit")
        email_edit1 = tab1_widget.findChild(CommandLineEdit, "email_edit")
        name_edit2 = tab2_widget.findChild(CommandLineEdit, "name_edit")
        email_edit2 = tab2_widget.findChild(CommandLineEdit, "email_edit")
        
        assert name_edit1 is not None, "Could not find name_edit in tab 1"
        assert email_edit1 is not None, "Could not find email_edit in tab 1"
        assert name_edit2 is not None, "Could not find name_edit in tab 2"
        assert email_edit2 is not None, "Could not find email_edit in tab 2"
        
        # Get edit IDs for verification
        name_edit1_id = get_id_registry().get_id(name_edit1)
        email_edit1_id = get_id_registry().get_id(email_edit1)
        name_edit2_id = get_id_registry().get_id(name_edit2)
        email_edit2_id = get_id_registry().get_id(email_edit2)
        
        print(f"Tab 1 Name Edit ID: {name_edit1_id}")
        print(f"Tab 1 Email Edit ID: {email_edit1_id}")
        print(f"Tab 2 Name Edit ID: {name_edit2_id}")
        print(f"Tab 2 Email Edit ID: {email_edit2_id}")
        
        # Identify the observable models created for each tab
        # They should be different instances since we passed the class
        registry = get_id_registry()
        
        # First, find the property IDs
        name_property1_id = name_edit1._controlled_properties.get("text")
        email_property1_id = email_edit1._controlled_properties.get("text")
        name_property2_id = name_edit2._controlled_properties.get("text")
        email_property2_id = email_edit2._controlled_properties.get("text")
        
        # Then find the observable IDs
        observable1_id = registry.get_observable_id_from_property_id(name_property1_id)
        observable2_id = registry.get_observable_id_from_property_id(name_property2_id)
        
        # Get the actual observable instances
        tab1_model = registry.get_observable(observable1_id)
        tab2_model = registry.get_observable(observable2_id)
        
        assert tab1_model is not None, "Could not find tab 1 model"
        assert tab2_model is not None, "Could not find tab 2 model"
        assert tab1_model is not tab2_model, "Tab models are the same instance"
        
        print(f"Tab 1 Model ID: {observable1_id}")
        print(f"Tab 2 Model ID: {observable2_id}")
        
        # Set values via edits
        name_edit1.setText("Modified User One")
        name_edit1.editingFinished.emit()
        email_edit2.setText("modified_two@example.com")
        email_edit2.editingFinished.emit()
        process_events_and_wait()
        
        # Verify model values were updated
        assert tab1_model.name == "Modified User One", "Tab 1 model name not updated"
        assert tab2_model.email == "modified_two@example.com", "Tab 2 model email not updated"
        
        # Print state before closing tab
        print_id_system_state("BEFORE CLOSING TAB")
        
        # Reset command tracking
        self.command_executions = []
        
        # Close the first tab via tabCloseRequested signal
        self.tab_widget.tabCloseRequested.emit(0)
        process_events_and_wait()
        
        # Verify command was created for tab close
        assert len(self.command_executions) == 1, "No command created for tab close"
        assert isinstance(self.command_executions[0][0], SerializationCommand), "Wrong command type"
        
        # Verify first tab was closed
        assert self.tab_widget.count() == 1, "Tab was not closed"
        
        # Print state after closing tab
        print_id_system_state("AFTER CLOSING TAB")
        
        # Verify first tab components were unregistered
        assert registry.get_widget(name_edit1_id) is None, "Name edit 1 still registered"
        assert registry.get_widget(email_edit1_id) is None, "Email edit 1 still registered"
        assert registry.get_observable_property(name_property1_id) is None, "Name property 1 still registered"
        assert registry.get_observable_property(email_property1_id) is None, "Email property 1 still registered"
        assert registry.get_observable(observable1_id) is None, "Observable 1 still registered"
        
        # Verify second tab components still exist
        assert registry.get_widget(name_edit2_id) is not None, "Name edit 2 was unregistered"
        assert registry.get_widget(email_edit2_id) is not None, "Email edit 2 was unregistered"
        assert registry.get_observable(observable2_id) is not None, "Observable 2 was unregistered"
        
        # Get command manager
        cmd_manager = get_command_manager()
        
        # Undo the close operation
        assert cmd_manager.can_undo(), "Cannot undo tab close"
        cmd_manager.undo()
        process_events_and_wait(100)  # Longer wait for complex operation
        
        print("Undid tab close - should restore all components")
        
        # Verify both tabs are now present
        assert self.tab_widget.count() == 2, "First tab not restored"
        
        # Print state after undo
        print_id_system_state("AFTER UNDO TAB CLOSE")
        
        # Find restored first tab widgets
        restored_tab1_widget = self.tab_widget.widget(0)
        restored_name_edit1 = restored_tab1_widget.findChild(CommandLineEdit, "name_edit")
        restored_email_edit1 = restored_tab1_widget.findChild(CommandLineEdit, "email_edit")
        
        assert restored_name_edit1 is not None, "Could not find restored name_edit in tab 1"
        assert restored_email_edit1 is not None, "Could not find restored email_edit in tab 1"
        
        # Get restored edit IDs
        restored_name_edit1_id = get_id_registry().get_id(restored_name_edit1)
        restored_email_edit1_id = get_id_registry().get_id(restored_email_edit1)
        
        print(f"Restored Tab 1 Name Edit ID: {restored_name_edit1_id}")
        print(f"Restored Tab 1 Email Edit ID: {restored_email_edit1_id}")
        
        # Verify they are new instances
        assert restored_name_edit1_id != name_edit1_id, "Name edit 1 has same ID after restoration"
        assert restored_email_edit1_id != email_edit1_id, "Email edit 1 has same ID after restoration"
        
        # Get the restored model
        restored_name_property1_id = restored_name_edit1._controlled_properties.get("text")
        restored_observable1_id = registry.get_observable_id_from_property_id(restored_name_property1_id)
        restored_tab1_model = registry.get_observable(restored_observable1_id)
        
        print(f"Restored Tab 1 Model ID: {restored_observable1_id}")
        
        # Verify restored model has the same values
        assert restored_tab1_model.name == "Modified User One", "Restored tab 1 model name incorrect"
        assert restored_name_edit1.text() == "Modified User One", "Restored name edit 1 text incorrect"
        
        # Redo the close operation
        assert cmd_manager.can_redo(), "Cannot redo tab close"
        cmd_manager.redo()
        process_events_and_wait(100)
        
        print("Redid tab close - should unregister components again")
        
        # Verify first tab is closed again
        assert self.tab_widget.count() == 1, "First tab not closed again"
        
        # Print final state
        print_id_system_state("FINAL STATE")
        
        print("Close tab undo/redo test completed successfully")
        print("===== COMPLETED test_close_tab_undo_redo =====")
    
    def test_complete_serialization_workflow(self):
        """Test comprehensive serialization workflow with multiple tabs and operations."""
        print("\n===== STARTING test_complete_serialization_workflow =====")
        # Create form models
        form_model = FormDataModel("Test User", "test@example.com")
        self.observables.append(form_model)
        
        tab_model = TabDataModel("Test Title", "Test Content")
        self.observables.append(tab_model)
        
        # Register tab types
        form_tab_type = self.tab_widget.register_tab(
            factory_func=create_form_widget,
            tab_name="Form Tab",
            observables=[form_model.get_id()]
        )
        
        content_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Content Tab",
            observables=[tab_model.get_id()]
        )
        
        # Print initial state
        print_id_system_state("INITIAL STATE")
        
        # Store initial widget references
        registry = get_id_registry()
        
        # Count unique widget IDs
        initial_widgets = set()
        for widget in [self.tab_widget]:
            widget_id = registry.get_id(widget)
            if widget_id:
                initial_widgets.add(widget_id)
        
        # Count observable IDs
        initial_observable_ids = []
        if hasattr(registry, '_observables'):
            initial_observable_ids = list(registry._observables.keys())
        else:
            # Alternative: use the observable references we have
            for model in self.observables:
                model_id = registry.get_id(model)
                if model_id:
                    initial_observable_ids.append(model_id)
                    
        # Count property IDs
        initial_property_ids = []
        for obs_id in initial_observable_ids:
            props = registry.get_observable_properties(obs_id) or []
            initial_property_ids.extend(props)
            
        print(f"Initial counts - Widgets: {len(initial_widgets)}, Observables: {len(initial_observable_ids)}, Properties: {len(initial_property_ids)}")
        
        # Add tabs
        form_tab_id = self.tab_widget.add_tab(form_tab_type)
        content_tab_id = self.tab_widget.add_tab(content_tab_type)
        process_events_and_wait()
        
        # Verify tabs were added
        assert self.tab_widget.count() == 2, "Failed to add both tabs"
        
        print(f"Added Form Tab ID: {form_tab_id}")
        print(f"Added Content Tab ID: {content_tab_id}")
        
        # Get tab widgets
        form_tab_widget = self.tab_widget.widget(0)
        content_tab_widget = self.tab_widget.widget(1)
        
        # Find edit controls
        form_name_edit = form_tab_widget.findChild(CommandLineEdit, "name_edit")
        form_email_edit = form_tab_widget.findChild(CommandLineEdit, "email_edit")
        
        content_title_edits = [w for w in content_tab_widget.findChildren(CommandLineEdit) 
                             if hasattr(w, '_controlled_properties') and 'text' in w._controlled_properties]
        content_title_edit = content_title_edits[0] if content_title_edits else None
        
        assert form_name_edit is not None, "Could not find form name edit"
        assert form_email_edit is not None, "Could not find form email edit"
        assert content_title_edit is not None, "Could not find content title edit"
        
        # Verify initial values
        assert form_name_edit.text() == "Test User", "Form name not initialized correctly"
        assert form_email_edit.text() == "test@example.com", "Form email not initialized correctly"
        assert content_title_edit.text() == "Test Title", "Content title not initialized correctly"
        
        # Record widget IDs after adding tabs
        after_add_widgets = set()
        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if tab_widget:
                widget_id = registry.get_id(tab_widget)
                if widget_id:
                    after_add_widgets.add(widget_id)
                for child in tab_widget.findChildren(QWidget):
                    child_id = registry.get_id(child)
                    if child_id:
                        after_add_widgets.add(child_id)
        
        # Add the tab widget itself
        tab_widget_id = registry.get_id(self.tab_widget)
        if tab_widget_id:
            after_add_widgets.add(tab_widget_id)
            
        # Count observable IDs
        after_add_observables = []
        if hasattr(registry, '_observables'):
            after_add_observables = list(registry._observables.keys())
        else:
            # Alternative: use the observable references we have
            for model in self.observables:
                model_id = registry.get_id(model)
                if model_id:
                    after_add_observables.append(model_id)
                    
        # Count property IDs
        after_add_properties = []
        for obs_id in after_add_observables:
            props = registry.get_observable_properties(obs_id) or []
            after_add_properties.extend(props)
            
        print(f"After adding tabs - Widgets: {len(after_add_widgets)}, Observables: {len(after_add_observables)}, Properties: {len(after_add_properties)}")
        
        # Modify values via edits
        form_name_edit.setText("Modified User")
        form_name_edit.editingFinished.emit()
        content_title_edit.setText("Modified Title")
        content_title_edit.editingFinished.emit()
        process_events_and_wait()
        
        # Verify model values were updated
        assert form_model.name == "Modified User", "Form model name not updated"
        assert tab_model.title == "Modified Title", "Tab model title not updated"
        
        # Print state after modifications
        print_id_system_state("AFTER MODIFICATIONS")
        
        # Serialize the entire tab widget
        serialized_state = self.tab_widget.get_serialization()
        
        # Verify serialized state has expected components
        assert "id" in serialized_state
        assert "current_index" in serialized_state
        assert "subcontainers" in serialized_state
        assert len(serialized_state["subcontainers"]) == 2
        
        print("Serialized entire tab widget")
        
        # Clear the tab widget (removing all tabs)
        self.tab_widget.clear()
        process_events_and_wait()
        
        # Verify tabs were removed
        assert self.tab_widget.count() == 0, "Failed to clear tabs"
        
        # Print state after clearing
        print_id_system_state("AFTER CLEARING TABS")
        
        # Count widgets after clearing
        after_clear_widgets = set()
        # Only count the tab widget since all tabs should be gone
        tab_widget_id = registry.get_id(self.tab_widget)
        if tab_widget_id:
            after_clear_widgets.add(tab_widget_id)
            
        # Count observable IDs
        after_clear_observables = []
        if hasattr(registry, '_observables'):
            after_clear_observables = list(registry._observables.keys())
        else:
            # Alternative: use the observable references we have
            for model in self.observables:
                model_id = registry.get_id(model)
                if model_id:
                    after_clear_observables.append(model_id)
                    
        # Count property IDs
        after_clear_properties = []
        for obs_id in after_clear_observables:
            props = registry.get_observable_properties(obs_id) or []
            after_clear_properties.extend(props)
            
        print(f"After clearing tabs - Widgets: {len(after_clear_widgets)}, Observables: {len(after_clear_observables)}, Properties: {len(after_clear_properties)}")
        
        # Verify tab-related components were unregistered
        assert len(after_clear_widgets) < len(after_add_widgets), "Widgets were not unregistered after clearing"
        
        # Re-register tab types (necessary for deserialization)
        form_tab_type = self.tab_widget.register_tab(
            factory_func=create_form_widget,
            tab_name="Form Tab",
            observables=[form_model.get_id()]
        )
        
        content_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Content Tab",
            observables=[tab_model.get_id()]
        )
        
        # Deserialize the tab widget
        result = self.tab_widget.deserialize(serialized_state)
        assert result, "Failed to deserialize tab widget"
        process_events_and_wait(200)  # Longer wait for complex restoration
        
        # Verify tabs were restored
        assert self.tab_widget.count() == 2, "Failed to restore tabs"
        
        # Print state after restoration
        print_id_system_state("AFTER RESTORATION")
        
        # Count widgets after restoration
        after_restore_widgets = set()
        for i in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(i)
            if tab_widget:
                widget_id = registry.get_id(tab_widget)
                if widget_id:
                    after_restore_widgets.add(widget_id)
                for child in tab_widget.findChildren(QWidget):
                    child_id = registry.get_id(child)
                    if child_id:
                        after_restore_widgets.add(child_id)
        
        # Add the tab widget itself
        tab_widget_id = registry.get_id(self.tab_widget)
        if tab_widget_id:
            after_restore_widgets.add(tab_widget_id)
            
        # Count observable IDs
        after_restore_observables = []
        if hasattr(registry, '_observables'):
            after_restore_observables = list(registry._observables.keys())
        else:
            # Alternative: use the observable references we have
            for model in self.observables:
                model_id = registry.get_id(model)
                if model_id:
                    after_restore_observables.append(model_id)
                    
        # Count property IDs
        after_restore_properties = []
        for obs_id in after_restore_observables:
            props = registry.get_observable_properties(obs_id) or []
            after_restore_properties.extend(props)
            
        print(f"After restoration - Widgets: {len(after_restore_widgets)}, Observables: {len(after_restore_observables)}, Properties: {len(after_restore_properties)}")
        
        # Find restored edit controls
        restored_form_tab = self.tab_widget.widget(0)
        restored_content_tab = self.tab_widget.widget(1)
        
        restored_form_name_edit = restored_form_tab.findChild(CommandLineEdit, "name_edit")
        restored_form_email_edit = restored_form_tab.findChild(CommandLineEdit, "email_edit")
        
        restored_content_title_edits = [w for w in restored_content_tab.findChildren(CommandLineEdit) 
                                      if hasattr(w, '_controlled_properties') and 'text' in w._controlled_properties]
        restored_content_title_edit = restored_content_title_edits[0] if restored_content_title_edits else None
        
        assert restored_form_name_edit is not None, "Could not find restored form name edit"
        assert restored_form_email_edit is not None, "Could not find restored form email edit"
        assert restored_content_title_edit is not None, "Could not find restored content title edit"
        
        # Verify restored values match the modified values before serialization
        assert restored_form_name_edit.text() == "Modified User", "Form name not restored correctly"
        assert restored_form_email_edit.text() == "test@example.com", "Form email not restored correctly"
        assert restored_content_title_edit.text() == "Modified Title", "Content title not restored correctly"
        
        # Verify model values are still correct
        assert form_model.name == "Modified User", "Form model name changed"
        assert tab_model.title == "Modified Title", "Tab model title changed"
        
        # Test bidirectional binding is working in restored tabs
        # Change model values
        form_model.name = "Model Updated"
        tab_model.title = "Model Title Updated"
        process_events_and_wait()
        
        # Verify controls update
        assert restored_form_name_edit.text() == "Model Updated", "Restored form edit not updating from model"
        assert restored_content_title_edit.text() == "Model Title Updated", "Restored content edit not updating from model"
        
        # Change control values
        restored_form_email_edit.setText("updated@example.com")
        restored_form_email_edit.editingFinished.emit()
        process_events_and_wait()
        
        # Verify model updates
        assert form_model.email == "updated@example.com", "Model not updating from restored edit"
        
        print("Complete serialization workflow test successful")
        print("===== COMPLETED test_complete_serialization_workflow =====")
    
    def test_tab_move_serialization(self):
        """Test serialization of tab widget after moving tabs around."""
        print("\n===== STARTING test_tab_move_serialization =====")
        # Create models
        model1 = TabDataModel("Tab 1", "Content 1")
        model2 = TabDataModel("Tab 2", "Content 2")
        model3 = TabDataModel("Tab 3", "Content 3")
        self.observables.extend([model1, model2, model3])
        
        # Register tab type
        tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Content Tab",
            observables=[TabDataModel]  # Use class to create new instances
        )
        
        # Add three tabs
        tab_id1 = self.tab_widget.add_tab(tab_type)
        tab_id2 = self.tab_widget.add_tab(tab_type)
        tab_id3 = self.tab_widget.add_tab(tab_type)
        process_events_and_wait()
        
        # Verify tabs were added
        assert self.tab_widget.count() == 3, "Failed to add three tabs"
        
        # Enable tab moving
        self.tab_widget.setMovable(True)
        
        # Record initial order by getting tab text
        initial_tab_widgets = [self.tab_widget.widget(i) for i in range(3)]
        initial_tab_ids = [get_id_registry().get_id(widget) for widget in initial_tab_widgets]
        
        print(f"Initial tab IDs: {initial_tab_ids}")
        
        # Move tab 0 to position 2
        self.tab_widget.tabBar().moveTab(0, 2)
        process_events_and_wait()
        
        # Verify tab order changed
        moved_tab_widgets = [self.tab_widget.widget(i) for i in range(3)]
        moved_tab_ids = [get_id_registry().get_id(widget) for widget in moved_tab_widgets]
        
        print(f"After move tab IDs: {moved_tab_ids}")
        
        # The first tab should now be at the end
        assert moved_tab_ids[2] == initial_tab_ids[0], "Tab not moved correctly"
        
        # Serialize tab widget with moved tabs
        serialized_state = self.tab_widget.get_serialization()
        
        # Verify serialization contains current tab order
        assert "subcontainers" in serialized_state
        assert len(serialized_state["subcontainers"]) == 3
        
        # Clear tab widget
        self.tab_widget.clear()
        process_events_and_wait()
        
        assert self.tab_widget.count() == 0, "Failed to clear tabs"
        
        # Re-register tab type
        tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Content Tab",
            observables=[TabDataModel]
        )
        
        # Deserialize with moved tab order
        result = self.tab_widget.deserialize(serialized_state)
        assert result, "Failed to deserialize tab widget"
        process_events_and_wait(100)
        
        # Verify tabs were restored with correct order
        assert self.tab_widget.count() == 3, "Failed to restore all tabs"
        
        restored_tab_widgets = [self.tab_widget.widget(i) for i in range(3)]
        restored_tab_ids = [get_id_registry().get_id(widget) for widget in restored_tab_widgets]
        
        print(f"Restored tab IDs: {restored_tab_ids}")
        
        # Verify order matches the moved order, not the initial order
        # We can't compare exact IDs since they're recreated, but we can check relative positions
        # through the tab contents
        
        # Navigate to the tabs and check their content
        # This part depends on finding a reliable way to identify the tabs,
        # we'll use the title edit values
        
        # Find the title edits in each tab
        title_edits = []
        for i in range(3):
            tab_widget = self.tab_widget.widget(i)
            edits = [w for w in tab_widget.findChildren(CommandLineEdit) 
                     if hasattr(w, '_controlled_properties') and 'text' in w._controlled_properties]
            if edits:
                title_edits.append(edits[0])
        
        # If we found all title edits, compare their values
        if len(title_edits) == 3:
            values = [edit.text() for edit in title_edits]
            print(f"Tab title values: {values}")
            
            # Since we're using new model instances, we can't verify exact titles
            # But we should have 3 distinct tabs
            assert len(set(values)) == 3, "Did not restore 3 distinct tabs"
        
        print("Tab move serialization test successful")
        print("===== COMPLETED test_tab_move_serialization =====")


if __name__ == "__main__":
    # Run tests when script is executed directly
    setup_module()
    pytest.main(["-v", __file__])
    teardown_module()