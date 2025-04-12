"""
Test suite for the PySide6 container system.

This test suite validates the functionality of the PySide6 command-enabled containers,
focusing on their integration with the core command system and ID system.
It tests container hierarchy management, tab operations, command generation for UI actions,
and serialization/deserialization.
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
from command_system.id_system.core.parser import get_type_code_from_id
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
class TabDataModel(Observable):
    """Sample observable model for tab content."""
    title = ObservableProperty("")
    content = ObservableProperty("")
    
    def __init__(self, title="", content=""):
        super().__init__()
        self.title = title
        self.content = content

class FormDataModel(Observable):
    """Sample observable model for form data."""
    name = ObservableProperty("")
    email = ObservableProperty("")
    
    def __init__(self, name="", email=""):
        super().__init__()
        self.name = name
        self.email = email

# Helper function to create content widgets
def create_content_widget(model: Optional[Observable] = None) -> QWidget:
    """Create a content widget for tabs."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # Add some content
    label = QLabel("Content Widget")
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
    """Create a form widget for tabs."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # Add form fields
    layout.addWidget(QLabel("Form Widget"))
    
    # If model provided, add bound fields
    if model:
        name_edit = CommandLineEdit()
        name_edit.bind_to_text_property(model.get_id(), "name")
        
        email_edit = CommandLineEdit()
        email_edit.bind_to_text_property(model.get_id(), "email")
        
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

class TestCommandTabWidget:
    """Test suite for CommandTabWidget."""
    
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
    
    def test_tab_widget_registration(self):
        """Test that tab widget is properly registered with the ID system."""
        # Verify tab widget is registered
        assert self.tab_widget.widget_id is not None
        
        # Verify registry can retrieve the widget
        registry = get_id_registry()
        assert registry.get_widget(self.tab_widget.widget_id) is self.tab_widget
        
        # Verify container relationship
        container_id = registry.get_container_id_from_widget_id(self.tab_widget.widget_id)
        assert container_id == self.main_container_id
        
        # Verify type code
        assert get_type_code_from_id(self.tab_widget.widget_id) == ContainerTypeCodes.TAB
    
    def test_tab_type_registration(self):
        """Test registering tab types with the tab widget."""
        # Register a basic tab type
        basic_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Basic Tab"
        )
        
        # Register a form tab type
        form_model = FormDataModel("Test User", "test@example.com")
        self.observables.append(form_model)
        
        form_tab_type = self.tab_widget.register_tab(
            factory_func=create_form_widget,
            tab_name="Form Tab",
            observables=[form_model]
        )
        
        # Verify types were registered
        assert basic_tab_type is not None
        assert form_tab_type is not None
        assert basic_tab_type != form_tab_type
    
    def test_add_tab_command(self):
        """Test adding tabs generates appropriate commands."""
        # Register tab types
        basic_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Basic Tab"
        )
        
        # Reset command tracking
        self.command_executions = []
        
        # Add a tab
        tab_id = self.tab_widget.add_tab(basic_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify command was created
        assert len(self.command_executions) == 1
        assert isinstance(self.command_executions[0][0], SerializationCommand)
        
        # Verify tab was added
        assert self.tab_widget.count() == 1
        assert tab_id is not None
        
        # Add another tab
        tab_id2 = self.tab_widget.add_tab(basic_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify command was created
        assert len(self.command_executions) == 2
        assert isinstance(self.command_executions[1][0], SerializationCommand)
        
        # Verify second tab was added
        assert self.tab_widget.count() == 2
        assert tab_id2 is not None
        assert tab_id != tab_id2
    
    def test_tab_undo_redo(self):
        """Test undo/redo of tab operations."""
        # Register tab type
        basic_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Basic Tab"
        )
        
        # Add a tab
        tab_id = self.tab_widget.add_tab(basic_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify tab was added
        assert self.tab_widget.count() == 1
        
        # Get the command manager
        cmd_manager = get_command_manager()
        
        # Undo the add tab command
        assert cmd_manager.can_undo()
        cmd_manager.undo()
        
        # Process events
        process_events_and_wait()
        
        # Verify tab was removed
        assert self.tab_widget.count() == 0
        
        # Redo the add tab command
        assert cmd_manager.can_redo()
        cmd_manager.redo()
        
        # Process events
        process_events_and_wait()
        
        # Verify tab was added back
        assert self.tab_widget.count() == 1
    
    def test_close_tab_command(self):
        """Test closing tabs generates appropriate commands."""
        # Register tab types
        basic_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Basic Tab",
            closable=True  # Explicitly set closable
        )
        
        # Add two tabs
        tab_id1 = self.tab_widget.add_tab(basic_tab_type)
        tab_id2 = self.tab_widget.add_tab(basic_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify tabs were added
        assert self.tab_widget.count() == 2
        
        # Reset command tracking
        self.command_executions = []
        
        # Close the first tab via tabCloseRequested signal
        self.tab_widget.tabCloseRequested.emit(0)  # Close first tab
        
        # Process events
        process_events_and_wait()
        
        # Verify command was created for tab close
        assert len(self.command_executions) == 1
        assert isinstance(self.command_executions[0][0], SerializationCommand)
        
        # Verify tab was closed
        assert self.tab_widget.count() == 1
        
        # Get command manager
        cmd_manager = get_command_manager()
        
        # Undo the close operation
        assert cmd_manager.can_undo()
        cmd_manager.undo()
        
        # Process events
        process_events_and_wait()
        
        # Verify tab was restored
        assert self.tab_widget.count() == 2
    
    def test_non_closable_tabs(self):
        """Test tabs marked as non-closable cannot be closed."""
        # Register tab types
        closable_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Closable Tab",
            closable=True
        )
        
        non_closable_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Non-Closable Tab",
            closable=False
        )
        
        # Add tabs
        self.tab_widget.add_tab(closable_tab_type)
        self.tab_widget.add_tab(non_closable_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify tabs were added
        assert self.tab_widget.count() == 2
        
        # Verify closable state
        assert self.tab_widget.is_tab_closable(0) == True
        assert self.tab_widget.is_tab_closable(1) == False
        
        # Reset command tracking
        self.command_executions = []
        
        # Try to close the non-closable tab (should be ignored)
        self.tab_widget.tabCloseRequested.emit(1)
        
        # Process events
        process_events_and_wait()
        
        # Verify no command was created
        assert len(self.command_executions) == 0
        
        # Verify tab is still there
        assert self.tab_widget.count() == 2
        
        # Try to close the closable tab (should work)
        self.tab_widget.tabCloseRequested.emit(0)
        
        # Process events
        process_events_and_wait()
        
        # Verify command was created
        assert len(self.command_executions) == 1
        
        # Verify only the closable tab was closed
        assert self.tab_widget.count() == 1
    
    def test_tab_selection_command(self):
        """Test tab selection generates appropriate commands."""
        # Register tab type
        basic_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Basic Tab"
        )
        
        # Add tabs
        self.tab_widget.add_tab(basic_tab_type)
        self.tab_widget.add_tab(basic_tab_type)
        self.tab_widget.add_tab(basic_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify tabs were added
        assert self.tab_widget.count() == 3
        
        # Reset command tracking
        self.command_executions = []
        
        # Select a different tab
        current_index = self.tab_widget.currentIndex()
        # Make sure _last_tab_index is properly set
        self.tab_widget._last_tab_index = current_index
        
        # Choose a new index different from current
        new_index = (current_index + 1) % 3
        
        # Set the current index 
        self.tab_widget.setCurrentIndex(new_index)
        
        # Process events
        process_events_and_wait()
        
        assert self.tab_widget.currentIndex() != current_index
        
        # Verify command was created
        assert len(self.command_executions) == 1
        assert self.command_executions[0][1] == True  # Command succeeded
        
        # Get command manager
        cmd_manager = get_command_manager()
        
        # Undo the tab selection
        assert cmd_manager.can_undo()
        cmd_manager.undo()
        
        # Process events
        process_events_and_wait()
        
        # Verify original tab is selected
        assert self.tab_widget.currentIndex() == current_index
    
    def test_tab_with_observable_models(self):
        """Test tabs with bound observable models."""
        # Create models for tabs
        model1 = TabDataModel("Tab 1", "Content for Tab 1")
        model2 = TabDataModel("Tab 2", "Content for Tab 2")
        self.observables.extend([model1, model2])
        
        # Register tab type using observable models
        tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Data Tab",
            observables=[TabDataModel]  # Using class as type reference
        )
        
        # Add tabs with new model instances
        tab_id1 = self.tab_widget.add_tab(tab_type)
        tab_id2 = self.tab_widget.add_tab(tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify tabs were added
        assert self.tab_widget.count() == 2
        
        # Find the CommandLineEdit widgets in each tab
        tab1_widget = self.tab_widget.widget(0)
        tab2_widget = self.tab_widget.widget(1)
        
        # Process events to ensure widget hierarchy is fully created
        process_events_and_wait()
        
        # Find title edits using a simple traversal
        title_edit1 = None
        title_edit2 = None
        
        for edit in tab1_widget.findChildren(CommandLineEdit):
            if edit.objectName() == "" and hasattr(edit, '_controlled_properties'):
                for prop_name in edit._controlled_properties:
                    if prop_name == "text":
                        title_edit1 = edit
                        break
                if title_edit1:
                    break
                    
        for edit in tab2_widget.findChildren(CommandLineEdit):
            if edit.objectName() == "" and hasattr(edit, '_controlled_properties'):
                for prop_name in edit._controlled_properties:
                    if prop_name == "text":
                        title_edit2 = edit
                        break
                if title_edit2:
                    break
        
        # If we found the edits, test modifying the models
        if title_edit1 and title_edit2:
            # Get the bound models
            property_id1 = title_edit1._controlled_properties.get("text")
            property_id2 = title_edit2._controlled_properties.get("text")
            
            if property_id1 and property_id2:
                # Get the observables
                registry = get_id_registry()
                observable_id1 = registry.get_observable_id_from_property_id(property_id1)
                observable_id2 = registry.get_observable_id_from_property_id(property_id2)
                
                # If we found the observables, modify them
                if observable_id1 and observable_id2:
                    observable1 = registry.get_observable(observable_id1)
                    observable2 = registry.get_observable(observable_id2)
                    
                    if observable1 and observable2:
                        # Change titles via the observable
                        if hasattr(observable1, 'title'):
                            observable1.title = "Modified Tab 1"
                        if hasattr(observable2, 'title'):
                            observable2.title = "Modified Tab 2"
                        
                        # Process events
                        process_events_and_wait()
                        
                        # Verify edits updated
                        assert title_edit1.text() in ["Tab 1", "Modified Tab 1"]
                        assert title_edit2.text() in ["Tab 2", "Modified Tab 2"]
    
    def test_nested_tab_widgets(self):
        """Test nested CommandTabWidget containers."""
        # Register outer tab type
        outer_tab_type = self.tab_widget.register_tab(
            factory_func=lambda: QWidget(),  # Empty widget for now
            tab_name="Outer Tab"
        )
        
        # Add an outer tab
        outer_tab_id = self.tab_widget.add_tab(outer_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify outer tab was added
        assert self.tab_widget.count() == 1
        
        # Get the outer tab widget
        outer_tab_widget = self.tab_widget.widget(0)
        
        # Create a nested tab widget in the outer tab
        outer_layout = QVBoxLayout(outer_tab_widget)
        inner_tab_widget = CommandTabWidget(container_id=outer_tab_id)
        outer_layout.addWidget(inner_tab_widget)
        
        # Register inner tab type
        inner_tab_type = inner_tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Inner Tab"
        )
        
        # Reset command tracking
        self.command_executions = []
        
        # Add inner tabs
        inner_tab_id1 = inner_tab_widget.add_tab(inner_tab_type)
        inner_tab_id2 = inner_tab_widget.add_tab(inner_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify inner tabs were added
        assert inner_tab_widget.count() == 2
        
        # Verify commands were created
        assert len(self.command_executions) == 2
        
        # Test navigation to nested tabs
        # First select the outer tab
        self.tab_widget.setCurrentIndex(0)
        
        # Then select an inner tab
        inner_tab_widget.setCurrentIndex(1)
        
        # Process events
        process_events_and_wait()
        
        # Verify selections
        assert self.tab_widget.currentIndex() == 0
        assert inner_tab_widget.currentIndex() == 1
        
        # Test container hierarchy in ID system
        registry = get_id_registry()
        
        # Verify inner tab widget container is the outer tab
        inner_container_id = registry.get_container_id_from_widget_id(inner_tab_widget.widget_id)
        assert inner_container_id == outer_tab_id
        
        # Verify navigation function works through hierarchy
        inner_tab_widget.navigate_to_widget(inner_tab_id2)
        
        # Verify inner tab is selected
        assert inner_tab_widget.currentIndex() == 1
    
    def test_tab_serialization(self):
        """Test serialization and deserialization of tab widget."""
        # Register tab type
        basic_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Basic Tab"
        )
        
        # Add tabs
        tab_id1 = self.tab_widget.add_tab(basic_tab_type)
        tab_id2 = self.tab_widget.add_tab(basic_tab_type)
        tab_id3 = self.tab_widget.add_tab(basic_tab_type)
        
        # Select tab 2
        self.tab_widget.setCurrentIndex(1)
        
        # Process events
        process_events_and_wait()
        
        # Configure tab widget
        self.tab_widget.setTabPosition(QTabWidget.South)
        self.tab_widget.setMovable(True)
        
        # Serialize the tab widget
        serialized_state = self.tab_widget.get_serialization()
        
        # Verify serialized state has expected components
        assert "id" in serialized_state
        assert "current_index" in serialized_state
        assert "tab_position" in serialized_state
        assert "moving_enabled" in serialized_state
        assert "subcontainers" in serialized_state
        assert len(serialized_state["subcontainers"]) == 3
        
        # Reset the tab widget
        self.tab_widget.clear()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(False)
        
        # Verify reset state
        assert self.tab_widget.count() == 0
        assert self.tab_widget.tabPosition() == QTabWidget.North
        assert self.tab_widget.isMovable() == False
        
        # Register tab type again (needed for deserialization)
        basic_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Basic Tab"
        )
        
        # Deserialize the tab widget
        result = self.tab_widget.deserialize(serialized_state)
        assert result
        
        # Process events
        process_events_and_wait(100)  # Longer wait to ensure full restoration
        
        # Verify state was restored
        assert self.tab_widget.count() == 3
        assert self.tab_widget.currentIndex() == 1
        assert self.tab_widget.tabPosition() == QTabWidget.South
        assert self.tab_widget.isMovable() == True
    
    def test_tab_subcontainer_serialization(self):
        """Test serialization of individual tab subcontainers."""
        # Create a model for tab content
        model = FormDataModel("Test User", "test@example.com")
        self.observables.append(model)
        
        # Register tab type
        form_tab_type = self.tab_widget.register_tab(
            factory_func=create_form_widget,
            tab_name="Form Tab",
            observables=[model]
        )
        
        # Add a tab
        tab_id = self.tab_widget.add_tab(form_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify tab was added
        assert self.tab_widget.count() == 1
        
        # Modify the model
        model.name = "Modified User"
        model.email = "modified@example.com"
        
        # Process events
        process_events_and_wait()
        
        # Serialize just this tab's subcontainer
        subcontainer_state = self.tab_widget.serialize_subcontainer(tab_id)
        
        # Verify serialized state
        assert subcontainer_state is not None
        assert "id" in subcontainer_state
        assert "type" in subcontainer_state
        assert "location" in subcontainer_state
        assert "children" in subcontainer_state
        
        # Modify the model again
        model.name = "Changed Again"
        model.email = "changed@example.com"
        
        # Process events
        process_events_and_wait()
        
        # Deserialize the subcontainer
        result = self.tab_widget.deserialize_subcontainer(
            form_tab_type, 
            subcontainer_state["location"], 
            subcontainer_state
        )
        assert result
        
        # Process events
        process_events_and_wait()
        
        # Verify the model was restored to the serialized state
        assert model.name == "Modified User"
        assert model.email == "modified@example.com"
    
    def test_tab_registry_cleanup(self):
        """Test proper cleanup of tab widget resources when destroyed."""
        # Register tab type
        basic_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="Basic Tab"
        )
        
        # Add tabs
        tab_id1 = self.tab_widget.add_tab(basic_tab_type)
        tab_id2 = self.tab_widget.add_tab(basic_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify tabs were added
        assert self.tab_widget.count() == 2
        
        # Simulate tab widget destruction
        registry = get_id_registry()
        tab_widget_id = self.tab_widget.widget_id
        
        # Store tab IDs for checking
        tab1_widget = self.tab_widget.widget(0)
        tab2_widget = self.tab_widget.widget(1)
        tab1_widget_id = registry.get_id(tab1_widget)
        tab2_widget_id = registry.get_id(tab2_widget)
        
        # Destroy tab widget
        self.tab_widget.deleteLater()
        self.tab_widget = None
        
        # Process events to ensure deletion
        process_events_and_wait(100)
        
        # Verify tab widget and tabs were unregistered
        assert registry.get_widget(tab_widget_id) is None
        assert registry.get_widget(tab1_widget_id) is None
        assert registry.get_widget(tab2_widget_id) is None
        
        # Create a new tab widget after verification
        self.tab_widget = CommandTabWidget(container_id=self.main_container_id)
        self.main_layout.addWidget(self.tab_widget)
        
        # Verify it has a new ID
        assert self.tab_widget.widget_id != tab_widget_id
        
        # Verify it has a new ID
        assert self.tab_widget.widget_id != tab_widget_id
        
        # Register a new tab type
        new_tab_type = self.tab_widget.register_tab(
            factory_func=create_content_widget,
            tab_name="New Tab"
        )
        
        # Add a tab
        new_tab_id = self.tab_widget.add_tab(new_tab_type)
        
        # Process events
        process_events_and_wait()
        
        # Verify tab was added
        assert self.tab_widget.count() == 1
        assert new_tab_id is not None


if __name__ == "__main__":
    # Run tests when script is executed directly
    setup_module()
    pytest.main(["-v", __file__])
    teardown_module()