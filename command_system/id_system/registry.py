"""
ID registry for managing component ID mappings.

This module provides a central registry for tracking widgets, containers, observables, 
and observable properties by their unique IDs.

Implementation based on the documentation in docs/id_system.md.
"""
from typing import Dict, Any, List, Optional, TypeVar, Union, Callable, Tuple, Set
import weakref

from .generator import IDGenerator
from .utils import (
    extract_type_code, extract_unique_id, extract_container_unique_id, extract_location,
    extract_location_parts, extract_subcontainer_path, extract_widget_location_id,
    extract_observable_unique_id, extract_property_name, extract_controller_unique_id,
    create_location_path, append_to_location_path,
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
        
        # Component mapping dictionaries
        self._component_to_id_map = {}  # Component object -> ID string
        self._id_to_component_map = weakref.WeakValueDictionary()  # ID string -> Component object (weak reference)
        
        # ID generator
        self._id_generator = IDGenerator()
        
        # Store subcontainer ID generators
        self._subcontainer_generators = {}  # subcontainer_id -> IDGenerator
        
        # Store locations map for containers
        self._container_locations_map = {}  # container_id -> {subcontainer_id -> location}
        
        # Callbacks for unregisters and changes
        self._on_widget_unregister = lambda widget_id: None
        self._on_observable_unregister = lambda observable_id: None
        self._on_property_unregister = lambda property_id: None
        self._on_id_changed = lambda old_id, new_id: None
    
    # -------------------- Registration methods --------------------
    
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
        final_location = location or "0"
        
        # Process location - determine if we need to generate a widget_location_id
        if container_id and is_subcontainer_id(container_id):
            # Check if location already has a widget_location_id (contains a hyphen)
            if not final_location or final_location == "0" or not ("-" in final_location):
                # We need to generate a widget_location_id
                # Get the subcontainer location part
                subcontainer_location = final_location if final_location != "0" else "0"
                
                # Get or create a generator for this subcontainer
                sub_generator = self._get_subcontainer_generator(container_id)
                
                # Generate a widget location ID
                widget_location_id = extract_unique_id(sub_generator.generate_observable_id("tmp"))
                
                # Create composite location
                final_location = f"{subcontainer_location}-{widget_location_id}"
                
                # Update container locations map
                parent_container_id = self.get_container_id_from_widget_id(container_id)
                
                if parent_container_id:
                    # Get or initialize locations map for parent container
                    if parent_container_id not in self._container_locations_map:
                        self._container_locations_map[parent_container_id] = {}
                    
                    # Store subcontainer location
                    self._container_locations_map[parent_container_id][container_id] = subcontainer_location
        
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
    
    def register_observable(self, observable: Any, type_code: str, 
                          observable_id: Optional[str] = None) -> str:
        """
        Register an observable with the ID system.
        
        Args:
            observable: Observable to register
            type_code: Short code indicating observable type
            observable_id: Optional existing ID to use/update
            
        Returns:
            Generated or updated observable ID
        """
        # If observable_id is provided, use it
        if observable_id:
            # Check if it's a valid format
            parts = observable_id.split(':')
            if len(parts) != 2:
                # Invalid format, generate new ID
                observable_id = self._id_generator.generate_observable_id(type_code)
        else:
            # Generate new ID
            observable_id = self._id_generator.generate_observable_id(type_code)
        
        # Store mappings
        old_id = self._component_to_id_map.get(observable)
        self._component_to_id_map[observable] = observable_id
        self._id_to_component_map[observable_id] = observable
        
        # Signal ID change if applicable
        if old_id and old_id != observable_id:
            self._on_id_changed(old_id, observable_id)
        
        return observable_id
    
    def register_observable_property(self, property: Any, type_code: str,
                                   property_id: Optional[str] = None,
                                   property_name: str = "0",
                                   observable_id: str = "0",
                                   controller_id: Optional[str] = None) -> str:
        """
        Register an observable property with the ID system.
        
        Args:
            property: Property to register
            type_code: Short code indicating property type
            property_id: Optional existing ID to use/update
            property_name: Name of the property
            observable_id: ID of the parent observable
            controller_id: Optional ID of controlling widget
            
        Returns:
            Generated or updated property ID
        """
        # Extract observable unique ID if full ID provided
        observable_unique_id = extract_unique_id(observable_id) if observable_id else "0"
        
        # Extract controller unique ID if full ID provided
        controller_unique_id = "0"
        if controller_id:
            if is_widget_id(controller_id):
                controller_unique_id = extract_unique_id(controller_id)
        
        # If property_id is provided, update it
        if property_id:
            # Check if it's a valid format
            parts = property_id.split(':')
            if len(parts) != 5:
                # Invalid format, generate new ID
                property_id = self._id_generator.generate_observable_property_id(
                    type_code, observable_unique_id, property_name, controller_unique_id)
            else:
                # Update with new values
                property_id = self._id_generator.update_observable_property_id(
                    property_id, observable_unique_id, property_name, controller_unique_id)
        else:
            # Generate new ID
            property_id = self._id_generator.generate_observable_property_id(
                type_code, observable_unique_id, property_name, controller_unique_id)
        
        # Store mappings
        old_id = self._component_to_id_map.get(property)
        self._component_to_id_map[property] = property_id
        self._id_to_component_map[property_id] = property
        
        # Signal ID change if applicable
        if old_id and old_id != property_id:
            self._on_id_changed(old_id, property_id)
        
        return property_id
    
    # -------------------- Subcontainer methods --------------------
    
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
            widget_location = extract_location(widget_id)
            if widget_location.startswith(subcontainer_location) or widget_location.split('-')[0] == subcontainer_location:
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
    
    # -------------------- Lookup methods --------------------
    
    def get_id(self, component: Any) -> Optional[str]:
        """
        Get the ID for a component.
        
        Args:
            component: Component to look up
            
        Returns:
            Component ID or None if not registered
        """
        return self._component_to_id_map.get(component)
    
    def get_widget(self, widget_id: str) -> Optional[Any]:
        """
        Get a widget by its ID.
        
        Args:
            widget_id: Widget ID to look up
            
        Returns:
            Widget or None if not found
        """
        if not is_widget_id(widget_id):
            return None
        return self._id_to_component_map.get(widget_id)
    
    def get_observable(self, observable_id: str) -> Optional[Any]:
        """
        Get an observable by its ID.
        
        Args:
            observable_id: Observable ID to look up
            
        Returns:
            Observable or None if not found
        """
        if not is_observable_id(observable_id):
            return None
        return self._id_to_component_map.get(observable_id)
    
    def get_observable_property(self, property_id: str) -> Optional[Any]:
        """
        Get an observable property by its ID.
        
        Args:
            property_id: Property ID to look up
            
        Returns:
            Observable property or None if not found
        """
        if not is_observable_property_id(property_id):
            return None
        return self._id_to_component_map.get(property_id)
    
    def get_unique_id_from_id(self, id_string: str) -> str:
        """
        Extract the unique ID portion from an ID string.
        
        Args:
            id_string: Full ID string
            
        Returns:
            Unique ID component
        """
        return extract_unique_id(id_string)
    
    def get_full_id_from_unique_id(self, unique_id: str) -> Optional[str]:
        """
        Look up a full ID using just the unique ID portion.
        
        Args:
            unique_id: Unique ID to look up
            
        Returns:
            Full ID string or None if not found
        """
        # Search through all component IDs for a match
        for component_id in self._id_to_component_map.keys():
            if extract_unique_id(component_id) == unique_id:
                return component_id
        return None
    
    # -------------------- Relationship methods --------------------
    
    def get_container_id_from_widget_id(self, widget_id: str) -> Optional[str]:
        """
        Get the container ID for a widget.
        
        Args:
            widget_id: Widget ID
            
        Returns:
            Container ID or None if standalone
        """
        if not is_widget_id(widget_id):
            return None
            
        # Extract container unique ID
        container_unique_id = extract_container_unique_id(widget_id)
        if container_unique_id == "0":
            return None
            
        # Look up full container ID
        return self.get_full_id_from_unique_id(container_unique_id)
    
    def get_widget_ids_by_container_id(self, container_id: str) -> List[str]:
        """
        Get all widget IDs for a container.
        
        Args:
            container_id: Container ID
            
        Returns:
            List of widget IDs in the container
        """
        if not container_id:
            return []
            
        # Extract container unique ID
        container_unique_id = extract_unique_id(container_id)
        
        # Find all widgets with this container
        widget_ids = []
        for component_id in self._id_to_component_map.keys():
            if (is_widget_id(component_id) and 
                extract_container_unique_id(component_id) == container_unique_id):
                widget_ids.append(component_id)
                
        return widget_ids
    
    def get_widget_ids_by_container_id_and_location(self, container_id: str, location: str) -> List[str]:
        """
        Get all widget IDs for a container at a specific location.
        
        Args:
            container_id: Container ID
            location: Location within container
            
        Returns:
            List of widget IDs at the specified location
        """
        if not container_id or not location:
            return []
            
        # Extract container unique ID
        container_unique_id = extract_unique_id(container_id)
        
        # Find all widgets with this container at this location
        widget_ids = []
        for component_id in self._id_to_component_map.keys():
            if (is_widget_id(component_id) and 
                extract_container_unique_id(component_id) == container_unique_id):
                # Check if location matches or starts with the specified location
                widget_location = extract_location(component_id)
                if widget_location == location or widget_location.startswith(f"{location}-"):
                    widget_ids.append(component_id)
                
        return widget_ids
    
    def get_observable_id_from_property_id(self, property_id: str) -> Optional[str]:
        """
        Get the observable ID for a property.
        
        Args:
            property_id: Property ID
            
        Returns:
            Observable ID or None if standalone
        """
        if not is_observable_property_id(property_id):
            return None
            
        # Extract observable unique ID
        observable_unique_id = extract_observable_unique_id(property_id)
        if observable_unique_id == "0":
            return None
            
        # Look up full observable ID
        return self.get_full_id_from_unique_id(observable_unique_id)
    
    def get_property_ids_by_observable_id(self, observable_id: str) -> List[str]:
        """
        Get all property IDs for an observable.
        
        Args:
            observable_id: Observable ID
            
        Returns:
            List of property IDs for the observable
        """
        if not observable_id:
            return []
            
        # Extract observable unique ID
        observable_unique_id = extract_unique_id(observable_id)
        
        # Find all properties with this observable
        property_ids = []
        for component_id in self._id_to_component_map.keys():
            if (is_observable_property_id(component_id) and 
                extract_observable_unique_id(component_id) == observable_unique_id):
                property_ids.append(component_id)
                
        return property_ids
    
    def get_property_ids_by_observable_id_and_property_name(self, observable_id: str, 
                                                         property_name: str) -> List[str]:
        """
        Get all property IDs for an observable with a specific property name.
        
        Args:
            observable_id: Observable ID
            property_name: Property name
            
        Returns:
            List of property IDs matching the criteria
        """
        if not observable_id or not property_name:
            return []
            
        # Extract observable unique ID
        observable_unique_id = extract_unique_id(observable_id)
        
        # Find all properties with this observable and property name
        property_ids = []
        for component_id in self._id_to_component_map.keys():
            if (is_observable_property_id(component_id) and 
                extract_observable_unique_id(component_id) == observable_unique_id and
                extract_property_name(component_id) == property_name):
                property_ids.append(component_id)
                
        return property_ids
    
    def get_controller_id_from_property_id(self, property_id: str) -> Optional[str]:
        """
        Get the controller widget ID for a property.
        
        Args:
            property_id: Property ID
            
        Returns:
            Controller widget ID or None if no controller
        """
        if not is_observable_property_id(property_id):
            return None
            
        # Extract controller unique ID
        controller_unique_id = extract_controller_unique_id(property_id)
        if controller_unique_id == "0":
            return None
            
        # Look up full controller ID
        return self.get_full_id_from_unique_id(controller_unique_id)
    
    def get_property_ids_by_controller_id(self, controller_id: str) -> List[str]:
        """
        Get all property IDs controlled by a widget.
        
        Args:
            controller_id: Controller widget ID
            
        Returns:
            List of property IDs controlled by the widget
        """
        if not controller_id:
            return []
            
        # Extract controller unique ID
        controller_unique_id = extract_unique_id(controller_id)
        
        # Find all properties with this controller
        property_ids = []
        for component_id in self._id_to_component_map.keys():
            if (is_observable_property_id(component_id) and 
                extract_controller_unique_id(component_id) == controller_unique_id):
                property_ids.append(component_id)
                
        return property_ids
    
    # -------------------- Update methods --------------------
    
    def update_container_id(self, widget_id: str, new_container_id: Optional[str]) -> bool:
        """
        Update the container ID for a widget.
        
        Args:
            widget_id: Widget ID to update
            new_container_id: New container ID or None to remove container
            
        Returns:
            True if successful, False otherwise
        """
        if not is_widget_id(widget_id):
            return False
            
        # Get the widget
        widget = self.get_widget(widget_id)
        if not widget:
            return False
            
        # Extract new container unique ID
        container_unique_id = "0"
        if new_container_id:
            container_unique_id = extract_unique_id(new_container_id)
            
        # Preserve the original location
        current_location = extract_location(widget_id)
            
        # Update ID
        updated_widget_id = self._id_generator.update_id(
            widget_id, container_unique_id, current_location)
            
        # Update mappings
        self._component_to_id_map[widget] = updated_widget_id
        self._id_to_component_map[updated_widget_id] = widget
        
        # Remove old ID mapping if different
        if updated_widget_id != widget_id:
            if widget_id in self._id_to_component_map:
                del self._id_to_component_map[widget_id]
            
            # Signal ID change
            self._on_id_changed(widget_id, updated_widget_id)
            
        return True
    
    def update_location(self, widget_id: str, new_location: str) -> bool:
        """
        Update the location for a widget.
        
        Args:
            widget_id: Widget ID to update
            new_location: New location
            
        Returns:
            True if successful, False otherwise
        """
        if not is_widget_id(widget_id):
            return False
            
        # Get the widget
        widget = self.get_widget(widget_id)
        if not widget:
            return False
        
        # Determine container ID
        container_id = self.get_container_id_from_widget_id(widget_id)
        
        # Process location based on whether it has widget_location_id
        final_location = new_location
        
        # If we have a container and the location doesn't include a separator
        if container_id and is_subcontainer_id(container_id) and "-" not in new_location:
            # Need to generate a widget location ID
            sub_generator = self._get_subcontainer_generator(container_id)
            widget_location_id = extract_unique_id(sub_generator.generate_observable_id("tmp"))
            final_location = f"{new_location}-{widget_location_id}"
            
        # Update ID
        updated_widget_id = self._id_generator.update_id(
            widget_id, None, final_location)
            
        # Update mappings
        self._component_to_id_map[widget] = updated_widget_id
        self._id_to_component_map[updated_widget_id] = widget
        
        # Remove old ID mapping if different
        if updated_widget_id != widget_id:
            if widget_id in self._id_to_component_map:
                del self._id_to_component_map[widget_id]
            
            # Signal ID change
            self._on_id_changed(widget_id, updated_widget_id)
            
        return True
    
    def update_observable_id(self, property_id: str, new_observable_id: Optional[str]) -> bool:
        """
        Update the observable ID for a property.
        
        Args:
            property_id: Property ID to update
            new_observable_id: New observable ID or None to remove observable
            
        Returns:
            True if successful, False otherwise
        """
        if not is_observable_property_id(property_id):
            return False
            
        # Get the property
        property = self.get_observable_property(property_id)
        if not property:
            return False
            
        # Extract new observable unique ID
        observable_unique_id = "0"
        if new_observable_id:
            observable_unique_id = extract_unique_id(new_observable_id)
            
        # Update ID
        updated_property_id = self._id_generator.update_observable_property_id(
            property_id, observable_unique_id, None, None)
            
        # Update mappings
        self._component_to_id_map[property] = updated_property_id
        self._id_to_component_map[updated_property_id] = property
        
        # Remove old ID mapping if different
        if updated_property_id != property_id:
            if property_id in self._id_to_component_map:
                del self._id_to_component_map[property_id]
            
            # Signal ID change
            self._on_id_changed(property_id, updated_property_id)
            
        return True
    
    def update_property_name(self, property_id: str, new_property_name: str) -> bool:
        """
        Update the property name for a property.
        
        Args:
            property_id: Property ID to update
            new_property_name: New property name
            
        Returns:
            True if successful, False otherwise
        """
        if not is_observable_property_id(property_id):
            return False
            
        # Get the property
        property = self.get_observable_property(property_id)
        if not property:
            return False
            
        # Update ID
        updated_property_id = self._id_generator.update_observable_property_id(
            property_id, None, new_property_name, None)
            
        # Update mappings
        self._component_to_id_map[property] = updated_property_id
        self._id_to_component_map[updated_property_id] = property
        
        # Remove old ID mapping if different
        if updated_property_id != property_id:
            if property_id in self._id_to_component_map:
                del self._id_to_component_map[property_id]
            
            # Signal ID change
            self._on_id_changed(property_id, updated_property_id)
            
        return True
    
    def update_controller_id(self, property_id: str, new_controller_id: Optional[str]) -> bool:
        """
        Update the controller ID for a property.
        
        Args:
            property_id: Property ID to update
            new_controller_id: New controller ID or None to remove controller
            
        Returns:
            True if successful, False otherwise
        """
        if not is_observable_property_id(property_id):
            return False
            
        # Get the property
        property = self.get_observable_property(property_id)
        if not property:
            return False
            
        # Extract new controller unique ID
        controller_unique_id = "0"
        if new_controller_id:
            controller_unique_id = extract_unique_id(new_controller_id)
            
        # Update ID
        updated_property_id = self._id_generator.update_observable_property_id(
            property_id, None, None, controller_unique_id)
            
        # Update mappings
        self._component_to_id_map[property] = updated_property_id
        self._id_to_component_map[updated_property_id] = property
        
        # Remove old ID mapping if different
        if updated_property_id != property_id:
            if property_id in self._id_to_component_map:
                del self._id_to_component_map[property_id]
            
            # Signal ID change
            self._on_id_changed(property_id, updated_property_id)
            
        return True
    
    def remove_container_reference(self, widget_id: str) -> Optional[str]:
        """
        Remove the container reference from a widget.
        
        Args:
            widget_id: Widget ID to update
            
        Returns:
            Updated widget ID or None if failed
        """
        return self.update_container_id(widget_id, None) and self.get_id(self.get_widget(widget_id))
    
    def remove_observable_reference(self, property_id: str) -> Optional[str]:
        """
        Remove the observable reference from a property.
        
        Args:
            property_id: Property ID to update
            
        Returns:
            Updated property ID or None if failed
        """
        return self.update_observable_id(property_id, None) and self.get_id(self.get_observable_property(property_id))
    
    def remove_controller_reference(self, property_id: str) -> Optional[str]:
        """
        Remove the controller reference from a property.
        
        Args:
            property_id: Property ID to update
            
        Returns:
            Updated property ID or None if failed
        """
        return self.update_controller_id(property_id, None) and self.get_id(self.get_observable_property(property_id))
    
    # -------------------- Unregistration methods --------------------
    
    def unregister(self, component_id: str, replacement_id: Optional[str] = None) -> bool:
        """
        Unregister a component and optionally replace its container.
        
        Args:
            component_id: Component ID to unregister
            replacement_id: Optional container ID to assign child widgets to
            
        Returns:
            True if successful, False otherwise
        """
        # Check if the component exists
        component = None
        if is_widget_id(component_id):
            component = self.get_widget(component_id)
            if not component:
                return False
                
            # Handle container operations
            if is_subcontainer_id(component_id):
                # Get all child widgets
                child_ids = self.get_widget_ids_by_container_id(component_id)
                
                if replacement_id:
                    # Update container for each child
                    for child_id in child_ids:
                        self.update_container_id(child_id, replacement_id)
                else:
                    # Unregister all children without replacement
                    for child_id in child_ids:
                        self.unregister(child_id)
                        
                # Clean up subcontainer generators
                if component_id in self._subcontainer_generators:
                    del self._subcontainer_generators[component_id]
                    
                # Remove from location maps if present
                for container_id, locations_map in self._container_locations_map.items():
                    if component_id in locations_map:
                        del locations_map[component_id]
            
            # Call widget unregister callback
            self._on_widget_unregister(component_id)
                
        elif is_observable_id(component_id):
            component = self.get_observable(component_id)
            if not component:
                return False
                
            # Remove properties that reference this observable
            property_ids = self.get_property_ids_by_observable_id(component_id)
            for property_id in property_ids:
                if replacement_id:
                    # Update observable reference
                    self.update_observable_id(property_id, replacement_id)
                else:
                    # Remove observable reference
                    self.remove_observable_reference(property_id)
                    
            # Call observable unregister callback
            self._on_observable_unregister(component_id)
                
        elif is_observable_property_id(component_id):
            component = self.get_observable_property(component_id)
            if not component:
                return False
                
            # Call property unregister callback
            self._on_property_unregister(component_id)
        
        # Remove component from mappings
        if component:
            del self._component_to_id_map[component]
        
        if component_id in self._id_to_component_map:
            del self._id_to_component_map[component_id]
            
        return True
    
    # -------------------- Callback registration methods --------------------
    
    def set_on_widget_unregister(self, callback: Callable[[str], None]) -> None:
        """
        Set callback for widget unregistration.
        
        Args:
            callback: Function to call when a widget is unregistered (widget_id)
        """
        self._on_widget_unregister = callback
    
    def set_on_observable_unregister(self, callback: Callable[[str], None]) -> None:
        """
        Set callback for observable unregistration.
        
        Args:
            callback: Function to call when an observable is unregistered (observable_id)
        """
        self._on_observable_unregister = callback
    
    def set_on_property_unregister(self, callback: Callable[[str], None]) -> None:
        """
        Set callback for property unregistration.
        
        Args:
            callback: Function to call when a property is unregistered (property_id)
        """
        self._on_property_unregister = callback
    
    def set_on_id_changed(self, callback: Callable[[str, str], None]) -> None:
        """
        Set callback for ID changes.
        
        Args:
            callback: Function to call when an ID changes (old_id, new_id)
        """
        self._on_id_changed = callback
    
def get_id_registry():
    """
    Get the singleton ID registry instance.
    
    Returns:
        IDRegistry singleton instance
    """
    return IDRegistry.get_instance()