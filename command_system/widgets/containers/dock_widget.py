"""
Command-aware dock widget with dynamic content support.

This module provides a dock widget that implements container functionality
for navigation during undo/redo operations and supports dynamic content creation.
"""
from typing import Any, Dict, Callable, Optional
import uuid

from PySide6.QtWidgets import QDockWidget, QWidget, QMainWindow
from PySide6.QtCore import Signal, Qt

from .base_container import ContainerWidgetMixin


class CommandDockWidget(QDockWidget, ContainerWidgetMixin):
    """
    A dock widget that supports command-based navigation and dynamic content creation.
    """
    
    # Signal emitted when content is added
    contentAdded = Signal(str)  # instance_id
    
    # Signal emitted when content is removed
    contentRemoved = Signal(str)  # instance_id
    
    def __init__(self, dock_id: str, title: str, parent: Optional[QMainWindow] = None):
        """
        Initialize the command dock widget.
        
        Args:
            dock_id: Unique identifier for this dock
            title: Title to display in the dock header
            parent: Parent widget (typically the main window)
        """
        QDockWidget.__init__(self, title, parent)
        ContainerWidgetMixin.__init__(self, dock_id)
        
        # Set objectName to match dock_id for Qt
        self.setObjectName(dock_id)
        
        # Currently active content instance ID
        self._active_instance_id = None
        
    def activate_child(self, widget: Any) -> bool:
        """
        Activate this dock and focus the child widget.
        
        Args:
            widget: Widget to activate
            
        Returns:
            True if widget was activated
        """
        # Make the dock visible if it's not
        if not self.isVisible():
            self.setVisible(True)
            
        # Raise the dock to front if it's in a tab group
        self.raise_()
        
        # Set focus to the widget
        if widget and widget.isVisible():
            widget.setFocus()
            return True
            
        return False
        
    def setWidget(self, widget: QWidget) -> None:
        """
        Override to register the widget with this container.
        
        Args:
            widget: Widget to set as the dock content
        """
        super().setWidget(widget)
        if widget:
            self.register_contents(widget)
    
    # ===== Dynamic Content Methods =====
    
    def register_dock(self, factory_func: Callable, dock_name: str = None, 
                     dynamic: bool = False, closable: bool = True, 
                     **options) -> str:
        """
        Register a dock type that can be dynamically created.
        
        Args:
            factory_func: Function that creates the dock content
            dock_name: Display name for the dock
            dynamic: Whether multiple instances can be created
            closable: Whether dock can be closed by the user
            options: Additional options for this dock type
            
        Returns:
            ID of the registered dock type
        """
        # Generate a type ID based on the dock name if not provided
        type_id = options.pop('type_id', dock_name.lower().replace(' ', '_') if dock_name else None)
        return self.register_content_type(
            type_id, factory_func, display_name=dock_name, 
            dynamic=dynamic, closable=closable, **options
        )
    
    def add_dock(self, dock_type_id: str, dock_id: str = None, **params) -> str:
        """
        Add content of a registered type to this dock.
        
        Args:
            dock_type_id: ID of the registered dock type
            dock_id: Optional unique ID for this dock content (generated if not provided)
            params: Parameters to pass to the factory function
            
        Returns:
            ID of the created dock content
        """
        return self.add(dock_type_id, instance_id=dock_id, **params)
    
    def _add_content_to_container(self, content_widget: QWidget, instance_id: str, content_type: Dict):
        """
        Add content to this dock widget.
        
        Args:
            content_widget: Widget to add as dock content
            instance_id: ID of the content instance
            content_type: Content type info dictionary
        """
        # If this is the first content, just set it
        if not self._active_instance_id:
            self.setWidget(content_widget)
            self._active_instance_id = instance_id
            
            # Update title if provided
            if content_type['display_name']:
                self.setWindowTitle(content_type['display_name'])
                
            # Update closable state
            if content_type['closable']:
                self.setFeatures(self.features() | QDockWidget.DockWidgetClosable)
            else:
                self.setFeatures(self.features() & ~QDockWidget.DockWidgetClosable)
                
            # Emit signal
            self.contentAdded.emit(instance_id)
            return
        
        # If we already have content, we need to handle the case
        # For simplicity, we'll just replace the current content
        # In a real implementation, you might want to create a new dock widget
        current_widget = self.widget()
        if current_widget:
            current_widget.setParent(None)  # Remove from dock
            
        # Set the new content
        self.setWidget(content_widget)
        self._active_instance_id = instance_id
        
        # Update title if provided
        if content_type['display_name']:
            self.setWindowTitle(content_type['display_name'])
            
        # Emit signal
        self.contentAdded.emit(instance_id)
    
    def close_dock(self, instance_id: str) -> bool:
        """
        Close dock content by instance ID.
        
        Args:
            instance_id: ID of the content to close
            
        Returns:
            True if content was successfully closed
        """
        return self.close_content(instance_id)
    
    def _close_content(self, content_widget: QWidget, instance_id: str) -> bool:
        """
        Close content in this dock widget.
        
        Args:
            content_widget: Widget to close
            instance_id: ID of the content instance
            
        Returns:
            True if content was successfully closed
        """
        # Only allow closing the active content
        if instance_id != self._active_instance_id:
            return False
        
        # Remove the widget
        content_widget.setParent(None)
        self.setWidget(None)
        self._active_instance_id = None
        
        # Emit signal
        self.contentRemoved.emit(instance_id)
        
        # Hide the dock if set to auto-hide
        options = self._content_types.get(
            self._content_instances.get(instance_id, {}).get('type_id', ''), 
            {}
        ).get('options', {})
        
        if options.get('auto_hide_when_empty', True):
            self.setVisible(False)
        
        return True
    
    def navigate_to_container(self, widget=None, info=None):
        """Navigate to this dock widget."""
        # First ensure parent containers are visible
        if hasattr(self, "container") and self.container:
            self.container.navigate_to_container()
        
        # Make dock visible and raise it
        self.setVisible(True)
        self.raise_()
        
        # Activate specific widget if provided
        if widget:
            return self.activate_child(widget)
        
        return True