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
        self._registry = {}  # type: Dict[str, str]
        self._counters = {}  # type: Dict[str, int]
        
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
            self._registry[id_str] = name
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
        self._registry[new_id] = name
        
        return new_id
    
    def get_name(self, id_str: str) -> Optional[str]:
        """
        Get the name for a registered ID.
        
        Args:
            id_str: ID string to look up
            
        Returns:
            Name or None if not registered
        """
        for name, registered_id in self._registry.items():
            if registered_id == id_str:
                return name
        return None
    
    def is_registered(self, name: str) -> bool:
        """
        Check if a name is registered.
        
        Args:
            name: Name to check
            
        Returns:
            True if registered, False otherwise
        """
        return name in self._registry
    
    def unregister(self, id_str: str) -> bool:
        """
        Unregister a name.
        
        Args:
            name: Name to unregister
            
        Returns:
            True if successfully unregistered, False if not found
        """
        if id_str not in self._registry:
            return False
            
        del self._registry[id_str]
        return True
    
    def reset(self):
        """Reset the registry (for testing only)."""
        self._registry.clear()
        self._counters.clear()


def get_simple_id_registry():
    """Get the singleton SimpleIDRegistry instance."""
    return SimpleIDRegistry.get_instance()