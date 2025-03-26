"""
Command-aware dock widget.

This module provides a dock widget that implements container functionality
for navigation during undo/redo operations.
"""
from typing import Any, Optional

from PySide6.QtWidgets import QDockWidget, QWidget, QMainWindow

from .base_container import ContainerWidgetMixin


class CommandDockWidget(QDockWidget, ContainerWidgetMixin):
    """
    A dock widget that supports command-based navigation.
    """
    
    def __init__(self, dock_id: str, title: str, parent: Optional[QMainWindow] = None):
        """
        Initialize the command dock widget.
        
        Args:
            dock_id: Unique identifier for this dock
            title: Title to display in the dock header
            parent: Parent widget (typically the main window)
        """
        QDockWidget.__init__(self, title, parent)
        ContainerWidgetMixin.__init__(self)
        
        # Set objectName to match dock_id for Qt
        self.setObjectName(dock_id)
        
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
        
        self.register_contents(widget)
        
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