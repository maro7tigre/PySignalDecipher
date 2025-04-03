"""
Command pattern implementation for undo/redo functionality.

This module provides a clean implementation of the command pattern
for action encapsulation and history tracking using the ID system.
"""
from abc import ABC, abstractmethod
from typing import List, Any, Optional, TypeVar, Dict, Union
from ..id_system import get_id_registry, TypeCodes, extract_property_name

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
        self.trigger_widget_id = None
        self.context_info = {}
        
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
        
    def set_trigger_widget(self, widget_id: str) -> None:
        """
        Set the widget that triggered this command.
        
        Args:
            widget_id: ID of widget that triggered the command
        """
        self.trigger_widget_id = widget_id
        
    def get_trigger_widget(self) -> Optional[Any]:
        """
        Get the widget that triggered this command.
        
        Returns:
            Widget object or None if not set/found
        """
        if not self.trigger_widget_id:
            return None
        return get_id_registry().get_widget(self.trigger_widget_id)
    
    def set_context_info(self, key: str, value: Any) -> None:
        """
        Store context information with the command.
        
        Args:
            key: Context information key
            value: Context information value
        """
        self.context_info[key] = value
        
    def get_context_info(self, key: str, default: Any = None) -> Any:
        """
        Get stored context information.
        
        Args:
            key: Context information key
            default: Default value if key not found
            
        Returns:
            Stored value or default
        """
        return self.context_info.get(key, default)

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
        super().__init__()
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
    """
    Command for changing a property on an observable object.
    Uses property IDs from the ID system directly.
    """
    
    def __init__(self, property_id: str, new_value: Any):
        """
        Initialize a property change command.
        
        Args:
            property_id: ID of the observable property to change
            new_value: New property value
        """
        super().__init__()
        self.property_id = property_id
        self.new_value = new_value
        
        # Get the target object and property name to store the old value
        id_registry = get_id_registry()
        target_id = id_registry.get_observable_id_from_property_id(property_id)
        property_name = extract_property_name(property_id)
        
        self.target_id = target_id
        self.property_name = property_name
        
        if target_id:
            target = id_registry.get_observable(target_id)
            if target:
                self.old_value = getattr(target, property_name)
            else:
                self.old_value = None
        else:
            self.old_value = None
        
    def execute(self) -> None:
        """Execute the command by setting the new property value."""
        id_registry = get_id_registry()
        target_id = self.target_id
        
        if not target_id:
            # Try to get it again in case relationships changed
            target_id = id_registry.get_observable_id_from_property_id(self.property_id)
            
        if target_id:
            target = id_registry.get_observable(target_id)
            if target:
                setattr(target, self.property_name, self.new_value)
        
    def undo(self) -> None:
        """Undo the command by restoring the old property value."""
        id_registry = get_id_registry()
        target_id = self.target_id
        
        if not target_id:
            # Try to get it again in case relationships changed
            target_id = id_registry.get_observable_id_from_property_id(self.property_id)
            
        if target_id:
            target = id_registry.get_observable(target_id)
            if target:
                setattr(target, self.property_name, self.old_value)

# MARK: - MacroCommand
class MacroCommand(CompoundCommand):
    """
    A specialized compound command that represents a user-level action.
    Used for grouping related commands with a description of the action.
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
        
# MARK: - Widget Property Commands
class WidgetPropertyCommand(Command):
    """
    Command for changing a property on a widget.
    Uses widget IDs from the ID system.
    """
    
    def __init__(self, widget_id: str, property_name: str, new_value: Any):
        """
        Initialize a widget property change command.
        
        Args:
            widget_id: ID of target widget
            property_name: Name of property to change
            new_value: New property value
        """
        super().__init__()
        self.widget_id = widget_id
        self.property_name = property_name
        self.new_value = new_value
        
        # Get the widget to store the old value
        widget = get_id_registry().get_widget(widget_id)
        if widget:
            self.old_value = getattr(widget, property_name)
        else:
            self.old_value = None
        
    def execute(self) -> None:
        """Execute the command by setting the new property value."""
        widget = get_id_registry().get_widget(self.widget_id)
        if widget:
            setattr(widget, self.property_name, self.new_value)
        
    def undo(self) -> None:
        """Undo the command by restoring the old property value."""
        widget = get_id_registry().get_widget(self.widget_id)
        if widget:
            setattr(widget, self.property_name, self.old_value)
            
# MARK:  serialization Command
class SerializationCommand(Command):
    """
    Command that captures serialized state for undo/redo.
    
    This command uses the serialization system to capture component state
    before and after operations, enabling undo/redo through state restoration.
    """
    
    def __init__(self, component_id: str):
        """
        Initialize with component to track.
        
        Args:
            component_id: ID of the Component to track
        """
        super().__init__()
        self.component_id = component_id
        self.serialized_state = None
        self.post_state = None
    
    def capture_state(self) -> None:
        """
        Capture the current state of the component.
        
        This should be called before making changes to capture the original state
        for later restoration during undo operations.
        """
        component = get_id_registry().get_widget(self.component_id)
        if component and hasattr(component, 'get_serialization'):
            self.serialized_state = component.get_serialization()
    
    def capture_post_state(self) -> None:
        """
        Capture the state after changes have been made.
        
        This can be used for redo operations to restore to the post-change state
        instead of re-executing the potentially complex operations.
        """
        component = get_id_registry().get_widget(self.component_id)
        if component and hasattr(component, 'get_serialization'):
            self.post_state = component.get_serialization()
    
    def restore_state(self) -> bool:
        """
        Restore the component to its original state.
        
        This is typically called during undo to restore the component
        to its state before the command was executed.
        
        Returns:
            True if state was successfully restored, False otherwise
        """
        if not self.serialized_state:
            return False
            
        component = get_id_registry().get_widget(self.component_id)
        if component and hasattr(component, 'deserialize'):
            return component.deserialize(self.serialized_state)
        return False
    
    def restore_post_state(self) -> bool:
        """
        Restore the component to its post-operation state.
        
        This can be used during redo to restore the component to the state
        after changes were made initially.
        
        Returns:
            True if post state was successfully restored, False otherwise
        """
        if not self.post_state:
            return False
            
        component = get_id_registry().get_widget(self.component_id)
        if component and hasattr(component, 'deserialize'):
            return component.deserialize(self.post_state)
        return False
    
    def execute(self) -> None:
        """
        Execute the command and capture post-operation state.
        
        This base implementation just captures the post-state after
        the operation. Subclasses should override this to implement
        their specific operations, and call super().execute() at the end.
        """
        # Default implementation captures the post-state
        self.capture_post_state()
    
    def undo(self) -> None:
        """
        Undo the command by restoring the original state.
        
        This restores the component to its state before the command
        was executed.
        """
        self.restore_state()
    
    def redo(self) -> None:
        """
        Redo the command.
        
        If post_state is available, restores to that state.
        Otherwise, falls back to re-executing the command.
        """
        if self.post_state and self.restore_post_state():
            # Successfully restored post state
            return
            
        # Fall back to standard execute method
        super().redo()