"""
ID Generator module.

This module contains the UniqueIDGenerator class for generating unique
identifiers used in the ID system.
"""

import string

#MARK: - Base62 encoding utilities

# Character set for base62 encoding (0-9, A-Z, a-z)
BASE62_CHARS = string.digits + string.ascii_uppercase + string.ascii_lowercase

def int_to_base62(num):
    """Convert an integer to a base62 string."""
    if num == 0:
        return BASE62_CHARS[0]
    
    result = ""
    base = len(BASE62_CHARS)
    
    while num:
        num, remainder = divmod(num, base)
        result = BASE62_CHARS[remainder] + result
        
    return result

def base62_to_int(base62_str):
    """Convert a base62 string to an integer."""
    result = 0
    base = len(BASE62_CHARS)
    
    for char in base62_str:
        result = result * base + BASE62_CHARS.index(char)
        
    return result

#MARK: - UniqueIDGenerator class

class UniqueIDGenerator:
    """
    Generates unique IDs for components in the ID system.
    
    This class uses an incremental counter with base62 encoding to generate
    compact string IDs. It also tracks used IDs to prevent collisions.
    """
    
    def __init__(self, counter_start=0):
        """
        Initialize the generator with a starting counter value.
        
        Args:
            counter_start: Initial value for the ID counter
        """
        self._counter = counter_start
        self._used_ids = set()
    
    def generate(self):
        """
        Generate a new unique ID.
        
        Returns:
            str: A unique base62-encoded ID
        """
        # Find an available ID
        while True:
            self._counter += 1
            unique_id = int_to_base62(self._counter)
            
            if unique_id not in self._used_ids:
                self._used_ids.add(unique_id)
                return unique_id
    
    def register(self, unique_id):
        """
        Register an existing ID to prevent future collisions.
        
        Args:
            unique_id: The ID to register
            
        Returns:
            bool: True if registration succeeded, False if ID already registered
        """
        if unique_id in self._used_ids:
            return False
        
        # Try to convert to an integer to update counter
        try:
            id_int = base62_to_int(unique_id)
            if id_int > self._counter:
                self._counter = id_int
        except ValueError:
            # If not a valid base62 ID, just register it
            pass
        
        self._used_ids.add(unique_id)
        return True
    
    def unregister(self, unique_id):
        """
        Unregister an ID to allow reuse.
        
        Args:
            unique_id: The ID to unregister
            
        Returns:
            bool: True if unregistration succeeded, False if ID wasn't registered
        """
        if unique_id in self._used_ids:
            self._used_ids.remove(unique_id)
            return True
        return False
    
    def is_registered(self, unique_id):
        """
        Check if an ID is already registered.
        
        Args:
            unique_id: The ID to check
            
        Returns:
            bool: True if the ID is registered, False otherwise
        """
        return unique_id in self._used_ids
    
    def reset(self):
        """Reset the generator, clearing all registered IDs."""
        self._counter = 0
        self._used_ids.clear()


#MARK: - Location ID Generator

class LocationIDGenerator:
    """
    Generates and manages widget location IDs within a specific container location.
    
    Each container location has its own generator to ensure stable and predictable
    IDs within each location context.
    """
    
    def __init__(self):
        """Initialize the location ID generator."""
        self._counter = 0
        self._used_ids = set()
    
    def generate(self):
        """
        Generate a new unique location ID.
        
        Returns:
            str: A unique ID for use at this location
        """
        # Find an available ID
        while True:
            self._counter += 1
            # For simplicity, we use string numbers as location IDs
            # Advanced implementations can use base62 encoding like the UniqueIDGenerator
            location_id = str(self._counter)
            
            if location_id not in self._used_ids:
                self._used_ids.add(location_id)
                return location_id
    
    def register(self, location_id):
        """
        Register an existing location ID to prevent future collisions.
        
        Args:
            location_id: The location ID to register
            
        Returns:
            bool: True if registration succeeded, False if ID already registered
        """
        if location_id in self._used_ids:
            return False
        
        # Try to convert to an integer to update counter
        try:
            id_int = int(location_id)
            if id_int > self._counter:
                self._counter = id_int
        except ValueError:
            # If not a valid integer ID, just register it
            pass
        
        self._used_ids.add(location_id)
        return True
    
    def unregister(self, location_id):
        """
        Unregister a location ID to allow reuse.
        
        Args:
            location_id: The location ID to unregister
            
        Returns:
            bool: True if unregistration succeeded, False if ID wasn't registered
        """
        if location_id in self._used_ids:
            self._used_ids.remove(location_id)
            return True
        return False
    
    def is_registered(self, location_id):
        """
        Check if a location ID is already registered.
        
        Args:
            location_id: The location ID to check
            
        Returns:
            bool: True if the ID is registered, False otherwise
        """
        return location_id in self._used_ids
    
    def reset(self):
        """Reset the generator, clearing all registered location IDs."""
        self._counter = 0
        self._used_ids.clear()