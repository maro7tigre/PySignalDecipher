"""
Utility functions for working with component IDs.

This module provides helper functions for parsing and manipulating IDs with the following formats:
- Widget/Container: [type_code]:[unique_id]:[container_unique_id]:[location_path]
- Observable: [type_code]:[unique_id]
- ObservableProperty: [type_code]:[unique_id]:[observable_unique_id]:[property_name]:[controller_id]
"""
from typing import Dict, Tuple, Optional, List

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
        Location string in format [subcontainer_location]-[widget_location_id]
    """
    parts = id_string.split(':')
    if len(parts) < 4:
        return "0"
    return parts[3]

def extract_location_parts(id_string: str) -> List[str]:
    """
    Extract the hierarchical location parts from a widget ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        List of location path segments
    """
    location = extract_location(id_string)
    if location == "0":
        return ["0"]
    
    # Split by forward slashes for hierarchical path segments
    return location.split("/")

def extract_subcontainer_path(id_string: str) -> str:
    """
    Extract the subcontainer path from a widget ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Subcontainer path string
    """
    parts = extract_location_parts(id_string)
    if len(parts) <= 1 or parts[0] == "0":
        return "0"
    
    # Return all but the last segment (the widget location ID)
    return "/".join(parts[:-1])

def extract_widget_location_id(id_string: str) -> str:
    """
    Extract just the widget_location_id from a widget ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Widget location ID string
    """
    parts = extract_location_parts(id_string)
    if len(parts) <= 1 or parts[0] == "0":
        return "0"
    
    # Last segment is the widget location ID
    return parts[-1]

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

def create_location_path(*path_segments: str) -> str:
    """
    Create a hierarchical location path from path segments.
    
    Args:
        *path_segments: Variable number of path segments
        
    Returns:
        Location path string in format "segment1/segment2/.../segmentN"
    """
    # Filter out empty segments or "0"
    valid_segments = [seg for seg in path_segments if seg and seg != "0"]
    
    if not valid_segments:
        return "0"
    
    return "/".join(valid_segments)

def append_to_location_path(base_path: str, new_segment: str) -> str:
    """
    Append a new segment to an existing location path.
    
    Args:
        base_path: Existing location path
        new_segment: New segment to append
        
    Returns:
        Updated location path
    """
    if base_path == "0":
        return new_segment
    
    if new_segment == "0":
        return base_path
        
    return f"{base_path}/{new_segment}"

def is_subcontainer_id(id_string: str) -> bool:
    """
    Determine if an ID string belongs to a subcontainer.
    
    Args:
        id_string: ID string to check
        
    Returns:
        True if the ID belongs to a subcontainer
    """
    # Subcontainers are widgets with specific type codes
    if not is_widget_id(id_string):
        return False
        
    type_code = extract_type_code(id_string)
    subcontainer_types = ['t', 'd', 'w', 'x']  # tab, dock, window, custom container
    return type_code in subcontainer_types