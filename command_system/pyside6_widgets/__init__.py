"""
PySide6 integration for command system.

This package provides PySide6 widgets and containers that integrate with the command system
for automatic undo/redo support, property binding, and serialization.
"""

from .base_widget import BaseCommandWidget, CommandTriggerMode
from .line_edit import CommandLineEdit

# Also create the containers package
from .containers.base_container import BaseCommandContainer

__all__ = [
    # Base classes
    'BaseCommandWidget',
    'CommandTriggerMode',
    'BaseCommandContainer',
    
    # Widgets
    'CommandLineEdit',
]