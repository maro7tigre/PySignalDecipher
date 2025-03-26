"""
Command-aware tab widget.

This module provides a tab widget that implements container functionality
for navigation during undo/redo operations.
"""
from typing import Any

from PySide6.QtWidgets import QTabWidget, QWidget

from .base_container import ContainerWidgetMixin


class CommandTabWidget(QTabWidget, ContainerWidgetMixin):
    """
    A tab widget that supports command-based navigation.
    """
    
    def __init__(self, parent=None, container_id=None):
        """
        Initialize the command tab widget.
        
        Args:
            parent: Parent widget
            container_id: Optional unique ID for this container
        """
        QTabWidget.__init__(self, parent)
        ContainerWidgetMixin.__init__(self, container_id)
        
    def activate_child(self, widget: Any) -> bool:
        """
        Activate the tab containing the specified widget.
        
        Args:
            widget: Widget to activate
            
        Returns:
            True if widget was found and activated
        """
        # Find the tab containing this widget
        for i in range(self.count()):
            tab_widget = self.widget(i)
            
            # Direct child case
            if tab_widget == widget:
                self.setCurrentIndex(i)
                widget.setFocus()
                return True
                
            # Nested case - check if widget is a descendant
            if self._is_descendant(tab_widget, widget):
                self.setCurrentIndex(i)
                widget.setFocus()
                print(f"Activating tab {i} for widget {widget}")
                return True
                
        return False
        
    def _is_descendant(self, parent: QWidget, widget: QWidget) -> bool:
        """
        Check if widget is a descendant of parent.
        
        Args:
            parent: Potential parent widget
            widget: Widget to check
            
        Returns:
            True if widget is a descendant of parent
        """
        descendants = parent.findChildren(QWidget)
        return widget in descendants
        
    def addTab(self, tab: QWidget, label: str) -> int:
        """
        Override to register the widget with this container.
        
        Args:
            widget: Tab widget to add
            label: Tab label
            
        Returns:
            Index of the new tab
        """
        index = super().addTab(tab, label)
        self.register_contents(tab)
        return index