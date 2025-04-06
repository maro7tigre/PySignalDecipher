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
    
    # Check if all path components are digits
    try:
        parts = location.split(PATH_SEPARATOR)
        return all(part.isdigit() for part in parts)
    except (ValueError, AttributeError):
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
