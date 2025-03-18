"""
Command base class for PySignalDecipher.

This module provides the foundation for the command system,
including the base Command class, CommandContext, and related interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar, Generic, List, Set

T = TypeVar('T')  # Generic type for services


class CommandContext:
    """
    Context for command execution.
    
    Provides access to the command manager, active project, and other
    contextual information needed by commands.
    """
    
    def __init__(self, manager=None):
        """
        Initialize the command context.
        
        Args:
            manager: The command manager instance (defaults to singleton)
        """
        # Import here to avoid circular import
        from .command_manager import CommandManager
        self.manager = manager or CommandManager.instance()
        self.active_project = self.manager.get_active_project()
        self.active_workspace = None
        self.parameters = {}  # Additional parameters that may be needed
    
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service from the command manager.
        
        Args:
            service_type: Type of service to retrieve
            
        Returns:
            The service instance
        """
        return self.manager.get_service(service_type)
    
    def add_parameter(self, key: str, value: Any) -> None:
        """
        Add a parameter to the context.
        
        Args:
            key: Parameter name
            value: Parameter value
        """
        self.parameters[key] = value
        
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        Get a parameter from the context.
        
        Args:
            key: Parameter name
            default: Default value if parameter doesn't exist
            
        Returns:
            The parameter value or default
        """
        return self.parameters.get(key, default)


class Command(ABC):
    """
    Base class for all commands in the system.
    
    Commands encapsulate user actions and state changes, allowing for
    undo/redo functionality and project serialization.
    """
    
    def __init__(self, context: Optional[CommandContext] = None):
        """
        Initialize the command.
        
        Args:
            context: Command execution context (optional)
        """
        self.context = context
        
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service from the command context.
        
        Args:
            service_type: Type of service to retrieve
            
        Returns:
            The service instance
            
        Raises:
            AttributeError: If the command has no context
        """
        if self.context is None:
            raise AttributeError("Command has no context")
        
        return self.context.get_service(service_type)
    
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
    Factory for creating commands from serialized state or by type.
    
    Maintains a registry of command types that can be instantiated
    by name, class, or from serialized representation.
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
    def create_from_state(cls, command_type: str, state: Dict[str, Any], 
                         context: Optional[CommandContext] = None) -> Optional[Command]:
        """
        Create a command instance from its type and serialized state.
        
        Args:
            command_type: The name of the command class
            state: The serialized state of the command
            context: Optional command context to use
            
        Returns:
            A new command instance, or None if the type is not registered
        """
        if command_type in cls._registry:
            cmd = cls._registry[command_type].from_state(state)
            if cmd and context:
                cmd.context = context
            return cmd
        return None
    
    @classmethod
    def create(cls, command_type: Type[Command], context: Optional[CommandContext] = None, 
              **kwargs) -> Command:
        """
        Create a command instance by type with parameters.
        
        Args:
            command_type: The command class to create
            context: Optional command context to use
            **kwargs: Parameters to pass to the command constructor
            
        Returns:
            A new command instance
            
        Raises:
            ValueError: If the command type is not registered
        """
        if command_type.__name__ not in cls._registry:
            raise ValueError(f"Command type {command_type.__name__} is not registered")
        
        if context is None:
            # Import here to avoid circular import
            from .command_manager import CommandManager
            context = CommandContext(CommandManager.instance())
            
        return command_type(context, **kwargs)
    
    @classmethod
    def create_property_change(cls, target: Any, property_name: str, 
                              new_value: Any, context: Optional[CommandContext] = None) -> Command:
        """
        Convenience factory method for property change commands.
        
        Args:
            target: Object to change property on
            property_name: Name of the property to change
            new_value: New value for the property
            context: Optional command context to use
            
        Returns:
            A PropertyChangeCommand instance
        """
        from .observable import PropertyChangeCommand
        
        if context is None:
            # Import here to avoid circular import
            from .command_manager import CommandManager
            context = CommandContext(CommandManager.instance())
            
        return PropertyChangeCommand(context, target, property_name, new_value)


class CompoundCommand(Command):
    """
    A command that groups multiple commands together as a single unit.
    
    Useful for operations that involve multiple steps but should be
    treated as a single action for undo/redo purposes.
    """
    
    def __init__(self, name: str, context: Optional[CommandContext] = None, 
                commands: List[Command] = None):
        """
        Initialize the compound command.
        
        Args:
            name: A descriptive name for the command group
            context: Command execution context
            commands: Optional list of commands to include
        """
        super().__init__(context)
        self.name = name
        self.commands = commands or []
    
    def add_command(self, command: Command) -> None:
        """
        Add a command to the group.
        
        Args:
            command: Command to add
        """
        if command.context is None and self.context is not None:
            command.context = self.context
        
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