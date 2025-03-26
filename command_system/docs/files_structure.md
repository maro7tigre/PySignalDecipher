# Updated Command System File Structure

```
command_system/
├── __init__.py                   # Public API exports
├── _auto_init.py                 # Auto-initialization
├── core/                         # Core command system components
│   ├── __init__.py               # Exports core components
│   ├── observable.py             # Observable pattern
│   ├── command.py                # Command pattern
│   ├── command_manager.py        # Command tracking
│   └── widget_context.py         # Widget context registry for navigation
├── serialization/                # Serialization system
│   ├── __init__.py               # Exports serialization API
│   ├── manager.py                # SerializationManager
│   ├── registry.py               # Type and factory registration
│   ├── adapters/                 # Format adapters
│   │   ├── __init__.py
│   │   ├── json_adapter.py       # JSON serialization
│   │   ├── binary_adapter.py     # Binary serialization
│   │   ├── xml_adapter.py        # XML serialization
│   │   └── yaml_adapter.py       # YAML serialization
│   └── serializers/              # Component serializers
│       ├── __init__.py
│       ├── observable.py         # Observable serialization
│       └── widget.py             # Widget serialization
├── project/                      # Project management
│   ├── __init__.py
│   ├── project_manager.py        # Project operations
│   └── project_serializer.py     # Project serialization
├── layout/                       # Layout management
│   ├── __init__.py
│   ├── layout_manager.py
│   ├── layout_serialization.py
│   └── project_integration.py
├── widgets/                      # UI components
│   ├── __init__.py
│   ├── base_widget.py                   # Base class for command-aware widgets
│   ├── line_edit.py              # Command-aware line edit
│   ├── containers/               # Container widgets
│   │   ├── __init__.py
│   │   ├── base_container.py     # Base container interface
│   │   ├── tab_widget.py         # Command-aware tab widget
│   │   └── dock_widget.py        # Command-aware dock widget
│   └── other widget types...
```

## Key Changes

1. **Widget Context System**: Added `widget_context.py` to the core directory to support navigation during undo/redo
2. **Container Organization**: Created a dedicated `containers` folder under `widgets` for all container components
3. **Dock Simplification**: Consolidated dock-related functionality into a single `dock_widget.py` file
4. **Container Base Class**: Added `base_container.py` to define the common interface for container widgets
5. **Command-Aware Tab Widget**: Added a tab widget that supports command-based navigation

This reorganization improves code organization by:
- Grouping related container widgets together
- Simplifying the dock management system
- Providing a clear interface for all container types
- Adding support for navigating back to the originating widget during undo/redo

The new structure maintains clean separation of concerns while making the system more maintainable and easier to extend with new container types in the future.