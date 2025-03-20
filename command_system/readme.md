# PySignalDecipher Command System

A lightweight, flexible command pattern implementation for building applications with robust undo/redo functionality.

## Overview

The PySignalDecipher Command System provides a clean implementation of the Command Pattern, integrated with an Observable pattern for property tracking and UI binding capabilities. This system allows for:

- Tracking user actions as commands
- Maintaining a history stack for undo/redo operations
- Binding UI controls to model properties
- Managing dock widgets with undo/redo support
- Serializing application state

## Core Concepts

### Command Pattern

The command pattern encapsulates actions as objects that can be executed, undone, and redone. This system provides:

- `Command`: Abstract base class for all commands
- `CompoundCommand`: Groups multiple commands into a single undoable unit
- `PropertyCommand`: Specialized command for property changes

### Observable Pattern

The observable pattern enables properties to notify observers when they change:

- `Observable`: Base class for objects that need to track property changes
- `ObservableProperty`: Descriptor for properties that notify observers when changed

### Command Management

The command system uses a command manager to track history:

- `CommandManager`: Singleton that manages command execution and maintains history
- `CommandHistory`: Tracks executed and undone commands

### Dock Management

The dock management system provides undo/redo support for dock operations:

- `DockManager`: Manages dock widgets and their state
- Dock-specific commands like `CreateDockCommand` and `DeleteDockCommand`
- `CommandDockWidget`: Command-aware dock widget

### UI Integration

The system provides tight integration with UI frameworks:

- `PropertyBinder`: Manages bindings between model properties and UI widgets
- Command-aware widgets that automatically create commands when modified

## Quick Start

### Basic Command

```python
from command_system import Command, get_command_manager

# Create a simple command
class AddTextCommand(Command):
    def __init__(self, text_buffer, text_to_add):
        self.buffer = text_buffer
        self.text_to_add = text_to_add
        self.position = len(self.buffer)
        
    def execute(self):
        self.buffer.insert(self.position, self.text_to_add)
        
    def undo(self):
        self.buffer.remove(self.position, self.position + len(self.text_to_add))

# Use the command
cmd_manager = get_command_manager()
text_buffer = []
cmd = AddTextCommand(text_buffer, "Hello World")
cmd_manager.execute(cmd)
```

### Observable Model

```python
from command_system import Observable, ObservableProperty

class NoteModel(Observable):
    title = ObservableProperty[str](default="Untitled")
    content = ObservableProperty[str](default="")
    
    def __init__(self):
        super().__init__()
        
# Create and use a model
note = NoteModel()
note.title = "My First Note"  # This will notify observers
```

### Initialization Mode

To prevent commands executed during initialization from being added to the undo history:

```python
# In your window's __init__ method
def __init__(self):
    super().__init__()
    
    # Get command manager
    self.cmd_manager = get_command_manager()
    
    # Begin initialization mode (commands execute but aren't added to history)
    self.cmd_manager.begin_init()
    
    # Set up initial UI state, create default widgets, etc.
    self._setup_initial_state()
    
    # End initialization mode (commands are now tracked in history)
    self.cmd_manager.end_init()
```

## Example Implementations

The command system includes demonstration applications that showcase its capabilities:

### Widgets Demo

The `widgets_demo.py` file demonstrates how to use command-aware widgets with an observable model to automatically create commands for UI interactions.

Key features demonstrated:

- Creating a model with observable properties
- Using command-aware widgets like `CommandLineEdit`, `CommandSpinBox`, etc.
- Binding widgets to model properties
- Automatic undo/redo capability

Example from the demo:

```python
# Create model with observable properties
class DemoModel(Observable):
    name = ObservableProperty[str](default="John Doe")
    count = ObservableProperty[int](default=0)
    is_active = ObservableProperty[bool](default=True)

# Bind widgets to model properties
self.name_edit = CommandLineEdit()
self.name_edit.bind_to_model(self.model, "name")

self.count_spin = CommandSpinBox()
self.count_spin.bind_to_model(self.model, "count")

self.active_check = CommandCheckBox()
self.active_check.bind_to_model(self.model, "is_active")
```

### File Menu Demo

The `file_menu_demo.py` file shows how to implement save/load functionality with the command system, including:

- Project serialization/deserialization
- File format selection
- Checking for unsaved changes
- Updating window titles to reflect modification state

Example from the demo:

```python
# Register model factory
self.project_manager.register_model_type("note", lambda: NoteModel())

# Save project
if self.project_manager.save_project(self.model, filename):
    # Update window title
    self._update_window_title()

# Load project
model = self.project_manager.load_project(filename)
if model is not None:
    # Update model
    self.model = model
    
    # Rebind widgets to new model
    self.title_edit.bind_to_model(self.model, "title")
```

### Docks Demo

The `docks_demo.py` file demonstrates the dock management system with undo/redo support:

- Creating and managing dock widgets
- Tracking dock states for undo/redo
- Parent-child relationships between docks
- Using the dock manager with the command system

Example from the demo:

```python
# Create a new dock
dock_id = "new_dock"
dock = CommandDockWidget(dock_id, "Text Editor", self)
dock.closeRequested.connect(self._on_dock_close_requested)

# Create and execute command to add dock (undoable)
cmd = CreateDockCommand(dock_id, dock, None, Qt.RightDockWidgetArea)
self.cmd_manager.execute(cmd)

# Later, to close the dock with undo support
def _on_dock_close_requested(self, dock_id):
    # Create and execute command to delete dock
    cmd = DeleteDockCommand(dock_id)
    self.cmd_manager.execute(cmd)
```

## Using Command-Aware Widgets

The system includes a set of command-aware widgets that automatically create undo/redo commands when their values change:

### Available Widgets

- `CommandLineEdit`: For text entry
- `CommandSpinBox`: For integer values
- `CommandDoubleSpinBox`: For floating-point values  
- `CommandComboBox`: For selection from a list
- `CommandCheckBox`: For boolean values
- `CommandSlider`: For adjustable numeric values
- `CommandDateEdit`: For date selection
- `CommandTextEdit`: For multi-line text entry

### Binding to Models

To bind a widget to a model property:

```python
text_edit = CommandTextEdit()
text_edit.bind_to_model(my_model, "content")
```

The widget will now:
1. Display the current value of the property
2. Update automatically when the property changes
3. Create undo/redo commands when the user modifies the value

## Dock Management System

The dock management system provides undo/redo support for dock-related operations:

### Dock Manager

The `DockManager` class manages dock widgets and their state:

```python
# Get the dock manager
dock_manager = get_dock_manager()

# Set the main window
dock_manager.set_main_window(self)

# Register a dock
dock_manager.register_dock("my_dock", dock_widget)

# Save the current dock layout
layout = dock_manager.serialize_layout()
```

### Command-Aware Dock Widgets

The system provides command-aware dock widgets:

```python
# Create a command-aware dock widget
dock = CommandDockWidget("my_dock", "My Dock", self)

# Connect the close signal
dock.closeRequested.connect(self._on_dock_close_requested)

# Observable dock widget with property binding
model = MyModel()
dock = ObservableDockWidget("my_dock", "My Dock", self, model)
```

### Dock Commands

Dock operations are encapsulated as commands:

```python
# Create a dock
cmd = CreateDockCommand("my_dock", dock_widget, None, Qt.RightDockWidgetArea)
cmd_manager.execute(cmd)

# Delete a dock
cmd = DeleteDockCommand("my_dock")
cmd_manager.execute(cmd)

# Change dock location
cmd = DockLocationCommand("my_dock")
cmd_manager.execute(cmd)
```

## Serialization

The command system includes serialization support for saving and loading application state:

```python
from command_system import get_project_manager

# Save a model
project_manager = get_project_manager()
project_manager.save_project(model, "my_document.json")

# Load a model
loaded_model = project_manager.load_project("my_document.json")
```

The system supports multiple formats including JSON, Binary, XML, and YAML.

## Best Practices

1. **Use initialization mode for setup operations**:
   ```python
   cmd_manager.begin_init()
   # Set up initial application state
   cmd_manager.end_init()
   ```

2. **Use CompoundCommand for complex operations**:
   ```python
   compound = CompoundCommand("Rename and Move")
   compound.add_command(RenameCommand(item, new_name))
   compound.add_command(MoveCommand(item, new_position))
   cmd_manager.execute(compound)
   ```

3. **Handle property changes with ObservableProperty**:
   ```python
   class MyModel(Observable):
       value = ObservableProperty[int](default=0)
       
   model = MyModel()
   model.add_property_observer("value", lambda prop, old, new: print(f"Changed: {old} -> {new}"))
   ```

4. **Register model factories for new projects**:
   ```python
   project_manager.register_model_type("document", lambda: DocumentModel())
   ```

5. **Check for unsaved changes**:
   ```python
   if cmd_manager.can_undo():
       # There are unsaved changes
       # Prompt user to save
   ```

## Architecture Benefits

- **Decoupled UI and model**: Changes can originate from either UI or code
- **Testable actions**: Commands can be unit tested independently
- **Consistent state management**: All state changes go through the command system
- **Simplified UI code**: Widget bindings reduce boilerplate code
- **Automatic undo/redo**: Most common operations get undo/redo for free
- **Clean initialization**: Prevent setup operations from polluting command history

## Integration with PySide/PyQt

The command system is designed to work seamlessly with Qt-based applications, providing Qt-specific bindings and command-aware widgets that maintain the familiar Qt API.