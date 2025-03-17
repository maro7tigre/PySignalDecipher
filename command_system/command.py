"""
Command base class for PySignalDecipher.

This module provides the foundation for the command system,
including the base Command class and related interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type


class Command(ABC):
    """
    Base class for all commands in the system.
    
    Commands encapsulate user actions and state changes, allowing for
    undo/redo functionality and project serialization.
    """
    
    @abstractmethod
    def execute(self) -> None:
        """
        Execute the command.
        
        This method performs the command's action and should store
        any state needed for undo operations.
        """
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """
        Undo the command.
        
        This method reverts the effects of the command's execution.
        """
        pass
    
    def redo(self) -> None:
        """
        Redo the command.
        
        By default, this simply executes the command again.
        Override if a different behavior is needed.
        """
        self.execute()
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            A dictionary containing the command's state that can be
            serialized to JSON or another format.
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_state(cls, state: Dict[str, Any]) -> 'Command':
        """
        Reconstruct a command from its serialized state.
        
        Args:
            state: The previously serialized state from get_state()
            
        Returns:
            A new command instance with the reconstructed state
        """
        pass


class CommandFactory:
    """
    Factory for creating commands from serialized state.
    
    Maintains a registry of command types that can be instantiated
    from their serialized representation.
    """
    
    _registry: Dict[str, Type[Command]] = {}
    
    @classmethod
    def register(cls, command_class: Type[Command]) -> None:
        """
        Register a command class.
        
        Args:
            command_class: The command class to register
        """
        cls._registry[command_class.__name__] = command_class
    
    @classmethod
    def create_from_state(cls, command_type: str, state: Dict[str, Any]) -> Optional[Command]:
        """
        Create a command instance from its type and serialized state.
        
        Args:
            command_type: The name of the command class
            state: The serialized state of the command
            
        Returns:
            A new command instance, or None if the type is not registered
        """
        if command_type in cls._registry:
            return cls._registry[command_type].from_state(state)
        return None


class CompoundCommand(Command):
    """
    A command that groups multiple commands together as a single unit.
    
    Useful for operations that involve multiple steps but should be
    treated as a single action for undo/redo purposes.
    """
    
    def __init__(self, name: str, commands: list[Command] = None):
        """
        Initialize the compound command.
        
        Args:
            name: A descriptive name for the command group
            commands: Optional list of commands to include
        """
        self.name = name
        self.commands = commands or []
    
    def add_command(self, command: Command) -> None:
        """
        Add a command to the group.
        
        Args:
            command: Command to add
        """
        self.commands.append(command)
    
    def execute(self) -> None:
        """
        Execute all commands in the group.
        """
        for command in self.commands:
            command.execute()
    
    def undo(self) -> None:
        """
        Undo all commands in the group in reverse order.
        """
        for command in reversed(self.commands):
            command.undo()
    
    def redo(self) -> None:
        """
        Redo all commands in the group in the original order.
        """
        for command in self.commands:
            command.redo()
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the serialized state of the compound command.
        
        Returns:
            A dictionary with the command's state
        """
        return {
            "name": self.name,
            "commands": [
                {
                    "type": cmd.__class__.__name__,
                    "state": cmd.get_state()
                }
                for cmd in self.commands
            ]
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'CompoundCommand':
        """
        Create a compound command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            A new CompoundCommand instance
        """
        cmd = cls(state["name"])
        
        for command_data in state.get("commands", []):
            command = CommandFactory.create_from_state(
                command_data["type"], 
                command_data["state"]
            )
            if command:
                cmd.add_command(command)
        
        return cmd