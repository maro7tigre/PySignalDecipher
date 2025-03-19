"""
Observable pattern implementation for property change tracking.
"""
import uuid

class Observable:
    """
    Base class for objects that need to track property changes.
    Provides methods to add and remove property observers.
    """
    def __init__(self):
        self._property_observers = {}
        self._id = str(uuid.uuid4())
        
    def add_property_observer(self, property_name, callback):
        """
        Add observer for property changes.
        
        Args:
            property_name (str): Name of the property to observe
            callback (callable): Function to call when property changes,
                                should accept (property_name, old_value, new_value)
        
        Returns:
            str: Observer ID that can be used to remove the observer
        """
        if property_name not in self._property_observers:
            self._property_observers[property_name] = {}
            
        observer_id = str(uuid.uuid4())
        self._property_observers[property_name][observer_id] = callback
        return observer_id
        
    def remove_property_observer(self, property_name, observer_id):
        """
        Remove property observer.
        
        Args:
            property_name (str): Name of the property
            observer_id (str): ID of the observer to remove
            
        Returns:
            bool: True if observer was removed, False otherwise
        """
        if (property_name in self._property_observers and 
            observer_id in self._property_observers[property_name]):
            del self._property_observers[property_name][observer_id]
            return True
        return False
        
    def _notify_property_changed(self, property_name, old_value, new_value):
        """
        Notify observers of property change.
        
        Args:
            property_name (str): Name of the property that changed
            old_value: Previous value of the property
            new_value: New value of the property
        """
        if property_name in self._property_observers:
            for callback in self._property_observers[property_name].values():
                callback(property_name, old_value, new_value)
                
    def get_id(self):
        """
        Get unique identifier.
        
        Returns:
            str: Unique ID for this observable object
        """
        return self._id
        
    def set_id(self, id_value):
        """
        Set unique identifier (for deserialization).
        
        Args:
            id_value (str): ID to assign to this object
        """
        self._id = id_value


class ObservableProperty:
    """
    Descriptor for observable properties that automatically 
    notifies observers when changed.
    """
    def __init__(self, default=None):
        """
        Initialize a new observable property.
        
        Args:
            default: Default value for the property
        """
        self.default = default
        self.name = None
        self.private_name = None
        
    def __set_name__(self, owner, name):
        """
        Called when descriptor is assigned to a class attribute.
        
        Args:
            owner: Class that owns this property
            name (str): Name of the attribute this descriptor is assigned to
        """
        self.name = name
        self.private_name = f"_{name}"
        
    def __get__(self, instance, owner):
        """
        Get property value from instance.
        
        Args:
            instance: Object instance 
            owner: Class that owns this property
            
        Returns:
            Current property value
        """
        if instance is None:
            return self
            
        # Return current value or default if not set
        return getattr(instance, self.private_name, self.default)
        
    def __set__(self, instance, value):
        """
        Set property value and notify observers if changed.
        
        Args:
            instance: Object instance
            value: New property value
        """
        old_value = getattr(instance, self.private_name, self.default)
        
        # Only notify if value actually changed
        if old_value != value:
            setattr(instance, self.private_name, value)
            instance._notify_property_changed(self.name, old_value, value)