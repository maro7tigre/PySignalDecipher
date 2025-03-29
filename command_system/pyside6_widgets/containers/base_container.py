"""
Base container for integrating PySide6 containers with the command system.

This module provides a base implementation for all command-enabled containers,
extending the base widget with container-specific functionality.
"""
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from PySide6.QtWidgets import QWidget

from command_system.id_system import get_id_registry, TypeCodes
from ..base_widget import BaseCommandWidget

class BaseCommandContainer(BaseCommandWidget):
    """
    Base class for all command-system enabled containers.
    
    Provides container-specific functionality for child management and navigation.
    """
    
    def __init__(self):
        """
        Empty initializer to avoid multiple inheritance issues.
        Child classes should call initiate_widget after their own initialization.
        """
        pass
    
    def initiate_container(self, type_code: str, container_id: Optional[str] = None, 
                 location: Optional[str] = None):
        """
        Initialize the base command container.
        
        Args:
            type_code: Type code for ID system
            container_id: Optional ID of the parent container
            location: Optional location within the container
        """
        # Initialize the base class
        super().initiate_widget(type_code, container_id, location)
        
        # Container-specific state
        self._child_locations: Dict[str, str] = {}  # Widget ID -> Location string
    
    def register_child(self, widget: Union[QWidget, BaseCommandWidget], location: str) -> str:
        """
        Register a child widget with this container.
        
        Args:
            widget: Child widget to register
            location: Location identifier within this container
            
        Returns:
            Widget ID of the registered child
        """
        if not isinstance(widget, QWidget):
            raise TypeError("Child must be a QWidget")
            
        id_registry = get_id_registry()
        
        # Determine widget type code
        if isinstance(widget, BaseCommandWidget):
            # Already a command widget, just update container
            widget.update_container(self.widget_id)
            widget.update_location(location)
            widget_id = widget.widget_id
        else:
            # Regular QWidget, register with ID system
            widget_id = id_registry.register(
                widget, 
                TypeCodes.CUSTOM_WIDGET, 
                None,
                self.widget_id, 
                location
            )
        
        # Store child location
        self._child_locations[widget_id] = location
        
        return widget_id
    
    def unregister_child(self, widget: Union[QWidget, BaseCommandWidget, str]) -> bool:
        """
        Unregister a child widget from this container.
        
        Args:
            widget: Child widget or widget ID to unregister
            
        Returns:
            True if successfully unregistered
        """
        id_registry = get_id_registry()
        
        # Get widget ID
        if isinstance(widget, str):
            widget_id = widget
        else:
            widget_id = id_registry.get_id(widget)
            
        if not widget_id:
            return False
        
        # Remove from container tracking
        if widget_id in self._child_locations:
            del self._child_locations[widget_id]
        
        # If it's a BaseCommandWidget, just update its container reference
        if isinstance(widget, BaseCommandWidget):
            widget.update_container(None)
            return True
        else:
            # Otherwise remove the container reference in the ID system
            return id_registry.remove_container_reference(widget_id) != ""
    
    def get_child_location(self, widget: Union[QWidget, BaseCommandWidget, str]) -> Optional[str]:
        """
        Get the location of a child widget.
        
        Args:
            widget: Child widget or widget ID
            
        Returns:
            Location string or None if not found
        """
        id_registry = get_id_registry()
        
        # Get widget ID
        if isinstance(widget, str):
            widget_id = widget
        else:
            widget_id = id_registry.get_id(widget)
            
        if not widget_id:
            return None
            
        return self._child_locations.get(widget_id)
    
    def get_children(self) -> List[Tuple[str, str]]:
        """
        Get all child widgets.
        
        Returns:
            List of (widget_id, location) tuples
        """
        return [(widget_id, location) for widget_id, location in self._child_locations.items()]
    
    def get_children_at_location(self, location: str) -> List[str]:
        """
        Get all child widgets at a specific location.
        
        Args:
            location: Location to check
            
        Returns:
            List of widget IDs at the specified location
        """
        return [widget_id for widget_id, loc in self._child_locations.items() if loc == location]
    
    def navigate_to_container(self, trigger_widget: Any, container_info: Dict[str, Any]) -> bool:
        """
        Navigate to this container's context.
        Used by command manager for restoration during undo/redo.
        
        Args:
            trigger_widget: Widget that triggered the command
            container_info: Container-specific navigation information
            
        Returns:
            True if navigation was successful
        """
        # Base implementation does nothing
        # Subclasses should override to implement container-specific navigation
        return False