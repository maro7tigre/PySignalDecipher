"""
Command manager for coordinating command execution and history.

This module provides the command manager and history tracking system
that serves as the central hub for command execution and undo/redo operations.
Uses the ID system for tracking dependencies between commands and widgets.
"""
from typing import List, Optional, Dict, Callable, Any
import uuid

from .command import Command
from ..id_system import get_id_registry
from ..id_system.core.mapping import Mapping

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
        
    def get_executed_commands(self) -> List[Command]:
        """
        Get list of executed commands (for debugging/inspection).
        
        Returns:
            List of executed commands
        """
        return self._executed_commands.copy()
        
    def get_undone_commands(self) -> List[Command]:
        """
        Get list of undone commands (for debugging/inspection).
        
        Returns:
            List of undone commands
        """
        return self._undone_commands.copy()

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
            raise RuntimeError("Use get_command_manager() to get the singleton instance")
            
        CommandManager._instance = self
        self._history = CommandHistory()
        self._is_updating = False  # Flag to prevent recursive command execution
        self._is_initializing = False  # Flag to disable history tracking during init
        
        # Get the ID registry
        self.id_registry = get_id_registry()
        
        # Command lifecycle callbacks using Mapping class
        self._before_execute_callbacks = Mapping(update_keys=True, update_values=False)
        self.id_registry.mappings.append(self._before_execute_callbacks)
        
        self._after_execute_callbacks = Mapping(update_keys=True, update_values=False)
        self.id_registry.mappings.append(self._after_execute_callbacks)
        
        self._before_undo_callbacks = Mapping(update_keys=True, update_values=False)
        self.id_registry.mappings.append(self._before_undo_callbacks)
        
        self._after_undo_callbacks = Mapping(update_keys=True, update_values=False)
        self.id_registry.mappings.append(self._after_undo_callbacks)
    
    def execute(self, command: Command, trigger_widget_id: Optional[str] = None) -> bool:
        """
        Execute a command and add it to the history.
        
        Args:
            command: Command to execute
            trigger_widget_id: Optional ID of widget that triggered the command
            
        Returns:
            True if command executed successfully
        """
        
        if self._is_updating or command is None:
            return True
            
        # Set trigger widget if provided
        if trigger_widget_id:
            command.set_trigger_widget(trigger_widget_id)
            
        try:
            self._is_updating = True
            
            # Call before execute callbacks
            for callback_id in self._before_execute_callbacks:
                callback = self._before_execute_callbacks.get(callback_id)
                if callback:
                    callback(command)
            
            command.execute()
            
            # Only add to history if not in initialization mode
            if not self._is_initializing:
                self._history.add_command(command)
                
            # Call after execute callbacks
            for callback_id in self._after_execute_callbacks:
                callback = self._after_execute_callbacks.get(callback_id)
                if callback:
                    callback(command, True)
                
            return True
        except Exception as e:
            print(f"Error executing command: {e}")
            
            # Call after execute callbacks with failure
            for callback_id in self._after_execute_callbacks:
                callback = self._after_execute_callbacks.get(callback_id)
                if callback:
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
                
                # Navigate to command context if available
                self._navigate_to_command_context(command)
                # Call before undo callbacks
                for callback_id in self._before_undo_callbacks:
                    callback = self._before_undo_callbacks.get(callback_id)
                    if callback:
                        callback(command)
                
                command.undo()
                
                # Call after undo callbacks
                for callback_id in self._after_undo_callbacks:
                    callback = self._after_undo_callbacks.get(callback_id)
                    if callback:
                        callback(command, True)
                
                return True
            except Exception as e:
                print(f"Error undoing command: {e}")
                
                # Call after undo callbacks with failure
                for callback_id in self._after_undo_callbacks:
                    callback = self._after_undo_callbacks.get(callback_id)
                    if callback:
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
                
                # Navigate to command context if available
                self._navigate_to_command_context(command)
                # Call before execute callbacks (same as execute)
                for callback_id in self._before_execute_callbacks:
                    callback = self._before_execute_callbacks.get(callback_id)
                    if callback:
                        callback(command)
                
                command.redo()
                
                # Call after execute callbacks (same as execute)
                for callback_id in self._after_execute_callbacks:
                    callback = self._after_execute_callbacks.get(callback_id)
                    if callback:
                        callback(command, True)
                
                return True
            except Exception as e:
                print(f"Error redoing command: {e}")
                
                # Call after execute callbacks with failure
                for callback_id in self._after_execute_callbacks:
                    callback = self._after_execute_callbacks.get(callback_id)
                    if callback:
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

    def _navigate_to_command_context(self, command: Command) -> None:
        """
        Navigate to the UI context where the command was created using ID system.
        
        Args:
            command: Command containing execution context
        """
        if not command or not command.trigger_widget_id:
            return False
            
        # Get the trigger widget ID
        trigger_widget_id = command.trigger_widget_id
        # Get the container 
        id_registry = self.id_registry
        container_id = id_registry.get_container_id_from_widget_id(trigger_widget_id)
        if not container_id or container_id == "0":
            trigger_widget = id_registry.get_widget(trigger_widget_id)
            trigger_widget.setFocus()
            return True
            
        container = id_registry.get_widget(container_id)
        if container and hasattr(container, 'navigate_to_widget'):
            # Navigate to this container first
            container.navigate_to_widget(trigger_widget_id)
        else:
            parent_container_id = id_registry.get_container_id_from_widget_id(container_id)
            parent_container = id_registry.get_widget(parent_container_id) if parent_container_id else None
            if parent_container and hasattr(parent_container, 'navigate_to_widget'):
                parent_container.navigate_to_widget(container_id)        
                
        
        return True

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
        self._before_execute_callbacks.delete(callback_id)
        self._after_execute_callbacks.delete(callback_id)
        self._before_undo_callbacks.delete(callback_id)
        self._after_undo_callbacks.delete(callback_id)
        
    def __del__(self):
        """Clean up mappings from the ID registry."""
        try:
            if hasattr(self, 'id_registry') and hasattr(self.id_registry, 'mappings'):
                if self._before_execute_callbacks in self.id_registry.mappings:
                    self.id_registry.mappings.remove(self._before_execute_callbacks)
                if self._after_execute_callbacks in self.id_registry.mappings:
                    self.id_registry.mappings.remove(self._after_execute_callbacks)
                if self._before_undo_callbacks in self.id_registry.mappings:
                    self.id_registry.mappings.remove(self._before_undo_callbacks)
                if self._after_undo_callbacks in self.id_registry.mappings:
                    self.id_registry.mappings.remove(self._after_undo_callbacks)
        except:
            pass  # Ignore errors during cleanup

def get_command_manager():
    """
    Get the singleton command manager instance.
    
    Returns:
        CommandManager singleton instance
    """
    return CommandManager.get_instance()