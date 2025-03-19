"""
Command pattern implementation for undo/redo functionality.
"""
from abc import ABC, abstractmethod


class Command(ABC):
    """
    Abstract base class for all commands.
    Commands encapsulate actions that can be executed, undone, and redone.
    """
    
    @abstractmethod
    def execute(self):
        """
        Execute the command.
        Should perform the action and store any state needed for undo.
        """
        pass
        
    @abstractmethod
    def undo(self):
        """
        Undo the command.
        Should restore the state to what it was before execute was called.
        """
        pass
        
    def redo(self):
        """
        Redo the command.
        Default implementation is to call execute again.
        """
        self.execute()
        
    @abstractmethod
    def serialize(self):
        """
        Convert command to serializable state.
        
        Returns:
            dict: Serialized command state
        """
        pass
        
    @classmethod
    @abstractmethod
    def deserialize(cls, state, registry):
        """
        Create command from serialized state.
        
        Args:
            state (dict): Serialized command state
            registry: Object registry for resolving references
            
        Returns:
            Command: Reconstructed command
        """
        pass


class CompoundCommand(Command):
    """
    A command that groups multiple commands together.
    All commands in the group are executed, undone, and redone as a unit.
    """
    
    def __init__(self, name="Compound Command"):
        """
        Initialize a new compound command.
        
        Args:
            name (str): Name of the compound command
        """
        self.name = name
        self.commands = []
        
    def add_command(self, command):
        """
        Add a command to the compound.
        
        Args:
            command (Command): Command to add
        """
        self.commands.append(command)
        
    def execute(self):
        """
        Execute all commands in order.
        """
        for command in self.commands:
            command.execute()
            
    def undo(self):
        """
        Undo all commands in reverse order.
        """
        for command in reversed(self.commands):
            command.undo()
            
    def serialize(self):
        """
        Serialize all commands in the compound.
        
        Returns:
            dict: Serialized state
        """
        return {
            "name": self.name,
            "commands": [cmd.serialize() for cmd in self.commands]
        }
        
    @classmethod
    def deserialize(cls, state, registry):
        """
        Create a compound command from serialized state.
        
        Args:
            state (dict): Serialized state
            registry: Object registry for resolving references
            
        Returns:
            CompoundCommand: Reconstructed compound command
        """
        from command_system.internal.serialization import deserialize_command
        
        compound = cls(state["name"])
        
        for cmd_state in state["commands"]:
            command = deserialize_command(cmd_state, registry)
            if command:
                compound.add_command(command)
                
        return compound


class PropertyCommand(Command):
    """
    Command for changing a property on an observable object.
    """
    
    def __init__(self, target, property_name, new_value):
        """
        Initialize a property change command.
        
        Args:
            target (Observable): Target object
            property_name (str): Name of property to change
            new_value: New property value
        """
        self.target = target
        self.property_name = property_name
        self.new_value = new_value
        self.old_value = getattr(target, property_name)
        
    def execute(self):
        """
        Execute the command by setting the new property value.
        """
        setattr(self.target, self.property_name, self.new_value)
        
    def undo(self):
        """
        Undo the command by restoring the old property value.
        """
        setattr(self.target, self.property_name, self.old_value)
        
    def serialize(self):
        """
        Serialize command state.
        
        Returns:
            dict: Serialized state
        """
        return {
            "type": "PropertyCommand",
            "target_id": self.target.get_id(),
            "property_name": self.property_name,
            "new_value": self.new_value,
            "old_value": self.old_value
        }
        
    @classmethod
    def deserialize(cls, state, registry):
        """
        Create a property command from serialized state.
        
        Args:
            state (dict): Serialized state
            registry: Object registry for resolving references
            
        Returns:
            PropertyCommand: Reconstructed property command
        """
        target = registry.get_object(state["target_id"])
        if not target:
            return None
            
        cmd = cls(target, state["property_name"], state["new_value"])
        cmd.old_value = state["old_value"]
        return cmd