"""
Base container for integrating PySide6 containers with the command system.

Provides a lightweight base implementation for command-enabled containers
leveraging the ID system for efficient relationship tracking.
"""
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Type
import uuid
import inspect
from PySide6.QtWidgets import QWidget

from command_system.id_system import get_id_registry, TypeCodes, extract_location
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
            func_name = factory_func.__name__
            type_id = f"{func_name}_{str(uuid.uuid4())[:8]}"
        
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
        
        # Get type info
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
            widget_id = self.register_child(widget, location)
            
            # Remember the widget type and created observables for later recreation
            id_registry = get_id_registry()
            widget_obj = id_registry.get_widget(widget_id)
            
            # Store recreation info
            recreation_info = {
                "type_id": type_id,
                "created_observables": [
                    {"class": type(obs).__name__, "id": obs.get_id()}
                    for obs in created_observables
                ],
                "observable_ids": [
                    obs if isinstance(obs, str) else None
                    for obs in registered_observables
                ]
            }
            
            if hasattr(widget_obj, "set_context_info"):
                widget_obj.set_context_info("recreation_info", recreation_info)
            
            # Add the widget to the container - must be implemented by subclasses
            self._add_widget_to_container(widget, location, type_info["options"])
            
            return widget_id
        
        except Exception as e:
            print(f"Error creating widget of type {type_id}: {e}")
            return None
    
    def register_child(self, widget: QWidget, location: str) -> str:
        """Register a child widget with this container."""
        id_registry = get_id_registry()
        
        if isinstance(widget, BaseCommandWidget):
            # Already a command widget, just update container
            widget.update_container(self.widget_id)
            widget.update_location(location)
            return widget.widget_id
        else:
            # Regular QWidget, register with ID system
            return id_registry.register(
                widget, 
                TypeCodes.CUSTOM_WIDGET, 
                None,
                self.widget_id, 
                location
            )
    
    def unregister_child(self, widget: Union[QWidget, str]) -> bool:
        """Unregister a child widget from this container."""
        id_registry = get_id_registry()
        
        # Get widget ID
        widget_id = widget if isinstance(widget, str) else id_registry.get_id(widget)
        if not widget_id:
            return False
        
        # If it's a BaseCommandWidget, just update its container reference
        if isinstance(widget, BaseCommandWidget):
            widget.update_container(None)
            return True
        else:
            # Otherwise remove the container reference in the ID system
            return id_registry.remove_container_reference(widget_id) != ""
    
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
    
    def navigate_to_container(self, trigger_widget=None, container_info=None) -> bool:
        """
        Navigate to this container's context.
        Used by command manager for restoration during undo/redo.
        
        Should be implemented by container subclasses.
        """
        # First navigate to parent container if exists
        parent_container_id = get_id_registry().get_container_id_from_widget_id(self.widget_id)
        if parent_container_id:
            parent_container = get_id_registry().get_widget(parent_container_id)
            if parent_container and hasattr(parent_container, 'navigate_to_container'):
                parent_container.navigate_to_container()
        
        return True