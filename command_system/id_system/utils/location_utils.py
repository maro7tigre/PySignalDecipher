"""
Location Utilities module.

This module contains utility functions for working with container locations.
"""

from command_system.id_system.types import PATH_SEPARATOR

#MARK: - Container location utilities

def is_valid_container_location(location):
    """
    Check if a container location string is valid.
    
    Args:
        location: The container location string to check
        
    Returns:
        bool: True if the location is valid, False otherwise
    """
    if not location:
        return False
        
    # Root location is valid
    if location == "0":
        return True
    
    # Check if all path components are digits or valid sublocations
    try:
        parts = location.split(PATH_SEPARATOR)
        # First part should be "0" (root)
        if parts[0] != "0":
            return False
            
        # Remaining parts should be non-empty
        return all(part and part != "" for part in parts)
    except (ValueError, AttributeError, TypeError):
        return False


def get_parent_container_location(location):
    """
    Get the parent container location of a given container location.
    
    Args:
        location: The container location to get the parent of
        
    Returns:
        str: The parent container location, or "0" if the location is already at the root
    """
    if location == "0" or PATH_SEPARATOR not in location:
        return "0"
    
    last_separator = location.rindex(PATH_SEPARATOR)
    return location[:last_separator] if last_separator > 0 else "0"


def join_container_locations(parent_location, child_index):
    """
    Join a parent container location with a child index to form a new location path.
    
    Args:
        parent_location: The parent container location
        child_index: The child container index
        
    Returns:
        str: The joined container location
    """
    if parent_location == "0":
        return str(child_index)
    return f"{parent_location}{PATH_SEPARATOR}{child_index}"


def get_location_depth(location):
    """
    Get the depth of a container location in the hierarchy.
    
    Args:
        location: The container location
        
    Returns:
        int: The depth of the location (0 for root)
    """
    if location == "0":
        return 0
    return location.count(PATH_SEPARATOR) + 1


def is_ancestor_location(ancestor, descendant):
    """
    Check if a location is an ancestor of another location.
    
    Args:
        ancestor: The potential ancestor location
        descendant: The potential descendant location
        
    Returns:
        bool: True if ancestor is an ancestor of descendant
    """
    if ancestor == "0":
        return descendant != "0"
    
    return (descendant.startswith(ancestor + PATH_SEPARATOR) or 
            descendant == ancestor)


def is_direct_child_location(parent, child):
    """
    Check if a location is a direct child of another location.
    
    Args:
        parent: The potential parent location
        child: The potential child location
        
    Returns:
        bool: True if child is a direct child of parent
    """
    if parent == "0":
        # For root, a direct child has no path separators
        return child != "0" and PATH_SEPARATOR not in child
    
    # Otherwise, child should start with parent + separator and have exactly one more level
    parent_depth = get_location_depth(parent)
    child_depth = get_location_depth(child)
    
    return (is_ancestor_location(parent, child) and 
            child_depth == parent_depth + 1)


def get_location_components(location):
    """
    Split a container location into its component indices.
    
    Args:
        location: The container location
        
    Returns:
        list: The component indices of the location
    """
    if location == "0":
        return ["0"]
    return location.split(PATH_SEPARATOR)


def get_common_ancestor_location(location1, location2):
    """
    Find the common ancestor location of two container locations.
    
    Args:
        location1: The first container location
        location2: The second container location
        
    Returns:
        str: The common ancestor location, or "0" if no common ancestor
    """
    if location1 == "0" or location2 == "0":
        return "0"
    
    components1 = get_location_components(location1)
    components2 = get_location_components(location2)
    
    common_components = []
    for c1, c2 in zip(components1, components2):
        if c1 == c2:
            common_components.append(c1)
        else:
            break
    
    if not common_components:
        return "0"
    
    return PATH_SEPARATOR.join(common_components)


def get_child_at_index(parent_location, index):
    """
    Get the child location at a specific index within a parent location.
    
    Args:
        parent_location: The parent container location
        index: The child index
        
    Returns:
        str: The child location
    """
    if parent_location == "0":
        return str(index)
    return f"{parent_location}{PATH_SEPARATOR}{index}"


def get_last_component(location):
    """
    Get the last component of a container location.
    
    Args:
        location: The container location
        
    Returns:
        str: The last component, or "0" if location is root
    """
    if location == "0":
        return "0"
    
    components = get_location_components(location)
    return components[-1]


def update_location_for_container_move(widget_location, old_container_path, new_container_path):
    """
    Update a widget's container_location when its container moves.
    
    This is used when a container changes position in the hierarchy and
    all its child widgets need to have their locations updated.
    
    Args:
        widget_location: The widget's current container_location
        old_container_path: The container's old path
        new_container_path: The container's new path
        
    Returns:
        str: The updated container_location
    """
    # If the widget location exactly matches the old container path, return the new path
    if widget_location == old_container_path:
        return new_container_path
    
    # If the widget location is a child of the old container path, update it
    if widget_location.startswith(old_container_path + PATH_SEPARATOR):
        suffix = widget_location[len(old_container_path):]
        return new_container_path + suffix
    
    # Otherwise, the widget location is unrelated
    return widget_location


def is_valid_widget_location_id(location_id):
    """
    Check if a widget location ID is valid.
    
    Args:
        location_id: The widget location ID to check
        
    Returns:
        bool: True if the location ID is valid, False otherwise
    """
    # Widget location IDs should not be empty and should not contain path separators
    return (location_id is not None and 
            location_id != "" and 
            PATH_SEPARATOR not in location_id)