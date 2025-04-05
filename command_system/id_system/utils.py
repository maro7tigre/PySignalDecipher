"""
Utility functions for working with component IDs.

This module provides helper functions for parsing and manipulating IDs with the following formats:
- Widget/Container: [type_code]:[unique_id]:[container_unique_id]:[subcontainer_path]-[widget_location_id]
- Observable: [type_code]:[unique_id]
- ObservableProperty: [type_code]:[unique_id]:[observable_unique_id]:[property_name]:[controller_id]
"""
from typing import Dict, Tuple, Optional, List


def extract_type_code(id_string: str) -> str:
    """
    Extract the type_code portion from a full ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Type code string or empty string if invalid
    """
    parts = id_string.split(':')
    return parts[0] if parts else ""


def extract_unique_id(id_string: str) -> str:
    """
    Extract the unique_id portion from a full ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Unique ID string or "0" if not found
    """
    parts = id_string.split(':')
    return parts[1] if len(parts) > 1 else "0"


def extract_container_unique_id(id_string: str) -> str:
    """
    Extract the container_unique_id portion from a widget/container ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Container unique ID string or "0" if not found
    """
    parts = id_string.split(':')
    return parts[2] if len(parts) > 2 else "0"


def extract_location(id_string: str) -> str:
    """
    Extract the location portion from a widget/container ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Location string in format [subcontainer_path]-[widget_location_id] or "0" if not found
    """
    parts = id_string.split(':')
    return parts[3] if len(parts) > 3 else "0"


def extract_location_parts(id_string: str) -> List[str]:
    """
    Extract hierarchical location parts from a widget ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        List of location path segments
    """
    location = extract_location(id_string)
    if location == "0":
        return ["0"]
    
    # Split by slashes first (for hierarchical paths)
    path_segments = []
    
    # Handle / hierarchy path and - widget location ID separator
    if "/" in location:
        # Split hierarchical path
        path_parts = location.split('/')
        
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1 and "-" in part:
                # Last part with widget location ID
                subparts = part.split('-')
                if len(subparts) > 0 and subparts[0]:
                    path_segments.append(subparts[0])
                if len(subparts) > 1:
                    path_segments.append(subparts[1])
            else:
                path_segments.append(part)
    elif "-" in location:
        # Simple location with just subcontainer_path-widget_id format
        subparts = location.split('-')
        if len(subparts) > 0 and subparts[0] and subparts[0] != "0":
            path_segments.append(subparts[0])
        if len(subparts) > 1:
            path_segments.append(subparts[1])
    else:
        # Just a simple location with no separators
        path_segments.append(location)
    
    return path_segments if path_segments else ["0"]


def extract_subcontainer_path(id_string: str) -> str:
    """
    Extract the subcontainer path from a widget ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Subcontainer path string
    """
    location = extract_location(id_string)
    if location == "0":
        return "0"
    
    # If there's a hyphen, the part before it is the subcontainer path
    if "-" in location:
        return location.split("-")[0]
    
    # If there are slashes but no hyphen, take everything up to the last slash
    if "/" in location:
        parts = location.split("/")
        if len(parts) > 1:
            return "/".join(parts[:-1])
    
    # No path separators found
    return location


def extract_widget_location_id(id_string: str) -> str:
    """
    Extract the widget_location_id from a widget ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Widget location ID string
    """
    location = extract_location(id_string)
    if location == "0":
        return "0"
    
    # If there's a hyphen, the part after it is the widget location ID
    if "-" in location:
        parts = location.split("-")
        return parts[-1]
    
    # If there are slashes, take the last segment
    if "/" in location:
        parts = location.split("/")
        last_part = parts[-1]
        
        # Check if last part has a hyphen for widget location ID
        if "-" in last_part:
            return last_part.split("-")[-1]
    
    # No specific widget location ID found
    return "0"


def extract_observable_unique_id(id_string: str) -> str:
    """
    Extract the observable_unique_id portion from an observable property ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Observable unique ID string
    """
    parts = id_string.split(':')
    return parts[2] if len(parts) > 2 else "0"


def extract_property_name(id_string: str) -> str:
    """
    Extract the property_name portion from an observable property ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Property name string
    """
    parts = id_string.split(':')
    return parts[3] if len(parts) > 3 else "0"


def extract_controller_unique_id(id_string: str) -> str:
    """
    Extract the controller_unique_id portion from an observable property ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Controller unique ID string
    """
    parts = id_string.split(':')
    return parts[4] if len(parts) > 4 else "0"


def is_widget_id(id_string: str) -> bool:
    """
    Determine if an ID string belongs to a widget or container.
    
    Args:
        id_string: ID string to check
        
    Returns:
        True if the ID belongs to a widget/container
    """
    parts = id_string.split(':')
    if len(parts) != 4:
        return False
    
    # Widget type codes should not be 'o' or 'op'
    return parts[0] != 'o' and parts[0] != 'op'


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
    # Filter out empty segments but keep explicit "0" values
    valid_segments = [seg for seg in path_segments if seg != ""]
    
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