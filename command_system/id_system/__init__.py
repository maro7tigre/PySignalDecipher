"""
PySignalDecipher ID System

Public API for the ID system that creates and manages unique identifiers
for tracking components without maintaining direct references.
"""

#MARK: - Public API exports

# Import core functionality
from command_system.id_system.core.registry import IDRegistry, get_id_registry

from command_system.id_system.core.parser import parse_property_id
# Import error classes
from command_system.id_system.managers.widget_manager import IDRegistrationError

# Import simple registry for basic ID management
from command_system.id_system.simple.simple_registry import SimpleIDRegistry, get_simple_id_registry

# Import subscription functions
from command_system.id_system.managers.subscription_manager import (
    subscribe_to_id,
    unsubscribe_from_id,
    clear_subscriptions,
)

# Export type codes for public use
from command_system.id_system.types import (
    ContainerTypeCodes,
    WidgetTypeCodes,
    ObservableTypeCodes,
    PropertyTypeCodes,
    TypeCodes
)

__all__ = [
    # Registry classes and accessors
    'IDRegistry', 'get_id_registry',
    'SimpleIDRegistry', 'get_simple_id_registry',
    
    # Error classes
    'IDRegistrationError',
    
    # Subscription system
    'subscribe_to_id', 'unsubscribe_from_id', 'clear_subscriptions',
    
    # Type codes
    'ContainerTypeCodes', 'WidgetTypeCodes', 
    'ObservableTypeCodes', 'PropertyTypeCodes', 'TypeCodes',
    
    # ID parsing and creation
    'parse_property_id',
]