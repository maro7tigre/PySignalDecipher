"""
Serialization utilities for commands and objects.
"""
import importlib


def deserialize_command(state, registry):
    """
    Deserialize a command from its state.
    
    Args:
        state (dict): Serialized command state
        registry: Object registry for resolving references
        
    Returns:
        Command: Deserialized command, or None if deserialization failed
    """
    if not state or not isinstance(state, dict):
        return None
        
    # Extract command type
    cmd_type = state.get("type")
    
    # Handle known command types
    if cmd_type == "PropertyCommand":
        from command_system.command import PropertyCommand
        return PropertyCommand.deserialize(state, registry)
        
    # Try to import and deserialize by class path
    try:
        module_path, class_name = cmd_type.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cmd_class = getattr(module, class_name)
        
        # Call deserialize class method
        if hasattr(cmd_class, "deserialize") and callable(getattr(cmd_class, "deserialize")):
            return cmd_class.deserialize(state, registry)
    except (ImportError, AttributeError, ValueError) as e:
        print(f"Error deserializing command: {e}")
        
    return None


def deserialize_object(serialized, registry):
    """
    Deserialize an object from its serialized state.
    
    Args:
        serialized (dict): Serialized object state
        registry: Object registry for resolving references
        
    Returns:
        The deserialized object, or None if deserialization failed
    """
    if not serialized or not isinstance(serialized, dict):
        return None
        
    obj_id = serialized.get("id")
    obj_type = serialized.get("type")
    obj_state = serialized.get("state", {})
    
    if not obj_id or not obj_type:
        return None
        
    # Check if object already exists in registry
    existing_obj = registry.get_object(obj_id)
    if existing_obj:
        return existing_obj
        
    # Import class by name
    try:
        module_path, class_name = obj_type.rsplit(".", 1)
        module = importlib.import_module(module_path)
        obj_class = getattr(module, class_name)
        
        # Create instance
        obj = obj_class()
        
        # Set ID
        if hasattr(obj, "set_id") and callable(getattr(obj, "set_id")):
            obj.set_id(obj_id)
            
        # Register object early to handle circular references
        registry.register_object(obj, obj_id)
        
        # If object has deserialize method, use it
        if hasattr(obj, "deserialize") and callable(getattr(obj, "deserialize")):
            obj.deserialize(obj_state, registry)
        else:
            # Basic deserialization
            for attr_name, value in obj_state.items():
                # Recursively deserialize nested objects
                if isinstance(value, dict) and "id" in value and "type" in value:
                    value = deserialize_object(value, registry)
                    
                # Set attribute
                try:
                    setattr(obj, attr_name, value)
                except (AttributeError, TypeError) as e:
                    print(f"Error setting attribute {attr_name}: {e}")
        
        return obj
    except (ImportError, AttributeError, ValueError) as e:
        print(f"Error deserializing object: {e}")
        return None