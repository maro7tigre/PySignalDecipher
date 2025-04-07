"""
Simple ID Registry module.

This module contains a simplified ID registry implementation for basic ID management.
"""

# Global simple ID registry instance
_simple_id_registry = None

def get_simple_id_registry():
    """
    Get the global simple ID registry instance.
    
    Returns:
        SimpleIDRegistry: The global simple ID registry
    """
    global _simple_id_registry
    if _simple_id_registry is None:
        _simple_id_registry = SimpleIDRegistry()
    
    return _simple_id_registry

#MARK: - SimpleIDRegistry class

class SimpleIDRegistry:
    """
    A simplified ID registry for creating unique IDs.
    
    This class provides a way to create unique IDs for components
    that don't require the full hierarchy of the main ID system.
    """
    
    def __init__(self):
        """Initialize the simple ID registry."""
        # Set of registered IDs
        self._registered_ids = set()
        
        # Counters for auto-generated IDs by type code
        self._type_counters = {}
    
    def register(self, type_code, custom_id=None):
        """
        Register and generate a unique ID.
        
        Args:
            type_code: The type code for the component
            custom_id: An optional custom ID to use (default: None, will be generated)
            
        Returns:
            str: The generated or custom ID
        """
        # Use custom ID if provided, or generate a new one
        if custom_id:
            id_str = custom_id
            
            # Check for ID collisions
            if id_str in self._registered_ids:
                # If custom ID collides, append a suffix
                suffix = 1
                while f"{id_str}_{suffix}" in self._registered_ids:
                    suffix += 1
                id_str = f"{id_str}_{suffix}"
        else:
            # Initialize counter for this type if needed
            if type_code not in self._type_counters:
                self._type_counters[type_code] = 0
            
            # Generate ID and ensure it's unique
            while True:
                # Increment counter and create ID
                self._type_counters[type_code] += 1
                id_str = f"{type_code}:{self._type_counters[type_code]}"
                
                # Check if this ID is already registered
                if id_str not in self._registered_ids:
                    break
        
        # Register the ID
        self._registered_ids.add(id_str)
        
        return id_str
    
    def unregister(self, id_str):
        """
        Unregister an ID from the registry.
        
        Args:
            id_str: The ID to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        if id_str in self._registered_ids:
            self._registered_ids.remove(id_str)
            return True
        return False
    
    def is_registered(self, id_str):
        """
        Check if an ID is registered.
        
        Args:
            id_str: The ID to check
            
        Returns:
            bool: True if registered, False otherwise
        """
        return id_str in self._registered_ids
    
    def get_all_ids(self):
        """
        Get all registered IDs.
        
        Returns:
            list: A list of all registered IDs
        """
        return list(self._registered_ids)
    
    def clear(self):
        """Clear all registrations."""
        self._registered_ids.clear()
        self._type_counters.clear()