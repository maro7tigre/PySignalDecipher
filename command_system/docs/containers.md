# Dynamic Container System Documentation

This document provides a comprehensive guide to the Dynamic Container Management System, explaining its architecture, usage patterns, and integration with the underlying command system.

## Overview

The Dynamic Container System provides a flexible framework for creating UI containers with built-in support for:

- Content type registration and dynamic instance creation
- Command pattern integration for undo/redo operations
- Container navigation and hierarchy management
- Widget lifecycle management

The system is designed to be memory-efficient and support complex UI layouts with nested containers.

## Core Architecture

```mermaid
flowchart TD
    subgraph "Container System"
        BaseCommandContainer["BaseCommandContainer"] --> CommandTabWidget["CommandTabWidget"]
        BaseCommandContainer --> CommandDockWidget["CommandDockWidget"]
        
        subgraph "Core Components"
            TypeRegistry["Content Type Registry"]
            InstanceMgmt["Instance Management"]
            IDSystem["ID System"]
            ContainerNav["Container Navigation"]
        end
        
        BaseCommandContainer --- TypeRegistry
        BaseCommandContainer --- InstanceMgmt
        BaseCommandContainer --- IDSystem
        BaseCommandContainer --- ContainerNav
    end
    
    subgraph "Command System"
        CommandManager --> CommandHistory
        CommandManager --> PropertyCommand
        PropertyCommand --> TriggerWidget
    end
    
    TriggerWidget --> ContainerNav
    
    style BaseCommandContainer stroke:#9370db,stroke-width:2px
    style CommandTabWidget stroke:#9370db,stroke-width:1px
    style CommandDockWidget stroke:#9370db,stroke-width:1px
    style CommandManager stroke:#4682b4,stroke-width:1px
    style CommandHistory stroke:#4682b4,stroke-width:1px
    style PropertyCommand stroke:#4682b4,stroke-width:1px
    style TriggerWidget stroke:#cd853f,stroke-width:1px
    style TypeRegistry stroke:#228b22,stroke-width:1px
    style InstanceMgmt stroke:#228b22,stroke-width:1px
    style IDSystem stroke:#228b22,stroke-width:1px
    style ContainerNav stroke:#228b22,stroke-width:1px
```

## Key Components

### BaseCommandContainer

The `BaseCommandContainer` class serves as the foundation for all container implementations. It provides:

- Widget type registration
- Factory-based content creation
- Child widget management
- Container navigation

#### Key Methods

| Method | Description |
|--------|-------------|
| `initiate_container(type_code, container_id, location)` | Initialize the container with type code and optional parent |
| `register_widget_type(factory_func, observables, type_id, **options)` | Register a widget factory function with optional observables |
| `add_widget(type_id, location)` | Create and add a widget of the registered type |
| `register_child(widget, location)` | Register a child widget with this container |
| `unregister_child(widget)` | Unregister a child widget from this container |
| `get_child_widgets()` | Get all child widgets of this container |
| `get_widgets_at_location(location)` | Get all widgets at a specific location |
| `navigate_to_container(trigger_widget, container_info)` | Navigate to this container's context |

### CommandTabWidget

The `CommandTabWidget` class extends `BaseCommandContainer` to provide a tab-based container implementation with undo/redo support. It seamlessly integrates with the command system.

#### Key Methods

| Method | Description |
|--------|-------------|
| `register_tab(factory_func, tab_name, observables, closable)` | Register a tab type with factory function |
| `add_tab(type_id)` | Add a new tab of the registered type |
| `set_tab_closable(index, closable)` | Set whether a specific tab should be closable |
| `addTab(widget, label)` | Override to register the widget with this container |
| `insertTab(index, widget, label)` | Override to register the widget and update locations |
| `removeTab(index)` | Override to unregister the widget and update locations |

## Container Registration Flow

```mermaid
sequenceDiagram
    participant User as User Code
    participant Container as CommandTabWidget
    participant Factory as Factory Functions
    participant Registry as Type Registry
    
    User->>Container: register_tab(factory_func, "Tab Name", closable=true)
    Container->>Registry: Generate type_id if not provided
    Container->>Registry: Store factory and metadata
    Registry-->>Container: Return type_id
    Container-->>User: Return type_id for future reference
    
    Note over User,Registry: Registration is done once during initialization
    
    User->>Container: register_tab(another_factory, "Another Tab")
    Container->>Registry: Store another factory
    Registry-->>Container: Return another type_id
    Container-->>User: Return type_id
```

## Content Instance Creation Flow

```mermaid
sequenceDiagram
    participant User as User Code
    participant Container as CommandTabWidget
    participant Factory as Factory Function
    participant Registry as Type Registry
    participant Widget as Content Widget
    
    User->>Container: add_tab(type_id)
    Container->>Registry: Look up factory function
    Registry-->>Container: Return factory function + metadata
    Container->>Factory: Call factory function
    Factory-->>Container: Return created widget
    Container->>Container: Register widget with ID system
    Container->>Container: Add widget to container at location
    Container-->>User: Return widget_id
```

## Navigation During Undo/Redo

```mermaid
sequenceDiagram
    participant User as User Code
    participant CmdMgr as CommandManager
    participant Command as Command
    participant Widget as TriggerWidget
    participant Container as CommandTabWidget
    
    User->>CmdMgr: undo()
    CmdMgr->>Command: Get trigger_widget
    Command-->>CmdMgr: Return widget reference
    CmdMgr->>Widget: Get container
    Widget-->>CmdMgr: Return container reference
    CmdMgr->>Container: navigate_to_container(widget)
    Container->>Container: Make visible if needed
    
    alt Tab Container
        Container->>Container: Find tab containing widget
        Container->>Container: setCurrentIndex(tab_index)
    else Dock Container
        Container->>Container: setVisible(true)
        Container->>Container: raise()
    end
    
    Container->>Widget: setFocus()
    CmdMgr->>Command: undo()
    Command->>Command: Restore previous state
```

## Nested Container Hierarchy

```mermaid
flowchart TD
    MainWindow --> MainTabs["Main Tab Widget"]
    MainWindow --> PropertyDock["Property Dock Widget"]
    
    MainTabs --> Tab1["Tab 1"]
    MainTabs --> Tab2["Tab 2"]
    MainTabs --> Tab3["Tab 3"]
    
    Tab2 --> NestedTabs["Nested Tab Widget"]
    
    NestedTabs --> SubTab1["Sub Tab 1"]
    NestedTabs --> SubTab2["Sub Tab 2"]
    
    PropertyDock --> PropsWidget["Properties Widget"]
    
    %% Container references
    SubTab1 -.->|container| NestedTabs
    SubTab2 -.->|container| NestedTabs
    NestedTabs -.->|container| Tab2
    Tab1 -.->|container| MainTabs
    Tab2 -.->|container| MainTabs
    Tab3 -.->|container| MainTabs
    PropsWidget -.->|container| PropertyDock
    
    style MainTabs stroke:#9370db,stroke-width:2px
    style PropertyDock stroke:#9370db,stroke-width:2px
    style NestedTabs stroke:#9370db,stroke-width:2px
    style Tab1 stroke:#cd853f,stroke-width:1px
    style Tab2 stroke:#cd853f,stroke-width:1px
    style Tab3 stroke:#cd853f,stroke-width:1px
    style SubTab1 stroke:#cd853f,stroke-width:1px
    style SubTab2 stroke:#cd853f,stroke-width:1px
    style PropsWidget stroke:#cd853f,stroke-width:1px
```

## User Guide

### Basic Container Setup

To create a tab container:

```python
from command_system.pyside6_widgets.containers import CommandTabWidget

# Create the tab container
main_tabs = CommandTabWidget(parent)

# Add it to your main layout
layout.addWidget(main_tabs)
```

### Registering Content Types

Register content factories once during initialization:

```python
def create_personal_info_tab(person_model):
    """Factory function to create a person info tab."""
    form = QWidget()
    layout = QFormLayout(form)
    
    name_edit = CommandLineEdit()
    name_edit.bind_to_text_property(person_model.get_id(), "name")
    
    age_spin = CommandSpinBox()
    age_spin.bind_to_value_property(person_model.get_id(), "age")
    
    layout.addRow("Name:", name_edit)
    layout.addRow("Age:", age_spin)
    
    return form

# Register the tab type
person_tab_type = main_tabs.register_tab(
    create_personal_info_tab,
    tab_name="Personal Info",
    observables=[Person],  # Will create a new Person instance
    closable=True
)
```

### Creating Content Instances

Create instances dynamically at runtime:

```python
# Add a new tab instance
tab_id = main_tabs.add_tab(person_tab_type)
```

This will:
1. Look up the factory function
2. Create a new Person instance
3. Call the factory with the instance
4. Add the resulting widget as a tab
5. Return the widget ID for reference

### Working with Observables

You can also use existing observable instances:

```python
# Create a person model
person = Person(name="John Doe", age=30)
person_id = person.get_id()

# Register a tab type that uses the existing model
details_tab_type = main_tabs.register_tab(
    create_personal_details_tab,
    tab_name="Details",
    observables=[person_id],  # Use existing observable
    closable=True
)

# Add a tab that will show the person details
main_tabs.add_tab(details_tab_type)
```

### Undo/Redo Support

All container operations automatically integrate with the command system:

```python
# Get command manager
manager = get_command_manager()

# Undo the last operation (e.g., tab addition)
if manager.can_undo():
    manager.undo()

# Redo the operation
if manager.can_redo():
    manager.redo()
```

### Nested Containers

Containers can be nested for complex layouts:

```python
# Create a nested tab container
nested_tabs = CommandTabWidget(parent=None)

# Register content for the nested container
nested_tab_type = nested_tabs.register_tab(create_nested_content)

# Add the nested container to a parent tab
main_tab_content = QWidget()
layout = QVBoxLayout(main_tab_content)
layout.addWidget(nested_tabs)

# Add the parent tab
main_tabs.addTab(main_tab_content, "Parent Tab")
```

## Widget Registration and Container References

```mermaid
flowchart TD
    Container["Container Widget"] --> AddContent["Add Content Widget"]
    AddContent --> RegisterContents["register_child(widget, location)"]
    
    RegisterContents --> IDRegistry["ID Registry"]
    
    IDRegistry --> SetContainer["Set container and location in ID"]
    
    SetContainer --> CommandWidgetRef["Container ID stored in widget ID"]
    CommandWidgetRef --> CommandCreation["Command Creation:\ntrigger_widget = widget"]
    CommandCreation --> UndoRedo["Used during Undo/Redo\nfor navigation"]
    
    style Container stroke:#9370db,stroke-width:2px
    style AddContent stroke:#9370db,stroke-width:1px
    style RegisterContents stroke:#9370db,stroke-width:1px
    style IDRegistry stroke:#228b22,stroke-width:1px
    style SetContainer stroke:#228b22,stroke-width:1px
    style CommandWidgetRef stroke:#cd853f,stroke-width:1px
    style CommandCreation stroke:#4682b4,stroke-width:1px
    style UndoRedo stroke:#4682b4,stroke-width:1px
```

## Factory Pattern Implementation

```mermaid
flowchart TD
    subgraph "Factory Pattern"
        direction LR
        FactoryFunc["Factory Function \ncreate_personal_tab(person)"]
        
        subgraph "Parameters"
            Person["person: Person object"]
            Options["other parameters"]
        end
        
        subgraph "Created Widget"
            TabWidget["Tab Widget"]
            Form["Form Layout"]
            NameField["Name Field"]
            EmailField["Email Field"]
        end
        
        FactoryFunc --> TabWidget
        Person --> FactoryFunc
        Options --> FactoryFunc
        
        TabWidget --> Form
        Form --> NameField
        Form --> EmailField
        
        NameField -.->|bind_to_model| Person
        EmailField -.->|bind_to_model| Person
    end
    
    Register["register_tab(factory_func)"] --> FactoryFunc
    Add["add_tab(type_id)"] --> FactoryFunc
    
    style FactoryFunc stroke:#ff7f50,stroke-width:2px
    style TabWidget stroke:#cd853f,stroke-width:1px
    style Person stroke:#228b22,stroke-width:1px
    style Options stroke:#228b22,stroke-width:1px
    style NameField stroke:#cd853f,stroke-width:1px
    style EmailField stroke:#cd853f,stroke-width:1px
    style Register stroke:#9370db,stroke-width:1px
    style Add stroke:#9370db,stroke-width:1px
```

## Best Practices

1. **Register Types Once**: Register all content types during initialization, not during runtime
2. **Use Factory Functions**: Create dedicated factory functions for content creation
3. **Bind to Observable Models**: Use the observable pattern for data binding
4. **Leverage Automatic Undo/Redo**: Let the system handle command creation
5. **Use Type IDs**: Store type IDs for reuse, not factory functions
6. **Nest Containers**: Create complex layouts by nesting containers
7. **Close with Commands**: Use commands for closing tabs to enable undo

## Complete Flow Example

```mermaid
sequenceDiagram
    participant App as Application
    participant Tab as CommandTabWidget
    participant Factory as Factory Function
    participant CmdWidget as Command Widget
    participant Cmd as Command System
    
    Note over App,Cmd: Initialization Phase
    App->>Tab: new CommandTabWidget(parent)
    App->>Tab: register_tab(create_personal_tab, "Personal", observables=[Person])
    
    Note over App,Cmd: Content Creation Phase
    App->>Tab: add_tab("personal_tab_type")
    Tab->>Factory: create_personal_tab(person=new_person)
    Factory-->>Tab: Return tab widget with form
    Tab->>Tab: addTab(tab_widget, "Personal")
    Tab->>Tab: register_child(tab_widget, "0")
    
    Note over App,Cmd: User Interaction Phase
    CmdWidget->>CmdWidget: User edits field value
    CmdWidget->>Cmd: _create_property_command()
    CmdWidget->>Cmd: Command.trigger_widget = self
    Cmd->>Cmd: execute(command)
    
    Note over App,Cmd: Undo Operation Phase
    App->>Cmd: undo()
    Cmd->>CmdWidget: Get trigger_widget
    Cmd->>Tab: trigger_widget.container.navigate_to_container()
    Tab->>Tab: setCurrentIndex(tab_index)
    Tab->>CmdWidget: setFocus()
    Cmd->>Cmd: command.undo()
```

## Advanced Features

### Tab Closability Control

Control whether specific tabs can be closed:

```python
# Make a tab unclosable
main_tabs.set_tab_closable(1, False)
```

### Container Navigation

Navigate programmatically to containers:

```python
# Navigate to a specific container
container.navigate_to_container()
```

### Content Recreation

The system stores creation information to enable undo/redo of tab closures:

```python
# Container tracking allows proper recreation
recreation_info = {
    "type_id": type_id,
    "created_observables": [...],
    "observable_ids": [...]
}
```

## Conclusion

The Dynamic Container System provides a powerful framework for building complex UIs with built-in undo/redo support. By leveraging the factory pattern, observable pattern, and command pattern, it enables clean separation of concerns and excellent user experience.

For more details on the underlying command system and ID system, refer to their respective documentation.