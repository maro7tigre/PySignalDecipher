# PySignalDecipher Command System

A lightweight, flexible command pattern implementation for building applications with robust undo/redo functionality, layout management, and project serialization.

## Overview

The PySignalDecipher Command System provides a clean, integrated implementation of several design patterns:

- **Command Pattern**: Track user actions as undoable operations
- **Observable Pattern**: Monitor property changes with callbacks
- **Model-View Binding**: Connect UI controls to model properties
- **Serialization**: Save and load application state
- **Layout Management**: Store and restore UI configurations

This comprehensive architecture allows you to build applications with:

- Consistent undo/redo functionality
- Automatic state tracking
- UI binding with property synchronization
- Project save/load capabilities
- Persistent layout configurations
- Dock widget management

## System Architecture

The command system consists of several integrated components:

```
┌─────────────────────────────────────────────────┐
│                   UI Layer                       │
│  Command-aware widgets, Dock widgets, Layouts    │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────┐
│             Management Layer                     │
│  CommandManager, ProjectManager, LayoutManager   │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────┐
│                Core Layer                        │
│        Commands, Observable Properties           │
└─────────────────────────────────────────────────┘
```

### Core Components

#### Command System
- `Command`: Abstract base class for all commands
- `CompoundCommand`: Groups multiple commands into a single unit
- `PropertyCommand`: Command for property changes
- `CommandManager`: Tracks undo/redo history

#### Observable System
- `Observable`: Base class for objects that track property changes
- `ObservableProperty`: Descriptor for properties that notify on changes

#### UI Integration
- Command-aware widgets that auto-create commands
- Property binding system for two-way synchronization
- Dock management with command integration

#### Layout Management
- Layout serialization for UI configurations
- Preset management for named layouts
- Widget state tracking and restoration

#### Project Serialization
- Multi-format serialization (JSON, Binary, XML, YAML)
- Model factory registration for type-safe deserialization
- Layout integration with project files

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

### Command-Aware Widgets

```python
from command_system.ui.widgets import CommandLineEdit, CommandSpinBox

# Create model with observable properties
class DemoModel(Observable):
    name = ObservableProperty[str](default="John Doe")
    count = ObservableProperty[int](default=0)

# Bind widgets to model properties
model = DemoModel()
name_edit = CommandLineEdit()
name_edit.bind_to_model(model, "name")

count_spin = CommandSpinBox()
count_spin.bind_to_model(model, "count")
```

### Project Save/Load

```python
from command_system import get_project_manager

# Get project manager
project_manager = get_project_manager()

# Register model type
project_manager.register_model_type("note", lambda: NoteModel())

# Save project
project_manager.save_project(model, "myproject.json")

# Load project
loaded_model = project_manager.load_project("myproject.json")
```

### Layout Management

```python
from command_system.layout import get_layout_manager

# Get layout manager
layout_manager = get_layout_manager()
layout_manager.set_main_window(main_window)

# Register widgets to track
layout_manager.register_widget("main_splitter", main_splitter)

# Save current layout
layout_manager.save_layout_preset("default")

# Restore layout
layout_manager.load_layout_preset("default")
```

### Dock Management

```python
from command_system.ui.dock import get_dock_manager, CommandDockWidget

# Get dock manager
dock_manager = get_dock_manager()
dock_manager.set_main_window(main_window)

# Create a dock widget
dock = CommandDockWidget("my_dock", "My Dock", main_window)
dock.setWidget(content_widget)

# Add to manager
dock_manager.register_dock("my_dock", dock)
```

## Using the Command System

### Commands

The `Command` class encapsulates actions that can be executed, undone, and redone:

```python
class MyCommand(Command):
    def __init__(self, target, new_value):
        self.target = target
        self.new_value = new_value
        self.old_value = target.value
        
    def execute(self):
        self.target.value = self.new_value
        
    def undo(self):
        self.target.value = self.old_value
```

### Observable Properties

Observable properties notify observers when they change:

```python
class MyModel(Observable):
    name = ObservableProperty[str](default="")
    count = ObservableProperty[int](default=0)
    
model = MyModel()

# Add observer
def on_name_changed(prop_name, old_value, new_value):
    print(f"Name changed from {old_value} to {new_value}")
    
model.add_property_observer("name", on_name_changed)
```

### Command Manager

The command manager tracks history and provides undo/redo:

```python
# Execute a command
cmd_manager.execute(my_command)

# Check if undo/redo is available
can_undo = cmd_manager.can_undo()
can_redo = cmd_manager.can_redo()

# Perform undo/redo
cmd_manager.undo()
cmd_manager.redo()
```

### UI Integration

The system provides ready-to-use command-aware widgets:

- `CommandLineEdit`: For text input
- `CommandTextEdit`: For multi-line text
- `CommandSpinBox`: For numbers
- `CommandCheckBox`: For boolean values
- `CommandComboBox`: For selections
- `CommandSlider`: For ranges
- `CommandDateEdit`: For dates

These widgets automatically create commands when their values change.

### Layout Integration

The layout system allows:

- Saving current UI state as named presets
- Restoring UI configurations
- Embedding layout data within project files
- Widget factory registration for recreating UIs

### Project Serialization

The serialization system provides:

- Multi-format support (JSON, Binary, XML, YAML)
- Observable property serialization
- Model factory system for proper reconstruction
- Integration with layout management

## Advanced Features

### Initialization Mode

Disable command tracking during setup:

```python
cmd_manager.begin_init()
# Perform setup operations
cmd_manager.end_init()
```

### Compound Commands

Group multiple commands into a single undoable unit:

```python
compound = CompoundCommand("Rename and Move")
compound.add_command(RenameCommand(item, new_name))
compound.add_command(MoveCommand(item, new_position))
cmd_manager.execute(compound)
```

### Layout with Projects

Save layouts with projects:

```python
# Enable layout saving
project_manager.set_save_layouts(True)
project_manager.save_project(model, filename)
```

## Demos and Examples

The system includes several demo applications:

- `widgets_demo.py`: Demonstrates command-aware widgets
- `file_menu_demo.py`: Shows project save/load functionality
- `docks_demo.py`: Illustrates dock management
- `layout_demo.py`: Demonstrates layout system
- `complete_demo.py`: Comprehensive demo of all features

## Key Benefits

- **Clean architecture**: Separation of concerns through layered design
- **Type safety**: Type hints and descriptors for better editor support
- **Auto-tracking**: Widget changes automatically create commands
- **UI binding**: Two-way synchronization between models and UI
- **Persistence**: Save and restore application state
- **Layout management**: Store and apply UI configurations

## Integration with Qt

The system works seamlessly with Qt/PySide/PyQt applications, with specialized support for:

- Qt widgets (through command-aware wrappers)
- Qt signals/slots (for property binding)
- Dock widgets (for window layout management)
- MainWindow layouts (for restoration)