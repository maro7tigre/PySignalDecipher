# Widget ID System Documentation

This document provides a concise overview of the ID system for tracking and referencing widgets, containers, observables, and observable properties in the PySignalDecipher application.

## Overview

The ID system creates and manages unique identifiers that encode type, hierarchy, and relationships between different components using string-based IDs. It supports both static and dynamic components through a hierarchical design.

## ID Formats

### Widget/Container Format
```
[type_code]:[unique_id]:[container_unique_id]:[location_path]
```

Where `location_path` uses a hierarchical format with forward slashes: `segment1/segment2/.../segmentN`

Examples:
- `le:1Z:0:0` - A line edit widget with no container
- `t:2J:0:1` - A tab container (in slot 1) with no parent
- `pb:3a:2J:2/4b` - A push button widget in a subcontainer at location 2, with widget location ID 4b
- `cb:5c:3a:2/4b/7d` - A checkbox in a deeply nested container at path 2/4b with widget location ID 7d

### Observable Format
```
[type_code]:[unique_id]
```

Example:
- `o:4C` - An observable with unique ID "4C"

### Observable Property Format
```
[type_code]:[unique_id]:[observable_unique_id]:[property_name]:[controller_id]
```

Examples:
- `op:5D:0:name:0` - A standalone property with name "name"
- `op:6E:4C:count:0` - A property "count" belonging to observable with unique_id "4C"
- `op:7F:4C:value:3a` - A property "value" belonging to observable with unique_id "4C", controlled by widget with unique_id "3a"

## Container Hierarchy

Each container can have subcontainers (tabs, docks, etc.) which have their own locations within the parent container. 
Each subcontainer has its own ID generator for creating stable widget location IDs.

```
Container (t:1A:0:0)
  ├── Subcontainer 1 (t:2B:1A:0)
  │     ├── Widget 1-1 (pb:3C:2B:0/1)
  │     ├── Widget 1-2 (le:4D:2B:0/2)
  │     └── Nested Container (d:8H:2B:0/3)
  │           ├── Nested Widget 1 (pb:9I:8H:0/3/1)
  │           └── Nested Widget 2 (le:10J:8H:0/3/2)
  │
  └── Subcontainer 2 (t:5E:1A:1)
        ├── Widget 2-1 (pb:6F:5E:1/1)
        └── Widget 2-2 (le:7G:5E:1/2)
```

This hierarchical approach supports arbitrarily deep nesting of containers, with each level maintaining its own location context.

## Registry Methods

### Registration Methods
- `register(widget, type_code, widget_id, container_id, location)`
- `register_observable(observable, type_code, observable_id)`
- `register_observable_property(property, type_code, property_id, property_name, observable_id, controller_id)`

### ID Retrieval
- `get_widget(widget_id)`
- `get_observable(observable_id)`
- `get_observable_property(property_id)`
- `get_id(component)`
- `get_unique_id_from_id(id_string)`
- `get_full_id_from_unique_id(unique_id)`

### Container and Location Management
- `get_locations_map(container_id)` - Get mapping of subcontainer IDs to locations
- `set_locations_map(container_id, locations_map)` - Set locations map for a container
- `get_widgets_at_subcontainer_location(container_id, subcontainer_location)` - Get widgets at a specific location
- `get_subcontainer_id_at_location(container_id, location)` - Get subcontainer at a specific location

### ID-Based Relationship Queries
- `get_container_id_from_widget_id(widget_id)`
- `get_widget_ids_by_container_id(container_unique_id)`
- `get_widget_ids_by_container_id_and_location(container_unique_id, location)`
- `get_observable_id_from_property_id(property_id)`
- `get_property_ids_by_observable_id(observable_unique_id)`
- `get_property_ids_by_observable_id_and_property_name(observable_unique_id, property_name)`
- `get_controller_id_from_property_id(property_id)`
- `get_property_ids_by_controller_id(controller_unique_id)`

### ID Updates
- `update_container_id(widget_id, new_container_id)`
- `update_location(widget_id, new_location)`
- `update_observable_id(property_id, new_observable_id)`
- `update_property_name(property_id, new_property_name)`
- `update_controller_id(property_id, new_controller_id)`
- `remove_container_reference(widget_id)`
- `remove_observable_reference(property_id)`
- `remove_controller_reference(property_id)`

### Unregistration
- `unregister(component_id, replacement_id=None)`
- `set_on_widget_unregister(callback)`
- `set_on_observable_unregister(callback)`
- `set_on_property_unregister(callback)`
- `set_on_id_changed(callback)` - Set callback for ID changes

### Utility Functions

```python
from command_system.id_system.utils import (
    extract_type_code, extract_unique_id, 
    extract_container_unique_id, extract_location,
    extract_location_parts, extract_subcontainer_location,
    extract_widget_location_id, extract_observable_unique_id, 
    extract_property_name, extract_controller_unique_id,
    create_composite_location, is_widget_id,
    is_observable_id, is_observable_property_id,
    is_subcontainer_id
)

# Extract parts from IDs
type_code = extract_type_code("pb:3a:2J:2-4b")  # -> "pb"
unique_id = extract_unique_id("pb:3a:2J:2-4b")  # -> "3a"
container_id = extract_container_unique_id("pb:3a:2J:2-4b")  # -> "2J"
location = extract_location("pb:3a:2J:2-4b")  # -> "2-4b"

# Extract location parts
subcontainer_loc, widget_loc_id = extract_location_parts("pb:3a:2J:2-4b")  # -> ("2", "4b")
subcontainer_loc = extract_subcontainer_location("pb:3a:2J:2-4b")  # -> "2"
widget_loc_id = extract_widget_location_id("pb:3a:2J:2-4b")  # -> "4b"

# Create composite location
location = create_composite_location("2", "4b")  # -> "2-4b"

# Extract observable-related parts
observable_id = extract_observable_unique_id("op:7F:4C:value:3a")  # -> "4C"
property_name = extract_property_name("op:7F:4C:value:3a")  # -> "value"
controller_id = extract_controller_unique_id("op:7F:4C:value:3a")  # -> "3a"

# Check ID types
is_widget = is_widget_id("pb:3a:2J:2-4b")  # -> True
is_observable = is_observable_id("o:4C")  # -> True
is_property = is_observable_property_id("op:7F:4C:value:3a")  # -> True
is_subcontainer = is_subcontainer_id("t:2J:0:1")  # -> True
```

## Simple ID Registry

The SimpleIDRegistry provides a way to create and track consistent IDs for widget types and other components.

```python
from command_system.id_system import get_simple_id_registry

# Get the registry
registry = get_simple_id_registry()

# Register a name with a type code
widget_id = registry.register("welcome_tab", "wt")   # "wt:1"
form_id = registry.register("main_form", "fm")       # "fm:1"

# Register with a custom ID
custom_id = registry.register("custom_widget", "wt", "wt:custom")

# Look up IDs and names
id_str = registry.get_id("welcome_tab")      # "wt:1"
name = registry.get_name("wt:1")             # "welcome_tab"

# Check registration and unregister
is_reg = registry.is_registered("welcome_tab")   # True
registry.unregister("welcome_tab")               # True
```

## Using with Containers

### Setting Up a Container

```python
# Create a main container
container = CommandTabWidget()
container_id = get_id_registry().register(container, TypeCodes.TAB_CONTAINER)

# Create a subcontainer (tab)
tab = QWidget()
tab_id = get_id_registry().register(tab, TypeCodes.CUSTOM_CONTAINER, 
                                  None, container_id, "0")
                                  
# Create a widget in the subcontainer
button = QPushButton("Click Me")
button_id = get_id_registry().register(button, TypeCodes.PUSH_BUTTON,
                                     None, tab_id, "0")  # Location will be composite
```

### Serializing a Container

```python
def serialize_container(container):
    container_id = get_id_registry().get_id(container)
    if not container_id:
        return None
        
    # Get container properties
    result = {
        "id": container_id,
        "type_code": extract_type_code(container_id),
        "locations_map": get_id_registry().get_locations_map(container_id)
    }
    
    # Get all subcontainers
    subcontainers = []
    for subcontainer_id, location in result["locations_map"].items():
        subcontainer = get_id_registry().get_widget(subcontainer_id)
        if subcontainer and hasattr(subcontainer, "get_serialization"):
            subcontainer_data = subcontainer.get_serialization()
            subcontainers.append(subcontainer_data)
    
    result["subcontainers"] = subcontainers
    return result
```

### Deserializing a Container

```python
def deserialize_container(data, parent=None):
    # Create container
    container = CommandTabWidget(parent)
    container_id = get_id_registry().register(container, data["type_code"], data["id"])
    
    # Restore locations map
    get_id_registry().set_locations_map(container_id, data["locations_map"])
    
    # Track ID mappings for reference updates
    id_map = {data["id"]: container_id}
    
    # Recreate subcontainers
    for subcontainer_data in data["subcontainers"]:
        # Create subcontainer
        subcontainer = deserialize_component(subcontainer_data, container)
        if subcontainer:
            # Map old ID to new ID
            id_map[subcontainer_data["id"]] = get_id_registry().get_id(subcontainer)
    
    # Update references using ID map
    update_component_references(container, id_map)
    
    return container
```

## Type Codes Reference

| Component Type | Code |
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
| **Observables** |  |
| Observable | o |
| Observable Property | op |