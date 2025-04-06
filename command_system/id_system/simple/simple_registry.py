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
    A simplified ID registry for creating and tracking consistent IDs.
    
    This class provides a way to create and track consistent IDs for components
    that don't require the full hierarchy of the main ID system.
    """
    
    def __init__(self):
        """Initialize the simple ID registry."""
        # Maps names to ID strings
        self._name_to_id = {}
        
        # Maps ID strings to names
        self._id_to_name = {}
        
        # Counters for auto-generated IDs by type code
        self._type_counters = {}
    
    def register(self, name, type_code, custom_id=None):
        """
        Register a name with the registry.
        
        Args:
            name: The name to register
            type_code: The type code for the component
            custom_id: An optional custom ID to use (default: None, will be generated)
            
        Returns:
            str: The generated or custom ID
        """
        # Check if name is already registered
        if name in self._name_to_id:
            return self._name_to_id[name]
        
        # Use custom ID if provided, or generate a new one
        if custom_id:
            id_str = custom_id
        else:
            # Initialize counter for this type if needed
            if type_code not in self._type_counters:
                self._type_counters[type_code] = 0
            
            # Increment counter and create ID
            self._type_counters[type_code] += 1
            id_str = f"{type_code}:{self._type_counters[type_code]}"
        
        # Check for ID collisions
        if id_str in self._id_to_name:
            # If custom ID collides, append a suffix
            if custom_id:
                suffix = 1
                while f"{id_str}_{suffix}" in self._id_to_name:
                    suffix += 1
                id_str = f"{id_str}_{suffix}"
            # If generated ID collides, increment counter and try again
            else:
                self._type_counters[type_code] += 1
                id_str = f"{type_code}:{self._type_counters[type_code]}"
        
        # Register the name and ID
        self._name_to_id[name] = id_str
        self._id_to_name[id_str] = name
        
        return id_str
    
    def unregister(self, name_or_id):
        """
        Unregister a name or ID from the registry.
        
        Args:
            name_or_id: The name or ID to unregister
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if it's a name
        if name_or_id in self._name_to_id:
            id_str = self._name_to_id[name_or_id]
            del self._name_to_id[name_or_id]
            del self._id_to_name[id_str]
            return True
        
        # Check if it's an ID
        if name_or_id in self._id_to_name:
            name = self._id_to_name[name_or_id]
            del self._id_to_name[name_or_id]
            del self._name_to_id[name]
            return True
        
        # Not found
        return False
    
    def get_id(self, name):
        """
        Get the ID for a registered name.
        
        Args:
            name: The registered name
            
        Returns:
            str: The ID for the name, or None if not found
        """
        return self._name_to_id.get(name)
    
    def get_name(self, id_str):
        """
        Get the name for a registered ID.
        
        Args:
            id_str: The registered ID
            
        Returns:
            str: The name for the ID, or None if not found
        """
        return self._id_to_name.get(id_str)
    
    def is_registered(self, name_or_id):
        """
        Check if a name or ID is registered.
        
        Args:
            name_or_id: The name or ID to check
            
        Returns:
            bool: True if registered, False otherwise
        """
        return name_or_id in self._name_to_id or name_or_id in self._id_to_name
    
    def get_all_ids(self):
        """
        Get all registered IDs.
        
        Returns:
            list: A list of all registered IDs
        """
        return list(self._id_to_name.keys())
    
    def get_all_names(self):
        """
        Get all registered names.
        
        Returns:
            list: A list of all registered names
        """
        return list(self._name_to_id.keys())
    
    def get_all_mappings(self):
        """
        Get all name-to-ID mappings.
        
        Returns:
            dict: A dictionary mapping names to IDs
        """
        return self._name_to_id.copy()
    
    def clear(self):
        """Clear all registrations."""
        self._name_to_id.clear()
        self._id_to_name.clear()
        self._type_counters.clear()