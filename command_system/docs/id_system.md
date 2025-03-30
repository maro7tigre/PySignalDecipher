# Widget ID System Documentation

This document provides a concise overview of the ID system for tracking and referencing widgets, containers, observables, and observable properties in the PySignalDecipher application.

## Overview

The ID system creates and manages unique identifiers that encode type, hierarchy, and relationships between different components using string-based IDs.

## ID Formats

### Widget/Container Format
```
[type_code]:[unique_id]:[container_unique_id]:[location]
```

Examples:
- `le:1Z:0:0` - A line edit widget with no container
- `t:2J:0:1` - A tab container (in slot 1) with no parent
- `pb:3a:2J:2` - A push button widget in a container with unique_id 2J, at location 2

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

### Utility Functions

```python
from command_system.id_system.utils import (
    extract_type_code, extract_unique_id, 
    extract_container_unique_id, extract_location,
    extract_observable_unique_id, extract_property_name,
    extract_controller_unique_id, is_widget_id,
    is_observable_id, is_observable_property_id
)

# Extract parts from IDs
type_code = extract_type_code("pb:3a:2J:3")  # -> "pb"
unique_id = extract_unique_id("pb:3a:2J:3")  # -> "3a"
container_id = extract_container_unique_id("pb:3a:2J:3")  # -> "2J"
location = extract_location("pb:3a:2J:3")  # -> "3"
observable_id = extract_observable_unique_id("op:7F:4C:value:3a")  # -> "4C"
property_name = extract_property_name("op:7F:4C:value:3a")  # -> "value"
controller_id = extract_controller_unique_id("op:7F:4C:value:3a")  # -> "3a"

# Check ID types
is_widget = is_widget_id("pb:3a:2J:3")  # -> True
is_observable = is_observable_id("o:4C")  # -> True
is_property = is_observable_property_id("op:7F:4C:value:3a")  # -> True
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

The SimpleIDRegistry integrates with the main ID system's generator to produce consistent IDs in the format of `[type_code]:[unique_id]`, while providing a simple mapping between names and IDs. It is primarily used in the container system for widget type registration.

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