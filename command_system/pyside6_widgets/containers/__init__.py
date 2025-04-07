"""
PySide6 container integration for command system.

This package provides PySide6 containers that integrate with the command system
for automatic undo/redo support, property binding, and serialization.
"""

from .base_container import BaseCommandContainer
from .tab_widget import CommandTabWidget

__all__ = [
    'BaseCommandContainer',
    'CommandTabWidget',
]