"""
Base container mixin for command-aware container widgets.

This module provides a mixin class for container widgets like tabs and docks
that implement the necessary methods for command navigation.
"""
from typing import Any, Optional
from PySide6.QtWidgets import QWidget

class ContainerWidgetMixin:
    """
    Mixin class for container widgets that can activate child widgets.
    This provides common functionality for all container types.
    """
    
    def __init__(self):
        """
        Initialize the container mixin.
        
        Args:
            container_id: Optional unique ID for this container
        """
        # This will be called by __init__ of the actual widget class that uses this mixin
        self.container = None #refers to the container of this container if it exists
        self.container_info = None #refers to the container of this container if it exists
        
    def get_container_id(self) -> str:
        """
        Get unique identifier for this container.
        
        Returns:
            Container identifier string
        """
        return self._container_id
    
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
    
    def register_contents(self, widget: Any, container_info=None) -> None:
        """
        Register a widget and all its children with this container.
        
        Args:
            widget: The widget to register
        """
        widgets_to_process = [widget]
        
        while widgets_to_process:
            current_widget = widgets_to_process.pop(0)
            
            # Set this container as the widget's container
            if hasattr(current_widget, "container"):
                current_widget.container = self
                current_widget.container_info = container_info
            else :
                # Add all child widgets to be processed
                child_widgets = current_widget.findChildren(QWidget)
                widgets_to_process.extend(child_widgets)

    def navigate_to_container(self, widget=None, info=None):
        """
        Navigate to this container and optionally focus on a specific widget.
        
        Args:
            widget: Optional widget to focus on
            info: Optional additional navigation info
            
        Returns:
            True if navigation was successful
        """
        # Make the container visible and active
        if hasattr(self, "setVisible"):
            self.setVisible(True)
            
        # If parent container exists, navigate to it first
        if hasattr(self, "container") and self.container:
            self.container.navigate_to_container()
            
        # Activate the specific widget if provided
        if widget:
            return self.activate_child(widget)
        
        return True