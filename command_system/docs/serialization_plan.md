# Serialization System Implementation Plan

This document outlines the implementation plan for the new serialization system in the PySignalDecipher command framework.

## Phase 1: Core Serialization Framework

### 1.1. Complete SerializationManager Implementation

```python
# serialization/manager.py
def serialize(self, obj: Any, format_type: str = FORMAT_JSON) -> Any:
    """Serialize an object to the specified format."""
    # Create serialization context
    context = {"registry": get_registry_engine(), "references": {}}
    
    # Get adapter for format
    adapter = self._format_adapters.get(format_type)
    if not adapter:
        raise ValueError(f"No adapter found for format: {format_type}")
        
    # Convert object to serializable form
    data = self._serialize_object(obj, context)
    
    # Use adapter to serialize
    return adapter.serialize(data)
```

### 1.2. Complete RegistryEngine Implementation

```python
# serialization/registry.py
def serialize_object(self, obj: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize an object to a dictionary.
    
    Args:
        obj: Object to serialize
        context: Serialization context
        
    Returns:
        Dictionary representation of the object
    """
    # Find the appropriate serializer
    result = self.find_best_serializer(obj)
    if result:
        type_name, serializer, _ = result
        return serializer(obj, context)
        
    # Default serialization for simple types
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
        
    # Default dictionary serialization
    if isinstance(obj, dict):
        return {
            "$type": "dict",
            "items": {
                str(k): self.serialize_object(v, context) 
                for k, v in obj.items()
            }
        }
        
    # Default list serialization
    if isinstance(obj, (list, tuple)):
        return {
            "$type": "list" if isinstance(obj, list) else "tuple",
            "items": [self.serialize_object(item, context) for item in obj]
        }
        
    # Cannot serialize
    raise TypeError(f"Cannot serialize object of type: {type(obj).__name__}")
```

### 1.3. Implement JSON Adapter

```python
# serialization/adapters/json_adapter.py
class JSONAdapter:
    """Adapter for JSON serialization and deserialization."""
    
    def serialize(self, data: Dict) -> str:
        """
        Serialize dictionary to JSON string.
        
        Args:
            data: Dictionary to serialize
            
        Returns:
            JSON string
        """
        return json.dumps(data, cls=JSONEncoder, indent=2)
        
    def deserialize(self, json_str: str) -> Dict:
        """
        Deserialize JSON string to dictionary.
        
        Args:
            json_str: JSON string to parse
            
        Returns:
            Deserialized dictionary
        """
        return json.loads(json_str, object_hook=json_decoder)
```

## Phase 2: Observable Serialization

### 2.1. Observable Serializer

```python
# serialization/serializers/observable.py
def serialize_observable(obj: Observable, context: Dict) -> Dict[str, Any]:
    """
    Serialize Observable object to dictionary.
    
    Args:
        obj: Observable object
        context: Serialization context
        
    Returns:
        Dictionary representation of Observable
    """
    registry = context["registry"]
    references = context.get("references", {})
    
    # Check if already serialized
    obj_id = obj.get_id()
    if obj_id in references:
        return {"$ref": obj_id}
        
    # Add to references
    references[obj_id] = True
    
    # Get object type
    type_name = registry.get_type_name(obj)
    if not type_name:
        type_name = obj.__class__.__name__
        
    # Get serializable properties
    if hasattr(obj, "get_serializable_properties"):
        properties = obj.get_serializable_properties()
    else:
        # Use default property discovery
        properties = {}
        for name in dir(obj):
            if name.startswith("_"):
                continue
                
            value = getattr(obj, name)
            if callable(value) or isinstance(value, property):
                continue
                
            properties[name] = value
            
    # Serialize properties
    serialized_props = {}
    for name, value in properties.items():
        serialized_props[name] = registry.serialize_object(value, context)
        
    # Build result
    result = {
        "$type": type_name,
        "$id": obj_id,
        "properties": serialized_props
    }
    
    # Add relationship info
    if hasattr(obj, "get_parent_id") and obj.get_parent_id():
        result["parent_id"] = obj.get_parent_id()
        
    if hasattr(obj, "get_generation"):
        result["generation"] = obj.get_generation()
        
    return result
```

### 2.2. Observable Deserializer

```python
# serialization/serializers/observable.py
def deserialize_observable(data: Dict, context: Dict) -> Observable:
    """
    Deserialize Observable from dictionary.
    
    Args:
        data: Serialized data
        context: Deserialization context
        
    Returns:
        Deserialized Observable instance
    """
    registry = context["registry"]
    references = context.get("references", {})
    
    # Handle references
    if "$ref" in data:
        ref_id = data["$ref"]
        if ref_id in references:
            return references[ref_id]
        else:
            raise ValueError(f"Reference not found: {ref_id}")
            
    # Get type and ID
    type_name = data.get("$type")
    obj_id = data.get("$id")
    
    if not type_name:
        raise ValueError("Missing $type in serialized data")
        
    # Create instance
    obj = registry.create_instance(type_name)
    
    # Store in references
    if obj_id:
        references[obj_id] = obj
        obj.set_id(obj_id)
        
    # Set parent ID if present
    if "parent_id" in data and hasattr(obj, "set_parent_id"):
        obj.set_parent_id(data["parent_id"])
        
    # Set generation if present
    if "generation" in data and hasattr(obj, "set_generation"):
        obj.set_generation(data["generation"])
        
    # Set properties
    properties = data.get("properties", {})
    for name, value in properties.items():
        # Handle references and complex types
        if isinstance(value, dict) and ("$type" in value or "$ref" in value):
            value = registry.deserialize_object(value, context)
            
        setattr(obj, name, value)
        
    return obj
```

## Phase 3: Command Serialization

### 3.1. Command Serializer

```python
# serialization/serializers/command.py
def serialize_command(command: Command, context: Dict) -> Dict[str, Any]:
    """
    Serialize command to dictionary.
    
    Args:
        command: Command object
        context: Serialization context
        
    Returns:
        Dictionary representation of command
    """
    registry = context["registry"]
    
    # Get command type
    if hasattr(command, "get_command_type"):
        type_name = command.get_command_type()
    else:
        type_name = command.__class__.__name__
        
    # Get command state
    if hasattr(command, "get_serializable_state"):
        state = command.get_serializable_state()
    else:
        # Use default state extraction
        state = {}
        for name in dir(command):
            if name.startswith("_"):
                continue
                
            value = getattr(command, name)
            if callable(value) or isinstance(value, property):
                continue
                
            state[name] = value
            
    # Serialize state
    serialized_state = {}
    for name, value in state.items():
        serialized_state[name] = registry.serialize_object(value, context)
        
    # Handle CompoundCommand
    if isinstance(command, CompoundCommand):
        # Serialize child commands
        serialized_state["commands"] = [
            serialize_command(cmd, context)
            for cmd in command.commands
        ]
        
    return {
        "$type": type_name,
        "state": serialized_state
    }
```

### 3.2. Command Deserializer

```python
# serialization/serializers/command.py
def deserialize_command(data: Dict, context: Dict) -> Command:
    """
    Deserialize command from dictionary.
    
    Args:
        data: Serialized data
        context: Deserialization context
        
    Returns:
        Deserialized command instance
    """
    registry = context["registry"]
    
    # Get type
    type_name = data.get("$type")
    if not type_name:
        raise ValueError("Missing $type in serialized command data")
        
    # Create instance
    command = registry.create_instance(type_name)
    
    # Set state
    state = data.get("state", {})
    for name, value in state.items():
        # Skip commands list for CompoundCommand (handled separately)
        if name == "commands" and isinstance(command, CompoundCommand):
            continue
            
        # Handle references and complex types
        if isinstance(value, dict) and ("$type" in value or "$ref" in value):
            value = registry.deserialize_object(value, context)
            
        setattr(command, name, value)
        
    # Handle CompoundCommand
    if isinstance(command, CompoundCommand) and "commands" in state:
        # Deserialize child commands
        for cmd_data in state["commands"]:
            child_cmd = deserialize_command(cmd_data, context)
            command.add_command(child_cmd)
            
    return command
```

## Phase 4: Integration with Project Manager

### 4.1. Update ProjectManager.save_project method

```python
# project/project_manager.py
def save_project(self, model: Observable, filename: Optional[str] = None, 
                format_type: Optional[str] = None, save_layout: Optional[bool] = None) -> bool:
    """
    Save project to file.
    
    Args:
        model: Observable model to save
        filename: Path to save to (uses current filename if None)
        format_type: Serialization format (uses default if None)
        save_layout: Whether to save layout with project (uses default if None)
        
    Returns:
        True if saved successfully
    """
    # Resolve filename and format
    if not filename:
        filename = self._current_filename
        if not filename:
            return False
            
    if not format_type:
        format_type = self._default_format
        
    if save_layout is None:
        save_layout = self._save_layouts
        
    # Call before save callbacks
    for callback in self._before_save_callbacks.values():
        callback(model, filename)
        
    try:
        # Get serialization manager
        from ..serialization.manager import get_serialization_manager
        serialization_manager = get_serialization_manager()
        
        # Serialize model
        serialized_data = serialization_manager.serialize(model, format_type)
        
        # Write to file
        if format_type == self.FORMAT_JSON:
            with open(filename, 'w') as f:
                f.write(serialized_data)
        else:
            with open(filename, 'wb') as f:
                f.write(serialized_data)
            
        # Save layout if enabled
        layout_success = True
        if save_layout and self._save_layout_func:
            layout_success = self._save_layout_func(filename)
            
        # Update current filename
        self._current_filename = filename
        
        # Call after save callbacks
        for callback in self._after_save_callbacks.values():
            callback(model, filename, True)
            
        return layout_success
    except Exception as e:
        print(f"Error saving project: {e}")
        
        # Call after save callbacks with failure
        for callback in self._after_save_callbacks.values():
            callback(model, filename, False)
            
        return False
```

### 4.2. Update ProjectManager.load_project method

```python
# project/project_manager.py
def load_project(self, filename: str, format_type: Optional[str] = None,
                load_layout: Optional[bool] = None) -> Optional[Observable]:
    """
    Load project from file.
    
    Args:
        filename: Path to load from
        format_type: Serialization format (auto-detect if None)
        load_layout: Whether to load layout with project (uses default if None)
        
    Returns:
        Loaded model, or None if loading failed
    """
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return None
        
    if not format_type:
        # Auto-detect format from extension
        ext = os.path.splitext(filename)[1].lower()
        for fmt, fmt_ext in self._format_extensions.items():
            if ext == fmt_ext:
                format_type = fmt
                break
        
        if not format_type:
            format_type = self._default_format
            
    if load_layout is None:
        load_layout = self._save_layouts
        
    # Call before load callbacks
    for callback in self._before_load_callbacks.values():
        callback(filename)
        
    try:
        # Get serialization manager
        from ..serialization.manager import get_serialization_manager
        serialization_manager = get_serialization_manager()
        
        # Read file content
        if format_type == self.FORMAT_JSON:
            with open(filename, 'r') as f:
                serialized_data = f.read()
        else:
            with open(filename, 'rb') as f:
                serialized_data = f.read()
                
        # Deserialize model
        model = serialization_manager.deserialize(serialized_data, format_type)
        
        if model:
            # Update current filename
            self._current_filename = filename
            
            # Clear command history
            self._command_manager.clear()
            
            # Load layout if enabled
            if load_layout and self._load_layout_func:
                self._load_layout_func(filename)
                
            # Call after load callbacks
            for callback in self._after_load_callbacks.values():
                callback(model, filename, True)
                
        return model
    except Exception as e:
        print(f"Error loading project: {e}")
        
        # Call after load callbacks with failure
        for callback in self._after_load_callbacks.values():
            callback(None, filename, False)
            
        return None
```

## Phase 5: Registration and Initialization

### 5.1. Initialize SerializationManager

```python
# serialization/__init__.py
# Import components
from .manager import SerializationManager, get_serialization_manager
from .registry import RegistryEngine, get_registry_engine
from .adapters.json_adapter import JSONAdapter
from .serializers.observable import serialize_observable, deserialize_observable
from .serializers.command import serialize_command, deserialize_command

# Initialize serialization system
def initialize_serialization():
    """Initialize the serialization system."""
    manager = get_serialization_manager()
    registry = get_registry_engine()
    
    # Register format adapters
    manager.register_format_adapter(FORMAT_JSON, JSONAdapter())
    
    # Register serializers
    from ..core.observable import Observable
    from ..core.command import Command, CompoundCommand, PropertyCommand
    
    # Register types
    registry.register_type("Observable", Observable)
    registry.register_type("Command", Command)
    registry.register_type("CompoundCommand", CompoundCommand)
    registry.register_type("PropertyCommand", PropertyCommand)
    
    # Register serializers
    registry.register_serializer("Observable", serialize_observable, deserialize_observable)
    registry.register_serializer("Command", serialize_command, deserialize_command)
    registry.register_serializer("CompoundCommand", serialize_command, deserialize_command)
    registry.register_serializer("PropertyCommand", serialize_command, deserialize_command)
    
    print("Serialization system initialized")
```

### 5.2. Connect to Application Startup

```python
# _auto_init.py
def _initialize_system():
    """
    Automatically initialize the command system components.
    """
    # Initialize serialization system
    if importlib.util.find_spec("command_system.serialization") is not None:
        try:
            from command_system.serialization import initialize_serialization
            initialize_serialization()
        except Exception as e:
            print(f"Warning: Failed to initialize serialization system: {e}")
    
    # Check if layout module is available
    if importlib.util.find_spec("command_system.layout") is not None:
        try:
            # Import the layout module first
            from command_system.layout import initialize_layout_integration
            
            # Initialize layout integration
            initialize_layout_integration()
        except Exception as e:
            print(f"Warning: Failed to initialize layout integration: {e}")
```

## Testing Strategy

1. **Unit Tests:**
   - Test each serializer/deserializer individually
   - Test reference resolution
   - Test circular dependencies

2. **Integration Tests:**
   - Test saving/loading complete models
   - Test saving/loading UI layouts
   - Test cross-object references

3. **Regression Tests:**
   - Test compatibility with existing code
   - Test performance with large models