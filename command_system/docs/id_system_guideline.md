# ID System Implementation Guide

## Overview

This guide outlines the implementation plan for adding a memory-efficient ID system to the existing command system architecture. The goal is to enhance the system with unique identifiers for widgets and containers while maintaining current functionality.

## Implementation Approach

We'll implement the ID system in parallel with the existing direct reference system, allowing both to coexist:

1. **Dual reference approach**: Maintain direct object references for runtime operations while using IDs for serialization/deserialization
2. **Non-disruptive integration**: Add the ID system with minimal changes to existing code
3. **Progressive enhancement**: Start with core functionality and expand to more features

## File Structure

```
command_system/
├── id_system/
│   ├── __init__.py             # Public API exports
│   ├── generator.py            # IDGenerator for unique ID creation
│   ├── registry.py             # IDRegistry singleton
│   ├── utils.py                # Helper functions for ID manipulation
```

## Core Components

### 1. ID Generator (`generator.py`)

Responsible for creating unique, memory-efficient IDs following the pattern:
```
[type_code]:[unique_id]:[container_unique_id]:[location]
```

```python
class IDGenerator:
    def __init__(self):
        self._type_counters = {}  # Track counters for each type
    
    def generate_id(self, type_code, container_unique_id="0", location="0"):
        """Generate a unique ID with the specified parameters"""
        # Get or initialize counter for this type
        counter = self._type_counters.get(type_code, 0) + 1
        self._type_counters[type_code] = counter
        
        # Generate unique ID component using base62 encoding
        unique_id = self._encode_to_base62(counter)
        
        # Create full ID
        return f"{type_code}:{unique_id}:{container_unique_id}:{location}"
    
    def _encode_to_base62(self, number):
        """Convert integer to base62 for compact representation"""
        # Implementation of base62 encoding
        # ...
```

### 2. ID Registry (`registry.py`)

Central singleton for managing ID-to-widget mappings:

```python
class IDRegistry:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = IDRegistry()
        return cls._instance
    
    def __init__(self):
        if IDRegistry._instance is not None:
            raise RuntimeError("Use get_instance() to get the IDRegistry singleton")
            
        IDRegistry._instance = self
        self._widget_to_id_map = {}  # Widget -> ID
        self._id_to_widget_map = {}  # ID -> Widget
        self._id_generator = IDGenerator()
    
    def register(self, widget, type_code, container_unique_id="0", location="0"):
        """Register a widget with the ID system"""
        # Generate ID if not already registered
        if widget in self._widget_to_id_map:
            return self._widget_to_id_map[widget]
            
        # Create new ID
        widget_id = self._id_generator.generate_id(type_code, container_unique_id, location)
        
        # Store mappings
        self._widget_to_id_map[widget] = widget_id
        self._id_to_widget_map[widget_id] = widget
        
        return widget_id
    
    def unregister(self, widget_or_id):
        """Unregister a widget from the ID system"""
        # Implementation
        # ...
    
    def get_widget(self, widget_id):
        """Get widget by ID"""
        return self._id_to_widget_map.get(widget_id)
    
    def get_id(self, widget):
        """Get ID for a widget"""
        return self._widget_to_id_map.get(widget)
    
    def get_container_widgets(self, container_unique_id):
        """Get all widgets in a container"""
        # Implementation
        # ...
```

### 3. ID Utilities (`utils.py`)

Helper functions for working with IDs:

```python
def parse_id(id_string):
    """Parse an ID string into components"""
    parts = id_string.split(':')
    return {
        'type_code': parts[0],
        'unique_id': parts[1],
        'container_unique_id': parts[2],
        'location': parts[3]
    }

def extract_unique_id(id_string):
    """Extract just the unique_id portion from a full ID"""
    return id_string.split(':')[1]

def extract_container_unique_id(id_string):
    """Extract just the container_unique_id portion from a full ID"""
    return id_string.split(':')[2]
```

## Integration with Existing System

### 1. Update `CommandWidgetBase` in `widgets/base_widget.py`

Enhance the existing class to integrate with the ID system:

```python
# Add to imports
from ..id_system.registry import IDRegistry

class CommandWidgetBase(Generic[T]):
    # Existing code...
    
    def __init__(self):
        # Existing initialization...
        self.container = None
        self.container_info = None
        self._id = None  # Store ID
        
    def register_with_id_system(self, type_code, location="0"):
        """Register this widget with the ID system"""
        registry = IDRegistry.get_instance()
        
        # Get container unique ID if we have a container
        container_unique_id = "0"
        if self.container:
            container_id = registry.get_id(self.container)
            if container_id:
                container_unique_id = extract_unique_id(container_id)
        
        # Register with registry
        self._id = registry.register(self, type_code, container_unique_id, location)
        return self._id
    
    def unregister_from_id_system(self):
        """Unregister from the ID system"""
        if self._id:
            registry = IDRegistry.get_instance()
            registry.unregister(self)
            self._id = None
    
    def update_container_in_id_system(self):
        """Update container reference in ID system after container change"""
        if self._id:
            # Implementation
            # ...
```

### 2. Update `ContainerWidgetMixin` in `widgets/containers/base_container.py`

Enhance container mixin to handle widget registration:

```python
# Add to imports
from ...id_system.registry import IDRegistry
from ...id_system.utils import extract_unique_id

class ContainerWidgetMixin:
    # Existing code...
    
    def __init__(self, container_id=None):
        # Existing initialization...
        self._container_id = container_id or str(uuid.uuid4())
        self._id_registry = IDRegistry.get_instance()
        
    def register_with_id_system(self, type_code, location="0"):
        """Register this container with the ID system"""
        # Get container unique ID if we have a container
        container_unique_id = "0"
        if hasattr(self, "container") and self.container:
            container_id = self._id_registry.get_id(self.container)
            if container_id:
                container_unique_id = extract_unique_id(container_id)
        
        # Register with registry
        self._id = self._id_registry.register(self, type_code, container_unique_id, location)
        return self._id
        
    def _register_child_with_id_system(self, widget, type_code, location="0"):
        """Register a child widget with the ID system"""
        # Get our unique ID
        container_id = self._id_registry.get_id(self)
        if not container_id:
            # Register self first if needed
            container_id = self.register_with_id_system(self._get_container_type_code())
            
        container_unique_id = extract_unique_id(container_id)
        
        # Register child
        if hasattr(widget, "register_with_id_system"):
            widget.register_with_id_system(type_code, location)
        else:
            # Direct registration for non-command widgets
            self._id_registry.register(widget, type_code, container_unique_id, location)
    
    def register_contents(self, widget, container_info=None):
        """Update to register with ID system in addition to existing behavior"""
        # Existing code...
        
        # Additionally register with ID system
        self._register_child_with_id_system(
            widget, 
            self._get_widget_type_code(widget),
            self._get_widget_location(widget)
        )
        
    def _get_container_type_code(self):
        """Get type code for this container"""
        # Default implementation - can be overridden by subclasses
        if "TabWidget" in self.__class__.__name__:
            return "t"
        elif "DockWidget" in self.__class__.__name__:
            return "d"
        else:
            return "x"  # Custom container
            
    def _get_widget_type_code(self, widget):
        """Determine type code for a widget"""
        # Implementation based on widget type
        # ...
        
    def _get_widget_location(self, widget):
        """Get location identifier for a widget in this container"""
        # Default implementation - should be overridden by subclasses
        return "0"
```

### 3. Update `CommandTabWidget` in `widgets/containers/tab_widget.py`

Implement container-specific location handling:

```python
class CommandTabWidget(QTabWidget, ContainerWidgetMixin):
    # Existing code...
    
    def _get_widget_location(self, widget):
        """Get tab index as location"""
        for i in range(self.count()):
            if self.widget(i) == widget:
                return str(i)
        return "0"
        
    def _get_container_type_code(self):
        """Get type code for tab container"""
        return "t"
        
    def addTab(self, tab, label):
        """Update to register with ID system"""
        index = super().addTab(tab, label)
        self.register_contents(tab, {"tab_index": index})
        
        # Update location in ID system since we now know the index
        registry = IDRegistry.get_instance()
        tab_id = registry.get_id(tab)
        if tab_id:
            # Update location part of ID
            # Implementation...
            
        return index
```

### 4. Update `CommandDockWidget` in `widgets/containers/dock_widget.py`

Similar updates for dock widget:

```python
class CommandDockWidget(QDockWidget, ContainerWidgetMixin):
    # Existing code...
    
    def _get_widget_location(self, widget):
        """Get dock location code"""
        # For docks, location might be area code (0=center, 1=left, etc.)
        return "0"  # Default for primary content
        
    def _get_container_type_code(self):
        """Get type code for dock container"""
        return "d"
```

## Type Codes Reference

Define standard type codes for consistent usage:

| Widget Type | Code |
|-------------|------|
| **Containers** |  |
| Tab Container | t |
| Dock Container | d |
| Window Container | w |
| Custom Container | x |
| **Command Widgets** |  |
| Line Edit Widget | le |
| Check Box Widget | cb |
| Push Button | pb |
| Radio Button | rb |
| Combo Box | co |
| Slider | sl |
| Spin Box | sp |
| Text Edit | te |
| List Widget | lw |
| Tree Widget | tw |
| Table Widget | tb |
| Custom Widget | cw |

## Implementation Strategy

### Phase 1: Core ID System
1. Implement `IDGenerator` for creating unique IDs
2. Implement `IDRegistry` singleton for tracking widgets and IDs
3. Create utility functions for ID parsing and manipulation

### Phase 2: Container Integration
1. Update `ContainerWidgetMixin` to integrate with ID system
2. Implement container-specific type codes and location generation
3. Update container subclasses with type-specific implementations

### Phase 3: Widget Integration
1. Update `CommandWidgetBase` to register with ID system
2. Implement proper ID updates when widgets move between containers
3. Add automatic registration/unregistration in widget lifecycle

### Phase 4: Serialization Support
1. Add methods to serialize/deserialize widgets using their IDs
2. Integrate with existing Observable serialization system
3. Implement container hierarchy serialization

## Testing Strategy

1. **Unit Tests**:
   - Test ID generation for uniqueness and format correctness
   - Test registry operations (register, unregister, lookups)
   - Test ID parsing and manipulation utilities

2. **Integration Tests**:
   - Test widget registration/unregistration with containers
   - Test container hierarchy navigation using IDs
   - Test ID updates when widgets move between containers

3. **Serialization Tests**:
   - Test serialization/deserialization of widget hierarchies
   - Test container reconstruction from serialized IDs
   - Test reference resolution during deserialization

## Considerations and Edge Cases

1. **Dynamic Containers**: Ensure IDs are updated properly when containers are created/destroyed dynamically
2. **Widget Movement**: Handle ID updates when widgets move between containers
3. **Bulk Operations**: Optimize performance for bulk registration/unregistration
4. **Nested Containers**: Ensure proper handling of container hierarchies
5. **Weak References**: Consider using weak references to avoid memory leaks

## Usage Examples

### Basic Widget Registration

```python
# In CommandLineEdit constructor
def __init__(self, parent=None):
    QLineEdit.__init__(self, parent)
    CommandWidgetBase.__init__(self)
    # Other initialization...
    
    # Register with ID system
    self.register_with_id_system("le")
```

### Container Navigation by ID

```python
def navigate_to_widget_by_id(widget_id):
    registry = IDRegistry.get_instance()
    widget = registry.get_widget(widget_id)
    
    if widget:
        # Get container from widget
        container = widget.container
        if container:
            container.navigate_to_container(widget, widget.container_info)
            return True
    return False
```

### Getting All Widgets in a Container

```python
def get_all_widgets_in_container(container):
    registry = IDRegistry.get_instance()
    container_id = registry.get_id(container)
    
    if container_id:
        container_unique_id = extract_unique_id(container_id)
        return registry.get_container_widgets(container_unique_id)
    return []
```

This implementation plan provides a roadmap for integrating the ID system into your existing command system with minimal disruption while adding powerful new capabilities for serialization and reference management.