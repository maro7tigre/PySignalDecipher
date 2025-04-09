"""
ID parser module.

This module contains functions for parsing different types of ID strings
and creating IDs in the ID system.
"""

from command_system.id_system.types import (
    ID_SEPARATOR,
    LOCATION_SEPARATOR,
    PATH_SEPARATOR,
    DEFAULT_NO_CONTAINER,
    DEFAULT_NO_OBSERVABLE,
    DEFAULT_NO_CONTROLLER,
    DEFAULT_NO_PROPERTY_NAME,
)


#MARK: - ID parsing functions

def parse_widget_id(id_string):
    """
    Parse a widget ID string into its components.
    
    Format: [type_code]:[unique_id]:[container_unique_id]:[location]
    Where location: [container_location]-[widget_location_id]
    
    Args:
        id_string: The widget ID string to parse
        
    Returns:
        dict: A dictionary with parsed components or None if invalid
    """
    try:
        # Split the main parts
        parts = id_string.split(ID_SEPARATOR)
        if len(parts) != 4:
            return None
        
        type_code, unique_id, container_unique_id, location = parts
        
        # Split the location part
        location_parts = location.split(LOCATION_SEPARATOR)
        if len(location_parts) != 2:
            return None
        
        container_location, widget_location_id = location_parts
        
        return {
            'type_code': type_code,
            'unique_id': unique_id,
            'container_unique_id': container_unique_id,
            'location': location,
            'container_location': container_location,
            'widget_location_id': widget_location_id
        }
    except (ValueError, AttributeError, TypeError):
        return None


def parse_observable_id(id_string):
    """
    Parse an observable ID string into its components.
    
    Format: [type_code]:[unique_id]
    
    Args:
        id_string: The observable ID string to parse
        
    Returns:
        dict: A dictionary with parsed components or None if invalid
    """
    try:
        # Split the main parts
        parts = id_string.split(ID_SEPARATOR)
        if len(parts) != 2:
            return None
        
        type_code, unique_id = parts
        
        return {
            'type_code': type_code,
            'unique_id': unique_id
        }
    except (ValueError, AttributeError, TypeError):
        return None


def parse_property_id(id_string):
    """
    Parse a property ID string into its components.
    
    Format: [type_code]:[unique_id]:[observable_unique_id]:[property_name]:[controller_id]
    
    Args:
        id_string: The property ID string to parse
        
    Returns:
        dict: A dictionary with parsed components or None if invalid
    """
    try:
        # Split the main parts
        parts = id_string.split(ID_SEPARATOR)
        if len(parts) != 5:
            return None
        
        type_code, unique_id, observable_unique_id, property_name, controller_id = parts
        
        return {
            'type_code': type_code,
            'unique_id': unique_id,
            'observable_unique_id': observable_unique_id,
            'property_name': property_name,
            'controller_id': controller_id
        }
    except (ValueError, AttributeError, TypeError):
        return None


#MARK: - ID creation functions

def create_widget_id(type_code, unique_id, container_id=DEFAULT_NO_CONTAINER, 
                    container_location="0", widget_location_id="0"):
    """
    Create a widget ID string from components.
    
    Args:
        type_code: The widget type code
        unique_id: The unique ID of the widget
        container_id: The container ID or unique ID (default: "0")
        container_location: The container's location path (default: "0")
        widget_location_id: The widget's ID within the container (default: "0")
        
    Returns:
        str: The formatted widget ID string
    """
    # Extract container_unique_id if full container ID is provided
    container_unique_id = container_id
    if container_id and ID_SEPARATOR in container_id:
        container_unique_id = get_unique_id_from_id(container_id)
    
    location = f"{container_location}{LOCATION_SEPARATOR}{widget_location_id}"
    return f"{type_code}{ID_SEPARATOR}{unique_id}{ID_SEPARATOR}{container_unique_id}{ID_SEPARATOR}{location}"


def create_observable_id(type_code, unique_id):
    """
    Create an observable ID string from components.
    
    Args:
        type_code: The observable type code
        unique_id: The unique ID of the observable
        
    Returns:
        str: The formatted observable ID string
    """
    return f"{type_code}{ID_SEPARATOR}{unique_id}"


def create_property_id(type_code, unique_id, observable_id=DEFAULT_NO_OBSERVABLE,
                      property_name=DEFAULT_NO_PROPERTY_NAME, controller_id=DEFAULT_NO_CONTROLLER):
    """
    Create a property ID string from components.
    
    Args:
        type_code: The property type code
        unique_id: The unique ID of the property
        observable_id: The observable ID or unique ID (default: "0")
        property_name: The name of the property (default: "0")
        controller_id: The controller ID or unique ID (default: "0")
        
    Returns:
        str: The formatted property ID string
    """
    # Extract observable_unique_id if full observable ID is provided
    observable_unique_id = observable_id
    if observable_id and observable_id != DEFAULT_NO_OBSERVABLE and ID_SEPARATOR in observable_id:
        observable_unique_id = get_unique_id_from_id(observable_id)
        
    # Extract controller_unique_id if full controller ID is provided
    controller_unique_id = controller_id
    if controller_id and controller_id != DEFAULT_NO_CONTROLLER and ID_SEPARATOR in controller_id:
        controller_unique_id = get_unique_id_from_id(controller_id)
    
    return (f"{type_code}{ID_SEPARATOR}{unique_id}{ID_SEPARATOR}"
            f"{observable_unique_id}{ID_SEPARATOR}{property_name}{ID_SEPARATOR}{controller_unique_id}")


#MARK: - ID utility functions

def get_unique_id_from_id(id_string):
    """
    Extract the unique ID portion from any type of ID string.
    
    Args:
        id_string: The ID string to extract from
        
    Returns:
        str: The unique ID or None if invalid format
    """
    try:
        # The unique ID is always the second part (index 1) in all ID formats
        parts = id_string.split(ID_SEPARATOR)
        if len(parts) >= 2:
            return parts[1]
        return None
    except (ValueError, AttributeError, IndexError, TypeError):
        return None


def get_type_code_from_id(id_string):
    """
    Extract the type code portion from any type of ID string.
    
    Args:
        id_string: The ID string to extract from
        
    Returns:
        str: The type code or None if invalid format
    """
    try:
        # The type code is always the first part (index 0) in all ID formats
        parts = id_string.split(ID_SEPARATOR)
        if parts:
            return parts[0]
        return None
    except (ValueError, AttributeError, IndexError, TypeError):
        return None


def parse_location(location_string):
    """
    Parse a location string into container location and widget location ID.
    
    Args:
        location_string: The location string to parse (format: "container_loc-widget_loc_id")
        
    Returns:
        tuple: (container_location, widget_location_id) or (None, None) if invalid
    """
    try:
        parts = location_string.split(LOCATION_SEPARATOR)
        if len(parts) == 2:
            return parts[0], parts[1]
        return None, None
    except (ValueError, AttributeError, TypeError):
        return None, None


def join_location_parts(container_location, widget_location_id):
    """
    Join container location and widget location ID into a single location string.
    
    Args:
        container_location: The container's location path 
        widget_location_id: The widget's location ID within the container
        
    Returns:
        str: The combined location string
    """
    return f"{container_location}{LOCATION_SEPARATOR}{widget_location_id}"


def is_subcontainer_location(parent_loc, child_loc):
    """
    Check if child_loc is a direct subcontainer of parent_loc.
    
    Args:
        parent_loc: The parent container location
        child_loc: The potential child container location
        
    Returns:
        bool: True if child_loc is a direct subcontainer of parent_loc
    """
    # If parent is root "0", then any top-level container is a subcontainer
    if parent_loc == "0" and PATH_SEPARATOR not in child_loc:
        return True
        
    # Otherwise, check if child starts with parent and has one more level
    return (child_loc.startswith(parent_loc + PATH_SEPARATOR) and 
            child_loc.count(PATH_SEPARATOR) == parent_loc.count(PATH_SEPARATOR) + 1)


def get_parent_container_location(container_location):
    """
    Get the parent container location of a given container location.
    
    Args:
        container_location: The container location to get the parent of
        
    Returns:
        str: The parent container location, or "0" if at root
    """
    if container_location == "0":
        return "0"  # Root has no parent
        
    # Find the last path separator
    last_separator_index = container_location.rfind(PATH_SEPARATOR)
    if last_separator_index == -1:
        return "0"  # Top-level container, parent is root
        
    # Return everything before the last separator
    return container_location[:last_separator_index]


def get_container_path_components(container_location):
    """
    Split a container location path into its component segments.
    
    Args:
        container_location: The container location path
        
    Returns:
        list: The component segments of the path
    """
    if container_location == "0":
        return ["0"]
        
    return container_location.split(PATH_SEPARATOR)


def join_container_path(components):
    """
    Join container path components into a single path.
    
    Args:
        components: List of path components
        
    Returns:
        str: The joined container path
    """
    if not components:
        return "0"
        
    if len(components) == 1 and components[0] == "0":
        return "0"
        
    return PATH_SEPARATOR.join(components)


def get_full_container_path(container_location, container_widget_location_id):
    """
    Create a full container path by combining a container's location with its widget location ID.
    
    This is used to get the container_location for widgets that will be placed
    inside this container.
    
    Args:
        container_location: The container's container_location
        container_widget_location_id: The container's widget_location_id
        
    Returns:
        str: The full container path
    """
    if container_location == "0":
        return f"0{PATH_SEPARATOR}{container_widget_location_id}"
    else:
        return f"{container_location}{PATH_SEPARATOR}{container_widget_location_id}"


def replace_container_path_prefix(path, old_prefix, new_prefix):
    """
    Replace the prefix of a container path.
    
    This is used when updating container locations to maintain the hierarchy.
    
    Args:
        path: The full container path
        old_prefix: The old prefix to replace
        new_prefix: The new prefix to use
        
    Returns:
        str: The updated container path
    """
    if path == old_prefix:
        return new_prefix
        
    if path.startswith(old_prefix + PATH_SEPARATOR):
        return new_prefix + path[len(old_prefix):]
        
    return path  # Path doesn't start with the prefix, return unchanged


#MARK: - ID comparison functions

def compare_ids(id1, id2):
    """
    Compare two IDs and determine what components differ.
    
    Args:
        id1: First ID string
        id2: Second ID string
        
    Returns:
        dict: A dictionary with differences, or None if IDs are not comparable
    """
    # Try to parse as widget IDs
    widget1 = parse_widget_id(id1)
    widget2 = parse_widget_id(id2)
    
    if widget1 and widget2:
        # Both are widget IDs
        return {
            'type': 'widget',
            'type_code_changed': widget1['type_code'] != widget2['type_code'],
            'unique_id_changed': widget1['unique_id'] != widget2['unique_id'],
            'container_changed': widget1['container_unique_id'] != widget2['container_unique_id'],
            'container_location_changed': widget1['container_location'] != widget2['container_location'],
            'widget_location_id_changed': widget1['widget_location_id'] != widget2['widget_location_id']
        }
    
    # Try to parse as observable IDs
    obs1 = parse_observable_id(id1)
    obs2 = parse_observable_id(id2)
    
    if obs1 and obs2:
        # Both are observable IDs
        return {
            'type': 'observable',
            'type_code_changed': obs1['type_code'] != obs2['type_code'],
            'unique_id_changed': obs1['unique_id'] != obs2['unique_id']
        }
    
    # Try to parse as property IDs
    prop1 = parse_property_id(id1)
    prop2 = parse_property_id(id2)
    
    if prop1 and prop2:
        # Both are property IDs
        return {
            'type': 'property',
            'type_code_changed': prop1['type_code'] != prop2['type_code'],
            'unique_id_changed': prop1['unique_id'] != prop2['unique_id'],
            'observable_changed': prop1['observable_unique_id'] != prop2['observable_unique_id'],
            'property_name_changed': prop1['property_name'] != prop2['property_name'],
            'controller_changed': prop1['controller_id'] != prop2['controller_id']
        }
    
    # IDs are not of the same type
    return None


def get_id_components(id_string):
    """
    Get all components from an ID string based on its type.
    
    Args:
        id_string: The ID string to parse
        
    Returns:
        dict: A dictionary with all components, or None if invalid
    """
    # Try to parse as different ID types
    widget = parse_widget_id(id_string)
    if widget:
        return {
            'type': 'widget',
            'components': widget
        }
    
    observable = parse_observable_id(id_string)
    if observable:
        return {
            'type': 'observable',
            'components': observable
        }
    
    property_id = parse_property_id(id_string)
    if property_id:
        return {
            'type': 'property',
            'components': property_id
        }
    
    # Invalid ID
    return None