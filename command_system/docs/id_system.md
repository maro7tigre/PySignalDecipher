# PySignalDecipher ID System Documentation

## Overview

The ID system creates and manages unique identifiers for tracking components without maintaining direct references. This enables advanced serialization, navigation, and reference management across the application.

The system uses string-based IDs that encode type, hierarchy, and relationships between different components using a consistent format. It supports both static and dynamic components through a hierarchical design.

## Table of Contents

- [Core Concepts](#core-concepts)
- [ID Formats](#id-formats)
- [Registry Methods Reference](#registry-methods-reference)
  - [Getting Started](#getting-started)
  - [Registration Methods](#registration-methods)
  - [Component Retrieval Methods](#component-retrieval-methods)
  - [Container Relationship Methods](#container-relationship-methods)
  - [Observable Relationship Methods](#observable-relationship-methods)
  - [ID Update Methods](#id-update-methods)
  - [Reference Removal Methods](#reference-removal-methods)
  - [Subscription Methods](#subscription-methods)
  - [Callback Registration Methods](#callback-registration-methods)
- [Utility Functions](#utility-functions)
  - [ID Subscription Utilities](#id-subscription-utilities)
  - [Parser Utilities](#parser-utilities)
  - [Creation Utilities](#creation-utilities)
  - [Validation Utilities](#validation-utilities)
  - [Location Utilities](#location-utilities)
- [Simple ID Registry](#simple-id-registry)
- [Type Code Constants](#type-code-constants)
- [Common Patterns and Examples](#common-patterns-and-examples)
  - [Widget Registration](#widget-registration)
  - [Container Hierarchies](#container-hierarchies)
  - [Observable Properties](#observable-properties)
  - [Property Controllers](#property-controllers)
  - [ID Subscription](#id-subscription)
  - [Serialization and Restoration](#serialization-and-restoration)
- [Common Patterns and Best Practices](#common-patterns-and-best-practices)
- [Error Handling](#error-handling)

## Core Concepts

The ID system is built around four main component types:

1. **Widgets**: UI components that users interact with (buttons, text fields, etc.)
2. **Containers**: Special widgets that can contain other widgets (windows, tabs, etc.)
3. **Observables**: Objects with properties that can be observed for changes
4. **Properties**: Individual properties of observable objects that can be bound to widgets

Each component is assigned a unique ID that encodes its type, identity, and relationships with other components. These IDs are used to track and manipulate components throughout the system.

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

## Registry Methods Reference

### Getting Started

To use the ID system, import it and get a reference to the registry:

```python
from command_system.id_system import get_id_registry

# Get the global ID registry
registry = get_id_registry()
```

### Registration Methods

| Method | Description |
|--------|-------------|
| `register(widget, type_code, widget_id=None, container_id=None, location=None)` | Register a widget or container. Returns the widget's full ID as a string. |
| `register_observable(observable, type_code, observable_id=None)` | Register an observable object. Returns the observable's full ID as a string. |
| `register_observable_property(property_obj, type_code, property_id=None, property_name="0", observable_id="0", controller_id=None)` | Register a property with relationships. Returns the property's full ID as a string. |
| `unregister(component_id)` | Unregister any component. Returns True if successful, False otherwise. |

#### Example: Register Components

```python
# Register a widget (returns the full widget ID)
widget_id = registry.register(
    widget_object,      # The widget object to register
    "pb",               # Type code (e.g., "pb" for push button)
    unique_id=None,     # Optional unique ID (default: auto-generated)
    container_id=None,  # Container widget ID (default: root container)
    location=None       # Location ID within container (default: auto-generated)
)

# Register an observable
observable_id = registry.register_observable(
    observable_object,  # The observable object
    "ob",               # Type code ("ob" for observable)
    observable_id=None  # Optional unique ID (default: auto-generated)
)

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

### Component Retrieval Methods

| Method | Description |
|--------|-------------|
| `get_widget(widget_id)` | Get a widget by ID. Returns the widget object or None if not found. |
| `get_observable(observable_id)` | Get an observable by ID. Returns the observable object or None if not found. |
| `get_observable_property(property_id)` | Get a property by ID. Returns the property object or None if not found. |
| `get_id(component)` | Get the ID for a component. Returns the component ID as a string, or None if not found. |
| `get_unique_id_from_id(id_string)` | Extract unique ID from any ID string. Returns the unique ID portion as a string. |
| `get_full_id_from_unique_id(unique_id, type_code=None)` | Get full ID from a unique ID. Returns the full ID string or None if not found. |

#### Example: Retrieve Components

```python
# Get a widget by its ID
widget = registry.get_widget(widget_id)

# Get an observable by its ID
observable = registry.get_observable(observable_id)

# Get a property by its ID
property_obj = registry.get_observable_property(property_id)

# Get the ID for any registered component
component_id = registry.get_id(component_object)

# Extract the unique ID portion from any ID string
unique_id = registry.get_unique_id_from_id(component_id)
```

### Container Relationship Methods

| Method | Description |
|--------|-------------|
| `get_container_widgets(container_id)` | Get widgets in a container. Returns a list of widget IDs. |
| `get_widgets_by_container_id(container_id)` | Get all widgets in a container. Returns a list of widget IDs. |
| `get_container_id_from_widget_id(widget_id)` | Get a widget's container. Returns the container ID or "0" if at root. |
| `get_locations_map(container_id)` | Get container's locations map. Returns dictionary mapping location paths to widget IDs. |
| `set_locations_map(container_id, locations_map)` | Set container's locations map. |
| `get_container_widgets_at_location(container_id, location)` | Get widgets at a specific location. Returns a list of widget IDs. |

#### Example: Working with Containers

```python
# Get all widgets in a container
widgets = registry.get_widgets_by_container_id(container_id)

# Get the container a widget belongs to
container_id = registry.get_container_id_from_widget_id(widget_id)

# Get all widgets at a specific location in a container
widgets_at_location = registry.get_container_widgets_at_location(container_id, location)

# Get the container's widget structure (organized by location)
locations_map = registry.get_locations_map(container_id)
```

### Observable Relationship Methods

| Method | Description |
|--------|-------------|
| `get_observable_properties(observable_id)` | Get all properties for an observable. Returns a list of property IDs. |
| `get_observable_id_from_property_id(property_id)` | Get a property's observable. Returns the observable ID or None. |
| `get_controller_properties(controller_id)` | Get properties controlled by a widget. Returns a list of property IDs. |
| `get_controller_id_from_property_id(property_id)` | Get a property's controller. Returns the controller ID or None. |
| `get_property_ids_by_observable_id_and_property_name(observable_id, property_name)` | Get properties by name. Returns a list of property IDs. |

#### Example: Working with Observables

```python
# Get all properties for an observable
properties = registry.get_observable_properties(observable_id)

# Get a property's observable
observable_id = registry.get_observable_id_from_property_id(property_id)

# Get all properties controlled by a widget
controlled_properties = registry.get_controller_properties(controller_id)

# Get a property's controller widget
controller_id = registry.get_controller_id_from_property_id(property_id)

# Get properties with a specific name on an observable
name_properties = registry.get_property_ids_by_observable_id_and_property_name(
    observable_id, "name"
)
```

### ID Update Methods

| Method | Description |
|--------|-------------|
| `update_id(old_id, new_id)` | Update any component's ID directly. Returns (success, actual_new_id, error_message). |
| `update_container(widget_id, new_container_id)` | Move a widget to a different container. Returns the new widget ID. |
| `update_location(widget_id, new_location)` | Change a widget's location within its container. Returns the new widget ID. |
| `update_observable_reference(property_id, new_observable_id)` | Change a property's observable. Returns the new property ID. |
| `update_property_name(property_id, new_property_name)` | Change a property's name. Returns the new property ID. |
| `update_controller_reference(property_id, new_controller_id)` | Change a property's controller. Returns the new property ID. |

#### Example: Updating Components

```python
# Update a widget's container
updated_widget_id = registry.update_container(widget_id, new_container_id)

# Update a widget's location within its container
updated_widget_id = registry.update_location(widget_id, new_location)

# Update a property's observable reference
updated_property_id = registry.update_observable_reference(property_id, new_observable_id)

# Update a property's name
updated_property_id = registry.update_property_name(property_id, new_property_name)

# Update a property's controller
updated_property_id = registry.update_controller_reference(property_id, new_controller_id)

# Direct ID update (advanced usage)
success, updated_id, error = registry.update_id(old_id, new_id)
if not success:
    print(f"Update failed: {error}")
```

### Reference Removal Methods

| Method | Description |
|--------|-------------|
| `remove_container_reference(widget_id)` | Remove a widget's container reference. Returns the updated widget ID. |
| `remove_observable_reference(property_id)` | Remove a property's observable reference. Returns the updated property ID. |
| `remove_controller_reference(property_id)` | Remove a property's controller reference. Returns the updated property ID. |

#### Example: Removing References

```python
# Remove a widget's container (set to root)
updated_id = registry.remove_container_reference(widget_id)

# Remove a property's observable reference
updated_id = registry.remove_observable_reference(property_id)

# Remove a property's controller reference
updated_id = registry.remove_controller_reference(property_id)
```

### Subscription Methods

| Method | Description |
|--------|-------------|
| `subscribe_to_id(component_id, callback)` | Subscribe to ID changes. Returns True if subscription was successful. |
| `unsubscribe_from_id(component_id, callback=None)` | Unsubscribe from ID changes. Returns True if unsubscription was successful. |
| `clear_subscriptions()` | Clear all subscriptions. Returns True if successful. |

#### Example: ID Subscriptions

```python
# Define a callback function for ID changes
def on_id_changed(old_id, new_id):
    print(f"ID changed: {old_id} -> {new_id}")
    # Update references as needed

# Subscribe to ID changes
registry.subscribe_to_id(component_id, on_id_changed)

# Unsubscribe from ID changes
registry.unsubscribe_from_id(component_id, on_id_changed)

# Clear all subscriptions
registry.clear_subscriptions()
```

### Callback Registration Methods

| Method | Description |
|--------|-------------|
| `add_widget_unregister_callback(callback)` | Add a callback for widget unregistration. Callback receives (widget_id, widget). |
| `remove_widget_unregister_callback(callback)` | Remove a widget unregister callback. |
| `add_observable_unregister_callback(callback)` | Add a callback for observable unregistration. Callback receives (observable_id, observable). |
| `remove_observable_unregister_callback(callback)` | Remove an observable unregister callback. |
| `add_property_unregister_callback(callback)` | Add a callback for property unregistration. Callback receives (property_id, property_obj). |
| `remove_property_unregister_callback(callback)` | Remove a property unregister callback. |
| `add_id_changed_callback(callback)` | Add a callback for ID changes. Callback receives (old_id, new_id). |
| `remove_id_changed_callback(callback)` | Remove an ID changed callback. |
| `clear_widget_unregister_callbacks()` | Clear all widget unregister callbacks. |
| `clear_observable_unregister_callbacks()` | Clear all observable unregister callbacks. |
| `clear_property_unregister_callbacks()` | Clear all property unregister callbacks. |
| `clear_id_changed_callbacks()` | Clear all ID changed callbacks. |
| `clear_all_callbacks()` | Clear all callbacks. |

#### Example: Callback Registration

```python
# Add a callback for widget unregistration
def on_widget_unregister(widget_id, widget):
    print(f"Widget unregistered: {widget_id}")

registry.add_widget_unregister_callback(on_widget_unregister)

# Add a callback for ID changes
def on_id_changed(old_id, new_id):
    print(f"ID changed: {old_id} -> {new_id}")

registry.add_id_changed_callback(on_id_changed)

# Clear all callbacks when done
registry.clear_all_callbacks()
```

## Utility Functions

### ID Subscription Utilities

| Function | Description |
|----------|-------------|
| `subscribe_to_id(component_id, callback)` | Global function to subscribe to ID changes. Returns True if successful. |
| `unsubscribe_from_id(component_id, callback=None)` | Global function to unsubscribe from ID changes. Returns True if successful. |
| `clear_subscriptions()` | Global function to clear all subscriptions. Returns True if successful. |

### Parser Utilities

| Function | Description |
|----------|-------------|
| `parse_widget_id(id_string)` | Parse a widget ID string into its components. Returns a dictionary or None if invalid. |
| `parse_observable_id(id_string)` | Parse an observable ID string into its components. Returns a dictionary or None if invalid. |
| `parse_property_id(id_string)` | Parse a property ID string into its components. Returns a dictionary or None if invalid. |
| `get_unique_id_from_id(id_string)` | Extract the unique ID portion from any type of ID string. Returns a string or None if invalid. |
| `get_type_code_from_id(id_string)` | Extract the type code portion from any type of ID string. Returns a string or None if invalid. |

#### Example: Parsing IDs

```python
from command_system.id_system.core.parser import (
    parse_widget_id, 
    parse_observable_id, 
    parse_property_id,
    get_unique_id_from_id
)

# Parse a widget ID
widget_components = parse_widget_id(widget_id)
if widget_components:
    print(f"Type code: {widget_components['type_code']}")
    print(f"Unique ID: {widget_components['unique_id']}")
    print(f"Container ID: {widget_components['container_unique_id']}")
    print(f"Container location: {widget_components['container_location']}")
    print(f"Widget location ID: {widget_components['widget_location_id']}")

# Extract unique ID from any component ID
unique_id = get_unique_id_from_id(some_id)
```

### Creation Utilities

| Function | Description |
|----------|-------------|
| `create_widget_id(type_code, unique_id, container_id=DEFAULT_NO_CONTAINER, container_location="0", widget_location_id="0")` | Create a widget ID string from components. Returns the widget ID string. |
| `create_observable_id(type_code, unique_id)` | Create an observable ID string from components. Returns the observable ID string. |
| `create_property_id(type_code, unique_id, observable_id=DEFAULT_NO_OBSERVABLE, property_name=DEFAULT_NO_PROPERTY_NAME, controller_id=DEFAULT_NO_CONTROLLER)` | Create a property ID string from components. Returns the property ID string. |

#### Example: Creating IDs

```python
from command_system.id_system.core.parser import (
    create_widget_id, 
    create_observable_id, 
    create_property_id
)

# Create a widget ID
widget_id = create_widget_id(
    "pb",                   # Type code
    "custom_unique_id",     # Unique ID 
    "container_unique_id",  # Container ID
    "0/1",                  # Container location
    "button_location"       # Widget location ID
)

# Create an observable ID
observable_id = create_observable_id("ob", "model_id")

# Create a property ID
property_id = create_property_id(
    "op",                   # Type code
    "prop_id",              # Unique ID
    "model_id",             # Observable ID
    "value",                # Property name
    "controller_id"         # Controller ID
)
```

### Validation Utilities

| Function | Description |
|----------|-------------|
| `is_valid_widget_id(id_string)` | Check if a widget ID string is valid. Returns a boolean. |
| `is_valid_observable_id(id_string)` | Check if an observable ID string is valid. Returns a boolean. |
| `is_valid_property_id(id_string)` | Check if a property ID string is valid. Returns a boolean. |
| `is_valid_type_code(type_code, component_type=None)` | Check if a type code is valid for the given component type. Returns a boolean. |

### Location Utilities

| Function | Description |
|----------|-------------|
| `is_valid_container_location(location)` | Check if a container location string is valid. Returns a boolean. |
| `get_parent_container_location(location)` | Get the parent container location of a given container location. Returns a string. |
| `join_container_locations(parent_location, child_index)` | Join a parent container location with a child index to form a new path. Returns a string. |
| `increment_widget_location_id(location_id)` | Increment a widget location ID to find the next available ID. Returns a string. |
| `find_available_widget_location_id(location_id, is_registered_func)` | Find an available widget location ID starting from the given ID. Returns a string. |

## Simple ID Registry

The Simple ID Registry provides a lightweight way to generate IDs without the full hierarchy and relationship tracking of the main ID system. It's useful for simpler components or temporary IDs.

| Method | Description |
|--------|-------------|
| `get_simple_id_registry()` | Get the global SimpleIDRegistry instance. Returns the SimpleIDRegistry singleton. |
| `SimpleIDRegistry.register(type_code, custom_id=None)` | Register and generate a unique ID. Returns an ID string. |
| `SimpleIDRegistry.unregister(id_str)` | Unregister an ID. Returns True if successful, False otherwise. |
| `SimpleIDRegistry.is_registered(id_str)` | Check if an ID is registered. Returns a boolean. |
| `SimpleIDRegistry.get_all_ids()` | Get all registered IDs. Returns a list of ID strings. |
| `SimpleIDRegistry.clear()` | Clear all registrations. |

#### Example: Simple ID Registry

```python
from command_system.id_system import get_simple_id_registry

# Get the simple registry
simple_registry = get_simple_id_registry()

# Register a type with a type code
widget_id = simple_registry.register("pb")   # "pb:1"
form_id = simple_registry.register("fm")     # "fm:1"

# Register with a custom ID
custom_id = simple_registry.register("t", "t:custom")

# Look up IDs
all_ids = simple_registry.get_all_ids()

# Check registration and unregister
is_reg = simple_registry.is_registered("pb:1")
simple_registry.unregister("pb:1")
```

## Type Code Constants

The ID system defines several sets of type codes for different component types:

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

## Common Patterns and Examples

### Widget Registration

```python
# Basic widget registration
button = PushButton("Submit")
button_id = registry.register(button, WidgetTypeCodes.PUSH_BUTTON)

# Widget with specific container
container = TabWidget()
container_id = registry.register(container, ContainerTypeCodes.TAB)
label = Label("Name:")
label_id = registry.register(label, WidgetTypeCodes.CUSTOM_WIDGET, None, container_id)

# Widget with custom unique ID
spinner = SpinBox()
spinner_id = registry.register(spinner, WidgetTypeCodes.SPIN_BOX, "age_spinner")
```

### Container Hierarchies

```python
# Create a nested container structure
main_window = Window()
tab_container = TabWidget()
panel = Panel()

# Register with hierarchy
main_id = registry.register(main_window, "w")           # Window container
tab_id = registry.register(tab_container, "t", None, main_id)  # Tab in main window
panel_id = registry.register(panel, "x", None, tab_id)   # Panel in tab

# Add widgets to different levels
button1 = PushButton("Main")
button2 = PushButton("Tab")
button3 = PushButton("Panel")

button1_id = registry.register(button1, "pb", None, main_id)
button2_id = registry.register(button2, "pb", None, tab_id)
button3_id = registry.register(button3, "pb", None, panel_id)

# Get widgets at each level
main_widgets = registry.get_widgets_by_container_id(main_id)
tab_widgets = registry.get_widgets_by_container_id(tab_id)
panel_widgets = registry.get_widgets_by_container_id(panel_id)
```

### Observable Properties

```python
# Create observable data model
data_model = DataModel()
model_id = registry.register_observable(data_model, "ob")

# Register properties
name_property_id = registry.register_observable_property(
    data_model.name_property,  # Property object
    "op",                      # Type code
    None,                      # Auto-generated ID
    "name",                    # Property name
    model_id                   # Observable ID
)

age_property_id = registry.register_observable_property(
    data_model.age_property,
    "op", 
    None,
    "age",
    model_id
)

# Get all properties for the model
model_properties = registry.get_observable_properties(model_id)

# Get properties by name
name_properties = registry.get_property_ids_by_observable_id_and_property_name(
    model_id, "name"
)
```

### Property Controllers

```python
# Create components
data_model = PersonModel()
name_edit = LineEdit()
age_spinner = SpinBox()

# Register components
model_id = registry.register_observable(data_model, "ob")
name_edit_id = registry.register(name_edit, "le")
age_spinner_id = registry.register(age_spinner, "sp")

# Register properties with controllers
name_property_id = registry.register_observable_property(
    data_model.name_property,
    "op",
    None,
    "name",
    model_id,
    name_edit_id  # Controller widget
)

age_property_id = registry.register_observable_property(
    data_model.age_property,
    "op",
    None,
    "age",
    model_id,
    age_spinner_id  # Controller widget
)

# Get properties controlled by a widget
name_edit_properties = registry.get_controller_properties(name_edit_id)
```

### ID Subscription

```python
# Subscribe to ID changes
def on_id_changed(old_id, new_id):
    print(f"ID changed: {old_id} -> {new_id}")
    # Update any references to this ID in your application

# Subscribe to a widget's ID changes
subscribe_to_id(widget_id, on_id_changed)

# When the widget is updated (e.g., moved to a new container)
new_widget_id = registry.update_container(widget_id, new_container_id)
# on_id_changed will be called with (widget_id, new_widget_id)

# Unsubscribe when no longer needed
unsubscribe_from_id(new_widget_id, on_id_changed)
```

### Serialization and Restoration

```python
# Serialize a UI component hierarchy
def serialize_component(component_id):
    # Get component and its relationships
    component = registry.get_widget(component_id)
    container_id = registry.get_container_id_from_widget_id(component_id)
    child_ids = registry.get_widgets_by_container_id(component_id)
    
    # Serialize the component hierarchy
    serialized = {
        'id': component_id,
        'type': get_type_code_from_id(component_id),
        'container': container_id,
        'children': [serialize_component(child_id) for child_id in child_ids],
        'properties': {}
    }
    
    # If component has properties, serialize them too
    if hasattr(component, 'get_properties'):
        for prop_name, prop_value in component.get_properties().items():
            serialized['properties'][prop_name] = prop_value
            
    return serialized

# Restore from serialization
def restore_component(serialized_data):
    # Create component instance based on type
    type_code = serialized_data['type']
    component = create_component_by_type(type_code)
    
    # Register with the same ID
    component_id = registry.register(
        component,
        type_code,
        get_unique_id_from_id(serialized_data['id']),
        serialized_data['container']
    )
    
    # Restore properties
    if hasattr(component, 'set_properties') and 'properties' in serialized_data:
        component.set_properties(serialized_data['properties'])
        
    # Restore children
    for child_data in serialized_data['children']:
        restore_component(child_data)
    
    return component_id
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

Common errors include:
- Attempting to use a location ID that's already in use
- Trying to change a component's type code
- Attempting to use a unique ID that's already registered
- Referencing components that don't exist
- Invalid ID format

## Practical Real-World Examples

### Example 1: Widget Registration and Container Hierarchy

```python
# Create a nested container structure
main_container = MainWindow()
tab_container = TabWidget()
button = PushButton("Click me")

# Register with ID system
id_registry = get_id_registry()
main_id = id_registry.register(main_container, "w")  # Window container
tab_id = id_registry.register(tab_container, "t", None, main_id)
button_id = id_registry.register(button, "pb", None, tab_id)

# Later, get a widget by its ID
retrieved_button = id_registry.get_widget(button_id)
```

### Example 2: Observable Property Binding

```python
# Create and register observable and widget
data_model = DataModel()
slider = Slider()

# Register with ID system
id_registry = get_id_registry()
model_id = id_registry.register_observable(data_model, "ob")
slider_id = id_registry.register(slider, "sl")

# Register property with controller
property_id = id_registry.register_observable_property(
    data_model.value_property,  # Property object
    "op",                       # Type code
    None,                       # Unique ID (auto-generated)
    "value",                    # Property name
    model_id,                   # Observable ID
    slider_id                   # Controller widget ID
)

# Later, find all properties controlled by a widget
controlled_properties = id_registry.get_controller_properties(slider_id)
```

### Example 3: Subscription to ID Changes

```python
# Subscribe to ID changes
def on_id_changed(old_id, new_id):
    print(f"ID changed: {old_id} -> {new_id}")
    # Update any references to this ID

# Subscribe to widget ID changes
subscribe_to_id(widget_id, on_id_changed)

# Update widget location, triggering notification
updated_id = id_registry.update_location(widget_id, "new_location")

# When done, unsubscribe
unsubscribe_from_id(updated_id, on_id_changed)
```

### Example 4: Using the Simple ID Registry

```python
# Get the simple registry for basic ID generation
simple_registry = get_simple_id_registry()

# Generate IDs for different component types
button_id = simple_registry.register("pb")   # "pb:1"
slider_id = simple_registry.register("sl")   # "sl:1"

# Register with a custom ID
custom_id = simple_registry.register("cw", "cw:custom")

# Check registration status
is_registered = simple_registry.is_registered("pb:1")  # True

# Unregister when done
simple_registry.unregister("pb:1")
```

### Example 5: Integration with Command System

```python
from command_system.core import PropertyCommand, get_command_manager

# Create a command to update a property value
def create_property_command(property_id, new_value, trigger_widget_id=None):
    # Create the property command
    command = PropertyCommand(property_id, new_value)
    
    # Set the widget that triggered this command
    if trigger_widget_id:
        command.set_trigger_widget(trigger_widget_id)
    
    # Execute the command
    command_manager = get_command_manager()
    command_manager.execute(command)
    
    return command

# Usage with ID system
value_property_id = registry.register_observable_property(
    model.value_property, "op", None, "value", model_id, slider_id
)

# User changed the slider, create a command
create_property_command(value_property_id, 75, slider_id)
```

## Advanced Topics

### ID Format Internals

Understanding the ID format can help when debugging or implementing custom extensions:

1. **Widget ID parts**:
   - Type code: 2-3 letter code indicating widget type
   - Unique ID: Alphanumeric identifier specific to this instance
   - Container unique ID: The unique ID of the containing widget (or "0" for root)
   - Location: Composite of the container path and widget-location-id

2. **Observable ID parts**:
   - Type code: "ob" for standard observables
   - Unique ID: Alphanumeric identifier specific to this instance

3. **Property ID parts**:
   - Type code: "op" for observable properties
   - Unique ID: Alphanumeric identifier specific to this instance
   - Observable unique ID: The unique ID of the associated observable (or "0" for none)
   - Property name: Name of the property
   - Controller ID: The unique ID of the widget controlling this property (or "0" for none)

### Custom Type Codes

You can extend the ID system with custom type codes for your own component types:

```python
# Define custom type codes
class MyWidgetTypeCodes:
    GAUGE = 'ga'
    CHART = 'ch'
    
# Register with custom type codes
gauge_widget = GaugeWidget()
gauge_id = registry.register(gauge_widget, MyWidgetTypeCodes.GAUGE)
```

### Callback Systems

The ID system provides multiple callback systems:

1. **ID Subscription**: For tracking when component IDs change
2. **Unregister Callbacks**: For cleanup when components are unregistered
3. **ID Changed Callbacks**: For system-level monitoring of ID changes

Use the appropriate system based on your needs:
- For UI components that need to maintain references, use ID subscription
- For cleanup tasks during unregistration, use unregister callbacks
- For system-wide monitoring, use ID changed callbacks

### Custom Component Registry

For applications with custom component types, you can extend the default registry:

```python
from command_system.id_system import IDRegistry

class ExtendedIDRegistry(IDRegistry):
    def __init__(self):
        super().__init__()
        self._custom_components = {}
        
    def register_custom_component(self, component, type_code, unique_id=None):
        # Register with base class first
        component_id = self.register(component, type_code, unique_id)
        
        # Add to custom tracking
        self._custom_components[component_id] = component
        
        return component_id
        
    def get_all_custom_components(self):
        return self._custom_components
```

## Conclusion

The ID system provides a flexible and powerful way to manage component relationships in complex applications. By leveraging unique identifiers instead of direct references, it enables advanced serialization, navigation, and relationship tracking while avoiding common issues with reference cycles and memory management.

Key benefits include:

1. **Relationship Tracking**: Easily track and manage relationships between components
2. **Serialization Support**: Serialize component hierarchies without complex reference handling
3. **Change Notification**: Subscribe to component changes to update dependent parts of the application
4. **Undo/Redo Support**: Enable comprehensive undo/redo systems by tracking component relationships

By understanding and using the ID system effectively, you can create more modular, maintainable, and feature-rich applications.