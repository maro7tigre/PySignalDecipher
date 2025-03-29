"""
ID registry for managing widget and observable ID mappings.

This module provides a central registry for tracking widgets and observables by their unique IDs,
allowing for reference tracking without maintaining direct object references.
"""
from typing import Dict, Any, List, Optional, Set, TypeVar, Tuple
import weakref

from .generator import IDGenerator
from .utils import (
    extract_unique_id, extract_container_unique_id, extract_location, 
    extract_widget_unique_id, extract_property_name,
    is_observable_id, is_widget_id
)

# Type variables for widgets and observables
T = TypeVar('T')
O = TypeVar('O')

class IDRegistry:
    """
    Central registry for managing ID-to-object mappings.
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
        
        # Widget mappings
        self._widget_to_id_map = {}  # Widget object -> ID string
        self._id_to_widget_map = weakref.WeakValueDictionary()  # ID string -> Widget object (weak reference)
        
        # Observable mappings
        self._observable_to_id_map = {}  # Observable object -> ID string
        self._id_to_observable_map = weakref.WeakValueDictionary()  # ID string -> Observable object (weak reference)
        
        # Binding maps (for tracking widget-observable bindings)
        self._widget_id_to_observable_ids = {}  # Widget ID -> Set of Observable IDs
        self._observable_id_to_widget_ids = {}  # Observable ID -> Set of Widget IDs
        
        # Property bindings
        self._observable_id_to_property_map = {}  # Observable ID -> property name
        
        # ID generator
        self._id_generator = IDGenerator()
    
    # Widget Registration
    def register_widget(self, widget: Any, type_code: str, 
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
        if widget_id and is_widget_id(widget_id):
            # Extract parts
            parts = widget_id.split(':')
            if len(parts) != 4:
                # Invalid format, generate new ID
                container_unique_id = extract_unique_id(container_id) if container_id else "0"
                new_widget_id = self._id_generator.generate_widget_id(type_code, container_unique_id, location or "0")
            else:
                # Update with new container if provided
                container_unique_id = container_id and extract_unique_id(container_id) or None
                new_location = location or None
                new_widget_id = self._id_generator.update_widget_id(widget_id, container_unique_id, new_location)
        else:
            # Generate new ID
            container_unique_id = extract_unique_id(container_id) if container_id else "0"
            new_widget_id = self._id_generator.generate_widget_id(type_code, container_unique_id, location or "0")
        
        # Store mappings
        self._widget_to_id_map[widget] = new_widget_id
        self._id_to_widget_map[new_widget_id] = widget
        
        return new_widget_id
    
    # Observable Registration
    def register_observable(self, observable: Any, 
                            observable_id: Optional[str] = None,
                            widget_id: Optional[str] = None,
                            property_name: str = "") -> str:
        """
        Register an observable with the ID system.
        
        Args:
            observable: Observable object to register
            observable_id: Optional existing ID to use/update
            widget_id: Optional ID of controlling widget
            property_name: Optional property name
            
        Returns:
            Generated or updated observable ID
        """
        # If observable_id is provided, update it
        if observable_id and is_observable_id(observable_id):
            # Extract parts
            parts = observable_id.split(':')
            if len(parts) != 4 or parts[0] != "obs":
                # Invalid format, generate new ID
                widget_unique_id = widget_id and extract_unique_id(widget_id) or "0"
                new_observable_id = self._id_generator.generate_observable_id(widget_unique_id, property_name)
            else:
                # Update with new widget if provided
                widget_unique_id = widget_id and extract_unique_id(widget_id) or None
                new_property_name = property_name if property_name else None
                new_observable_id = self._id_generator.update_observable_id(
                    observable_id, widget_unique_id, new_property_name)
        else:
            # Generate new ID
            widget_unique_id = widget_id and extract_unique_id(widget_id) or "0"
            new_observable_id = self._id_generator.generate_observable_id(widget_unique_id, property_name)
        
        # Store mappings
        self._observable_to_id_map[observable] = new_observable_id
        self._id_to_observable_map[new_observable_id] = observable
        
        # Track property binding if provided
        if property_name:
            self._observable_id_to_property_map[new_observable_id] = property_name
        
        # Track widget binding if provided
        if widget_id:
            self.bind_widget_to_observable(widget_id, new_observable_id)
        
        return new_observable_id
    
    # Binding methods
    def bind_widget_to_observable(self, widget_id: str, observable_id: str) -> None:
        """
        Bind a widget to an observable.
        
        Args:
            widget_id: ID of the widget
            observable_id: ID of the observable
        """
        # Add to widget -> observable mapping
        if widget_id not in self._widget_id_to_observable_ids:
            self._widget_id_to_observable_ids[widget_id] = set()
        self._widget_id_to_observable_ids[widget_id].add(observable_id)
        
        # Add to observable -> widget mapping
        if observable_id not in self._observable_id_to_widget_ids:
            self._observable_id_to_widget_ids[observable_id] = set()
        self._observable_id_to_widget_ids[observable_id].add(widget_id)
        
        # Update the observable ID to include this widget if not already bound
        observable = self._id_to_observable_map.get(observable_id)
        if observable and observable_id in self._observable_to_id_map:
            current_widget_id = extract_widget_unique_id(observable_id)
            if current_widget_id == "0":
                # Not bound to any widget yet, update the ID
                new_widget_unique_id = extract_unique_id(widget_id)
                property_name = extract_property_name(observable_id)
                updated_id = self._id_generator.update_observable_id(
                    observable_id, new_widget_unique_id, property_name)
                
                # Update mappings
                self._observable_to_id_map[observable] = updated_id
                self._id_to_observable_map[updated_id] = observable
                
                # Remove old mapping
                if observable_id in self._id_to_observable_map:
                    del self._id_to_observable_map[observable_id]
                
                # Update binding maps
                self._observable_id_to_widget_ids[updated_id] = self._observable_id_to_widget_ids.pop(observable_id)
                
                for w_id, obs_ids in self._widget_id_to_observable_ids.items():
                    if observable_id in obs_ids:
                        obs_ids.remove(observable_id)
                        obs_ids.add(updated_id)
    
    def unbind_widget_from_observable(self, widget_id: str, observable_id: str) -> None:
        """
        Unbind a widget from an observable.
        
        Args:
            widget_id: ID of the widget
            observable_id: ID of the observable
        """
        # Remove from widget -> observable mapping
        if widget_id in self._widget_id_to_observable_ids:
            self._widget_id_to_observable_ids[widget_id].discard(observable_id)
            if not self._widget_id_to_observable_ids[widget_id]:
                del self._widget_id_to_observable_ids[widget_id]
        
        # Remove from observable -> widget mapping
        if observable_id in self._observable_id_to_widget_ids:
            self._observable_id_to_widget_ids[observable_id].discard(widget_id)
            if not self._observable_id_to_widget_ids[observable_id]:
                del self._observable_id_to_widget_ids[observable_id]
                
                # If this was the controlling widget, update the observable ID
                observable = self._id_to_observable_map.get(observable_id)
                if observable and observable_id in self._observable_to_id_map:
                    current_widget_id = extract_widget_unique_id(observable_id)
                    if current_widget_id == extract_unique_id(widget_id):
                        # This was the controlling widget, clear it
                        property_name = extract_property_name(observable_id)
                        updated_id = self._id_generator.update_observable_id(
                            observable_id, "0", property_name)
                        
                        # Update mappings
                        self._observable_to_id_map[observable] = updated_id
                        self._id_to_observable_map[updated_id] = observable
                        
                        # Remove old mapping
                        if observable_id in self._id_to_observable_map:
                            del self._id_to_observable_map[observable_id]
    
    # Widget retrieval methods
    def get_widget(self, widget_id: str) -> Optional[Any]:
        """
        Get widget by ID.
        
        Args:
            widget_id: Widget ID string
            
        Returns:
            The widget object, or None if not found
        """
        return self._id_to_widget_map.get(widget_id)
    
    def get_widget_id(self, widget: Any) -> Optional[str]:
        """
        Get ID for a widget.
        
        Args:
            widget: Widget object
            
        Returns:
            Widget ID string, or None if widget is not registered
        """
        return self._widget_to_id_map.get(widget)
    
    # Observable retrieval methods
    def get_observable(self, observable_id: str) -> Optional[Any]:
        """
        Get observable by ID.
        
        Args:
            observable_id: Observable ID string
            
        Returns:
            The observable object, or None if not found
        """
        return self._id_to_observable_map.get(observable_id)
    
    def get_observable_id(self, observable: Any) -> Optional[str]:
        """
        Get ID for an observable.
        
        Args:
            observable: Observable object
            
        Returns:
            Observable ID string, or None if observable is not registered
        """
        return self._observable_to_id_map.get(observable)
    
    # Container methods
    def get_container_from_widget_id(self, widget_id: str) -> Optional[Any]:
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
        if not is_widget_id(widget_id):
            return None
            
        container_unique_id = extract_container_unique_id(widget_id)
        if container_unique_id == "0":
            return None
            
        # Find container ID by unique ID
        for w_id in self._id_to_widget_map:
            if extract_unique_id(w_id) == container_unique_id:
                return w_id
                
        return None
    
    # Widget and observable binding queries
    def get_bound_widget_ids(self, observable_id: str) -> List[str]:
        """
        Get all widget IDs bound to this observable.
        
        Args:
            observable_id: Observable ID
            
        Returns:
            List of widget ID strings
        """
        if observable_id in self._observable_id_to_widget_ids:
            return list(self._observable_id_to_widget_ids[observable_id])
        return []
    
    def get_bound_widgets(self, observable_id: str) -> List[Any]:
        """
        Get all widgets bound to this observable.
        
        Args:
            observable_id: Observable ID
            
        Returns:
            List of widget objects
        """
        widget_ids = self.get_bound_widget_ids(observable_id)
        return [self.get_widget(widget_id) for widget_id in widget_ids if self.get_widget(widget_id)]
    
    def get_bound_observable_ids(self, widget_id: str) -> List[str]:
        """
        Get all observable IDs bound to this widget.
        
        Args:
            widget_id: Widget ID
            
        Returns:
            List of observable ID strings
        """
        if widget_id in self._widget_id_to_observable_ids:
            return list(self._widget_id_to_observable_ids[widget_id])
        return []
    
    def get_bound_observables(self, widget_id: str) -> List[Any]:
        """
        Get all observables bound to this widget.
        
        Args:
            widget_id: Widget ID
            
        Returns:
            List of observable objects
        """
        observable_ids = self.get_bound_observable_ids(widget_id)
        return [self.get_observable(obs_id) for obs_id in observable_ids if self.get_observable(obs_id)]
    
    def get_controlling_widget_id(self, observable_id: str) -> Optional[str]:
        """
        Get the controlling widget ID for an observable.
        
        Args:
            observable_id: Observable ID
            
        Returns:
            Widget ID or None if not controlled by any widget
        """
        if not is_observable_id(observable_id):
            return None
            
        widget_unique_id = extract_widget_unique_id(observable_id)
        if widget_unique_id == "0":
            return None
            
        # Find widget ID by unique ID
        for w_id in self._id_to_widget_map:
            if extract_unique_id(w_id) == widget_unique_id:
                return w_id
                
        return None
    
    def get_controlling_widget(self, observable_id: str) -> Optional[Any]:
        """
        Get the controlling widget for an observable.
        
        Args:
            observable_id: Observable ID
            
        Returns:
            Widget object or None if not controlled by any widget
        """
        widget_id = self.get_controlling_widget_id(observable_id)
        if widget_id:
            return self.get_widget(widget_id)
        return None
    
    def get_property_name(self, observable_id: str) -> str:
        """
        Get the property name from an observable ID.
        
        Args:
            observable_id: Observable ID
            
        Returns:
            Property name or empty string if not bound to a property
        """
        if not is_observable_id(observable_id):
            return ""
            
        return extract_property_name(observable_id)
    
    # Container queries
    def get_widget_ids_by_container_id(self, container_id: str) -> List[str]:
        """
        Get all widget IDs that have this container ID.
        
        Args:
            container_id: Container's ID
            
        Returns:
            List of widget ID strings
        """
        if not container_id:
            return []
            
        container_unique_id = extract_unique_id(container_id)
        result = []
        for widget_id in self._id_to_widget_map:
            if is_widget_id(widget_id) and extract_container_unique_id(widget_id) == container_unique_id:
                result.append(widget_id)
        return result
        
    def get_widgets_by_container_id(self, container_id: str) -> List[Any]:
        """
        Get all widgets that have this container ID.
        
        Args:
            container_id: Container's ID
            
        Returns:
            List of widget objects
        """
        widget_ids = self.get_widget_ids_by_container_id(container_id)
        return [self.get_widget(widget_id) for widget_id in widget_ids]
        
    def get_widget_ids_by_container_id_and_location(self, container_id: str, location: str) -> List[str]:
        """
        Get all widget IDs that have this container ID and location.
        
        Args:
            container_id: Container's ID
            location: Location in container
            
        Returns:
            List of widget ID strings
        """
        if not container_id:
            return []
            
        container_unique_id = extract_unique_id(container_id)
        result = []
        for widget_id in self._id_to_widget_map:
            if (is_widget_id(widget_id) and 
                extract_container_unique_id(widget_id) == container_unique_id and 
                extract_location(widget_id) == location):
                result.append(widget_id)
        return result
        
    def get_widgets_by_container_id_and_location(self, container_id: str, location: str) -> List[Any]:
        """
        Get all widgets that have this container ID and location.
        
        Args:
            container_id: Container's ID
            location: Location in container
            
        Returns:
            List of widget objects
        """
        widget_ids = self.get_widget_ids_by_container_id_and_location(container_id, location)
        return [self.get_widget(widget_id) for widget_id in widget_ids]
    
    # ID management methods
    def update_widget_container(self, widget_id: str, new_container_id: Optional[str] = None) -> bool:
        """
        Update the container ID of a widget.
        
        Args:
            widget_id: Widget ID to update
            new_container_id: New container ID (or None to remove container)
            
        Returns:
            True if successfully updated
        """
        if not is_widget_id(widget_id) or widget_id not in self._id_to_widget_map:
            return False
            
        widget = self._id_to_widget_map[widget_id]
        container_unique_id = "0"
        
        if new_container_id:
            container_unique_id = extract_unique_id(new_container_id)
            
        # Update ID
        new_id = self._id_generator.update_widget_id(widget_id, container_unique_id)
        
        # Update mappings
        del self._id_to_widget_map[widget_id]
        self._widget_to_id_map[widget] = new_id
        self._id_to_widget_map[new_id] = widget
        
        # Update any bindings
        if widget_id in self._widget_id_to_observable_ids:
            obs_ids = self._widget_id_to_observable_ids.pop(widget_id)
            self._widget_id_to_observable_ids[new_id] = obs_ids
            
            # Update observable -> widget mappings
            for obs_id in obs_ids:
                if obs_id in self._observable_id_to_widget_ids:
                    self._observable_id_to_widget_ids[obs_id].discard(widget_id)
                    self._observable_id_to_widget_ids[obs_id].add(new_id)
        
        return True
        
    def update_widget_location(self, widget_id: str, new_location: str) -> bool:
        """
        Update the location of a widget.
        
        Args:
            widget_id: Widget ID to update
            new_location: New location value
            
        Returns:
            True if successfully updated
        """
        if not is_widget_id(widget_id) or widget_id not in self._id_to_widget_map:
            return False
            
        widget = self._id_to_widget_map[widget_id]
            
        # Update ID
        new_id = self._id_generator.update_widget_id(widget_id, None, new_location)
        
        # Update mappings
        del self._id_to_widget_map[widget_id]
        self._widget_to_id_map[widget] = new_id
        self._id_to_widget_map[new_id] = widget
        
        # Update any bindings
        if widget_id in self._widget_id_to_observable_ids:
            obs_ids = self._widget_id_to_observable_ids.pop(widget_id)
            self._widget_id_to_observable_ids[new_id] = obs_ids
            
            # Update observable -> widget mappings
            for obs_id in obs_ids:
                if obs_id in self._observable_id_to_widget_ids:
                    self._observable_id_to_widget_ids[obs_id].discard(widget_id)
                    self._observable_id_to_widget_ids[obs_id].add(new_id)
        
        return True
    
    def update_observable_widget(self, observable_id: str, new_widget_id: Optional[str] = None) -> bool:
        """
        Update the controlling widget of an observable.
        
        Args:
            observable_id: Observable ID to update
            new_widget_id: New widget ID (or None to remove widget control)
            
        Returns:
            True if successfully updated
        """
        if not is_observable_id(observable_id) or observable_id not in self._id_to_observable_map:
            return False
            
        observable = self._id_to_observable_map[observable_id]
        widget_unique_id = "0"
        
        if new_widget_id:
            if not is_widget_id(new_widget_id):
                return False
            widget_unique_id = extract_unique_id(new_widget_id)
            
        # Update ID
        property_name = extract_property_name(observable_id)
        new_id = self._id_generator.update_observable_id(observable_id, widget_unique_id, property_name)
        
        # Update mappings
        del self._id_to_observable_map[observable_id]
        self._observable_to_id_map[observable] = new_id
        self._id_to_observable_map[new_id] = observable
        
        # Update any bindings
        if observable_id in self._observable_id_to_widget_ids:
            widget_ids = self._observable_id_to_widget_ids.pop(observable_id)
            self._observable_id_to_widget_ids[new_id] = widget_ids
            
            # Update widget -> observable mappings
            for w_id in widget_ids:
                if w_id in self._widget_id_to_observable_ids:
                    self._widget_id_to_observable_ids[w_id].discard(observable_id)
                    self._widget_id_to_observable_ids[w_id].add(new_id)
        
        # Add binding to new controlling widget if provided
        if new_widget_id:
            self.bind_widget_to_observable(new_widget_id, new_id)
        
        return True
    
    def update_observable_property(self, observable_id: str, new_property_name: str) -> bool:
        """
        Update the property name of an observable.
        
        Args:
            observable_id: Observable ID to update
            new_property_name: New property name
            
        Returns:
            True if successfully updated
        """
        if not is_observable_id(observable_id) or observable_id not in self._id_to_observable_map:
            return False
            
        observable = self._id_to_observable_map[observable_id]
            
        # Update ID
        new_id = self._id_generator.update_observable_id(observable_id, None, new_property_name)
        
        # Update mappings
        del self._id_to_observable_map[observable_id]
        self._observable_to_id_map[observable] = new_id
        self._id_to_observable_map[new_id] = observable
        
        # Update property mapping
        if observable_id in self._observable_id_to_property_map:
            del self._observable_id_to_property_map[observable_id]
        if new_property_name:
            self._observable_id_to_property_map[new_id] = new_property_name
        
        # Update any bindings
        if observable_id in self._observable_id_to_widget_ids:
            widget_ids = self._observable_id_to_widget_ids.pop(observable_id)
            self._observable_id_to_widget_ids[new_id] = widget_ids
            
            # Update widget -> observable mappings
            for w_id in widget_ids:
                if w_id in self._widget_id_to_observable_ids:
                    self._widget_id_to_observable_ids[w_id].discard(observable_id)
                    self._widget_id_to_observable_ids[w_id].add(new_id)
        
        return True
    
    # Unregistration methods
    def unregister_widget(self, widget_or_id: Any) -> bool:
        """
        Unregister a widget or widget ID from the system.
        
        Args:
            widget_or_id: Widget object or ID string to unregister
            
        Returns:
            True if widget was found and unregistered
        """
        widget_id = None
        widget = None
        
        if isinstance(widget_or_id, str):
            # We were given an ID
            widget_id = widget_or_id
            widget = self._id_to_widget_map.get(widget_id)
        else:
            # We were given a widget
            widget = widget_or_id
            widget_id = self._widget_to_id_map.get(widget)
            
        if not widget_id:
            return False
            
        # Clean up any bindings
        if widget_id in self._widget_id_to_observable_ids:
            observable_ids = list(self._widget_id_to_observable_ids[widget_id])
            for obs_id in observable_ids:
                self.unbind_widget_from_observable(widget_id, obs_id)
            
            # Remove the entry
            if widget_id in self._widget_id_to_observable_ids:
                del self._widget_id_to_observable_ids[widget_id]
        
        # Remove from mappings
        if widget and widget in self._widget_to_id_map:
            del self._widget_to_id_map[widget]
        if widget_id in self._id_to_widget_map:
            del self._id_to_widget_map[widget_id]
            
        return True
    
    def unregister_observable(self, observable_or_id: Any) -> bool:
        """
        Unregister an observable or observable ID from the system.
        
        Args:
            observable_or_id: Observable object or ID string to unregister
            
        Returns:
            True if observable was found and unregistered
        """
        observable_id = None
        observable = None
        
        if isinstance(observable_or_id, str):
            # We were given an ID
            observable_id = observable_or_id
            observable = self._id_to_observable_map.get(observable_id)
        else:
            # We were given an observable
            observable = observable_or_id
            observable_id = self._observable_to_id_map.get(observable)
            
        if not observable_id:
            return False
            
        # Clean up any bindings
        if observable_id in self._observable_id_to_widget_ids:
            widget_ids = list(self._observable_id_to_widget_ids[observable_id])
            for w_id in widget_ids:
                self.unbind_widget_from_observable(w_id, observable_id)
            
            # Remove the entry
            if observable_id in self._observable_id_to_widget_ids:
                del self._observable_id_to_widget_ids[observable_id]
        
        # Remove from property mapping
        if observable_id in self._observable_id_to_property_map:
            del self._observable_id_to_property_map[observable_id]
        
        # Remove from mappings
        if observable and observable in self._observable_to_id_map:
            del self._observable_to_id_map[observable]
        if observable_id in self._id_to_observable_map:
            del self._id_to_observable_map[observable_id]
            
        return True
    
    def clear(self) -> None:
        """Clear all registry mappings."""
        self._widget_to_id_map.clear()
        self._id_to_widget_map.clear()
        self._observable_to_id_map.clear()
        self._id_to_observable_map.clear()
        self._widget_id_to_observable_ids.clear()
        self._observable_id_to_widget_ids.clear()
        self._observable_id_to_property_map.clear()