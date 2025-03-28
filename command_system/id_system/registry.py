"""
ID registry for managing widget and observable ID mappings.

This module provides a central registry for tracking widgets and observables by their unique IDs,
allowing for reference tracking without maintaining direct object references.
"""
from typing import Dict, Any, List, Optional, Set, TypeVar, Tuple, Union
import weakref

from .generator import IDGenerator
from .utils import (
    extract_type_code, extract_unique_id, extract_container_unique_id, extract_location, 
    extract_widget_unique_id, extract_property_name,
    is_observable_id, is_widget_id, is_property_id,
    extract_observable_id_from_property_id
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
        
        # Property mappings
        self._property_registry = {}  # Property ID -> Dict with property info
        self._observable_id_to_property_ids = {}  # Observable ID -> Set of Property IDs
        self._widget_id_to_property_ids = {}  # Widget ID -> Set of Property IDs
        
        # ID generator
        self._id_generator = IDGenerator()
    
    # Widget Registration and Management
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
    
    def get_widget(self, widget_id: Optional[str] = None, 
                  container_id: Optional[str] = None, 
                  location: Optional[str] = None,
                  type_code: Optional[str] = None) -> Union[Any, List[Any]]:
        """
        Get widget(s) with flexible filtering.
        
        Args:
            widget_id: Get specific widget by ID
            container_id: Get widgets in container
            location: Get widgets at location
            type_code: Get widgets of specific type
            
        Returns:
            Single widget if widget_id provided, otherwise list of widgets matching criteria
        """
        # Direct widget lookup by ID
        if widget_id is not None and container_id is None and location is None and type_code is None:
            return self._id_to_widget_map.get(widget_id)
            
        # Create a result set (will be filtered by each criteria)
        all_widget_ids = list(self._id_to_widget_map.keys())
        matching_ids = []
        
        # Apply filters based on provided parameters
        for wid in all_widget_ids:
            # Skip if not a widget ID
            if not is_widget_id(wid):
                continue
                
            # Check each criteria, if any doesn't match, skip this widget
            if type_code is not None and extract_type_code(wid) != type_code:
                continue
                
            if container_id is not None:
                container_unique_id = extract_unique_id(container_id)
                if extract_container_unique_id(wid) != container_unique_id:
                    continue
                    
            if location is not None and extract_location(wid) != location:
                continue
                
            # All criteria matched, add to results
            matching_ids.append(wid)
            
        # Return single widget if widget_id provided, otherwise list of widgets
        if widget_id is not None:
            return self._id_to_widget_map.get(widget_id)
            
        # Return all matching widgets
        return [self._id_to_widget_map[wid] for wid in matching_ids]
    
    def get_widget_id(self, widget: Optional[Any] = None, 
                     container_id: Optional[str] = None,
                     location: Optional[str] = None,
                     type_code: Optional[str] = None) -> Union[str, List[str]]:
        """
        Get widget ID(s) with flexible filtering.
        
        Args:
            widget: Get ID for specific widget object
            container_id: Get IDs for widgets in container
            location: Get IDs for widgets at location
            type_code: Get IDs for widgets of specific type
            
        Returns:
            Single ID if widget provided, otherwise list of IDs matching criteria
        """
        # Direct widget ID lookup
        if widget is not None and container_id is None and location is None and type_code is None:
            return self._widget_to_id_map.get(widget)
            
        # Use get_widget to find matching widgets, then extract IDs
        if widget is None:
            matched_widgets = self.get_widget(None, container_id, location, type_code)
            return [self._widget_to_id_map[w] for w in matched_widgets if w in self._widget_to_id_map]
        
        return self._widget_to_id_map.get(widget)
    
    def update_widget(self, widget_id: str, 
                     container_id: Optional[str] = None,
                     location: Optional[str] = None) -> bool:
        """
        Update widget properties.
        
        Args:
            widget_id: ID of widget to update
            container_id: New container ID (optional)
            location: New location (optional)
            
        Returns:
            True if update was successful
        """
        # Update container if provided
        if container_id is not None:
            if not self.update_widget_container(widget_id, container_id):
                return False
                
        # Update location if provided
        if location is not None:
            if not self.update_widget_location(widget_id, location):
                return False
                
        return True
    
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
        
        # Clean up any property bindings
        if widget_id in self._widget_id_to_property_ids:
            property_ids = list(self._widget_id_to_property_ids[widget_id])
            for prop_id in property_ids:
                self.unbind_widget(prop_id, widget_id)
            
            # Remove the entry
            if widget_id in self._widget_id_to_property_ids:
                del self._widget_id_to_property_ids[widget_id]
        
        # Remove from mappings
        if widget and widget in self._widget_to_id_map:
            del self._widget_to_id_map[widget]
        if widget_id in self._id_to_widget_map:
            del self._id_to_widget_map[widget_id]
            
        return True
    
    # Container Methods
    def get_container(self, widget_id: Optional[str] = None, 
                     container_id: Optional[str] = None) -> Optional[Any]:
        """
        Get container for a widget or by container ID.
        
        Args:
            widget_id: Get container for this widget
            container_id: Get container directly by ID
            
        Returns:
            Container widget or None
        """
        if container_id is not None:
            return self.get_widget(container_id)
            
        if widget_id is not None:
            return self.get_container_from_widget_id(widget_id)
            
        return None
        
    def get_container_id(self, widget_id: Optional[str] = None, 
                        container: Optional[Any] = None) -> Optional[str]:
        """
        Get container ID for a widget or from container.
        
        Args:
            widget_id: Get container ID for this widget
            container: Get ID from container object
            
        Returns:
            Container ID or None
        """
        if container is not None:
            return self.get_widget_id(container)
            
        if widget_id is not None:
            return self.get_container_id_from_widget_id(widget_id)
            
        return None
    
    # Observable Registration and Management
    def register_observable(self, observable: Any, 
                           observable_id: Optional[str] = None,
                           parent_id: Optional[str] = None,
                           container_id: Optional[str] = None) -> str:
        """
        Register an observable with the ID system.
        
        Args:
            observable: Observable object to register
            observable_id: Optional existing ID to use/update
            parent_id: Optional ID of parent (controlling) widget/observable
            container_id: Optional container ID (alternative to parent_id)
            
        Returns:
            Generated or updated observable ID
        """
        # Use parent_id if provided, otherwise use container_id
        widget_id = parent_id or container_id
        
        # If observable_id is provided, update it
        if observable_id and is_observable_id(observable_id):
            # Extract parts
            parts = observable_id.split(':')
            if len(parts) != 4 or parts[0] != "obs":
                # Invalid format, generate new ID
                widget_unique_id = widget_id and extract_unique_id(widget_id) or "0"
                property_name = ""
                new_observable_id = self._id_generator.generate_observable_id(widget_unique_id, property_name)
            else:
                # Update with new widget if provided
                widget_unique_id = widget_id and extract_unique_id(widget_id) or None
                property_name = None  # Keep existing property name
                new_observable_id = self._id_generator.update_observable_id(
                    observable_id, widget_unique_id, property_name)
        else:
            # Generate new ID
            widget_unique_id = widget_id and extract_unique_id(widget_id) or "0"
            property_name = ""
            new_observable_id = self._id_generator.generate_observable_id(widget_unique_id, property_name)
        
        # Store mappings
        self._observable_to_id_map[observable] = new_observable_id
        self._id_to_observable_map[new_observable_id] = observable
        
        # Track widget binding if provided
        if widget_id:
            self.bind_widget_to_observable(widget_id, new_observable_id)
        
        return new_observable_id
    
    def get_observable(self, observable_id: Optional[str] = None, 
                      parent_id: Optional[str] = None,
                      property_id: Optional[str] = None) -> Union[Any, List[Any]]:
        """
        Get observable(s) with flexible filtering.
        
        Args:
            observable_id: Get specific observable by ID
            parent_id: Get observables for this parent
            property_id: Get observable for this property
            
        Returns:
            Single observable if observable_id provided, otherwise list of observables matching criteria
        """
        # Direct observable lookup by ID
        if observable_id is not None:
            return self._id_to_observable_map.get(observable_id)
            
        # If property_id provided, find the observable that owns this property
        if property_id is not None and is_property_id(property_id):
            observable_id = extract_observable_id_from_property_id(property_id)
            if observable_id:
                return self._id_to_observable_map.get(observable_id)
            return None
            
        # Find observables with parent_id
        if parent_id is not None:
            parent_unique_id = extract_unique_id(parent_id)
            
            result = []
            for obs_id, obs in self._id_to_observable_map.items():
                if is_observable_id(obs_id) and extract_widget_unique_id(obs_id) == parent_unique_id:
                    result.append(obs)
                    
            return result
            
        # If no criteria provided, return all observables
        return list(self._id_to_observable_map.values())
    
    def get_observable_id(self, observable: Optional[Any] = None, 
                         parent_id: Optional[str] = None,
                         property_name: Optional[str] = None) -> Union[str, List[str]]:
        """
        Get observable ID(s) with flexible filtering.
        
        Args:
            observable: Get ID for specific observable object
            parent_id: Get IDs for observables with this parent
            property_name: Get IDs for observables with this property name
            
        Returns:
            Single ID if observable provided, otherwise list of IDs matching criteria
        """
        # Direct observable ID lookup
        if observable is not None:
            return self._observable_to_id_map.get(observable)
            
        result = []
        
        # Find observables matching parent_id and/or property_name
        for obs_id in self._id_to_observable_map:
            if not is_observable_id(obs_id):
                continue
                
            # Check parent_id if provided
            if parent_id is not None:
                parent_unique_id = extract_unique_id(parent_id)
                if extract_widget_unique_id(obs_id) != parent_unique_id:
                    continue
                    
            # Check property_name if provided
            if property_name is not None and extract_property_name(obs_id) != property_name:
                continue
                
            # All criteria matched
            result.append(obs_id)
            
        return result
    
    def update_observable(self, observable_id: str, 
                         parent_id: Optional[str] = None,
                         container_id: Optional[str] = None) -> bool:
        """
        Update observable properties.
        
        Args:
            observable_id: ID of observable to update
            parent_id: New parent ID (optional)
            container_id: New container ID (optional, alternative to parent_id)
            
        Returns:
            True if update was successful
        """
        # Use parent_id if provided, otherwise use container_id
        widget_id = parent_id or container_id
        
        if widget_id is not None:
            return self.update_observable_widget(observable_id, widget_id)
            
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
        
        # Clean up any property bindings
        if observable_id in self._observable_id_to_property_ids:
            property_ids = list(self._observable_id_to_property_ids[observable_id])
            for prop_id in property_ids:
                self.unregister_property(prop_id)
                
            # Remove the entry
            if observable_id in self._observable_id_to_property_ids:
                del self._observable_id_to_property_ids[observable_id]
        
        # Remove from mappings
        if observable and observable in self._observable_to_id_map:
            del self._observable_to_id_map[observable]
        if observable_id in self._id_to_observable_map:
            del self._id_to_observable_map[observable_id]
            
        return True
    
    # Property Methods
    def register_property(self, property_name: str, 
                         observable_id: Optional[str] = None,
                         observable_property: Optional[Any] = None,
                         widget_id: Optional[str] = None) -> str:
        """
        Register a property with the ID system.
        
        Args:
            property_name: Name of the property
            observable_id: Observable ID that owns this property (optional)
            observable_property: Observable property object (optional)
            widget_id: ID of widget to bind to property (optional)
            
        Returns:
            Generated property ID
        """
        if observable_id is None and observable_property is None:
            raise ValueError("Either observable_id or observable_property must be provided")
            
        # If we have the property object but not the ID, try to get the observable from it
        if observable_id is None and observable_property is not None:
            observable = getattr(observable_property, "observable", None)
            if observable is None:
                raise ValueError("Observable property does not have a reference to its observable")
                
            # Get or register the observable
            observable_id = self.get_observable_id(observable)
            if observable_id is None:
                observable_id = self.register_observable(observable)
        
        # Create property ID
        property_id = f"{observable_id}:{property_name}"
        
        # Store in property registry
        self._property_registry[property_id] = {
            "observable_id": observable_id,
            "property_name": property_name,
            "bound_widgets": set(),
            "is_controller": {}  # Widget ID -> bool (True if widget is controller)
        }
        
        # Add to observable's property set
        if observable_id not in self._observable_id_to_property_ids:
            self._observable_id_to_property_ids[observable_id] = set()
        self._observable_id_to_property_ids[observable_id].add(property_id)
        
        # Bind widget if provided
        if widget_id is not None:
            self.bind_widget(property_id, widget_id)
            
        return property_id
    
    def get_property(self, property_id: Optional[str] = None,
                   observable_id: Optional[str] = None,
                   property_name: Optional[str] = None,
                   widget_id: Optional[str] = None) -> Union[Dict, List[Dict], None]:
        """
        Get property with flexible filtering.
        
        Args:
            property_id: Get specific property by ID
            observable_id: Get properties for observable
            property_name: Get property with this name (used with observable_id)
            widget_id: Get properties bound to widget
            
        Returns:
            Property dict, list of property dicts, or None
        """
        # Direct property lookup by ID
        if property_id is not None:
            return self._property_registry.get(property_id)
            
        result = []
        
        # Get by observable_id + property_name
        if observable_id is not None and property_name is not None:
            prop_id = f"{observable_id}:{property_name}"
            if prop_id in self._property_registry:
                return self._property_registry[prop_id]
            return None
            
        # Get all properties for observable
        if observable_id is not None:
            if observable_id in self._observable_id_to_property_ids:
                prop_ids = self._observable_id_to_property_ids[observable_id]
                return [self._property_registry[pid] for pid in prop_ids if pid in self._property_registry]
            return []
            
        # Get all properties bound to widget
        if widget_id is not None:
            if widget_id in self._widget_id_to_property_ids:
                prop_ids = self._widget_id_to_property_ids[widget_id]
                return [self._property_registry[pid] for pid in prop_ids if pid in self._property_registry]
            return []
            
        # Return all properties if no criteria provided
        return list(self._property_registry.values())
    
    def get_property_id(self, observable_id: Optional[str] = None,
                       property_name: Optional[str] = None,
                       observable_property: Optional[Any] = None) -> Union[str, List[str], None]:
        """
        Get property ID with flexible filtering.
        
        Args:
            observable_id: Observable ID that owns the property
            property_name: Name of the property (used with observable_id)
            observable_property: Observable property object
            
        Returns:
            Property ID, list of property IDs, or None
        """
        # If we have the property object, try to get the observable from it
        if observable_property is not None and observable_id is None:
            observable = getattr(observable_property, "observable", None)
            if observable is not None:
                observable_id = self.get_observable_id(observable)
                
        # Get property name from property object if not provided
        if observable_property is not None and property_name is None:
            property_name = getattr(observable_property, "name", None)
            
        # Get by observable_id + property_name
        if observable_id is not None and property_name is not None:
            prop_id = f"{observable_id}:{property_name}"
            if prop_id in self._property_registry:
                return prop_id
            return None
            
        # Get all properties for observable
        if observable_id is not None:
            if observable_id in self._observable_id_to_property_ids:
                return list(self._observable_id_to_property_ids[observable_id])
            return []
            
        return None
    
    def bind_widget(self, property_id: str, widget_id: str, is_controller: bool = False) -> bool:
        """
        Bind widget to property.
        
        Args:
            property_id: ID of the property
            widget_id: ID of the widget
            is_controller: True if widget controls the property
            
        Returns:
            True if binding was successful
        """
        if property_id not in self._property_registry:
            return False
            
        # Add to property's bound widgets
        self._property_registry[property_id]["bound_widgets"].add(widget_id)
        self._property_registry[property_id]["is_controller"][widget_id] = is_controller
        
        # Add to widget's property set
        if widget_id not in self._widget_id_to_property_ids:
            self._widget_id_to_property_ids[widget_id] = set()
        self._widget_id_to_property_ids[widget_id].add(property_id)
        
        # If this is a controller, update the observable accordingly
        if is_controller:
            observable_id = self._property_registry[property_id]["observable_id"]
            self.update_observable_widget(observable_id, widget_id)
            
        return True
    
    def unbind_widget(self, property_id: str, widget_id: str) -> bool:
        """
        Unbind widget from property.
        
        Args:
            property_id: ID of the property
            widget_id: ID of the widget
            
        Returns:
            True if unbinding was successful
        """
        if property_id not in self._property_registry:
            return False
            
        # Remove from property's bound widgets
        if widget_id in self._property_registry[property_id]["bound_widgets"]:
            self._property_registry[property_id]["bound_widgets"].remove(widget_id)
            
        # Remove is_controller flag
        if widget_id in self._property_registry[property_id]["is_controller"]:
            was_controller = self._property_registry[property_id]["is_controller"][widget_id]
            del self._property_registry[property_id]["is_controller"][widget_id]
            
            # If this was a controller, update the observable accordingly
            if was_controller:
                observable_id = self._property_registry[property_id]["observable_id"]
                self.update_observable_widget(observable_id, None)
                
        # Remove from widget's property set
        if widget_id in self._widget_id_to_property_ids:
            if property_id in self._widget_id_to_property_ids[widget_id]:
                self._widget_id_to_property_ids[widget_id].remove(property_id)
                
            # Clean up empty set
            if not self._widget_id_to_property_ids[widget_id]:
                del self._widget_id_to_property_ids[widget_id]
                
        return True
    
    def update_property(self, property_id: str, widget_id: Optional[str] = None) -> bool:
        """
        Update property attributes.
        
        Args:
            property_id: ID of the property to update
            widget_id: New controller widget ID (optional)
            
        Returns:
            True if update was successful
        """
        if property_id not in self._property_registry:
            return False
            
        # Update controller widget if provided
        if widget_id is not None:
            # Remove existing controller(s)
            for wid, is_ctrl in list(self._property_registry[property_id]["is_controller"].items()):
                if is_ctrl:
                    self._property_registry[property_id]["is_controller"][wid] = False
                    
            # Bind new controller
            self.bind_widget(property_id, widget_id, True)
            
        return True
    
    def unregister_property(self, property_id: str) -> bool:
        """
        Unregister a property.
        
        Args:
            property_id: ID of the property to unregister
            
        Returns:
            True if unregistration was successful
        """
        if property_id not in self._property_registry:
            return False
            
        # Unbind all widgets
        for widget_id in list(self._property_registry[property_id]["bound_widgets"]):
            self.unbind_widget(property_id, widget_id)
            
        # Remove from observable's property set
        observable_id = self._property_registry[property_id]["observable_id"]
        if observable_id in self._observable_id_to_property_ids:
            if property_id in self._observable_id_to_property_ids[observable_id]:
                self._observable_id_to_property_ids[observable_id].remove(property_id)
                
            # Clean up empty set
            if not self._observable_id_to_property_ids[observable_id]:
                del self._observable_id_to_property_ids[observable_id]
                
        # Remove from registry
        del self._property_registry[property_id]
        
        return True
    
    # Binding Methods
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
    
    def get_bindings(self, widget_id: Optional[str] = None, 
                    property_id: Optional[str] = None,
                    observable_id: Optional[str] = None) -> List[Dict]:
        """
        Get bindings with flexible filtering.
        
        Args:
            widget_id: Get bindings for widget
            property_id: Get bindings for property
            observable_id: Get bindings for observable
            
        Returns:
            List of binding information dictionaries
        """
        result = []
        
        # Case 1: Property bindings
        if property_id is not None:
            if property_id in self._property_registry:
                prop_info = self._property_registry[property_id]
                observable_id = prop_info["observable_id"]
                
                for w_id in prop_info["bound_widgets"]:
                    result.append({
                        "property_id": property_id,
                        "observable_id": observable_id,
                        "widget_id": w_id,
                        "is_controller": prop_info["is_controller"].get(w_id, False)
                    })
            return result
        
        # Case 2: Widget bindings (properties + direct observable bindings)
        if widget_id is not None:
            # Add property bindings
            if widget_id in self._widget_id_to_property_ids:
                for prop_id in self._widget_id_to_property_ids[widget_id]:
                    if prop_id in self._property_registry:
                        prop_info = self._property_registry[prop_id]
                        result.append({
                            "property_id": prop_id,
                            "observable_id": prop_info["observable_id"],
                            "widget_id": widget_id,
                            "is_controller": prop_info["is_controller"].get(widget_id, False)
                        })
            
            # Add direct observable bindings
            if widget_id in self._widget_id_to_observable_ids:
                for obs_id in self._widget_id_to_observable_ids[widget_id]:
                    # Skip if already added through property
                    if not any(b["observable_id"] == obs_id for b in result):
                        result.append({
                            "property_id": None,
                            "observable_id": obs_id,
                            "widget_id": widget_id,
                            "is_controller": extract_widget_unique_id(obs_id) == extract_unique_id(widget_id)
                        })
            return result
        
        # Case 3: Observable bindings
        if observable_id is not None:
            # Add property bindings
            if observable_id in self._observable_id_to_property_ids:
                for prop_id in self._observable_id_to_property_ids[observable_id]:
                    if prop_id in self._property_registry:
                        prop_info = self._property_registry[prop_id]
                        for w_id in prop_info["bound_widgets"]:
                            result.append({
                                "property_id": prop_id,
                                "observable_id": observable_id,
                                "widget_id": w_id,
                                "is_controller": prop_info["is_controller"].get(w_id, False)
                            })
            
            # Add direct widget bindings
            if observable_id in self._observable_id_to_widget_ids:
                for w_id in self._observable_id_to_widget_ids[observable_id]:
                    # Skip if already added through property
                    if not any(b["widget_id"] == w_id for b in result):
                        result.append({
                            "property_id": None,
                            "observable_id": observable_id,
                            "widget_id": w_id,
                            "is_controller": extract_widget_unique_id(observable_id) == extract_unique_id(w_id)
                        })
            return result
        
        # Case 4: All bindings
        # First add all property bindings
        for prop_id, prop_info in self._property_registry.items():
            for w_id in prop_info["bound_widgets"]:
                result.append({
                    "property_id": prop_id,
                    "observable_id": prop_info["observable_id"],
                    "widget_id": w_id,
                    "is_controller": prop_info["is_controller"].get(w_id, False)
                })
        
        # Then add direct observable-widget bindings not covered by properties
        for obs_id, widget_ids in self._observable_id_to_widget_ids.items():
            for w_id in widget_ids:
                # Skip if already added through property
                if not any(b["observable_id"] == obs_id and b["widget_id"] == w_id for b in result):
                    result.append({
                        "property_id": None,
                        "observable_id": obs_id,
                        "widget_id": w_id,
                        "is_controller": extract_widget_unique_id(obs_id) == extract_unique_id(w_id)
                    })
        
        return result
    
    # Preserved methods for backward compatibility
    def get_widget_ids_by_container_id(self, container_id: str) -> List[str]:
        """
        Get all widget IDs that have this container ID.
        
        Args:
            container_id: Container's ID
            
        Returns:
            List of widget ID strings
        """
        widgets = self.get_widget(container_id=container_id)
        return [self.get_widget_id(w) for w in widgets]
        
    def get_widgets_by_container_id(self, container_id: str) -> List[Any]:
        """
        Get all widgets that have this container ID.
        
        Args:
            container_id: Container's ID
            
        Returns:
            List of widget objects
        """
        return self.get_widget(container_id=container_id)
        
    def get_widget_ids_by_container_id_and_location(self, container_id: str, location: str) -> List[str]:
        """
        Get all widget IDs that have this container ID and location.
        
        Args:
            container_id: Container's ID
            location: Location in container
            
        Returns:
            List of widget ID strings
        """
        widgets = self.get_widget(container_id=container_id, location=location)
        return [self.get_widget_id(w) for w in widgets]
        
    def get_widgets_by_container_id_and_location(self, container_id: str, location: str) -> List[Any]:
        """
        Get all widgets that have this container ID and location.
        
        Args:
            container_id: Container's ID
            location: Location in container
            
        Returns:
            List of widget objects
        """
        return self.get_widget(container_id=container_id, location=location)
    
    def get_bound_widget_ids(self, observable_id: str) -> List[str]:
        """
        Get all widget IDs bound to this observable.
        
        Args:
            observable_id: Observable ID
            
        Returns:
            List of widget ID strings
        """
        bindings = self.get_bindings(observable_id=observable_id)
        return [b["widget_id"] for b in bindings]
    
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
        bindings = self.get_bindings(widget_id=widget_id)
        return [b["observable_id"] for b in bindings]
    
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
            if is_widget_id(w_id) and extract_unique_id(w_id) == widget_unique_id:
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
            if is_widget_id(w_id) and extract_unique_id(w_id) == container_unique_id:
                return w_id
                
        return None
    
    def clear(self) -> None:
        """Clear all registry mappings."""
        self._widget_to_id_map.clear()
        self._id_to_widget_map.clear()
        self._observable_to_id_map.clear()
        self._id_to_observable_map.clear()
        self._widget_id_to_observable_ids.clear()
        self._observable_id_to_widget_ids.clear()
        # Clear property-related mappings if they exist
        if hasattr(self, '_property_registry'):
            self._property_registry.clear()
        if hasattr(self, '_observable_id_to_property_ids'):
            self._observable_id_to_property_ids.clear()
        if hasattr(self, '_widget_id_to_property_ids'):
            self._widget_id_to_property_ids.clear()
    
    
def get_id_registry():
    """
    Get the singleton ID registry instance.
    Returns:
        IDRegistry singleton instance
    """
    return IDRegistry.get_instance()