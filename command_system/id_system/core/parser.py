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
    except (ValueError, AttributeError):
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
    except (ValueError, AttributeError):
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
    except (ValueError, AttributeError):
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
    except (ValueError, AttributeError, IndexError):
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
    except (ValueError, AttributeError, IndexError):
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
    except (ValueError, AttributeError):
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