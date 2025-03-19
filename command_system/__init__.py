"""
PySignalDecipher Command System

A command-based system for tracking user actions, undo/redo functionality,
property observation, UI integration, and project serialization.
"""

# Export public API

# Core components
from command_system.command import Command, CompoundCommand
from command_system.command_manager import get_command_manager
from command_system.observable import Observable, ObservableProperty

# UI integration
from command_system.ui.property_binding import PropertyBinder, Binding
from command_system.ui.dock_manager import DockManager

# Signal data handling
from command_system.data.signal_data import SignalData, SignalDataManager, AdaptiveSampler

# Version info
__version__ = "0.1.0"