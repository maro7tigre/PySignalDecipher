# PySignalDecipher Command System - Developer Guide

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
   - [Command Pattern](#command-pattern)
   - [Observable Pattern](#observable-pattern)
   - [Command Manager](#command-manager)
   - [UI Integration](#ui-integration)
   - [Serialization](#serialization)
4. [Implementation Details](#implementation-details)
   - [Command Execution Flow](#command-execution-flow)
   - [Property Change Tracking](#property-change-tracking)
   - [UI Widget Binding](#ui-widget-binding)
   - [Save/Load Mechanism](#saveload-mechanism)
5. [Extending the System](#extending-the-system)
   - [Creating Custom Commands](#creating-custom-commands)
   - [Adding New Observable Models](#adding-new-observable-models)
   - [Developing Command-Aware Widgets](#developing-command-aware-widgets)
   - [Implementing Custom Serializers](#implementing-custom-serializers)
6. [Advanced Usage](#advanced-usage)
   - [Handling Complex Domain Logic](#handling-complex-domain-logic)
   - [Proper Error Handling](#proper-error-handling)
   - [Performance Considerations](#performance-considerations)
   - [Threading and Concurrency](#threading-and-concurrency)
7. [Testing Strategies](#testing-strategies)
8. [Common Pitfalls](#common-pitfalls)

## Introduction

The PySignalDecipher Command System is designed to address several common challenges in application development:

1. **Managing application state changes**: Tracking when and how data changes
2. **Supporting undo/redo**: Allowing users to reverse or replay actions
3. **Binding UI to data models**: Keeping the UI and model in sync
4. **Serializing application state**: Saving and loading the application state

The system implements the Command Pattern and Observable Pattern to create a cohesive architecture that solves these problems while maintaining separation of concerns and testability.

## System Architecture

The system follows a layered architecture:

1. **Core Layer**: Command and Observable implementations
2. **Management Layer**: Command Manager and Project Manager
3. **UI Integration Layer**: Property bindings and command-aware widgets
4. **Serialization Layer**: JSON and other format serializers

These layers interact in the following way:

```
┌─────────────────┐     ┌───────────────┐
│     UI Layer    │     │ Serialization │
│  (Qt Widgets)   │     │     Layer     │
└────────┬────────┘     └───────┬───────┘
         │                      │
         ▼                      ▼
┌─────────────────────────────────────────┐
│              Management Layer           │
│   (Command Manager, Project Manager)    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│                Core Layer               │
│       (Command, Observable Models)      │
└─────────────────────────────────────────┘
```

Changes flow in a cyclical pattern:
1. UI actions create commands
2. Commands modify the model
3. Model changes notify observers
4. UI updates in response to notifications

## Core Components

### Command Pattern

The Command Pattern encapsulates actions as objects with two primary operations:
- `execute()`: Perform the action
- `undo()`: Reverse the action

The basic implementation consists of:

```python
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass
        
    @abstractmethod
    def undo(self) -> None:
        """Undo the command."""
        pass
        
    def redo(self) -> None:
        """Redo the command. Default implementation calls execute."""
        self.execute()
```

Key command implementations:

1. **PropertyCommand**: Changes a property value on an observable object
   ```python
   class PropertyCommand(Command):
       def __init__(self, target, property_name: str, new_value):
           self.target = target
           self.property_name = property_name
           self.new_value = new_value
           self.old_value = getattr(target, property_name)
           
       def execute(self) -> None:
           setattr(self.target, self.property_name, self.new_value)
           
       def undo(self) -> None:
           setattr(self.target, self.property_name, self.old_value)
   ```

2. **CompoundCommand**: Groups multiple commands into a single unit
   ```python
   class CompoundCommand(Command):
       def __init__(self, name: str = "Compound Command"):
           self.name = name
           self.commands = []
           
       def add_command(self, command: Command) -> None:
           self.commands.append(command)
           
       def execute(self) -> None:
           for command in self.commands:
               command.execute()
               
       def undo(self) -> None:
           for command in reversed(self.commands):
               command.undo()
   ```

### Observable Pattern

The Observable Pattern enables objects to notify observers when their properties change:

```python
class ObservableProperty(Generic[T]):
    """Descriptor for observable properties."""
    def __init__(self, default: T = None):
        self.default = default
        self.name = None
        self.private_name = None
        
    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_{name}"
        
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.private_name, self.default)
        
    def __set__(self, instance, value):
        old_value = getattr(instance, self.private_name, self.default)
        
        # Only notify if value actually changed
        if old_value != value:
            setattr(instance, self.private_name, value)
            instance._notify_property_changed(self.name, old_value, value)
```

And the Observable base class:

```python
class Observable:
    """Base class for objects that need to track property changes."""
    def __init__(self):
        self._property_observers = {}
        self._id = str(uuid.uuid4())
        self._is_updating = False
        
    def add_property_observer(self, property_name: str, callback: Callable) -> str:
        """Add observer for property changes."""
        if property_name not in self._property_observers:
            self._property_observers[property_name] = {}
            
        observer_id = str(uuid.uuid4())
        self._property_observers[property_name][observer_id] = callback
        return observer_id
        
    def _notify_property_changed(self, property_name: str, old_value: Any, new_value: Any) -> None:
        """Notify observers of property change."""
        if self._is_updating:
            return  # Prevent recursive updates
            
        if property_name in self._property_observers:
            try:
                self._is_updating = True
                for callback in self._property_observers[property_name].values():
                    callback(property_name, old_value, new_value)
            finally:
                self._is_updating = False
```

### Command Manager

The Command Manager maintains the history of commands and provides undo/redo functionality:

```python
class CommandManager:
    """Singleton manager for command execution and history tracking."""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CommandManager()
        return cls._instance
    
    def __init__(self):
        self._history = CommandHistory()
        self._is_updating = False
    
    def execute(self, command: Command) -> bool:
        """Execute a command and add it to the history."""
        if self._is_updating:
            return True  # Skip if already processing a command
            
        try:
            self._is_updating = True
            self._history.add_command(command)
            command.execute()
            return True
        except Exception as e:
            print(f"Error executing command: {e}")
            return False
        finally:
            self._is_updating = False
    
    def undo(self) -> bool:
        """Undo the most recent command in the history."""
        if self._is_updating:
            return False
            
        command = self._history.undo()
        if command:
            try:
                self._is_updating = True
                command.undo()
                return True
            finally:
                self._is_updating = False
        return False
```

### UI Integration

The UI integration layer bridges the gap between UI widgets and the observable model:

```python
class Binding(ABC):
    """Abstract base class for property bindings."""
    
    def __init__(self, model: Observable, property_name: str, widget, command_manager=None):
        self.model = model
        self.property_name = property_name
        self.widget = widget
        self.command_manager = command_manager or get_command_manager()
        self.observer_id = None
        self.updating_model = False
        self.updating_widget = False
        
    def activate(self) -> None:
        """Activate the binding."""
        # Observe model property changes
        self.observer_id = self.model.add_property_observer(
            self.property_name, self._on_property_changed
        )
        
        # Connect widget signals
        self._connect_widget_signals()
        
        # Initialize widget with model value
        self._update_widget_from_model()
        
    def _on_property_changed(self, property_name: str, old_value: Any, new_value: Any) -> None:
        """Called when the bound property changes."""
        # Prevent infinite recursion
        if self.updating_model:
            return
            
        self.updating_widget = True
        try:
            self._update_widget_from_model()
        finally:
            self.updating_widget = False
            
    def _on_widget_changed(self) -> None:
        """Called when the widget value changes."""
        # Prevent infinite recursion
        if self.updating_widget:
            return
            
        self.updating_model = True
        try:
            value = self._get_widget_value()
            
            # Create and execute command
            cmd = PropertyCommand(self.model, self.property_name, value)
            self.command_manager.execute(cmd)
        finally:
            self.updating_model = False
```

### Serialization

The serialization system allows saving and loading application state:

```python
class ProjectSerializer:
    """Handles serialization and deserialization of project data."""
    
    @staticmethod
    def save_to_file(model: Observable, filename: str, format_type="json") -> bool:
        """Save a model to a file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(model, f, cls=ObservableEncoder, indent=2)
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    @staticmethod
    def load_from_file(filename: str, format_type=None) -> Optional[Observable]:
        """Load a model from a file."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f, object_hook=observable_decoder)
        except Exception as e:
            print(f"Error loading project: {e}")
            return None
```

## Implementation Details

### Command Execution Flow

When a command is executed, it follows this flow:

1. Client code creates a command object
2. Command is passed to `CommandManager.execute()`
3. CommandManager adds the command to history
4. The command's `execute()` method is called
5. Changes are applied to the model
6. Model notifies observers of changes
7. UI updates in response to notifications

```
┌──────────┐    ┌──────────────┐    ┌─────────┐    ┌──────────┐
│   User   │    │    Widget    │    │ Command │    │  Model   │
│  Action  │───>│  (Observer)  │───>│ Manager │───>│ (Subject)│
└──────────┘    └──────────────┘    └─────────┘    └──────────┘
                       ▲                                │
                       └────────────────────────────────┘
                              Notification
```

### Property Change Tracking

Observable properties use Python descriptors to track changes:

1. `ObservableProperty.__set__()` compares old and new values
2. If changed, calls `_notify_property_changed()` on the instance
3. `_notify_property_changed()` iterates through registered callbacks
4. Each callback is called with (property_name, old_value, new_value)

The `_is_updating` flag prevents recursive updates that could occur if an observer modifies the property it's observing.

### UI Widget Binding

Command-aware widgets use a bidirectional binding approach:

1. **Model → Widget**: Property observers update the widget when model changes
2. **Widget → Model**: Widget signal handlers create commands to update the model

This creates a circular update path, which is managed through the following mechanism:

- Each binding has `updating_model` and `updating_widget` flags
- These flags prevent infinite loops when updates occur
- The CommandManager's `_is_updating` flag prevents recursive command execution

### Save/Load Mechanism

The serialization mechanism uses custom JSON encoding/decoding:

1. `ObservableEncoder` serializes Observable objects by:
   - Saving class information 
   - Saving unique ID
   - Collecting and saving all ObservableProperty values

2. `observable_decoder` deserializes by:
   - Importing the original class based on saved path
   - Creating an instance
   - Setting the unique ID
   - Setting all property values

## Extending the System

### Creating Custom Commands

To create a custom command:

1. Subclass the `Command` base class
2. Implement `execute()` and `undo()` methods
3. Store any state needed to undo the operation

```python
class InsertTextCommand(Command):
    def __init__(self, text_model, position, text):
        self.model = text_model
        self.position = position
        self.text = text
        
    def execute(self):
        current = self.model.content
        new_content = current[:self.position] + self.text + current[self.position:]
        self.model.content = new_content
        
    def undo(self):
        current = self.model.content
        new_content = current[:self.position] + current[self.position + len(self.text):]
        self.model.content = new_content
```

### Adding New Observable Models

To create a new model:

1. Subclass `Observable`
2. Define properties using `ObservableProperty`
3. Add any domain-specific logic

```python
class Document(Observable):
    title = ObservableProperty[str](default="Untitled")
    content = ObservableProperty[str](default="")
    created_date = ObservableProperty[datetime](default=datetime.now())
    modified_date = ObservableProperty[datetime](default=datetime.now())
    
    def __init__(self):
        super().__init__()
        
        # Update modified date when content changes
        self.add_property_observer("content", self._on_content_changed)
        
    def _on_content_changed(self, prop, old, new):
        self.modified_date = datetime.now()
```

### Developing Command-Aware Widgets

To create a command-aware widget:

1. Inherit from both the Qt widget and `CommandWidgetBase`
2. Call both parent constructors
3. Set up the command widget with the property name
4. Connect widget signals to `_on_widget_value_changed()`
5. Implement `_get_widget_value()` and `_set_widget_value()`

```python
class CommandColorButton(QPushButton, CommandWidgetBase):
    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        CommandWidgetBase.__init__(self)
        
        # Set up command widget
        self._setup_command_widget("color")
        
        # Connect signals
        self.clicked.connect(self._on_clicked)
        
        # Set initial appearance
        self._update_button_appearance()
        
    def _on_clicked(self):
        # Show color dialog
        color = QColorDialog.getColor(self._get_widget_value(), self.parent())
        if color.isValid():
            # This will trigger _on_widget_value_changed
            self._color = color
            self._update_button_appearance()
            self._on_widget_value_changed()
            
    def _get_widget_value(self):
        return self._color
        
    def _set_widget_value(self, value):
        self._color = value
        self._update_button_appearance()
        
    def _update_button_appearance(self):
        style = f"background-color: {self._color.name()};"
        self.setStyleSheet(style)
```

### Implementing Custom Serializers

To add support for a new serialization format:

1. Extend `ProjectSerializer` with the new format
2. Add appropriate format constants
3. Implement format-specific save and load methods

```python
# Add support for YAML format
def save_to_yaml(model: Observable, filename: str) -> bool:
    try:
        import yaml
        
        # Convert model to dictionary
        model_dict = json.loads(json.dumps(model, cls=ObservableEncoder))
        
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(model_dict, f)
        return True
    except Exception as e:
        print(f"Error saving as YAML: {e}")
        return False

# Add to ProjectSerializer
@staticmethod
def save_to_file(model: Observable, filename: str, format_type="json") -> bool:
    if format_type == ProjectSerializer.FORMAT_YAML:
        return save_to_yaml(model, filename)
    # ... other formats
```

## Advanced Usage

### Handling Complex Domain Logic

For complex domain operations:

1. Encapsulate the operation in a dedicated command class
2. Use CompoundCommand for multi-step operations
3. Add validation to the execute method
4. Add domain-specific error recovery when needed

Example of a complex operation using CompoundCommand:

```python
def rename_and_move_item(item, new_name, new_parent):
    # Create a compound command for the operation
    compound = CompoundCommand(f"Rename and Move {item.name}")
    
    # Add individual commands
    compound.add_command(RenameItemCommand(item, new_name))
    compound.add_command(MoveItemCommand(item, new_parent))
    
    # Execute the compound command
    cmd_manager = get_command_manager()
    success = cmd_manager.execute(compound)
    
    return success
```

### Proper Error Handling

Commands should handle errors gracefully:

1. Validate inputs before executing
2. Catch and handle exceptions during execution
3. Ensure undo can still work even if execute fails partially

```python
class DeleteFileCommand(Command):
    def __init__(self, file_path):
        self.file_path = file_path
        self.backup_data = None
        
    def execute(self):
        # Validate
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
            
        # Backup before deleting
        try:
            with open(self.file_path, 'rb') as f:
                self.backup_data = f.read()
            
            # Delete the file
            os.remove(self.file_path)
        except Exception as e:
            raise CommandExecutionError(f"Failed to delete file: {e}")
        
    def undo(self):
        if self.backup_data is None:
            raise CommandUndoError("No backup data available")
            
        try:
            # Restore from backup
            with open(self.file_path, 'wb') as f:
                f.write(self.backup_data)
        except Exception as e:
            raise CommandUndoError(f"Failed to restore file: {e}")
```

### Performance Considerations

For performance-critical applications:

1. Batch small changes into compound commands to reduce overhead
2. Implement lazy property observers that only update when needed
3. Use command compression to reduce history size
4. Consider memory usage for large histories

Example of command compression:

```python
class CommandHistory:
    def add_command(self, command: Command) -> None:
        """
        Add a command to the history with optional compression.
        """
        if self._can_compress(command):
            # Compress with last command
            last_command = self._executed_commands[-1]
            compressed = self._compress_commands(last_command, command)
            self._executed_commands[-1] = compressed
        else:
            # Add as normal
            self._executed_commands.append(command)
        self._undone_commands.clear()
        
    def _can_compress(self, command: Command) -> bool:
        """Check if command can be compressed with the previous one."""
        if not self._executed_commands:
            return False
            
        last_command = self._executed_commands[-1]
        
        # Only compress property commands on the same property
        if (isinstance(command, PropertyCommand) and 
            isinstance(last_command, PropertyCommand) and
            command.target == last_command.target and
            command.property_name == last_command.property_name):
            return True
            
        return False
        
    def _compress_commands(self, old_cmd: PropertyCommand, 
                           new_cmd: PropertyCommand) -> PropertyCommand:
        """
        Compress two property commands into one.
        Keep first command's old value and last command's new value.
        """
        return PropertyCommand(old_cmd.target, old_cmd.property_name, 
                              new_cmd.new_value, old_cmd.old_value)
```

### Threading and Concurrency

The command system is primarily designed for single-threaded use, but can be adapted for multi-threaded environments:

1. Add locking to CommandManager and CommandHistory
2. Ensure Observable notifications run on the UI thread
3. Queue commands from background threads

Example of thread-safe command manager:

```python
import threading

class ThreadSafeCommandManager(CommandManager):
    def __init__(self):
        super().__init__()
        self._lock = threading.RLock()
        
    def execute(self, command: Command) -> bool:
        with self._lock:
            return super().execute(command)
            
    def undo(self) -> bool:
        with self._lock:
            return super().undo()
            
    def redo(self) -> bool:
        with self._lock:
            return super().redo()
```

## Testing Strategies

The command system architecture enables several testing approaches:

1. **Unit tests for commands**: Test execute and undo in isolation
   ```python
   def test_property_command():
       # Create model
       model = TestModel()
       model.value = 10
       
       # Create and execute command
       cmd = PropertyCommand(model, "value", 20)
       cmd.execute()
       
       # Check execution
       assert model.value == 20
       
       # Check undo
       cmd.undo()
       assert model.value == 10
   ```

2. **Observable property tests**: Verify notifications
   ```python
   def test_observable_property_notification():
       model = TestModel()
       
       # Track notifications
       notifications = []
       model.add_property_observer("value", 
                   lambda p, o, n: notifications.append((p, o, n)))
       
       # Change property
       model.value = 99
       
       # Check notification
       assert len(notifications) == 1
       assert notifications[0] == ("value", 0, 99)
   ```

3. **Command manager tests**: Verify history and undo/redo
   ```python
   def test_command_manager_undo_redo():
       manager = CommandManager.get_instance()
       manager.clear()
       
       # Create model
       model = TestModel()
       
       # Execute commands
       manager.execute(PropertyCommand(model, "value", 10))
       manager.execute(PropertyCommand(model, "value", 20))
       
       # Verify execution
       assert model.value == 20
       
       # Verify undo
       manager.undo()
       assert model.value == 10
       
       # Verify redo
       manager.redo()
       assert model.value == 20
   ```

4. **UI binding tests**: Verify two-way binding
   ```python
   def test_line_edit_binding(qtbot):
       # Create model and widget
       model = TestModel()
       model.text = "Initial"
       
       edit = CommandLineEdit()
       edit.bind_to_model(model, "text")
       
       # Verify initial state
       assert edit.text() == "Initial"
       
       # Change model, verify widget updates
       model.text = "Changed"
       assert edit.text() == "Changed"
       
       # Change widget, verify model updates
       edit.setText("User Input")
       qtbot.keyClick(edit, Qt.Key_Return)
       assert model.text == "User Input"
   ```

## Common Pitfalls

1. **Circular updates**: When property observers modify properties, causing infinite recursion
   - Solution: Use the `_is_updating` flag to break cycles

2. **Memory leaks**: Failing to remove property observers when no longer needed
   - Solution: Implement proper cleanup in UI components

3. **Command granularity**: Too many small commands can slow down the system
   - Solution: Use compound commands for logically related operations

4. **Serialization failures**: Forgetting to handle circular references
   - Solution: Implement proper reference tracking in serialization

5. **Thread safety issues**: Using the system across multiple threads
   - Solution: Add synchronization or ensure single-threaded access

6. **UI binding complexity**: Managing bidirectional updates
   - Solution: Use the provided binding classes which handle this automatically

7. **State consistency**: Ensuring the model stays in a valid state
   - Solution: Validate changes in model setters and command execution

8. **Command undo safety**: Ensuring undo operations work correctly
   - Solution: Test undo operations thoroughly and handle edge cases