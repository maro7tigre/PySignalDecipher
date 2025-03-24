# New Command System File Structure

```
command_system/
├── __init__.py                   # Public API exports
├── _auto_init.py                 # Auto-initialization (unchanged)
├── core/                         # Core command system components
│   ├── __init__.py               # Exports core components
│   ├── observable.py             # Observable pattern (rewritten)
│   ├── command.py                # Command pattern (rewritten)
│   └── command_manager.py        # Command tracking (rewritten)
├── serialization/                # New serialization system
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
│       ├── dock.py               # Dock serialization
│       └── widget.py             # Widget serialization
├── project/                      # Project management
│   ├── __init__.py
│   ├── project_manager.py        # Project operations (rewritten)
│   └── project_serializer.py     # Project serialization
├── layout/                       # Layout management (unchanged structure)
│   ├── __init__.py
│   ├── layout_manager.py
│   ├── layout_serialization.py
│   └── project_integration.py
├── ui/                           # UI components (unchanged structure)
│   ├── __init__.py
│   ├── property_binding.py
│   ├── qt_bindings.py
│   ├── dock/
│   │   ├── __init__.py
│   │   ├── dock_manager.py
│   │   ├── dock_commands.py
│   │   └── dock_widgets.py
│   └── widgets/
│       ├── __init__.py
│       ├── base.py
│       ├── line_edit.py
│       ├── ...
```

## Key Changes

1. **Core separation**: Move core components (observable, command, command_manager) to a dedicated `core` directory
2. **New serialization system**: Completely separate serialization system
3. **Project management**: Dedicated project directory for project operations
4. **Preserved layout system**: Keep layout system with same structure
5. **Unchanged UI components**: Preserve existing UI components

This structure clearly separates concerns while maintaining compatibility with existing code.