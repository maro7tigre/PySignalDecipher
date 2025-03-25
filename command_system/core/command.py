"""
Command pattern implementation for undo/redo functionality.

This module provides a clean implementation of the command pattern
for action encapsulation and history tracking.
"""
from abc import ABC, abstractmethod
from typing import List, Any, Optional, TypeVar, Dict


# Type for command targets
T = TypeVar('T')

# MARK: - Command
class Command(ABC):
    """
    Abstract base class for all commands.
    Commands encapsulate actions that can be executed, undone, and redone.
    """
    
    def __init__(self):
        """Initialize the command."""
        self._execution_context = None
        
    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass
        
    @abstractmethod
    def undo(self) -> None:
        """Undo the command."""
        pass
        
    def redo(self) -> None:
        """Redo the command. Default implementation is to call execute again."""
        self.execute()
        
    def set_execution_context(self, context: dict) -> None:
        """Set the widget context that created this command."""
        self._execution_context = context
        
    def get_execution_context(self) -> dict:
        """Get the widget context that created this command."""
        return self._execution_context

# MARK: - Concrete Commands
class CompoundCommand(Command):
    """
    A command that groups multiple commands together.
    All commands in the group are executed, undone, and redone as a unit.
    """
    
    def __init__(self, name: str = "Compound Command"):
        """
        Initialize a new compound command.
        
        Args:
            name: Human-readable name for the command
        """
        self.name = name
        self.commands: List[Command] = []
        
    def add_command(self, command: Command) -> None:
        """
        Add a command to the compound.
        
        Args:
            command: Command to add
        """
        self.commands.append(command)
        
    def execute(self) -> None:
        """Execute all commands in order."""
        for command in self.commands:
            command.execute()
            
    def undo(self) -> None:
        """Undo all commands in reverse order."""
        for command in reversed(self.commands):
            command.undo()
            
    def is_empty(self) -> bool:
        """
        Check if compound command is empty.
        
        Returns:
            True if no commands have been added, False otherwise
        """
        return len(self.commands) == 0

# MARK: - Property Commands
class PropertyCommand(Command):
    """Command for changing a property on an observable object."""
    
    def __init__(self, target: Any, property_name: str, new_value: Any):
        """
        Initialize a property change command.
        
        Args:
            target: Target observable object
            property_name: Name of property to change
            new_value: New property value
        """
        self.target = target
        self.property_name = property_name
        self.new_value = new_value
        self.old_value = getattr(target, property_name)
        
    def execute(self) -> None:
        """Execute the command by setting the new property value."""
        setattr(self.target, self.property_name, self.new_value)
        
    def undo(self) -> None:
        """Undo the command by restoring the old property value."""
        setattr(self.target, self.property_name, self.old_value)

# MARK: - MacroCommand
class MacroCommand(CompoundCommand):
    """
    A specialized compound command that represents a user-level action.
    Used for grouping related commands with a describtion of the action.
    """
    
    def __init__(self, name: str):
        """
        Initialize a new macro command.
        
        Args:
            name: Descriptive name for the macro command
        """
        super().__init__(name)
        self.description = name
        
    def set_description(self, description: str) -> None:
        """
        Set a human-readable description for this command.
        
        Args:
            description: Command description
        """
        self.description = description
        
    def get_description(self) -> str:
        """
        Get the human-readable description of this command.
        
        Returns:
            Command description
        """
        return self.description