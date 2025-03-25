"""
Container widget interface for navigable UI components.

This module defines the interface for container widgets that can hold
command-aware widgets and activate them for navigation during undo/redo.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class ContainerWidget(ABC):
    """
    Interface for container widgets like docks and tabs.
    Implementations should allow navigation to specific child widgets.
    """
    
    @abstractmethod
    def activate_child(self, widget: Any) -> bool:
        """
        Activate the specified child widget.
        This may involve showing a tab, dock, or otherwise making the widget visible.
        
        Args:
            widget: The child widget to activate
            
        Returns:
            True if widget was successfully activated
        """
        pass
        
    @abstractmethod
    def get_container_id(self) -> str:
        """
        Get unique identifier for this container.
        
        Returns:
            Container identifier string
        """
        pass
        
    def register_child(self, widget: Any) -> None:
        """
        Register a child widget with this container.
        Default implementation registers with the widget context registry.
        
        Args:
            widget: Child widget to register
        """
        from ...core.widget_context import get_widget_context_registry
        
        registry = get_widget_context_registry()
        registry.register_widget_container(
            widget=widget,
            container=self,
            container_id=self.get_container_id()
        )