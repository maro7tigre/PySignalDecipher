"""
Observable pattern implementation for property change tracking with improved observer management.

This module provides a clean implementation of the observable pattern
with property change notifications that fully leverages the ID system.
"""
from typing import Any, Dict, Callable, TypeVar, Generic, Optional, List, Set
from weakref import WeakKeyDictionary
from ..id_system import (
    get_id_registry,
    parse_property_id
)
from ..id_system.core.mapping import Mapping
from ..id_system.types import ObservableTypeCodes, PropertyTypeCodes

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
            property_id = instance._get_property_id(self.name)
            
            # Notify observers if we're not already in an update
            if not instance._is_updating:
                try:
                    instance._is_updating = True
                    instance._notify_property_observers(self.name, old_value, value)
                finally:
                    instance._is_updating = False

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
        self.id_registry = get_id_registry()
        # Register with ID system but don't store the ID
        self.id_registry.register_observable(self, ObservableTypeCodes.OBSERVABLE)
        
        # Update status tracking
        self._is_updating = False
        
        # Store observer callbacks with improved structure using Mapping
        # property_name -> {observer_id: callback}
        self._property_observers = {}
        
        # Auto-register all observable properties defined on the class
        self._auto_register_properties()

    # MARK: - Property Registration
    def _auto_register_properties(self):
        """Auto-register all ObservableProperty attributes on instance creation."""
        for attr_name, attr_value in self.__class__.__dict__.items():
            if isinstance(attr_value, ObservableProperty):
                # Get the property ID to force registration
                property_id = self._get_property_id(attr_name)
                
                # If property wasn't registered for some reason, register it explicitly
                if property_id is None:
                    # Get the property descriptor
                    property_descriptor = getattr(self.__class__, attr_name)
                    
                    # Register the property with the ID system
                    observable_id = self.get_id()
                    property_id = self.id_registry.register_observable_property(
                        property_descriptor,  # Use the actual descriptor instead of None
                        PropertyTypeCodes.OBSERVABLE_PROPERTY,
                        None,  # Auto-generated unique ID
                        attr_name,
                        observable_id
                    )
                    
                # Initialize observer dict for this property
                self._property_observers[attr_name] = Mapping(update_keys=True, update_values=False)
                self.id_registry.mappings.append(self._property_observers[attr_name])
    
    def _get_property_id(self, property_name: str) -> Optional[str]:
        """
        Get or create the ID for a property.
        
        Args:
            property_name: Name of the property
            
        Returns:
            str: Property ID or None if property doesn't exist
        """
        # Check if the property exists
        if not hasattr(self.__class__, property_name) or not isinstance(getattr(self.__class__, property_name), ObservableProperty):
            return None
            
        # Check if the property already exists in the ID system
        observable_id = self.get_id()
        property_ids = self.id_registry.get_property_ids_by_observable_id_and_property_name(
            observable_id, property_name)
        
        if property_ids:
            # Property already registered
            return property_ids[0]
        else:
            # Get the property descriptor
            property_descriptor = getattr(self.__class__, property_name)
            
            # Register the property
            return self.id_registry.register_observable_property(
                property_descriptor,  # Use the actual descriptor instead of None
                PropertyTypeCodes.OBSERVABLE_PROPERTY,
                None,  # Auto-generated unique ID
                property_name,
                observable_id
            )
    
    def _notify_property_observers(self, property_name: str, old_value: Any, new_value: Any) -> None:
        """
        Notify all observers of a property change.
        
        Args:
            property_name: Name of the property that changed
            old_value: Previous value of the property
            new_value: New value of the property
        """
        # Make sure we have the observers dict for this property
        if property_name not in self._property_observers:
            return
        
        # Notify all observers - iterate through values (callbacks)
        for observer_id in self._property_observers[property_name]:
            callback = self._property_observers[property_name].get(observer_id)
            if callback:
                try:
                    callback(property_name, old_value, new_value)
                except Exception as e:
                    print(f"Error in property observer callback: {e}")
    
    # MARK: - Observer Management
    def add_property_observer(self, property_name: str, 
                             callback: Callable[[str, Any, Any], None],
                             observer_obj: Any = None) -> Optional[str]:
        """
        Add observer for property changes.
        
        Args:
            property_name: Name of the property to observe
            callback: Function to call when property changes,
                     should accept (property_name, old_value, new_value)
            observer_obj: Object that owns the callback (for ID tracking)
                         If None, a new ID will be generated
        
        Returns:
            str: Observer ID that can be used to remove the observer or None if property doesn't exist
        """
        # Get property ID
        property_id = self._get_property_id(property_name)
        if not property_id:
            return None
        
        # Register observer if it's an object
        observer_id = None
        if observer_obj is not None:
            observer_id = self.id_registry.get_id(observer_obj)
            if not observer_id:
                # Register as widget if not already registered
                observer_id = self.id_registry.register(observer_obj, "cw")
        else:
            # Create a proxy object to hold the callback
            observer_obj = {"callback": callback}
            observer_id = self.id_registry.register(observer_obj, "cw")
            
        # Ensure we have an observer dict for this property
        if property_name not in self._property_observers:
            self._property_observers[property_name] = Mapping(update_keys=True, update_values=False)
            self.id_registry.mappings.append(self._property_observers[property_name])
            
        # Add the callback to our observer dict with observer_id as key
        self._property_observers[property_name][observer_id] = callback
        
        return observer_id
        
    def remove_property_observer(self, property_name: str, observer_id: str) -> bool:
        """
        Remove property observer.
        
        Args:
            property_name: Name of the property
            observer_id: ID of the observer to remove
            
        Returns:
            bool: True if observer was removed, False otherwise
        """
        # Check if property exists
        if property_name not in self._property_observers:
            return False
            
        # Direct lookup using observer_id as key
        if observer_id in self._property_observers[property_name]:
            self._property_observers[property_name].delete(observer_id)
            return True
            
        return False
    
    # MARK: - Identity and Relationship
    def get_id(self) -> str:
        """
        Get unique identifier from ID registry.
        
        Returns:
            str: ID for this object
        """
        return self.id_registry.get_id(self)
        
    def is_updating(self) -> bool:
        """
        Check if object is currently processing a property update.
        
        Returns:
            bool: True if the object is updating, False otherwise
        """
        return self._is_updating
    
    # MARK: - Resource Management
    def unregister_property(self, property_name: str) -> bool:
        """
        Unregister a property from this observable.
        
        Args:
            property_name: Name of the property to unregister
            
        Returns:
            bool: True if the property was unregistered, False otherwise
        """
        property_id = self._get_property_id(property_name)
        if not property_id:
            return False
        
        # Remove property observers and cleanup mapping
        if property_name in self._property_observers:
            if self._property_observers[property_name] in self.id_registry.mappings:
                self.id_registry.mappings.remove(self._property_observers[property_name])
            self._property_observers.pop(property_name, None)
            
        return self.id_registry.unregister(property_id)
    
    def unregister(self) -> bool:
        """
        Unregister this observable from the ID system.
        
        This will also unregister all properties associated with this observable.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Clean up property observers
        for property_name, observer_mapping in list(self._property_observers.items()):
            if observer_mapping in self.id_registry.mappings:
                self.id_registry.mappings.remove(observer_mapping)
        
        self._property_observers.clear()
        
        return self.id_registry.unregister(self.get_id())
    
    def __del__(self):
        """Clean up by unregistering from ID registry."""
        try:
            self.unregister()
        except:
            pass  # Ignore errors during cleanup
    
    # MARK: - Property Serialization
    def serialize_property(self, property_name: str) -> Optional[Dict[str, Any]]:
        """
        Serialize a property to a dictionary.
        
        Args:
            property_name: Name of the property to serialize
            
        Returns:
            dict: Dictionary containing serialized property data or None if property doesn't exist
        """
        property_id = self._get_property_id(property_name)
        if not property_id:
            return None
            
        return {
            'property_id': property_id,
            'property_name': property_name,
            'value': getattr(self, property_name) if hasattr(self, property_name) else None,
            'observable_id': self.get_id()
        }
    
    def deserialize_property(self, property_name: str, data: Dict[str, Any]) -> bool:
        """
        Deserialize property data and apply it to this observable.
        
        Args:
            property_name: Name of the property to deserialize
            data: Dictionary containing serialized property data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not data or not isinstance(data, dict):
            return False
        
        # Get relevant data from the serialized dictionary
        property_id = data.get('property_id')
        value = data.get('value')
        observable_id = data.get('observable_id')
        print(f"Deserializing property {property_name} with ID {property_id} and value {value} for observable {observable_id}")
        if not property_id or not observable_id:
            return False
        
        # Get the ID registry
        registry = self.id_registry
        
        # If observable ID has changed, update our ID
        if observable_id != self.get_id():
            # Special handling for None observable case
            # If the new ID was created with None as the observable,
            # we need to take ownership of that ID
            target_observable = registry.get_observable(observable_id)
            if target_observable is None:
                # Unregister the empty observable ID, since we'll take it over
                registry.unregister(observable_id)
                # Now update our ID to match
                success, updated_id, error = registry.update_id(self.get_id(), observable_id)
            else:
                # Normal path - attempt to update our ID
                success, updated_id, error = registry.update_id(self.get_id(), observable_id)
                
            if not success:
                raise ValueError(f"Failed to update observable ID: {error}")
        
        # Check if the observable has a property with the same name
        if hasattr(self, property_name):
            # Get the property ID for the existing property
            existing_property_id = self._get_property_id(property_name)
            print(f"Existing property ID: {existing_property_id}, Property ID: {property_id}, Property Name: {property_name}")
            # Update the property value
            setattr(self, property_name, value)
            
            # If the existing property is registered and the property_id differs, update it
            if existing_property_id and property_id != existing_property_id:
                # First get the existing property's components

                success, updated_id, error = registry.update_id(existing_property_id, property_id)
                if not success:
                    raise ValueError(f"Failed to update property ID: {error}")
        else:
            # Property doesn't exist on this observable, create a new ObservableProperty
            # This is a dynamic addition of a property
            
            # Dynamically add the property to the instance
            setattr(self.__class__, property_name, ObservableProperty(value))
            
            # Set the initial value
            setattr(self, property_name, value)
            
            # Make sure we have an observer set for this property
            self._property_observers[property_name] = Mapping(update_keys=True, update_values=False)
            self.id_registry.mappings.append(self._property_observers[property_name])
            
            # Now register the property with the ID system
            # First get the original property components to extract controller information
            original_components = parse_property_id(property_id)
            
            if original_components:
                controller_id = original_components['controller_id']
                # Get the newly created property descriptor
                property_descriptor = getattr(self.__class__, property_name)
                
                # Register the property with the same ID
                registry.register_observable_property(
                    property_descriptor,  # Use the descriptor instead of None
                    original_components['type_code'],
                    original_components['unique_id'],
                    property_name,
                    self.get_id(),
                    controller_id if controller_id != "0" else None
                )
        
        return True

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the entire observable to a dictionary.
        
        Returns:
            dict: Dictionary containing all serialized properties
        """
        result = {
            'id': self.get_id(),
            'properties': {}
        }
        
        # Serialize all ObservableProperties
        for attr_name, attr_value in self.__class__.__dict__.items():
            if isinstance(attr_value, ObservableProperty):
                property_data = self.serialize_property(attr_name)
                if property_data:
                    result['properties'][attr_name] = property_data
                
        return result
    
    def deserialize(self, data: Dict[str, Any]) -> bool:
        """
        Deserialize data and apply it to this observable.
        
        Args:
            data: Dictionary containing serialized observable data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not data or not isinstance(data, dict):
            return False
            
        # Update observable ID if needed
        observable_id = data.get('id')
        if observable_id and observable_id != self.get_id():
            # Special handling for None observable case
            target_observable = self.id_registry.get_observable(observable_id)
            if target_observable is None:
                # Unregister the empty observable ID, since we'll take it over
                self.id_registry.unregister(observable_id)
                # Now update our ID to match
                success, updated_id, error = self.id_registry.update_id(self.get_id(), observable_id)
            else:
                # Normal path - attempt to update our ID
                success, updated_id, error = self.id_registry.update_id(self.get_id(), observable_id)
                
            if not success:
                raise ValueError(f"Failed to update observable ID: {error}")
            
        # Update properties
        if 'properties' in data and isinstance(data['properties'], dict):
            for prop_name, prop_data in data['properties'].items():
                if hasattr(self, prop_name):
                    self.deserialize_property(prop_name, prop_data)
                    
        return True