"""
Mapping module.

This module provides a trackable dictionary-like class that automatically updates
when IDs change within the ID system.
"""

import collections.abc # Use this for robust checking

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
        if isinstance(value, list):
            for item in value:
                self._value_log.discard(item)
        else:
            self._value_log.discard(value)
        
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