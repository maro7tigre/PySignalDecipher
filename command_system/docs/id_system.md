# Widget ID System Documentation

This document provides a concise overview of the ID system for tracking and referencing widgets, containers, observables, and observable properties in the PySignalDecipher application.

## Overview

The ID system creates and manages unique identifiers that encode type, hierarchy, and relationships between different components using string-based IDs. It supports both static and dynamic components through a hierarchical design.

## ID Formats

### Widget/Container Format
```
[type_code]:[unique_id]:[container_unique_id]:[location]
```

Where `location` uses a composite format: `[subcontainer_path]-[widget_location_id]`

Examples:
- `le:1Z:0:0-2A` - A line edit widget with no container (at root location 0 with widget ID 2A)
- `t:2J:0:1-3B` - A tab container (in slot 1 with widget ID 3B) with no parent
- `pb:3a:2J:2-4b` - A push button widget in a subcontainer at location 2, with widget location ID 4b
- `cb:5c:3a:2/1-7d` - A checkbox in a deeply nested container at path 2/1 with widget location ID 7d

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
Container (t:1A:0:0-5X)
  ├── Subcontainer 1 (t:2B:1A:0-1Y)
  │     ├── Widget 1-1 (pb:3C:2B:0-1Z)
  │     ├── Widget 1-2 (le:4D:2B:0-2A)
  │     └── Nested Container (d:8H:2B:0/1-3B)
  │           ├── Nested Widget 1 (pb:9I:8H:0/1-1C)
  │           └── Nested Widget 2 (le:10J:8H:0/1-2D)
  │
  └── Subcontainer 2 (t:5E:1A:1-1E)
        ├── Widget 2-1 (pb:6F:5E:1-1F)
        └── Widget 2-2 (le:7G:5E:1-2G)
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
- `update_location_from_container(widget_id, container_id, preserve_widget_location_id)` - Update a widget's location based on its container

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
    extract_location_parts, extract_subcontainer_path,
    extract_widget_location_id, extract_observable_unique_id, 
    extract_property_name, extract_controller_unique_id,
    create_location_path, append_to_location_path,
    is_widget_id, is_observable_id, is_observable_property_id,
    is_subcontainer_id
)

# Extract parts from IDs
type_code = extract_type_code("pb:3a:2J:2-4b")  # -> "pb"
unique_id = extract_unique_id("pb:3a:2J:2-4b")  # -> "3a"
container_id = extract_container_unique_id("pb:3a:2J:2-4b")  # -> "2J"
location = extract_location("pb:3a:2J:2-4b")  # -> "2-4b"

# Extract location parts
location_parts = extract_location_parts("pb:3a:2J:2/1-4b")  # -> ["2", "1", "4b"]
subcontainer_path = extract_subcontainer_path("pb:3a:2J:2/1-4b")  # -> "2/1"
widget_loc_id = extract_widget_location_id("pb:3a:2J:2-4b")  # -> "4b"

# Create composite location
location = create_location_path("2", "1")  # -> "2/1"
full_location = append_to_location_path("2/1", "4b")  # -> "2/1/4b"

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
registry.unregister_by_name("welcome_tab")       # True
registry.unregister_by_id("wt:1")                # True
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
                                     None, tab_id, "0")  # Location will be composite with ID
```

### Working with Location IDs

```python
# Get a subcontainer generator for custom location IDs
sub_generator = registry._get_subcontainer_generator(container_id)

# Generate a unique widget location ID
widget_location_id = sub_generator.generate_location_id()

# Create a location with this ID
location = f"0-{widget_location_id}"

# Create a widget with this location
button_id = registry.register(button, TypeCodes.PUSH_BUTTON, None, container_id, location)

# Update a widget's location
registry.update_location(button_id, "1")  # Will generate a new location like "1-<ID>"

# Update location based on container
registry.update_location_from_container(button_id, container_id)
```

### Hierarchical Locations

Locations use a composite format:
- For subcontainers: `subcontainer_location` (e.g., "0", "1", "2/1")
- For widgets: `subcontainer_location-widget_location_id` (e.g., "0-1", "2/1-3a")

When registering:
- If you provide a full location with widget_id part, it will be used as is
- If you provide only a subcontainer path, a widget_id will be generated using the subcontainer's generator
- If no location is provided, the system will generate a default location with the subcontainer's generator

When updating a widget's container:
- The system will automatically update the location to match the new container's hierarchy
- You can preserve the original widget location ID part if needed

### Container Navigation

```python
# Find widgets at a specific location
widgets = registry.get_widgets_at_subcontainer_location(container_id, "1")

# Get the subcontainer at a specific location
subcontainer_id = registry.get_subcontainer_id_at_location(container_id, "2")

# Navigate to a widget in a container
container_widget.navigate_to_widget(widget_id)
```

### ID Updates

```python
from command_system.id_system import get_id_registry

# Get the registry
registry = get_id_registry()

# Update a component's ID
old_id = "pb:3a:2J:2-4b"
new_id = "pb:7c:2J:3-5d"
result_id = registry.update_id(old_id, new_id)

# This will automatically update:
# - Container references in child widgets
# - Location maps for containers
# - Observable references in properties
# - Controller references in properties
```

The `update_id` method provides a way to update a component's ID while maintaining all the relationships that reference it. This is particularly useful for complex operations like moving components between containers, merging containers, or implementing custom serialization/deserialization logic.

Unlike the more specialized update methods like `update_container_id` or `update_observable_id`, this method handles all types of IDs and updates all relevant relationships automatically. The method returns the new ID if successful or `None` if the update fails.

When updating an ID:
- The component type must remain the same (type code is preserved)
- All child widgets' container references are updated
- All location maps are updated
- All property bindings are maintained
- The ID registry's change callback is triggered

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