# Command System Serialization Architecture

This document outlines the design for a serialization system that integrates with the existing command system. The approach combines ID-based serialization with component hooks and a centralized registry.

## Core Design Principles

1. **Flexible Granularity**: Support serialization at different levels (individual components, containers, or the entire application)
2. **ID Preservation**: Maintain component identities during serialization/deserialization
3. **Relationship Integrity**: Properly restore all relationships between components
4. **Integration with Commands**: Support command-based operations for serialized states
5. **Extensibility**: Allow for custom serialization needs

## Architecture Overview

```mermaid
flowchart TB
    SM[Serialization Manager] --> SR[Serialization Registry]
    SM --> SO[Serialization Operations]
    SR --> CP[Component Protocols]
    SR --> FG[Factory Registry]

    SO --> RS[Restore State]   
    SO --> SS[Save State]
    SO --> CS[Command Serialization]
    
    subgraph Components
        WS[Widget Serialization]
        OS[Observable Serialization]
        RS[Relationship Serialization]
        CHS[Custom Hooks]
    end
    
    CP --> Components
    
    style SM stroke:#4682b4,stroke-width:2px
    style SR stroke:#228b22,stroke-width:2px
    style FG stroke:#228b22,stroke-width:2px
    style SO stroke:#cd853f,stroke-width:1px
    style CP stroke:#9370db,stroke-width:1px
    style WS stroke:#228b22,stroke-width:1px
    style OS stroke:#228b22,stroke-width:1px
    style RS stroke:#228b22,stroke-width:1px
    style CHS stroke:#228b22,stroke-width:1px
    style SS stroke:#4682b4,stroke-width:1px
    style RS stroke:#4682b4,stroke-width:1px
    style CS stroke:#4682b4,stroke-width:1px
```

## Serialization Data Structure

The serialization system organizes data into distinct categories:

```mermaid
flowchart TD
    SS[Serialized State] --> WC[Widgets/Containers]
    SS --> OB[Observables]
    SS --> RL[Relationships]
    SS --> CD[Custom Data]
    
    style SS stroke:#4682b4,stroke-width:2px
    style WC stroke:#9370db,stroke-width:1px
    style OB stroke:#9370db,stroke-width:1px
    style RL stroke:#9370db,stroke-width:1px
    style CD stroke:#9370db,stroke-width:1px
```

### Widget/Container Tree Structure

Widgets and containers are organized in a tree structure:

```mermaid
flowchart TD
    subgraph "Widget/Container Tree"
        R[Root Container: ID + Type ID + Layout]
        C1[Container: ID + Type ID + Layout]
        C2[Container: ID + Type ID + Layout]
        C3[Widget: ID + Type ID + Layout]
        W1[Widget: ID]
        W2[Widget: ID]
        W3[Widget: ID]
        W4[Widget: ID]
        W5[Widget: ID]
        
        R --> C1
        R --> C2
        C1 --> C3
        C1 --> W1
        C1 --> W2
        C2 --> W3
        C2 --> W4
        C3 --> W5
    end
    
    style R stroke:#4682b4,stroke-width:3px
    style C1 stroke:#9370db,stroke-width:2px
    style C2 stroke:#9370db,stroke-width:2px
    style C3 stroke:#9370db,stroke-width:2px
    style W1 stroke:#cd853f,stroke-width:1px
    style W2 stroke:#cd853f,stroke-width:1px
    style W3 stroke:#cd853f,stroke-width:1px
    style W4 stroke:#cd853f,stroke-width:1px
    style W5 stroke:#cd853f,stroke-width:1px
```

### Observable Structure

Observables are serialized as flat lists with their properties:

```mermaid
flowchart TD
    subgraph "Observable List"
        O1[Observable: ID]
        O2[Observable: ID]
        
        P1[Property: ID + Value]
        P2[Property: ID + Value]
        P3[Property: ID + Value]
        P4[Property: ID + Value]
        
        O1 --> P1
        O1 --> P2
        O2 --> P3
        O2 --> P4
    end
    
    style O1 stroke:#4682b4,stroke-width:2px
    style O2 stroke:#4682b4,stroke-width:2px
    style P1 stroke:#228b22,stroke-width:1px
    style P2 stroke:#228b22,stroke-width:1px
    style P3 stroke:#228b22,stroke-width:1px
    style P4 stroke:#228b22,stroke-width:1px
```

### Relationship Structure

Relationships between components are stored separately:

```mermaid
flowchart TD
    subgraph "Relationships"
        CL[Controllers]
        OB[Observers]
        
        CL1[Property ID → Widget ID + Property]
        CL2[Property ID → Widget ID + Property]
        
        OB1[Property ID → Observer ID + Callback]
        OB2[Property ID → Observer ID + Callback]
        
        CL --> CL1
        CL --> CL2
        OB --> OB1
        OB --> OB2
    end
    
    style CL stroke:#4682b4,stroke-width:2px
    style OB stroke:#4682b4,stroke-width:2px
    style CL1 stroke:#cd853f,stroke-width:1px
    style CL2 stroke:#cd853f,stroke-width:1px
    style OB1 stroke:#cd853f,stroke-width:1px
    style OB2 stroke:#cd853f,stroke-width:1px
```

## Serialization and Deserialization Process

### Serialization Process

```mermaid
sequenceDiagram
    participant Client
    participant SM as SerializationManager
    participant IDReg as IDRegistry
    participant Component
    
    Client->>SM: serialize_component(component)
    SM->>IDReg: get_id(component)
    IDReg-->>SM: component_id
    SM->>Component: get_serialization_data()
    Component-->>SM: component_data
    SM->>SM: process_relationships()
    SM-->>Client: serialized_state
```

### Deserialization Process (Two-Phase)

```mermaid
sequenceDiagram
    participant Client
    participant SM as SerializationManager
    participant FR as FactoryRegistry
    participant IDReg as IDRegistry
    
    Client->>SM: deserialize_state(state)
    
    Note over SM: Phase 1 - Object Creation
    SM->>FR: create_components(component_data)
    FR->>IDReg: register(component, id)
    IDReg-->>FR: registered_component
    FR-->>SM: created_components
    
    Note over SM: Phase 2 - Relationship Restoration
    SM->>SM: restore_relationships(created_components, relationship_data)
    SM-->>Client: restored_state
```

## Component Types and Their Serialization

### 1. Widgets and Containers

Widgets and containers are serialized in a tree structure that preserves the hierarchy:

```json
{
  "id": "t:1A:0:0",
  "type_code": "t",
  "type_id": "tab_container",
  "layout": { "width": 800, "height": 600 },
  "children": [
    {
      "id": "pb:2B:1A:0",
      "type_code": "pb",
      "type_id": "button_type_1",
      "layout": { "x": 10, "y": 10, "width": 100, "height": 30 },
      "children": []
    },
    {
      "id": "x:3C:1A:1",
      "type_code": "x",
      "type_id": "panel_container",
      "layout": { "x": 120, "y": 10, "width": 200, "height": 200 },
      "children": [
        {
          "id": "le:4D:3C:0",
          "type_code": "le",
          "type_id": "line_edit_type_1",
          "layout": { "x": 10, "y": 10, "width": 180, "height": 30 },
          "children": []
        }
      ]
    }
  ]
}
```

Note that:
- Containers have both a `type_code`, `type_id`, and `children` array
- Leaf widgets have a `type_code`, `type_id`, and empty `children` array
- All nodes have `id` and `layout` information

### 2. Observables and Properties

Observables and their properties are serialized as flat lists:

```json
{
  "observables": [
    {
      "id": "o:4D",
      "properties": {
        "name": { "id": "op:5E:4D:name:0", "value": "John Doe" },
        "age": { "id": "op:6F:4D:age:3C", "value": 30 }
      }
    }
  ]
}
```

### 3. Relationships

Relationships are stored as maps of property IDs to their controllers and observers:

```json
{
  "controllers": {
    "op:6F:4D:age:3C": { "widget_id": "le:3C:1A:1", "widget_property": "text" }
  },
  "observers": {
    "op:5E:4D:name:0": [
      { "observer_id": "pb:2B:1A:0", "callback": "on_name_changed" }
    ]
  }
}
```

## Key Components

### SerializationManager

The central coordinator for serialization operations:

```mermaid
classDiagram
    class SerializationManager {
        -instance: SerializationManager
        -registry: SerializationRegistry
        +get_instance(): SerializationManager
        +serialize_component(component): dict
        +serialize_container(container): dict
        +serialize_application(): dict
        +deserialize_component(data): Object
        +deserialize_container(data): Container
        +deserialize_application(data): void
    }
    
    style SerializationManager stroke:#4682b4,stroke-width:2px
```

### SerializationRegistry

Maintains registrations for component types and their factory functions:

```mermaid
classDiagram
    class SerializationRegistry {
        -factories: Dict[str, FactoryFunction]
        -serializers: Dict[str, SerializerFunction]
        -deserializers: Dict[str, DeserializerFunction]
        +register_factory(type_id, factory_func): void
        +register_serializer(type_id, serializer_func): void 
        +register_deserializer(type_id, deserializer_func): void
        +get_factory(type_id): FactoryFunction
        +get_serializer(type_id): SerializerFunction 
        +get_deserializer(type_id): DeserializerFunction
    }
    
    style SerializationRegistry stroke:#228b22,stroke-width:2px
```

### Serializable Protocol

Components can implement this protocol to control their serialization:

```python
class Serializable:
    def get_serialization_data(self) -> dict:
        """Return data to be serialized for this component."""
        pass
        
    @classmethod
    def from_serialization_data(cls, data: dict) -> 'Serializable':
        """Create a new instance from serialized data."""
        pass
    
    def restore_relationships(self, serialized_state: dict) -> None:
        """Restore relationships after all objects are created."""
        pass
```

## Command Integration

### SerializedStateCommand

A command that encapsulates state changes through serialization:

```mermaid
classDiagram
    class Command {
        +execute(): void
        +undo(): void
        +redo(): void
    }
    
    class SerializedStateCommand {
        -component_id: str
        -old_state: dict
        -new_state: dict
        -serialization_manager: SerializationManager
        +execute(): void
        +undo(): void
    }
    
    Command <|-- SerializedStateCommand
    
    style Command stroke:#4682b4,stroke-width:2px
    style SerializedStateCommand stroke:#cd853f,stroke-width:1px
```

This command would store the serialized state before and after an operation, allowing complete state restoration during undo/redo operations.

## Implementation Strategy

### Phase 1: Core Infrastructure

1. Implement `SerializationManager` and `SerializationRegistry`
2. Define basic serialization formats for each component type
3. Create the `Serializable` protocol

### Phase 2: Widget and Observable Serialization

1. Implement widget tree serialization
2. Implement observable list serialization
3. Add factory registration for standard components

### Phase 3: Relationship Restoration

1. Implement the two-phase deserialization process
2. Add relationship mapping serialization
3. Create logic to rebind properties and observers

### Phase 4: Command Integration

1. Create the `SerializedStateCommand` class
2. Update container operations to use serialized commands
3. Add support for partial serialization in existing commands

## Usage Examples

### Saving a Container State

```python
def save_container_state(container, filename):
    """Save a container's state to a file."""
    serialization_manager = get_serialization_manager()
    state = serialization_manager.serialize_container(container)
    with open(filename, 'w') as f:
        json.dump(state, f, indent=2)
```

### Restoring a Container State

```python
def load_container_state(parent, filename):
    """Load a container's state from a file."""
    with open(filename, 'r') as f:
        state = json.load(f)
    serialization_manager = get_serialization_manager()
    container = serialization_manager.deserialize_container(state, parent)
    return container
```

### Creating a Serialized Command for Container Operations

```python
def create_add_tab_command(tab_widget, tab_type_id):
    """Create a command to add a tab with serialization for undo/redo."""
    # Capture the container state before change
    serialization_manager = get_serialization_manager()
    old_state = serialization_manager.serialize_container(tab_widget)
    
    # Create the tab (directly, not as a command)
    tab_widget.add_widget(tab_type_id, str(tab_widget.count()))
    
    # Capture the container state after change
    new_state = serialization_manager.serialize_container(tab_widget)
    
    # Create a serialized state command
    return SerializedStateCommand(tab_widget.widget_id, old_state, new_state)
```

## Benefits of this Approach

1. **Hierarchical Serialization**: Components can be serialized individually or as part of a larger structure
2. **ID Preservation**: Components maintain their identities across serialization/deserialization
3. **Component-Level Integration**: Each component can control its serialization process
4. **Command System Integration**: Serialized states can be used for command operations
5. **Extensibility**: New component types can be added without changing the core system

## Next Steps

1. Implement the core serialization manager and registry
2. Add serialization support to the existing widget containers
3. Extend the observable system to support serialization
4. Integrate with the command system for undo/redo operations
5. Add serialization-aware commands for container operations

## Conclusion

This serialization architecture provides a flexible, extensible system that integrates seamlessly with the existing command system. It preserves the identity and relationships of components while supporting operations at various levels of granularity, from individual elements to entire application states.

The design balances simplicity with power, leveraging the existing ID system while adding the necessary hooks for component-specific serialization needs.