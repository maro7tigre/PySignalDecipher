# Command System Documentation

This document provides a concise overview of the Command System for creating observable objects and implementing undo/redo functionality in PySignalDecipher applications.

## Overview

The Command System provides two key patterns:
1. **Observable Pattern**: For property change notification
2. **Command Pattern**: For encapsulating actions that can be executed, undone, and redone

Both patterns are integrated with the ID System for efficient memory management, reference tracking, and serialization support.

## Observable Pattern

### Creating Observable Objects

```python
from command_system.core import Observable, ObservableProperty

class Person(Observable):
    name = ObservableProperty("")
    age = ObservableProperty(0)
    
    def __init__(self):
        super().__init__()  # Important: Initialize the Observable first
        # Set initial values if needed
        self.name = "Alice"
        self.age = 30
```

### Property Change Tracking

```python
# Create an observer object (usually a widget)
class NameChangeObserver:
    def on_name_changed(self, property_name, old_value, new_value):
        print(f"Name changed from {old_value} to {new_value}")

observer = NameChangeObserver()
person = Person()

# Register observer with its object for proper ID tracking
observer_id = person.add_property_observer("name", observer.on_name_changed, observer)

# Property changes trigger notifications
person.name = "Bob"  # Triggers notification: "Name changed from Alice to Bob"

# Remove observer when no longer needed
person.remove_property_observer("name", observer_id)
```

You can also register observers without providing an observer object:

```python
# This creates a proxy object internally
observer_id = person.add_property_observer("name", lambda prop, old, new: print(f"{old} -> {new}"))
```

### Working with Object IDs

Each observable object and property is assigned a unique ID:

```python
# Get the observable's ID
person_id = person.get_id()  # Returns something like "o:1A"

# Looking up objects by ID
from command_system.id_system import get_id_registry
registry = get_id_registry()
same_person = registry.get_observable(person_id)
```

### Property Cleanup

```python
# Property IDs are cached in the observable
property_id = person._property_id_cache.get("name")

# Unregister a specific property
person.unregister_property(property_id)

# The observable will automatically unregister itself if all properties are removed
```

## Command Pattern

### Basic Commands

All commands must implement the `execute` and `undo` methods:

```python
from command_system.core import Command

class MyCommand(Command):
    def __init__(self, parameter):
        super().__init__()
        self.parameter = parameter
        
    def execute(self):
        # Perform the action
        print(f"Executing with {self.parameter}")
        
    def undo(self):
        # Reverse the action
        print(f"Undoing {self.parameter}")
```

### Property Change Commands

Change properties with automatic undo/redo support:

```python
from command_system.core import PropertyCommand, get_command_manager

person = Person()

# Get property ID - two ways to do this:
# 1. Directly from the observable
property_id = person._property_id_cache.get("name")

# 2. From the ID registry
id_registry = get_id_registry()
property_ids = id_registry.get_property_ids_by_observable_id_and_property_name(
    person.get_id(), "name"
)
property_id = property_ids[0]

# Create command with property_id and new value
cmd = PropertyCommand(property_id, "Bob")

# Execute the command
manager = get_command_manager()
manager.execute(cmd)

# Now person.name is "Bob"
print(person.name)  # Output: Bob

# Undo the command
manager.undo()

# Now person.name is back to original value
print(person.name)  # Output: Alice
```

### Widget Property Commands

Similar to PropertyCommand but for UI widgets:

```python
from command_system.core import WidgetPropertyCommand

# Get the widget's ID
widget_id = id_registry.get_id(my_widget)

# Create command to change widget property
cmd = WidgetPropertyCommand(widget_id, "text", "New Label")
manager.execute(cmd)
```

### Compound Commands

Group multiple commands to execute them as a unit:

```python
from command_system.core import CompoundCommand

# Create a compound command
compound = CompoundCommand("Update Person")

# Add multiple commands
property_id_name = person._property_id_cache.get("name")
property_id_age = person._property_id_cache.get("age")

compound.add_command(PropertyCommand(property_id_name, "Bob"))
compound.add_command(PropertyCommand(property_id_age, 30))

# Execute both commands as a unit
manager.execute(compound)

# Undo both commands at once
manager.undo()
```

### Macro Commands

Create user-level operations with descriptions:

```python
from command_system.core import MacroCommand

# Create a macro command with a descriptive name
macro = MacroCommand("Create Person")

# Add commands to the macro
property_id_name = person._property_id_cache.get("name")
property_id_age = person._property_id_cache.get("age")

macro.add_command(PropertyCommand(property_id_name, "Bob"))
macro.add_command(PropertyCommand(property_id_age, 30))

# Set a human-readable description
macro.set_description("Create a new person named Bob")

# Execute the macro
manager.execute(macro)
```

### Serialization Commands

For commands that need to capture and restore state:

```python
from command_system.core import SerializationCommand

class TabChangeCommand(SerializationCommand):
    def __init__(self, tab_widget_id, new_tab_index):
        super().__init__(tab_widget_id)
        self.new_tab_index = new_tab_index
        self.old_tab_index = None
        
        # Capture the current state before changes
        self.get_serialization()
    
    def execute(self):
        tab_widget = get_id_registry().get_widget(self.component_id)
        if tab_widget:
            self.old_tab_index = tab_widget.currentIndex()
            tab_widget.setCurrentIndex(self.new_tab_index)
    
    def undo(self):
        # Restore previous state
        self.deserialize()
```

## Command Manager

### Basic Usage

```python
from command_system.core import get_command_manager

manager = get_command_manager()

# Execute a command
manager.execute(my_command)

# Check if undo/redo is available
if manager.can_undo():
    manager.undo()
    
if manager.can_redo():
    manager.redo()
    
# Clear history
manager.clear()
```

### Command Lifecycle Hooks

Register callbacks for command execution/undo events:

```python
def before_execute(command):
    print(f"About to execute: {command}")

def after_execute(command, success):
    print(f"Executed: {command}, Success: {success}")

# Register callbacks
manager.add_before_execute_callback("my_callback", before_execute)
manager.add_after_execute_callback("my_callback", after_execute)

# Remove when no longer needed
manager.remove_callback("my_callback")
```

### Initialization Mode

Disable history tracking during initialization:

```python
manager.begin_init()

# Commands executed won't be added to history
manager.execute(setup_command1)
manager.execute(setup_command2)

manager.end_init()
```

## Integration with UI Components

### Triggering Commands from UI

```python
def on_button_clicked():
    button_id = id_registry.get_id(button)
    
    # Create command
    cmd = MyCommand(parameter)
    
    # Execute with trigger widget information
    manager.execute(cmd, button_id)
    
    # Store additional context info for navigation
    cmd.set_context_info("container_info", {"tab": 2, "panel": "settings"})
```

### Command Context Navigation

The system will automatically navigate back to the UI context when undoing/redoing commands:

```python
# In your container widget implementation:
def navigate_to_widget(self, widget_id):
    """Navigate to the given widget within this container."""
    # Implementation to focus the widget, show its tab, etc.
    widget = get_id_registry().get_widget(widget_id)
    if widget:
        widget.setFocus()
```

## Best Practices

1. **Use IDs, not direct references**
   - Store IDs instead of direct object references in commands
   - Use the ID system for lookup and relationship management

2. **Keep commands small and focused**
   - Each command should do one specific thing
   - Use compound commands for complex operations

3. **Store context information**
   - Use `set_context_info` to store navigation context with commands

4. **Clean up properly**
   - Remove observers when they're no longer needed
   - Unregister properties when they're no longer needed

5. **Use property commands for observable changes**
   - Always use PropertyCommand for changing observable properties
   - This ensures undo/redo works properly

6. **Check ID validity**
   - Always ensure IDs are valid before using them
   - Handle cases where IDs might have changed

7. **Handle serialization carefully**
   - Be consistent in how you serialize and deserialize state
   - Test serialization with undo/redo thoroughly