"""
Core components of the command system.

This module exports the core classes and functions for the command
pattern implementation and observable pattern using the ID system.
"""

from .observable import Observable, ObservableProperty
from .command import (
    Command, 
    CompoundCommand, 
    PropertyCommand, 
    MacroCommand,
    WidgetPropertyCommand,
    SerializationCommand
)
from .command_manager import CommandManager, get_command_manager, CommandHistory

__all__ = [
    # Observable pattern
    'Observable',
    'ObservableProperty',
    
    # Command pattern
    'Command',
    'CompoundCommand',
    'PropertyCommand',
    'MacroCommand',
    'WidgetPropertyCommand',
    'SerializationCommand',
    
    # Command management
    'CommandManager',
    'get_command_manager',
    'CommandHistory'
]