"""
Utility functions for working with widget and observable IDs.

This module provides helper functions for parsing and manipulating IDs
following the formats:
- Widgets: [type_code]:[unique_id]:[container_unique_id]:[location]
- Observables: [obs]:[unique_id]:[widget_unique_id]:[property_name]
- Properties: [obs_id]:[property_name]
"""
from typing import Dict, Optional

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

def is_property_id(id_string: str) -> bool:
    """
    Check if an ID string is a property ID.
    
    Args:
        id_string: ID string to check
        
    Returns:
        True if this is a property ID, False otherwise
    """
    if not id_string or ':' not in id_string:
        return False
        
    parts = id_string.split(':')
    
    # Property ID format: [obs_id]:[property_name]
    # First part must be an observable ID
    if len(parts) < 2:
        return False
        
    observable_id = ':'.join(parts[:-1])  # All parts except the last one
    return is_observable_id(observable_id)

def extract_observable_id_from_property_id(property_id: str) -> Optional[str]:
    """
    Extract observable ID from a property ID.
    
    Args:
        property_id: Property ID string
        
    Returns:
        Observable ID string or None if invalid
    """
    if not is_property_id(property_id):
        return None
        
    parts = property_id.split(':')
    if len(parts) < 5:  # obs:unique_id:widget_unique_id:property_name:property_name
        return None
        
    # The observable ID is everything except the last part
    return ':'.join(parts[:-1])

def extract_widget_id_from_property_id(property_id: str) -> Optional[str]:
    """
    Extract widget ID from a property ID.
    
    Args:
        property_id: Property ID string
        
    Returns:
        Widget ID or None if not bound to a widget
    """
    observable_id = extract_observable_id_from_property_id(property_id)
    if not observable_id:
        return None
        
    widget_unique_id = extract_widget_unique_id(observable_id)
    if widget_unique_id == "0":
        return None
        
    # We only have the unique ID, not the full widget ID
    # This function is more of a placeholder - the registry would need to
    # lookup the full widget ID based on the unique ID
    return None

def get_full_id(unique_id: str, id_type: str, **params) -> str:
    """
    Reconstruct full ID from unique part and other params.
    
    Args:
        unique_id: Unique ID part
        id_type: Type of ID ('widget' or 'observable')
        **params: Additional parameters based on ID type
            For widgets: type_code, container_unique_id, location
            For observables: widget_unique_id, property_name
        
    Returns:
        Reconstructed full ID
    """
    if id_type == 'widget':
        type_code = params.get('type_code', '')
        container_unique_id = params.get('container_unique_id', '0')
        location = params.get('location', '0')
        return f"{type_code}:{unique_id}:{container_unique_id}:{location}"
    elif id_type == 'observable':
        widget_unique_id = params.get('widget_unique_id', '0')
        property_name = params.get('property_name', '')
        return f"obs:{unique_id}:{widget_unique_id}:{property_name}"
    else:
        raise ValueError(f"Unknown ID type: {id_type}")

def get_unique_id(full_id: str) -> str:
    """
    Extract unique part from full ID.
    
    Args:
        full_id: Full ID string
        
    Returns:
        Unique ID part
    """
    return extract_unique_id(full_id)