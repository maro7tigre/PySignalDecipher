"""
Simple ID registry for creating and tracking IDs.

This module provides a simple registry for tracking and generating IDs
that integrate with the main ID system.
"""
from typing import Dict, Set, Optional
from .registry import get_id_registry

class SimpleIDRegistry:
    """
    Simple registry for tracking and generating IDs.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = SimpleIDRegistry()
        return cls._instance
    
    def __init__(self):
        """Initialize the ID registry."""
        if SimpleIDRegistry._instance is not None:
            raise RuntimeError("Use get_simple_id_registry() to get the singleton instance")
            
        SimpleIDRegistry._instance = self
        self._id_to_name = {}  # type: Dict[str, str]
        self._name_to_id = {}  # type: Dict[str, str]
        self._counters = {}    # type: Dict[str, int]
        
        # Get the main ID registry for unique ID generation
        self._id_registry = get_id_registry()
    
    def register(self, name: str, type_code: str, id_str: Optional[str] = None) -> str:
        """
        Register a name with an ID.
        
        Args:
            name: Name to register
            type_code: Type code for the ID
            id_str: Optional existing ID to use
            
        Returns:
            The registered ID string
        """  
        # If ID is provided, use it
        if id_str:
            self._id_to_name[id_str] = name
            self._name_to_id[name] = id_str
            return id_str
            
        # Generate a new ID
        if type_code not in self._counters:
            self._counters[type_code] = 0
            
        # Increment counter
        self._counters[type_code] += 1
        
        # Generate ID using the ID registry's generator
        id_generator = self._id_registry._id_generator
        unique_id = id_generator._encode_to_base62(self._counters[type_code])
        
        # Format ID as [type_code]:[unique_id]
        new_id = f"{type_code}:{unique_id}"
        
        # Register the ID
        self._id_to_name[new_id] = name
        self._name_to_id[name] = new_id
        
        return new_id
    
    def get_name(self, id_str: str) -> Optional[str]:
        """
        Get the name for a registered ID.
        
        Args:
            id_str: ID string to look up
            
        Returns:
            Name or None if not registered
        """
        return self._id_to_name.get(id_str)
    
    def get_id(self, name: str) -> Optional[str]:
        """
        Get the ID for a registered name.
        
        Args:
            name: Name to look up
            
        Returns:
            ID string or None if not registered
        """
        return self._name_to_id.get(name)
    
    def is_registered(self, name: str) -> bool:
        """
        Check if a name is registered.
        
        Args:
            name: Name to check
            
        Returns:
            True if registered, False otherwise
        """
        return name in self._name_to_id
    
    def unregister_by_id(self, id_str: str) -> bool:
        """
        Unregister by ID.
        
        Args:
            id_str: ID to unregister
            
        Returns:
            True if successfully unregistered, False if not found
        """
        if id_str not in self._id_to_name:
            return False
            
        name = self._id_to_name[id_str]
        del self._id_to_name[id_str]
        
        if name in self._name_to_id:
            del self._name_to_id[name]
            
        return True
    
    def unregister_by_name(self, name: str) -> bool:
        """
        Unregister by name.
        
        Args:
            name: Name to unregister
            
        Returns:
            True if successfully unregistered, False if not found
        """
        if name not in self._name_to_id:
            return False
            
        id_str = self._name_to_id[name]
        del self._name_to_id[name]
        
        if id_str in self._id_to_name:
            del self._id_to_name[id_str]
            
        return True
    
    def reset(self):
        """Reset the registry (for testing only)."""
        self._id_to_name.clear()
        self._name_to_id.clear()
        self._counters.clear()


def get_simple_id_registry():
    """Get the singleton SimpleIDRegistry instance."""
    return SimpleIDRegistry.get_instance()