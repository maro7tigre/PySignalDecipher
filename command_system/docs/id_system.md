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
  - `container_location`: Path within the container hierarchy (e.g., "0", "0/1", "2/3")
  - `widget_location_id`: Unique identifier within that specific container location

Examples:
- `pb:3a:0:0-1` - A push button with no container, at root location with widget ID "1"
- `t:2J:0:0-0` - A tab container at the root level (project itself)
- `pb:3a:2J:0/1-4b` - A push button in container "2J", at path "0/1" with widget location ID "4b"
- `cb:5c:3a:2/1-7d` - A checkbox in container "3a", at nested path "2/1" with widget location ID "7d"

### 2. Observable Format
```
[type_code]:[unique_id]
```

Example:
- `o:4C` - An observable with unique ID "4C"

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
  ├── Container 1 (t:1A:0:0-0)
  │     ├── Widget 1-1 (pb:3C:1A:0/0-1)
  │     ├── Widget 1-2 (le:4D:1A:0/0-2)
  │     └── Nested Container (d:8H:1A:0/0-3)
  │           ├── Nested Widget 1 (pb:9I:8H:0/0/3-1)
  │           └── Nested Widget 2 (le:10J:8H:0/0/3-2)
  │
  └── Container 2 (t:2B:0:0-1)
        ├── Widget 2-1 (pb:6F:2B:0/1-1)
        └── Widget 2-2 (le:7G:2B:0/1-2)
```

This hierarchical approach supports arbitrarily deep nesting of containers, with each level maintaining its own location context.

## Location System

The location is a composite identifier with two parts:
1. `container_location`: Path in the container hierarchy (e.g., "0", "0/1", "2/3")
2. `widget_location_id`: Unique ID within that specific container location

Important behaviors:
- The project itself is container "0" at location "0"
- Each container location has its own ID generator
- Widget location IDs remain stable when moving within the same container location
- When a widget changes container, its widget_location_id may change if there's a collision
- The container location in a widget's location string is controlled by its container

## Registration and Updates

### Widget Registration

When registering a widget:
1. If a container is specified, the widget's location includes the container's location path
2. If a location is specified without a widget_location_id, one is generated automatically
3. If a full location is provided (with widget_location_id), it's used as-is unless there's a collision
4. In case of collision, the system increments the widget_location_id until finding an available one

### ID Updates

When updating a widget's container:
1. The container_unique_id in the widget's ID is updated
2. The container_location part of the location is updated to match the new container
3. The widget_location_id remains the same unless there's a collision
4. The widget is unregistered from the old container's location generator
5. The widget is registered with the new container's location generator

When updating a widget's location:
1. Only the widget_location_id part changes, not the container_location
2. If the specified widget_location_id exists, it's incremented until an available ID is found
3. The widget is unregistered from the old location and registered at the new location

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
- `update_id(old_id, new_id)` - Update any component's ID and all references to it
- `update_container_id(widget_id, new_container_id)` - Update widget's container
- `update_location(widget_id, new_location)` - Update widget's location
- `update_observable_id(property_id, new_observable_id)` - Update property's observable
- `update_property_name(property_id, new_property_name)` - Update property's name
- `update_controller_id(property_id, new_controller_id)` - Update property's controller
- `remove_container_reference(widget_id)` - Remove container reference
- `remove_observable_reference(property_id)` - Remove observable reference
- `remove_controller_reference(property_id)` - Remove controller reference

### Unregistration
- `unregister(component_id, replacement_id=None)` - Unregister a component with optional replacement
- `set_on_widget_unregister(callback)` - Set callback for widget unregistration
- `set_on_observable_unregister(callback)` - Set callback for observable unregistration
- `set_on_property_unregister(callback)` - Set callback for property unregistration
- `set_on_id_changed(callback)` - Set callback for ID changes

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
When updating an ID with `update_id`:

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
   - The system will increment the ID until finding an available one
   - For example, if IDs [0,1,2,3] exist and you try to register with ID "3"
   - The system will try "4" and use that if available

### ID Collisions

The system handles potential collisions:
- For unique_ids: The global generator ensures no collisions by tracking all used IDs
- For widget_location_ids: Each container location maintains its own set of used IDs
- When attempting to register an ID that already exists, the system increments until finding an available ID

### Container Updates

When updating a widget's container:
1. The old container's location generator removes the widget_location_id
2. The new container's location generator registers or generates a new widget_location_id
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
                 │        Registry Facade Layer       │
                 │  (Complex operations using lower   │
                 │        level functionality)        │
                 └─────────────────┬─────────────────┘
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       │                           │                           │
┌──────┴──────┐            ┌──────┴──────┐            ┌──────┴──────┐
│   Widget    │            │ Observable  │            │ Subscription │
│   Manager   │            │   Manager   │            │   Manager    │
└──────┬──────┘            └──────┬──────┘            └──────┬──────┘
       │                           │                           │
       └───────────────────────────┼───────────────────────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 │       Core Utilities Layer        │
                 │   (ID parsing, generation, etc.)  │
                 └─────────────────────────────────────┘
```

This pyramid structure provides several benefits:
1. Each higher layer uses the functionality of lower layers
2. Base utilities handle specific atomic tasks
3. Managers coordinate related operations
4. The registry facade presents a unified API
5. Complex operations are built from simpler ones

### Revised File Structure

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