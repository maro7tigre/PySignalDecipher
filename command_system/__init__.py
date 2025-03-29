"""
PySignalDecipher Command System

A comprehensive system for building UIs with integrated undo/redo functionality,
observable pattern for property change tracking, and widget binding.

This package provides core components for:
1. Observable pattern (property change notification)
2. Command pattern (undo/redo functionality)
3. ID system (memory-efficient tracking and relationship management)
4. PySide6 widget integration

For complete documentation, see the docs directory.
"""

# Version info
__version__ = "1.0.0"

# Re-export core modules
from .core import (
    # Observable pattern
    Observable,
    ObservableProperty,
    
    # Command pattern
    Command,
    CompoundCommand,
    PropertyCommand,
    MacroCommand,
    WidgetPropertyCommand,
    
    # Command management
    CommandManager,
    get_command_manager,
    CommandHistory
)

# Re-export ID system
from .id_system import (
    TypeCodes,
    IDRegistry,
    get_id_registry,
    
    # ID utilities
    extract_type_code,
    extract_unique_id,
    extract_container_unique_id,
    extract_location,
    extract_observable_unique_id,
    extract_property_name,
    extract_controller_unique_id,
    is_widget_id,
    is_observable_id,
    is_observable_property_id
)

# Import PySide6 widgets if PySide6 is available
try:
    from .pyside6_widgets import (
        # Base classes
        BaseCommandWidget,
        CommandTriggerMode,
        BaseCommandContainer,
        
        # Widgets
        CommandLineEdit,
        # More widgets will be added here
    )
    
    __has_pyside6__ = True
except ImportError:
    __has_pyside6__ = False

__all__ = [
    # Version info
    '__version__',
    '__has_pyside6__',
    
    # Observable pattern
    'Observable',
    'ObservableProperty',
    
    # Command pattern
    'Command',
    'CompoundCommand',
    'PropertyCommand',
    'MacroCommand',
    'WidgetPropertyCommand',
    
    # Command management
    'CommandManager',
    'get_command_manager',
    'CommandHistory',
    
    # ID system
    'TypeCodes',
    'IDRegistry',
    'get_id_registry',
    'extract_type_code',
    'extract_unique_id',
    'extract_container_unique_id',
    'extract_location',
    'extract_observable_unique_id',
    'extract_property_name',
    'extract_controller_unique_id',
    'is_widget_id',
    'is_observable_id',
    'is_observable_property_id',
]

# Add PySide6 widgets to __all__ if available
if __has_pyside6__:
    __all__.extend([
        # Base classes
        'BaseCommandWidget',
        'CommandTriggerMode',
        'BaseCommandContainer',
        
        # Widgets
        'CommandLineEdit',
        # More widgets will be added here
    ])