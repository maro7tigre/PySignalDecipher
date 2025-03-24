"""
Observable pattern implementation for property change tracking.

This module provides a clean implementation of the observable pattern
with property change notifications, independent of serialization concerns.
"""
import uuid
from typing import Any, Dict, Callable, TypeVar, Generic, Optional, Set

# Type variable for generic property types
T = TypeVar('T')


class ObservableProperty(Generic[T]):
    """
    Descriptor for observable properties that notifies observers when changed.
    """
    def __init__(self, default: Optional[T] = None):
        """
        Initialize a new observable property.
        
        Args:
            default: Default value for the property if not set
        """
        self.default = default
        self.name = None
        self.private_name = None
        
    def __set_name__(self, owner, name):
        """Called when descriptor is assigned to a class attribute."""
        self.name = name
        self.private_name = f"_{name}"
        
    def __get__(self, instance, owner):
        """Get property value from instance."""
        if instance is None:
            return self
            
        # Return current value or default if not set
        return getattr(instance, self.private_name, self.default)
        
    def __set__(self, instance, value):
        """Set property value and notify observers if changed."""
        old_value = getattr(instance, self.private_name, self.default)
        
        # Only notify if value actually changed
        if old_value != value:
            setattr(instance, self.private_name, value)
            instance._notify_property_changed(self.name, old_value, value)


class Observable:
    """
    Base class for objects that need to track property changes.
    """
    def __init__(self, parent: Optional['Observable'] = None):
        """
        Initialize an observable object.
        
        Args:
            parent: Optional parent observable object
        """
        # Property change observers
        self._property_observers: Dict[str, Dict[str, Callable]] = {}
        
        # Unique identity management
        self._id = str(uuid.uuid4())
        
        # Update status tracking
        self._is_updating = False
        
        # Relationship tracking
        self._parent_id = parent.get_id() if parent else None
        
        # Hierarchy tracking
        if parent and hasattr(parent, 'get_generation'):
            self._generation = parent.get_generation() + 1
        else:
            self._generation = 0
        
    def add_property_observer(self, property_name: str, 
                             callback: Callable[[str, Any, Any], None]) -> str:
        """
        Add observer for property changes.
        
        Args:
            property_name: Name of the property to observe
            callback: Function to call when property changes,
                     should accept (property_name, old_value, new_value)
        
        Returns:
            Observer ID that can be used to remove the observer
        """
        if property_name not in self._property_observers:
            self._property_observers[property_name] = {}
            
        observer_id = str(uuid.uuid4())
        self._property_observers[property_name][observer_id] = callback
        return observer_id
        
    def remove_property_observer(self, property_name: str, observer_id: str) -> bool:
        """
        Remove property observer.
        
        Args:
            property_name: Name of the property
            observer_id: ID of the observer to remove
            
        Returns:
            True if observer was removed, False otherwise
        """
        if (property_name in self._property_observers and 
            observer_id in self._property_observers[property_name]):
            del self._property_observers[property_name][observer_id]
            return True
        return False
        
    def _notify_property_changed(self, property_name: str, old_value: Any, new_value: Any) -> None:
        """
        Notify observers of property change.
        
        Args:
            property_name: Name of the property that changed
            old_value: Previous value of the property
            new_value: New value of the property
        """
        if self._is_updating:
            return  # Skip notification if we're already processing an update
            
        if property_name in self._property_observers:
            try:
                self._is_updating = True
                for callback in self._property_observers[property_name].values():
                    callback(property_name, old_value, new_value)
            finally:
                self._is_updating = False
                
    def get_id(self) -> str:
        """
        Get unique identifier.
        
        Returns:
            String UUID for this object
        """
        return self._id
        
    def set_id(self, id_value: str) -> None:
        """
        Set unique identifier.
        
        Args:
            id_value: New ID value (for deserialization)
        """
        self._id = id_value
        
    def is_updating(self) -> bool:
        """
        Check if object is currently processing a property update.
        
        Returns:
            True if the object is updating, False otherwise
        """
        return self._is_updating

    def get_parent_id(self) -> Optional[str]:
        """
        Get parent identifier.
        
        Returns:
            Parent ID or None if no parent
        """
        return self._parent_id
        
    def set_parent_id(self, parent_id: Optional[str]) -> None:
        """
        Set parent identifier.
        
        Args:
            parent_id: New parent ID or None to clear parent
        """
        self._parent_id = parent_id
        
    def get_generation(self) -> int:
        """
        Get object generation (hierarchical depth).
        
        Returns:
            Generation number (0 for root objects)
        """
        return self._generation
        
    def set_generation(self, generation: int) -> None:
        """
        Set object generation.
        
        Args:
            generation: New generation value
        """
        self._generation = generation
        
    # TODO: Add serialization support hooks
    # These methods will provide integration points for the serialization system
    # without directly implementing serialization logic in this class
    # 1. Support for property metadata and serialization hints
    # 2. Support for relationship tracking during serialization
    # 3. Hooks for pre/post serialization processing