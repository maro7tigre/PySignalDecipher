"""
Observable properties for PySignalDecipher.

This module provides property tracking and change notification
for objects whose state changes should be tracked and undoable.
"""

from typing import Any, Dict, Callable, List, Optional, Set, TypeVar, Generic
import uuid
from PySide6.QtCore import QObject, Signal

T = TypeVar('T')  # Generic type for property values


class ObservableProperty(Generic[T]):
    """
    A property descriptor that tracks changes and notifies observers.
    
    This provides a way to track changes to object properties and
    automatically integrate with the command system.
    """
    
    def __init__(self, default_value: T = None):
        """
        Initialize a new observable property.
        
        Args:
            default_value: The default value for the property
        """
        self.default_value = default_value
        self.name = None  # Will be set when the property is assigned to a class
    
    def __set_name__(self, owner, name):
        """
        Called when the property is assigned to a class.
        
        Args:
            owner: The class that owns this property
            name: The name of the property
        """
        self.name = name
        self.private_name = f"_{name}"
    
    def __get__(self, instance, owner):
        """
        Get the property value.
        
        Args:
            instance: The object instance
            owner: The class
            
        Returns:
            The property value
        """
        if instance is None:
            return self
        
        # Return the value or default
        return getattr(instance, self.private_name, self.default_value)
    
    def __set__(self, instance, value):
        """
        Set the property value.
        
        Args:
            instance: The object instance
            value: The new value
        """
        if not hasattr(instance, self.private_name):
            # First time setting, just set it
            setattr(instance, self.private_name, value)
            return
        
        # Get the old value
        old_value = getattr(instance, self.private_name)
        
        # If the value is the same, do nothing
        if old_value == value:
            return
        
        # Set the new value
        setattr(instance, self.private_name, value)
        
        # Notify property changed if instance is Observable
        if isinstance(instance, Observable) and hasattr(instance, "_property_changed"):
            instance._property_changed(self.name, old_value, value)


class Observable(QObject):
    """
    Base class for objects with observable properties.
    
    Objects that need to track property changes for undo/redo
    should inherit from this class.
    """
    
    # Signal emitted when a property changes
    property_changed = Signal(str, object, object)  # property_name, old_value, new_value
    
    def __init__(self):
        """Initialize the observable object."""
        super().__init__()
        self._property_observers: Dict[str, List[Callable[[str, Any, Any], None]]] = {}
        self._ignore_changes = False
    
    def _property_changed(self, property_name: str, old_value: Any, new_value: Any) -> None:
        """
        Handle property changes.
        
        Args:
            property_name: Name of the changed property
            old_value: Previous value
            new_value: New value
        """
        if self._ignore_changes:
            return
        
        # Emit signal
        self.property_changed.emit(property_name, old_value, new_value)
        
        # Notify observers
        if property_name in self._property_observers:
            for observer in self._property_observers[property_name]:
                observer(property_name, old_value, new_value)
    
    def add_property_observer(self, 
                             property_name: str, 
                             observer: Callable[[str, Any, Any], None]) -> None:
        """
        Add an observer for a specific property.
        
        Args:
            property_name: The property to observe
            observer: Callback to invoke when the property changes
        """
        if property_name not in self._property_observers:
            self._property_observers[property_name] = []
        
        self._property_observers[property_name].append(observer)
    
    def remove_property_observer(self, 
                                property_name: str, 
                                observer: Callable[[str, Any, Any], None]) -> None:
        """
        Remove a property observer.
        
        Args:
            property_name: The property being observed
            observer: The observer to remove
        """
        if property_name in self._property_observers:
            if observer in self._property_observers[property_name]:
                self._property_observers[property_name].remove(observer)
    
    def get_all_properties(self) -> Dict[str, Any]:
        """
        Get all observable properties.
        
        Returns:
            Dictionary of property names and values
        """
        result = {}
        
        for attr_name in dir(self.__class__):
            if isinstance(getattr(self.__class__, attr_name, None), ObservableProperty):
                result[attr_name] = getattr(self, attr_name)
        
        return result
    
    def set_properties(self, properties: Dict[str, Any], track_changes: bool = True) -> None:
        """
        Set multiple properties at once.
        
        Args:
            properties: Dictionary of property names and values
            track_changes: Whether to track the changes or not
        """
        old_ignore = self._ignore_changes
        if not track_changes:
            self._ignore_changes = True
        
        try:
            for name, value in properties.items():
                if hasattr(self.__class__, name) and isinstance(getattr(self.__class__, name), ObservableProperty):
                    setattr(self, name, value)
        finally:
            self._ignore_changes = old_ignore


class PropertyChangeCommand:
    """
    Base class for commands that change observable properties.
    
    This is a mixin class that can be combined with Command to create
    property change commands.
    """
    
    def __init__(self, 
                target: Observable, 
                property_name: str, 
                new_value: Any):
        """
        Initialize the property change command.
        
        Args:
            target: The object whose property will change
            property_name: The name of the property
            new_value: The new value for the property
        """
        self.target = target
        self.property_name = property_name
        self.new_value = new_value
        self.old_value = getattr(target, property_name)
    
    def execute(self) -> None:
        """Execute the property change."""
        setattr(self.target, self.property_name, self.new_value)
    
    def undo(self) -> None:
        """Undo the property change."""
        setattr(self.target, self.property_name, self.old_value)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the serialized state.
        
        Returns:
            Dictionary with the command state
        """
        # Note: This requires the target to be identifiable
        # You may need a more sophisticated approach for real objects
        return {
            "target_id": id(self.target),  # This is a simplification
            "property_name": self.property_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }
        
class SignalVariable(Observable):
    """
    A variable that can be linked to multiple components and notifies
    subscribers when its value changes.
    """
    
    value = ObservableProperty(None)
    
    def __init__(self, name, initial_value=None, parent_id=None):
        super().__init__()
        self.id = str(uuid.uuid4())
        self.name = name
        self.parent_id = parent_id  # Store the parent dock/widget ID
        self.value = initial_value
        self._subscribers = {}  # Dictionary of callback functions keyed by subscriber ID
    
    def subscribe(self, subscriber_id, callback):
        """Register a subscriber to be notified of value changes"""
        self._subscribers[subscriber_id] = callback
        # Immediately notify with current value
        callback(self.value)
    
    def unsubscribe(self, subscriber_id):
        """Remove a subscriber"""
        if subscriber_id in self._subscribers:
            del self._subscribers[subscriber_id]
    
    def clear_subscribers(self):
        """Remove all subscribers"""
        self._subscribers.clear()