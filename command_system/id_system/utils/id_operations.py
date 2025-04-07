"""
ID Operations utility module.

This module contains functions for manipulating and operating on IDs.
"""

import re
from command_system.id_system.core.parser import (
    create_widget_id,
    create_observable_id,
    create_property_id,
    parse_widget_id,
    parse_observable_id,
    parse_property_id,
    get_unique_id_from_id,
    get_type_code_from_id,
)
from command_system.id_system.utils.location_utils import (
    update_location_for_container_move,
    is_valid_container_location,
    is_valid_widget_location_id,
)

#MARK: - ID incrementation utilities

def increment_widget_location_id(location_id):
    """
    Increment a widget location ID to find the next available ID.
    
    Args:
        location_id: The current widget location ID
        
    Returns:
        str: The next widget location ID
    """
    # If it's a numeric ID, increment the number
    if location_id.isdigit():
        return str(int(location_id) + 1)
    
    # If it has a numeric suffix, increment that suffix
    match = re.match(r'([a-zA-Z]+)(\d+)$', location_id)
    if match:
        prefix, number = match.groups()
        return f"{prefix}{int(number) + 1}"
    
    # Otherwise, just append "1"
    return f"{location_id}1"


def find_available_widget_location_id(location_id, is_registered_func):
    """
    Find an available widget location ID starting from the given ID.
    
    Args:
        location_id: The starting widget location ID
        is_registered_func: Function to check if an ID is already registered
        
    Returns:
        str: An available widget location ID
    """
    current_id = location_id
    while is_registered_func(current_id):
        current_id = increment_widget_location_id(current_id)
    return current_id


#MARK: - ID update utilities

def update_widget_container(widget_id_str, new_container_unique_id, new_container_location):
    """
    Update a widget ID string with a new container reference.
    
    Args:
        widget_id_str: The current widget ID string
        new_container_unique_id: The new container's unique ID
        new_container_location: The new container's location
        
    Returns:
        str: The updated widget ID string
    """
    components = parse_widget_id(widget_id_str)
    if not components:
        return widget_id_str
    
    return create_widget_id(
        components['type_code'],
        components['unique_id'],
        new_container_unique_id,
        new_container_location,
        components['widget_location_id']
    )


def update_widget_location(widget_id_str, new_widget_location_id):
    """
    Update a widget ID string with a new widget location ID.
    
    Args:
        widget_id_str: The current widget ID string
        new_widget_location_id: The new widget location ID
        
    Returns:
        str: The updated widget ID string
    """
    components = parse_widget_id(widget_id_str)
    if not components:
        return widget_id_str
    
    return create_widget_id(
        components['type_code'],
        components['unique_id'],
        components['container_unique_id'],
        components['container_location'],
        new_widget_location_id
    )


def update_widget_container_location(widget_id_str, new_container_location):
    """
    Update a widget ID string with a new container location path.
    
    This is used when a container hierarchy changes and all widgets' paths
    need to be updated to reflect the new structure.
    
    Args:
        widget_id_str: The current widget ID string
        new_container_location: The new container location path
        
    Returns:
        str: The updated widget ID string
    """
    components = parse_widget_id(widget_id_str)
    if not components:
        return widget_id_str
    
    return create_widget_id(
        components['type_code'],
        components['unique_id'],
        components['container_unique_id'],
        new_container_location,
        components['widget_location_id']
    )


def update_container_for_moved_widget(widget_id_str, old_container_path, new_container_path):
    """
    Update a widget's ID when its container moves to a new location.
    
    This updates the container_location part of the widget ID to reflect
    the container's new path while preserving all other parts.
    
    Args:
        widget_id_str: The current widget ID string
        old_container_path: The container's old path
        new_container_path: The container's new path
        
    Returns:
        str: The updated widget ID string
    """
    components = parse_widget_id(widget_id_str)
    if not components:
        return widget_id_str
    
    # Update the container_location based on the container's move
    new_location = update_location_for_container_move(
        components['container_location'],
        old_container_path,
        new_container_path
    )
    
    return create_widget_id(
        components['type_code'],
        components['unique_id'],
        components['container_unique_id'],
        new_location,
        components['widget_location_id']
    )


def update_property_observable(property_id_str, new_observable_unique_id):
    """
    Update a property ID string with a new observable reference.
    
    Args:
        property_id_str: The current property ID string
        new_observable_unique_id: The new observable's unique ID
        
    Returns:
        str: The updated property ID string
    """
    components = parse_property_id(property_id_str)
    if not components:
        return property_id_str
    
    return create_property_id(
        components['type_code'],
        components['unique_id'],
        new_observable_unique_id,
        components['property_name'],
        components['controller_id']
    )


def update_property_name(property_id_str, new_property_name):
    """
    Update a property ID string with a new property name.
    
    Args:
        property_id_str: The current property ID string
        new_property_name: The new property name
        
    Returns:
        str: The updated property ID string
    """
    components = parse_property_id(property_id_str)
    if not components:
        return property_id_str
    
    return create_property_id(
        components['type_code'],
        components['unique_id'],
        components['observable_unique_id'],
        new_property_name,
        components['controller_id']
    )


def update_property_controller(property_id_str, new_controller_id):
    """
    Update a property ID string with a new controller reference.
    
    Args:
        property_id_str: The current property ID string
        new_controller_id: The new controller's unique ID
        
    Returns:
        str: The updated property ID string
    """
    components = parse_property_id(property_id_str)
    if not components:
        return property_id_str
    
    return create_property_id(
        components['type_code'],
        components['unique_id'],
        components['observable_unique_id'],
        components['property_name'],
        new_controller_id
    )


def update_id_type_code(id_str, new_type_code):
    """
    Update the type code of any ID string.
    
    Args:
        id_str: The current ID string
        new_type_code: The new type code
        
    Returns:
        str: The updated ID string
    """
    parts = id_str.split(':')
    if not parts:
        return id_str
    
    parts[0] = new_type_code
    return ':'.join(parts)


#MARK: - Validation utilities

def is_valid_widget_id_components(type_code, unique_id, container_unique_id, container_location, widget_location_id):
    """
    Validate all components of a widget ID.
    
    Args:
        type_code: The widget type code
        unique_id: The unique ID
        container_unique_id: The container unique ID
        container_location: The container location
        widget_location_id: The widget location ID
        
    Returns:
        bool: True if all components are valid, False otherwise
    """
    # Type code and unique ID must not be empty
    if not type_code or not unique_id:
        return False
    
    # Container unique ID can be "0" but not empty
    if container_unique_id is None:
        return False
    
    # Container location must be valid
    if not is_valid_container_location(container_location):
        return False
    
    # Widget location ID must be valid
    if not is_valid_widget_location_id(widget_location_id):
        return False
    
    return True


def is_valid_observable_id_components(type_code, unique_id):
    """
    Validate all components of an observable ID.
    
    Args:
        type_code: The observable type code
        unique_id: The unique ID
        
    Returns:
        bool: True if all components are valid, False otherwise
    """
    # Type code and unique ID must not be empty
    return bool(type_code and unique_id)


def is_valid_property_id_components(type_code, unique_id, observable_unique_id, property_name, controller_id):
    """
    Validate all components of a property ID.
    
    Args:
        type_code: The property type code
        unique_id: The unique ID
        observable_unique_id: The observable unique ID
        property_name: The property name
        controller_id: The controller ID
        
    Returns:
        bool: True if all components are valid, False otherwise
    """
    # Type code and unique ID must not be empty
    if not type_code or not unique_id:
        return False
    
    # Observable unique ID and controller ID can be "0" but not None
    if observable_unique_id is None or controller_id is None:
        return False
    
    # Property name must not be empty
    if not property_name:
        return False
    
    return True