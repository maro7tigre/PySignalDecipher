"""
Object registry for tracking objects by ID.
"""

class Registry:
    """
    Singleton registry for tracking objects by ID.
    Used for serialization and deserialization to maintain object references.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = Registry()
        return cls._instance
    
    def __init__(self):
        """Initialize the registry."""
        if Registry._instance is not None:
            raise RuntimeError("Use Registry.get_instance() to get the singleton instance")
            
        Registry._instance = self
        self._objects = {}  # ID -> object
        self._object_types = {}  # ID -> type name
        
    def register_object(self, obj, obj_id=None):
        """
        Register an object with the registry.
        
        Args:
            obj: The object to register
            obj_id (str, optional): ID to use for the object.
                                  If not provided, uses obj.get_id()
        
        Returns:
            str: The ID of the registered object
        """
        if obj_id is None:
            # Try to get ID from object
            if hasattr(obj, "get_id") and callable(getattr(obj, "get_id")):
                obj_id = obj.get_id()
            else:
                obj_id = str(id(obj))
                
        self._objects[obj_id] = obj
        self._object_types[obj_id] = f"{obj.__class__.__module__}.{obj.__class__.__name__}"
        
        return obj_id
        
    def unregister_object(self, obj_id):
        """
        Remove an object from the registry.
        
        Args:
            obj_id (str): ID of the object to remove
            
        Returns:
            bool: True if object was removed, False if not found
        """
        if obj_id in self._objects:
            del self._objects[obj_id]
            if obj_id in self._object_types:
                del self._object_types[obj_id]
            return True
        return False
        
    def get_object(self, obj_id):
        """
        Get an object by ID.
        
        Args:
            obj_id (str): ID of the object to get
            
        Returns:
            The object, or None if not found
        """
        return self._objects.get(obj_id)
        
    def get_object_type(self, obj_id):
        """
        Get the type name of an object by ID.
        
        Args:
            obj_id (str): ID of the object
            
        Returns:
            str: Type name of the object, or None if not found
        """
        return self._object_types.get(obj_id)
        
    def clear(self):
        """Clear the registry."""
        self._objects.clear()
        self._object_types.clear()
        
    def serialize_object(self, obj):
        """
        Serialize an object, registering it if needed.
        
        Args:
            obj: Object to serialize
            
        Returns:
            dict: Serialized object state
        """
        # Register object if needed
        obj_id = self.register_object(obj)
        
        # If object has serialize method, use it
        if hasattr(obj, "serialize") and callable(getattr(obj, "serialize")):
            state = obj.serialize()
        else:
            # Basic serialization
            state = {}
            
            # Try to get attributes
            for attr_name in dir(obj):
                # Skip private attributes and methods
                if attr_name.startswith("_") or callable(getattr(obj, attr_name)):
                    continue
                    
                # Get attribute value
                try:
                    value = getattr(obj, attr_name)
                    
                    # Skip non-serializable types and handle common types
                    if isinstance(value, (int, float, str, bool)) or value is None:
                        state[attr_name] = value
                    elif isinstance(value, list):
                        # Convert lists to serializable form
                        serializable_list = []
                        for item in value:
                            if isinstance(item, (int, float, str, bool)) or item is None:
                                serializable_list.append(item)
                        state[attr_name] = serializable_list
                    elif isinstance(value, dict):
                        # Convert dicts with simple keys and values
                        serializable_dict = {}
                        for k, v in value.items():
                            if isinstance(k, str) and isinstance(v, (int, float, str, bool)) or v is None:
                                serializable_dict[k] = v
                        state[attr_name] = serializable_dict
                except Exception as e:
                    print(f"Warning: could not serialize attribute {attr_name}: {e}")
        
        # Add object ID and type
        return {
            "id": obj_id,
            "type": self._object_types[obj_id],
            "state": state
        }