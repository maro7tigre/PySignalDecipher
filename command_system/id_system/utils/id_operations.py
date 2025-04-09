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


def update_id_unique_id(id_str, new_unique_id):
    """
    Update the unique ID portion of any ID string.
    
    Args:
        id_str: The current ID string
        new_unique_id: The new unique ID
        
    Returns:
        str: The updated ID string
    """
    # First determine the ID type by trying to parse it
    widget_components = parse_widget_id(id_str)
    if widget_components:
        return create_widget_id(
            widget_components['type_code'],
            new_unique_id,
            widget_components['container_unique_id'],
            widget_components['container_location'],
            widget_components['widget_location_id']
        )
    
    observable_components = parse_observable_id(id_str)
    if observable_components:
        return create_observable_id(
            observable_components['type_code'],
            new_unique_id
        )
    
    property_components = parse_property_id(id_str)
    if property_components:
        return create_property_id(
            property_components['type_code'],
            new_unique_id,
            property_components['observable_unique_id'],
            property_components['property_name'],
            property_components['controller_id']
        )
    
    # If none of the parsers could handle it, just do a simple replacement
    parts = id_str.split(':')
    if len(parts) > 1:
        parts[1] = new_unique_id
        return ':'.join(parts)
    
    return id_str


#MARK: - Direct ID update utilities for all component types

def update_id(old_id, new_id):
    """
    Create an updated ID based on the differences between old and new IDs.
    This function preserves the original structure while applying only the
    changes specified in the new ID.
    
    Args:
        old_id: The current ID string
        new_id: The new ID string to extract changes from
        
    Returns:
        tuple: (success, updated_id, error_message) where:
           - success is a boolean indicating if the update is valid
           - updated_id is the resulting ID after applying changes
           - error_message is None if successful or a string describing the issue
    """
    # First check if both IDs are of the same type
    old_type = None
    new_type = None
    
    # Try to parse as widget
    old_widget = parse_widget_id(old_id)
    new_widget = parse_widget_id(new_id)
    
    if old_widget and new_widget:
        # Widget ID update
        if old_widget['type_code'] != new_widget['type_code']:
            return False, old_id, "Cannot change widget type"
        
        # Create the updated widget ID
        updated_id = create_widget_id(
            old_widget['type_code'],
            new_widget['unique_id'] if new_widget['unique_id'] != old_widget['unique_id'] else old_widget['unique_id'],
            new_widget['container_unique_id'] if new_widget['container_unique_id'] != old_widget['container_unique_id'] else old_widget['container_unique_id'],
            new_widget['container_location'] if new_widget['container_location'] != old_widget['container_location'] else old_widget['container_location'],
            new_widget['widget_location_id'] if new_widget['widget_location_id'] != old_widget['widget_location_id'] else old_widget['widget_location_id']
        )
        
        return True, updated_id, None
    
    # Try to parse as observable
    old_observable = parse_observable_id(old_id)
    new_observable = parse_observable_id(new_id)
    
    if old_observable and new_observable:
        # Observable ID update
        if old_observable['type_code'] != new_observable['type_code']:
            return False, old_id, "Cannot change observable type"
        
        # Create the updated observable ID
        updated_id = create_observable_id(
            old_observable['type_code'],
            new_observable['unique_id'] if new_observable['unique_id'] != old_observable['unique_id'] else old_observable['unique_id']
        )
        
        return True, updated_id, None
    
    # Try to parse as property
    old_property = parse_property_id(old_id)
    new_property = parse_property_id(new_id)
    
    if old_property and new_property:
        # Property ID update
        if old_property['type_code'] != new_property['type_code']:
            return False, old_id, "Cannot change property type"
        
        # Create the updated property ID
        updated_id = create_property_id(
            old_property['type_code'],
            new_property['unique_id'] if new_property['unique_id'] != old_property['unique_id'] else old_property['unique_id'],
            new_property['observable_unique_id'] if new_property['observable_unique_id'] != old_property['observable_unique_id'] else old_property['observable_unique_id'],
            new_property['property_name'] if new_property['property_name'] != old_property['property_name'] else old_property['property_name'],
            new_property['controller_id'] if new_property['controller_id'] != old_property['controller_id'] else old_property['controller_id']
        )
        
        return True, updated_id, None
    
    # IDs not of the same type or one/both are invalid
    return False, old_id, "Cannot update ID: incompatible ID formats"