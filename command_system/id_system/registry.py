"""
ID registry for managing component ID mappings.

This module provides a central registry for tracking widgets, containers, observables, 
and observable properties by their unique IDs.
"""
from typing import Dict, Any, List, Optional, TypeVar, Union, Callable
import weakref

from .generator import IDGenerator
from .utils import (
    extract_unique_id, extract_container_unique_id, extract_location,
    extract_observable_unique_id, extract_property_name, extract_controller_unique_id,
    is_widget_id, is_observable_id, is_observable_property_id
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
        
        # Callbacks for unregisters
        self._on_widget_unregister = lambda widget_id: None
        self._on_observable_unregister = lambda observable_id: None
        self._on_property_unregister = lambda property_id: None
    
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
            location: Optional location in container
            
        Returns:
            Generated or updated widget ID
        """
        # If widget_id is provided, update it
        if widget_id:
            # Extract parts
            parts = widget_id.split(':')
            if len(parts) != 4:
                # Invalid format, generate new ID
                container_unique_id = extract_unique_id(container_id) if container_id else "0"
                widget_id = self._id_generator.generate_id(type_code, container_unique_id, location or "0")
            else:
                # Update with new container if provided
                container_unique_id = container_id and extract_unique_id(container_id) or None
                new_location = location or None
                widget_id = self._id_generator.update_id(widget_id, container_unique_id, new_location)
        else:
            # Generate new ID
            container_unique_id = extract_unique_id(container_id) if container_id else "0"
            widget_id = self._id_generator.generate_id(type_code, container_unique_id, location or "0")
        
        # Store mappings
        self._component_to_id_map[widget] = widget_id
        self._id_to_component_map[widget_id] = widget
        
        return widget_id
    
    def register_observable(self, observable: Any, type_code: str,
                           observable_id: Optional[str] = None) -> str:
        """
        Register an observable with the ID system.
        
        Args:
            observable: Observable to register
            type_code: Short code indicating observable type
            observable_id: Optional existing ID to use
            
        Returns:
            Generated or existing observable ID
        """
        # If observable_id is provided and valid, use it
        if observable_id and is_observable_id(observable_id):
            # Store mappings
            self._component_to_id_map[observable] = observable_id
            self._id_to_component_map[observable_id] = observable
            return observable_id
        
        # Generate new ID
        observable_id = self._id_generator.generate_observable_id(type_code)
        
        # Store mappings
        self._component_to_id_map[observable] = observable_id
        self._id_to_component_map[observable_id] = observable
        
        return observable_id
    
    def register_observable_property(self, property: Any, type_code: str,
                                    property_id: Optional[str] = None,
                                    property_name: str = "0",
                                    observable_id: Optional[str] = None,
                                    controller_id: Optional[str] = None) -> str:
        """
        Register an observable property with the ID system.
        
        Args:
            property: Property to register
            type_code: Short code indicating property type
            property_id: Optional existing ID to use/update
            property_name: Name of the property
            observable_id: Optional observable ID this property belongs to
            controller_id: Optional controller widget ID
            
        Returns:
            Generated or updated property ID
        """
        observable_unique_id = "0"
        controller_unique_id = "0"
        
        # Extract unique IDs if provided
        if observable_id:
            observable_unique_id = extract_unique_id(observable_id)
        
        if controller_id:
            controller_unique_id = extract_unique_id(controller_id)
        
        # If property_id is provided, update it
        if property_id and is_observable_property_id(property_id):
            # Update with new values if provided
            property_id = self._id_generator.update_observable_property_id(
                property_id, 
                observable_unique_id if observable_id else None,
                property_name if property_name != "0" else None,
                controller_unique_id if controller_id else None
            )
        else:
            # Generate new ID
            property_id = self._id_generator.generate_observable_property_id(
                type_code, observable_unique_id, property_name, controller_unique_id
            )
        
        # Store mappings
        self._component_to_id_map[property] = property_id
        self._id_to_component_map[property_id] = property
        
        return property_id
    
    # Component retrieval methods
    
    def get_widget(self, widget_id: str) -> Optional[Any]:
        """
        Get widget by ID.
        
        Args:
            widget_id: ID string
            
        Returns:
            The widget object, or None if not found
        """
        if not is_widget_id(widget_id):
            return None
        return self._id_to_component_map.get(widget_id)
    
    def get_observable(self, observable_id: str) -> Optional[Any]:
        """
        Get observable by ID.
        
        Args:
            observable_id: ID string
            
        Returns:
            The observable object, or None if not found
        """
        if not is_observable_id(observable_id):
            return None
        return self._id_to_component_map.get(observable_id)
    
    def get_observable_property(self, property_id: str) -> Optional[Any]:
        """
        Get observable property by ID.
        
        Args:
            property_id: ID string
            
        Returns:
            The property object, or None if not found
        """
        if not is_observable_property_id(property_id):
            return None
        return self._id_to_component_map.get(property_id)
    
    def get_id(self, component: Any) -> Optional[str]:
        """
        Get ID for a component.
        
        Args:
            component: Component object
            
        Returns:
            ID string, or None if component is not registered
        """
        return self._component_to_id_map.get(component)
    
    # ID extraction methods
    
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
        for component_id in self._id_to_component_map:
            if extract_unique_id(component_id) == unique_id:
                return component_id
        return None
    
    # ID-based relationship queries
    
    def get_container_id_from_widget_id(self, widget_id: str) -> Optional[str]:
        """
        Get the container's ID from a widget ID.
        
        Args:
            widget_id: Widget ID string
            
        Returns:
            Container ID or None if not found
        """
        if not is_widget_id(widget_id):
            return None
            
        container_unique_id = extract_container_unique_id(widget_id)
        if container_unique_id == "0":
            return None
            
        # Find container ID by unique ID
        for component_id in self._id_to_component_map:
            if (is_widget_id(component_id) and 
                extract_unique_id(component_id) == container_unique_id):
                return component_id
                
        return None
    
    def get_widget_ids_by_container_id(self, container_id: str) -> List[str]:
        """
        Get all widget IDs that have this container ID.
        
        Args:
            container_id: Container's ID
            
        Returns:
            List of widget ID strings
        """
        if not is_widget_id(container_id):
            return []
            
        container_unique_id = extract_unique_id(container_id)
        result = []
        
        for component_id in self._id_to_component_map:
            if (is_widget_id(component_id) and 
                extract_container_unique_id(component_id) == container_unique_id):
                result.append(component_id)
                
        return result
        
    def get_widget_ids_by_container_id_and_location(self, container_id: str, location: str) -> List[str]:
        """
        Get all widget IDs that have this container ID and location.
        
        Args:
            container_id: Container's ID
            location: Location in container
            
        Returns:
            List of widget ID strings
        """
        if not is_widget_id(container_id):
            return []
            
        container_unique_id = extract_unique_id(container_id)
        result = []
        
        for component_id in self._id_to_component_map:
            if (is_widget_id(component_id) and 
                extract_container_unique_id(component_id) == container_unique_id and
                extract_location(component_id) == location):
                result.append(component_id)
                
        return result
    
    def get_observable_id_from_property_id(self, property_id: str) -> Optional[str]:
        """
        Get the observable's ID from a property ID.
        
        Args:
            property_id: Property ID string
            
        Returns:
            Observable ID or None if not found
        """
        if not is_observable_property_id(property_id):
            return None
            
        observable_unique_id = extract_observable_unique_id(property_id)
        if observable_unique_id == "0":
            return None
            
        # Find observable ID by unique ID
        for component_id in self._id_to_component_map:
            if (is_observable_id(component_id) and 
                extract_unique_id(component_id) == observable_unique_id):
                return component_id
                
        return None
    
    def get_property_ids_by_observable_id(self, observable_id: str) -> List[str]:
        """
        Get all property IDs that belong to this observable ID.
        
        Args:
            observable_id: Observable's ID
            
        Returns:
            List of property ID strings
        """
        if not is_observable_id(observable_id):
            return []
            
        observable_unique_id = extract_unique_id(observable_id)
        result = []
        
        for component_id in self._id_to_component_map:
            if (is_observable_property_id(component_id) and 
                extract_observable_unique_id(component_id) == observable_unique_id):
                result.append(component_id)
                
        return result
    
    def get_property_ids_by_observable_id_and_property_name(self, observable_id: str, property_name: str) -> List[str]:
        """
        Get all property IDs that belong to this observable ID with the specified name.
        
        Args:
            observable_id: Observable's ID
            property_name: Property name
            
        Returns:
            List of property ID strings
        """
        if not is_observable_id(observable_id):
            return []
            
        observable_unique_id = extract_unique_id(observable_id)
        result = []
        
        for component_id in self._id_to_component_map:
            if (is_observable_property_id(component_id) and 
                extract_observable_unique_id(component_id) == observable_unique_id and
                extract_property_name(component_id) == property_name):
                result.append(component_id)
                
        return result
    
    def get_controller_id_from_property_id(self, property_id: str) -> Optional[str]:
        """
        Get the controller's ID from a property ID.
        
        Args:
            property_id: Property ID string
            
        Returns:
            Controller ID or None if not found
        """
        if not is_observable_property_id(property_id):
            return None
            
        controller_unique_id = extract_controller_unique_id(property_id)
        if controller_unique_id == "0":
            return None
            
        # Find controller ID by unique ID
        for component_id in self._id_to_component_map:
            if (is_widget_id(component_id) and 
                extract_unique_id(component_id) == controller_unique_id):
                return component_id
                
        return None
    
    def get_property_ids_by_controller_id(self, controller_id: str) -> List[str]:
        """
        Get all property IDs that are controlled by this widget ID.
        
        Args:
            controller_id: Controller's ID
            
        Returns:
            List of property ID strings
        """
        if not is_widget_id(controller_id):
            return []
            
        controller_unique_id = extract_unique_id(controller_id)
        result = []
        
        for component_id in self._id_to_component_map:
            if (is_observable_property_id(component_id) and 
                extract_controller_unique_id(component_id) == controller_unique_id):
                result.append(component_id)
                
        return result
    
    # ID update methods
    
    def update_container_id(self, widget_id: str, new_container_id: Optional[str] = None) -> bool:
        """
        Update the container ID of a widget.
        
        Args:
            widget_id: Widget ID to update
            new_container_id: New container ID (or None to remove container)
            
        Returns:
            True if successfully updated
        """
        if not is_widget_id(widget_id) or widget_id not in self._id_to_component_map:
            return False
            
        container_unique_id = "0"
        
        if new_container_id:
            container_unique_id = extract_unique_id(new_container_id)
            
        # Update ID
        widget = self._id_to_component_map[widget_id]
        new_id = self._id_generator.update_id(widget_id, container_unique_id)
        
        # Update mappings
        del self._id_to_component_map[widget_id]
        self._component_to_id_map[widget] = new_id
        self._id_to_component_map[new_id] = widget
        
        return True
    
    def update_location(self, widget_id: str, new_location: str) -> bool:
        """
        Update the location of a widget.
        
        Args:
            widget_id: Widget ID to update
            new_location: New location value
            
        Returns:
            True if successfully updated
        """
        if not is_widget_id(widget_id) or widget_id not in self._id_to_component_map:
            return False
            
        # Update ID
        widget = self._id_to_component_map[widget_id]
        new_id = self._id_generator.update_id(widget_id, None, new_location)
        
        # Update mappings
        del self._id_to_component_map[widget_id]
        self._component_to_id_map[widget] = new_id
        self._id_to_component_map[new_id] = widget
        
        return True
    
    def update_observable_id(self, property_id: str, new_observable_id: Optional[str] = None) -> bool:
        """
        Update the observable ID of a property.
        
        Args:
            property_id: Property ID to update
            new_observable_id: New observable ID (or None to remove observable)
            
        Returns:
            True if successfully updated
        """
        if not is_observable_property_id(property_id) or property_id not in self._id_to_component_map:
            return False
            
        observable_unique_id = "0"
        
        if new_observable_id:
            observable_unique_id = extract_unique_id(new_observable_id)
            
        # Update ID
        property = self._id_to_component_map[property_id]
        new_id = self._id_generator.update_observable_property_id(property_id, observable_unique_id)
        
        # Update mappings
        del self._id_to_component_map[property_id]
        self._component_to_id_map[property] = new_id
        self._id_to_component_map[new_id] = property
        
        return True
    
    def update_property_name(self, property_id: str, new_property_name: str) -> bool:
        """
        Update the property name of a property.
        
        Args:
            property_id: Property ID to update
            new_property_name: New property name
            
        Returns:
            True if successfully updated
        """
        if not is_observable_property_id(property_id) or property_id not in self._id_to_component_map:
            return False
            
        # Update ID
        property = self._id_to_component_map[property_id]
        new_id = self._id_generator.update_observable_property_id(property_id, None, new_property_name)
        
        # Update mappings
        del self._id_to_component_map[property_id]
        self._component_to_id_map[property] = new_id
        self._id_to_component_map[new_id] = property
        
        return True
    
    def update_controller_id(self, property_id: str, new_controller_id: Optional[str] = None) -> bool:
        """
        Update the controller ID of a property.
        
        Args:
            property_id: Property ID to update
            new_controller_id: New controller ID (or None to remove controller)
            
        Returns:
            True if successfully updated
        """
        if not is_observable_property_id(property_id) or property_id not in self._id_to_component_map:
            return False
            
        controller_unique_id = "0"
        
        if new_controller_id:
            controller_unique_id = extract_unique_id(new_controller_id)
            
        # Update ID
        property = self._id_to_component_map[property_id]
        new_id = self._id_generator.update_observable_property_id(property_id, None, None, controller_unique_id)
        
        # Update mappings
        del self._id_to_component_map[property_id]
        self._component_to_id_map[property] = new_id
        self._id_to_component_map[new_id] = property
        
        return True
    
    def remove_container_reference(self, widget_id: str) -> str:
        """
        Remove the container reference from a widget ID.
        
        Args:
            widget_id: Widget ID to update
            
        Returns:
            Updated widget ID
        """
        if not is_widget_id(widget_id):
            return widget_id
            
        # Remove container reference (set to "0")
        return self.update_container_id(widget_id, None) and widget_id or ""
    
    def remove_observable_reference(self, property_id: str) -> str:
        """
        Remove the observable reference from a property ID.
        
        Args:
            property_id: Property ID to update
            
        Returns:
            Updated property ID
        """
        if not is_observable_property_id(property_id):
            return property_id
            
        # Remove observable reference (set to "0")
        return self.update_observable_id(property_id, None) and property_id or ""
    
    def remove_controller_reference(self, property_id: str) -> str:
        """
        Remove the controller reference from a property ID.
        
        Args:
            property_id: Property ID to update
            
        Returns:
            Updated property ID
        """
        if not is_observable_property_id(property_id):
            return property_id
            
        # Remove controller reference (set to "0")
        return self.update_controller_id(property_id, None) and property_id or ""
    
    # Unregistration methods
    
    def unregister(self, component_id: str, replacement_id: Optional[str] = None) -> bool:
        """
        Unregister a component by ID from the system.
        
        Args:
            component_id: ID string to unregister
            replacement_id: Optional replacement ID for dependent components
            
        Returns:
            True if component was found and unregistered
        """
        component = self._id_to_component_map.get(component_id)
        
        # Check if the component exists
        if component is None:
            # Component might have been garbage collected already
            if component_id in self._id_to_component_map:
                del self._id_to_component_map[component_id]
            return False
        
        # Handle different component types
        if is_widget_id(component_id):
            # For containers, update or unregister contained widgets
            container_unique_id = extract_unique_id(component_id)
            child_ids = self.get_widget_ids_by_container_id(component_id)
            
            for child_id in child_ids:
                if replacement_id:
                    # Update container reference
                    self.update_container_id(child_id, replacement_id)
                else:
                    # Unregister child
                    self.unregister(child_id)
            
            # Check for any properties controlled by this widget
            controlled_property_ids = self.get_property_ids_by_controller_id(component_id)
            
            for property_id in controlled_property_ids:
                # Just remove the controller reference
                self.remove_controller_reference(property_id)
            
            # Trigger callback
            self._on_widget_unregister(component_id)
            
        elif is_observable_id(component_id):
            # For observables, update or unregister properties
            observable_unique_id = extract_unique_id(component_id)
            property_ids = self.get_property_ids_by_observable_id(component_id)
            
            for property_id in property_ids:
                if replacement_id:
                    # Update observable reference
                    self.update_observable_id(property_id, replacement_id)
                else:
                    # Unregister property
                    self.unregister(property_id)
            
            # Trigger callback
            self._on_observable_unregister(component_id)
            
        elif is_observable_property_id(component_id):
            # Trigger callback
            self._on_property_unregister(component_id)
        
        # Remove component mappings
        if component in self._component_to_id_map:
            del self._component_to_id_map[component]
        if component_id in self._id_to_component_map:
            del self._id_to_component_map[component_id]
            
        return True
    
    # Callback setters
    
    def set_on_widget_unregister(self, callback: Callable[[str], None]) -> None:
        """
        Set callback for widget unregistration.
        
        Args:
            callback: Function to call when a widget is unregistered
        """
        self._on_widget_unregister = callback
    
    def set_on_observable_unregister(self, callback: Callable[[str], None]) -> None:
        """
        Set callback for observable unregistration.
        
        Args:
            callback: Function to call when an observable is unregistered
        """
        self._on_observable_unregister = callback
    
    def set_on_property_unregister(self, callback: Callable[[str], None]) -> None:
        """
        Set callback for property unregistration.
        
        Args:
            callback: Function to call when a property is unregistered
        """
        self._on_property_unregister = callback


def get_id_registry():
    """
    Get the singleton ID registry instance.
    
    Returns:
        IDRegistry singleton instance
    """
    return IDRegistry.get_instance()