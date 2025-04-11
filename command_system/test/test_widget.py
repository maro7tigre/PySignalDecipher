"""
Comprehensive test suite for the PySide6 widget integration with command system.

This test suite validates the functionality of the command-enabled widgets:
- Widget registration and ID management
- Property binding and change tracking
- Command generation and execution
- Widget serialization and deserialization
- Real-world usage scenarios

The tests use mock classes to simulate Qt functionality without requiring the actual
PySide6 dependencies, focusing on the command and ID system integration logic.
"""
import pytest
import sys
import os
from typing import Dict, Any, List, Optional, Callable
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock PySide6 imports for testing without Qt dependency
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()

# Mock QLineEdit class
class MockQLineEdit:
    def __init__(self, text="", parent=None):
        self.text_value = text
        self.blocked = False
        self.placeholder_text = ""
        # Create mock signals
        self.textChanged = MagicMock()
        self.textChanged.connect = MagicMock(return_value=True)
        self.editingFinished = MagicMock()
        self.editingFinished.connect = MagicMock(return_value=True)
        
    def text(self):
        return self.text_value
        
    def setText(self, text):
        old_text = self.text_value
        self.text_value = text
        if not self.blocked and old_text != text:
            self.textChanged.emit(text)
            
    def setPlaceholderText(self, text):
        self.placeholder_text = text
        
    def blockSignals(self, block):
        self.blocked = block
        return True

# Mock QTimer class
class MockQTimer:
    def __init__(self):
        self.timeout = MagicMock()
        self.timeout.connect = MagicMock(return_value=True)
        self._is_active = False
        self._interval = 0
        self._single_shot = False
        
    def setSingleShot(self, single_shot):
        self._single_shot = single_shot
        
    def start(self, ms):
        self._interval = ms
        self._is_active = True
        
    def stop(self):
        self._is_active = False
        
    def isActive(self):
        return self._is_active

# Add mock classes to the mock PySide6 module
sys.modules['PySide6.QtWidgets'].QLineEdit = MockQLineEdit
sys.modules['PySide6.QtCore'].QTimer = MockQTimer

# Now that the PySide6 modules are mocked, import the command system modules
from command_system.core import (
    Observable, ObservableProperty,
    Command, PropertyCommand, get_command_manager, CompoundCommand
)

from command_system.id_system import (
    get_id_registry, WidgetTypeCodes, ContainerTypeCodes, parse_property_id
)

# Define command trigger modes without importing widget module
class CommandTriggerMode:
    """
    Defines when a command should be triggered for widget value changes.
    Used for testing without importing the actual module.
    """
    IMMEDIATE = 0
    DELAYED = 1
    ON_EDIT_FINISHED = 2

# MARK: - Test Models

class Person(Observable):
    """Sample observable class for testing."""
    name = ObservableProperty("")
    age = ObservableProperty(0)
    email = ObservableProperty("")
    
    def __init__(self, name="", age=0, email=""):
        # Initialize Observable base
        super().__init__()
        # Set initial values
        self.name = name
        self.age = age
        self.email = email

# MARK: - Mock Command Widgets

class MockCommandWidget:
    """Base class for command-enabled widget testing."""
    
    def __init__(self, type_code=WidgetTypeCodes.CUSTOM_WIDGET, container_id=None, location=None):
        # Initialize widget state
        self._text = ""
        self._visible = True
        self._enabled = True
        self._pending_changes = {}
        self._last_values = {}  # Property name -> Last committed value
        self._controlled_properties = {}  # Widget property -> Property ID
        
        # Create mock Qt widget
        self.qt_widget = MockQLineEdit()
        
        # Command settings
        self._command_trigger_mode = CommandTriggerMode.IMMEDIATE
        self._change_delay_ms = 300
        self._processing_command = False
        
        # Create mock timer for delayed updates
        self._change_timer = MockQTimer()
        
        # Register with ID system
        id_registry = get_id_registry()
        self.widget_id = id_registry.register(self, type_code, None, container_id, location)
        self.type_code = type_code
    
    def text(self):
        """Get widget text property."""
        return self._text
        
    def setText(self, text):
        """Set widget text property and trigger command if needed."""
        if self._text != text:
            self._text = text
            self._on_widget_value_changed("text", text)
            
    def setVisible(self, visible):
        """Set widget visibility."""
        self._visible = visible
        
    def isVisible(self):
        """Get widget visibility."""
        return self._visible
        
    def setEnabled(self, enabled):
        """Set widget enabled state."""
        self._enabled = enabled
        
    def isEnabled(self):
        """Get widget enabled state."""
        return self._enabled
    
    def bind_property(self, widget_property, observable_id, property_name):
        """
        Bind a widget property to an observable property.
        
        Args:
            widget_property: Name of the widget property to bind
            observable_id: ID of the observable object
            property_name: Name of the property on the observable
        """
        # Get registry and observable
        id_registry = get_id_registry()
        observable = id_registry.get_observable(observable_id)
        
        if not observable:
            raise ValueError(f"Observable with ID {observable_id} not found")
        
        # Ensure the observable property exists
        if not hasattr(observable, property_name):
            raise ValueError(f"Observable does not have property '{property_name}'")
        
        # Get property IDs associated with this observable and property name
        property_ids = id_registry.get_property_ids_by_observable_id_and_property_name(
            observable_id, property_name)
        
        if property_ids:
            # Property already exists, update controller reference
            property_id = property_ids[0]
            id_registry.update_controller_reference(property_id, self.widget_id)
        else:
            # This shouldn't happen with ObservableProperty attributes
            # They should be registered when the Observable is initialized
            raise ValueError(f"Property '{property_name}' not registered with observable")
        
        # Store the controlled property mapping
        self._controlled_properties[widget_property] = property_id
        
        # Set up observer for property changes
        observable.add_property_observer(
            property_name, 
            lambda prop_name, old_val, new_val: self._on_observed_property_changed(
                widget_property, old_val, new_val
            ),
            self
        )
        
        # Initialize widget with current observable value
        current_value = getattr(observable, property_name)
        self._on_observed_property_changed(widget_property, None, current_value)
    
    def unbind_property(self, widget_property):
        """Unbind a widget property from its observable property."""
        if widget_property not in self._controlled_properties:
            return
        
        # Get the property ID
        property_id = self._controlled_properties[widget_property]
        
        # Remove the controller reference
        id_registry = get_id_registry()
        id_registry.remove_controller_reference(property_id)
        
        # Remove from our tracking
        del self._controlled_properties[widget_property]
    
    def _on_observed_property_changed(self, widget_property, old_value, new_value):
        """Handle changes from the observable property."""
        if self._processing_command:
            return  # Avoid recursion
            
        self._processing_command = True
        try:
            # Update the widget property
            self._update_widget_property(widget_property, new_value)
            # Update last known value
            self._last_values[widget_property] = new_value
        finally:
            self._processing_command = False
    
    def _update_widget_property(self, property_name, value):
        """Update a widget property value."""
        if property_name == "text":
            self._text = value if value is not None else ""
        elif property_name == "visible":
            self._visible = value
        elif property_name == "enabled":
            self._enabled = value
        else:
            raise ValueError(f"Unsupported property: {property_name}")
    
    def _on_widget_value_changed(self, widget_property, new_value):
        """Handle value changes from the widget."""
        if self._processing_command:
            return  # Avoid recursion
            
        # Skip if no change from last value
        last_value = self._last_values.get(widget_property)
        if last_value == new_value:
            return
            
        # Handle based on trigger mode
        if self._command_trigger_mode == CommandTriggerMode.IMMEDIATE:
            self._create_and_execute_property_command(widget_property, new_value)
        elif self._command_trigger_mode == CommandTriggerMode.DELAYED:
            # Store pending change and restart timer
            self._pending_changes[widget_property] = new_value
            self._change_timer.start(self._change_delay_ms)
        elif self._command_trigger_mode == CommandTriggerMode.ON_EDIT_FINISHED:
            # Store for later processing when editing is finished
            self._pending_changes[widget_property] = new_value
    
    def triggerEditingFinished(self):
        """Simulate editing finished event."""
        self._on_widget_editing_finished()
    
    def _on_widget_editing_finished(self):
        """Handle the completion of editing."""
        # Stop any pending delayed updates
        if self._change_timer.isActive():
            self._change_timer.stop()
            
        # Process all pending changes
        for widget_property, new_value in list(self._pending_changes.items()):
            self._create_and_execute_property_command(widget_property, new_value)
        self._pending_changes.clear()
    
    def _on_change_timer_timeout(self):
        """Handle the timeout of the change delay timer."""
        # Process all pending changes
        for widget_property, new_value in list(self._pending_changes.items()):
            self._create_and_execute_property_command(widget_property, new_value)
        self._pending_changes.clear()
    
    def _create_and_execute_property_command(self, widget_property, new_value):
        """Create and execute a command to update the controlled property."""
        if widget_property not in self._controlled_properties:
            return
        
        # Skip if no change from last value
        last_value = self._last_values.get(widget_property)
        if last_value == new_value:
            return
            
        # Get the property ID
        property_id = self._controlled_properties[widget_property]
        
        # Create and execute the command
        command = PropertyCommand(property_id, new_value)
        command.set_trigger_widget(self.widget_id)
        
        # Execute the command
        get_command_manager().execute(command)
        
        # Update last known value
        self._last_values[widget_property] = new_value
    
    def update_container(self, new_container_id=None):
        """Update the container for this widget."""
        id_registry = get_id_registry()
        if new_container_id is not None:
            # Update container in the ID system
            updated_id = id_registry.update_container(self.widget_id, new_container_id)
            if updated_id != self.widget_id:
                # Update our stored widget ID if it changed
                self.widget_id = updated_id
        return self.widget_id
    
    def set_command_trigger_mode(self, mode, delay_ms=300):
        """Set when commands should be triggered for widget value changes."""
        self._command_trigger_mode = mode
        self._change_delay_ms = delay_ms
    
    def get_serialization(self):
        """Get serialized representation of this widget."""
        result = {
            'id': self.widget_id,
            'properties': {},
            'widget_props': {
                'text': self._text,
                'visible': self._visible,
                'enabled': self._enabled
            }
        }
        
        # Serialize controlled properties
        for widget_property, property_id in self._controlled_properties.items():
            id_registry = get_id_registry()
            # Get observable ID from property ID
            observable_id = id_registry.get_observable_id_from_property_id(property_id)
            
            if observable_id:
                # Get the observable
                observable = id_registry.get_observable(observable_id)
                if observable and hasattr(observable, 'serialize_property'):
                    # Get property name from property_id
                    property_components = parse_property_id(property_id)
                    if property_components:
                        property_name = property_components['property_name']
                        # Serialize the property
                        serialized_property = observable.serialize_property(property_name)
                        if serialized_property:
                            result['properties'][widget_property] = serialized_property
        
        return result
    
    def deserialize(self, data):
        """Restore this widget's state from serialized data."""
        if not data or not isinstance(data, dict):
            return False
            
        id_registry = get_id_registry()
        
        # Update widget ID if needed
        if 'id' in data and data['id'] != self.widget_id:
            success, updated_id, error = id_registry.update_id(self.widget_id, data['id'])
            if success:
                self.widget_id = updated_id
        
        # Restore properties
        if 'properties' in data and isinstance(data['properties'], dict):
            for widget_property, serialized_property in data['properties'].items():
                # Find the matching controlled property
                if widget_property in self._controlled_properties:
                    property_id = self._controlled_properties[widget_property]
                    observable_id = id_registry.get_observable_id_from_property_id(property_id)
                    
                    if observable_id:
                        observable = id_registry.get_observable(observable_id)
                        if observable and hasattr(observable, 'deserialize_property'):
                            # Extract property name from property_id
                            property_components = parse_property_id(property_id)
                            if property_components:
                                property_name = property_components['property_name']
                                # Deserialize the property
                                observable.deserialize_property(property_name, serialized_property)
        
        # Restore widget properties
        if 'widget_props' in data:
            props = data['widget_props']
            if 'text' in props:
                self._text = props['text']
            if 'visible' in props:
                self._visible = props['visible']
            if 'enabled' in props:
                self._enabled = props['enabled']
        
        return True
    
    def unregister_widget(self):
        """Unregister this widget from the ID system."""
        id_registry = get_id_registry()
        return id_registry.unregister(self.widget_id)

class MockCommandLineEdit(MockCommandWidget):
    """A specialized mock line edit with command support."""
    def __init__(self, text="", container_id=None, location=None):
        super().__init__(WidgetTypeCodes.LINE_EDIT, container_id, location)
        self._text = text
        
    def bind_to_text_property(self, observable_id, property_name):
        """Convenience method to bind text property."""
        self.bind_property("text", observable_id, property_name)
        
    def unbind_text_property(self):
        """Convenience method to unbind text property."""
        self.unbind_property("text")
        
class MockCommandContainer(MockCommandWidget):
    """A mock container widget that can hold other widgets."""
    
    def __init__(self, type_code=ContainerTypeCodes.CUSTOM, container_id=None, location=None):
        super().__init__(type_code, container_id, location)
        self.children = {}  # Location -> Widget ID mapping
        self.active_child = None
    
    def add_child(self, child_id, location):
        """Add a child widget at the specified location."""
        self.children[location] = child_id
        
    def remove_child(self, location):
        """Remove a child widget from the specified location."""
        if location in self.children:
            del self.children[location]
            
    def get_child(self, location):
        """Get the child widget at the specified location."""
        return self.children.get(location)
    
    def set_active_child(self, location):
        """Set the active child widget."""
        if location in self.children:
            self.active_child = location
        
    def navigate_to_widget(self, widget_id):
        """Navigate to a specific widget within this container."""
        # Find the widget's location
        for location, wid in self.children.items():
            if wid == widget_id:
                self.active_child = location
                return True
        return False
    
    def get_serialization(self):
        """Get serialized representation of this container."""
        result = super().get_serialization()
        result['children'] = self.children.copy()
        result['active_child'] = self.active_child
        return result
    
    def deserialize(self, data):
        """Restore this container's state from serialized data."""
        if not super().deserialize(data):
            return False
        
        if 'children' in data:
            self.children = data['children'].copy()
        if 'active_child' in data:
            self.active_child = data['active_child']
        
        return True

# MARK: - Tests

class TestWidgetRegistration:
    """Test cases for widget registration and ID management."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
        
        # Clear command manager
        manager = get_command_manager()
        manager.clear()
    
    def test_widget_registration_basics(self):
        """Test basic widget registration and ID retrieval."""
        # Create and register widget
        widget = MockCommandWidget()
        
        # Verify widget is registered
        registry = get_id_registry()
        widget_id = widget.widget_id
        assert widget_id is not None
        
        # Verify widget can be retrieved by ID
        retrieved_widget = registry.get_widget(widget_id)
        assert retrieved_widget is widget
        
        # Verify ID can be retrieved from widget
        retrieved_id = registry.get_id(widget)
        assert retrieved_id == widget_id
    
    def test_widget_type_codes(self):
        """Test widgets with different type codes."""
        # Create widgets with different type codes
        line_edit = MockCommandWidget(WidgetTypeCodes.LINE_EDIT)
        button = MockCommandWidget(WidgetTypeCodes.PUSH_BUTTON)
        container = MockCommandWidget(ContainerTypeCodes.TAB)
        
        # Verify IDs have correct type codes
        assert line_edit.widget_id.startswith(f"{WidgetTypeCodes.LINE_EDIT}:")
        assert button.widget_id.startswith(f"{WidgetTypeCodes.PUSH_BUTTON}:")
        assert container.widget_id.startswith(f"{ContainerTypeCodes.TAB}:")
    
    def test_widget_container_relationship(self):
        """Test container-widget relationship."""
        # Create container and widget
        container = MockCommandContainer()
        widget = MockCommandWidget()
        
        # Set up widget's container
        original_id = widget.widget_id
        updated_id = widget.update_container(container.widget_id)
        
        # Verify widget ID was updated
        assert updated_id != original_id
        
        # Verify container reference
        registry = get_id_registry()
        container_id = registry.get_container_id_from_widget_id(widget.widget_id)
        assert container_id == container.widget_id
        
        # Verify container's widgets list
        container_widgets = registry.get_container_widgets(container.widget_id)
        assert widget.widget_id in container_widgets
    
    def test_widget_hierarchy(self):
        """Test nested container hierarchy."""
        # Create container hierarchy
        root = MockCommandContainer(ContainerTypeCodes.WINDOW)
        level1 = MockCommandContainer(ContainerTypeCodes.TAB)
        level2 = MockCommandContainer(ContainerTypeCodes.DOCK)
        
        # Set up hierarchy
        level1.update_container(root.widget_id)
        level2.update_container(level1.widget_id)
        
        # Create widget in the deepest container
        widget = MockCommandWidget()
        widget.update_container(level2.widget_id)
        
        # Verify container hierarchy
        registry = get_id_registry()
        widget_container_id = registry.get_container_id_from_widget_id(widget.widget_id)
        assert widget_container_id == level2.widget_id
        
        level2_container_id = registry.get_container_id_from_widget_id(level2.widget_id)
        assert level2_container_id == level1.widget_id
        
        level1_container_id = registry.get_container_id_from_widget_id(level1.widget_id)
        assert level1_container_id == root.widget_id
    
    def test_widget_unregistration(self):
        """Test widget unregistration."""
        # Create widget
        widget = MockCommandWidget()
        widget_id = widget.widget_id
        
        # Unregister widget
        result = widget.unregister_widget()
        
        # Verify unregistration
        assert result
        
        # Verify widget is no longer registered
        registry = get_id_registry()
        assert registry.get_widget(widget_id) is None
        assert registry.get_id(widget) is None
    
    def test_container_unregister_cascade(self):
        """Test that unregistering a container cascades to children."""
        # Create container hierarchy
        container = MockCommandContainer()
        widget1 = MockCommandWidget()
        widget2 = MockCommandWidget()
        
        # Set up hierarchy
        widget1.update_container(container.widget_id)
        widget2.update_container(container.widget_id)
        
        # Store all IDs
        container_id = container.widget_id
        widget1_id = widget1.widget_id
        widget2_id = widget2.widget_id
        
        # Unregister container
        registry = get_id_registry()
        result = registry.unregister(container_id)
        
        # Verify unregistration
        assert result
        
        # Verify container and all widgets are no longer registered
        assert registry.get_widget(container_id) is None
        assert registry.get_widget(widget1_id) is None
        assert registry.get_widget(widget2_id) is None


class TestPropertyBinding:
    """Test cases for property binding between widgets and observables."""
    
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
        self.widget = MockCommandLineEdit()
    
    def test_property_binding_basics(self):
        """Test basic property binding functionality."""
        # Bind widget to observable property
        self.widget.bind_to_text_property(self.person.get_id(), "name")
        
        # Check that widget was initialized with observable's value
        assert self.widget.text() == "Alice"
        
        # Change observable property
        self.person.name = "Bob"
        
        # Check that widget was updated
        assert self.widget.text() == "Bob"
        
        # Change widget property
        self.widget.setText("Charlie")
        
        # Check that observable was updated
        assert self.person.name == "Charlie"
    
    def test_property_binding_multiple_widgets(self):
        """Test binding multiple widgets to the same observable property."""
        # Create multiple widgets
        widget1 = MockCommandLineEdit()
        widget2 = MockCommandLineEdit()
        
        # Bind both widgets to the same property
        widget1.bind_to_text_property(self.person.get_id(), "name")
        widget2.bind_to_text_property(self.person.get_id(), "name")
        
        # Verify both widgets have the initial value
        assert widget1.text() == "Alice"
        assert widget2.text() == "Alice"
        
        # Change property from one widget
        widget1.setText("Bob")
        
        # Verify observable and all widgets were updated
        assert self.person.name == "Bob"
        assert widget1.text() == "Bob"
        assert widget2.text() == "Bob"
        
        # Change property from observable
        self.person.name = "Charlie"
        
        # Verify all widgets were updated
        assert widget1.text() == "Charlie"
        assert widget2.text() == "Charlie"
    
    def test_property_binding_multiple_properties(self):
        """Test binding widgets to different properties of the same observable."""
        # Create multiple widgets
        name_widget = MockCommandLineEdit()
        age_widget = MockCommandLineEdit()
        email_widget = MockCommandLineEdit()
        
        # Bind widgets to different properties
        name_widget.bind_to_text_property(self.person.get_id(), "name")
        age_widget.bind_to_text_property(self.person.get_id(), "age")
        email_widget.bind_to_text_property(self.person.get_id(), "email")
        
        # Verify widgets have the initial values
        assert name_widget.text() == "Alice"
        assert age_widget.text() == "30"  # Converted to string
        assert email_widget.text() == "alice@example.com"
        
        # Change each property from its widget
        name_widget.setText("Bob")
        age_widget.setText("40")
        email_widget.setText("bob@example.com")
        
        # Verify observable properties were updated
        assert self.person.name == "Bob"
        assert self.person.age == 40  # Converted to number
        assert self.person.email == "bob@example.com"
    
    def test_unbind_property(self):
        """Test unbinding a property."""
        # Bind widget to observable property
        self.widget.bind_to_text_property(self.person.get_id(), "name")
        
        # Verify binding works
        self.person.name = "Bob"
        assert self.widget.text() == "Bob"
        
        # Unbind property
        self.widget.unbind_text_property()
        
        # Change observable - should not update widget anymore
        self.person.name = "Charlie"
        assert self.widget.text() == "Bob"  # Still has old value
        
        # Change widget - should not update observable anymore
        self.widget.setText("Dave")
        assert self.person.name == "Charlie"  # Observable unchanged


class TestSerializationDeserialization:
    """Test cases for widget serialization and deserialization."""
    
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
        self.widget = MockCommandLineEdit()
    
    def test_basic_serialization(self):
        """Test basic widget serialization without binding."""
        # Set widget properties
        self.widget.setText("Test Text")
        self.widget.setVisible(False)
        self.widget.setEnabled(False)
        
        # Serialize widget
        serialized_data = self.widget.get_serialization()
        
        # Verify serialized data structure
        assert "id" in serialized_data
        assert serialized_data["id"] == self.widget.widget_id
        assert "widget_props" in serialized_data
        assert serialized_data["widget_props"]["text"] == "Test Text"
        assert serialized_data["widget_props"]["visible"] is False
        assert serialized_data["widget_props"]["enabled"] is False
        
        # Change widget properties
        self.widget.setText("New Text")
        self.widget.setVisible(True)
        self.widget.setEnabled(True)
        
        # Deserialize widget to restore original state
        self.widget.deserialize(serialized_data)
        
        # Verify properties were restored
        assert self.widget.text() == "Test Text"
        assert self.widget.isVisible() is False
        assert self.widget.isEnabled() is False
    
    def test_serialization_with_binding(self):
        """Test serialization with property binding."""
        # Bind widget to observable property
        self.widget.bind_to_text_property(self.person.get_id(), "name")
        
        # Verify initial binding
        assert self.widget.text() == "Alice"
        
        # Serialize widget
        serialized_data = self.widget.get_serialization()
        
        # Verify serialized data includes property binding
        assert "properties" in serialized_data
        assert "text" in serialized_data["properties"]
        assert serialized_data["properties"]["text"]["value"] == "Alice"
        
        # Change observable and widget properties
        self.person.name = "Bob"
        
        # Verify widget was updated
        assert self.widget.text() == "Bob"
        
        # Deserialize to restore original state
        result = self.widget.deserialize(serialized_data)
        
        # Verify deserialization worked
        assert result is True
        
        # Verify properties were restored
        assert self.person.name == "Alice"
        assert self.widget.text() == "Alice"
        
        # Verify binding still works
        self.person.name = "Charlie"
        assert self.widget.text() == "Charlie"
    
    def test_container_serialization(self):
        """Test serialization of containers with children."""
        # Create container with widgets
        container = MockCommandContainer()
        widget1 = MockCommandLineEdit("Widget 1")
        widget2 = MockCommandLineEdit("Widget 2")
        
        # Add widgets to container
        widget1.update_container(container.widget_id)
        widget2.update_container(container.widget_id)
        
        # Update container's internal child tracking
        registry = get_id_registry()
        container_widgets = registry.get_widgets_by_container_id(container.widget_id)
        
        # Find locations for widgets (in a real container this would be managed automatically)
        for i, widget_id in enumerate(container_widgets):
            container.add_child(widget_id, f"location_{i}")
        
        # Set active child
        container.set_active_child("location_0")
        
        # Serialize container
        serialized_data = container.get_serialization()
        
        # Verify serialized data includes children
        assert "children" in serialized_data
        assert len(serialized_data["children"]) == 2
        assert "active_child" in serialized_data
        assert serialized_data["active_child"] == "location_0"
        
        # Change container state
        container.set_active_child("location_1")
        container.remove_child("location_0")
        
        # Deserialize to restore original state
        container.deserialize(serialized_data)
        
        # Verify container state was restored
        assert len(container.children) == 2
        assert "location_0" in container.children
        assert "location_1" in container.children
        assert container.active_child == "location_0"
    
    def test_restore_after_unregister(self):
        """Test restoring widget state after unregistering and recreating."""
        # Bind widget to observable property
        self.widget.bind_to_text_property(self.person.get_id(), "name")
        self.widget.setText("Alice")
        
        # Serialize widget
        serialized_data = self.widget.get_serialization()
        widget_id = self.widget.widget_id
        
        # Unregister widget
        self.widget.unregister_widget()
        
        # Create a new widget
        new_widget = MockCommandLineEdit()
        assert new_widget.widget_id != widget_id  # Different ID
        
        # Try to deserialize with original data
        new_widget.deserialize(serialized_data)
        
        # Bind to the same observable
        new_widget.bind_to_text_property(self.person.get_id(), "name")
        
        # Verify widget has the correct property values
        assert new_widget.text() == "Alice"
        
        # Verify binding works
        self.person.name = "Bob"
        assert new_widget.text() == "Bob"


class TestErrorHandling:
    """Test cases for error handling in widgets."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
        
        # Clear command manager
        manager = get_command_manager()
        manager.clear()
        
        # Create test objects
        self.person = Person(name="Alice", age=30)
        self.widget = MockCommandLineEdit()
    
    def test_binding_nonexistent_property(self):
        """Test handling of binding to a nonexistent property."""
        # Try to bind to nonexistent property
        with pytest.raises(ValueError) as excinfo:
            self.widget.bind_to_text_property(self.person.get_id(), "nonexistent")
        
        # Verify error message
        assert "does not have property" in str(excinfo.value)
    
    def test_binding_nonexistent_observable(self):
        """Test handling of binding to a nonexistent observable."""
        # Get a nonexistent observable ID
        invalid_id = "ob:999"
        
        # Try to bind to nonexistent observable
        with pytest.raises(ValueError) as excinfo:
            self.widget.bind_to_text_property(invalid_id, "name")
        
        # Verify error message
        assert "not found" in str(excinfo.value)
    
    def test_unbinding_nonexistent_property(self):
        """Test handling of unbinding a nonexistent property."""
        # Unbind property that was never bound (should not raise error)
        self.widget.unbind_text_property()
    
    def test_invalid_widget_property(self):
        """Test handling of invalid widget property."""
        # Bind to valid property
        self.widget.bind_to_text_property(self.person.get_id(), "name")
        
        # Try to update invalid property
        with pytest.raises(ValueError) as excinfo:
            self.widget._update_widget_property("nonexistent", "value")
        
        # Verify error message
        assert "Unsupported property" in str(excinfo.value)


class TestRealWorldScenarios:
    """Test cases for real-world usage scenarios."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
        
        # Clear command manager
        manager = get_command_manager()
        manager.clear()
        
        # Enable initialization mode to avoid tracking setup commands
        manager.begin_init()
        
        # Create test objects
        self.person = Person(name="Alice", age=30, email="alice@example.com")
        
        # End initialization mode
        manager.end_init()
    
    def test_form_editing_scenario(self):
        """Test a typical form editing scenario with multiple fields."""
        # Create form widgets
        name_widget = MockCommandLineEdit()
        age_widget = MockCommandLineEdit()
        email_widget = MockCommandLineEdit()
        
        # Set edit finished trigger mode
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
        name_widget.triggerEditingFinished()
        age_widget.triggerEditingFinished()
        email_widget.triggerEditingFinished()
        
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
    
    def test_container_navigation(self):
        """Test container navigation with command context."""
        # Create container hierarchy
        main_container = MockCommandContainer(ContainerTypeCodes.WINDOW)
        tab_container = MockCommandContainer(ContainerTypeCodes.TAB)
        panel_container = MockCommandContainer(ContainerTypeCodes.DOCK)
        
        # Set up hierarchy
        tab_container.update_container(main_container.widget_id)
        panel_container.update_container(tab_container.widget_id)
        
        # Create widgets
        name_widget = MockCommandLineEdit()
        age_widget = MockCommandLineEdit()
        
        # Place widgets in containers
        name_widget.update_container(tab_container.widget_id)
        age_widget.update_container(panel_container.widget_id)
        
        # Update container tracking
        tab_container.add_child(name_widget.widget_id, "name_field")
        panel_container.add_child(age_widget.widget_id, "age_field")
        
        # Bind widgets to observable
        name_widget.bind_to_text_property(self.person.get_id(), "name")
        age_widget.bind_to_text_property(self.person.get_id(), "age")
        
        # Change a property from a widget
        name_widget.setText("Bob")
        
        # Get the command that was generated
        manager = get_command_manager()
        history = manager._history
        commands = history.get_executed_commands()
        command = commands[0]
        
        # Verify command has the trigger widget ID
        assert command.trigger_widget_id == name_widget.widget_id
        
        # Simulate command manager navigating to context when undoing
        # (Usually done by CommandManager._navigate_to_command_context)
        assert tab_container.navigate_to_widget(command.trigger_widget_id)
        
        # Verify tab_container found and activated the widget
        assert tab_container.active_child == "name_field"
    
    def test_compound_edits(self):
        """Test compound commands with multiple widget edits."""
        # Create widgets
        name_widget = MockCommandLineEdit()
        age_widget = MockCommandLineEdit()
        
        # Bind to model properties
        name_widget.bind_to_text_property(self.person.get_id(), "name")
        age_widget.bind_to_text_property(self.person.get_id(), "age")
        
        # Create a compound command
        compound = CompoundCommand("Update Person")
        
        # Get property IDs
        name_property_id = self.person._get_property_id("name")
        age_property_id = self.person._get_property_id("age")
        
        # Create property commands
        name_command = PropertyCommand(name_property_id, "Bob")
        age_command = PropertyCommand(age_property_id, 40)
        
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


class TestCommandGeneration:
    """Test cases for command generation from widget interactions."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        # Clear ID registry for clean tests
        registry = get_id_registry()
        registry.clear()
        
        # Clear command manager
        manager = get_command_manager()
        manager.clear()
        
        # Create test objects
        self.person = Person(name="Alice", age=30)
        self.widget = MockCommandLineEdit()
        
        # Bind widget to observable
        self.widget.bind_to_text_property(self.person.get_id(), "name")
    
    def test_command_immediate_mode(self):
        """Test commands are generated immediately by default."""
        # Set immediate trigger mode
        self.widget.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
        
        # Change widget text
        self.widget.setText("Bob")
        
        # Verify command was created and executed
        manager = get_command_manager()
        assert manager.can_undo()
        
        # Undo the command
        manager.undo()
        
        # Verify observable and widget were restored
        assert self.person.name == "Alice"
        assert self.widget.text() == "Alice"


if __name__ == "__main__":
    # Run the tests directly if this script is executed
    pytest.main(["-v", __file__])
    
    def test_multiple_property_changes(self):
        """Test batching multiple property changes."""
        # Set edit finished trigger mode
        self.widget.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
        
        # Make multiple changes
        self.widget.setText("Bob")
        self.widget.setText("Charlie")
        self.widget.setText("Dave")
        
        # Verify no command was created yet
        manager = get_command_manager()
        assert not manager.can_undo()
        
        # Simulate finishing editing
        self.widget.triggerEditingFinished()
        
        # Verify only one command was created
        assert manager.can_undo()
        
        # Get command from history
        history = manager._history
        commands = history.get_executed_commands()
        assert len(commands) == 1
        
        # Undo the command
        manager.undo()
        
        # Verify observable and widget went back to original state
        assert self.person.name == "Alice"
        assert self.widget.text() == "Alice"
    
    def test_command_properties(self):
        """Test properties of generated commands."""
        # Change widget text to generate command
        self.widget.setText("Bob")
        
        # Get command from history
        manager = get_command_manager()
        history = manager._history
        commands = history.get_executed_commands()
        
        # Verify command properties
        command = commands[0]
        assert isinstance(command, PropertyCommand)
        assert command.trigger_widget_id == self.widget.widget_id
        assert command.new_value == "Bob"
        assert command.old_value == "Alice"
        
        # Verify property ID references the correct observable property
        property_id = command.property_id
        
        # Get name property ID from person
        name_property_id = self.person._get_property_id("name")
        
        # Should be the same property ID
        assert property_id == name_property_id
        
        # Verify observable and widget were restored
        assert self.person.name == "Alice"
        assert self.widget.text() == "Alice"
    
    def test_command_edit_finished_mode(self):
        """Test commands are only generated when editing is finished."""
        # Set edit finished trigger mode
        self.widget.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
        
        # Change widget text but don't finish editing
        self.widget.setText("Bob")
        
        # Verify no command was created
        manager = get_command_manager()
        assert not manager.can_undo()
        
        # Simulate finishing editing
        self.widget.triggerEditingFinished()
        
        # Verify command was created
        assert manager.can_undo()
        
        # Undo the command
        manager.undo()
        
        # Verify observable and widget were restored
        assert self.person.name == "Alice"
        assert self.widget.text() == "Alice"
    
    def test_command_delayed_mode(self):
        """Test commands are generated after a delay."""
        # Set delayed trigger mode
        self.widget.set_command_trigger_mode(CommandTriggerMode.DELAYED)
        
        # Change widget text
        self.widget.setText("Bob")
        
        # Verify no command was created yet
        manager = get_command_manager()
        assert not manager.can_undo()
        
        # Simulate timer timeout
        self.widget._on_change_timer_timeout()
        
        # Verify command was created
        assert manager.can_undo()
        
        # Undo the command
        manager.undo()
        
if __name__ == "__main__":
    # Run the tests directly if this script is executed
    pytest.main(["-v", __file__])