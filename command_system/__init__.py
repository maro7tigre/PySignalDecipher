"""
PySignalDecipher Simplified Command System

A simplified command-based system that focuses on properly tracking user actions,
providing working undo/redo functionality, and integrating with Qt widgets.
"""

# Public API
from .command import Command, CompoundCommand
from .observable import Observable, ObservableProperty
from .command_manager import CommandManager, get_command_manager
from .ui.property_binding import PropertyBinder
from .serialization import ProjectSerializer
from .project_manager import ProjectManager, get_project_manager

# Version info
__version__ = "0.1.1"