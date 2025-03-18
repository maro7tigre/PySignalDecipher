"""
Command manager for PySignalDecipher.

This module provides the central command manager that coordinates
command execution, history, and handles command-related events.
"""

from typing import Dict, Type, Optional, List, Any, Callable
from PySide6.QtCore import QObject, Signal

from .command import Command, CommandFactory
from .command_history import CommandHistory
from .variable_registry import VariableRegistry
from .hardware_manager import HardwareManager
from .workspace_manager import WorkspaceTabManager

class CommandManager(QObject):
    """
    Central manager for the command system.
    
    Coordinates command execution, history, and provides signals
    for command-related events to update the UI.
    """
    
    # Signals
    command_executed = Signal(object)  # Emitted when a command is executed
    command_undone = Signal(object)    # Emitted when a command is undone
    command_redone = Signal(object)    # Emitted when a command is redone
    history_changed = Signal()         # Emitted when the history state changes
    
    def __init__(self):
        """Initialize the command manager."""
        super().__init__()
        
        self._command_history = CommandHistory()
        self._active_project = None  # Will be set later
        
        # Register for internal signals
        self.command_executed.connect(self._on_history_change)
        self.command_undone.connect(self._on_history_change)
        self.command_redone.connect(self._on_history_change)
        
        # New components
        self._variable_registry = VariableRegistry()
        self._hardware_manager = HardwareManager(self._variable_registry)
        self._workspace_manager = WorkspaceTabManager(self, self._variable_registry)
    
    def register_command(self, command_class: Type[Command]) -> None:
        """
        Register a command class with the command factory.
        
        Args:
            command_class: The command class to register
        """
        CommandFactory.register(command_class)
    
    def execute_command(self, command: Command) -> None:
        """
        Execute a command and add it to the history.
        
        Args:
            command: The command to execute
        """
        self._command_history.execute_command(command)
        self.command_executed.emit(command)
    
    def undo(self) -> bool:
        """
        Undo the last command.
        
        Returns:
            True if a command was undone, False otherwise
        """
        if self._command_history.undo():
            self.command_undone.emit(None)  # We could pass the undone command here if needed
            return True
        return False
    
    def redo(self) -> bool:
        """
        Redo the last undone command.
        
        Returns:
            True if a command was redone, False otherwise
        """
        if self._command_history.redo():
            self.command_redone.emit(None)  # We could pass the redone command here if needed
            return True
        return False
    
    def can_undo(self) -> bool:
        """
        Check if undo is possible.
        
        Returns:
            True if undo is possible, False otherwise
        """
        return self._command_history.can_undo()
    
    def can_redo(self) -> bool:
        """
        Check if redo is possible.
        
        Returns:
            True if redo is possible, False otherwise
        """
        return self._command_history.can_redo()
    
    def clear_history(self) -> None:
        """Clear the command history."""
        self._command_history.clear()
        self.history_changed.emit()
    
    def set_active_project(self, project) -> None:
        """
        Set the active project.
        
        Args:
            project: The project to set as active
        """
        self._active_project = project
    
    def get_active_project(self):
        """
        Get the active project.
        
        Returns:
            The active project or None
        """
        return self._active_project
    
    def _on_history_change(self, _=None) -> None:
        """
        Handle history state changes.
        
        Args:
            _: Ignored parameter (command object from signal)
        """
        self.history_changed.emit()
    
    def get_serializable_history(self) -> List[Dict[str, Any]]:
        """
        Get a serializable representation of the command history.
        
        Returns:
            A list of serialized commands
        """
        return self._command_history.get_serializable_history()
    
    def restore_history_from_serialized(self, history_data: List[Dict[str, Any]]) -> None:
        """
        Restore command history from serialized data.
        
        Args:
            history_data: Serialized command history
        """
        self._command_history = CommandHistory.from_serialized_history(history_data)
        self.history_changed.emit()
    
    def register_history_observers(self, 
                                  can_undo_changed: Callable[[bool], None],
                                  can_redo_changed: Callable[[bool], None]) -> None:
        """
        Register callbacks for undo/redo state changes.
        
        Args:
            can_undo_changed: Callback for undo state changes
            can_redo_changed: Callback for redo state changes
        """
        def update_states():
            can_undo_changed(self.can_undo())
            can_redo_changed(self.can_redo())
        
        self.history_changed.connect(update_states)
        update_states()  # Initial update
        
    def get_variable_registry(self):
        return self._variable_registry
        
    def get_hardware_manager(self):
        return self._hardware_manager
        
    def get_workspace_manager(self):
        return self._workspace_manager