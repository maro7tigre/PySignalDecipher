"""
Dock management system for Qt applications with command integration.

This module provides dock management functionality that integrates with
the command system to enable undo/redo capability for dock operations.
"""

from .dock_manager import DockManager, get_dock_manager
from .dock_commands import (
    CreateDockCommand, DeleteDockCommand, 
    DockLocationCommand, SaveLayoutCommand
)
from .dock_widgets import CommandDockWidget, ObservableDockWidget

__all__ = [
    'DockManager',
    'get_dock_manager',
    'CreateDockCommand',
    'DeleteDockCommand',
    'DockLocationCommand',
    'SaveLayoutCommand',
    'CommandDockWidget',
    'ObservableDockWidget'
]