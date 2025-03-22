# PySignalDecipher Command System - User Guide

This guide provides a comprehensive overview of how to use the PySignalDecipher command system in your applications. It covers the core components, their relationships, and practical usage examples.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Core Command System](#core-command-system)
3. [Observable Properties](#observable-properties)
4. [Command Management](#command-management)
5. [UI Integration](#ui-integration)
6. [Dock Management](#dock-management)
7. [Layout Management](#layout-management)
8. [Project Serialization](#project-serialization)
9. [Integrating All Components](#integrating-all-components)
10. [Best Practices](#best-practices)

## System Architecture

The PySignalDecipher command system is designed with a modular architecture that separates concerns while providing seamless integration between components:

### Core Components and Their Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer                             │
│                                                             │
│  ┌─────────────────┐   ┌────────────────┐   ┌────────────┐  │
│  │  Command Widgets │───│  Dock Widgets  │───│  Layouts   │  │
│  └─────────────────┘   └────────────────┘   └────────────┘  │
└──────────────┬────────────────┬───────────────┬─────────────┘
               │                │               │
               ▼                ▼               ▼
┌─────────────────┐   ┌────────────────┐   ┌────────────────┐
│ CommandManager  │───│  DockManager   │───│ LayoutManager  │
└─────────────────┘   └────────────────┘   └────────────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐   ┌────────────────┐   ┌────────────────┐
│    Commands     │   │   Observable   │───│ ProjectManager │
└─────────────────┘   └────────────────┘   └────────────────┘
                               │                    │
                               │                    │
                               ▼                    ▼
                      ┌────────────────┐   ┌────────────────┐
                      │ObservableProps │   │ Serialization  │
                      └────────────────┘   └────────────────┘
```

The system consists of several interconnected components that work together:

1. **Core Command System**: Command pattern implementation for undo/redo
2. **Observable System**: Property change notification system 
3. **UI Integration**: Widgets that automatically create commands
4. **Dock Management**: Management of dock widgets with undo/redo support
5. **Layout Management**: Saving and restoring UI configurations
6. **Project Serialization**: Saving and loading application state

Each component can be used independently, but they are designed to work together seamlessly.

## Core Command System

The command system implements the Command pattern to encapsulate actions that can be executed, undone, and redone.

### Command Base Class

```python
from command_system import Command

class MyCommand(Command):
    def __init__(self, data, new_value):
        self.data = data
        self.new_value = new_value
        self.old_value = data.value
        
    def execute(self):
        """Execute the command."""
        self.data.value = self.new_value
        
    def undo(self):
        """Undo the command."""
        self.data.value = self.old_value
```

### CompoundCommand

Group multiple commands together to be executed and undone as a unit:

```python
from command_system import CompoundCommand

# Create compound command
compound = CompoundCommand("Complex Operation")

# Add child commands
compound.add_command(Command1(...))
compound.add_command(Command2(...))

# Execute entire group
cmd_manager.execute(compound)
```

### PropertyCommand

A specialized command for changing properties:

```python
from command_system import PropertyCommand

# Create command to change a property
cmd = PropertyCommand(model, "name", "New Name")

# Execute the command
cmd_manager.execute(cmd)
```

## Observable Properties

The Observable pattern enables objects to notify observers when their properties change.

### Creating Observable Models

```python
from command_system import Observable, ObservableProperty

class PersonModel(Observable):
    name = ObservableProperty[str](default="")
    age = ObservableProperty[int](default=0)
    is_active = ObservableProperty[bool](default=True)
    
    def __init__(self):
        super().__init__()
```

### Using Observable Properties

```python
# Create a model
person = PersonModel()

# Get property values
print(person.name)  # ""

# Set property values (triggers notifications)
person.name = "John"
person.age = 30
```

### Observing Property Changes

```python
# Define a change handler
def on_name_changed(property_name, old_value, new_value):
    print(f"Name changed from '{old_value}' to '{new_value}'")

# Register the observer
observer_id = person.add_property_observer("name", on_name_changed)

# Later, remove the observer if needed
person.remove_property_observer("name", observer_id)
```

## Command Management

The CommandManager handles the execution of commands and maintains the undo/redo history.

### Accessing the Command Manager

```python
from command_system import get_command_manager

# Get the singleton command manager instance
cmd_manager = get_command_manager()
```

### Executing Commands

```python
# Create a command
cmd = MyCommand(data, new_value)

# Execute it (automatically adds to undo stack)
cmd_manager.execute(cmd)
```

### Undo/Redo Operations

```python
# Check if operations are available
can_undo = cmd_manager.can_undo()
can_redo = cmd_manager.can_redo()

# Perform operations
if can_undo:
    cmd_manager.undo()
    
if can_redo:
    cmd_manager.redo()
```

### Initialization Mode

During initialization, you may want to execute commands without adding them to the history:

```python
# Begin initialization mode
cmd_manager.begin_init()

# Setup operations (not added to history)
cmd_manager.execute(cmd1)
cmd_manager.execute(cmd2)

# End initialization mode
cmd_manager.end_init()
```

## UI Integration

The UI integration layer connects the command system with UI widgets, automatically creating commands for widget changes.

### Command-Aware Widgets

```python
from command_system.ui.widgets import (
    CommandLineEdit, CommandSpinBox, CommandCheckBox
)

# Create widgets
name_edit = CommandLineEdit()
age_spin = CommandSpinBox()
active_check = CommandCheckBox("Active")

# Bind to model properties
name_edit.bind_to_model(model, "name")
age_spin.bind_to_model(model, "age")
active_check.bind_to_model(model, "is_active")
```

### Available Command Widgets

- `CommandLineEdit`: Text input
- `CommandTextEdit`: Multi-line text
- `CommandSpinBox`: Integer values
- `CommandDoubleSpinBox`: Float values  
- `CommandComboBox`: Selection from list
- `CommandCheckBox`: Boolean values
- `CommandSlider`: Adjustable numeric values
- `CommandDateEdit`: Date selection

### Manual Property Binding

If you need more control over binding, you can use the PropertyBinder directly:

```python
from command_system.ui import PropertyBinder

# Create a binder
binder = PropertyBinder()

# Bind properties to widgets
binding_id = binder.bind(model, "name", line_edit, "text")

# Later, unbind if needed
binder.unbind(binding_id)
```

## Dock Management

The dock management system provides undo/redo support for dock-related operations.

### Creating Command-Aware Docks

```python
from command_system.ui.dock import (
    get_dock_manager, CommandDockWidget, CreateDockCommand
)

# Get the dock manager
dock_manager = get_dock_manager()
dock_manager.set_main_window(main_window)

# Create a command-aware dock widget
dock = CommandDockWidget("dock_id", "My Dock", main_window)
dock.setWidget(content_widget)

# Add the dock using a command
cmd = CreateDockCommand("dock_id", dock, None, Qt.RightDockWidgetArea)
cmd_manager.execute(cmd)
```

### Observable Dock Widgets

Docks with their own observable models:

```python
from command_system.ui.dock import ObservableDockWidget

# Create a model for the dock
model = NoteModel()

# Create dock with associated model
dock = ObservableDockWidget("dock_id", "Note", main_window, model)
```

### Dock Commands

```python
from command_system.ui.dock import (
    CreateDockCommand, DeleteDockCommand, DockLocationCommand
)

# Create a dock
cmd = CreateDockCommand("dock_id", dock, parent_id, area)
cmd_manager.execute(cmd)

# Delete a dock
cmd = DeleteDockCommand("dock_id")
cmd_manager.execute(cmd)

# Change dock location
cmd = DockLocationCommand("dock_id")
cmd_manager.execute(cmd)
```

## Layout Management

The layout management system allows saving and restoring UI layouts.

### Setting Up Layout Manager

```python
from command_system.layout import get_layout_manager

# Get the layout manager
layout_manager = get_layout_manager()
layout_manager.set_main_window(main_window)

# Set a directory for storing layout presets
layout_manager.set_layouts_directory("./layouts")
```

### Registering Widgets

```python
# Register widgets to include in layouts
layout_manager.register_widget("main_splitter", main_splitter)
layout_manager.register_widget("content_splitter", content_splitter)
layout_manager.register_widget("text_editor", text_editor)
```

### Widget Factories

To recreate widgets that might not exist when loading layouts:

```python
def create_dock_widget():
    """Factory function to create a new dock widget."""
    dock = CommandDockWidget("new_dock", "New Dock", main_window)
    # Configure the dock...
    return dock

# Register factory
layout_manager.register_widget_factory("CommandDockWidget", create_dock_widget)
```

### Saving and Loading Layouts

```python
# Save the current layout as a preset
layout_manager.save_layout_preset("default_layout")

# Load a saved layout
layout_manager.load_layout_preset("default_layout")

# Get available layouts
presets = layout_manager.get_available_presets()
```

## Project Serialization

The serialization system handles saving and loading of application state.

### Setting Up Project Manager

```python
from command_system import get_project_manager

# Get the project manager
project_manager = get_project_manager()

# Register model factories for creating instances when loading
project_manager.register_model_type("note", lambda: NoteModel())
project_manager.register_model_type("person", lambda: PersonModel())
```

### Saving Projects

```python
# Save to a file
success = project_manager.save_project(model, "myproject.json")

# Save with specific format
success = project_manager.save_project(
    model, 
    "myproject.bin", 
    format_type=ProjectSerializer.FORMAT_BINARY
)
```

### Loading Projects

```python
# Load from a file
model = project_manager.load_project("myproject.json")

# Check if loading succeeded
if model is not None:
    # Update UI with loaded model
```

### Saving Layouts with Projects

```python
# Enable layout saving with projects
project_manager.set_save_layouts(True)

# Save project with layout
project_manager.save_project(model, filename, save_layout=True)

# Load project with layout
model = project_manager.load_project(filename, load_layout=True)
```

### File Formats

```python
from command_system import ProjectSerializer

# Set the default format
project_manager.set_default_format(ProjectSerializer.FORMAT_JSON)

# Get file extension for current format
extension = project_manager.get_default_extension()
```

## Integrating All Components

Here's how to integrate all components in a complete application:

```python
from PySide6.QtWidgets import QApplication, QMainWindow
from command_system import (
    get_command_manager, get_project_manager, Observable, ObservableProperty
)
from command_system.layout import get_layout_manager, extend_project_manager
from command_system.ui.dock import get_dock_manager
from command_system.ui.widgets import CommandLineEdit, CommandTextEdit

# Define model
class DocumentModel(Observable):
    title = ObservableProperty[str](default="Untitled")
    content = ObservableProperty[str](default="")

# Application initialization
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Get managers
        self.cmd_manager = get_command_manager()
        self.project_manager = get_project_manager()
        self.layout_manager = get_layout_manager()
        self.dock_manager = get_dock_manager()
        
        # Set main window references
        self.layout_manager.set_main_window(self)
        self.dock_manager.set_main_window(self)
        
        # Register model types
        self.project_manager.register_model_type("document", lambda: DocumentModel())
        
        # Enable layout saving with projects
        project_manager.set_save_layouts(True)
        
        # Begin initialization (disable command tracking)
        self.cmd_manager.begin_init()
        
        # Create model
        self.model = DocumentModel()
        
        # Set up UI
        self._create_ui()
        
        # Register widgets with layout manager
        self._register_layout_widgets()
        
        # End initialization (enable command tracking)
        self.cmd_manager.end_init()
        
    def _create_ui(self):
        # Create UI components and bind to model
        self.title_edit = CommandLineEdit()
        self.title_edit.bind_to_model(self.model, "title")
        
        self.content_edit = CommandTextEdit()
        self.content_edit.bind_to_model(self.model, "content")
        
        # Create and add docks...
        
    def _register_layout_widgets(self):
        self.layout_manager.register_widget("main_splitter", self.main_splitter)
        # Register other widgets...
        
    def save_project(self, filename):
        return self.project_manager.save_project(self.model, filename)
        
    def load_project(self, filename):
        model = self.project_manager.load_project(filename)
        if model:
            self.model = model
            self._update_bindings()
            return True
        return False
        
    def _update_bindings(self):
        # Rebind widgets to the new model
        self.title_edit.bind_to_model(self.model, "title")
        self.content_edit.bind_to_model(self.model, "content")
        # Update other bindings...

# Initialize application
app = QApplication([])
extend_project_manager()  # Integrate layout system with project manager
window = MainWindow()
window.show()
app.exec()
```

## Best Practices

### Command Design

1. **Keep commands focused**: Each command should do one logical operation
2. **Store state for undo**: Capture all needed data in the command constructor
3. **Use CompoundCommand** for complex operations

### Observable Models

1. **Distinct properties**: Avoid redundant properties
2. **Use type hints**: Provide type hints for better IDE support
3. **Avoid circular updates**: Be careful with property observers that modify other properties

### UI Integration

1. **Prefer command widgets**: Use command-aware widgets when possible
2. **Bind early**: Bind widgets to models right after creation
3. **Update bindings on model change**: Rebind widgets when loading a new model

### Layout Management

1. **Register all important widgets**: Register any widget that users might want to resize/position
2. **Use unique IDs**: Give widgets meaningful, unique object names
3. **Register factories**: Provide factories for recreating widgets during layout loading

### Project Serialization

1. **Register model types**: Register factories for all model types you'll save/load
2. **Match IDs**: Use the same IDs for models and their corresponding widgets
3. **Test serialization**: Verify serialization works with complex nested models

### Error Handling

1. **Validate in execute()**: Check preconditions before making changes
2. **Robust undo()**: Make undo work even if execute partially failed
3. **Report errors**: Return false from execute/undo on failure

### Performance

1. **Batch commands**: Use compound commands for bulk operations
2. **Lazy property updates**: Only update UI when property actually changes
3. **Consider memory usage**: Be cautious with large history stacks