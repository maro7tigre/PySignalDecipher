"""
ID registry for managing component ID mappings.

This module provides a central registry for tracking widgets, containers, observables, 
and observable properties by their unique IDs.
"""
from typing import Dict, Any, List, Optional, TypeVar, Union, Callable, Tuple
import weakref

from .generator import IDGenerator
from .utils import (
    extract_unique_id, extract_container_unique_id, extract_location,
    extract_subcontainer_path, extract_widget_location_id, append_to_location_path,
    extract_observable_unique_id, extract_property_name, extract_controller_unique_id,
    is_widget_id, is_observable_id, is_observable_property_id, is_subcontainer_id
)

# Type variable for components
T = TypeVar('T')

class IDRegistry:
    """
    Central registry for managing ID-to-component mappings.
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
            raise RuntimeError("Use get_id_registry() to get the singleton instance")
            
        IDRegistry._instance = self
        self._component_to_id_map = {}  # Component object -> ID string
        self._id_to_component_map = weakref.WeakValueDictionary()  # ID string -> Component object (weak reference)
        self._id_generator = IDGenerator()
        
        # Store subcontainer ID generators
        self._subcontainer_generators = {}  # subcontainer_id -> IDGenerator
        
        # Store locations map for containers
        self._container_locations_map = {}  # container_id -> {subcontainer_id -> location}
        
        # Callbacks for unregisters
        self._on_widget_unregister = lambda widget_id: None
        self._on_observable_unregister = lambda observable_id: None
        self._on_property_unregister = lambda property_id: None
        
        # ID change signal
        self._on_id_changed = lambda old_id, new_id: None
    
    # Registration methods
    
    def register(self, widget: Any, type_code: str, 
                widget_id: Optional[str] = None, 
                container_id: Optional[str] = None,
                location: Optional[str] = None) -> str:
        """
        Register a widget with the ID system.
        
        Args:
            widget: Widget to register
            type_code: Short code indicating widget type
            widget_id: Optional existing ID to use/update
            container_id: Optional container ID
            location: Optional location in container (subcontainer_location or composite)
            
        Returns:
            Generated or updated widget ID
        """
        # Process location - it can be a simple path segment or a hierarchical path
        final_location = location or "0"
        
        # If container is provided and it's a subcontainer, we need to build a hierarchical path
        if container_id and is_subcontainer_id(container_id):
            # Start with the provided location or "0"
            container_path = location or "0"
            
            # Get or create a generator for this subcontainer
            sub_generator = self._get_subcontainer_generator(container_id)
            
            # Generate a widget location ID
            widget_location_id = extract_unique_id(sub_generator.generate_observable_id("tmp"))
            
            # Create hierarchical location path
            final_location = append_to_location_path(container_path, widget_location_id)
            
            # Update container locations map
            parent_container_id = self.get_container_id_from_widget_id(container_id)
            
            if parent_container_id:
                # Get or initialize locations map for parent container
                if parent_container_id not in self._container_locations_map:
                    self._container_locations_map[parent_container_id] = {}
                
                # Store subcontainer location
                self._container_locations_map[parent_container_id][container_id] = container_path
        
        # If widget_id is provided, update it
        if widget_id:
            # Extract parts
            parts = widget_id.split(':')
            if len(parts) != 4:
                # Invalid format, generate new ID
                container_unique_id = extract_unique_id(container_id) if container_id else "0"
                widget_id = self._id_generator.generate_id(type_code, container_unique_id, final_location)
            else:
                # Update with new container if provided
                container_unique_id = container_id and extract_unique_id(container_id) or None
                new_location = final_location or None
                widget_id = self._id_generator.update_id(widget_id, container_unique_id, new_location)
        else:
            # Generate new ID
            container_unique_id = extract_unique_id(container_id) if container_id else "0"
            widget_id = self._id_generator.generate_id(type_code, container_unique_id, final_location)
        
        # Store mappings
        old_id = self._component_to_id_map.get(widget)
        self._component_to_id_map[widget] = widget_id
        self._id_to_component_map[widget_id] = widget
        
        # If this is a subcontainer, create a subcontainer generator
        if is_subcontainer_id(widget_id) and widget_id not in self._subcontainer_generators:
            self._subcontainer_generators[widget_id] = self._id_generator.create_sub_generator()
        
        # Signal ID change if applicable
        if old_id and old_id != widget_id:
            self._on_id_changed(old_id, widget_id)
        
        return widget_id
    
    def _get_subcontainer_generator(self, subcontainer_id: str) -> IDGenerator:
        """
        Get or create an ID generator for a subcontainer.
        
        Args:
            subcontainer_id: ID of the subcontainer
            
        Returns:
            IDGenerator for the subcontainer
        """
        if subcontainer_id not in self._subcontainer_generators:
            self._subcontainer_generators[subcontainer_id] = self._id_generator.create_sub_generator()
        return self._subcontainer_generators[subcontainer_id]
    
    def get_locations_map(self, container_id: str) -> Dict[str, str]:
        """
        Get the locations map for a container.
        
        Args:
            container_id: Container ID
            
        Returns:
            Dictionary mapping subcontainer IDs to locations
        """
        return self._container_locations_map.get(container_id, {}).copy()
    
    def set_locations_map(self, container_id: str, locations_map: Dict[str, str]) -> None:
        """
        Set the locations map for a container.
        
        Args:
            container_id: Container ID
            locations_map: Dictionary mapping subcontainer IDs to locations
        """
        self._container_locations_map[container_id] = locations_map.copy()
    
    def set_on_id_changed(self, callback: Callable[[str, str], None]) -> None:
        """
        Set callback for ID changes.
        
        Args:
            callback: Function to call when an ID changes (old_id, new_id)
        """
        self._on_id_changed = callback
    
    def get_widgets_at_subcontainer_location(self, container_id: str, subcontainer_location: str) -> List[str]:
        """
        Get all widget IDs at a specific subcontainer location.
        
        Args:
            container_id: Container ID
            subcontainer_location: Location within container
            
        Returns:
            List of widget IDs at the specified location
        """
        widget_ids = []
        
        # Get all widgets in this container
        container_widgets = self.get_widget_ids_by_container_id(container_id)
        
        # Filter by subcontainer location
        for widget_id in container_widgets:
            widget_subcontainer_path = extract_subcontainer_path(widget_id)
            if widget_subcontainer_path == subcontainer_location:
                widget_ids.append(widget_id)
        
        return widget_ids
    
    def get_subcontainer_id_at_location(self, container_id: str, location: str) -> Optional[str]:
        """
        Get the subcontainer ID at a specific location in a container.
        
        Args:
            container_id: Container ID
            location: Location within container
            
        Returns:
            Subcontainer ID or None if not found
        """
        if container_id not in self._container_locations_map:
            return None
            
        # Find subcontainer with the specified location
        for subcontainer_id, subcontainer_location in self._container_locations_map[container_id].items():
            if subcontainer_location == location:
                return subcontainer_id
                
        return None

def get_id_registry():
    """
    Get the singleton ID registry instance.
    
    Returns:
        IDRegistry singleton instance
    """
    return IDRegistry.get_instance()