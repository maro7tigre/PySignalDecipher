# Command System Documentation

This document provides a comprehensive overview of the Command System for creating observable objects and implementing undo/redo functionality in applications.

## Table of Contents

- [Overview](#overview)
- [Observable Pattern](#observable-pattern)
  - [Creating Observable Objects](#creating-observable-objects)
  - [Property Change Tracking](#property-change-tracking)
  - [Observer Management](#observer-management)
  - [Working with Observable IDs](#working-with-observable-ids)
  - [Serialization and Deserialization](#serialization-and-deserialization)
  - [Resource Management](#resource-management)
- [Command Pattern](#command-pattern)
  - [Basic Commands](#basic-commands)
  - [Property Commands](#property-commands)
  - [Widget Property Commands](#widget-property-commands)
  - [Compound Commands](#compound-commands)
  - [Macro Commands](#macro-commands)
  - [Serialization Commands](#serialization-commands)
  - [Command Context Information](#command-context-information)
- [Command Manager](#command-manager)
  - [Basic Usage](#basic-usage)
  - [Command Lifecycle Hooks](#command-lifecycle-hooks)
  - [Initialization Mode](#initialization-mode)
  - [Command Context Navigation](#command-context-navigation)
- [Integration with UI Components](#integration-with-ui-components)
  - [Command-Enabled Widgets](#command-enabled-widgets)
  - [Property Binding](#property-binding)
  - [Unbinding Properties](#unbinding-properties)
  - [Custom Command Triggering](#custom-command-triggering)
  - [Widget Serialization](#widget-serialization)
- [Common Patterns and Examples](#common-patterns-and-examples)
  - [Form Data Binding](#form-data-binding)
  - [Multi-step Operations](#multi-step-operations)
  - [Undo/Redo Stack Management](#undoredo-stack-management)
  - [Component State Persistence](#component-state-persistence)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Overview

The Command System consists of two primary design patterns working together:

1. **Observable Pattern**: For tracking property changes with automatic notification
2. **Command Pattern**: For encapsulating actions that can be executed, undone, and redone

Both patterns are integrated with the ID System for efficient memory management, reference tracking, and serialization. This combination provides a robust foundation for building applications with comprehensive undo/redo functionality.

Key benefits include:
- Decoupling UI components from data models
- Simple implementation of undo/redo functionality 
- Automatic tracking of relationships between components
- Clean serialization and restoration of application state
- Event-driven UI updates through property observation

## Observable Pattern

### Creating Observable Objects

To create an observable object, inherit from the `Observable` base class and define properties using `ObservableProperty`:

```python
from command_system.core import Observable, ObservableProperty

class Person(Observable):
    name = ObservableProperty("")
    age = ObservableProperty(0)
    
    def __init__(self):
        # Important: Initialize Observable first to register with ID system
        super().__init__()
        
        # Set initial values if needed
        self.name = "Alice"
        self.age = 30
```

Key points:
- Always call `super().__init__()` first in your initializer
- Each `ObservableProperty` generates automatic change notifications
- Default values can be provided to the `ObservableProperty` constructor
- You can set property values in the constructor after calling `super().__init__()`

### Property Change Tracking

Observable properties automatically notify observers when their values change:

```python
# Create an observer function
def on_name_changed(property_name, old_value, new_value):
    print(f"Name changed from {old_value} to {new_value}")

# Create person object
person = Person()

# Register observer function (returns observer ID for later removal)
observer_id = person.add_property_observer("name", on_name_changed)

# Property changes trigger notifications
person.name = "Bob"  # Triggers notification: "Name changed from Alice to Bob"

# Remove observer when no longer needed
person.remove_property_observer("name", observer_id)
```

You can also register observers with an observer object for proper tracking:

```python
class NameObserver:
    def on_name_changed(self, property_name, old_value, new_value):
        print(f"Name changed from {old_value} to {new_value}")

observer = NameObserver()
observer_id = person.add_property_observer("name", observer.on_name_changed, observer)
```

### Observer Management

Observer callbacks receive three arguments:
1. `property_name`: Name of the property that changed
2. `old_value`: Previous value of the property
3. `new_value`: New value of the property

The `add_property_observer` method returns an observer ID that you should store if you plan to later remove this observer:

```python
# Store the observer ID for later removal
observer_id = person.add_property_observer("name", on_name_changed)

# Later, use the ID to remove the observer
person.remove_property_observer("name", observer_id)
```

Internally, observables track observers using a mapping from observer IDs to callbacks. This ensures reliable observer removal even when using lambda functions or other complex callback scenarios.

Best practices for observers:
- Always store the observer ID returned from add_property_observer
- Always remove observers when they're no longer needed
- Keep observer callbacks lightweight
- Avoid modifying observed properties inside observer callbacks
- When registering class methods as observers, provide the instance as the observer object

### Working with Observable IDs

Each observable and its properties are assigned unique IDs by the ID system:

```python
# Get the observable's ID
person_id = person.get_id()

# Get property ID from the observable
property_id = person._get_property_id("name")

# Looking up objects by ID
from command_system.id_system import get_id_registry
registry = get_id_registry()
same_person = registry.get_observable(person_id)
```

The ID system maintains relationships between observables and their properties, enabling:
- Reference tracking without direct object references
- Serialization and restoration of object hierarchies
- Change notification across component boundaries

### Serialization and Deserialization

Observables and their properties can be serialized to dictionaries:

```python
# Serialize a specific property
serialized_name = person.serialize_property("name")
# Result: {'property_id': 'op:1:1:name:0', 'property_name': 'name', 'value': 'Bob', 'observable_id': 'ob:1'}

# Serialize the entire observable
serialized_person = person.serialize()
# Result: {'id': 'ob:1', 'properties': {'name': {...}, 'age': {...}}}

# Deserialize property
person.deserialize_property("name", serialized_name)

# Deserialize entire observable
person.deserialize(serialized_person)
```

Serialization preserves:
- Property values
- Observable and property IDs
- Relationships between properties and observables

This is particularly useful for:
- Saving application state
- Implementing undo/redo functionality
- Transferring object state between components

### Resource Management

To prevent memory leaks, unregister observables and properties when they're no longer needed:

```python
# Unregister a specific property
person.unregister_property("name")

# Unregister the entire observable with all its properties
person.unregister()
```

Observables also implement `__del__` to clean up when they're garbage collected, but explicit unregistration is recommended when possible.

## Command Pattern

### Basic Commands

All commands must extend the `Command` abstract base class and implement at least `execute()` and `undo()` methods:

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
        
    def redo(self):
        # Optional: Override if redo differs from execute
        # Default implementation calls execute()
        self.execute()
```

Key principles:
- Commands should be self-contained with all necessary data
- Each command should perform a single logical operation
- The `undo()` method should restore the exact previous state
- Store state information during `execute()` for use during `undo()`

### Property Commands

`PropertyCommand` changes observable properties with automatic undo/redo support:

```python
from command_system.core import PropertyCommand, get_command_manager

person = Person()

# Get property ID from observable
property_id = person._get_property_id("name")

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

# Redo the command
manager.redo()
```

Key features:
- Uses property IDs rather than direct references
- Automatically captures the old value for undo
- Works with any property registered with the ID system

### Widget Property Commands

`WidgetPropertyCommand` changes widget properties with automatic undo/redo:

```python
from command_system.core import WidgetPropertyCommand

# Get the widget's ID from ID registry
widget_id = registry.get_id(my_widget)

# Create command to change widget property
cmd = WidgetPropertyCommand(widget_id, "text", "New Label")
manager.execute(cmd)
```

This is particularly useful for:
- UI state changes that should be undoable
- Widget properties not bound to observable properties
- One-time property changes

### Compound Commands

Group multiple commands to execute them as a unit with `CompoundCommand`:

```python
from command_system.core import CompoundCommand

# Create a compound command
compound = CompoundCommand("Update Person")

# Add multiple commands
property_id_name = person._get_property_id("name")
property_id_age = person._get_property_id("age")

compound.add_command(PropertyCommand(property_id_name, "Bob"))
compound.add_command(PropertyCommand(property_id_age, 30))

# Execute both commands as a unit
manager.execute(compound)

# Undo both commands at once
manager.undo()
```

Advantages:
- All commands execute, undo, and redo as a single unit
- Ensures atomic operations across multiple properties
- Simplifies complex operations in the command history

### Macro Commands

`MacroCommand` extends `CompoundCommand` with user-level operation descriptions:

```python
from command_system.core import MacroCommand

# Create a macro command with a descriptive name
macro = MacroCommand("Create Person")

# Add commands to the macro
property_id_name = person._get_property_id("name")
property_id_age = person._get_property_id("age")

macro.add_command(PropertyCommand(property_id_name, "Bob"))
macro.add_command(PropertyCommand(property_id_age, 30))

# Set a human-readable description
macro.set_description("Create a new person named Bob")

# Execute the macro
manager.execute(macro)
```

Macro commands are useful for:
- User-visible operations in undo/redo history
- Grouping related changes with a descriptive name
- Operations that should appear as a single step to users

### Serialization Commands

For commands that need to capture and restore component state:

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

SerializationCommand is ideal for:
- Complex widget state changes
- Components with hierarchical structure
- Container contents manipulation

### Command Context Information

Commands can store additional context information:

```python
# Create and execute a command
cmd = PropertyCommand(property_id, "Bob")
cmd.set_trigger_widget(button_id)
cmd.set_context_info("editor_context", {"line": 10, "column": 5})
manager.execute(cmd)
```

This context is useful for:
- Navigation back to command source during undo/redo
- Storing auxiliary information about command origins
- Preserving UI state across command operations

## Command Manager

### Basic Usage

The `CommandManager` is a singleton that coordinates command execution and history:

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

The manager ensures:
- Commands execute properly
- History is maintained for undo/redo
- Command lifecycle callbacks are triggered
- Command context is navigated during undo/redo

### Command Lifecycle Hooks

Register callbacks for command execution and undo events:

```python
def before_execute(command):
    print(f"About to execute: {command}")

def after_execute(command, success):
    print(f"Executed: {command}, Success: {success}")

# Register callbacks
manager = get_command_manager()
manager.add_before_execute_callback("my_callback", before_execute)
manager.add_after_execute_callback("my_callback", after_execute)

# Remove when no longer needed
manager.remove_callback("my_callback")
```

Available callback types:
- `before_execute`: Called before a command executes
- `after_execute`: Called after a command executes, with success flag
- `before_undo`: Called before a command undoes
- `after_undo`: Called after a command undoes, with success flag

These callbacks enable:
- UI updates before/after operations
- Logging of command operations
- Error handling for failed commands
- Application state validation

### Initialization Mode

Disable history tracking during initialization:

```python
manager = get_command_manager()
manager.begin_init()

# Commands executed won't be added to history
manager.execute(setup_command1)
manager.execute(setup_command2)

manager.end_init()
```

This is useful during:
- Application startup
- Loading saved state
- Initial UI setup
- Data initialization

### Command Context Navigation

The command manager automatically navigates back to the UI context when undoing/redoing commands:

```python
# Define navigation in your container widget
class MyContainer:
    def navigate_to_widget(self, widget_id):
        """Navigate to the given widget within this container."""
        # Implementation to focus the widget, show its tab, etc.
        widget = get_id_registry().get_widget(widget_id)
        if widget:
            widget.setFocus()
```

This enables:
- Automatic focus restoration during undo/redo
- Navigation to the correct UI context
- Improved user experience with complex UIs

## Integration with UI Components

### Command-Enabled Widgets

The system provides command-enabled widgets that integrate with observables:

```python
from command_system.pyside6_widgets import CommandLineEdit

# Create a command-enabled line edit
line_edit = CommandLineEdit(container_id=container.widget_id)

# Bind to an observable property
line_edit.bind_to_text_property(person.get_id(), "name")
```

Key features:
- Automatic command generation for changes
- Synchronization with observable properties
- Built-in undo/redo support
- Configurable command trigger modes

### Property Binding

Bind widget properties to observable properties:

```python
# Create an observable model
person = Person()
person.name = "Alice"

# Create a command-enabled widget
line_edit = CommandLineEdit()

# Bind the widget to the observable property
line_edit.bind_property("text", person.get_id(), "name")

# Changes to the widget generate commands that update the model
# Changes to the model update the widget automatically
```

Benefits:
- Two-way data binding
- Automatic command generation
- Clean separation of UI and data
- Simplified undo/redo support

### Unbinding Properties

When a property binding is no longer needed, it should be properly unbound:

```python
# Unbind a property when it's no longer needed
line_edit.unbind_property("text")

# For convenience methods:
line_edit.unbind_text_property()
```

After unbinding:
- The widget no longer receives updates from the observable
- Changes to the widget no longer create commands to update the observable
- The observer is properly removed from the observable's internal tracking
- All references between the widget and observable are cleaned up

Proper unbinding is important to:
- Prevent memory leaks
- Avoid unexpected behavior
- Allow objects to be garbage collected
- Ensure widgets don't respond to observables they shouldn't

### Custom Command Triggering

Configure when commands are generated:

```python
from command_system.pyside6_widgets import CommandTriggerMode

# Configure when commands are triggered
line_edit.set_command_trigger_mode(CommandTriggerMode.IMMEDIATE)  # On every change
line_edit.set_command_trigger_mode(CommandTriggerMode.DELAYED, 500)  # After 500ms delay
line_edit.set_command_trigger_mode(CommandTriggerMode.ON_EDIT_FINISHED)  # When editing is done
```

This allows:
- Fine-grained control over command generation
- Batching rapid changes into a single command
- Appropriate command timing for different input types

### Widget Serialization

Command-enabled widgets support serialization:

```python
# Save widget state
serialized_state = line_edit.get_serialization()

# Restore widget state
line_edit.deserialize(serialized_state)
```

The serialized state includes:
- Widget ID
- Bound property relationships
- Current values
- Widget-specific configuration

Deserialization restores both the widget state and re-establishes binding relationships with observables. If a widget had property bindings before serialization, those bindings will be recreated during deserialization.

## Common Patterns and Examples

### Form Data Binding

Create a form with multiple fields bound to a data model:

```python
# Create data model
class PersonModel(Observable):
    name = ObservableProperty("")
    email = ObservableProperty("")
    age = ObservableProperty(0)
    
    def __init__(self):
        super().__init__()

# Create model instance
person = PersonModel()

# Create form fields
name_edit = CommandLineEdit()
email_edit = CommandLineEdit()
age_spinner = CommandSpinBox()

# Bind fields to model
name_edit.bind_property("text", person.get_id(), "name")
email_edit.bind_property("text", person.get_id(), "email")
age_spinner.bind_property("value", person.get_id(), "age")

# Don't forget to unbind when the form is closed
def on_form_close():
    name_edit.unbind_property("text")
    email_edit.unbind_property("text")
    age_spinner.unbind_property("value")
```

### Multi-step Operations

Create a complex operation with multiple steps:

```python
# Create a macro for a multi-step operation
macro = MacroCommand("Create New Document")

# Add component commands
macro.add_command(CreateDocumentCommand(doc_id))
macro.add_command(PropertyCommand(title_property_id, "New Document"))
macro.add_command(PropertyCommand(author_property_id, "User"))
macro.add_command(PropertyCommand(created_date_property_id, datetime.now()))

# Execute the macro as a single operation
manager.execute(macro)
```

### Undo/Redo Stack Management

Add custom UI for undo/redo functionality:

```python
class MyApplication:
    def setup_undo_redo(self):
        # Create undo/redo actions
        self.undo_action = QAction("Undo", self)
        self.redo_action = QAction("Redo", self)
        
        # Connect to undo/redo functionality
        self.undo_action.triggered.connect(self.undo)
        self.redo_action.triggered.connect(self.redo)
        
        # Update action state when command history changes
        manager = get_command_manager()
        manager.add_after_execute_callback("ui_update", self.update_actions)
        manager.add_after_undo_callback("ui_update", self.update_actions)
        
    def update_actions(self, command, success):
        manager = get_command_manager()
        self.undo_action.setEnabled(manager.can_undo())
        self.redo_action.setEnabled(manager.can_redo())
        
    def undo(self):
        manager = get_command_manager()
        manager.undo()
        
    def redo(self):
        manager = get_command_manager()
        manager.redo()
```

### Component State Persistence

Save and restore application state using serialization:

```python
def save_application_state(filename):
    # Collect all model data
    models = collect_all_models()
    serialized_models = {}
    
    for model_id, model in models.items():
        serialized_models[model_id] = model.serialize()
    
    # Collect UI state
    ui_components = collect_ui_components()
    serialized_ui = {}
    
    for component_id, component in ui_components.items():
        if hasattr(component, 'get_serialization'):
            serialized_ui[component_id] = component.get_serialization()
    
    # Save to file
    with open(filename, 'w') as f:
        json.dump({
            'models': serialized_models,
            'ui': serialized_ui
        }, f)

def restore_application_state(filename):
    # Load from file
    with open(filename, 'r') as f:
        data = json.load(f)
    
    # Begin initialization mode to prevent command history
    manager = get_command_manager()
    manager.begin_init()
    
    try:
        # Restore models
        for model_id, model_data in data['models'].items():
            model = get_id_registry().get_observable(model_id)
            if model:
                model.deserialize(model_data)
        
        # Restore UI components
        for component_id, component_data in data['ui'].items():
            component = get_id_registry().get_widget(component_id)
            if component and hasattr(component, 'deserialize'):
                component.deserialize(component_data)
    finally:
        # End initialization mode
        manager.end_init()
```

## Best Practices

1. **Use IDs, not direct references**
   - Store IDs instead of direct object references in commands
   - Use the ID system for lookup and relationship management
   - This prevents memory leaks and circular references

2. **Keep commands small and focused**
   - Each command should do one specific thing
   - Use compound/macro commands for complex operations
   - This improves granularity of undo/redo and simplifies debugging

3. **Bind UI to observables**
   - Use property binding instead of manual updates
   - Create command-enabled widgets for automatic command generation
   - This ensures UI and data stay synchronized with undo/redo support

4. **Manage observer lifecycle**
   - Always store observer IDs returned from add_property_observer
   - Always unbind properties when widgets are no longer needed
   - Use unregister_widget() for comprehensive cleanup
   - This prevents memory leaks and unexpected behavior

5. **Preserve context information**
   - Use `set_trigger_widget` to track command sources
   - Use `set_context_info` to store navigation context
   - This improves user experience during undo/redo operations

6. **Use initialization mode properly**
   - Use `begin_init`/`end_init` during application startup
   - Don't add setup operations to undo history
   - This keeps undo/redo history focused on user operations

7. **Serialize with IDs**
   - Serialize using IDs rather than direct references
   - Restore with the same IDs for proper relationship recovery
   - This enables robust serialization of complex object graphs

## Troubleshooting

### Common Issues

1. **Widget continues updating after unbinding**
   - Ensure you're calling the correct unbind method (e.g., `unbind_property("text")`)
   - Make sure you're storing the observer ID returned from add_property_observer
   - Check if you have multiple bindings to the same property

2. **Command not executing**
   - Check if `is_updating` flag is preventing execution
   - Ensure command is properly created with correct IDs
   - Verify the command manager is not in initialization mode

3. **Observer not receiving notifications**
   - Check if observer is properly registered
   - Verify property exists on the observable
   - Ensure property changes are happening through the property attribute, not direct variable access

4. **UI not updating after undo/redo**
   - Check if widget is properly bound to observable
   - Verify observable property changes are triggering notifications
   - Check for signal blocking or recursive update prevention

5. **ID-related errors**
   - Ensure components are properly registered with the ID system
   - Check for mismatched or invalid IDs
   - Verify ID references point to existing components

6. **Memory leaks**
   - Check for missing calls to unbind_property()
   - Ensure observers are properly removed
   - Verify unregister_widget() is called when widgets are deleted

### Debugging Techniques

1. **Command History Inspection**
   ```python
   manager = get_command_manager()
   executed_commands = manager._history.get_executed_commands()
   for cmd in executed_commands:
       print(f"Command: {cmd.__class__.__name__}")
   ```

2. **Observable Tracing**
   ```python
   def trace_property(property_name, old_value, new_value):
       print(f"Property {property_name} changed: {old_value} -> {new_value}")
       
   observer_id = observable.add_property_observer("property_name", trace_property)
   # Don't forget to remove the observer when done
   observable.remove_property_observer("property_name", observer_id)
   ```

3. **ID Registry Inspection**
   ```python
   registry = get_id_registry()
   print(f"Observable ID: {registry.get_id(observable)}")
   print(f"Property IDs: {registry.get_observable_properties(observable_id)}")
   print(f"Controller properties: {registry.get_controller_properties(widget_id)}")
   ```

4. **Widget Binding Inspection**
   ```python
   # Check which properties are bound to a widget
   print(f"Controlled properties: {widget._controlled_properties}")
   ```

## API Reference

### Observable Classes

#### Observable

Base class for objects that need to track property changes.

**Methods:**
- `__init__()`: Initialize observable and register with ID system
- `get_id() -> str`: Get the ID for this observable
- `add_property_observer(property_name, callback, observer_obj=None) -> str`: Add observer for property changes
- `remove_property_observer(property_name, observer_id) -> bool`: Remove property observer
- `_get_property_id(property_name) -> str`: Get ID for a property
- `serialize_property(property_name) -> dict`: Serialize a property to a dictionary
- `deserialize_property(property_name, data) -> bool`: Deserialize property data
- `serialize() -> dict`: Serialize the entire observable
- `deserialize(data) -> bool`: Deserialize observable data
- `unregister_property(property_name) -> bool`: Unregister a property
- `unregister() -> bool`: Unregister this observable

#### ObservableProperty

Descriptor for observable properties that notifies observers when changed.

**Methods:**
- `__init__(default=None)`: Initialize with optional default value
- `__get__(instance, owner)`: Get property value
- `__set__(instance, value)`: Set property value and notify observers

### Command Classes

#### Command

Abstract base class for all commands.

**Methods:**
- `__init__()`: Initialize command
- `execute()`: Execute the command (abstract)
- `undo()`: Undo the command (abstract)
- `redo()`: Redo the command (default implementation calls execute)
- `set_trigger_widget(widget_id)`: Set the widget that triggered this command
- `get_trigger_widget()`: Get the widget that triggered this command
- `set_context_info(key, value)`: Store context information
- `get_context_info(key, default=None)`: Get stored context information

#### PropertyCommand

Command for changing a property on an observable object.

**Methods:**
- `__init__(property_id, new_value)`: Initialize with property ID and new value
- `execute()`: Set the new property value
- `undo()`: Restore the old property value

#### WidgetPropertyCommand

Command for changing a property on a widget.

**Methods:**
- `__init__(widget_id, property_name, new_value)`: Initialize with widget ID, property name, and new value
- `execute()`: Set the new property value
- `undo()`: Restore the old property value

#### CompoundCommand

A command that groups multiple commands together.

**Methods:**
- `__init__(name="Compound Command")`: Initialize with optional name
- `add_command(command)`: Add a command to the compound
- `execute()`: Execute all commands in order
- `undo()`: Undo all commands in reverse order
- `is_empty() -> bool`: Check if compound command is empty

#### MacroCommand

A specialized compound command that represents a user-level action.

**Methods:**
- `__init__(name)`: Initialize with descriptive name
- `set_description(description)`: Set a human-readable description
- `get_description() -> str`: Get the description

#### SerializationCommand

Command for handling serialization of components/containers.

**Methods:**
- `__init__(component_id=None, type_id=None, container_id=None)`: Initialize with component info
- `get_serialization() -> bool`: Get serialization from component
- `deserialize() -> bool`: Deserialize state to component
- `serialize_subcontainer() -> bool`: Get serialization from container's subcontainer
- `deserialize_subcontainer() -> bool`: Deserialize subcontainer state back to container

### BaseCommandWidget Class

Base class for command-enabled widgets.

**Methods:**
- `initiate_widget(type_code, container_id=None, location=None)`: Initialize widget
- `bind_property(widget_property, observable_id, property_name)`: Bind widget property to observable
- `unbind_property(widget_property)`: Unbind widget property
- `set_command_trigger_mode(mode, delay_ms=300)`: Configure when commands are generated
- `update_container(new_container_id)`: Update widget's container
- `unregister_widget() -> bool`: Unregister widget and clean up resources
- `get_serialization() -> dict`: Get serialized widget state
- `deserialize(data) -> bool`: Restore widget state from serialization

### Command Manager Classes

#### CommandHistory

Tracks command history for undo/redo operations.

**Methods:**
- `__init__()`: Initialize empty command history
- `add_command(command)`: Add a command to the history
- `undo() -> Command`: Undo the most recent command
- `redo() -> Command`: Redo the most recently undone command
- `clear()`: Clear both command stacks
- `can_undo() -> bool`: Check if there are commands that can be undone
- `can_redo() -> bool`: Check if there are commands that can be redone
- `get_executed_commands() -> list`: Get list of executed commands
- `get_undone_commands() -> list`: Get list of undone commands

#### CommandManager

Singleton manager for command execution and history tracking.

**Methods:**
- `get_instance() -> CommandManager`: Get the singleton instance
- `execute(command, trigger_widget_id=None) -> bool`: Execute a command
- `undo() -> bool`: Undo the most recent command
- `redo() -> bool`: Redo the most recently undone command
- `clear()`: Clear command history
- `can_undo() -> bool`: Check if undo is available
- `can_redo() -> bool`: Check if redo is available
- `is_updating() -> bool`: Check if a command is being processed
- `begin_init()`: Begin initialization mode
- `end_init()`: End initialization mode
- `add_before_execute_callback(callback_id, callback)`: Add callback before execution
- `add_after_execute_callback(callback_id, callback)`: Add callback after execution
- `add_before_undo_callback(callback_id, callback)`: Add callback before undo
- `add_after_undo_callback(callback_id, callback)`: Add callback after undo
- `remove_callback(callback_id)`: Remove a callback

**Global Function:**
- `get_command_manager() -> CommandManager`: Get the singleton command manager instance

## Conclusion

The Command System provides a powerful foundation for building applications with rich undo/redo functionality, property change tracking, and UI integration. By combining the Observable pattern with the Command pattern and leveraging the ID system for relationship management, it enables sophisticated application architectures with minimal boilerplate code.

Key advantages of the system include:

1. **Clean Separation of Concerns**
   - UI components remain decoupled from data models
   - Commands encapsulate all the logic for performing and undoing actions
   - Observables handle property change notification independently

2. **Comprehensive Undo/Redo**
   - Automatic tracking of property changes
   - Command composition for complex operations
   - Consistent undo/redo behavior across the application

3. **Robust Resource Management**
   - Systematic tracking of component relationships
   - Clear lifecycle for observers and bindings
   - Proper cleanup to prevent memory leaks

4. **Flexible UI Integration**
   - Command-enabled widgets with automatic binding
   - Configurable command generation timing
   - Built-in support for serialization and restoration

By following the patterns and best practices described in this document, developers can create applications that are more maintainable, feature-rich, and user-friendly.