"""
Command manager for coordinating command execution and history.
"""
from typing import List, Optional

from .command import Command


# MARK: - Command History

class CommandHistory:
    """
    Tracks command history for undo/redo operations.
    """
    
    def __init__(self):
        """Initialize empty command history."""
        self._executed_commands: List[Command] = []  # Stack of executed commands
        self._undone_commands: List[Command] = []    # Stack of undone commands
        
    def add_command(self, command: Command) -> None:
        """
        Add a command to the history.
        Clears the undone commands stack since a new command creates a new branch.
        """
        self._executed_commands.append(command)
        self._undone_commands.clear()  # Clear redo stack
        
    def undo(self) -> Optional[Command]:
        """
        Move the most recent command from executed to undone stack.
        
        Returns:
            The command that was undone, or None if no commands to undo
        """
        if not self._executed_commands:
            return None
            
        command = self._executed_commands.pop()
        self._undone_commands.append(command)
        return command
        
    def redo(self) -> Optional[Command]:
        """
        Move the most recently undone command back to the executed stack.
        
        Returns:
            The command that was redone, or None if no commands to redo
        """
        if not self._undone_commands:
            return None
            
        command = self._undone_commands.pop()
        self._executed_commands.append(command)
        return command
        
    def clear(self) -> None:
        """Clear both command stacks."""
        self._executed_commands.clear()
        self._undone_commands.clear()
        
    def can_undo(self) -> bool:
        """Check if there are commands that can be undone."""
        return len(self._executed_commands) > 0
        
    def can_redo(self) -> bool:
        """Check if there are commands that can be redone."""
        return len(self._undone_commands) > 0


# MARK: - Command Manager

class CommandManager:
    """
    Singleton manager for command execution and history tracking.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = CommandManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the command manager."""
        if CommandManager._instance is not None:
            raise RuntimeError("Use CommandManager.get_instance() to get the singleton instance")
            
        CommandManager._instance = self
        self._history = CommandHistory()
        self._is_updating = False  # Flag to prevent recursive command execution
    
    def execute(self, command: Command) -> bool:
        """
        Execute a command and add it to the history.
        
        Args:
            command: Command to execute
            
        Returns:
            True if command executed successfully
        """
        
        if self._is_updating:
            return True  # Skip if we're already processing a command
            
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
        """
        Undo the most recent command in the history.
        
        Returns:
            True if a command was undone
        """
        if self._is_updating:
            return False
            
        command = self._history.undo()
        if command:
            try:
                self._is_updating = True
                command.undo()
                return True
            except Exception as e:
                print(f"Error undoing command: {e}")
                # Re-add the command since undo failed
                self._history.redo()
                return False
            finally:
                self._is_updating = False
        return False
    
    def redo(self) -> bool:
        """
        Redo the most recently undone command.
        
        Returns:
            True if a command was redone
        """
        if self._is_updating:
            return False
            
        command = self._history.redo()
        if command:
            try:
                self._is_updating = True
                command.redo()
                return True
            except Exception as e:
                print(f"Error redoing command: {e}")
                # Remove the command since redo failed
                self._history.undo()
                return False
            finally:
                self._is_updating = False
        return False
    
    def clear(self) -> None:
        """Clear command history."""
        self._history.clear()
    
    def can_undo(self) -> bool:
        """Check if there are commands that can be undone."""
        return self._history.can_undo()
    
    def can_redo(self) -> bool:
        """Check if there are commands that can be redone."""
        return self._history.can_redo()
    
    def is_updating(self) -> bool:
        """Check if we're currently processing a command update."""
        return self._is_updating


def get_command_manager():
    """Get the singleton command manager instance."""
    return CommandManager.get_instance()