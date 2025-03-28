# Widget & Observable ID System Documentation

This document provides a concise overview of the ID system for tracking and referencing widgets and observables in the PySignalDecipher application. The system provides memory-efficient unique identifiers for widgets, observables, and their relationships, allowing for serialization, navigation, and reference management without maintaining direct object references.

## Overview

The ID system creates and manages unique identifiers for both widgets and observables, encoding their type, relationships, and properties.

```mermaid
flowchart TD
    subgraph "ID System Core"
        IDRegistry["IDRegistry\n(Singleton)"]
        IDGenerator["IDGenerator"]
        IDUtils["ID Utilities"]
    end
    
    subgraph "Widget ID Format"
        WidgetFormat["type_code:unique_id:container_unique_id:location"]
    end
    
    subgraph "Observable ID Format"
        ObservableFormat["obs:unique_id:widget_unique_id:property_name"]
    end
    
    subgraph "Property ID Format"
        PropertyFormat["observable_id:property_name"]
    end
    
    IDRegistry --> IDGenerator
    IDRegistry --> IDUtils
    
    style IDRegistry stroke:#9370db,stroke-width:2px
    style IDGenerator stroke:#228b22,stroke-width:1px
    style IDUtils stroke:#228b22,stroke-width:1px
    style WidgetFormat stroke:#4682b4,stroke-width:2px
    style ObservableFormat stroke:#ff7f50,stroke-width:2px
    style PropertyFormat stroke:#32cd32,stroke-width:2px
```

## ID Formats

### Widget ID Format
Each widget ID follows this format:
```
[type_code]:[unique_id]:[container_unique_id]:[location]
```

Where:
- `type_code`: Short code indicating widget type (e.g., 'le', 't')
- `unique_id`: Base62-encoded unique identifier
- `container_unique_id`: The unique_id of the parent container (or "0" if none)
- `location`: Container-specific location identifier (or "0" if not applicable)

Examples:
- `le:1Z:0:0` - A line edit widget with no container
- `t:2J:0:1` - A tab container (in slot 1) with no parent
- `pb:3a:2J:2` - A push button widget in a container with unique_id 2J, at location 2

### Observable ID Format
Each observable ID follows this format:
```
obs:[unique_id]:[widget_unique_id]:[property_name]
```

Where:
- `obs`: Fixed code indicating this is an observable
- `unique_id`: Base62-encoded unique identifier
- `widget_unique_id`: The unique_id of the controlling widget (or "0" if none)
- `property_name`: The name of the property this observable represents (or empty if not applicable)

Examples:
- `obs:4a:0:` - An observable with no controlling widget or property
- `obs:5C:1Z:name` - An observable for the "name" property, controlled by widget with unique_id 1Z
- `obs:6D:3a:value` - An observable for the "value" property, controlled by widget with unique_id 3a

### Property ID Format
Each property ID follows this format:
```
[observable_id]:[property_name]
```

Where:
- `observable_id`: The full observable ID
- `property_name`: The name of the property

Examples:
- `obs:5C:1Z:name:name` - A property named "name" for the observable with ID obs:5C:1Z:name
- `obs:6D:3a:value:value` - A property named "value" for the observable with ID obs:6D:3a:value

## Core API

### Integration with Widgets

To use the ID system in your widgets, modify your base widget class as follows:

```python
class CommandWidgetBase(Generic[T]):
    def __init__(self, widget_id=None, container_id=None):
        self.registry = get_id_registry()
        self.widget_register(widget_id, container_id)
        ...
        
    def widget_register(self, widget_id, container_id):
        raise NotImplementedError("Subclasses must implement widget_register")
```

Then implement the registration in your subclasses:

```python
def widget_register(self, widget_id, container_id):
    widget_code = "ZZ"  # Use appropriate type code from TypeCodes class
    self.widget_id = self.registry.register_widget(self, widget_code, widget_id, container_id)
```

### Integration with Observables

For observable objects, implement registration as follows:

```python
class Person(Observable):
    name = ObservableProperty[str]("John Doe")
    email = ObservableProperty[str]("john@example.com")
    
    def __init__(self):
        super().__init__()
        self.registry = get_id_registry()
        self.observable_id = self.registry.register_observable(self)
        
        # Register properties (optional)
        self.registry.register_property("name", self.observable_id, self.name)
        self.registry.register_property("email", self.observable_id, self.email)
```

### Binding Widgets to Observables

To bind a widget to an observable:

```python
# Create an observable and register it
person = Person()
person_observable_id = registry.get_observable_id(person)

# Create a widget and register it
name_field = LineEditWidget()
name_widget_id = registry.get_widget_id(name_field)

# Bind the widget to the observable's name property
registry.register_observable(person.name, None, name_widget_id, "name")

# Or update an existing observable binding
registry.update_observable_widget(name_observable_id, name_widget_id)
registry.update_observable_property(name_observable_id, "name")
```

### Property Binding (New in this version)

To bind a widget to a property:

```python
# Register a property
property_id = registry.register_property("name", observable_id)

# Bind widget to property (optionally as controller)
registry.bind_widget(property_id, widget_id, is_controller=True)

# Unbind widget from property
registry.unbind_widget(property_id, widget_id)
```

### Core Registry Methods

```mermaid
classDiagram
    class IDRegistry {
        +register_widget(widget, type_code, widget_id, container_id, location)
        +get_widget(widget_id, container_id, location, type_code)
        +get_widget_id(widget, container_id, location, type_code)
        +update_widget(widget_id, container_id, location)
        +unregister_widget(widget_or_id)
        
        +register_observable(observable, observable_id, parent_id, container_id)
        +get_observable(observable_id, parent_id, property_id)
        +get_observable_id(observable, parent_id, property_name)
        +update_observable(observable_id, parent_id, container_id)
        +unregister_observable(observable_or_id)
        
        +register_property(property_name, observable_id, observable_property, widget_id)
        +get_property(property_id, observable_id, property_name, widget_id)
        +get_property_id(observable_id, property_name, observable_property)
        +bind_widget(property_id, widget_id, is_controller)
        +unbind_widget(property_id, widget_id)
        +update_property(property_id, widget_id)
        +unregister_property(property_id)
        
        +get_container(widget_id, container_id)
        +get_container_id(widget_id, container)
        
        +bind_widget_to_observable(widget_id, observable_id)
        +unbind_widget_from_observable(widget_id, observable_id)
        +get_bindings(widget_id, property_id, observable_id)
        
        +clear()
    }
```

## Usage Examples

### Widget Registration and Management

```python
# Get the registry
registry = get_id_registry()

# Register a widget (generate new ID)
widget_id = registry.register_widget(widget, "le")

# Register with existing ID or container reference
widget_id = registry.register_widget(widget, "pb", widget_id, container_id)

# Register with location
widget_id = registry.register_widget(widget, "pb", widget_id, container_id, "3")

# Get widget by ID
widget = registry.get_widget("pb:3a:2J:3")  
# OR with named parameter
widget = registry.get_widget(widget_id="pb:3a:2J:3")

# Get widgets by container ID
widgets = registry.get_widget(container_id="t:2J:0:1")
# Legacy method also supported
widgets = registry.get_widgets_by_container_id("t:2J:0:1")

# Get widget by location
widgets = registry.get_widget(container_id="t:2J:0:1", location="3")
# Legacy method also supported
widgets = registry.get_widgets_by_container_id_and_location("t:2J:0:1", "3")

# Get widgets by type
widgets = registry.get_widget(type_code="pb")

# Get ID for a widget
widget_id = registry.get_widget_id(widget)

# Get container from widget ID
container = registry.get_container_from_widget_id("pb:3a:2J:3")
# New method
container = registry.get_container(widget_id="pb:3a:2J:3")

# Get container's ID from widget ID
container_id = registry.get_container_id_from_widget_id("pb:3a:2J:3")
# New method
container_id = registry.get_container_id(widget_id="pb:3a:2J:3")

# Update a widget's container
registry.update_widget_container(widget_id, new_container_id)
# New method
registry.update_widget(widget_id, container_id=new_container_id)

# Update a widget's location
registry.update_widget_location(widget_id, "4")
# New method
registry.update_widget(widget_id, location="4")

# Unregister a widget
registry.unregister_widget(widget)  # or registry.unregister_widget(widget_id)
```

### Observable Registration and Management

```python
# Register an observable (generate new ID)
observable_id = registry.register_observable(person)

# Register with property name
observable_id = registry.register_observable(person.name, None, None, "name")

# Register with controlling widget
observable_id = registry.register_observable(person.name, None, widget_id, "name")

# Get observable by ID
observable = registry.get_observable("obs:5C:1Z:name")
# OR with named parameter
observable = registry.get_observable(observable_id="obs:5C:1Z:name")

# Get observables by parent widget
observables = registry.get_observable(parent_id=widget_id)

# Get observable for property
observable = registry.get_observable(property_id="obs:5C:1Z:name:name")

# Get ID for an observable
observable_id = registry.get_observable_id(observable)

# Get ID for observable with specific parent and property
observable_id = registry.get_observable_id(None, widget_id, "name")

# Get property name (legacy method)
property_name = registry.get_property_name("obs:5C:1Z:name")  # Returns "name"

# Get controlling widget (legacy method)
widget = registry.get_controlling_widget("obs:5C:1Z:name")
widget_id = registry.get_controlling_widget_id("obs:5C:1Z:name")

# Update an observable's controlling widget
registry.update_observable_widget(observable_id, new_widget_id)
# New method
registry.update_observable(observable_id, parent_id=new_widget_id)

# Update an observable's property name
registry.update_observable_property(observable_id, "new_property")

# Unregister an observable
registry.unregister_observable(observable)  # or registry.unregister_observable(observable_id)
```

### Property Registration and Management

```python
# Register a property
property_id = registry.register_property("name", observable_id)

# Register using property object
property_id = registry.register_property("name", None, person.name)

# Register and bind to widget in one step
property_id = registry.register_property("name", observable_id, None, widget_id)

# Get property by ID
property_info = registry.get_property(property_id="obs:5C:1Z:name:name")

# Get properties for observable
properties = registry.get_property(observable_id="obs:5C:1Z:name")

# Get property by name for specific observable
property_info = registry.get_property(observable_id="obs:5C:1Z:name", property_name="name")

# Get properties bound to widget
properties = registry.get_property(widget_id="pb:3a:2J:3")

# Get property ID
property_id = registry.get_property_id(observable_id, "name")

# Get property ID from property object
property_id = registry.get_property_id(None, None, person.name)

# Bind widget to property
registry.bind_widget(property_id, widget_id)

# Bind widget as controller
registry.bind_widget(property_id, widget_id, is_controller=True)

# Unbind widget from property
registry.unbind_widget(property_id, widget_id)

# Update property controller
registry.update_property(property_id, new_controller_widget_id)

# Unregister property
registry.unregister_property(property_id)
```

### Binding Widgets and Observables

```python
# Direct binding (without properties)
registry.bind_widget_to_observable(widget_id, observable_id)

# Unbind a widget from an observable
registry.unbind_widget_from_observable(widget_id, observable_id)

# Get all bindings for a widget
bindings = registry.get_bindings(widget_id="pb:3a:2J:3")

# Get all bindings for a property
bindings = registry.get_bindings(property_id="obs:5C:1Z:name:name")

# Get all bindings for an observable
bindings = registry.get_bindings(observable_id="obs:5C:1Z:name")

# Legacy methods for getting bound objects
observable_ids = registry.get_bound_observable_ids(widget_id)
observables = registry.get_bound_observables(widget_id)
widget_ids = registry.get_bound_widget_ids(observable_id)
widgets = registry.get_bound_widgets(observable_id)
```

### Utility Functions

```python
from command_system.id_system.utils import (
    extract_type_code, extract_unique_id, 
    extract_container_unique_id, extract_location,
    extract_widget_unique_id, extract_property_name,
    extract_observable_id_from_property_id, extract_widget_id_from_property_id,
    is_observable_id, is_widget_id, is_property_id,
    get_full_id, get_unique_id
)

# Check ID types
is_widget = is_widget_id("pb:3a:2J:3")  # -> True
is_obs = is_observable_id("obs:5C:1Z:name")  # -> True
is_prop = is_property_id("obs:5C:1Z:name:name")  # -> True

# Extract parts from a widget ID
type_code = extract_type_code("pb:3a:2J:3")  # -> "pb"
unique_id = extract_unique_id("pb:3a:2J:3")  # -> "3a"
container_id = extract_container_unique_id("pb:3a:2J:3")  # -> "2J"
location = extract_location("pb:3a:2J:3")  # -> "3"

# Extract parts from an observable ID
type_code = extract_type_code("obs:5C:1Z:name")  # -> "obs"
unique_id = extract_unique_id("obs:5C:1Z:name")  # -> "5C"
widget_id = extract_widget_unique_id("obs:5C:1Z:name")  # -> "1Z"
property_name = extract_property_name("obs:5C:1Z:name")  # -> "name"

# Extract parts from a property ID
observable_id = extract_observable_id_from_property_id("obs:5C:1Z:name:name")  # -> "obs:5C:1Z:name"
widget_id = extract_widget_id_from_property_id("obs:5C:1Z:name:name")  # Widget ID or None

# Build and extract IDs
full_id = get_full_id("3a", "widget", type_code="pb", container_unique_id="2J", location="3")
unique_id = get_unique_id("pb:3a:2J:3")  # -> "3a"
```

## Type Codes Reference

The system uses short type codes to identify different widget types:

| Widget Type | Code |
|-------------|------|
| **Observable** |  |
| Observable | obs |
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