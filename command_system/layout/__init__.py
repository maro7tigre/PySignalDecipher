"""
Layout management system for PySignalDecipher.

This system allows saving and restoring UI layouts independently from
the command system and doesn't affect the undo/redo history.
"""

from .layout_manager import LayoutManager, get_layout_manager
from .layout_serialization import serialize_layout, deserialize_layout
from .project_integration import (
    save_layout_with_project, 
    load_layout_from_project,
    extend_project_manager,
    initialize_layout_integration  # Added this function
)

__all__ = [
    'LayoutManager',
    'get_layout_manager',
    'serialize_layout',
    'deserialize_layout',
    'save_layout_with_project',
    'load_layout_from_project',
    'extend_project_manager',
    'initialize_layout_integration'  # Added this function
]