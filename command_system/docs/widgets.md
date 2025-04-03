# Widget System Documentation

This document provides a concise overview of the PySide6 widget integrations for using command system widgets and containers in PySignalDecipher applications.

## Overview

The widgets system provides:
1. **Command-aware widgets** that integrate with the command system for undo/redo
2. **Container widgets** for managing subcontainers and their relationships
3. **Property binding** to connect widgets with observable properties
4. **Automatic ID handling** for proper tracking and serialization

## Command Widgets

### Available Widgets

```python
from command_system.pyside6_widgets import (
    CommandLineEdit,
    # More widgets will be added
)
```

### Basic Widget Usage

```python
from command_system.pyside6_widgets import CommandLineEdit

# Create a command-aware line edit
edit = CommandLineEdit()
```

### Binding to Observable Properties

```python
# Create an observable
person = Person()  # An Observable class with properties
person_id = person.get_id()

# Bind a widget to an observable property
edit = CommandLineEdit()
edit.bind_to_text_property(person_id, "name")

# More generic binding method
edit.bind_property("text", person_id, "name")

# Unbinding when no longer needed
edit.unbind_property("text")
```

### Controlling Command Trigger Behavior

```python
from command_system.pyside6_widgets import CommandTriggerMode

# Change when commands are generated
edit = CommandLineEdit()

# Immediate: Generate command on every keystroke
edit.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)

# Delayed: Wait for typing to pause (good for search fields)
edit.set_command_trigger_mode(CommandTriggerMode.DELAYED, delay_ms=500)

# On Edit Finished: Only generate command when editing is complete (default)
edit.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)
```

## Container Widgets

Containers provide a way to manage collections of subcontainers (like tabs, docks, etc.) with proper ID tracking and undo/redo support.

### Available Containers

```python
from command_system.pyside6_widgets.containers import (
    CommandTabWidget,
    # More containers will be added
)
```

### Container Usage

#### Creating a Container

```python
from command_system.pyside6_widgets.containers import CommandTabWidget

# Create a tab widget container
tabs = CommandTabWidget()
```

#### Registering Subcontainer Types

```python
# Register a subcontainer type
welcome_tab_id = tabs.register_subcontainer_type(
    create_welcome_tab,   # Function that creates the content
    tab_name="Welcome",   # Display name
    observables=[],       # No observables needed
    closable=False        # Cannot be closed
)

# Function to create tab content
def create_welcome_tab():
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.addWidget(QLabel("Welcome to the app!"))
    return widget
```

#### Adding Subcontainers

```python
# Add a subcontainer of registered type
subcontainer_id = tabs.add_tab(welcome_tab_id)

# All subcontainer operations generate commands automatically
# for undo/redo support
```

### Using Observables with Containers

Containers support both existing and new observable instances:

```python
# Register subcontainer with existing observable instance
edit_tab_id = tabs.register_subcontainer_type(
    create_edit_tab,
    tab_name="Edit Data",
    observables=[person.get_id()],  # Pass existing observable ID
    closable=True
)

# Register subcontainer that creates new observable instances
new_person_tab_id = tabs.register_subcontainer_type(
    create_person_tab,
    tab_name="New Person",
    observables=[Person],  # Pass the class to create new instances
    closable=True
)

# Content factory that takes an observable
def create_edit_tab(person):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # The person parameter is the observable instance
    name_edit = CommandLineEdit()
    name_edit.bind_to_text_property(person.get_id(), "name")
    layout.addWidget(name_edit)
    
    return widget
```

### Working with Subcontainers

```python
# Get a subcontainer by ID
subcontainer = tabs.get_subcontainer(subcontainer_id)

# Get the type of a subcontainer
type_id = tabs.get_subcontainer_type(subcontainer_id)

# Get location of a subcontainer
location = tabs.get_subcontainer_location(subcontainer_id)

# Get all subcontainers
all_subcontainers = tabs.get_all_subcontainers()

# Close a subcontainer
tabs.close_subcontainer(subcontainer_id)
```

### Container Navigation

Containers support automatic navigation for undo/redo operations:

```python
# Navigate to a specific widget
container.navigate_to_widget(widget_id)

# Navigate to a specific location
tab_widget.navigate_to_location("2")  # Go to tab index 2
```

### Tab-specific Operations

```python
# Tab specific methods
tab_widget.set_tab_closable(1, False)  # Make tab at index 1 non-closable
```

## Container Serialization

Containers support serialization for saving and restoring state:

```python
# Get serialized state of a container
serialized_data = container.get_serialization()

# Restore container from serialized state
container.deserialize(serialized_data)
```

## Widget Lifecycle Management

```python
# Unregister a widget when no longer needed
widget.unregister_widget()

# Containers handle cleanup of subcontainers automatically
container.unregister_widget()  # Also unregisters all subcontainers
```

## Best Practices

1. **Use appropriate trigger modes** for each widget type
   - Immediate: For toggles, radio buttons
   - Delayed: For search fields, filters
   - On Edit Finished: For text fields, numeric inputs

2. **Unregister widgets** when removing them from the UI
   - Always call `unregister_widget()` when removing widgets
   - Container widgets handle this automatically for subcontainers

3. **Use type registration pattern** for containers
   - Register subcontainer types with `register_subcontainer_type()`
   - Add subcontainers with `add_subcontainer()` or specific methods like `add_tab()`
   - This ensures proper command tracking and undo/redo

4. **Keep widgets bound to observables**
   - Don't update widgets directly, update the observable
   - This ensures proper command tracking and undo/redo

5. **Serialization for persistence**
   - Use `get_serialization()` to save container state
   - Use `deserialize()` to restore container state
   - This works recursively for all subcontainers

## Advanced Usage: Creating Custom Containers

To create a custom container type:

1. Inherit from both your Qt container and `BaseCommandContainer`
2. Initialize both parent classes
3. Implement the `create_subcontainer()` method to create your container type

```python
class CustomDockContainer(QDockWidget, BaseCommandContainer):
    def __init__(self, parent=None, container_id=None, location=None):
        # Initialize both parent classes
        QDockWidget.__init__(self, parent)
        self.initiate_container(TypeCodes.DOCK_CONTAINER, container_id, location)
        
    def create_subcontainer(self, type_id, location):
        # Create your container type
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Set up your container widget
        self.setWidget(panel)
        self.setWindowTitle(f"Dock {location}")
        
        # Return the subcontainer widget
        return panel
        
    def navigate_to_location(self, location):
        # Implement navigation
        self.setVisible(True)
        self.raise_()
        return True
```