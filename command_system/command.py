"""
Command pattern implementation for undo/redo functionality.
"""
from abc import ABC, abstractmethod
from typing import List


# MARK: - Command Classes

class Command(ABC):
    """
    Abstract base class for all commands.
    Commands encapsulate actions that can be executed, undone, and redone.
    """
    
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


class CompoundCommand(Command):
    """
    A command that groups multiple commands together.
    All commands in the group are executed, undone, and redone as a unit.
    """
    
    def __init__(self, name: str = "Compound Command"):
        """Initialize a new compound command."""
        self.name = name
        self.commands: List[Command] = []
        
    def add_command(self, command: Command) -> None:
        """Add a command to the compound."""
        self.commands.append(command)
        
    def execute(self) -> None:
        """Execute all commands in order."""
        for command in self.commands:
            command.execute()
            
    def undo(self) -> None:
        """Undo all commands in reverse order."""
        for command in reversed(self.commands):
            command.undo()


class PropertyCommand(Command):
    """Command for changing a property on an observable object."""
    
    def __init__(self, target, property_name: str, new_value):
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