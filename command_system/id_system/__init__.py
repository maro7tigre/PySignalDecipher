"""
PySignalDecipher ID System

A memory-efficient ID system for tracking widgets, containers, observables, and observable properties
without maintaining direct references, enabling advanced serialization and navigation.
"""

# Public API
from .generator import IDGenerator
from .registry import IDRegistry, get_id_registry
from .utils import (
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

# Type code constants
class TypeCodes:
    """Type code constants for components."""
    
    # Containers
    TAB_CONTAINER = "t"
    DOCK_CONTAINER = "d"
    WINDOW_CONTAINER = "w"
    CUSTOM_CONTAINER = "x"
    
    # Command Widgets
    LINE_EDIT = "le"
    CHECK_BOX = "cb"
    PUSH_BUTTON = "pb"
    RADIO_BUTTON = "rb"
    COMBO_BOX = "co"
    SLIDER = "sl"
    SPIN_BOX = "sp"
    TEXT_EDIT = "te"
    LIST_WIDGET = "lw"
    TREE_WIDGET = "tw"
    TABLE_WIDGET = "tb"
    CUSTOM_WIDGET = "cw"
    
    # Observables
    OBSERVABLE = "o"
    OBSERVABLE_PROPERTY = "op"

__all__ = [
    # Classes
    'IDGenerator',
    'IDRegistry',
    'TypeCodes',
    
    # Functions
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
    'is_observable_property_id'
]