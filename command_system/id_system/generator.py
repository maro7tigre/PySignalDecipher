"""
ID generator for unique, memory-efficient component IDs.

This module implements a generator for unique IDs following these patterns:
- Widget/Container: [type_code]:[unique_id]:[container_unique_id]:[subcontainer_location]-[widget_location_id]
- Observable: [type_code]:[unique_id]
- ObservableProperty: [type_code]:[unique_id]:[observable_unique_id]:[property_name]:[controller_id]
"""
from typing import Dict, Optional, Set

class IDGenerator:
    """Generates unique, memory-efficient component IDs."""
    
    def __init__(self):
        """Initialize the ID generator with a global counter."""
        self._counter: int = 0
        self._used_ids: Set[str] = set()  # Track used unique IDs to avoid collisions
        
    def generate_id(self, type_code: str, container_unique_id: str = "0", 
                   location: str = "0") -> str:
        """
        Generate a unique widget/container ID with the specified parameters.
        
        Args:
            type_code: Short code indicating widget type (e.g., 'le', 't')
            container_unique_id: ID of parent container (or "0" if none)
            location: Container-specific location identifier with format:
                     [subcontainer_location]-[widget_location_id]
                     (or "0" if not applicable)
            
        Returns:
            A unique ID string in format: type_code:unique_id:container_unique_id:location
        """
        # Increment the global counter
        self._counter += 1
        
        # Generate unique ID component using base62 encoding
        unique_id = self._generate_unique_id()
        
        # Create full ID
        return f"{type_code}:{unique_id}:{container_unique_id}:{location}"
    
    def generate_observable_id(self, type_code: str) -> str:
        """
        Generate a unique observable ID.
        
        Args:
            type_code: Short code indicating observable type (e.g., 'o')
            
        Returns:
            A unique ID string in the format: type_code:unique_id
        """
        # Generate unique ID component using base62 encoding
        unique_id = self._generate_unique_id()
        
        # Create full ID
        return f"{type_code}:{unique_id}"
    
    def generate_observable_property_id(self, type_code: str, observable_unique_id: str = "0", 
                                        property_name: str = "0", controller_unique_id: str = "0") -> str:
        """
        Generate a unique observable property ID.
        
        Args:
            type_code: Short code indicating property type (e.g., 'op')
            observable_unique_id: ID of parent observable (or "0" if standalone)
            property_name: Name identifier for the property
            controller_unique_id: ID of controlling widget (or "0" if none)
            
        Returns:
            A unique ID string in format: type_code:unique_id:observable_unique_id:property_name:controller_unique_id
        """
        # Generate unique ID component using base62 encoding
        unique_id = self._generate_unique_id()
        
        # Create full ID
        return f"{type_code}:{unique_id}:{observable_unique_id}:{property_name}:{controller_unique_id}"
    
    def create_sub_generator(self) -> 'IDGenerator':
        """
        Create a new ID generator for a subcontainer.
        Each subcontainer has its own generator to ensure stable widget location IDs.
        
        Returns:
            A new IDGenerator instance with a fresh counter
        """
        sub_generator = IDGenerator()
        sub_generator._counter = 0  # Start fresh for this subcontainer
        return sub_generator
    
    def update_id(self, id_string: str, new_container_id: Optional[str] = None, 
                  new_location: Optional[str] = None) -> str:
        """
        Update parts of an existing widget/container ID string.
        
        Args:
            id_string: Existing ID to update
            new_container_id: New container unique ID (or None to keep existing)
            new_location: New location (or None to keep existing)
            
        Returns:
            Updated ID string
        """
        parts = id_string.split(':')
        if len(parts) != 4:
            raise ValueError(f"Invalid widget/container ID format: {id_string}")
            
        type_code = parts[0]
        unique_id = parts[1]
        container_id = new_container_id if new_container_id is not None else parts[2]
        location = new_location if new_location is not None else parts[3]
        
        return f"{type_code}:{unique_id}:{container_id}:{location}"
    
    def update_observable_property_id(self, id_string: str, new_observable_id: Optional[str] = None,
                                     new_property_name: Optional[str] = None, 
                                     new_controller_id: Optional[str] = None) -> str:
        """
        Update parts of an existing observable property ID string.
        
        Args:
            id_string: Existing ID to update
            new_observable_id: New observable unique ID (or None to keep existing)
            new_property_name: New property name (or None to keep existing)
            new_controller_id: New controller unique ID (or None to keep existing)
            
        Returns:
            Updated ID string
        """
        parts = id_string.split(':')
        if len(parts) != 5:
            raise ValueError(f"Invalid observable property ID format: {id_string}")
            
        type_code = parts[0]
        unique_id = parts[1]
        observable_id = new_observable_id if new_observable_id is not None else parts[2]
        property_name = new_property_name if new_property_name is not None else parts[3]
        controller_id = new_controller_id if new_controller_id is not None else parts[4]
        
        return f"{type_code}:{unique_id}:{observable_id}:{property_name}:{controller_id}"
    
    def generate_location_id(self) -> str:
        """
        Generate a unique location ID for a widget within a subcontainer.
        
        Returns:
            Unique location ID string
        """
        return self._generate_unique_id()
    
    def register_existing_id(self, unique_id: str) -> None:
        """
        Register an existing unique ID to avoid future collisions.
        
        Args:
            unique_id: Unique ID string to register
        """
        self._used_ids.add(unique_id)
    
    def _generate_unique_id(self) -> str:
        """
        Generate a unique ID ensuring no collisions with previously used IDs.
        
        Returns:
            A unique base62-encoded string
        """
        while True:
            self._counter += 1
            unique_id = self._encode_to_base62(self._counter)
            if unique_id not in self._used_ids:
                self._used_ids.add(unique_id)
                return unique_id
    
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