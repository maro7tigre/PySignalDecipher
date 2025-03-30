# Widget System Documentation

This document provides a concise overview of the PySide6 widget integrations for using command system widgets in PySignalDecipher applications.

## Overview

The widgets system provides:
1. **Command-aware widgets** that integrate with the command system for undo/redo
2. **Container widgets** for managing child widgets and relationships
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

### Available Containers

```python
from command_system.pyside6_widgets.containers import (
    CommandTabWidget,
    # More containers will be added
)
```

### Tab Widget Usage

```python
from command_system.pyside6_widgets.containers import CommandTabWidget

# Create tab widget
tabs = CommandTabWidget()

# Register tab types
welcome_tab_id = tabs.register_tab(
    create_welcome_tab,   # Function that creates the tab content
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

### Adding Tabs

```python
# Add a tab of registered type
tabs.add_tab(welcome_tab_id)

# All tab operations generate commands automatically
# for undo/redo support
```

### Using Observables with Tabs

```python
# Register tab with existing observable instance
edit_tab_id = tabs.register_tab(
    create_edit_tab,
    tab_name="Edit Data",
    observables=[person.get_id()],  # Pass existing observable ID
    closable=True
)

# Register tab that creates new observable instances
new_person_tab_id = tabs.register_tab(
    create_person_tab,
    tab_name="New Person",
    observables=[Person],  # Pass the class to create new instances
    closable=True
)

# Tab content factory that takes an observable
def create_edit_tab(person):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # The person parameter is the observable instance
    name_edit = CommandLineEdit()
    name_edit.bind_to_text_property(person.get_id(), "name")
    layout.addWidget(name_edit)
    
    return widget
```

## Container Navigation

Containers support automatic navigation for undo/redo operations:

```python
# Navigate to a specific widget
container.navigate_to_widget(widget_id)

# Navigate to a specific location
tab_widget.navigate_to_location("2")  # Go to tab index 2
```

## Widget Lifecycle Management

```python 
# TODO: automatically  unregister when removed
# Cleaning up when widgets are no longer needed
widget.unregister_widget()

# Containers handle cleanup of children automatically
container.unregister_widget()  # Also unregisters all children
```

## Best Practices

1. **Use appropriate trigger modes** for each widget type
   - Immediate: For toggles, radio buttons
   - Delayed: For search fields, filters
   - On Edit Finished: For text fields, numeric inputs

2. **Unregister widgets** when removing them from the UI
   - Always call `unregister_widget()` when removing widgets
   - Container widgets handle this automatically for children

3. **Prefer tab registration pattern** over direct creation
   - Use `register_tab` and `add_tab` instead of directly creating tabs
   - This ensures proper command tracking and undo/redo

4. **Keep widgets bound to observables**
   - Don't update widgets directly, update the observable
   - This ensures proper command tracking and undo/redo

5. **Use container IDs**
   - Always provide container_id when creating widgets in a container
   - This ensures proper relationship tracking