"""
Widget context registry for tracking widget containers.

This module provides a registry for tracking which container holds each widget,
enabling navigation during command undo/redo operations.
"""
from typing import Dict, Any, Optional


class WidgetContextRegistry:
    """
    Registry to track widget container relationships.
    Maps widgets to their container context information.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = WidgetContextRegistry()
        return cls._instance
    
    def __init__(self):
        """Initialize the registry."""
        if WidgetContextRegistry._instance is not None:
            raise RuntimeError("Use WidgetContextRegistry.get_instance() to get the singleton instance")
            
        WidgetContextRegistry._instance = self
        self._widget_contexts = {}
        
    def register_widget_container(self, widget: Any, container: Any, container_id: str) -> None:
        """
        Register a widget with its container.
        
        Args:
            widget: The widget to register
            container: The container holding the widget
            container_id: Unique identifier for the container
        """
        self._widget_contexts[widget] = {
            "container": container,
            "container_id": container_id,
            "container_type": container.__class__.__name__,
            "widget": widget
        }
        
    def unregister_widget(self, widget: Any) -> None:
        """
        Unregister a widget from the registry.
        
        Args:
            widget: The widget to unregister
        """
        if widget in self._widget_contexts:
            del self._widget_contexts[widget]
            
    def get_widget_container(self, widget: Any) -> Optional[Dict[str, Any]]:
        """
        Get container context for a widget.
        
        Args:
            widget: The widget to look up
            
        Returns:
            Container context dictionary or None if not registered
        """
        return self._widget_contexts.get(widget, None)


def get_widget_context_registry():
    """
    Get the singleton widget context registry instance.
    
    Returns:
        WidgetContextRegistry singleton instance
    """
    return WidgetContextRegistry.get_instance()