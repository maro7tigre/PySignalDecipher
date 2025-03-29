"""
Observable pattern implementation for property change tracking.

This module provides a clean implementation of the observable pattern
with property change notifications that fully leverages the ID system.
"""
from typing import Any, Dict, Callable, TypeVar, Generic, Optional, Set
from ..id_system import get_id_registry, TypeCodes, is_widget_id

# Type variable for generic property types
T = TypeVar('T')

# MARK: -ObservableProperty
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
        self.property_id = None
        
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
            
            # Ensure property is registered with ID system
            instance._ensure_property_registered(self.name)
            
            # Notify observers
            instance._notify_property_changed(self.name, old_value, value)

# MARK: -Observable
class Observable:
    """
    Base class for objects that need to track property changes.
    Uses the ID system for identification and relationship tracking.
    """
    def __init__(self, parent_id: Optional[str] = None):
        """
        Initialize an observable object.
        
        Args:
            parent_id: Optional parent observable ID
        """
        # Register with ID system
        id_registry = get_id_registry()
        self._id = id_registry.register_observable(self, TypeCodes.OBSERVABLE)
        
        # Property change observers: {property_id -> {observer_id -> callback}}
        self._property_observers: Dict[str, Dict[str, Callable]] = {}
        
        # Cache for property IDs by name
        self._property_id_cache: Dict[str, str] = {}
        
        # Update status tracking
        self._is_updating = False
        
        # Relationship tracking
        self._parent_id = parent_id
        
        # Hierarchy tracking
        if parent_id:
            parent = id_registry.get_observable(parent_id)
            if parent and hasattr(parent, 'get_generation'):
                self._generation = parent.get_generation() + 1
            else:
                self._generation = 0
        else:
            self._generation = 0
        
        self._auto_register_properties()

    def _auto_register_properties(self):
        """Auto-register all ObservableProperty attributes on instance creation."""
        # Get all class attributes that are ObservableProperties
        for attr_name, attr_value in self.__class__.__dict__.items():
            if isinstance(attr_value, ObservableProperty):
                # Force property registration by accessing it once
                self._ensure_property_registered(attr_name)
        
    def _ensure_property_registered(self, property_name: str) -> str:
        """
        Ensure a property is registered with the ID system.
        
        Args:
            property_name: Name of the property
            
        Returns:
            Property ID
        """
        # Check if we've already registered this property
        if property_name in self._property_id_cache:
            return self._property_id_cache[property_name]
            
        id_registry = get_id_registry()
        observable_id = self.get_id()
        
        # Check if this property is already registered
        property_ids = id_registry.get_property_ids_by_observable_id_and_property_name(
            observable_id, property_name)
        
        if property_ids:
            # Property already registered
            property_id = property_ids[0]
        else:
            # Register the property
            property_id = id_registry.register_observable_property(
                self, TypeCodes.OBSERVABLE_PROPERTY,
                None, property_name, observable_id
            )
            
        # Cache the ID
        self._property_id_cache[property_name] = property_id
        return property_id
        
    def add_property_observer(self, property_name: str, 
                             callback: Callable[[str, Any, Any], None],
                             observer_obj: Any = None) -> str:
        """
        Add observer for property changes.
        
        Args:
            property_name: Name of the property to observe
            callback: Function to call when property changes,
                     should accept (property_name, old_value, new_value)
            observer_obj: Object that owns the callback (for ID tracking)
                         If None, a new ID will be generated
        
        Returns:
            Observer ID that can be used to remove the observer
        """
        # Ensure property is registered
        property_id = self._ensure_property_registered(property_name)
        
        # Initialize observers dictionary for this property if needed
        if property_id not in self._property_observers:
            self._property_observers[property_id] = {}
            
        # Get or register the observer
        id_registry = get_id_registry()
        
        if observer_obj is not None:
            # If we have an object, get or register its ID
            observer_id = id_registry.get_id(observer_obj)
            if not observer_id:
                # Register as widget if not already registered
                observer_id = id_registry.register(
                    observer_obj, TypeCodes.CUSTOM_WIDGET
                )
        else:
            # Create a proxy object to hold the callback
            observer_obj = {"callback": callback}
            observer_id = id_registry.register(
                observer_obj, TypeCodes.CUSTOM_WIDGET
            )
            
        # Store the callback
        self._property_observers[property_id][observer_id] = callback
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
        # Get property ID
        property_id = self._property_id_cache.get(property_name)
        if not property_id:
            return False
            
        if (property_id in self._property_observers and 
            observer_id in self._property_observers[property_id]):
            del self._property_observers[property_id][observer_id]
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
            
        # Get property ID
        property_id = self._property_id_cache.get(property_name)
        if not property_id:
            return
            
        if property_id in self._property_observers:
            try:
                self._is_updating = True
                for callback in self._property_observers[property_id].values():
                    callback(property_name, old_value, new_value)
            finally:
                self._is_updating = False
                
    def get_id(self) -> str:
        """
        Get unique identifier from ID registry.
        
        Returns:
            String ID for this object
        """
        return self._id
        
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
        
    def is_updating(self) -> bool:
        """
        Check if object is currently processing a property update.
        
        Returns:
            True if the object is updating, False otherwise
        """
        return self._is_updating
        
    def __del__(self):
        """Clean up by unregistering from ID registry."""
        try:
            get_id_registry().unregister(self._id)
        except:
            pass  # Ignore errors during cleanup