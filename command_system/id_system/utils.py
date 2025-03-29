"""
Utility functions for working with component IDs.

This module provides helper functions for parsing and manipulating IDs with the following formats:
- Widget/Container: [type_code]:[unique_id]:[container_unique_id]:[location]
- Observable: [type_code]:[unique_id]
- ObservableProperty: [type_code]:[unique_id]:[observable_unique_id]:[property_name]:[controller_id]
"""
from typing import Dict

def extract_type_code(id_string: str) -> str:
    """
    Extract just the type_code portion from a full ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Type code string
    """
    return id_string.split(':')[0]

def extract_unique_id(id_string: str) -> str:
    """
    Extract just the unique_id portion from a full ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Unique ID string
    """
    return id_string.split(':')[1]

def extract_container_unique_id(id_string: str) -> str:
    """
    Extract just the container_unique_id portion from a widget/container ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Container unique ID string
    """
    parts = id_string.split(':')
    if len(parts) < 3:
        return "0"
    return parts[2]

def extract_location(id_string: str) -> str:
    """
    Extract just the location portion from a widget/container ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Location string
    """
    parts = id_string.split(':')
    if len(parts) < 4:
        return "0"
    return parts[3]

def extract_observable_unique_id(id_string: str) -> str:
    """
    Extract just the observable_unique_id portion from an observable property ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Observable unique ID string
    """
    parts = id_string.split(':')
    if len(parts) < 3:
        return "0"
    return parts[2]

def extract_property_name(id_string: str) -> str:
    """
    Extract just the property_name portion from an observable property ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Property name string
    """
    parts = id_string.split(':')
    if len(parts) < 4:
        return "0"
    return parts[3]

def extract_controller_unique_id(id_string: str) -> str:
    """
    Extract just the controller_unique_id portion from an observable property ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Controller unique ID string
    """
    parts = id_string.split(':')
    if len(parts) < 5:
        return "0"
    return parts[4]

def is_widget_id(id_string: str) -> bool:
    """
    Determine if an ID string belongs to a widget or container.
    
    Args:
        id_string: ID string to check
        
    Returns:
        True if the ID belongs to a widget/container
    """
    parts = id_string.split(':')
    return len(parts) == 4

def is_observable_id(id_string: str) -> bool:
    """
    Determine if an ID string belongs to an observable.
    
    Args:
        id_string: ID string to check
        
    Returns:
        True if the ID belongs to an observable
    """
    parts = id_string.split(':')
    return len(parts) == 2 and parts[0] == 'o'

def is_observable_property_id(id_string: str) -> bool:
    """
    Determine if an ID string belongs to an observable property.
    
    Args:
        id_string: ID string to check
        
    Returns:
        True if the ID belongs to an observable property
    """
    parts = id_string.split(':')
    return len(parts) == 5 and parts[0] == 'op'