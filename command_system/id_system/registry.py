"""
ID registry for managing widget ID mappings.

This module provides a central registry for tracking widgets by their unique IDs,
allowing for reference tracking without maintaining direct object references.
"""
from typing import Dict, Any, List, Optional, Set, TypeVar
import weakref

from .generator import IDGenerator
from .utils import extract_unique_id, extract_container_unique_id, extract_location

# Type variable for widgets
T = TypeVar('T')

class IDRegistry:
    """
    Central registry for managing ID-to-widget mappings.
    Implemented as a singleton for global access.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance.
        
        Returns:
            IDRegistry singleton instance
        """
        if cls._instance is None:
            cls._instance = IDRegistry()
        return cls._instance
    
    def __init__(self):
        """Initialize the ID registry."""
        if IDRegistry._instance is not None:
            raise RuntimeError("You can't have multiple instances of IDRegistry. Use get_id_registry() to get the singleton instance")
            
        IDRegistry._instance = self
        self._widget_to_id_map = {}  # Widget object -> ID string
        self._id_to_widget_map = weakref.WeakValueDictionary()  # ID string -> Widget object (weak reference)
        self._id_generator = IDGenerator()
    
    def register(self, widget: Any, type_code: str, 
                observable_id: Optional[str] = None, 
                container_id: Optional[str] = None,
                location: Optional[str] = None) -> str:
        """
        Register a widget with the ID system.
        
        Args:
            widget: Widget to register
            type_code: Short code indicating widget type
            observable_id: Optional existing ID to use/update
            container_id: Optional container ID
            location: Optional location in container
            
        Returns:
            Generated or updated widget ID
        """
        # If observable_id is provided, update it
        if observable_id:
            # Extract parts
            parts = observable_id.split(':')
            if len(parts) != 4:
                # Invalid format, generate new ID
                container_unique_id = extract_unique_id(container_id) if container_id else "0"
                widget_id = self._id_generator.generate_id(type_code, container_unique_id, location or "0")
            else:
                # Update with new container if provided
                container_unique_id = container_id and extract_unique_id(container_id) or None
                new_location = location or None
                widget_id = self._id_generator.update_id(observable_id, container_unique_id, new_location)
        else:
            # Generate new ID
            container_unique_id = extract_unique_id(container_id) if container_id else "0"
            widget_id = self._id_generator.generate_id(type_code, container_unique_id, location or "0")
        
        # Store mappings
        self._widget_to_id_map[widget] = widget_id
        self._id_to_widget_map[widget_id] = widget
        
        return widget_id
    
    def get_widget(self, widget_id: str) -> Optional[Any]:
        """
        Get widget by ID.
        
        Args:
            widget_id: ID string
            
        Returns:
            The widget object, or None if not found
        """
        return self._id_to_widget_map.get(widget_id)
    
    def get_id(self, widget: Any) -> Optional[str]:
        """
        Get ID for a widget.
        
        Args:
            widget: Widget object
            
        Returns:
            ID string, or None if widget is not registered
        """
        return self._widget_to_id_map.get(widget)
    
    def get_container_from_id(self, widget_id: str) -> Optional[Any]:
        """
        Get the container widget from a widget ID.
        
        Args:
            widget_id: Widget ID string
            
        Returns:
            Container widget or None if not found
        """
        container_id = self.get_container_id_from_widget_id(widget_id)
        if container_id:
            return self.get_widget(container_id)
        return None
    
    def get_container_id_from_widget_id(self, widget_id: str) -> Optional[str]:
        """
        Get the container's ID from a widget ID.
        
        Args:
            widget_id: Widget ID string
            
        Returns:
            Container ID or None if not found
        """
        container_unique_id = extract_container_unique_id(widget_id)
        if container_unique_id == "0":
            return None
            
        # Find container ID by unique ID
        for w_id in self._id_to_widget_map:
            if extract_unique_id(w_id) == container_unique_id:
                return w_id
                
        return None
    
    def get_unique_id_from_id(self, id_string: str) -> str:
        """
        Extract the unique ID portion from a full ID.
        
        Args:
            id_string: Full ID string
            
        Returns:
            Unique ID portion
        """
        return extract_unique_id(id_string)
    
    def get_full_id_from_unique_id(self, unique_id: str) -> Optional[str]:
        """
        Find the full ID string from a unique ID.
        
        Args:
            unique_id: Unique ID portion
            
        Returns:
            Full ID string or None if not found
        """
        for w_id in self._id_to_widget_map:
            if extract_unique_id(w_id) == unique_id:
                return w_id
                
        return None
    
    def get_widget_ids_by_container_id(self, container_unique_id: str) -> List[str]:
        """
        Get all widget IDs that have this container ID.
        
        Args:
            container_unique_id: Container's unique ID
            
        Returns:
            List of widget ID strings
        """
        result = []
        for widget, widget_id in self._widget_to_id_map.items():
            if extract_container_unique_id(widget_id) == container_unique_id:
                result.append(widget_id)
        return result
        
    def get_widgets_by_container_id(self, container_unique_id: str) -> List[Any]:
        """
        Get all widgets that have this container ID.
        
        Args:
            container_unique_id: Container's unique ID
            
        Returns:
            List of widget objects
        """
        result = []
        for widget, widget_id in self._widget_to_id_map.items():
            if extract_container_unique_id(widget_id) == container_unique_id:
                result.append(widget)
        return result
        
    def get_widget_ids_by_container_id_and_location(self, container_unique_id: str, location: str) -> List[str]:
        """
        Get all widget IDs that have this container ID and location.
        
        Args:
            container_unique_id: Container's unique ID
            location: Location in container
            
        Returns:
            List of widget ID strings
        """
        result = []
        for widget, widget_id in self._widget_to_id_map.items():
            if (extract_container_unique_id(widget_id) == container_unique_id and 
                extract_location(widget_id) == location):
                result.append(widget_id)
        return result
        
    def get_widgets_by_container_id_and_location(self, container_unique_id: str, location: str) -> List[Any]:
        """
        Get all widgets that have this container ID and location.
        
        Args:
            container_unique_id: Container's unique ID
            location: Location in container
            
        Returns:
            List of widget objects
        """
        result = []
        for widget, widget_id in self._widget_to_id_map.items():
            if (extract_container_unique_id(widget_id) == container_unique_id and 
                extract_location(widget_id) == location):
                result.append(widget)
        return result
    
    def update_container_id(self, widget: Any, new_container_id: Optional[str] = None) -> bool:
        """
        Update the container ID of a widget.
        
        Args:
            widget: Widget to update
            new_container_id: New container ID (or None to remove container)
            
        Returns:
            True if successfully updated
        """
        if widget not in self._widget_to_id_map:
            return False
            
        old_id = self._widget_to_id_map[widget]
        container_unique_id = "0"
        
        if new_container_id:
            container_unique_id = extract_unique_id(new_container_id)
            
        # Update ID
        new_id = self._id_generator.update_id(old_id, container_unique_id)
        
        # Update mappings
        del self._id_to_widget_map[old_id]
        self._widget_to_id_map[widget] = new_id
        self._id_to_widget_map[new_id] = widget
        
        return True
        
    def update_location(self, widget: Any, new_location: str) -> bool:
        """
        Update the location of a widget.
        
        Args:
            widget: Widget to update
            new_location: New location value
            
        Returns:
            True if successfully updated
        """
        if widget not in self._widget_to_id_map:
            return False
            
        old_id = self._widget_to_id_map[widget]
            
        # Update ID
        new_id = self._id_generator.update_id(old_id, None, new_location)
        
        # Update mappings
        del self._id_to_widget_map[old_id]
        self._widget_to_id_map[widget] = new_id
        self._id_to_widget_map[new_id] = widget
        
        return True
    
    def remove_container_reference(self, widget_id: str) -> str:
        """
        Remove the container reference from a widget ID.
        
        Args:
            widget_id: Widget ID to update
            
        Returns:
            Updated widget ID
        """
        # TODO: Reconsider this approach
        return self._id_generator.update_id(widget_id, "0")
    
    def unregister(self, widget_or_id: Any) -> bool:
        """
        Unregister a widget or ID from the system.
        
        Args:
            widget_or_id: Widget object or ID string to unregister
            
        Returns:
            True if widget was found and unregistered
        """
        if isinstance(widget_or_id, str):
            # We were given an ID
            widget_id = widget_or_id
            widget = self._id_to_widget_map.get(widget_id)
            
            if widget is None:
                # Widget might have been garbage collected already
                if widget_id in self._id_to_widget_map:
                    del self._id_to_widget_map[widget_id]
                return False
                
            # Remove both mappings
            if widget in self._widget_to_id_map:
                del self._widget_to_id_map[widget]
            if widget_id in self._id_to_widget_map:
                del self._id_to_widget_map[widget_id]
            return True
        else:
            # We were given a widget
            widget = widget_or_id
            if widget not in self._widget_to_id_map:
                return False
                
            widget_id = self._widget_to_id_map[widget]
            
            # Remove both mappings
            del self._widget_to_id_map[widget]
            if widget_id in self._id_to_widget_map:
                del self._id_to_widget_map[widget_id]
            return True


def get_id_registry():
    """
    Get the singleton ID registry instance.
    
    Returns:
        IDRegistry singleton instance
    """
    return IDRegistry.get_instance()