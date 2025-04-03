"""
Base container for integrating PySide6 containers with the command system.

Provides a base implementation for command-enabled containers
leveraging the ID system for efficient relationship tracking and
support for nested container hierarchies.
"""
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Type
import inspect
from PySide6.QtWidgets import QWidget, QVBoxLayout

from command_system.id_system import get_id_registry, TypeCodes, extract_location, get_simple_id_registry
from command_system.core import Observable
from ..base_widget import BaseCommandWidget

class BaseCommandContainer(BaseCommandWidget):
    """
    Base class for all command-system enabled containers.
    
    Provides essential container-specific functionality while leveraging the ID system
    for relationship tracking and subcontainer management.
    """
    
    def initiate_container(self, type_code: str, container_id: Optional[str] = None, 
                          location: Optional[str] = None):
        """Initialize the container with type code and optional parent."""
        # Initialize the base widget
        super().initiate_widget(type_code, container_id, location)
        
        # Widget type registry for factory functions
        self._widget_types = {}  # type_id -> {factory, observables, options}
        
        # Track registered subcontainers
        self._subcontainers = {}  # subcontainer_id -> subcontainer
        
        # Type mapping for subcontainers
        self._types_map = {}  # subcontainer_id -> type_id
        
        # Locations map for subcontainers
        self._locations_map = {}  # subcontainer_id -> location
    
    # MARK: - Type Registration
    def register_subcontainer_type(self, factory_func: Callable, 
                                  observables: List[Union[str, Type[Observable]]] = None,
                                  type_id: str = None,
                                  **options) -> str:
        """
        Register a subcontainer factory function.
        
        Args:
            factory_func: Function that creates the subcontainer content
            observables: List of Observable IDs or Observable classes
                        IDs will use existing observables
                        Classes will create new instances
            type_id: Optional unique ID for this subcontainer type
            **options: Additional options like closable, title, etc.
            
        Returns:
            Unique ID for the registered subcontainer type
        """
        # Generate type_id if not provided
        if type_id is None:
            # Use function name as part of the ID for better debugging
            function_name = factory_func.__name__
            simple_id_registry = get_simple_id_registry()
            type_id = simple_id_registry.register(function_name, self.type_code)
        
        # Store subcontainer type info
        self._widget_types[type_id] = {
            "factory": factory_func,
            "observables": observables or [],
            "options": options
        }
        
        return type_id
    
    # MARK: - Subcontainer Management
    def create_subcontainer(self, type_id: str, location: str = "0") -> Optional[QWidget]:
        """
        Create an empty subcontainer widget for the specified type.
        Must be implemented by subclasses.
        
        Args:
            type_id: Type ID of the subcontainer
            location: Location for the subcontainer
            
        Returns:
            The created subcontainer widget, or None if failed
        """
        raise NotImplementedError("Subclasses must implement create_subcontainer")
    
    def add_subcontainer(self, type_id: str, location: str = "0") -> Optional[str]:
        """
        Add a new subcontainer of the registered type.
        
        Args:
            type_id: ID of the registered subcontainer type
            location: Location identifier within this container
            
        Returns:
            ID of the created subcontainer, or None if failed
        """
        # Check if the type exists
        if type_id not in self._widget_types:
            return None
        
        # Create an empty subcontainer
        subcontainer = self.create_subcontainer(type_id, location)
        if not subcontainer:
            return None
        
        # Register the subcontainer with the ID system - using consistent container type
        id_registry = get_id_registry()
        subcontainer_id = id_registry.register(
            subcontainer, self.type_code, 
            None, self.widget_id, location
        )
        
        # Store type mapping
        self._types_map[subcontainer_id] = type_id
        
        # Store location mapping
        self._locations_map[subcontainer_id] = location
        
        # Store subcontainer
        self._subcontainers[subcontainer_id] = subcontainer
        
        # Get type info for the content
        type_info = self._widget_types[type_id]
        factory = type_info["factory"]
        registered_observables = type_info["observables"]
        
        # Prepare arguments - resolve observables
        factory_args = []
        created_observables = []
        
        # Process observables
        for obs in registered_observables:
            if isinstance(obs, str):
                # It's an ID - get the existing observable
                observable = id_registry.get_observable(obs)
                factory_args.append(observable)
            elif inspect.isclass(obs) and issubclass(obs, Observable):
                # It's a class - create a new instance
                observable = obs()
                factory_args.append(observable)
                created_observables.append(observable)
            else:
                print(f"Invalid observable specification: {obs}")
                return None
        
        try:
            # Create the widget content
            content = factory(*factory_args)
            
            if not isinstance(content, QWidget):
                print(f"Factory {type_id} didn't return a QWidget")
                return None
            
            # Add content to the subcontainer using layout
            if hasattr(subcontainer, 'layout'):
                subcontainer.layout().addWidget(content)
            else:
                layout = QVBoxLayout()
                layout.addWidget(content)
                subcontainer.setLayout(layout)
            
            return subcontainer_id
        
        except Exception as e:
            print(f"Error creating subcontainer of type {type_id}: {e}")
            return None
        
    # MARK: - Subcontainer Access
    def get_subcontainer(self, subcontainer_id: str) -> Optional[QWidget]:
        """
        Get a subcontainer by ID.
        
        Args:
            subcontainer_id: ID of the subcontainer
            
        Returns:
            Subcontainer widget, or None if not found
        """
        id_registry = get_id_registry()
        return id_registry.get_widget(subcontainer_id)
    
    def get_subcontainer_type(self, subcontainer_id: str) -> Optional[str]:
        """
        Get the type ID for a subcontainer.
        
        Args:
            subcontainer_id: ID of the subcontainer
            
        Returns:
            Type ID, or None if not found
        """
        return self._types_map.get(subcontainer_id)
    
    def get_subcontainer_location(self, subcontainer_id: str) -> Optional[str]:
        """
        Get the location for a subcontainer.
        
        Args:
            subcontainer_id: ID of the subcontainer
            
        Returns:
            Location, or None if not found
        """
        return self._locations_map.get(subcontainer_id)
    
    def get_subcontainer_at_location(self, location: str) -> Optional[str]:
        """
        Get the subcontainer ID at a specific location.
        
        Args:
            location: Location to look up
            
        Returns:
            Subcontainer ID, or None if not found
        """
        for subcontainer_id, loc in self._locations_map.items():
            if loc == location:
                return subcontainer_id
        return None
    
    def get_all_subcontainers(self) -> List[str]:
        """
        Get IDs of all subcontainers.
        
        Returns:
            List of subcontainer IDs
        """
        return list(self._subcontainers.keys())
    
    # MARK: - Navigation
    def navigate_to_widget(self, target_widget_id: str) -> bool:
        """
        Navigate to a specific widget by traversing the container hierarchy.
        
        Args:
            target_widget_id: ID of the widget to navigate to
            
        Returns:
            True if navigation was successful
        """
        # First check if this container is inside another container
        id_registry = get_id_registry()
        parent_container_id = id_registry.get_container_id_from_widget_id(self.widget_id)
        
        if parent_container_id:
            # If we have a parent container, ask it to navigate to the target
            parent_container = id_registry.get_widget(parent_container_id)
            if parent_container and hasattr(parent_container, 'navigate_to_widget'):
                # Navigate to this container first
                parent_container.navigate_to_widget(self.widget_id)
            else:
                grandparent_container_id = id_registry.get_container_id_from_widget_id(parent_container_id)
                grandparent_container = id_registry.get_widget(grandparent_container_id) if grandparent_container_id else None
                if grandparent_container and hasattr(grandparent_container, 'navigate_to_widget'):
                    grandparent_container.navigate_to_widget(parent_container_id)        
                    
        # Get the container of the target widget
        target_container_id = id_registry.get_container_id_from_widget_id(target_widget_id)
        
        # Check if the target is in one of our subcontainers
        if target_container_id in self._subcontainers:
            # Navigate to the subcontainer
            subcontainer_location = self._locations_map.get(target_container_id)
            if subcontainer_location:
                self.navigate_to_location(subcontainer_location)
        else:
            # Try to navigate to its location directly
            target_location = extract_location(target_widget_id)
            self.navigate_to_location(target_location)
        
        # Set focus on the target widget
        target_widget = id_registry.get_widget(target_widget_id)
        if target_widget:
            target_widget.setFocus()
        
        return True

    def navigate_to_location(self, location: str) -> bool:
        """
        Navigate to a specific location within this container.
        Must be implemented by container subclasses.
        
        Args:
            location: Location identifier
            
        Returns:
            True if navigation was successful
        """
        # Base implementation does nothing
        raise NotImplementedError("Subclasses must implement navigate_to_location")
    
    # MARK: - Resource Management
    def close_subcontainer(self, subcontainer_id: str) -> bool:
        """
        Close and unregister a subcontainer.
        
        Args:
            subcontainer_id: ID of the subcontainer to close
            
        Returns:
            True if successful, False otherwise
        """
        id_registry = get_id_registry()
        
        # Remove from tracking maps
        if subcontainer_id in self._subcontainers:
            del self._subcontainers[subcontainer_id]
        if subcontainer_id in self._types_map:
            del self._types_map[subcontainer_id]
        if subcontainer_id in self._locations_map:
            del self._locations_map[subcontainer_id]
        
        # Unregister from ID system
        return id_registry.unregister(subcontainer_id)
    
    def unregister_widget(self) -> None:
        """Unregister this container and all its subcontainers."""
        # Close all subcontainers first
        for subcontainer_id in list(self._subcontainers.keys()):
            self.close_subcontainer(subcontainer_id)
        
        # Unregister this container
        id_registry = get_id_registry()
        id_registry.unregister(self.widget_id)
    
    # MARK: - Serialization
    def get_serialization(self) -> Dict:
        """
        Get serialized representation of this container.
        
        Returns:
            Dict containing serialized container state
        """
        result = {
            'id': self.widget_id,
            'subcontainers': []
        }
        
        # Serialize all subcontainers
        for subcontainer_id in self._subcontainers.keys():
            serialized_subcontainer = self.serialize_subcontainer(subcontainer_id)
            if serialized_subcontainer:
                result['subcontainers'].append(serialized_subcontainer)
        
        return result
    
    def serialize_subcontainer(self, subcontainer_id: str) -> Dict:
        """
        Serialize a subcontainer.
        
        Args:
            subcontainer_id: ID of the subcontainer to serialize
            
        Returns:
            Dict containing serialized subcontainer state
        """
        # Get subcontainer info
        subcontainer_type = self._types_map.get(subcontainer_id)
        location = self._locations_map.get(subcontainer_id)
        
        if not subcontainer_type or not location:
            return None
            
        # Get the subcontainer widget
        id_registry = get_id_registry()
        subcontainer = id_registry.get_widget(subcontainer_id)
        
        if not subcontainer:
            return None
            
        # Create serialization for the subcontainer
        serialization = {
            'id': subcontainer_id,
            'type': subcontainer_type,
            'location': location,
            'children': {}
        }
        
        # Get all children of the subcontainer
        child_ids = id_registry.get_widget_ids_by_container_id(subcontainer_id)
        
        # Serialize each child
        for child_id in child_ids:
            child = id_registry.get_widget(child_id)
            if child and hasattr(child, 'get_serialization'):
                serialization['children'][child_id] = child.get_serialization()
                
        return serialization
    
    def deserialize(self, serialized_data: Dict) -> bool:
        """
        Deserialize and restore container state.
        
        Args:
            serialized_data: Dict containing serialized container state
            
        Returns:
            True if successful, False otherwise
        """
        # Update container ID if needed
        if 'id' in serialized_data and serialized_data['id'] != self.widget_id:
            id_registry = get_id_registry()
            self.widget_id = id_registry.register(self, self.type_code, serialized_data['id'])
        
        # Get current subcontainers
        current_subcontainers = set(self._subcontainers.keys())
        serialized_subcontainers = set()
        
        # Process serialized subcontainers
        if 'subcontainers' in serialized_data:
            for subcontainer_data in serialized_data['subcontainers']:
                subcontainer_id = subcontainer_data.get('id')
                subcontainer_type = subcontainer_data.get('type')
                location = subcontainer_data.get('location')
                
                if not subcontainer_id or not subcontainer_type or not location:
                    continue
                
                serialized_subcontainers.add(subcontainer_id)
                
                # Check if subcontainer exists
                if subcontainer_id in current_subcontainers:
                    # Update existing subcontainer
                    self.deserialize_subcontainer(
                        subcontainer_type, 
                        location, 
                        subcontainer_data, 
                        subcontainer_id
                    )
                else:
                    # Create new subcontainer
                    self.deserialize_subcontainer(
                        subcontainer_type,
                        location,
                        subcontainer_data
                    )
        
        # Close any subcontainers that aren't in the serialized data
        for subcontainer_id in current_subcontainers - serialized_subcontainers:
            self.close_subcontainer(subcontainer_id)
        
        return True
    
    def deserialize_subcontainer(self, type_id: str, location: str, 
                                serialized_subcontainer: Dict,
                                existing_subcontainer_id: Optional[str] = None) -> str:
        """
        Deserialize and restore a subcontainer.
        
        Args:
            type_id: Type ID of the subcontainer
            location: Location for the subcontainer
            serialized_subcontainer: Dict containing serialized subcontainer state
            existing_subcontainer_id: ID of existing subcontainer to update (optional)
            
        Returns:
            ID of the subcontainer
        """
        id_registry = get_id_registry()
        
        if existing_subcontainer_id:
            # Update existing subcontainer
            subcontainer = id_registry.get_widget(existing_subcontainer_id)
            if not subcontainer:
                # Subcontainer no longer exists, create a new one
                return self.deserialize_subcontainer(
                    type_id, location, serialized_subcontainer)
            
            # Update location if needed
            current_location = self._locations_map.get(existing_subcontainer_id)
            if current_location != location:
                self._locations_map[existing_subcontainer_id] = location
            
            # The ID stays the same
            subcontainer_id = existing_subcontainer_id
        else:
            # Create a new subcontainer
            subcontainer_id = self.create_subcontainer(type_id, location)
            if not subcontainer_id:
                return None
            
            # Store type and location mappings
            self._types_map[subcontainer_id] = type_id
            self._locations_map[subcontainer_id] = location
            
            # Store subcontainer
            self._subcontainers[subcontainer_id] = id_registry.get_widget(subcontainer_id)
        
        # Deserialize children
        if 'children' in serialized_subcontainer:
            children_data = serialized_subcontainer['children']
            
            # Get current children IDs
            current_children = set(id_registry.get_widget_ids_by_container_id(subcontainer_id))
            serialized_children = set(children_data.keys())
            
            # Find matching children
            for child_id in current_children:
                child = id_registry.get_widget(child_id)
                if not child or not hasattr(child, 'deserialize'):
                    continue
                    
                # Find matching serialized child
                if child_id in serialized_children:
                    # Deserialize child
                    child.deserialize(children_data[child_id])
                else:
                    # Child not in serialized data - this shouldn't happen
                    # Raise an error as the same container type should always
                    # generate the same children structure
                    raise ValueError(f"Child {child_id} not found in serialized data for subcontainer {subcontainer_id}")
        
        return subcontainer_id