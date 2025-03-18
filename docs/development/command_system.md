# PySignalDecipher Command System Guide

This guide provides an overview of the Command System in PySignalDecipher, explaining how to use it effectively without needing to dive into the internals.

## What is the Command System?

The Command System is a central architecture component that provides:

1. **Undo/Redo functionality** - Track all changes and allow reverting or reapplying them
2. **Project serialization** - Save and restore project state
3. **State management** - Track application state in a consistent way
4. **UI integration** - Connect UI components to application state with automatic updates

## Core Concepts

### Commands

Commands encapsulate a single action or change within the application. All user actions that modify state should be implemented as commands.

**Key characteristics of commands:**
- Self-contained units that know how to execute and undo themselves
- Store all necessary state for undoing the operation
- Can be serialized for project saving/loading

### Command Manager

The CommandManager is the central coordinator that:
- Executes commands
- Maintains command history
- Provides access to application services
- Manages the active project

### Variables and Variable Registry

Variables represent application state that can be observed and changed:
- SignalVariables for values that need change notification
- ObservableProperties for object properties that should be undoable
- VariableRegistry for centralized variable management

### Workspaces

Workspaces are UI environments with specific layouts and tools:
- Each workspace has a unique ID
- Workspace state is tracked in the project
- Workspaces can contain dock widgets

## Common Tasks

### Getting the Command Manager

```python
# In most classes, you'll receive the command manager in the constructor
def __init__(self, command_manager):
    self._command_manager = command_manager
    
# If needed, you can get the singleton instance
from command_system.command_manager import CommandManager
command_manager = CommandManager.instance()
```

### Creating and Executing Commands

```python
# Simple example: Rename a signal
from command_system.commands import RenameSignalCommand

# Create the command
command = RenameSignalCommand(signal, "New Signal Name")

# Execute it through the command manager
command_manager.execute_command(command)
```

### Creating Custom Commands

1. Define a new command class that inherits from `Command`
2. Implement `execute()`, `undo()`, and serialization methods
3. Register it with the CommandFactory

```python
from command_system.command import Command

class MyCustomCommand(Command):
    def __init__(self, my_object, new_value):
        super().__init__()
        self.my_object = my_object
        self.new_value = new_value
        self.old_value = my_object.value
        
    def execute(self):
        self.my_object.value = self.new_value
        
    def undo(self):
        self.my_object.value = self.old_value
        
    def get_state(self):
        return {
            "object_id": self.my_object.id,
            "old_value": self.old_value,
            "new_value": self.new_value
        }
    
    @classmethod
    def from_state(cls, state):
        # Logic to recreate the command from saved state
        object_registry = get_object_registry()
        my_object = object_registry.get_object(state["object_id"])
        cmd = cls(my_object, state["new_value"])
        cmd.old_value = state["old_value"]
        return cmd

# Register the command
from command_system.command import CommandFactory
CommandFactory.register(MyCustomCommand)
```

### Working with Variables

Variables provide a way to track and observe values in the application.

#### Creating and Registering a Variable

```python
from command_system.observable import SignalVariable

# Create a variable (usually in a dock widget or component initialization)
self.frequency_var = SignalVariable("frequency", 100.0, self.dock_id)

# Register it with the variable registry
variable_registry = command_manager.get_variable_registry()
variable_registry.register_variable(self.frequency_var)
```

#### Subscribing to a Variable

```python
# Subscribe to changes
self.frequency_var.subscribe(
    subscriber_id=self.dock_id,  # Unique ID for this subscription
    callback=self._on_frequency_changed
)

def _on_frequency_changed(self, value):
    # Handle the new value
    self.frequency_display.setText(f"{value:.2f} Hz")
```

#### Changing a Variable Value

```python
# Direct change (doesn't go through command system - use only for non-undoable changes)
self.frequency_var.set_value(150.0)

# Change through the command system (preferred for user actions)
from command_system.observable import PropertyChangeCommand
command = PropertyChangeCommand(self.frequency_var, "value", 150.0)
command_manager.execute_command(command)
```

#### Cleaning Up Variables

```python
# When a component is deleted, clean up its variables
def closeEvent(self, event):
    # Unregister all variables associated with this component
    variable_registry = command_manager.get_variable_registry()
    variable_registry.unregister_parent(self.dock_id)
    
    # Continue with the close event
    super().closeEvent(event)
```

### Working with Docks

Dock widgets are managed through the workspace system.

#### Creating a Dock Widget

```python
# Create a dock programmatically
from command_system.commands.workspace_commands import CreateDockCommand

# Get the workspace state
project = command_manager.get_active_project()
workspace_state = project.get_workspace_state(workspace_id)

# Create the command
command = CreateDockCommand(workspace_state, "signal_viewer")
command_manager.execute_command(command)

# The dock ID is available in the command after execution
dock_id = command.dock_id
```

#### Removing a Dock Widget

```python
from command_system.commands.workspace_commands import RemoveDockCommand

# Create and execute the command
command = RemoveDockCommand(workspace_state, dock_id)
command_manager.execute_command(command)
```

### UI Integration

#### Connecting UI Elements to Commands

```python
from command_system.ui_integration import CommandConnector

# Connect a button to a command
CommandConnector.connect_button(
    self.rename_button,
    RenameSignalCommand,
    signal=self.signal,
    new_name="New Name"
)

# Connect a menu action to a command
CommandConnector.connect_action(
    self.rename_action,
    RenameSignalCommand,
    signal=self.signal,
    new_name="New Name"
)

# Connect a widget signal to update a property
CommandConnector.connect_property(
    self.frequency_spinner,  # Widget
    "valueChanged",  # Signal name
    self.signal,  # Target object
    "frequency"  # Property name
)
```

#### Creating UI Controls that Use Commands

```python
from command_system.ui_integration import CommandButton

# Create a button that executes a command when clicked
rename_button = CommandButton(
    RenameSignalCommand,
    "Rename",
    parent=self,
    signal=self.signal,
    new_name="New Name"
)

from command_system.ui_integration import PropertyLineEdit

# Create a line edit bound to a property
name_edit = PropertyLineEdit(
    target=self.signal, 
    property_name="name",
    parent=self
)
```

### Project Management

#### Getting the Active Project

```python
project = command_manager.get_active_project()
```

#### Accessing Project Data

```python
# Get a signal by ID
signal = project.get_signal(signal_id)

# Get all signals
signals = project.get_all_signals()

# Get workspace state
workspace_state = project.get_workspace_state(workspace_id)
```

#### Creating Project Elements

```python
# Create a new signal
from command_system.project import SignalData
from command_system.commands import AddSignalCommand

signal = SignalData("My Signal")
signal.set_data(data_array)

command = AddSignalCommand(project, signal)
command_manager.execute_command(command)
```

## Best Practices

1. **Always use commands for state changes**
   - Direct property assignments won't be undoable or saved
   - Exception: UI-only state that doesn't need to be persisted

2. **Design commands to be atomic**
   - Each command should do one logical thing
   - Use CompoundCommand for complex operations

3. **Properly handle parent-child relationships**
   - When registering variables, always specify the correct parent
   - When destroying components, unregister their variables

4. **Use meaningful IDs**
   - IDs should be unique and descriptive
   - IDs are used for serialization, so they should be consistent

5. **Avoid circular dependencies**
   - Don't create commands that depend on the result of their own execution
   - Use the CommandContext to access services instead of direct references

6. **Clean up when components are destroyed**
   - Unsubscribe from variables
   - Unregister variables from the registry
   - Remove component references from other components

## Troubleshooting

### Common Issues

#### Changes Not Being Saved
- Make sure you're using commands instead of direct property assignments
- Verify the command is being executed through the command manager

#### Changes Not Appearing in UI
- Check that you've subscribed to the relevant variables
- Ensure the subscription callback is updating the UI correctly

#### Undo/Redo Not Working Correctly
- Verify the command's undo method properly restores the previous state
- Make sure all state is captured in the command when it's created

#### UI Components Not Updating
- Check that variables are being registered with the variable registry
- Verify subscriptions are set up correctly with the right subscriber IDs

### Debugging Tips

1. **Command Execution**
   - Connect to the command_manager's signals to log command execution
   - `command_manager.command_executed.connect(log_command)`

2. **Variable Changes**
   - Add debug callbacks to important variables
   - `variable.subscribe("debug", lambda v: print(f"Value changed to {v}"))`

3. **Component Lifecycle**
   - Add debug prints to closeEvent or destructor methods
   - Verify that cleanup is happening correctly

## Advanced Topics

### Command Context

Commands can access services and contextual information through the CommandContext:

```python
def execute(self):
    # Get a service from the context
    layout_manager = self.get_service(LayoutManager)
    
    # Access the active project
    project = self.context.active_project
    
    # Get context parameters
    parameter = self.context.get_parameter("key", default_value)
```

### Compound Commands

For operations that involve multiple steps:

```python
from command_system.command import CompoundCommand

# Create a compound command
compound = CompoundCommand("Complex Operation")

# Add individual commands
compound.add_command(Command1(...))
compound.add_command(Command2(...))
compound.add_command(Command3(...))

# Execute the compound command
command_manager.execute_command(compound)
```

### Custom Serialization

For commands that involve complex objects:

```python
def get_state(self):
    return {
        "complex_object": self._serialize_complex_object(self.my_object),
        "other_data": self.other_data
    }

def _serialize_complex_object(self, obj):
    # Custom serialization logic
    return {
        "id": obj.id,
        "properties": obj.get_serializable_properties()
    }

@classmethod
def from_state(cls, state):
    # Custom deserialization logic
    complex_obj = cls._deserialize_complex_object(state["complex_object"])
    return cls(complex_obj, state["other_data"])

@classmethod
def _deserialize_complex_object(cls, data):
    # Find or create the object
    obj = get_object_by_id(data["id"])
    if obj:
        obj.restore_properties(data["properties"])
    return obj
```