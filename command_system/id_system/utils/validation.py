"""
Validation Utilities module.

This module contains utility functions for validating ID strings and components.
"""

from command_system.id_system.types import (
    TypeCodes,
    RESERVED_CHARS,
)
from command_system.id_system.core.parser import (
    parse_widget_id,
    parse_observable_id,
    parse_property_id,
)
from command_system.id_system.utils.location_utils import is_valid_container_location

#MARK: - ID validation functions

def is_valid_widget_id(id_string):
    """
    Check if a widget ID string is valid.
    
    Args:
        id_string: The widget ID string to check
        
    Returns:
        bool: True if the ID is valid, False otherwise
    """
    components = parse_widget_id(id_string)
    if not components:
        return False
    
    # Check type code
    if not components['type_code'] in TypeCodes.get_all_widget_codes():
        return False
    
    # Check container location
    if not is_valid_container_location(components['container_location']):
        return False
    
    return True


def is_valid_observable_id(id_string):
    """
    Check if an observable ID string is valid.
    
    Args:
        id_string: The observable ID string to check
        
    Returns:
        bool: True if the ID is valid, False otherwise
    """
    components = parse_observable_id(id_string)
    if not components:
        return False
    
    # Check type code
    if not TypeCodes.is_valid_observers(components['type_code']):
        return False
    
    return True


def is_valid_property_id(id_string):
    """
    Check if a property ID string is valid.
    
    Args:
        id_string: The property ID string to check
        
    Returns:
        bool: True if the ID is valid, False otherwise
    """
    components = parse_property_id(id_string)
    if not components:
        return False
    
    # Check type code
    if not TypeCodes.is_valid_properties(components['type_code']):
        return False
    
    return True


#MARK: - Component validation functions

def is_valid_type_code(type_code, component_type=None):
    """
    Check if a type code is valid for the given component type.
    
    Args:
        type_code: The type code to check
        component_type: The component type ("widget", "container", "observable", "property")
            or None to check against all types
        
    Returns:
        bool: True if the type code is valid, False otherwise
    """
    if component_type == "widget":
        return TypeCodes.is_valid_all_widgets(type_code)
    elif component_type == "container":
        return TypeCodes.is_valid_containers(type_code)
    elif component_type == "observable":
        return TypeCodes.is_valid_observers(type_code)
    elif component_type == "property":
        return TypeCodes.is_valid_properties(type_code)
    else:
        return TypeCodes.is_valid_code(type_code)


def is_valid_unique_id(unique_id):
    """
    Check if a unique ID is valid.
    
    Args:
        unique_id: The unique ID to check
        
    Returns:
        bool: True if the unique ID is valid, False otherwise
    """
    if not unique_id:
        return False
    
    # Check for reserved characters
    for char in RESERVED_CHARS:
        if char in unique_id:
            return False
    
    return True


def is_valid_property_name(property_name):
    """
    Check if a property name is valid.
    
    Args:
        property_name: The property name to check
        
    Returns:
        bool: True if the property name is valid, False otherwise
    """
    if not property_name:
        return False
    
    # Check for reserved characters
    for char in RESERVED_CHARS:
        if char in property_name:
            return False
    
    return True


def validate_widget_components(type_code, unique_id, container_unique_id, location):
    """
    Validate all components of a widget ID.
    
    Args:
        type_code: The widget type code
        unique_id: The unique ID
        container_unique_id: The container unique ID
        location: The location string
        
    Returns:
        tuple: (is_valid, error_message) where is_valid is a boolean and
               error_message is None if valid or a string describing the issue
    """
    if not is_valid_type_code(type_code, "widget"):
        return False, f"Invalid widget type code: {type_code}"
    
    if not is_valid_unique_id(unique_id):
        return False, f"Invalid unique ID: {unique_id}"
    
    if not is_valid_unique_id(container_unique_id):
        return False, f"Invalid container unique ID: {container_unique_id}"
    
    container_location, widget_location_id = location.split("-") if "-" in location else (None, None)
    
    if container_location is None or not is_valid_container_location(container_location):
        return False, f"Invalid container location: {container_location}"
    
    if widget_location_id is None or not widget_location_id:
        return False, "Missing widget location ID"
    
    return True, None


def validate_observable_components(type_code, unique_id):
    """
    Validate all components of an observable ID.
    
    Args:
        type_code: The observable type code
        unique_id: The unique ID
        
    Returns:
        tuple: (is_valid, error_message) where is_valid is a boolean and
               error_message is None if valid or a string describing the issue
    """
    if not is_valid_type_code(type_code, "observable"):
        return False, f"Invalid observable type code: {type_code}"
    
    if not is_valid_unique_id(unique_id):
        return False, f"Invalid unique ID: {unique_id}"
    
    return True, None


def validate_property_components(type_code, unique_id, observable_unique_id, property_name, controller_id):
    """
    Validate all components of a property ID.
    
    Args:
        type_code: The property type code
        unique_id: The unique ID
        observable_unique_id: The observable unique ID
        property_name: The property name
        controller_id: The controller ID
        
    Returns:
        tuple: (is_valid, error_message) where is_valid is a boolean and
               error_message is None if valid or a string describing the issue
    """
    if not is_valid_type_code(type_code, "property"):
        return False, f"Invalid property type code: {type_code}"
    
    if not is_valid_unique_id(unique_id):
        return False, f"Invalid unique ID: {unique_id}"
    
    if not is_valid_unique_id(observable_unique_id):
        return False, f"Invalid observable unique ID: {observable_unique_id}"
    
    if not is_valid_property_name(property_name):
        return False, f"Invalid property name: {property_name}"
    
    if not is_valid_unique_id(controller_id):
        return False, f"Invalid controller ID: {controller_id}"
    
    return True, None


#MARK: - ID Update Validation Functions

def validate_id_type_consistency(old_id, new_id):
    """
    Validate that two IDs are of the same component type.
    
    Args:
        old_id: The current ID string
        new_id: The new ID string
        
    Returns:
        tuple: (is_valid, error_message) where is_valid is a boolean and
               error_message is None if valid or a string describing the issue
    """
    # Try widget ID parsing first
    old_components = parse_widget_id(old_id)
    new_components = parse_widget_id(new_id)
    
    if old_components and new_components:
        # Both are widget IDs
        if old_components['type_code'] != new_components['type_code']:
            return False, f"Type code mismatch: {old_components['type_code']} vs {new_components['type_code']}"
        return True, None
    
    # Try observable ID parsing
    old_components = parse_observable_id(old_id)
    new_components = parse_observable_id(new_id)
    
    if old_components and new_components:
        # Both are observable IDs
        if old_components['type_code'] != new_components['type_code']:
            return False, f"Type code mismatch: {old_components['type_code']} vs {new_components['type_code']}"
        return True, None
    
    # Try property ID parsing
    old_components = parse_property_id(old_id)
    new_components = parse_property_id(new_id)
    
    if old_components and new_components:
        # Both are property IDs
        if old_components['type_code'] != new_components['type_code']:
            return False, f"Type code mismatch: {old_components['type_code']} vs {new_components['type_code']}"
        return True, None
    
    # IDs are not of the same type or not valid
    return False, "IDs must be of the same component type"