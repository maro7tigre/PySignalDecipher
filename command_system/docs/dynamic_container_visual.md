# Dynamic Container System Visualization

This document provides visual explanations of the Dynamic Container Management System using Mermaid diagrams.

## Core Architecture

```mermaid
flowchart TD
    subgraph "Container System"
        ContainerMixin["ContainerWidgetMixin"] --> TabWidget["CommandTabWidget"]
        ContainerMixin --> DockWidget["CommandDockWidget"]
        
        subgraph "Core Components"
            TypeRegistry["Content Type Registry"]
            InstanceMgmt["Instance Management"]
            IDGen["ID Generation"]
            ContainerNav["Container Navigation"]
        end
        
        ContainerMixin --- TypeRegistry
        ContainerMixin --- InstanceMgmt
        ContainerMixin --- IDGen
        ContainerMixin --- ContainerNav
    end
    
    subgraph "Command System"
        CommandManager --> CommandHistory
        CommandManager --> PropertyCommand
        PropertyCommand --> TriggerWidget
    end
    
    TriggerWidget --> ContainerNav
    
    style ContainerMixin stroke:#9370db,stroke-width:2px
    style TabWidget stroke:#9370db,stroke-width:1px
    style DockWidget stroke:#9370db,stroke-width:1px
    style CommandManager stroke:#4682b4,stroke-width:1px
    style CommandHistory stroke:#4682b4,stroke-width:1px
    style PropertyCommand stroke:#4682b4,stroke-width:1px
    style TriggerWidget stroke:#cd853f,stroke-width:1px
    style TypeRegistry stroke:#228b22,stroke-width:1px
    style InstanceMgmt stroke:#228b22,stroke-width:1px
    style IDGen stroke:#228b22,stroke-width:1px
    style ContainerNav stroke:#228b22,stroke-width:1px
```

## Object Structure and Relationships

```mermaid
classDiagram
    class ContainerWidgetMixin {
        container
        container_info
        _container_id
        _content_types
        _content_instances
        +register_content_type()
        +add()
        +close()
        +register_contents()
        +navigate_to_container()
    }
    
    class CommandTabWidget {
        _tab_instance_map
        +register_tab()
        +add_tab()
        +close_tab()
        +activate_child()
        +_add_content_to_container()
        +_close_content()
    }
    
    class CommandDockWidget {
        _active_instance_id
        +register_dock()
        +add_dock()
        +close_dock()
        +activate_child()
        +_add_content_to_container()
        +_close_content()
    }
    
    class CommandWidgetBase {
        container
        container_info
        +bind_to_model()
        +_create_property_command()
    }
    
    class Command {
        trigger_widget
        +execute()
        +undo()
        +redo()
    }
    
    class CommandManager {
        +execute()
        +undo()
        +redo()
        -_navigate_to_command_context()
    }
    
    ContainerWidgetMixin <|-- CommandTabWidget
    ContainerWidgetMixin <|-- CommandDockWidget
    
    CommandWidgetBase -- ContainerWidgetMixin: references >
    Command -- CommandWidgetBase: references >
    CommandManager -- Command: executes >
```

## Content Type Registration Flow

```mermaid
sequenceDiagram
    participant User as User Code
    participant Container as ContainerWidget
    participant Factory as Factory Functions
    participant Registry as Content Type Registry
    
    User->>Container: register_tab(factory_func, "Tab Name", dynamic=true)
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
    participant Container as ContainerWidget
    participant Factory as Factory Functions
    participant Registry as Content Type Registry
    participant Widget as Content Widget
    
    User->>Container: add_tab(type_id, params={...})
    Container->>Registry: Look up factory function
    Registry-->>Container: Return factory function + metadata
    Container->>Factory: Call factory with params
    Factory-->>Container: Return created widget
    Container->>Container: Generate instance_id
    Container->>Container: Store instance details
    Container->>Container: _add_content_to_container()
    Container->>Widget: Register widget with container
    Container-->>User: Return instance_id
```

## Navigation During Undo/Redo

```mermaid
sequenceDiagram
    participant User as User Code
    participant CmdMgr as CommandManager
    participant Command as Command
    participant Widget as TriggerWidget
    participant Container as ContainerWidget
    
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

## Dynamic Content Creation and Management

```mermaid
flowchart LR
    subgraph Registration["Content Registration (Done once)"]
        direction TB
        Register["register_tab()"] --> TypesDict["_content_types Dictionary"]
        TypesDict --> TypeID1["type_id_1: \n{ factory, \ndisplay_name, \noptions }"]
        TypesDict --> TypeID2["type_id_2: \n{ factory, \ndisplay_name, \noptions }"]
    end
    
    subgraph Creation["Content Creation (Multiple times)"]
        direction TB
        AddInstance["add_tab(type_id)"] --> FactoryCall["Call Factory Function"]
        FactoryCall --> Widget["Content Widget"]
        Widget --> InstancesDict["_content_instances Dictionary"]
        InstancesDict --> Instance1["instance_id_1: \n{ widget, \ntype_id, \nparams }"]
        InstancesDict --> Instance2["instance_id_2: \n{ widget, \ntype_id, \nparams }"]
    end
    
    subgraph Container["Container Widget"]
        direction TB
        TabsMap["_tab_instance_map Dictionary"] --> MapEntry1["0: instance_id_1"]
        TabsMap --> MapEntry2["1: instance_id_2"]
        MapEntry1 --> TabWidget1["Tab Widget at index 0"]
        MapEntry2 --> TabWidget2["Tab Widget at index 1"]
    end
    
    Registration --> Creation
    Creation --> Container
    
    style Register stroke:#9370db,stroke-width:2px
    style TypesDict stroke:#228b22,stroke-width:2px
    style TypeID1 stroke:#228b22,stroke-width:1px
    style TypeID2 stroke:#228b22,stroke-width:1px
    style AddInstance stroke:#9370db,stroke-width:2px
    style FactoryCall stroke:#ff7f50,stroke-width:2px
    style Widget stroke:#cd853f,stroke-width:2px
    style InstancesDict stroke:#228b22,stroke-width:2px
    style Instance1 stroke:#228b22,stroke-width:1px
    style Instance2 stroke:#228b22,stroke-width:1px
    style TabsMap stroke:#9370db,stroke-width:2px
    style MapEntry1 stroke:#9370db,stroke-width:1px
    style MapEntry2 stroke:#9370db,stroke-width:1px
    style TabWidget1 stroke:#cd853f,stroke-width:1px
    style TabWidget2 stroke:#cd853f,stroke-width:1px
```

## Complete System Flow Example

```mermaid
sequenceDiagram
    participant App as Application
    participant Tab as TabWidget
    participant Factory as Factory Function
    participant CmdWidget as Command Widget
    participant Cmd as Command System
    
    Note over App,Cmd: Initialization Phase
    App->>Tab: new CommandTabWidget(parent, "main_tabs")
    App->>Tab: register_tab(create_personal_tab, "Personal", dynamic=true)
    
    Note over App,Cmd: Content Creation Phase
    App->>Tab: add_tab("personal", person=person_data)
    Tab->>Factory: create_personal_tab(person=person_data)
    Factory-->>Tab: Return tab widget with form
    Tab->>Tab: addTab(tab_widget, "Personal")
    Tab->>Tab: register_contents(tab_widget)
    
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

## Content Closure Flow

```mermaid
sequenceDiagram
    participant User as User Code
    participant Container as ContainerWidget
    participant Registry as Instance Registry
    
    alt Programmatic Closure
        User->>Container: close_tab(instance_id)
        Container->>Container: _close_content(widget, instance_id)
        Container->>Registry: Remove from _content_instances
    else UI-Triggered Closure
        User->>Container: Click tab close button
        Container->>Container: _on_tab_close_requested(index)
        Container->>Container: Get instance_id from _tab_instance_map
        Container->>Container: _close_content(widget, instance_id)
        Container->>Registry: Remove from _content_instances
    end
    
    Container->>Container: Update container-specific state
    Container->>Container: Emit contentClosed signal
    Container-->>User: Return success/failure
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
    Add["add_tab(type_id, person=person_obj)"] --> FactoryFunc
    
    style FactoryFunc stroke:#ff7f50,stroke-width:2px
    style TabWidget stroke:#cd853f,stroke-width:1px
    style Person stroke:#228b22,stroke-width:1px
    style Options stroke:#228b22,stroke-width:1px
    style NameField stroke:#cd853f,stroke-width:1px
    style EmailField stroke:#cd853f,stroke-width:1px
    style Register stroke:#9370db,stroke-width:1px
    style Add stroke:#9370db,stroke-width:1px
```

## Widget Registration and Container References

```mermaid
flowchart TD
    Container["Container Widget"] --> AddContent["Add Content Widget"]
    AddContent --> RegisterContents["register_contents(widget)"]
    
    RegisterContents --> ProcessWidgets["Process all children recursively"]
    
    ProcessWidgets --> SetContainer["Set container reference\nwidget.container = container\nwidget.container_info = info"]
    
    SetContainer --> CommandWidgetRef["CommandWidget container references set"]
    
    CommandWidgetRef --> CommandCreation["Command Creation:\ntrigger_widget = widget"]
    CommandCreation --> UndoRedo["Used during Undo/Redo\nfor navigation"]
    
    style Container stroke:#9370db,stroke-width:2px
    style AddContent stroke:#9370db,stroke-width:1px
    style RegisterContents stroke:#9370db,stroke-width:1px
    style ProcessWidgets stroke:#9370db,stroke-width:1px
    style SetContainer stroke:#9370db,stroke-width:1px
    style CommandWidgetRef stroke:#cd853f,stroke-width:1px
    style CommandCreation stroke:#4682b4,stroke-width:1px
    style UndoRedo stroke:#4682b4,stroke-width:1px
```