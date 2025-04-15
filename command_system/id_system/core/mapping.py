"""
Mapping module.

This module provides a trackable dictionary-like class that automatically updates
when IDs change within the ID system.
"""
from command_system.id_system.core.parser import (
    parse_widget_id,
    get_unique_id_from_id,
)
import collections.abc # Use this for robust checking
from command_system.id_system.core.generator import LocationIDGenerator
from command_system.id_system.types import DEFAULT_ROOT_LOCATION, TypeCodes


# MARK:-Mapping
class Mapping:
    """
    A dictionary-like class that tracks keys and values and updates automatically
    when IDs change in the ID system.
    """
    
    def __init__(self, update_keys=True, update_values=True):
        """
        Initialize a new mapping.
        
        Args:
            update_keys: If True, keys will be updated when IDs change
            update_values: If True, values will be updated when IDs change
        """
        self._storage = {}
        self._key_log = set()
        self._value_log = set()
        self._update_keys = update_keys
        self._update_values = update_values
    


    def add(self, key, value):
        """Add or replace a key-value pair."""
        if key in self._storage:
            self.set(key, value)
        else:
            self._storage[key] = value
            self._key_log.add(key)

            if isinstance(value, collections.abc.Iterable) and not isinstance(value, (str, bytes)): # Check if iterable (but not string/bytes)
                for item in value:
                    try: hash(item); self._value_log.add(item) # Add hashable items
                    except TypeError: pass
            else:
                try: hash(value); self._value_log.add(value) # Add hashable value
                except TypeError: pass

        return value

    def set(self, key, value):
        """Set a value for an existing key."""
        if key not in self._storage:
            return False

        old_value = self._storage[key]
        if isinstance(old_value, collections.abc.Iterable) and not isinstance(old_value, (str, bytes)): # Check if iterable (but not string/bytes)
            for item in old_value:
                self._value_log.discard(item)
        else:
            self._value_log.discard(old_value)

        self._storage[key] = value

        if isinstance(value, collections.abc.Iterable) and not isinstance(value, (str, bytes)): # Check if iterable (but not string/bytes)
            for item in value:
                try: hash(item); self._value_log.add(item) # Add hashable items
                except TypeError: pass
        else:
            try: hash(value); self._value_log.add(value) # Add hashable value
            except TypeError: pass

        return True
    
    def update(self, old_id, new_id):
        """Update any occurrences of old_id to new_id in keys and values."""
        updated = False
        
        # Update keys
        if self._update_keys and old_id in self._key_log:
            if old_id in self._storage:
                value = self._storage[old_id]
                del self._storage[old_id]
                self._storage[new_id] = value
                self._key_log.discard(old_id)
                self._key_log.add(new_id)
                updated = True
        
        # Update values
        if self._update_values and old_id in self._value_log:
            for key, value in list(self._storage.items()):
                if isinstance(value, list):
                    if old_id in value:
                        self._storage[key] = [new_id if x == old_id else x for x in value]
                        updated = True
                elif value == old_id:
                    self._storage[key] = new_id
                    updated = True
            
            if updated:
                self._value_log.discard(old_id)
                self._value_log.add(new_id)
        
        return updated
    
    def delete(self, key):
        """Delete a key and its value from the mapping."""
        if key not in self._storage:
            return False
        
        value = self._storage[key]
        if isinstance(value, collections.abc.Iterable) and not isinstance(value, (str, bytes)): # Check if iterable (but not string/bytes)
            for item in value:
                try: hash(item); self._value_log.discard(item) # Remove hashable items
                except TypeError: pass
        else:
            try: hash(value); self._value_log.discard(value) # Remove hashable value
            except TypeError: pass
        
        del self._storage[key]
        self._key_log.discard(key)
        return True
    
    def get(self, key):
        """Get a value for a key, or None if it doesn't exist."""
        return self._storage.get(key)
    
    def in_log(self, item):
        """Check if an item is in the key or value logs."""
        return item in self._key_log or item in self._value_log
    
    # Dictionary-like interface
    def __contains__(self, key): 
        return key in self._storage
    
    def __getitem__(self, key):
        if key in self._storage:
            return self._storage[key]
        raise KeyError(key)
    
    def __setitem__(self, key, value): 
        return self.add(key, value)
    
    def __delitem__(self, key):
        if key not in self._storage:
            raise KeyError(key)
        self.delete(key)
    
    def __len__(self): 
        return len(self._storage)
    
    def __iter__(self): 
        return iter(self._storage)
    
    def __str__(self): 
        return f"<Mapping with {len(self._storage)} items>"
    
    def __repr__(self): 
        return str(self)
    
# MARK:- uniqueIdMapping
class UniqueIdMapping(Mapping):
    """
    A specialized mapping for handling unique ID to full ID relationships.
    
    This class extends the base Mapping class with functionality specifically
    for managing unique ID to full ID mappings. It ensures that when full IDs
    are updated, the corresponding unique ID mappings are updated correctly.
    """
    
    def __init__(self):
        """Initialize the unique ID mapping."""
        super().__init__(update_keys=True, update_values=False)
    
    def update(self, old_id, new_id):
        """
        Update mapping when a full ID changes by handling the unique ID aspects.
        
        Args:
            old_id: The old full ID
            new_id: The new full ID
            
        Returns:
            bool: True if any updates were made, False otherwise
        """
        old_unique_id = get_unique_id_from_id(old_id)
        new_unique_id = get_unique_id_from_id(new_id)
        
        # If unique IDs are the same, we just need to update the value
        if old_unique_id == new_unique_id:
            # If this unique ID is mapped, update its corresponding full ID
            if old_unique_id in self._storage:
                self._storage[old_unique_id] = new_id
                return True
            return False
        
        # If unique IDs changed, we need to update both key and value
        if old_unique_id in self._storage:
            # Store the value and remove the old mapping
            old_value = self._storage[old_unique_id]
            del self._storage[old_unique_id]
            self._key_log.discard(old_unique_id)
            
            # Create the new mapping
            self._storage[new_unique_id] = new_id
            self._key_log.add(new_unique_id)
            return True
            
        return False
    
    def add_id_mapping(self, full_id):
        """
        Add a mapping from unique ID to full ID.
        
        Args:
            full_id: The full ID to add
            
        Returns:
            str: The unique ID extracted from the full ID
        """
        unique_id = get_unique_id_from_id(full_id)
        if unique_id:
            self.add(unique_id, full_id)
        return unique_id
    
# MARK:- generatorMapping
class GeneratorMapping(Mapping):
    """
    A specialized mapping for managing widget location generators.
    
    This class extends the base Mapping class with functionality specifically
    for managing location generators for widgets. It ensures that when widget IDs
    are updated or deleted, the corresponding location generators are updated correctly.
    """
    
    def __init__(self):
        """Initialize the generator mapping."""
        super().__init__(update_keys=True, update_values=False)
        # Ensure the root location always has a generator
        self._storage[DEFAULT_ROOT_LOCATION] = LocationIDGenerator()
    
    def get_generator(self, container_location):
        """
        Get or create a location generator for a specific container location.
        
        Args:
            container_location: The container location
            
        Returns:
            LocationIDGenerator: The location generator for the container
        """
        if container_location not in self._storage:
            self._storage[container_location] = LocationIDGenerator()
            self._key_log.add(container_location)
        
        return self._storage[container_location]
    
    def get_generator_for_widget(self, widget_id):
        """
        Get the location generator for a widget.
        
        Args:
            widget_id: The widget ID
            
        Returns:
            tuple: (generator, container_location, widget_location_id) or (None, None, None) if invalid
        """
        components = parse_widget_id(widget_id)
        if not components:
            return None, None, None
        
        container_location = components['container_location']
        widget_location_id = components['widget_location_id']
        
        generator = self.get_generator(container_location)
        return generator, container_location, widget_location_id
    
    def delete_widget_location(self, widget_id):
        """
        Delete a widget's location from the appropriate generator.
        
        Args:
            widget_id: The widget ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        generator, container_location, widget_location_id = self.get_generator_for_widget(widget_id)
        if not generator:
            return False
        
        return generator.unregister(widget_location_id)
    
    def register_widget_location(self, widget_id):
        """
        Register a widget's location with the appropriate generator.
        
        Args:
            widget_id: The widget ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        generator, container_location, widget_location_id = self.get_generator_for_widget(widget_id)
        if not generator:
            return False
        
        return generator.register(widget_location_id)
    
    def is_location_registered(self, container_location, widget_location_id):
        """
        Check if a widget location is already registered.
        
        Args:
            container_location: The container location
            widget_location_id: The widget location ID
            
        Returns:
            bool: True if registered, False otherwise
        """
        generator = self.get_generator(container_location)
        return generator.is_registered(widget_location_id)
    
    def generate_location_id(self, container_location):
        """
        Generate a new widget location ID for a container.
        
        Args:
            container_location: The container location
            
        Returns:
            str: A new widget location ID
        """
        generator = self.get_generator(container_location)
        return generator.generate()
    
    def update(self, old_id, new_id):
        """
        Update widget location registrations when a widget ID changes.
        
        Args:
            old_id: The old widget ID
            new_id: The new widget ID
            
        Returns:
            bool: True if any updates were made, False otherwise
        """
        # Only process widget IDs
        if not old_id.startswith(tuple(TypeCodes.get_all_widget_codes())):
            return False
            
        old_components = parse_widget_id(old_id)
        new_components = parse_widget_id(new_id)
        
        if not old_components or not new_components:
            return False
        
        old_container_location = old_components['container_location']
        old_widget_location_id = old_components['widget_location_id']
        
        new_container_location = new_components['container_location']
        new_widget_location_id = new_components['widget_location_id']
        
        # If neither location changed, nothing to do
        if (old_container_location == new_container_location and 
            old_widget_location_id == new_widget_location_id):
            return False
        
        # Unregister from old location
        old_generator = self.get_generator(old_container_location)
        old_generator.unregister(old_widget_location_id)
        
        # Register with new location
        new_generator = self.get_generator(new_container_location)
        return new_generator.register(new_widget_location_id)
    
    def cleanup_container_locations(self, container_path):
        """
        Clean up all location generators for a container and its children.
        
        This is called when a container is unregistered to ensure all
        its location generators are removed.
        
        Args:
            container_path: The container's full path
            
        Returns:
            bool: True if any generators were removed
        """
        updated = False
        
        # Remove the exact container path generator
        if container_path in self._storage and container_path != DEFAULT_ROOT_LOCATION:
            del self._storage[container_path]
            self._key_log.discard(container_path)
            updated = True
        
        # Also remove any child paths (starting with container_path/)
        prefix = container_path + "/"
        for path in list(self._storage.keys()):
            if path.startswith(prefix):
                del self._storage[path]
                self._key_log.discard(path)
                updated = True
        
        return updated