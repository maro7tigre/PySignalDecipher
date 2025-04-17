# PySide6 Command Widgets Guide

This guide explains how to use the PySide6 widget system with the command system for creating custom widgets with undo/redo functionality, property binding, and serialization support.

## Table of Contents

- [Overview](#overview)
- [Base Command Widget](#base-command-widget)
  - [Key Features](#key-features)
  - [Creating a Custom Widget](#creating-a-custom-widget)
  - [Property Implementation](#property-implementation)
  - [Handling Events](#handling-events)
  - [Command Trigger Modes](#command-trigger-modes)
  - [Widget Cleanup](#widget-cleanup)
- [Base Command Container](#base-command-container)
  - [Container Key Features](#container-key-features)
  - [Creating a Custom Container](#creating-a-custom-container)
  - [Subcontainer Registration and Management](#subcontainer-registration-and-management)
  - [Navigation Implementation](#navigation-implementation)
  - [Container Serialization](#container-serialization)
- [Complete Widget Example](#complete-widget-example)
- [Complete Container Example](#complete-container-example)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The PySide6 widget system integrates with the command system to provide:

- Automatic undo/redo functionality
- Observable property binding
- Widget state serialization
- Container hierarchy management
- Comprehensive event handling

The system is built around two base classes:

1. `BaseCommandWidget` - Foundation for all command-enabled widgets
2. `BaseCommandContainer` - Foundation for container widgets that can hold other widgets

## Base Command Widget

The `BaseCommandWidget` class provides the foundation for integrating PySide6 widgets with the command system.

### Key Features

- **Property Binding**: Connect widget properties to observable properties
- **Command Generation**: Auto-generate commands for property changes
- **ID System Integration**: Track widget relationships and hierarchy
- **Serialization**: Save and restore widget state

### Creating a Custom Widget

To create a custom command-enabled widget:

1. Inherit from both the PySide6 widget class and `BaseCommandWidget`
2. Initialize the base classes properly
3. Call the `initiate_widget` method
4. Implement the `_update_widget_property` method
5. Connect appropriate signals to handle property changes

Basic template:

```python
from PySide6.QtWidgets import QWidgetType
from command_system.pyside6_widgets import BaseCommandWidget
from command_system.id_system import WidgetTypeCodes

class CommandMyWidget(QWidgetType, BaseCommandWidget):
    def __init__(self, container_id=None, location=None, parent=None):
        # Initialize Qt widget first
        QWidgetType.__init__(self, parent)
        
        # Initialize command widget functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.CUSTOM_WIDGET, 
                                         container_id, location)
        
        # Connect signals for value changes
        self.valueChanged.connect(self._handle_value_changed)
        self.editingFinished.connect(self._handle_editing_finished)
    
    def _update_widget_property(self, property_name, value):
        """Update widget properties when observables change"""
        if property_name == "value":
            # Block signals to prevent recursion
            self.blockSignals(True)
            self.setValue(value)
            self.blockSignals(False)
        else:
            raise ValueError(f"Unsupported property: {property_name}")
    
    def _handle_value_changed(self, value):
        """Handle value changes from the widget"""
        self._on_widget_value_changed("value", value)
    
    def _handle_editing_finished(self):
        """Handle editing completion"""
        self._on_widget_editing_finished()
```

### Property Implementation

The `_update_widget_property` method is critical - it handles updates coming from bound observables:

```python
def _update_widget_property(self, property_name, value):
    """Called when a bound observable property changes"""
    
    # Always block signals to prevent recursion
    self.blockSignals(True)
    
    # Handle different property types
    if property_name == "value":
        self.setValue(value)
    elif property_name == "text":
        self.setText(str(value) if value is not None else "")
    elif property_name == "enabled":
        self.setEnabled(bool(value))
    else:
        raise ValueError(f"Unsupported property: {property_name}")
    
    # Re-enable signals after update
    self.blockSignals(False)
```

### Handling Events

Connect widget events to the base class handlers:

```python
# For immediate changes
self.valueChanged.connect(lambda v: self._on_widget_value_changed("value", v))

# For editing completion
self.editingFinished.connect(self._on_widget_editing_finished)
```

The base class provides two key methods:

- `_on_widget_value_changed(property_name, new_value)` - Handle property changes
- `_on_widget_editing_finished()` - Process pending changes when editing is complete

### Command Trigger Modes

Configure when commands are generated:

```python
# Set command trigger mode in __init__
self.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)  # Generate on every change
# or
self.set_command_trigger_mode(CommandTriggerMode.DELAYED, 500)  # 500ms delay after changes
# or
self.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)  # When editing completes
```

### Widget Cleanup

Ensure resources are properly cleaned up to prevent memory leaks:

```python
def closeEvent(self, event):
    """Override to clean up resources"""
    # Unregister from the ID system
    self.unregister_widget()
    
    # Allow the base class to handle the event
    super().closeEvent(event)
```

## Base Command Container

The `BaseCommandContainer` class extends `BaseCommandWidget` to provide container functionality.

### Container Key Features

- **Subcontainer Management**: Create and track subcontainers
- **Type Registration**: Register factory functions for subcontainer types
- **Hierarchy Navigation**: Navigate through container hierarchy
- **Widget Registration**: Track child widgets

### Creating a Custom Container

To create a custom command-enabled container:

1. Inherit from both a PySide6 container widget and `BaseCommandContainer`
2. Initialize the base classes properly
3. Call the `initiate_container` method
4. Implement the `create_subcontainer` method
5. Implement the `navigate_to_position` method

Basic template:

```python
from PySide6.QtWidgets import QContainerWidget
from command_system.pyside6_widgets import BaseCommandContainer
from command_system.id_system import ContainerTypeCodes

class CommandMyContainer(QContainerWidget, BaseCommandContainer):
    def __init__(self, container_id=None, location=None, parent=None):
        # Initialize Qt widget first
        QContainerWidget.__init__(self, parent)
        
        # Initialize container functionality with container type code
        self.initiate_container(ContainerTypeCodes.CUSTOM, container_id, location)
    
    def create_subcontainer(self, type_id, position=None):
        """Create an empty subcontainer for the specified type"""
        # Create the appropriate container widget
        subcontainer = QWidget()
        layout = QVBoxLayout(subcontainer)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add to this container
        index = self.addWidget(subcontainer)
        
        # Convert position to container-specific location format
        location = str(index)
        
        return subcontainer, location
    
    def navigate_to_position(self, position):
        """Navigate to a specific position within this container"""
        try:
            index = int(position)
            if 0 <= index < self.count():
                self.setCurrentIndex(index)
                return True
        except ValueError:
            pass
        
        return False
```

### Subcontainer Registration and Management

Register subcontainer types and add instances:

```python
# Register subcontainer type
def register_subcontainer_type(self, factory_func, observables=None, type_id=None, **options):
    return super().register_subcontainer_type(factory_func, observables, type_id, **options)

# Add a subcontainer of a registered type
def add_subcontainer(self, type_id, position=None):
    return super().add_subcontainer(type_id, position)

# Close a subcontainer
def close_subcontainer(self, subcontainer_id):
    return super().close_subcontainer(subcontainer_id)
```

The factory function creates content for subcontainers:

```python
def create_my_content(model):
    """Factory function for subcontainer content"""
    # Create widget content
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # Create child widgets using the model
    label = QLabel(model.name)
    button = QPushButton("Update")
    
    # Add to layout
    layout.addWidget(label)
    layout.addWidget(button)
    
    return widget
```

### Navigation Implementation

The navigation system allows moving between widgets in different containers:

```python
def navigate_to_position(self, position):
    """Navigate to a specific position within this container"""
    # Convert position string to container-specific format
    try:
        index = int(position)
        if 0 <= index < self.count():
            self.setCurrentIndex(index)
            return True
    except ValueError:
        # Handle case where position isn't a simple index
        pass
    
    return False
```

### Container Serialization

Containers handle serialization for both themselves and their subcontainers:

```python
def get_serialization(self):
    """Get serialized representation of this container"""
    # Get base serialization
    result = super().get_serialization()
    
    # Add container-specific state
    result.update({
        'current_index': self.currentIndex(),
        'other_setting': self.otherSetting()
    })
    
    return result

def deserialize(self, serialized_data):
    """Restore this container's state from serialized data"""
    # Let the base class handle the common serialization
    if not super().deserialize(serialized_data):
        return False
    
    # Handle container-specific properties
    if 'current_index' in serialized_data:
        self.setCurrentIndex(serialized_data['current_index'])
    
    if 'other_setting' in serialized_data:
        self.setOtherSetting(serialized_data['other_setting'])
    
    return True
```

## Complete Widget Example

Here's a complete example of a custom command-enabled spin box:

```python
from PySide6.QtWidgets import QSpinBox
from PySide6.QtCore import Signal, Slot
from command_system.pyside6_widgets import BaseCommandWidget, CommandTriggerMode
from command_system.id_system import WidgetTypeCodes

class CommandSpinBox(QSpinBox, BaseCommandWidget):
    """A command-system integrated spin box widget."""
    
    def __init__(self, container_id=None, location=None, parent=None):
        # Initialize QSpinBox first
        QSpinBox.__init__(self, parent)
        
        # Initialize command widget functionality
        BaseCommandWidget.initiate_widget(self, WidgetTypeCodes.SPIN_BOX, container_id, location)
        
        # Connect signals for value changes
        self.valueChanged.connect(self._handle_value_changed)
        self.editingFinished.connect(self._handle_editing_finished)
        
        # Default to immediate trigger mode for better UX with spin box
        self.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)
    
    def _update_widget_property(self, property_name, value):
        """Update widget properties when observables change"""
        if property_name == "value":
            self.blockSignals(True)
            self.setValue(int(value) if value is not None else 0)
            self.blockSignals(False)
        else:
            raise ValueError(f"Unsupported property: {property_name}")
    
    @Slot(int)
    def _handle_value_changed(self, value):
        """Handle value changes from the widget"""
        self._on_widget_value_changed("value", value)
    
    @Slot()
    def _handle_editing_finished(self):
        """Handle editing completion"""
        self._on_widget_editing_finished()
    
    # Convenience methods
    def bind_to_value_property(self, observable_id, property_name):
        """Convenience method to bind value property"""
        self.bind_property("value", observable_id, property_name)
    
    def unbind_value_property(self):
        """Convenience method to unbind value property"""
        self.unbind_property("value")
    
    # Serialization
    def get_serialization(self):
        """Get serialized representation of this widget"""
        result = super().get_serialization()
        
        # Add QSpinBox-specific properties
        result['spin_box_props'] = {
            'min_value': self.minimum(),
            'max_value': self.maximum(),
            'step': self.singleStep()
        }
        
        return result
    
    def deserialize(self, data):
        """Restore this widget's state from serialized data"""
        if not super().deserialize(data):
            return False
        
        # Handle QSpinBox-specific properties
        if 'spin_box_props' in data:
            props = data['spin_box_props']
            if 'min_value' in props:
                self.setMinimum(props['min_value'])
            if 'max_value' in props:
                self.setMaximum(props['max_value'])
            if 'step' in props:
                self.setSingleStep(props['step'])
        
        return True
```

## Complete Container Example

Here's a complete example of a custom command-enabled stack widget:

```python
from PySide6.QtWidgets import QStackedWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Signal, Slot
from command_system.pyside6_widgets import BaseCommandContainer
from command_system.id_system import ContainerTypeCodes
from command_system.core import SerializationCommand, get_command_manager

class CommandStackedWidget(QStackedWidget, BaseCommandContainer):
    """A command-system integrated stacked widget container."""
    
    # Signals
    pageAdded = Signal(str)      # subcontainer_id
    pageClosed = Signal(str)     # subcontainer_id
    
    def __init__(self, container_id=None, location=None, parent=None):
        # Initialize QStackedWidget
        QStackedWidget.__init__(self, parent)
        
        # Initialize container with CUSTOM type code
        self.initiate_container(ContainerTypeCodes.CUSTOM, container_id, location)
        
        # Track the current page for undo/redo operations
        self._last_page_index = self.currentIndex()
        
        # Connect signals
        self.currentChanged.connect(self._on_current_changed)
    
    def create_subcontainer(self, type_id, position=None):
        """Create an empty subcontainer for the specified type"""
        # Validate type exists
        type_info = self._widget_types.get(type_id)
        if not type_info:
            return None, None
        
        # Create an empty container widget for the page
        page_container = QWidget()
        
        # Use a layout for the page content
        layout = QVBoxLayout(page_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the page
        index = self.addWidget(page_container)
        
        # Set as current page
        self.setCurrentIndex(index)
        
        # Update the last page index to match current after adding
        self._last_page_index = self.currentIndex()
        
        # For ID system location, use the string representation of the index
        page_location = str(index)
        
        return page_container, page_location
    
    def add_page(self, type_id):
        """Add a new page of the registered type"""
        # Check if we're in a command execution
        if get_command_manager().is_updating():
            # Direct page addition during command execution
            subcontainer_id = self.add_subcontainer(type_id)
            if subcontainer_id:
                # Emit signal for the new page
                self.pageAdded.emit(subcontainer_id)
                # Update the last page index to match current
                self._last_page_index = self.currentIndex()
            return subcontainer_id
        
        # Create a command for adding a page
        cmd = AddPageCommand(type_id, self.get_id())
        cmd.set_trigger_widget(self.get_id())
        get_command_manager().execute(cmd)
        return cmd.component_id
    
    def close_page(self, page_index):
        """Close a page at the given index"""
        # Validate index
        if not (0 <= page_index < self.count()):
            return False
        
        # Get the widget at the index
        page_widget = self.widget(page_index)
        if not page_widget:
            return False
        
        # Get the subcontainer ID
        id_registry = self.id_registry
        subcontainer_id = id_registry.get_id(page_widget)
        if not subcontainer_id:
            return False
        
        # Close the subcontainer (will handle ID cleanup)
        if not self.close_subcontainer(subcontainer_id):
            return False
        
        # Emit signal before removing the page
        self.pageClosed.emit(subcontainer_id)
        
        # Remove the page from the widget
        self.removeWidget(page_widget)
        
        # Make sure _last_page_index is updated if needed
        if self._last_page_index >= self.count():
            self._last_page_index = self.currentIndex()
        
        return True
    
    def navigate_to_position(self, position):
        """Navigate to a specific page by position"""
        try:
            page_index = int(position)
            if 0 <= page_index < self.count():
                self.setCurrentIndex(page_index)
                return True
        except ValueError:
            pass
        
        return False
    
    @Slot(int)
    def _on_current_changed(self, index):
        """Handle page selection change"""
        # Skip if we're executing a command to avoid recursion
        if get_command_manager().is_updating():
            return
        
        # Get the old index for the command
        old_index = self._last_page_index
        
        # Update the last page index for future changes
        self._last_page_index = index
        
        # Only create command if index actually changed
        if old_index != index:
            cmd = PageSelectionCommand(self.get_id(), old_index, index)
            cmd.set_trigger_widget(self.get_id())
            get_command_manager().execute(cmd)
    
    def get_serialization(self):
        """Get serialized representation of this stacked widget"""
        result = super().get_serialization()
        
        # Add stacked widget specific state
        result.update({
            'current_index': self.currentIndex()
        })
        
        return result
    
    def deserialize(self, serialized_data):
        """Deserialize and restore stacked widget state"""
        # First restore base container state
        if not super().deserialize(serialized_data):
            return False
        
        # Set current index last to avoid multiple signals
        if 'current_index' in serialized_data:
            current_index = serialized_data['current_index']
            if 0 <= current_index < self.count():
                self.setCurrentIndex(current_index)
                # Update our tracking variable
                self._last_page_index = current_index
        
        return True

# Command classes for the stacked widget
class AddPageCommand(SerializationCommand):
    """Command for adding a new page with serialization support."""
    
    def __init__(self, type_id, container_id):
        super().__init__()
        self.type_id = type_id
        self.container_id = container_id
        self.component_id = None
    
    def execute(self):
        """Execute to add the page."""
        container = get_id_registry().get_widget(self.container_id)
        if container:
            self.component_id = container.add_subcontainer(self.type_id)
    
    def undo(self):
        """Undo saves serialization and closes page."""
        if self.component_id:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Save serialization before closing
                self.serialized_state = container.serialize_subcontainer(self.component_id)
                
                # Find position from stored value
                position = container.get_subcontainer_position(self.component_id)
                if position:
                    try:
                        page_index = int(position)
                        container.close_page(page_index)
                    except ValueError:
                        pass
    
    def redo(self):
        """Redo restores the page from serialization."""
        if self.serialized_state:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Restore from serialization
                container.deserialize_subcontainer(
                    self.type_id,
                    self.serialized_state.get('position', '0'),
                    self.serialized_state
                )
        else:
            # Fall back to normal execute if no serialization available
            self.execute()

class PageSelectionCommand(Command):
    """Command for changing the selected page."""
    
    def __init__(self, stack_widget_id, old_index, new_index):
        super().__init__()
        self.stack_widget_id = stack_widget_id
        self.old_index = old_index
        self.new_index = new_index
    
    def execute(self):
        """Execute the command to change the selected page."""
        stack_widget = get_id_registry().get_widget(self.stack_widget_id)
        if stack_widget and 0 <= self.new_index < stack_widget.count():
            stack_widget.setCurrentIndex(self.new_index)
            # Update the internal tracking to match
            if hasattr(stack_widget, '_last_page_index'):
                stack_widget._last_page_index = self.new_index
    
    def undo(self):
        """Undo the command by selecting the previous page."""
        stack_widget = get_id_registry().get_widget(self.stack_widget_id)
        if stack_widget and 0 <= self.old_index < stack_widget.count():
            stack_widget.setCurrentIndex(self.old_index)
            # Update the internal tracking to match
            if hasattr(stack_widget, '_last_page_index'):
                stack_widget._last_page_index = self.old_index
```

## Best Practices

1. **Always Block Signals During Updates**
   ```python
   self.blockSignals(True)
   # Update widget state
   self.blockSignals(False)
   ```

2. **Clean Up Resources Properly**
   ```python
   # Unbind all properties
   def closeEvent(self, event):
       self.unregister_widget()
       super().closeEvent(event)
   ```

3. **Use Appropriate Command Trigger Mode**
   - `IMMEDIATE`: For sliders, spinners where immediate feedback is expected
   - `DELAYED`: For typeahead searches and rapid changes
   - `ON_EDIT_FINISHED`: For text fields and forms

4. **Provide Convenience Methods for Property Binding**
   ```python
   def bind_to_value_property(self, observable_id, property_name):
       self.bind_property("value", observable_id, property_name)
   
   def unbind_value_property(self):
       self.unbind_property("value")
   ```

5. **Handle Serialization Carefully**
   ```python
   # Include all state needed for restoration
   def get_serialization(self):
       result = super().get_serialization()
       result['widget_specific'] = {
           'important_setting': self.importantSetting()
       }
       return result
   ```

6. **Use Container Hierarchy for Complex UIs**
   ```python
   # Create nested containers
   main_container = CommandTabWidget()
   tab_id = main_container.add_tab(tab_type_id)
   
   # Get the tab subcontainer
   tab_widget = main_container.get_subcontainer(tab_id)
   
   # Add content to the tab
   content_container = CommandStackedWidget(tab_id)
   ```

## Troubleshooting

1. **Property Changes Not Triggering Commands**
   - Check if signals are properly connected
   - Verify command trigger mode is appropriate 
   - Ensure you're not in a recursion loop with blocking signals

2. **Containers Not Tracking Children**
   - Check if widgets are registered with the correct container ID
   - Verify the container hierarchy is properly set up
   - Ensure `create_subcontainer` is implemented correctly

3. **Serialization Issues**
   - Ensure all required state is included in serialization
   - Check for correct ID handling during deserialization
   - Verify container hierarchy is properly maintained

4. **Memory Leaks**
   - Ensure `unregister_widget` is called during cleanup
   - Unbind properties when no longer needed
   - Check for lingering references to widgets