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
   - [Project Model](#project-model)
4. [Command Implementations](#command-implementations)
   - [Signal Commands](#signal-commands)
   - [Workspace Commands](#workspace-commands)
   - [Project Commands](#project-commands)
5. [Integration Guide](#integration-guide)
6. [File Reference](#file-reference)
7. [Usage Examples](#usage-examples)

## Overview

The command system provides a robust foundation for history tracking (undo/redo), project serialization, and state management in PySignalDecipher. It follows the Command pattern, where all user actions that modify state are encapsulated as commands that can be executed, undone, and redone. The system also provides observable properties for tracking state changes and a comprehensive project model for serialization.

## Architecture

The command system is organized into several key components:

```
┌──────────────────────────────────────┐
│            User Interface            │
│                                      │
│  ┌────────────┐    ┌──────────────┐  │
│  │ UI Actions │───▶│ Command Exec │  │
│  └────────────┘    └──────────────┘  │
└──────────────────────┬───────────────┘
                       │
                       ▼
┌──────────────────────────────────────┐
│            Command System            │
│                                      │
│  ┌────────────┐    ┌──────────────┐  │
│  │ Commands   │──▶ │    History   │  │
│  └────────────┘    └──────────────┘  │
│                          │           │
│  ┌────────────┐    ┌─────▼────────┐  │
│  │ Observable │◀───┤ State Changes│  │
│  │ Properties │    └──────────────┘  │
│  └─────┬──────┘                      │
└─────────┼─────────────────────────────┘
          │
          ▼
┌─────────┴──────────────────────────────┐
│            Project Model               │
│                                        │
│  ┌───────────┐     ┌────────────────┐  │
│  │  Signals  │     │   Workspaces   │  │
│  └───────────┘     └────────────────┘  │
│                                        │
│  ┌───────────────────────────────────┐ │
│  │       Serialization Layer         │ │
│  └───────────────────────────────────┘ │
└────────────────────┬───────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │  Project File │
            │  (.psd format)│
            └───────────────┘
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

Provides a centralized interface for executing commands and managing command history:

- `CommandManager`: Central point for command execution and history management
  - `execute_command()`: Executes a command and adds it to history
  - `undo()/redo()`: Undoes/redoes commands through history
  - `can_undo()/can_redo()`: Checks if undo/redo is possible
  - `register_command()`: Registers a command type with the factory
  - `register_history_observers()`: Registers callbacks for undo/redo state changes
  - Signal handling for command execution events:
    - `command_executed`: Emitted when a command is executed
    - `command_undone`: Emitted when a command is undone
    - `command_redone`: Emitted when a command is redone
    - `history_changed`: Emitted when history state changes

The CommandManager acts as a facade for the command system, providing a simple interface for UI components.

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

Observable properties provide the foundation for tracking state changes and integrating with the command system.

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

## Integration Guide

**File: `command_system/integration_template.py`**

Provides templates and examples for integrating the command system with PySignalDecipher:

1. Update `ServiceRegistry` to include CommandManager
2. Update `main.py` to initialize the command system
3. Create signal models that extend Observable
4. Update UI code to use commands for state changes
5. Implement project saving and loading
6. Add undo/redo actions to menus and toolbars
7. Implement command-based menu action handlers
8. Extend Observable for workspace state

The integration guide provides step-by-step instructions for incorporating the command system into the existing codebase.

## File Reference

| File | Description |
|------|-------------|
| `command_system/__init__.py` | Package exports and initialization |
| `command_system/command.py` | Command interface and factory |
| `command_system/command_history.py` | Undo/redo stack management |
| `command_system/command_manager.py` | Central command execution point |
| `command_system/observable.py` | Observable property system |
| `command_system/project.py` | Project model with command support |
| `command_system/commands/__init__.py` | Command implementations package |
| `command_system/commands/signal_commands.py` | Signal operation commands |
| `command_system/commands/workspace_commands.py` | Workspace operation commands |
| `command_system/commands/project_commands.py` | Project operation commands |
| `command_system/usage_example.py` | Example application using commands |
| `command_system/integration_template.py` | Template for integrating with existing code |

## Usage Examples

**File: `command_system/usage_example.py`**

Demonstrates how to use the command system in a simple application:

1. Initialize the command system and project
   ```python
   command_manager = CommandManager()
   project = Project("Example Project")
   project.set_command_manager(command_manager)
   ```

2. Create and execute commands
   ```python
   signal = SignalData("My Signal")
   command = AddSignalCommand(project, signal)
   command_manager.execute_command(command)
   ```

3. Undo and redo commands
   ```python
   command_manager.undo()  # Undo the last command
   command_manager.redo()  # Redo the undone command
   ```

4. Register for history state changes
   ```python
   command_manager.register_history_observers(
       lambda can_undo: update_undo_button(can_undo),
       lambda can_redo: update_redo_button(can_redo)
   )
   ```

5. Save and load projects
   ```python
   # Save project
   project.save("my_project.psd")
   
   # Load project
   project = Project.load("my_project.psd", command_manager)
   ```

The usage example provides a complete demonstration of how to use the command system in an application.