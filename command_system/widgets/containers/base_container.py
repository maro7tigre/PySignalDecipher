"""
Base container mixin for command-aware container widgets.

This module provides a mixin class for container widgets like tabs and docks
that implement the necessary methods for command navigation.
"""
from typing import Any, Optional
from ...core.widget_context import get_widget_context_registry

class ContainerWidgetMixin:
    """
    Mixin class for container widgets that can activate child widgets.
    This provides common functionality for all container types.
    """
    
    def __init__(self, container_id=None):
        """
        Initialize the container mixin.
        
        Args:
            container_id: Optional unique ID for this container
        """
        # This will be called by __init__ of the actual widget class that uses this mixin
        self._container_id = container_id or f"container_{id(self)}"
        
    def get_container_id(self) -> str:
        """
        Get unique identifier for this container.
        
        Returns:
            Container identifier string
        """
        return self._container_id
        
    def register_child(self, widget: Any) -> None:
        """
        Register a child widget with this container.
        
        Args:
            widget: Child widget to register
        """
        
        registry = get_widget_context_registry()
        registry.register_widget_container(
            widget=widget,
            container=self,
            container_id=self.get_container_id()
        )
    
    def activate_child(self, widget: Any) -> bool:
        """
        Activate the specified child widget.
        Must be implemented by subclasses.
        
        Args:
            widget: The child widget to activate
            
        Returns:
            True if widget was successfully activated
        """
        raise NotImplementedError("Subclasses must implement activate_child")