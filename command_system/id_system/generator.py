"""
ID generator for unique, memory-efficient widget IDs.

This module implements a generator for unique widget IDs following the pattern:
[type_code]:[unique_id]:[container_unique_id]:[location]
"""
from typing import Dict

class IDGenerator:
    """Generates unique, memory-efficient widget IDs."""
    
    def __init__(self):
        """Initialize the ID generator with a global counter."""
        self._counter: int = 0
        
    def generate_id(self, type_code: str, container_unique_id: str = "0", location: str = "0") -> str:
        """
        Generate a unique ID with the specified parameters.
        
        Args:
            type_code: Short code indicating widget type (e.g., 'c', 't')
            container_unique_id: ID of parent container (or "0" if none)
            location: Container-specific location identifier (or "0" if not applicable)
            
        Returns:
            A unique ID string in the format: type_code:unique_id:container_unique_id:location
        """
        # Increment the global counter for all types
        self._counter += 1
        
        # Generate unique ID component using base62 encoding
        unique_id = self._encode_to_base62(self._counter)
        
        # Create full ID
        return f"{type_code}:{unique_id}:{container_unique_id}:{location}"
    
    def update_id(self, id_string: str, new_container_id: str = None, new_location: str = None) -> str:
        """
        Update parts of an existing ID string.
        
        Args:
            id_string: Existing ID to update
            new_container_id: New container unique ID (or None to keep existing)
            new_location: New location (or None to keep existing)
            
        Returns:
            Updated ID string
        """
        parts = id_string.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid ID format: {id_string}")
            
        type_code = parts[0]
        unique_id = parts[1]
        container_id = new_container_id if new_container_id is not None else parts[2]
        location = new_location if new_location is not None else parts[3]
        
        return f"{type_code}:{unique_id}:{container_id}:{location}"
    
    def _encode_to_base62(self, number: int) -> str:
        """
        Convert integer to base62 for compact representation.
        
        Args:
            number: Integer to convert
            
        Returns:
            Base62 string representation of the number
        """
        if number == 0:
            return '0'
            
        charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        result = ""
        
        while number > 0:
            result = charset[number % 62] + result
            number //= 62
            
        return result
    
    def decode_from_base62(self, base62_str: str) -> int:
        """
        Convert base62 string back to integer.
        
        Args:
            base62_str: Base62 encoded string
            
        Returns:
            Decoded integer value
        """
        charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        result = 0
        
        for char in base62_str:
            result = result * 62 + charset.index(char)
            
        return result