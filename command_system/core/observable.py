"""
Observable pattern implementation for property change tracking.

This module provides a clean implementation of the observable pattern
with property change notifications that fully leverages the ID system.
"""
from typing import Any, Dict, Callable, TypeVar, Generic, Optional, Set
from ..id_system import (
    get_id_registry,
    subscribe_to_id,
    unsubscribe_from_id
)
from ..id_system.types import TypeCodes, ObservableTypeCodes, PropertyTypeCodes, WidgetTypeCodes
from ..id_system.core.parser import (
    get_unique_id_from_id,
    parse_property_id
)

# Type variable for generic property types
T = TypeVar('T')

# MARK: - Observable Property
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
            
    def update_property_id(self, new_id: str):
        """
        Update the property ID when it changes in the ID system.
        
        Args:
            new_id: The new property ID
        """
        self.property_id = new_id

# MARK: - Observable
class Observable:
    """
    Base class for objects that need to track property changes.
    Uses the ID system for identification and relationship tracking.
    """
    def __init__(self):
        """
        Initialize an observable object.
        """
        # Register with ID system
        id_registry = get_id_registry()
        self._id = id_registry.register_observable(self, ObservableTypeCodes.OBSERVABLE)
        
        # Property change observers: {property_id -> {observer_id -> callback}}
        self._property_observers: Dict[str, Dict[str, Callable]] = {}
        
        # Cache for property IDs by name
        self._property_id_cache: Dict[str, str] = {}
        
        # Subscribe to our own ID changes
        self._subscribe_to_id_changes()
        
        # Update status tracking
        self._is_updating = False
        
        # Default generation to 0
        self._generation = 0
        
        self._auto_register_properties()

    # MARK: - Property Registration
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
                None,  # No need to store the property object itself
                PropertyTypeCodes.OBSERVABLE_PROPERTY,
                None,
                property_name,
                observable_id
            )
            
        # Cache the ID
        self._property_id_cache[property_name] = property_id
        
        # Subscribe to property ID changes
        self._subscribe_to_property_id_changes(property_id)
        
        return property_id
    
    def _subscribe_to_id_changes(self):
        """Subscribe to our own ID changes to update internal state."""
        subscribe_to_id(self._id, self._on_id_changed)
        
    def _subscribe_to_property_id_changes(self, property_id: str):
        """
        Subscribe to property ID changes to update internal state.
        
        Args:
            property_id: The property ID to subscribe to
        """
        subscribe_to_id(property_id, self._on_property_id_changed)
    
    def _on_id_changed(self, old_id: str, new_id: str):
        """
        Handle changes to our own ID.
        
        Args:
            old_id: The previous ID
            new_id: The new ID
        """
        self._id = new_id
        
        # Update all property IDs that reference this observable
        id_registry = get_id_registry()
        for prop_name in list(self._property_id_cache.keys()):
            old_prop_id = self._property_id_cache[prop_name]
            
            # Get all property IDs for this observable and name
            new_prop_ids = id_registry.get_property_ids_by_observable_id_and_property_name(
                new_id, prop_name)
            
            if new_prop_ids:
                # Update cached property ID
                self._property_id_cache[prop_name] = new_prop_ids[0]
                
                # Update observers mapping if needed
                if old_prop_id in self._property_observers:
                    self._property_observers[new_prop_ids[0]] = self._property_observers.pop(old_prop_id)
    
    def _on_property_id_changed(self, old_id: str, new_id: str):
        """
        Handle changes to a property ID.
        
        Args:
            old_id: The previous property ID
            new_id: The new property ID
        """
        # Extract property name from old ID to update cache
        property_components = parse_property_id(old_id)
        if property_components:
            property_name = property_components['property_name']
            
            # Update cache with new ID
            if property_name in self._property_id_cache:
                self._property_id_cache[property_name] = new_id
            
            # Update observers mapping
            if old_id in self._property_observers:
                self._property_observers[new_id] = self._property_observers.pop(old_id)
                
    def _on_observer_id_changed(self, old_id: str, new_id: str):
        """
        Handle changes to an observer ID.
        
        Args:
            old_id: The previous observer ID
            new_id: The new observer ID
        """
        # Update observer ID in all property_observers mappings
        for property_id, observers in self._property_observers.items():
            if old_id in observers:
                # Copy the callback to the new ID and remove the old entry
                observers[new_id] = observers.pop(old_id)
    
    # MARK: - Observer Management
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
                    observer_obj, WidgetTypeCodes.CUSTOM_WIDGET
                )
        else:
            # Create a proxy object to hold the callback
            observer_obj = {"callback": callback}
            observer_id = id_registry.register(
                observer_obj, WidgetTypeCodes.CUSTOM_WIDGET
            )
            
        # Subscribe to observer ID changes to keep property_observers updated
        subscribe_to_id(observer_id, self._on_observer_id_changed)
            
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
            
            # Unsubscribe from observer ID changes
            unsubscribe_from_id(observer_id, self._on_observer_id_changed)
            
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
    
    # MARK: - Identity and Relationship
    def get_id(self) -> str:
        """
        Get unique identifier from ID registry.
        
        Returns:
            String ID for this object
        """
        return self._id
        
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
    
    # MARK: - Resource Management
    def unregister_property(self, property_id: str) -> bool:
        """
        Unregister a property from this observable.
        
        Args:
            property_id: ID of the property to unregister
            
        Returns:
            True if the property was unregistered, False otherwise
        """
        id_registry = get_id_registry()
        
        # Find the property name associated with this ID
        property_name = None
        for name, pid in self._property_id_cache.items():
            if pid == property_id:
                property_name = name
                break
        
        if property_name:
            # Remove from cache
            del self._property_id_cache[property_name]
            
            # Remove any observers
            if property_id in self._property_observers:
                del self._property_observers[property_id]
            
            # Unregister from ID system
            id_registry.unregister(property_id)
            
            # Check if we have any properties left
            if not self._property_id_cache:
                # No properties left, unregister the observable
                id_registry.unregister(self._id)
                
            return True
        
        return False
    
    def __del__(self):
        """Clean up by unregistering from ID registry."""
        try:
            # Unsubscribe from ID changes to prevent leaks
            unsubscribe_from_id(self._id)
            
            # Unsubscribe from all property ID changes
            for property_id in self._property_id_cache.values():
                unsubscribe_from_id(property_id)
                
            # Unsubscribe from all observer ID changes
            for observers in self._property_observers.values():
                for observer_id in observers:
                    unsubscribe_from_id(observer_id, self._on_observer_id_changed)
                
            # Unregister from ID registry
            get_id_registry().unregister(self._id)
        except:
            pass  # Ignore errors during cleanup
    
    # MARK: - Property Serialization
    def serialize_property(self, property_id: str) -> Dict[str, Any]:
        """
        Serialize a property to a dictionary.
        
        Args:
            property_id: ID of the property to serialize
            
        Returns:
            Dictionary containing serialized property data
        """
        # Get property name from ID
        property_components = parse_property_id(property_id)
        if not property_components:
            return {
                'property_id': property_id,
                'property_name': None,
                'value': None,
                'observable_id': self.get_id()
            }
            
        property_name = property_components['property_name']
        
        if hasattr(self, property_name):
            value = getattr(self, property_name)
            return {
                'property_id': property_id,
                'property_name': property_name,
                'value': value,
                'observable_id': self.get_id()
            }
        
        return {
            'property_id': property_id,
            'property_name': property_name,
            'value': None,
            'observable_id': self.get_id()
        }
    
    def deserialize_property(self, property_id: str, data: Dict[str, Any]) -> bool:
        """
        Deserialize property data and apply it to this observable.
        
        Args:
            property_id: ID of the property to deserialize
            data: Dictionary containing serialized property data
            
        Returns:
            True if successful, False otherwise
        """
        # Validate and extract data
        if not data or not isinstance(data, dict):
            return False
        
        property_name = data.get('property_name')
        value = data.get('value')
        observable_id = data.get('observable_id')
        
        if not property_name or not observable_id:
            return False
        
        # Check if this observable's ID has changed
        if self._id != observable_id:
            id_registry = get_id_registry()
            
            # Check for ID collision (another observable with the same ID)
            existing_observable = id_registry.get_observable(observable_id)
            if existing_observable and existing_observable is not self:
                raise ValueError(f"Observable ID collision: {observable_id} (potential cleanup failure)")
            
            # Save old ID for notification
            old_id = self._id
            
            # Store property names and IDs before the update
            old_property_ids = {}
            for prop_name in self._property_id_cache:
                old_property_ids[prop_name] = self._property_id_cache[prop_name]
            
            # Update our ID
            self._id = observable_id
            
            # Update property IDs in registry to reference the new observable ID
            for prop_name, old_prop_id in old_property_ids.items():
                # Update observable reference for this property in the registry
                new_prop_id = id_registry.update_observable_reference(old_prop_id, observable_id)
                # Update our cache
                self._property_id_cache[prop_name] = new_prop_id
            
            # Manually notify subscribers about the ID change
            id_registry._subscription_manager.notify(old_id, observable_id)
            
            # Unsubscribe from old ID and subscribe to new ID
            unsubscribe_from_id(old_id, self._on_id_changed)
            subscribe_to_id(observable_id, self._on_id_changed)
        
        # Update the property if it exists
        if hasattr(self, property_name):
            setattr(self, property_name, value)
            return True
            
        return False