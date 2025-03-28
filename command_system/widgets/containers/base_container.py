"""
Base container mixin for command-aware container widgets.

This module provides a mixin class for container widgets like tabs and docks
that implement the necessary methods for command navigation and dynamic content.
"""
from typing import Any, Optional, Dict, Callable, TypeVar, List
from PySide6.QtWidgets import QWidget
import uuid

# Type for container content
T = TypeVar('T')

class ContainerWidgetMixin:
    """
    Mixin class for container widgets that can activate child widgets.
    This provides common functionality for all container types including
    dynamic content creation and persistence.
    """
    
    def __init__(self, container_id: str = None):
        """
        Initialize the container mixin.
        
        Args:
            container_id: Optional unique ID for this container
        """
        # This will be called by __init__ of the actual widget class that uses this mixin
        self.container = None  # Refers to the container of this container if it exists
        self.container_info = None  # Additional container info
        
        # Set container ID (generate if not provided)
        self._container_id = container_id or str(uuid.uuid4())
        
        # Dictionary of registered content types
        # Key: content_type_id, Value: (factory_function, display_name, options)
        self._content_types = {}
        
        # Dictionary of content instances
        # Key: instance_id, Value: (content_widget, content_type_id, params)
        self._content_instances = {}
    
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
            container_info: Optional additional information about the container
        """
        widgets_to_process = [widget]
        
        while widgets_to_process:
            current_widget = widgets_to_process.pop(0)
            
            # Set this container as the widget's container
            if hasattr(current_widget, "container"):
                current_widget.container = self
                current_widget.container_info = container_info
            
            # Process child widgets - even for container widgets
            # This allows nested containers to work properly
            if isinstance(current_widget, QWidget):
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
    
    # ===== Dynamic Container Methods =====
    # MARK: Dynamic Container
    def register_content_type(self, content_type_id: str, factory_func: Callable, 
                             display_name: str = None, dynamic: bool = False, 
                             closable: bool = False, **options) -> str:
        """
        Register a content type with this container.
        
        Args:
            content_type_id: Unique identifier for this content type
            factory_func: Function that creates the content widget
            display_name: Human-readable name for this content type
            dynamic: Whether multiple instances can be created
            closable: Whether instances can be closed by the user
            options: Additional options for this content type
            
        Returns:
            The content type ID (same as input if provided)
        """
        type_id = content_type_id or str(uuid.uuid4())
        self._content_types[type_id] = {
            'factory': factory_func,
            'display_name': display_name or type_id,
            'dynamic': dynamic,
            'closable': closable,
            'options': options
        }
        return type_id
    
    def add(self, content_type_id: str, instance_id: str = None, **params) -> str:
        """
        Add a new instance of a registered content type.
        
        Args:
            content_type_id: ID of the registered content type
            instance_id: Optional unique ID for this instance (generated if not provided)
            params: Parameters to pass to the factory function
            
        Returns:
            ID of the created instance
        """
        if content_type_id not in self._content_types:
            raise ValueError(f"Unknown content type: {content_type_id}")
        
        # Generate instance ID if not provided
        if not instance_id:
            instance_id = f"{content_type_id}_{str(uuid.uuid4())}"
        
        # Create content using factory function
        content_type = self._content_types[content_type_id]
        factory_func = content_type['factory']
        
        # Create the content widget
        content_widget = factory_func(**params)
        
        # Store instance info
        self._content_instances[instance_id] = {
            'widget': content_widget,
            'type_id': content_type_id,
            'params': params
        }
        
        # Add to container - this must be implemented by subclasses
        self._add_content_to_container(content_widget, instance_id, content_type)
        
        return instance_id
    
    def _add_content_to_container(self, content_widget: QWidget, instance_id: str, content_type: Dict):
        """
        Add a content widget to this container.
        Must be implemented by subclasses.
        
        Args:
            content_widget: Widget to add
            instance_id: ID of the instance
            content_type: Content type info dictionary
        """
        raise NotImplementedError("Subclasses must implement _add_content_to_container")
    
    def close_content(self, instance_id: str) -> bool:
        """
        Close a content instance.
        
        Args:
            instance_id: ID of the instance to close
            
        Returns:
            True if instance was successfully closed
        """
        if instance_id not in self._content_instances:
            return False
        
        # Get instance info
        instance = self._content_instances[instance_id]
        
        # Implementation-specific close operation - must be implemented by subclasses
        result = self._close_content(instance['widget'], instance_id)
        
        if result:
            # Clean up instance
            del self._content_instances[instance_id]
        
        return result
    
    def _close_content(self, content_widget: QWidget, instance_id: str) -> bool:
        """
        Close a content widget in this container.
        Must be implemented by subclasses.
        
        Args:
            content_widget: Widget to close
            instance_id: ID of the instance
            
        Returns:
            True if content was successfully closed
        """
        raise NotImplementedError("Subclasses must implement _close_content")
    
    # State persistence methods will be added in future implementations
    # when the serialization system is integrated
    
    def get_registered_content_types(self) -> List[str]:
        """
        Get list of registered content type IDs.
        
        Returns:
            List of content type IDs
        """
        return list(self._content_types.keys())
    
    def get_content_instances(self) -> List[str]:
        """
        Get list of content instance IDs.
        
        Returns:
            List of instance IDs
        """
        return list(self._content_instances.keys())

    def _unbind_all_command_widgets(self, parent_widget: QWidget):
        """
        Recursively unbind all command widgets within a parent widget.
        """
        for widget in parent_widget.findChildren(QWidget):
            if hasattr(widget, 'unbind_from_model') and callable(widget.unbind_from_model):
                widget.unbind_from_model()