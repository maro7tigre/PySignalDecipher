# Command System Documentation

This document provides detailed information about the command system implementation for PySignalDecipher, including its architecture, components, and usage guidelines.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
   - [Command Interface](#command-interface)
   - [Command History](#command-history)
   - [Command Manager](#command-manager)
   - [Observable Properties](#observable-properties)
   - [Variable System](#variable-system)
   - [Project Model](#project-model)
4. [Hardware Integration](#hardware-integration)
5. [Workspace Management](#workspace-management)
6. [Command Implementations](#command-implementations)
   - [Signal Commands](#signal-commands)
   - [Workspace Commands](#workspace-commands)
   - [Project Commands](#project-commands)
   - [Dock Commands](#dock-commands)
7. [Integration Guide](#integration-guide)
8. [File Reference](#file-reference)
9. [Usage Examples](#usage-examples)

## Overview

The command system provides a robust foundation for history tracking (undo/redo), project serialization, and state management in PySignalDecipher. It follows the Command pattern, where all user actions that modify state are encapsulated as commands that can be executed, undone, and redone. The system also provides observable properties for tracking state changes, a variable registry for linking components, hardware integration through PyVISA, and a comprehensive project model for serialization.

## Architecture

The command system is organized into several key components:

```
┌───────────────────────────────────────────────────────────┐
│                    User Interface                         │
│                                                           │
│  ┌────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ UI Actions │───▶│ Command Exec │    │ Workspaces    │  │
│  └────────────┘    └──────────────┘    │ & Docks       │  │
│                                        └───────┬───────┘  │
└────────────────────────┬────────────────────────┼─────────┘
                         │                        │
┌────────────────────────▼────────────────────────▼─────────┐
│                     Command System                         │
│                                                           │
│  ┌────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ Commands   │──▶ │    History   │    │ Variable      │  │
│  └────────────┘    └──────────────┘    │ Registry      │  │
│                          │             └───────┬───────┘  │
│  ┌────────────┐    ┌─────▼────────┐           │          │
│  │ Observable │◀───┤ State Changes│◀──────────┘          │
│  │ Properties │    └──────────────┘                      │
│  └─────┬──────┘                                          │
└─────────┼────────────────────────────┬───────────────────┘
          │                            │
┌─────────▼────────────────────┐ ┌─────▼─────────────────────┐
│      Project Model           │ │   Hardware Integration     │
│                              │ │                            │
│  ┌───────────┐ ┌───────────┐ │ │ ┌──────────────────────┐  │
│  │  Signals  │ │ Workspaces│ │ │ │ Hardware Manager     │  │
│  └───────────┘ └───────────┘ │ │ │                      │  │
│                              │ │ │ ┌─────────────────┐  │  │
│  ┌──────────────────────────┐│ │ │ │PyVISA Interface │  │  │
│  │  Serialization Layer     ││ │ │ └─────────────────┘  │  │
│  └──────────────────────────┘│ │ └──────────────────────┘  │
└──────────────┬───────────────┘ └────────────────────────────┘
               │
        ┌──────▼─────┐
        │Project File│
        └────────────┘
```

## Core Components

### Command Interface

**File: `command_system/command.py`**

This file defines the core `Command` interface and related utilities:

- `Command`: Abstract base class that all commands must implement
  - `execute()`: Performs the command's action
  - `undo()`: Reverses the command's action
  - `redo()`: Redoes the command (by default calls execute)
  - `get_state()`: Returns a serializable representation of the command
  - `from_state()`: Creates a command from serialized state

- `CommandFactory`: Registry for command types that can create commands from serialized state
  - `register()`: Registers a command class with the factory
  - `create_from_state()`: Creates a command instance from type and state

- `CompoundCommand`: A command that groups multiple commands as a single unit
  - Useful for operations that involve multiple steps but should be treated as a single action

### Command History

**File: `command_system/command_history.py`**

Manages the history of executed commands for undo/redo functionality:

- `CommandHistory`: Tracks command execution and manages the undo/redo stacks
  - `execute_command()`: Executes a command and adds it to history
  - `undo()`: Undoes the most recently executed command
  - `redo()`: Redoes the most recently undone command
  - `can_undo()/can_redo()`: Checks if undo/redo is possible
  - `get_serializable_history()`: Returns a serializable representation of history
  - `from_serialized_history()`: Creates a history from serialized state

The history manager maintains an ordered list of executed commands and tracks the current position in the history, allowing for navigation through the command history.

### Command Manager

**File: `command_system/command_manager.py`**

Provides a centralized interface for executing commands, managing command history, and coordinating between different system components:

- `CommandManager`: Central point for system coordination
  - `execute_command()`: Executes a command and adds it to history
  - `undo()/redo()`: Undoes/redoes commands through history
  - `can_undo()/can_redo()`: Checks if undo/redo is possible
  - `register_command()`: Registers a command type with the factory
  - `register_history_observers()`: Registers callbacks for undo/redo state changes
  - `get_variable_registry()`: Returns the variable registry
  - `get_hardware_manager()`: Returns the hardware manager
  - `get_workspace_manager()`: Returns the workspace manager
  - Signal handling for command execution events:
    - `command_executed`: Emitted when a command is executed
    - `command_undone`: Emitted when a command is undone
    - `command_redone`: Emitted when a command is redone
    - `history_changed`: Emitted when history state changes

The CommandManager acts as a facade for the command system, providing a simple interface for UI components and coordinating between different subsystems.

### Observable Properties

**File: `command_system/observable.py`**

Provides property tracking and change notification for objects:

- `ObservableProperty`: A property descriptor that tracks changes and notifies observers
  - Automatically detects property changes
  - Notifies the owning object when changes occur
  
- `Observable`: Base class for objects with observable properties
  - `property_changed` signal: Emitted when a property changes
  - `add_property_observer()/remove_property_observer()`: Manages property observers
  - `get_all_properties()/set_properties()`: Bulk property operations

- `PropertyChangeCommand`: Mixin class for commands that change observable properties
  - Tracks old and new values for property changes
  - Provides standard execute/undo/redo implementations

- `SignalVariable`: Enhanced observable for linking values across components
  - `value` property: The variable's value
  - `subscribe()`: Register a subscriber to be notified of value changes
  - `unsubscribe()`: Remove a subscriber
  - `clear_subscribers()`: Remove all subscribers

Observable properties and signal variables provide the foundation for tracking state changes and linking components.

### Variable System

**File: `command_system/variable_registry.py`**

Provides a registry for tracking variables and their relationships:

- `VariableRegistry`: Central registry for variables
  - `register_variable()`: Register a variable in the system
  - `unregister_variable()`: Remove a variable from the registry
  - `unregister_parent()`: Unregister all variables belonging to a parent
  - `get_variable()`: Get a variable by ID
  - `get_variables_by_parent()`: Get all variables belonging to a parent

The variable registry provides a centralized system for tracking variables and their relationships, especially for components like dock widgets that need to be created and destroyed dynamically.

### Project Model

**File: `command_system/project.py`**

Defines the central project model that integrates with the command system:

- `Project`: Represents a complete PySignalDecipher project
  - Manages signals, workspace states, and project settings
  - Integrates with the command system for state tracking
  - Provides serialization/deserialization methods
  - Uses observable properties for state tracking

- `SignalData`: Represents signal data within a project
  - Uses observable properties for state tracking
  - Provides serialization/deserialization methods

- `WorkspaceState`: Represents the state of a workspace within a project
  - Tracks layout, dock states, and workspace settings
  - Uses observable properties for state tracking
  - Provides serialization/deserialization methods

The project model provides a comprehensive representation of application state that can be serialized, deserialized, and tracked for changes.

## Hardware Integration

**File: `command_system/hardware_manager.py`**

Provides integration with oscilloscopes and other hardware devices through PyVISA:

- `HardwareManager`: Manages hardware connections and device parameters
  - `initialize()`: Initialize the hardware manager
  - `get_available_devices()`: Get list of available devices
  - `connect_device()`: Connect to a device and create variables for its parameters
  - `disconnect_device()`: Disconnect a device and clean up associated variables
  - Creates and manages variables linked to device parameters
  - Provides device-specific operations through standard PyVISA commands

The hardware manager provides a bridge between the command system and physical devices, creating variables for device parameters that can be linked to UI components and monitored for changes.

## Workspace Management

**File: `command_system/workspace_manager.py`**

Manages workspaces, tabs, and their associated commands and variables:

- `WorkspaceTabManager`: Manages workspace tabs and their state
  - `create_workspace()`: Create a new workspace tab
  - `set_active_workspace()`: Set the active workspace
  - `remove_workspace()`: Remove a workspace and clean up resources
  - Updates available utility options based on active workspace
  - Coordinates between workspace state in the project and UI components

The workspace manager provides a centralized system for managing workspaces and their associated resources, including dock widgets, variables, and UI components.

## Command Implementations

### Signal Commands

**File: `command_system/commands/signal_commands.py`**

Implements commands for signal operations:

- `AddSignalCommand`: Adds a signal to the project
- `RemoveSignalCommand`: Removes a signal from the project
- `RenameSignalCommand`: Renames a signal

These commands demonstrate how to create concrete command implementations for signal operations.

### Workspace Commands

**File: `command_system/commands/workspace_commands.py`**

Implements commands for workspace operations:

- `ChangeLayoutCommand`: Changes the active layout of a workspace
- `SetDockStateCommand`: Sets the state of a dock widget
- `SetWorkspaceSettingCommand`: Changes a workspace setting

These commands handle workspace-specific operations, such as changing layouts and dock states.

### Project Commands

**File: `command_system/commands/project_commands.py`**

Implements commands for project-level operations:

- `RenameProjectCommand`: Renames the project
- `BatchCommand`: Executes multiple commands as a batch

These commands handle project-level operations and provide utilities for batch operations.

### Dock Commands

**File: `command_system/commands/workspace_commands.py`** (Extended)

New commands for dock widget operations:

- `CreateDockCommand`: Creates a new dock widget and registers it with the workspace
- `RemoveDockCommand`: Removes a dock widget and cleans up associated variables
- `DockLayoutCommand`: Changes the layout position of a dock widget

These commands provide operations for dock widgets, including creation, removal, and layout changes.

## Integration Guide

**File: `command_system/_integration_template.py`**

Provides templates and examples for integrating the command system with PySignalDecipher:

1. Create a central CommandManager that coordinates all subsystems
2. Implement the variable registry for linking components
3. Integrate hardware through the HardwareManager
4. Create workspace tab management through the WorkspaceTabManager
5. Implement dock widget creation and management
6. Add project serialization and deserialization
7. Set up utility groups for hardware connection, workspace options, etc.
8. Add undo/redo support to menus and toolbars
9. Link signals and variables to UI components

The integration guide provides step-by-step instructions for incorporating the command system into the PySignalDecipher application.

## File Reference

| File | Description |
|------|-------------|
| `command_system/__init__.py` | Package exports and initialization |
| `command_system/command.py` | Command interface and factory |
| `command_system/command_history.py` | Undo/redo stack management |
| `command_system/command_manager.py` | Central command execution point |
| `command_system/observable.py` | Observable property system |
| `command_system/variable_registry.py` | Variable registry for linking components |
| `command_system/project.py` | Project model with command support |
| `command_system/hardware_manager.py` | Hardware integration via PyVISA |
| `command_system/workspace_manager.py` | Workspace tab management |
| `command_system/commands/__init__.py` | Command implementations package |
| `command_system/commands/signal_commands.py` | Signal operation commands |
| `command_system/commands/workspace_commands.py` | Workspace and dock operation commands |
| `command_system/commands/project_commands.py` | Project operation commands |
| `command_system/_usage_example.py` | Example application using commands |
| `command_system/_integration_template.py` | Template for integrating with existing code |
| `gui/main_window.py` | Main window implementation |
| `gui/dock_widgets/signal_viewer_dock.py` | Example dock widget implementation |
| `app.py` or `pysignaldecipher.py` | Main application class |

## Usage Examples

**File: `command_system/_usage_example.py`**

Demonstrates how to use the command system in PySignalDecipher:

1. Initialize the command system and related components
   ```python
   command_manager = CommandManager()
   variable_registry = command_manager.get_variable_registry()
   hardware_manager = command_manager.get_hardware_manager()
   workspace_manager = command_manager.get_workspace_manager()
   
   project = Project("Example Project")
   project.set_command_manager(command_manager)
   ```

2. Create and execute commands
   ```python
   signal = SignalData("My Signal")
   command = AddSignalCommand(project, signal)
   command_manager.execute_command(command)
   ```

3. Work with variables and links
   ```python
   # Create a variable
   variable = SignalVariable("amplitude", 1.0, "dock1")
   variable_registry.register_variable(variable)
   
   # Subscribe to changes
   variable.subscribe("ui_component", update_ui_callback)
   
   # Change value through command
   cmd = PropertyChangeCommand(variable, "value", 2.0)
   command_manager.execute_command(cmd)
   ```

4. Create dock widgets
   ```python
   # Create a dock widget
   workspace_id = workspace_manager.get_active_workspace_id()
   workspace = project.get_workspace_state(workspace_id)
   
   cmd = CreateDockCommand(workspace, "signal_viewer")
   dock_id = command_manager.execute_command(cmd)
   
   # Create a dock widget in the UI
   dock_widget = SignalViewerDock(dock_id, command_manager)
   main_window.add_dock_widget(dock_widget)
   ```

5. Connect to hardware
   ```python
   # Get available devices
   devices = hardware_manager.get_available_devices()
   
   # Connect to a device
   device_id = hardware_manager.connect_device(devices[0], "Oscilloscope")
   
   # Get device variables
   variables = variable_registry.get_variables_by_parent(device_id)
   ```

6. Save and load projects
   ```python
   # Save project
   project.save("my_project.psd")
   
   # Load project
   project = Project.load("my_project.psd", command_manager)
   ```

The usage example provides a complete demonstration of how to use the command system in the PySignalDecipher application.