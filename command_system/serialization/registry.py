"""
Type and factory registry for serialization.

This module provides the registry system for managing types, factories,
and custom serializers during serialization and deserialization.
"""
from typing import Dict, Any, Optional, Type, Callable, Set, Tuple, List, TypeVar

T = TypeVar('T')


class RegistryEngine:
    """
    Engine for managing type registrations and object creation.
    Handles type mapping, object factories, and custom serializers.
    """
    
    def __init__(self):
        """Initialize the registry engine."""
        # Type mappings (name -> class)
        self._type_mappings: Dict[str, Type] = {}
        
        # Factory functions (type name -> factory function)
        self._factories: Dict[str, Callable[..., Any]] = {}
        
        # Custom serializers (type name -> (serializer, deserializer))
        self._serializers: Dict[str, Tuple[Callable, Callable]] = {}
        
        # Type hierarchy cache (class -> [parent classes])
        self._type_hierarchy: Dict[Type, List[Type]] = {}
        
    def register_type(self, type_name: str, cls: Type) -> None:
        """
        Register a type mapping.
        
        Args:
            type_name: Identifier for the type
            cls: Class to associate with the type name
        """
        self._type_mappings[type_name] = cls
        
        # Clear hierarchy cache entry for this type if exists
        if cls in self._type_hierarchy:
            del self._type_hierarchy[cls]
            
    def register_factory(self, type_name: str, factory: Callable[..., T]) -> None:
        """
        Register a factory function for a type.
        
        Args:
            type_name: Type identifier
            factory: Function that creates an instance of the type
        """
        self._factories[type_name] = factory
        
    def register_serializer(self, type_name: str, 
                          serializer: Callable[[T, Dict], Dict],
                          deserializer: Callable[[Dict, Dict], T]) -> None:
        """
        Register custom serializer and deserializer for a type.
        
        Args:
            type_name: Type identifier
            serializer: Function to convert object to dictionary
            deserializer: Function to create object from dictionary
        """
        self._serializers[type_name] = (serializer, deserializer)
        
    def get_type(self, type_name: str) -> Optional[Type]:
        """
        Get the class associated with a type name.
        
        Args:
            type_name: Type identifier
            
        Returns:
            Associated class or None if not found
        """
        return self._type_mappings.get(type_name)
        
    def get_factory(self, type_name: str) -> Optional[Callable]:
        """
        Get the factory function for a type.
        
        Args:
            type_name: Type identifier
            
        Returns:
            Factory function or None if not found
        """
        return self._factories.get(type_name)
        
    def get_serializer(self, type_name: str) -> Optional[Tuple[Callable, Callable]]:
        """
        Get custom serializer/deserializer for a type.
        
        Args:
            type_name: Type identifier
            
        Returns:
            Tuple of (serializer, deserializer) or None if not found
        """
        return self._serializers.get(type_name)
        
    def create_instance(self, type_name: str, **kwargs) -> Optional[Any]:
        """
        Create an instance of a type using its factory.
        
        Args:
            type_name: Type identifier
            **kwargs: Arguments to pass to the factory
            
        Returns:
            Created instance or None if factory not found
        """
        factory = self.get_factory(type_name)
        if factory:
            return factory(**kwargs)
            
        # Try using class constructor if available
        cls = self.get_type(type_name)
        if cls:
            try:
                return cls(**kwargs)
            except Exception as e:
                print(f"Error creating instance of {type_name}: {e}")
                
        return None
        
    def get_type_name(self, obj: Any) -> Optional[str]:
        """
        Get the type name for an object.
        
        Args:
            obj: Object to get type name for
            
        Returns:
            Type name or None if not registered
        """
        # Get the object's class
        obj_class = obj.__class__
        
        # First, look for exact type match
        for type_name, cls in self._type_mappings.items():
            if cls is obj_class:
                return type_name
                
        # If not found, check parent classes
        for type_name, cls in self._type_mappings.items():
            if isinstance(obj, cls):
                return type_name
                
        return None
        
    def find_best_serializer(self, obj: Any) -> Optional[Tuple[str, Callable, Callable]]:
        """
        Find the best serializer for an object based on its type hierarchy.
        
        Args:
            obj: Object to find serializer for
            
        Returns:
            Tuple of (type_name, serializer, deserializer) or None if not found
        """
        # First try to get type name
        type_name = self.get_type_name(obj)
        if type_name:
            serializer_pair = self.get_serializer(type_name)
            if serializer_pair:
                return (type_name, *serializer_pair)
                
        # If no direct match, try parent classes
        obj_class = obj.__class__
        for type_name, (serializer, deserializer) in self._serializers.items():
            cls = self.get_type(type_name)
            if cls and isinstance(obj, cls):
                return (type_name, serializer, deserializer)
                
        return None


# Singleton instance
_registry_instance = None

def get_registry_engine() -> RegistryEngine:
    """
    Get the singleton registry engine instance.
    
    Returns:
        RegistryEngine singleton instance
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = RegistryEngine()
    return _registry_instance