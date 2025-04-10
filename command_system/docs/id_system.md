# PySignalDecipher ID System Documentation

## Overview

The ID system creates and manages unique identifiers for tracking components without maintaining direct references. This enables advanced serialization, navigation, and reference management across the application.

The system uses string-based IDs that encode type, hierarchy, and relationships between different components using a consistent format. It supports both static and dynamic components through a hierarchical design.

## Registry Methods Reference

### Core Registration Methods
| Method | Description |
|--------|-------------|
| `register(widget, type_code, widget_id=None, container_id=None, location=None)` | Register a widget or container |
| `register_observable(observable, type_code, observable_id=None)` | Register an observable |
| `register_observable_property(property_obj, type_code, property_id=None, property_name="0", observable_id="0", controller_id=None)` | Register a property with relationships |
| `unregister(component_id)` | Unregister any component |

### Component Retrieval Methods
| Method | Description |
|--------|-------------|
| `get_widget(widget_id)` | Get a widget by ID |
| `get_observable(observable_id)` | Get an observable by ID |
| `get_observable_property(property_id)` | Get a property by ID |
| `get_id(component)` | Get the ID for a component |
| `get_unique_id_from_id(id_string)` | Extract unique ID from any ID string |
| `get_full_id_from_unique_id(unique_id, type_code=None)` | Get full ID from a unique ID |

### Container Relationship Methods
| Method | Description |
|--------|-------------|
| `get_container_widgets(container_id)` | Get widgets in a container by location |
| `get_widgets_by_container_id(container_id)` | Get all widgets in a container |
| `get_container_id_from_widget_id(widget_id)` | Get a widget's container |
| `get_locations_map(container_id)` | Get container's locations map |
| `set_locations_map(container_id, locations_map)` | Set container's locations map |
| `get_container_widgets_at_location(container_id, location)` | Get widgets at a specific location |

### Observable Relationship Methods
| Method | Description |
|--------|-------------|
| `get_observable_properties(observable_id)` | Get all properties for an observable |
| `get_observable_id_from_property_id(property_id)` | Get a property's observable |
| `get_controller_properties(controller_id)` | Get properties controlled by a widget |
| `get_controller_id_from_property_id(property_id)` | Get a property's controller |
| `get_property_ids_by_observable_id_and_property_name(observable_id, property_name)` | Get properties by name |

### ID Update Methods
| Method | Description |
|--------|-------------|
| `update_id(old_id, new_id)` | Update any component's ID directly |
| `update_container(widget_id, new_container_id)` | Move a widget to a different container |
| `update_location(widget_id, new_location)` | Change a widget's location within its container |
| `update_observable_reference(property_id, new_observable_id)` | Change a property's observable |
| `update_property_name(property_id, new_property_name)` | Change a property's name |
| `update_controller_reference(property_id, new_controller_id)` | Change a property's controller |

### Reference Removal Methods
| Method | Description |
|--------|-------------|
| `remove_container_reference(widget_id)` | Remove a widget's container reference |
| `remove_observable_reference(property_id)` | Remove a property's observable reference |
| `remove_controller_reference(property_id)` | Remove a property's controller reference |

### Subscription Methods
| Method | Description |
|--------|-------------|
| `subscribe_to_id(component_id, callback)` | Subscribe to ID changes |
| `unsubscribe_from_id(component_id, callback=None)` | Unsubscribe from ID changes |
| `clear_subscriptions()` | Clear all subscriptions |

### Callback Registration Methods
| Method | Description |
|--------|-------------|
| `add_widget_unregister_callback(callback)` | Add widget unregister callback |
| `remove_widget_unregister_callback(callback)` | Remove widget unregister callback |
| `add_observable_unregister_callback(callback)` | Add observable unregister callback |
| `remove_observable_unregister_callback(callback)` | Remove observable unregister callback |
| `add_property_unregister_callback(callback)` | Add property unregister callback |
| `remove_property_unregister_callback(callback)` | Remove property unregister callback |
| `add_id_changed_callback(callback)` | Add ID changed callback |
| `remove_id_changed_callback(callback)` | Remove ID changed callback |
| `clear_widget_unregister_callbacks()` | Clear widget unregister callbacks |
| `clear_observable_unregister_callbacks()` | Clear observable unregister callbacks |
| `clear_property_unregister_callbacks()` | Clear property unregister callbacks |
| `clear_id_changed_callbacks()` | Clear ID changed callbacks |
| `clear_all_callbacks()` | Clear all callbacks |

## Utility Functions

### ID Subscription Utilities
| Function | Description |
|----------|-------------|
| `subscribe_to_id(component_id, callback)` | Global function to subscribe to ID changes |
| `unsubscribe_from_id(component_id, callback=None)` | Global function to unsubscribe from ID changes |
| `clear_subscriptions()` | Global function to clear all subscriptions |

### Simple ID Registry
| Method | Description |
|--------|-------------|
| `get_simple_id_registry()` | Get the global SimpleIDRegistry instance |
| `SimpleIDRegistry.register(type_code, custom_id=None)` | Register and generate a unique ID |
| `SimpleIDRegistry.unregister(id_str)` | Unregister an ID |
| `SimpleIDRegistry.is_registered(id_str)` | Check if an ID is registered |
| `SimpleIDRegistry.get_all_ids()` | Get all registered IDs |
| `SimpleIDRegistry.clear()` | Clear all registrations |

### Type Code Constants
| Class | Description |
|-------|-------------|
| `ContainerTypeCodes` | Container type codes (TAB, DOCK, WINDOW, CUSTOM) |
| `WidgetTypeCodes` | Widget type codes (LINE_EDIT, CHECK_BOX, PUSH_BUTTON, etc.) |
| `ObservableTypeCodes` | Observable type codes (OBSERVABLE) |
| `PropertyTypeCodes` | Property type codes (OBSERVABLE_PROPERTY) |
| `TypeCodes` | Combined utility methods for working with all type codes |

## Getting Started

### Basic Setup

To use the ID system, import it and get a reference to the registry:

```python
from command_system.id_system import get_id_registry

# Get the global ID registry
registry = get_id_registry()
```

### Registering Components

The registry provides methods to register different types of components:

#### Widgets

```python
# Register a widget (returns the full widget ID)
widget_id = registry.register(
    widget_object,      # The widget object to register
    "pb",               # Type code (e.g., "pb" for push button)
    unique_id=None,     # Optional unique ID (default: auto-generated)
    container_id=None,  # Container widget ID (default: root container)
    location=None       # Location ID within container (default: auto-generated)
)
```

#### Containers

Containers are registered just like widgets, but with container type codes:

```python
# Register a tab container
container_id = registry.register(
    container_object,   # The container object
    "t",                # Type code ("t" for tab container)
    unique_id=None,     # Optional unique ID
    container_id=None,  # Parent container (default: root)
    location=None       # Location ID (default: auto-generated)
)
```

#### Observables

```python
# Register an observable
observable_id = registry.register_observable(
    observable_object,  # The observable object
    "ob",               # Type code ("ob" for observable)
    observable_id=None  # Optional unique ID (default: auto-generated)
)
```

#### Observable Properties

```python
# Register a property with relationships
property_id = registry.register_observable_property(
    property_object,    # The property object
    "op",               # Type code ("op" for observable property)
    property_id=None,   # Optional unique ID (default: auto-generated)
    property_name="0",  # Property name (default: "0")
    observable_id="0",  # Observable ID (default: none)
    controller_id="0"   # Controller widget ID (default: none)
)
```

### Retrieving Components

You can retrieve components by their IDs:

```python
# Get a widget by its ID
widget = registry.get_widget(widget_id)

# Get an observable by its ID
observable = registry.get_observable(observable_id)

# Get a property by its ID
property_obj = registry.get_observable_property(property_id)

# Get the ID for any registered component
component_id = registry.get_id(component_object)
```

### Unregistering Components

```python
# Unregister any type of component
success = registry.unregister(component_id)
```

## ID Formats

The ID system uses structured string formats to encode component information:

### Widget/Container Format
```
[type_code]:[unique_id]:[container_unique_id]:[location]
```

Where `location` uses a composite format: `[container_location]-[widget_location_id]`

For example:
- `pb:3a:0:0-1` - A push button with no container, at root location with widget ID "1"
- `t:2J:0:0-0` - A tab container at the root level
- `pb:3a:2J:0/1-4b` - A push button in container "2J", at path "0/1" with widget location ID "4b"

### Observable Format
```
[type_code]:[unique_id]
```

Example:
- `ob:4C` - An observable with unique ID "4C"

### Observable Property Format
```
[type_code]:[unique_id]:[observable_unique_id]:[property_name]:[controller_id]
```

Examples:
- `op:5D:0:name:0` - A standalone property with name "name"
- `op:6E:4C:count:0` - A property "count" belonging to observable "4C"
- `op:7F:4C:value:3a` - A property "value" belonging to observable "4C", controlled by widget "3a"

## Working with Containers

### Container Hierarchy

The ID system tracks container hierarchies automatically. When you register a widget inside a container, its ID encodes the full path:

```python
# Create a nested container structure
main_container_id = registry.register(main_container, "w")  # Window container
tab_container_id = registry.register(tab_container, "t", None, main_container_id)
button_id = registry.register(button, "pb", None, tab_container_id)
```

### Getting Container Contents

```python
# Get all widgets in a container (flat list)
widgets = registry.get_widgets_by_container_id(container_id)

# Get the container's widget structure (organized by location)
locations_map = registry.get_locations_map(container_id)

# Get widgets at a specific location in a container
widgets_at_location = registry.get_container_widgets_at_location(container_id, location)

# Get a widget's container
container_id = registry.get_container_id_from_widget_id(widget_id)
```

## Working with Observables and Properties

### Getting Observable Properties

```python
# Get all properties for an observable
properties = registry.get_observable_properties(observable_id)

# Get properties by name
properties = registry.get_property_ids_by_observable_id_and_property_name(
    observable_id, property_name
)

# Get the observable for a property
observable_id = registry.get_observable_id_from_property_id(property_id)
```

### Working with Controllers

```python
# Get all properties controlled by a widget
properties = registry.get_controller_properties(controller_id)

# Get a property's controller
controller_id = registry.get_controller_id_from_property_id(property_id)
```

## Updating Components

### Container and Location Updates

```python
# Move a widget to a different container
updated_id = registry.update_container(widget_id, new_container_id)

# Change a widget's location within its container
updated_id = registry.update_location(widget_id, new_location)
```

### Observable and Property Updates

```python
# Change a property's observable reference
updated_id = registry.update_observable_reference(property_id, new_observable_id)

# Change a property's name
updated_id = registry.update_property_name(property_id, new_property_name)

# Change a property's controller
updated_id = registry.update_controller_reference(property_id, new_controller_id)
```

### Direct ID Updates

For advanced cases, you can update component IDs directly:

```python
success, updated_id, error = registry.update_id(old_id, new_id)
```

### Removing References

```python
# Remove a widget's container (set to root)
updated_id = registry.remove_container_reference(widget_id)

# Remove a property's observable reference
updated_id = registry.remove_observable_reference(property_id)

# Remove a property's controller reference
updated_id = registry.remove_controller_reference(property_id)
```

## Subscribing to ID Changes

The ID system provides a subscription system to monitor ID changes:

```python
from command_system.id_system import subscribe_to_id, unsubscribe_from_id

# Subscribe to ID changes
def on_id_changed(old_id, new_id):
    print(f"ID changed: {old_id} -> {new_id}")

subscribe_to_id(component_id, on_id_changed)

# Unsubscribe from ID changes
unsubscribe_from_id(component_id, on_id_changed)

# Clear all subscriptions
clear_subscriptions()
```

## Simple ID Registry

For basic ID management without the full hierarchy:

```python
from command_system.id_system import get_simple_id_registry

# Get the simple registry
simple_registry = get_simple_id_registry()

# Register a name with a type code
widget_id = simple_registry.register("t")   # "t:1"
form_id = simple_registry.register("fm")    # "fm:1"

# Register with a custom ID
custom_id = simple_registry.register("t", "t:custom")

# Look up IDs
all_ids = simple_registry.get_all_ids()

# Check registration and unregister
is_reg = simple_registry.is_registered("t:1")
simple_registry.unregister("t:1")
```

## Type Codes Reference

The ID system uses distinct type codes for different component types:

### Container Type Codes
```python
from command_system.id_system import ContainerTypeCodes

ContainerTypeCodes.TAB       # 't' - Tab Container
ContainerTypeCodes.DOCK      # 'd' - Dock Container
ContainerTypeCodes.WINDOW    # 'w' - Window Container
ContainerTypeCodes.CUSTOM    # 'x' - Custom Container
```

### Widget Type Codes
```python
from command_system.id_system import WidgetTypeCodes

WidgetTypeCodes.LINE_EDIT     # 'le' - Line Edit Widget
WidgetTypeCodes.CHECK_BOX     # 'cb' - Check Box Widget
WidgetTypeCodes.PUSH_BUTTON   # 'pb' - Push Button
WidgetTypeCodes.RADIO_BUTTON  # 'rb' - Radio Button
WidgetTypeCodes.COMBO_BOX     # 'co' - Combo Box
WidgetTypeCodes.SLIDER        # 'sl' - Slider
WidgetTypeCodes.SPIN_BOX      # 'sp' - Spin Box
WidgetTypeCodes.TEXT_EDIT     # 'te' - Text Edit
WidgetTypeCodes.LIST_WIDGET   # 'lw' - List Widget
WidgetTypeCodes.TREE_WIDGET   # 'tw' - Tree Widget
WidgetTypeCodes.TABLE_WIDGET  # 'tb' - Table Widget
WidgetTypeCodes.CUSTOM_WIDGET # 'cw' - Custom Widget
```

### Observable and Property Type Codes
```python
from command_system.id_system import ObservableTypeCodes, PropertyTypeCodes

ObservableTypeCodes.OBSERVABLE           # 'ob' - Observable
PropertyTypeCodes.OBSERVABLE_PROPERTY    # 'op' - Observable Property
```

## Common Patterns and Best Practices

### Container Management

When working with containers, it's important to understand the location hierarchy:

1. The root container has ID "0" at location "0"
2. Each container has its own location context
3. Widget IDs encode their full path in the container hierarchy

### Observable-Property Relationships

Properties can have three different relationship states:
1. Standalone properties (no observable or controller)
2. Observable-bound properties (linked to an observable)
3. Controller-bound properties (linked to a widget that controls the property)

### ID Subscription

The subscription system is useful for:
1. UI synchronization when IDs change
2. Maintaining external references to components
3. Implementing undo/redo systems

Always remember to unsubscribe when you no longer need notifications to prevent memory leaks.

### Serialization and Restoration

The ID system supports serialization patterns:
1. Serialize component IDs instead of the components themselves
2. When deserializing, recreate components with the same IDs
3. Use update methods to handle changes in the serialized structure

## Error Handling

The ID system provides informative errors for common issues:

```python
from command_system.id_system import IDRegistrationError

try:
    # Attempt to register with a location ID that's already in use
    widget_id = registry.register(widget, "pb", None, container_id, "used_location")
except IDRegistrationError as e:
    print(f"Registration error: {e}")
```

When using `update_id()`, check the success flag and error message:

```python
success, updated_id, error = registry.update_id(old_id, new_id)
if not success:
    print(f"Update failed: {error}")
```