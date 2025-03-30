"""
Base container for integrating PySide6 containers with the command system.

Provides a lightweight base implementation for command-enabled containers
leveraging the ID system for efficient relationship tracking.
"""
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Type
import uuid
import inspect
from PySide6.QtWidgets import QWidget

from command_system.id_system import get_id_registry, TypeCodes, extract_location, get_simple_id_registry
from command_system.core import Observable
from ..base_widget import BaseCommandWidget

class BaseCommandContainer(BaseCommandWidget):
    """
    Base class for all command-system enabled containers.
    
    Provides essential container-specific functionality while leveraging the ID system
    for relationship tracking and widget factory registration.
    """
    
    def initiate_container(self, type_code: str, container_id: Optional[str] = None, 
                           location: Optional[str] = None):
        """Initialize the container with type code and optional parent."""
        # Initialize the base widget
        super().initiate_widget(type_code, container_id, location)
        
        # Widget type registry
        self._widget_types = {}  # type_id -> {factory, observables, options}
    
    def register_widget_type(self, factory_func: Callable, 
                           observables: List[Union[str, Type[Observable]]] = None,
                           type_id: str = None,
                           **options) -> str:
        """
        Register a widget factory function.
        
        Args:
            factory_func: Function that creates a widget
            observables: List of Observable IDs or Observable classes
                         IDs will use existing observables
                         Classes will create new instances
            type_id: Optional unique ID for this widget type
            **options: Additional options like closable, dynamic, etc.
            
        Returns:
            Unique ID for the registered widget type
        """
        # Generate type_id if not provided
        if type_id is None:
            # Use function name as part of the ID for better debugging
            function_name = factory_func.__name__
            simple_id_registry = get_simple_id_registry()
            type_id = simple_id_registry.register(function_name, self.type_code)
        # Store widget type info
        self._widget_types[type_id] = {
            "factory": factory_func,
            "observables": observables or [],
            "options": options
        }
        
        return type_id
    
    def add_widget(self, type_id: str, location: str = "0") -> Optional[str]:
        """
        Create and add a widget of the registered type.
        
        Args:
            type_id: ID of the registered widget type
            location: Location identifier within this container
            
        Returns:
            Widget ID of the created widget, or None if failed
        """
        # Check if the type exists
        if type_id not in self._widget_types:
            return None
        print(f"adding container {type_id}")
        # Get type info
        type_info = self._widget_types[type_id]
        factory = type_info["factory"]
        registered_observables = type_info["observables"]
        
        # Prepare arguments - resolve observables
        factory_args = []
        created_observables = []
        
        # Process observables #TODO: add support for properties
        for obs in registered_observables:
            if isinstance(obs, str):
                # It's an ID - get the existing observable
                id_registry = get_id_registry()
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
            # Create the widget
            widget = factory(*factory_args)
            
            if not isinstance(widget, QWidget):
                print(f"Factory {type_id} didn't return a QWidget")
                return None
            
            # Register the widget with this container
            widgets_ids = self.register_child(widget, location, type_info)

            
            # Add the widget to the container - must be implemented by subclasses
            self._add_widget_to_container(widget, location, type_info["options"])
            
            return widgets_ids
        
        except Exception as e:
            print(f"Error creating widget of type {type_id}: {e}")
            return None
    
    def register_child(self, widget: QWidget, location: str, type_info: Dict) -> None:
        """Register a widget and all BaseCommandWidget children with this container."""
        id_registry = get_id_registry()
        widgets_ids = []
        
        widgets_to_process = [widget]
        while widgets_to_process:
            current_widget = widgets_to_process.pop(0)
            
            if isinstance(current_widget, BaseCommandWidget):
                # It's a command widget - check if already registered
                widget_id = id_registry.get_id(current_widget)
                if widget_id:
                    # Already registered, update container and location
                    current_widget.update_container(self.widget_id)
                    current_widget.update_location(location)
                else:
                    # Not registered, register it
                    type_code = current_widget.type_code
                    widget_id = id_registry.register(
                        current_widget, type_code, None, self.widget_id, location
                    )
                widgets_ids.append(widget_id)
                self._add_widget_to_container(widget, location, type_info["options"])
                    
            elif isinstance(current_widget, QWidget):
                # Regular widget - add its children to process
                child_widgets = current_widget.findChildren(QWidget)
                widgets_to_process.extend(child_widgets)
        return widgets_ids
        
    
    def unregister_childs(self, location = None) -> bool:
            """
            Unregister a child widget and all its children from this container.
            
            Args:
                widget: Widget object or ID to unregister
                
            Returns:
                True if successful, False otherwise
            """
            id_registry = get_id_registry()
            
                
            # Get all child widgets if this is itself a container
            if location is None:
                child_ids = id_registry.get_widget_ids_by_container_id(self.widget_id)
            else :
                child_ids = id_registry.get_widget_ids_by_container_id_and_location(self.widget_id, location)
                
                
            # Unregister all children first
            for child_id in child_ids:
                child_widget = id_registry.get_widget(child_id)
                if child_widget:
                    if hasattr(child_widget, 'unregister_widget'):
                        child_widget.unregister_widget()
                    else:
                        id_registry.unregister(child_id)
    
    def get_child_widgets(self) -> List[QWidget]:
        """Get all child widgets of this container."""
        id_registry = get_id_registry()
        child_ids = id_registry.get_widget_ids_by_container_id(self.widget_id)
        
        return [id_registry.get_widget(widget_id) for widget_id in child_ids 
                if id_registry.get_widget(widget_id) is not None]
    
    def get_widgets_at_location(self, location: str) -> List[QWidget]:
        """Get all widgets at a specific location."""
        id_registry = get_id_registry()
        widget_ids = id_registry.get_widget_ids_by_container_id_and_location(
            self.widget_id, location)
        
        return [id_registry.get_widget(widget_id) for widget_id in widget_ids 
                if id_registry.get_widget(widget_id) is not None]
    
    def _add_widget_to_container(self, widget: QWidget, location: str, options: Dict) -> None:
        """
        Add a widget to this container at the specified location.
        Must be implemented by container subclasses.
        
        Args:
            widget: Widget to add
            location: Location identifier
            options: Widget type options
        """
        raise NotImplementedError(
            f"_add_widget_to_container not implemented in {self.__class__.__name__}"
        )
    
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
        
        # Now navigate to the target's location within this container
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
    
    def unregister_widget(self) -> None:
        """Unregister this widget and its children."""
        id_registry = get_id_registry()
        id_registry.unregister(self.widget_id)
        
        # Unregister all child widgets
        self.unregister_childs()
        
        # TODO: consider more cleanup