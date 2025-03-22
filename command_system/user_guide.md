# Command System User Guide

This guide explains how to use the command system for building applications with undo/redo functionality, observable properties, and UI layout management.

## Table of Contents

1. [Core Components](#core-components)
2. [Observable Properties](#observable-properties)
3. [Command Management](#command-management)
4. [UI Integration](#ui-integration)
5. [Layout Management](#layout-management)
6. [Project Save/Load](#project-saveload)

## Core Components

The command system consists of several key components:

- **Observable**: Base class for models with observable properties
- **ObservableProperty**: Type-safe property descriptor with change tracking
- **CommandManager**: Manages the undo/redo stack
- **DockManager**: Manages dock widgets
- **LayoutManager**: Saves and restores UI layouts
- **ProjectManager**: Handles project serialization

## Observable Properties

### Creating an Observable Model

```python
from command_system import Observable, ObservableProperty

class MyModel(Observable):
    # Define properties with type hints and default values
    name = ObservableProperty[str](default="Untitled")
    count = ObservableProperty[int](default=0)
    is_active = ObservableProperty[bool](default=True)
```

### Using Observable Properties

```python
# Create an instance
model = MyModel()

# Get property values
print(model.name)  # "Untitled"

# Set property values (automatically tracked for undo/redo)
model.name = "New Name"
model.count += 1
```

### Observing Property Changes

```python
# Define a change handler
def on_property_changed(property_name, old_value, new_value):
    print(f"Property {property_name} changed: {old_value} → {new_value}")

# Register the observer
model.add_property_observer("name", on_property_changed)
```

## Command Management

### Accessing the Command Manager

```python
from command_system import get_command_manager

# Get the global command manager instance
cmd_manager = get_command_manager()
```

### Creating Custom Commands

```python
from command_system import Command

class MyCommand(Command):
    def __init__(self, model, new_value):
        self.model = model
        self.new_value = new_value
        self.old_value = model.some_property
        
    def execute(self):
        # Perform the action
        self.model.some_property = self.new_value
        return True
        
    def undo(self):
        # Restore previous state
        self.model.some_property = self.old_value
        return True
```

### Executing Commands

```python
# Create a command
cmd = MyCommand(model, "new value")

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

### Batch Commands

```python
# Begin a compound operation
cmd_manager.begin_compound()

# Execute multiple commands that will be treated as one unit
cmd_manager.execute(cmd1)
cmd_manager.execute(cmd2)

# End the compound operation
cmd_manager.end_compound("Compound Operation Name")
```

## UI Integration

### Command-Aware Widgets

```python
from command_system.ui.widgets import (
    CommandLineEdit, CommandSpinBox, CommandCheckBox, CommandTextEdit
)

# Create a widget
name_edit = CommandLineEdit()

# Bind it to a model property
name_edit.bind_to_model(model, "name")

# Changes in the widget will now be tracked for undo/redo
```

### Available Command Widgets

- `CommandLineEdit`: Text input with undo/redo
- `CommandTextEdit`: Multi-line text with undo/redo
- `CommandSpinBox`: Integer spinner with undo/redo
- `CommandDoubleSpinBox`: Float spinner with undo/redo
- `CommandComboBox`: Dropdown selector with undo/redo
- `CommandCheckBox`: Boolean checkbox with undo/redo
- `CommandSlider`: Range slider with undo/redo
- `CommandDateEdit`: Date selector with undo/redo

### Dock Widgets

```python
from command_system.ui.dock import (
    get_dock_manager, CommandDockWidget, CreateDockCommand
)

# Get the dock manager
dock_manager = get_dock_manager()
dock_manager.set_main_window(main_window)

# Create a dock widget
dock = CommandDockWidget("dock_id", "Dock Title", main_window)
dock.setWidget(content_widget)

# Add the dock using a command
cmd = CreateDockCommand("dock_id", dock, None, Qt.RightDockWidgetArea)
cmd_manager.execute(cmd)
```

### Observable Dock Widgets

```python
from command_system.ui.dock import ObservableDockWidget

# Create a dock with an associated model
dock = ObservableDockWidget("dock_id", "Title", main_window, model)
```

## Layout Management

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
# Register a widget to track in layouts
layout_manager.register_widget("widget_id", widget)

# Register a factory for recreating widgets
def create_widget():
    # Create a new widget instance
    return new_widget

layout_manager.register_widget_factory("WidgetType", create_widget)
```

### Saving and Loading Layouts

```python
# Save the current layout
layout_manager.save_layout_preset("My Layout")

# Load a saved layout
layout_manager.load_layout_preset("My Layout")

# Get available layouts
presets = layout_manager.get_available_presets()
```

## Project Save/Load

### Setting Up Project Manager

```python
from command_system import get_project_manager

# Get the project manager
project_manager = get_project_manager()

# Register model types for serialization
project_manager.register_model_type("note", lambda: NoteModel())
```

### Saving and Loading Projects

```python
# Save the current project
project_manager.save_project(model, "myproject.json")

# Load a project
model = project_manager.load_project("myproject.json")

# Create a new project
model = project_manager.new_project("note")
```

### Project Formats

```python
# Set the default format
project_manager.set_default_format("json")  # Options: json, bin, xml, yaml

# Get file extension for current format
extension = project_manager.get_default_extension()
```

## Integrating with Layout System

```python
from command_system.layout import extend_project_manager

# Extend the project manager with layout capabilities
extend_project_manager()

# Now projects will include layout information when saved
```

## Best Practices

1. Use `begin_init()` and `end_init()` to disable command tracking during initialization:
   ```python
   cmd_manager.begin_init()
   # Perform setup operations
   cmd_manager.end_init()
   ```

2. Implement a confirmation dialog for unsaved changes:
   ```python
   if cmd_manager.can_undo() and not confirm_discard_changes():
       return  # Cancel operation if user doesn't want to discard changes
   ```

3. Update window title to show unsaved state:
   ```python
   if cmd_manager.can_undo():
       title = f"*{title}"  # Add asterisk for modified state
   ```

4. Connect property observers to update UI:
   ```python
   model.add_property_observer("property", update_ui_function)
   ```

By following these patterns, you can create applications with robust undo/redo capability, property binding, and layout persistence.