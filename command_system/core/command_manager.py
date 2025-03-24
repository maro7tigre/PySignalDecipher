"""
Command manager for coordinating command execution and history.

This module provides the command manager and history tracking system
that serves as the central hub for command execution and undo/redo operations.
"""
from typing import List, Optional, Dict, Callable, Any

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
        
        Args:
            command: Command to add to history
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
        """
        Check if there are commands that can be undone.
        
        Returns:
            True if there are commands in the executed stack
        """
        return len(self._executed_commands) > 0
        
    def can_redo(self) -> bool:
        """
        Check if there are commands that can be redone.
        
        Returns:
            True if there are commands in the undone stack
        """
        return len(self._undone_commands) > 0

# MARK: - Command Manager
class CommandManager:
    """
    Singleton manager for command execution and history tracking.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance.
        
        Returns:
            CommandManager singleton instance
        """
        if cls._instance is None:
            cls._instance = CommandManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the command manager."""
        if CommandManager._instance is not None:
            raise RuntimeError("You can't have multiple instances of CommandManager, Import and Use get_command_manager() to get the singleton instance")
            
        CommandManager._instance = self
        self._history = CommandHistory()
        self._is_updating = False  # Flag to prevent recursive command execution
        self._is_initializing = False  # Flag to disable history tracking during init
        
        # Command lifecycle callbacks
        self._before_execute_callbacks: Dict[str, Callable[[Command], None]] = {}
        self._after_execute_callbacks: Dict[str, Callable[[Command, bool], None]] = {}
        self._before_undo_callbacks: Dict[str, Callable[[Command], None]] = {}
        self._after_undo_callbacks: Dict[str, Callable[[Command, bool], None]] = {}
    
    def execute(self, command: Command) -> bool:
        """
        Execute a command and add it to the history.
        
        Args:
            command: Command to execute
            
        Returns:
            True if command executed successfully
        """
        
        if self._is_updating:
            return True  # Skip if we're already processing a command ? TODO: indicate that the command was skipped ?
            
        try:
            self._is_updating = True
            
            # Call before execute callbacks
            for callback in self._before_execute_callbacks.values():
                callback(command)
            
            # Only add to history if not in initialization mode
            if not self._is_initializing:
                self._history.add_command(command)
                
            command.execute()
            
            # Call after execute callbacks
            for callback in self._after_execute_callbacks.values():
                callback(command, True)
                
            return True
        except Exception as e:
            print(f"Error executing command: {e}")
            
            # Call after execute callbacks with failure
            for callback in self._after_execute_callbacks.values():
                callback(command, False)
                
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
                
                # Call before undo callbacks
                for callback in self._before_undo_callbacks.values():
                    callback(command)
                
                command.undo()
                
                # Call after undo callbacks
                for callback in self._after_undo_callbacks.values():
                    callback(command, True)
                
                return True
            except Exception as e:
                print(f"Error undoing command: {e}")
                
                # Call after undo callbacks with failure
                for callback in self._after_undo_callbacks.values():
                    callback(command, False)
                
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
                
                # Call before execute callbacks (same as execute)
                for callback in self._before_execute_callbacks.values():
                    callback(command)
                
                command.redo()
                
                # Call after execute callbacks (same as execute)
                for callback in self._after_execute_callbacks.values():
                    callback(command, True)
                
                return True
            except Exception as e:
                print(f"Error redoing command: {e}")
                
                # Call after execute callbacks with failure
                for callback in self._after_execute_callbacks.values():
                    callback(command, False)
                
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
        """
        Check if there are commands that can be undone.
        
        Returns:
            True if undo is available
        """
        return self._history.can_undo()
    
    def can_redo(self) -> bool:
        """
        Check if there are commands that can be redone.
        
        Returns:
            True if redo is available
        """
        return self._history.can_redo()
    
    def is_updating(self) -> bool:
        """
        Check if we're currently processing a command update.
        
        Returns:
            True if a command is being processed
        """
        return self._is_updating
    
    def begin_init(self):
        """
        Begin initialization - temporarily disable command tracking.
        Commands will be executed but not added to history.
        """
        self._is_initializing = True
        
    def end_init(self):
        """
        End initialization - re-enable command tracking.
        """
        self._is_initializing = False
        
    def add_before_execute_callback(self, callback_id: str, 
                                   callback: Callable[[Command], None]) -> None:
        """
        Add a callback to be called before a command is executed.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call before command execution
        """
        self._before_execute_callbacks[callback_id] = callback
        
    def add_after_execute_callback(self, callback_id: str, 
                                  callback: Callable[[Command, bool], None]) -> None:
        """
        Add a callback to be called after a command is executed.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call after command execution
                      Receives command and success flag
        """
        self._after_execute_callbacks[callback_id] = callback
        
    def add_before_undo_callback(self, callback_id: str, 
                                callback: Callable[[Command], None]) -> None:
        """
        Add a callback to be called before a command is undone.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call before command undo
        """
        self._before_undo_callbacks[callback_id] = callback
        
    def add_after_undo_callback(self, callback_id: str, 
                               callback: Callable[[Command, bool], None]) -> None:
        """
        Add a callback to be called after a command is undone.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call after command undo
                      Receives command and success flag
        """
        self._after_undo_callbacks[callback_id] = callback
        
    def remove_callback(self, callback_id: str) -> None:
        """
        Remove a callback by ID.
        
        Args:
            callback_id: ID of the callback to remove
        """
        if callback_id in self._before_execute_callbacks:
            del self._before_execute_callbacks[callback_id]
        if callback_id in self._after_execute_callbacks:
            del self._after_execute_callbacks[callback_id]
        if callback_id in self._before_undo_callbacks:
            del self._before_undo_callbacks[callback_id]
        if callback_id in self._after_undo_callbacks:
            del self._after_undo_callbacks[callback_id]
            
    # TODO: Add serialization integration hooks
    # 1. Add hooks for serialization events (save/load)
    # 2. Support for command batching
    # 3. Serialize/deserialize command history if needed


def get_command_manager():
    """
    Get the singleton command manager instance.
    
    Returns:
        CommandManager singleton instance
    """
    return CommandManager.get_instance()