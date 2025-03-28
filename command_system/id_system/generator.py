"""
ID generator for unique, memory-efficient widget and observable IDs.

This module implements a generator for unique IDs following these patterns:
- Widgets: [type_code]:[unique_id]:[container_unique_id]:[location]
- Observables: [obs]:[unique_id]:[widget_unique_id]:[property_name]
"""
from typing import Dict, Optional

class IDGenerator:
    """Generates unique, memory-efficient widget and observable IDs."""
    
    def __init__(self):
        """Initialize the ID generator with a global counter."""
        self._counter: int = 0
        
    def generate_widget_id(self, type_code: str, container_unique_id: str = "0", location: str = "0") -> str:
        """
        Generate a unique widget ID with the specified parameters.
        
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
    
    def generate_observable_id(self, widget_unique_id: str = "0", property_name: str = "") -> str:
        """
        Generate a unique observable ID with the specified parameters.
        
        Args:
            widget_unique_id: Unique ID of the controlling widget (or "0" if none)
            property_name: Name of the property (or "" if not applicable)
            
        Returns:
            A unique ID string in the format: obs:unique_id:widget_unique_id:property_name
        """
        # Increment the global counter for all types
        self._counter += 1
        
        # Generate unique ID component using base62 encoding
        unique_id = self._encode_to_base62(self._counter)
        
        # Create full ID
        return f"obs:{unique_id}:{widget_unique_id}:{property_name}"
    
    def update_widget_id(self, id_string: str, new_container_id: Optional[str] = None, 
                         new_location: Optional[str] = None) -> str:
        """
        Update parts of an existing widget ID string.
        
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
    
    def update_observable_id(self, id_string: str, new_widget_unique_id: Optional[str] = None, 
                            new_property_name: Optional[str] = None) -> str:
        """
        Update parts of an existing observable ID string.
        
        Args:
            id_string: Existing ID to update
            new_widget_unique_id: New widget unique ID (or None to keep existing)
            new_property_name: New property name (or None to keep existing)
            
        Returns:
            Updated ID string
        """
        parts = id_string.split(':')
        if len(parts) != 4 or parts[0] != "obs":
            raise ValueError(f"Invalid observable ID format: {id_string}")
            
        unique_id = parts[1]
        widget_unique_id = new_widget_unique_id if new_widget_unique_id is not None else parts[2]
        property_name = new_property_name if new_property_name is not None else parts[3]
        
        return f"obs:{unique_id}:{widget_unique_id}:{property_name}"
    
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