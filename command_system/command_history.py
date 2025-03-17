"""
Command history for PySignalDecipher.

This module provides the command history system for tracking command
execution and supporting undo/redo operations.
"""

from typing import List, Dict, Any, Optional
from .command import Command, CommandFactory


class CommandHistory:
    """
    Manages command history for undo/redo operations.
    
    Maintains an ordered list of executed commands and tracks
    the current position in the history.
    """
    
    def __init__(self):
        """Initialize a new command history."""
        self._history: List[Command] = []
        self._current_index: int = -1
        self._max_history_size: int = 100  # Limit history to prevent memory issues
    
    def execute_command(self, command: Command) -> None:
        """
        Execute a command and add it to the history.
        
        If we're not at the end of the history (i.e., commands have been
        undone), the undone commands will be discarded.
        
        Args:
            command: The command to execute
        """
        # Discard any redoable commands
        if self._current_index < len(self._history) - 1:
            self._history = self._history[:self._current_index + 1]
        
        # Execute the command
        command.execute()
        
        # Add to history
        self._history.append(command)
        self._current_index = len(self._history) - 1
        
        # Trim history if needed
        if len(self._history) > self._max_history_size:
            self._history = self._history[-self._max_history_size:]
            self._current_index = len(self._history) - 1
    
    def undo(self) -> bool:
        """
        Undo the last executed command.
        
        Returns:
            True if a command was undone, False otherwise
        """
        if not self.can_undo():
            return False
        
        self._history[self._current_index].undo()
        self._current_index -= 1
        return True
    
    def redo(self) -> bool:
        """
        Redo the last undone command.
        
        Returns:
            True if a command was redone, False otherwise
        """
        if not self.can_redo():
            return False
        
        self._current_index += 1
        self._history[self._current_index].redo()
        return True
    
    def can_undo(self) -> bool:
        """
        Check if there are commands that can be undone.
        
        Returns:
            True if undo is possible, False otherwise
        """
        return self._current_index >= 0
    
    def can_redo(self) -> bool:
        """
        Check if there are commands that can be redone.
        
        Returns:
            True if redo is possible, False otherwise
        """
        return self._current_index < len(self._history) - 1
    
    def clear(self) -> None:
        """Clear the command history."""
        self._history = []
        self._current_index = -1
    
    def get_serializable_history(self) -> List[Dict[str, Any]]:
        """
        Get a serializable representation of the command history.
        
        Returns:
            A list of serialized commands
        """
        return [
            {
                "type": command.__class__.__name__,
                "state": command.get_state()
            }
            for command in self._history
        ]
    
    @classmethod
    def from_serialized_history(cls, history_data: List[Dict[str, Any]]) -> 'CommandHistory':
        """
        Create a command history from serialized data.
        
        Args:
            history_data: List of serialized commands
            
        Returns:
            A new CommandHistory instance
        """
        history = cls()
        
        for command_data in history_data:
            command = CommandFactory.create_from_state(
                command_data["type"],
                command_data["state"]
            )
            if command:
                # Add to history without executing
                history._history.append(command)
        
        if history._history:
            history._current_index = len(history._history) - 1
        
        return history
    
    def get_history_size(self) -> int:
        """
        Get the number of commands in the history.
        
        Returns:
            The number of commands
        """
        return len(self._history)
    
    def get_current_index(self) -> int:
        """
        Get the current position in the history.
        
        Returns:
            The current index
        """
        return self._current_index
    
    def set_max_history_size(self, size: int) -> None:
        """
        Set the maximum number of commands to keep in history.
        
        Args:
            size: Maximum history size
        """
        if size < 1:
            raise ValueError("History size must be at least 1")
        
        self._max_history_size = size
        
        # Trim history if it exceeds the new size
        if len(self._history) > self._max_history_size:
            excess = len(self._history) - self._max_history_size
            self._history = self._history[excess:]
            self._current_index = max(0, self._current_index - excess)
    
    def get_max_history_size(self) -> int:
        """
        Get the maximum history size.
        
        Returns:
            The maximum number of commands in history
        """
        return self._max_history_size