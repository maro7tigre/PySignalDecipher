"""
PySignalDecipher Simplified Command System

A simplified command-based system that focuses on properly tracking user actions,
providing working undo/redo functionality, and integrating with Qt widgets.
"""

# Public API
from .core.observable import Observable, ObservableProperty
from .core.command import Command, CompoundCommand, PropertyCommand, MacroCommand
from .core.command_manager import CommandManager, get_command_manager
from .project.project_manager import ProjectManager, get_project_manager

# Initialize system components - this will auto-initialize layout integration
from . import _auto_init

# Version info
__version__ = "0.2.0"  # Incremented for new architecture

__all__ = [
    # Core components
    'Observable',
    'ObservableProperty',
    'Command',
    'CompoundCommand',
    'PropertyCommand',
    'MacroCommand',
    'CommandManager',
    'get_command_manager',
    
    # Project management
    'ProjectManager',
    'get_project_manager',
]