"""
Core ID system components.

This package contains the core components of the ID system, including
ID generation, parsing, and the central registry.
"""

from command_system.id_system.core.generator import UniqueIDGenerator
from command_system.id_system.core.parser import (
    parse_widget_id,
    parse_observable_id,
    parse_property_id,
    get_unique_id_from_id,
)
from command_system.id_system.core.registry import IDRegistry, get_id_registry

__all__ = [
    'UniqueIDGenerator',
    'parse_widget_id',
    'parse_observable_id',
    'parse_property_id',
    'get_unique_id_from_id',
    'IDRegistry',
    'get_id_registry',
]