"""
Improved base container for integrating PySide6 containers with the command system.

Provides an optimized implementation for command-enabled containers
leveraging the ID system for efficient relationship tracking and
support for nested container hierarchies.
"""
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Type
import inspect
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from command_system.id_system import get_id_registry, get_simple_id_registry, TypeCodes
from command_system.id_system.core.parser import parse_widget_id
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
        
        # Widget type registry - optimized structure for faster lookups
        self._widget_types = {}  # type_id -> {factory, observables, options}
        
        # Direct references to subcontainers for faster access
        self._subcontainers = {}  # subcontainer_id -> subcontainer widget
        
        # Bidirectional mapping for faster lookups
        self._types_map = {}  # subcontainer_id -> type_id
        self._locations_map = {}  # location -> subcontainer_id
        self._id_to_location_map = {}  # subcontainer_id -> location
    
    # MARK: - Type Registration
    def register_subcontainer_type(self, factory_func: Callable, 
                                observables: List[Union[str, Type[Observable]]] = None,
                                type_id: str = None,
                                **options) -> str:
        """
        Register a subcontainer type with factory function.
        
        Args:
            factory_func: Function that creates the subcontainer content
            observables: List of Observable IDs or Observable classes
                         IDs will use existing observables
                         Classes will create new instances
            type_id: Optional ID for the type, generated if not provided
            **options: Additional options for the subcontainer type
            
        Returns:
            Type ID of the registered subcontainer type
        """
        # Generate type_id if not provided - using efficient ID generation
        if type_id is None:
            simple_id_registry = get_simple_id_registry()
            type_id = simple_id_registry.register(self.type_code)
        
        # Store subcontainer type info - optimized structure
        self._widget_types[type_id] = {
            "factory": factory_func,
            "observables": observables or [],
            "options": options
        }
        
        return type_id
    
    # MARK: - Subcontainer Management
    def create_subcontainer(self, type_id: str, location: str = "0") -> Tuple[QWidget, str]:
        """
        Create an empty subcontainer widget for the specified type.
        Must be implemented by subclasses.
        
        Args:
            type_id: Type ID of the subcontainer
            location: Location for the subcontainer
            
        Returns:
            Tuple of (subcontainer widget, location string)
        """
        raise NotImplementedError("Subclasses must implement create_subcontainer")
    
    def add_subcontainer(self, type_id: str, location: str = None) -> Optional[str]:
        """
        Add a new subcontainer of the registered type.
        
        Args:
            type_id: ID of the registered subcontainer type
            location: Location identifier within this container
            
        Returns:
            ID of the created subcontainer, or None if failed
        """
        # Type validation with early return for performance
        if type_id not in self._widget_types:
            return None
        
        # Create an empty subcontainer
        subcontainer, subcontainer_location = self.create_subcontainer(type_id, location)
        if not subcontainer:
            return None
        
        # Register the subcontainer with the ID system - using consistent container type
        id_registry = get_id_registry()
        subcontainer_id = id_registry.register(subcontainer, self.type_code, None, self.widget_id, location)
        
        # Store mappings - now with bidirectional references for faster lookups
        self._types_map[subcontainer_id] = type_id
        self._locations_map[subcontainer_location] = subcontainer_id
        self._id_to_location_map[subcontainer_id] = subcontainer_location
        self._subcontainers[subcontainer_id] = subcontainer
        
        # Get type info for the content
        type_info = self._widget_types[type_id]
        factory = type_info["factory"]
        registered_observables = type_info["observables"]
        
        # Extract observable IDs (strings) to register as non-controlling
        observable_ids = []
        
        for obs in registered_observables:
            if isinstance(obs, str):
                # It's an observable ID - add to non-controlling list
                observable_ids.append(obs)
        
        # Register non-controlling observables if any found
        if observable_ids:
            id_registry.register_non_controlling_observables(subcontainer_id, observable_ids)
            print(f"Subcontainer {subcontainer_id} has non-controlling observables: {observable_ids}")
        
        # Create content using observable resolution
        content = self._create_content_with_observables(factory, registered_observables)
        if not content:
            return subcontainer_id  # Still return ID even if content creation fails
            
        if not isinstance(content, QWidget):
            return subcontainer_id
        
        # Add content to the subcontainer efficiently
        self._add_content_to_subcontainer(subcontainer, content)
        
        # Register child widgets efficiently
        self._register_contents(content, subcontainer_id)
        
        return subcontainer_id
        
    def _create_content_with_observables(self, factory: Callable, 
                                        registered_observables: List[Union[str, Type[Observable]]]) -> QWidget:
        """
        Create content for subcontainer with optimized observable handling.
        
        Args:
            factory: Factory function to create content
            registered_observables: List of observable specifications
            
        Returns:
            Created widget content or None if creation failed
        """
        factory_args = []
        id_registry = get_id_registry()
        
        # Process observables more efficiently
        for obs in registered_observables:
            if isinstance(obs, str):
                # It's an ID - get the existing observable
                observable = id_registry.get_observable(obs)
                factory_args.append(observable)
            elif inspect.isclass(obs) and issubclass(obs, Observable):
                # It's a class - create a new instance
                observable = obs()
                factory_args.append(observable)
            else:
                return None  # Invalid observable specification
        
        try:
            # Create the widget content
            return factory(*factory_args)
        except Exception as e:
            return None
    
    def _add_content_to_subcontainer(self, subcontainer: QWidget, content: QWidget):
        """
        Add content to subcontainer efficiently.
        
        Args:
            subcontainer: Container widget
            content: Content widget to add
        """
        # Reuse existing layout if available
        layout = subcontainer.layout()
        if layout is None:
            layout = QVBoxLayout(subcontainer)
            layout.setContentsMargins(0, 0, 0, 0)
        
        # Clear existing items if present (for reused containers)
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Add new content
        layout.addWidget(content)
        
    def _register_contents(self, widget: QWidget, container_id: str):
        """
        Register a widget and all its children with this container.
        
        Args:
            widget: The widget to register
            container_id: Container ID for the widgets
        """
        # Use non-recursive approach for better performance with deep hierarchies
        id_registry = get_id_registry()
        widgets_to_process = [widget]
        count = 0
        while widgets_to_process:
            current_widget = widgets_to_process.pop(0)
            
            # Set this container as the widget's container
            if hasattr(current_widget, "update_container"):
                current_widget.update_container(container_id, count)
                count += 1
            
            # Process child widgets - even for container widgets
            # This allows nested containers to work properly
            if isinstance(current_widget, QWidget):
                child_widgets = current_widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly)
                widgets_to_process.extend(child_widgets)
        
    # MARK: - Subcontainer Access
    def get_subcontainer(self, subcontainer_id: str) -> Optional[QWidget]:
        """
        Get a subcontainer by ID with direct lookup.
        
        Args:
            subcontainer_id: ID of the subcontainer
            
        Returns:
            Subcontainer widget, or None if not found
        """
        # Direct lookup from our cache for better performance
        return self._subcontainers.get(subcontainer_id)
    
    def get_subcontainer_type(self, subcontainer_id: str) -> Optional[str]:
        """
        Get the type ID for a subcontainer using direct mapping.
        
        Args:
            subcontainer_id: ID of the subcontainer
            
        Returns:
            Type ID, or None if not found
        """
        return self._types_map.get(subcontainer_id)
    
    def get_subcontainer_location(self, subcontainer_id: str) -> Optional[str]:
        """
        Get the location for a subcontainer using bidirectional mapping.
        
        Args:
            subcontainer_id: ID of the subcontainer
            
        Returns:
            Location, or None if not found
        """
        # Direct lookup using bidirectional mapping
        return self._id_to_location_map.get(subcontainer_id)
    
    def get_subcontainer_at_location(self, location: str) -> Optional[str]:
        """
        Get the subcontainer ID at a specific location.
        
        Args:
            location: Location to look up
            
        Returns:
            Subcontainer ID, or None if not found
        """
        return self._locations_map.get(location)
    
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
        container_id = id_registry.get_container_id_from_widget_id(self.widget_id)
        
        if container_id and container_id != "0":
            # If we have a parent container, ask it to navigate to us first
            parent_container = id_registry.get_widget(container_id)
            if parent_container and hasattr(parent_container, 'navigate_to_widget'):
                parent_container.navigate_to_widget(self.widget_id)
        
        # Get the container of the target widget
        target_container_id = id_registry.get_container_id_from_widget_id(target_widget_id)
        
        # Check if the target is in one of our subcontainers
        if target_container_id in self._subcontainers:
            # Get the location directly from our mapping
            subcontainer_location = self._id_to_location_map.get(target_container_id)
            if subcontainer_location:
                # Navigate to the subcontainer's location
                self.navigate_to_location(subcontainer_location)
        
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
        # Early validation
        if subcontainer_id not in self._subcontainers:
            return False
            
        id_registry = get_id_registry()
        
        # Get the location from our direct mapping
        location = self._id_to_location_map.get(subcontainer_id)
        
        # Remove from tracking maps efficiently
        if location:
            self._locations_map.pop(location, None)
        self._id_to_location_map.pop(subcontainer_id, None)
        self._types_map.pop(subcontainer_id, None)
        self._subcontainers.pop(subcontainer_id, None)
        
        # Unregister from ID system
        return id_registry.unregister(subcontainer_id)
    
    def unregister_widget(self) -> bool:
        """
        Unregister this container and all its subcontainers.
        
        Returns:
            True if successful, False otherwise
        """
        # Close all subcontainers first - create a copy of keys to avoid modification during iteration
        for subcontainer_id in list(self._subcontainers.keys()):
            self.close_subcontainer(subcontainer_id)
        
        # Unregister this container
        return super().unregister_widget()
    
    # MARK: - Serialization with optimized handling
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
        
        # Serialize all subcontainers efficiently
        for subcontainer_id in self._subcontainers:
            serialized_subcontainer = self.serialize_subcontainer(subcontainer_id)
            if serialized_subcontainer:
                result['subcontainers'].append(serialized_subcontainer)
        
        return result
    
    def serialize_subcontainer(self, subcontainer_id: str) -> Dict:
        """
        Serialize a subcontainer efficiently.
        
        Args:
            subcontainer_id: ID of the subcontainer to serialize
            
        Returns:
            Dict containing serialized subcontainer state
        """
        # Quick validation with early returns
        if subcontainer_id not in self._subcontainers:
            return None
            
        # Get subcontainer info from direct mappings
        subcontainer_type = self._types_map.get(subcontainer_id)
        location = self._id_to_location_map.get(subcontainer_id)
        
        if not subcontainer_type or not location:
            return None
            
        # Get the subcontainer widget from our cache
        subcontainer = self._subcontainers.get(subcontainer_id)
        if not subcontainer:
            return None
            
        # Create serialization for the subcontainer
        serialization = {
            'id': subcontainer_id,
            'type': subcontainer_type,
            'location': location,
            'children': {}
        }
        
        # Get all widgets that have this subcontainer as their container
        id_registry = get_id_registry()
        widget_ids = id_registry.get_widgets_by_container_id(subcontainer_id)
        
        # Serialize each child that can be serialized
        for widget_id in widget_ids:
            widget = id_registry.get_widget(widget_id)
            if widget and hasattr(widget, 'get_serialization'):
                serialization['children'][widget_id] = widget.get_serialization()
                
        return serialization
    
    def deserialize(self, serialized_data: Dict) -> bool:
        """
        Deserialize and restore container state efficiently.
        
        Args:
            serialized_data: Dict containing serialized container state
            
        Returns:
            True if successful, False otherwise
        """
        # Validate input
        if not serialized_data or not isinstance(serialized_data, dict):
            return False
            
        # Update container ID if needed
        self._update_container_id(serialized_data)
        
        # Process subcontainers efficiently
        return self._deserialize_subcontainers(serialized_data)
    
    def _update_container_id(self, serialized_data: Dict):
        """
        Update container ID if needed during deserialization.
        
        Args:
            serialized_data: Serialized container data
        """
        if 'id' in serialized_data and serialized_data['id'] != self.widget_id:
            id_registry = get_id_registry()
            # Register with specified ID to keep consistent with serialized state
            id_registry.unregister(self.widget_id)
            self.widget_id = id_registry.register(self, self.type_code, None)
    
    def _deserialize_subcontainers(self, serialized_data: Dict) -> bool:
        """
        Process subcontainers during deserialization efficiently.
        
        Args:
            serialized_data: Serialized container data
            
        Returns:
            True if successful, False otherwise
        """
        # Get current subcontainers and track which ones are in the serialized data
        current_subcontainers = set(self._subcontainers.keys())
        serialized_subcontainers = set()
        
        # Process serialized subcontainers
        if 'subcontainers' in serialized_data and isinstance(serialized_data['subcontainers'], list):
            for subcontainer_data in serialized_data['subcontainers']:
                # Validate required fields
                if not self._validate_subcontainer_data(subcontainer_data):
                    continue
                    
                subcontainer_id = subcontainer_data['id']
                subcontainer_type = subcontainer_data['type']
                location = subcontainer_data['location']
                
                serialized_subcontainers.add(subcontainer_id)
                
                # Check if subcontainer exists and handle appropriately
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
    
    def _validate_subcontainer_data(self, subcontainer_data: Dict) -> bool:
        """
        Validate subcontainer data before deserialization.
        
        Args:
            subcontainer_data: Serialized subcontainer data
            
        Returns:
            True if valid, False otherwise
        """
        return (isinstance(subcontainer_data, dict) and
                'id' in subcontainer_data and
                'type' in subcontainer_data and
                'location' in subcontainer_data)
    
    def deserialize_subcontainer(self, type_id: str, location: str, 
                                serialized_subcontainer: Dict,
                                existing_subcontainer_id: Optional[str] = None) -> str:
        """
        Deserialize and restore a subcontainer efficiently.
        
        Args:
            type_id: Type ID of the subcontainer
            location: Location for the subcontainer
            serialized_subcontainer: Dict containing serialized subcontainer state
            existing_subcontainer_id: ID of existing subcontainer to update (optional)
            
        Returns:
            ID of the subcontainer
        """
        print("___________________________________")
        id_registry = get_id_registry()
        # Handle existing vs. new subcontainer
        if existing_subcontainer_id:
            # Verify the subcontainer still exists
            subcontainer = self.get_subcontainer(existing_subcontainer_id)
            if not subcontainer:
                # Create a new one if the existing one is gone
                return self.deserialize_subcontainer(
                    type_id, location, serialized_subcontainer)
                
            # The ID stays the same
            subcontainer_id = existing_subcontainer_id
        else:
            # Create a new subcontainer
            subcontainer_id = self.add_subcontainer(type_id, location)
            if not subcontainer_id:
                return None
                
        print(f"The initial subcontainer_id: {subcontainer_id}")
        print(f"current_children_ids: {id_registry.get_widgets_by_container_id(subcontainer_id)}")
        # Update the subcontainer's ID
        success, subcontainer_id, error = id_registry.update_id(subcontainer_id, serialized_subcontainer['id'])
        if not success:
            raise ValueError(f"Failed to update ID for subcontainer {subcontainer_id}: {error}")
        print(f"The subcontainer_id after update: {subcontainer_id}")
        print(f"current_children_ids: {id_registry.get_widgets_by_container_id(subcontainer_id)}")
        # Deserialize children if included
        self._deserialize_children(subcontainer_id, serialized_subcontainer)

        print(f"___________________________________")
        return subcontainer_id
    
    def _deserialize_children(self, subcontainer_id: str, serialized_data: Dict):
        """
        Deserialize children of a subcontainer.
        
        Args:
            subcontainer_id: Subcontainer ID
            serialized_data: Serialized subcontainer data
        """
        print("######################################")
        id_registry = get_id_registry()
        print(f"subcontainer : {subcontainer_id} serialized_data: {serialized_data['children']}")
        if 'children' in serialized_data and isinstance(serialized_data['children'], dict):
            print("Passed first check")
            # Get all current child widgets that have this subcontainer as their container
            current_children_ids = id_registry.get_widgets_by_container_id(subcontainer_id)
            
            # Create a location map for newly created widgets
            new_widgets_by_location = {}
            
            # First, extract locations from all the current children
            for child_id in current_children_ids:
                widget = id_registry.get_widget(child_id)
                if widget:
                    # Parse the widget ID to get its location
                    parsed_id = parse_widget_id(child_id)
                    if parsed_id:
                        location_key = f"{parsed_id['container_location']}-{parsed_id['widget_location_id']}"
                        new_widgets_by_location[location_key] = (child_id, widget)
            print(f"new_widgets_by_location: {new_widgets_by_location}")
            
            # Process each serialized child
            for old_child_id, child_data in serialized_data['children'].items():
                # Parse the old ID to get its location
                parsed_old_id = parse_widget_id(old_child_id)
                if not parsed_old_id:
                    continue
                
                # Create a location key that combines container location and widget location ID
                location_key = f"{parsed_old_id['container_location']}-{parsed_old_id['widget_location_id']}"
                print(f"location_key: {location_key}")
                
                # Look for a widget with matching location in our current children
                if location_key in new_widgets_by_location:
                    new_child_id, new_child_widget = new_widgets_by_location[location_key]
                    
                    # Deserialize the child with matching location
                    if hasattr(new_child_widget, 'deserialize'):
                        new_child_widget.deserialize(child_data)
                else:
                    # No matching widget found - this might happen if widget structure changed
                    # Log this or handle as needed
                    pass
        print("######################################")