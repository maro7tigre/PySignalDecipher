# PySignalDecipher ID System Documentation

## Overview

The ID system creates and manages unique identifiers for tracking components without maintaining direct references. This enables advanced serialization, navigation, and reference management across the application.

The system uses string-based IDs that encode type, hierarchy, and relationships between different components using a consistent format. It supports both static and dynamic components through a hierarchical design.

## ID Formats

### 1. Widget/Container Format
```
[type_code]:[unique_id]:[container_unique_id]:[location]
```

Where `location` uses a composite format: `[container_location]-[widget_location_id]`

- `type_code`: Indicates the component type (e.g., "pb" for push button, "t" for tab container)
- `unique_id`: Globally unique identifier generated using base62 encoding
- `container_unique_id`: Unique ID of the parent container (or "0" if none)
- `location`: Composite value with two parts:
  - `container_location`: Full path within the container hierarchy (e.g., "0", "0/1", "0/1/2")
  - `widget_location_id`: Unique identifier within that specific container location

Examples:
- `pb:3a:0:0-1` - A push button with no container, at root location with widget ID "1"
- `t:2J:0:0-0` - A tab container at the root level (project itself)
- `pb:3a:2J:0/1-4b` - A push button in container "2J", at path "0/1" with widget location ID "4b"
- `cb:5c:3a:0/2/1-7d` - A checkbox in container "3a", at nested path "0/2/1" with widget location ID "7d"

### 2. Observable Format
```
[type_code]:[unique_id]
```

Example:
- `ob:4C` - An observable with unique ID "4C"

### 3. Observable Property Format
```
[type_code]:[unique_id]:[observable_unique_id]:[property_name]:[controller_id]
```

Examples:
- `op:5D:0:name:0` - A standalone property with name "name" (no observable or controller)
- `op:6E:4C:count:0` - A property "count" belonging to observable with unique_id "4C"
- `op:7F:4C:value:3a` - A property "value" belonging to observable with unique_id "4C", controlled by widget with unique_id "3a"

## ID Generation

### UniqueID Generator

- A single global instance generates all unique IDs across the application
- Uses incremental counter with base62 encoding for compact representation
- Tracks used IDs to prevent collisions

### Subcontainer Location Generators

- Each container location has its own ID generator for widget location IDs
- When a widget is registered at a specific location, that location's generator creates the widget_location_id
- Ensures stable and predictable IDs within each container location

## Container Hierarchy

Projects start with container ID "0" at location "0".

Each container can have subcontainers (tabs, docks, windows, etc.) with their own locations:

```
Project Container (0 at location 0)
  ├── Container 1 (t:1A:0:0-1)
  │     ├── Widget 1-1 (pb:3C:1A:0/1-1)
  │     ├── Widget 1-2 (le:4D:1A:0/1-2)
  │     └── Nested Container (d:8H:1A:0/1-3)
  │           ├── Nested Widget 1 (pb:9I:8H:0/1/3-1)
  │           └── Nested Widget 2 (le:10J:8H:0/1/3-2)
  │
  └── Container 2 (t:2B:0:0-2)
        ├── Widget 2-1 (pb:6F:2B:0/2-1)
        └── Widget 2-2 (le:7G:2B:0/2-2)
```

This hierarchical approach supports arbitrarily deep nesting of containers, with each level maintaining its own location context.

## Location System

The location is a composite identifier with two parts:
1. `container_location`: Full path in the container hierarchy (e.g., "0", "0/1", "0/1/3")
2. `widget_location_id`: Unique ID within that specific container location

Important behaviors:
- The project itself is container "0" at location "0"
- Each container location has its own ID generator
- Widget location IDs remain stable when moving within the same container location
- When a widget changes container, an attempt is made to keep its widget_location_id, generating a new one only if there's a collision
- The container location in a widget's location string reflects the full hierarchical path of its container

## Registration and Updates

### Widget Registration

When registering a widget:
1. If no container is specified, the widget is registered at the root container ("0") with location "0"
2. If a container is specified but no location, a widget_location_id is generated for that container's location
3. If a container and location are specified, the location is treated as the widget_location_id and the system checks if it's available in that container
4. If the widget_location_id is already in use, a new one is automatically generated

### ID Updates

When updating a widget's container:
1. The container_unique_id in the widget's ID is updated
2. The container_location is updated to reflect the new container's full path
3. The widget_location_id remains the same unless there's a collision
4. If there's a collision, a new widget_location_id is generated
5. The widget is unregistered from the old container's location generator
6. The widget is registered with the new container's location generator

When updating a widget's location:
1. Only the widget_location_id part changes
2. The specified widget_location_id is checked for availability
3. If the widget_location_id already exists, an error is raised
4. The widget is unregistered from the old location and registered at the new location

## ID Registry Methods

The registry provides methods for managing components and their relationships:

### Registration Methods
- `register(widget, type_code, widget_id=None, container_id=None, location=None)`
- `register_observable(observable, type_code, observable_id=None)`
- `register_observable_property(property, type_code, property_id=None, property_name="0", observable_id="0", controller_id=None)`

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
- `update_container(widget_id, new_container_id)` - Update widget's container
- `update_location(widget_id, new_location)` - Update widget's location
- `update_observable_reference(property_id, new_observable_id)` - Update property's observable
- `update_property_name(property_id, new_property_name)` - Update property's name
- `update_controller_reference(property_id, new_controller_id)` - Update property's controller
- `remove_container_reference(widget_id)` - Remove container reference
- `remove_observable_reference(property_id)` - Remove observable reference
- `remove_controller_reference(property_id)` - Remove controller reference

### Unregistration
- `unregister(component_id)` - Unregister a component
- `add_widget_unregister_callback(callback)` - Add callback for widget unregistration
- `remove_widget_unregister_callback(callback)` - Remove callback for widget unregistration
- `add_observable_unregister_callback(callback)` - Add callback for observable unregistration
- `remove_observable_unregister_callback(callback)` - Remove callback for observable unregistration
- `add_property_unregister_callback(callback)` - Add callback for property unregistration
- `remove_property_unregister_callback(callback)` - Remove callback for property unregistration
- `add_id_changed_callback(callback)` - Add callback for ID changes
- `remove_id_changed_callback(callback)` - Remove callback for ID changes
- `clear_widget_unregister_callbacks()` - Clear all widget unregister callbacks
- `clear_observable_unregister_callbacks()` - Clear all observable unregister callbacks
- `clear_property_unregister_callbacks()` - Clear all property unregister callbacks
- `clear_id_changed_callbacks()` - Clear all ID changed callbacks
- `clear_all_callbacks()` - Clear all callbacks

### Subscription Methods
- `subscribe_to_id(component_id, callback)` - Subscribe to ID changes
- `unsubscribe_from_id(component_id, callback=None)` - Unsubscribe from ID changes
- `clear_subscriptions()` - Clear all ID subscriptions

## Simple ID Registry

The SimpleIDRegistry provides a way to create and track consistent IDs for any components that don't require the full hierarchy:

```python
from command_system.id_system import get_simple_id_registry

# Get the registry
registry = get_simple_id_registry()

# Register a name with a type code
widget_id = registry.register("t")   # "t:1"
form_id = registry.register("fm")    # "fm:1"

# Register with a custom ID
custom_id = registry.register("t", "t:custom")

# Look up IDs
id_str = registry.get_all_ids()      # Returns all registered IDs

# Check registration and unregister
is_reg = registry.is_registered("t:1")   # True
registry.unregister("t:1")               # True
```

## ID Subscription System

The subscription system allows monitoring changes to component IDs:

```python
from command_system.id_system import subscribe_to_id, unsubscribe_from_id

# Subscribe to changes for a widget ID
def on_widget_id_changed(old_id, new_id):
    print(f"Widget ID changed: {old_id} -> {new_id}")
    
subscribe_to_id("pb:3a:2J:0/2-4b", on_widget_id_changed)

# Later, when the ID changes through any update method:
# The callback receives both old and new IDs
# If the widget moves, subscriptions follow the new ID
```

## Type Codes Reference
The ID system uses distinct type codes for different component types. These are organized into categories and can be accessed through class constants:

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
| Observable | ob |
| Observable Property | op |

### Container Type Codes
These codes represent container components that can hold other widgets:

```python
from command_system.id_system.types import ContainerTypeCodes

ContainerTypeCodes.TAB       # 't' - Tab Container
ContainerTypeCodes.DOCK      # 'd' - Dock Container
ContainerTypeCodes.WINDOW    # 'w' - Window Container
ContainerTypeCodes.CUSTOM    # 'x' - Custom Container
```

### Widget Type Codes
These codes represent UI widgets:

```python
from command_system.id_system.types import WidgetTypeCodes

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
These codes represent observable objects and their properties:

```python
from command_system.id_system.types import ObservableTypeCodes, PropertyTypeCodes

ObservableTypeCodes.OBSERVABLE           # 'ob' - Observable
PropertyTypeCodes.OBSERVABLE_PROPERTY    # 'op' - Observable Property
```

### Working with Type Codes
You can use utility methods to work with type codes:

```python
from command_system.id_system.types import TypeCodes

# Get all widget codes including containers
all_widget_codes = TypeCodes.get_all_widget_codes()

# Check what category a code belongs to
TypeCodes.get_type_category('pb')  # 'widget'
TypeCodes.get_type_category('ob')   # 'observable'

# Check if a code is valid
TypeCodes.is_valid_widgets('pb')       # True
TypeCodes.is_valid_containers('t')     # True
TypeCodes.is_valid_observers('ob')      # True
TypeCodes.is_valid_properties('op')    # True
TypeCodes.is_valid_all_widgets('pb')   # True
```

## Implementation Details

### Clean Handling of Component Lifecycle

#### Registration
- When registering a component, it's added to all relevant mappings
- For container widgets, a new location generator is created

#### Unregistration
Proper cleanup is essential when unregistering components:

1. **Widget/Container Unregistration**:
   - All child widgets using it as a container are either unregistered or reassigned
   - All properties controlled by the widget have their controller reference removed
   - The widget is removed from all mappings and location generators
   - The container's location generator is removed
   - Subscriptions to the widget's ID are properly cleaned up

2. **Observable Unregistration**:
   - All properties referencing this observable are either unregistered or have their observable reference removed
   - The observable is removed from all mappings
   - Subscriptions to the observable's ID are properly cleaned up

3. **Property Unregistration**:
   - The property is removed from all mappings
   - Subscriptions to the property's ID are properly cleaned up

#### ID Updates
When updating an ID:

1. **Widget/Container ID Updates**:
   - All child widgets' container references are updated to the new ID
   - If it's a container, its location generator is preserved but remapped
   - Location maps are updated to reference the new ID
   - All properties controlled by this widget have their controller reference updated
   - All mappings are updated to use the new ID
   - Subscriptions are transferred to the new ID

2. **Observable ID Updates**:
   - All properties referencing this observable have their observable reference updated
   - All mappings are updated to use the new ID
   - Subscriptions are transferred to the new ID

3. **Property ID Updates**:
   - All mappings are updated to use the new ID
   - Subscriptions are transferred to the new ID

### Location ID Generation

When a widget is registered or moved:

1. If no widget_location_id is provided, the container's location generator creates one
2. If a widget_location_id is provided but already exists in that location:
   - For registration: A new widget_location_id is automatically generated
   - For container updates: A new widget_location_id is generated

### ID Collisions

The system handles potential collisions:
- For unique_ids: The global generator ensures no collisions by tracking all used IDs
- For widget_location_ids: Each container location maintains its own set of used IDs
- When attempting to register a widget with an ID that already exists in a location, a new ID is generated
- When updating a container and a collision occurs, a new widget_location_id is generated

### Container Updates

When updating a widget's container:
1. The old container's location generator removes the widget_location_id
2. The new container's location generator either uses the same widget_location_id or generates a new one if there's a collision
3. All container references and location paths are updated automatically

### Multiple Projects Support

The system supports multiple projects running simultaneously:
- Each project has its own root container (normally at "0")
- Projects can have different container IDs to prevent collisions
- Location paths include the project's container hierarchy

## System Architecture: Pyramid Design

The ID system follows a pyramid architecture for maximum simplicity and maintainability:

```
                       ┌─────────────────────────┐
                       │     Public API Layer    │
                       │  (__init__.py exports)  │
                       └─────────────────────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 │        Registry Facade Layer      │
                 │  (Complex operations using lower  │
                 │        level functionality)       │
                 └─────────────────┬─────────────────┘
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       │                           │                           │
┌──────┴──────┐            ┌───────┴─────┐            ┌────────┴─────┐
│   Widget    │            │ Observable  │            │ Subscription │
│   Manager   │            │   Manager   │            │   Manager    │
└──────┬──────┘            └───────┬─────┘            └────────┬─────┘
       │                           │                           │
       └───────────────────────────┼───────────────────────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 │       Core Utilities Layer        │
                 │   (ID parsing, generation, etc.)  │
                 └───────────────────────────────────┘
```

This pyramid structure provides several benefits:
1. Each higher layer uses the functionality of lower layers
2. Base utilities handle specific atomic tasks
3. Managers coordinate related operations
4. The registry facade presents a unified API
5. Complex operations are built from simpler ones

### File Structure

```
command_system/id_system/
│
├── __init__.py                      # Public API exports only
├── types.py                         # Type codes and constants
│
├── core/
│   ├── __init__.py                  # Core exports
│   ├── generator.py                 # Base ID generation 
│   ├── parser.py                    # ID parsing utilities
│   └── registry.py                  # Central registry facade
│
├── managers/
│   ├── __init__.py                  # Manager exports
│   ├── widget_manager.py            # Widget/container relationships
│   ├── observable_manager.py        # Observable/property relationships
│   └── subscription_manager.py      # ID subscription system
│
├── utils/
│   ├── __init__.py                  # Utility exports
│   ├── id_operations.py             # Low-level ID manipulation
│   ├── location_utils.py            # Location path handling
│   └── validation.py                # ID validation functions
│
└── simple/
    ├── __init__.py                  # Simple registry exports
    └── simple_registry.py           # Simplified registry implementation
```

### Implementation Hierarchy

#### Base Utilities (Bottom Layer)
- **ID Parsing**: Extract components from ID strings
- **ID Validation**: Check ID format validity
- **ID Generation**: Create new unique identifiers
- **Location Utilities**: Manipulate location paths

#### Managers (Middle Layer)
- **Widget Manager**: Handle widget-container relationships using base utilities
- **Observable Manager**: Handle observable-property-controller relationships
- **Subscription Manager**: Track and notify ID changes

#### Registry Facade (Top Internal Layer)
- Delegates operations to appropriate managers
- Coordinates complex operations that span multiple managers
- Maintains weak references to components
- Provides a unified interface for the public API

#### Public API (Top Layer)
- Exposes only the necessary methods to external code
- Maintains backward compatibility
- Simplified interface hiding internal complexity

This pyramid structure ensures each component has a clear, focused responsibility, making the system easier to maintain, test, and extend while providing a simple interface to consumers.