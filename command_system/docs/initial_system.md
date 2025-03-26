```mermaid
classDiagram
    class Observable {
        -_property_observers: Dict
        -_id: str
        -_is_updating: bool
        -_parent_id: Optional[str]
        -_generation: int
        +add_property_observer()
        +remove_property_observer()
        +_notify_property_changed()
        +get_id()
        +set_id()
    }
    
    class ObservableProperty {
        -default: T
        -name: str
        -private_name: str
        +__get__()
        +__set__()
    }

    class Command {
        <<abstract>>
        -_execution_context: Dict
        +execute()* 
        +undo()*
        +redo()
        +set_execution_context()
        +get_execution_context()
    }
    
    class CompoundCommand {
        -name: str
        -commands: List[Command]
        +add_command()
        +execute()
        +undo()
        +is_empty()
    }
    
    class PropertyCommand {
        -target: Any
        -property_name: str
        -new_value: Any
        -old_value: Any
        +execute()
        +undo()
    }
    
    class MacroCommand {
        -description: str
        +set_description()
        +get_description()
    }
    
    class CommandHistory {
        -_executed_commands: List[Command]
        -_undone_commands: List[Command]
        +add_command()
        +undo()
        +redo()
        +clear()
        +can_undo()
        +can_redo()
    }
    
    class CommandManager {
        -_history: CommandHistory
        -_is_updating: bool
        -_is_initializing: bool
        +execute()
        +undo()
        +redo()
        +clear()
        +can_undo()
        +can_redo()
        -_navigate_to_command_context()
    }
    
    class WidgetContextRegistry {
        -_widget_contexts: Dict
        +register_widget_container()
        +unregister_widget()
        +get_widget_container()
    }
    
    class ContainerWidget {
        <<interface>>
        +activate_child()*
        +get_container_id()*
        +register_child()
    }
    
    class CommandTabWidget {
        -_container_id: str
        +get_container_id()
        +activate_child()
        +addTab()
    }
    
    class CommandDockWidget {
        -dock_id: str
        +get_container_id()
        +activate_child()
        +setWidget()
    }
    
    class LayoutManager {
        -_main_window: QMainWindow
        -_registered_widgets: Dict
        -_layout_presets: Dict
        +set_main_window()
        +register_widget()
        +capture_current_layout()
        +apply_layout()
    }
    
    class ProjectManager {
        -_command_manager: CommandManager
        -_current_filename: Optional[str]
        -_model_factory: Dict
        -_save_layouts: bool
        +register_model_type()
        +save_project()
        +load_project()
    }
    
    class CommandWidgetBase {
        -_command_enabled: bool
        -_command_manager: CommandManager
        -_observable_model: Observable
        -_observable_property: str
        +bind_to_model()
        +unbind_from_model()
        +_update_widget_from_model()
        +_on_widget_value_changed()
        +_create_property_command()
    }

    Observable --> ObservableProperty : uses
    Command <|-- CompoundCommand : extends
    Command <|-- PropertyCommand : extends
    CompoundCommand <|-- MacroCommand : extends
    CommandManager --> CommandHistory : uses
    CommandManager --> Command : executes
    CommandManager --> WidgetContextRegistry : uses for navigation
    ContainerWidget <|-- CommandTabWidget : implements
    ContainerWidget <|-- CommandDockWidget : implements
    CommandWidgetBase --> Observable : binds
    CommandWidgetBase --> CommandManager : uses
    CommandWidgetBase --> WidgetContextRegistry : registers with
    ProjectManager --> CommandManager : uses
    ProjectManager --> Observable : serializes
    LayoutManager --> ContainerWidget : manages
    ```