"""
Utility functions for working with widget IDs.

This module provides helper functions for parsing and manipulating widget IDs
following the format: [type_code]:[unique_id]:[container_unique_id]:[location]
"""
from typing import Dict

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
    Extract just the container_unique_id portion from a full ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Container unique ID string
    """
    return id_string.split(':')[2]

def extract_location(id_string: str) -> str:
    """
    Extract just the location portion from a full ID.
    
    Args:
        id_string: Full ID string
        
    Returns:
        Location string
    """
    return id_string.split(':')[3]