"""
Utility functions for working with widget and observable IDs.

This module provides helper functions for parsing and manipulating IDs
following the formats:
- Widgets: [type_code]:[unique_id]:[container_unique_id]:[location]
- Observables: [obs]:[unique_id]:[widget_unique_id]:[property_name]
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
    Extract just the container_unique_id portion from a widget ID.
    
    Args:
        id_string: Full widget ID string
        
    Returns:
        Container unique ID string
    """
    if not is_widget_id(id_string):
        raise ValueError(f"Not a widget ID: {id_string}")
        
    return id_string.split(':')[2]

def extract_location(id_string: str) -> str:
    """
    Extract just the location portion from a widget ID.
    
    Args:
        id_string: Full widget ID string
        
    Returns:
        Location string
    """
    if not is_widget_id(id_string):
        raise ValueError(f"Not a widget ID: {id_string}")
        
    return id_string.split(':')[3]

def extract_widget_unique_id(id_string: str) -> str:
    """
    Extract just the widget_unique_id portion from an observable ID.
    
    Args:
        id_string: Full observable ID string
        
    Returns:
        Widget unique ID string
    """
    if not is_observable_id(id_string):
        raise ValueError(f"Not an observable ID: {id_string}")
        
    return id_string.split(':')[2]

def extract_property_name(id_string: str) -> str:
    """
    Extract just the property_name portion from an observable ID.
    
    Args:
        id_string: Full observable ID string
        
    Returns:
        Property name string
    """
    if not is_observable_id(id_string):
        raise ValueError(f"Not an observable ID: {id_string}")
        
    return id_string.split(':')[3]

def is_observable_id(id_string: str) -> bool:
    """
    Check if an ID string is an observable ID.
    
    Args:
        id_string: ID string to check
        
    Returns:
        True if this is an observable ID, False otherwise
    """
    parts = id_string.split(':')
    return len(parts) == 4 and parts[0] == "obs"

def is_widget_id(id_string: str) -> bool:
    """
    Check if an ID string is a widget ID.
    
    Args:
        id_string: ID string to check
        
    Returns:
        True if this is a widget ID, False otherwise
    """
    parts = id_string.split(':')
    return len(parts) == 4 and parts[0] != "obs"