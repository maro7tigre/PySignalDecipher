# Command System Documentation

This document provides a concise overview of the Command System for creating observable objects and implementing undo/redo functionality in the PySignalDecipher application.

## Overview

The Command System provides two key patterns:
1. **Observable Pattern**: For property change notification
2. **Command Pattern**: For encapsulating actions that can be executed, undone, and redone

Both patterns are integrated with the ID System for efficient memory management and serialization support.

## Observable Pattern

### Creating Observable Objects

```python
from command_system.core import Observable, ObservableProperty

class Person(Observable):
    name = ObservableProperty("")
    age = ObservableProperty(0)
    
    def __init__(self):
        super().__init__()
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

person.name = "Alice"  # Triggers notification: "Name changed from  to Alice"

# Remove observer when no longer needed
person.remove_property_observer("name", observer_id)
```

You can also register observers without providing an object:

```python
# This creates a proxy object internally
observer_id = person.add_property_observer("name", lambda prop, old, new: print(f"{old} -> {new}"))
```

### Getting Object IDs

```python
# Get the observable's ID
person_id = person.get_id()

# IDs are used for commands and lookups
from command_system.id_system import get_id_registry
registry = get_id_registry()
same_person = registry.get_observable(person_id)
```

### Property Cleanup

```python
# Unregister a specific property
property_id = person._property_id_cache.get("name")
person.unregister_property(property_id)

# The observable will automatically unregister itself if all properties are removed
```

### Serialization and Deserialization

Observables support property-level serialization:

```python
# Serialize a specific property
property_id = person._property_id_cache.get("name")
serialized_property = person.serialize_property(property_id)

# Deserialize a property (updates the property value)
person.deserialize_property(property_id, serialized_property)
```

The serialized property format includes essential information:

```python
{
    'property_id': 'op:1A:2B:name:0',
    'property_name': 'name',
    'value': 'Alice',
    'observable_id': 'o:2B'
}
```

If the observable ID has changed during deserialization, the system will:
1. Check for any existing observables with that ID (to detect cleanup failures)
2. Update the observable's ID
3. Update all property IDs to maintain the relationship

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
person_id = person.get_id()

# Create a command to change the name
cmd = PropertyCommand(person_id, "name", "Bob")

# Execute the command
manager = get_command_manager()
manager.execute(cmd)

# Now person.name is "Bob"
print(person.name)  # Output: Bob

# Undo the command
manager.undo()

# Now person.name is back to original value
print(person.name)  # Output: ""
```

### Widget Property Commands

Similar to PropertyCommand but for UI widgets:

```python
from command_system.core import WidgetPropertyCommand

# Get the widget's ID
widget_id = registry.get_id(my_widget)

# Create command to change widget property
cmd = WidgetPropertyCommand(widget_id, "text", "New Label")
manager.execute(cmd)
```

### Compound Commands

Group multiple commands to execute them as a unit:

```python
from command_system.core import CompoundCommand

compound = CompoundCommand("Update Person")
compound.add_command(PropertyCommand(person_id, "name", "Bob"))
compound.add_command(PropertyCommand(person_id, "age", 30))

# Execute both commands as a unit
manager.execute(compound)

# Undo both commands at once
manager.undo()
```

### Macro Commands

Create user-level operations with descriptions:

```python
from command_system.core import MacroCommand

macro = MacroCommand("Create Person")
macro.add_command(PropertyCommand(person_id, "name", "Bob"))
macro.add_command(PropertyCommand(person_id, "age", 30))
macro.set_description("Create a new person named Bob")

# Execute the macro
manager.execute(macro)
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
    button_id = registry.get_id(button)
    
    # Create command
    cmd = MyCommand(parameter)
    
    # Execute with trigger widget information
    manager.execute(cmd, button_id)
    
    # Store additional context info for navigation
    cmd.set_context_info("container_info", {"tab": 2, "panel": "settings"})
```

### Command Context Navigation

The system will automatically navigate back to the UI context when undoing/redoing commands.

## Best Practices

1. **Use IDs, not references**: Store IDs instead of direct object references in commands
2. **Keep commands small**: Each command should do one specific thing
3. **Use compound commands** for complex operations
4. **Store context info** with commands for proper navigation during undo/redo
5. **Clean up observers** when they're no longer needed
6. **Unregister properties** when they're no longer needed
7. **Check for serialization errors** to detect cleanup failures