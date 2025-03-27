"""
Command-aware tab widget with dynamic content support.

This module provides a tab widget that implements container functionality
for navigation during undo/redo operations and supports dynamic content creation.
"""
from typing import Any, Dict, Callable, Optional
import uuid

from PySide6.QtWidgets import QTabWidget, QWidget, QTabBar
from PySide6.QtCore import Signal, Slot, Qt

from .base_container import ContainerWidgetMixin


class CommandTabWidget(QTabWidget, ContainerWidgetMixin):
    """
    A tab widget that supports command-based navigation and dynamic content creation.
    """
    
    # Signal emitted when a tab is added
    tabAdded = Signal(str)  # instance_id
    
    # Signal emitted when a tab is closed
    tabClosed = Signal(str)  # instance_id
    
    def __init__(self, parent=None, container_id=None):
        """
        Initialize the command tab widget.
        
        Args:
            parent: Parent widget
            container_id: Optional unique ID for this container
        """
        QTabWidget.__init__(self, parent)
        ContainerWidgetMixin.__init__(self, container_id)
        
        # Connect tab close signal if available
        if hasattr(self, 'tabCloseRequested'):
            self.setTabsClosable(True)
            self.tabCloseRequested.connect(self._on_tab_close_requested)
        
        # Map from tab index to instance ID for tracking
        self._tab_instance_map = {}
    
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
            tab: Tab widget to add
            label: Tab label
            
        Returns:
            Index of the new tab
        """
        index = super().addTab(tab, label)
        self.register_contents(tab, {"tab_index": index})
        return index
    
    def set_tab_closable(self, index: int, closable: bool) -> None:
        """
        Set whether a specific tab should be closable.
        
        Args:
            index: Tab index
            closable: Whether the tab should be closable
        """
        try:
            # Keep all tabs closable at Qt level
            self.setTabsClosable(True)
            
            # Store closable state in tab data
            self.tabBar().setTabData(index, {"closable": closable})
            
            # Get the close button for this tab
            button_position = QTabBar.RightSide
            close_button = self.tabBar().tabButton(index, button_position)
            
            # If we have a button, control its visibility
            if close_button:
                close_button.setVisible(closable)
        except Exception as e:
            print(f"Error setting tab closability: {e}")
    
    # ===== Dynamic Content Methods =====
    
    def register_tab(self, factory_func: Callable, tab_name: str = None, 
                    dynamic: bool = False, closable: bool = False, 
                    **options) -> str:
        """
        Register a tab type that can be dynamically created.
        
        Args:
            factory_func: Function that creates the tab content
            tab_name: Display name for the tab
            dynamic: Whether multiple instances can be created
            closable: Whether tabs can be closed by the user
            options: Additional options for this tab type
            
        Returns:
            ID of the registered tab type
        """
        # Generate a type ID based on the tab name if not provided
        type_id = options.pop('type_id', tab_name.lower().replace(' ', '_') if tab_name else None)
        return self.register_content_type(
            type_id, factory_func, display_name=tab_name, 
            dynamic=dynamic, closable=closable, **options
        )
    
    def add_tab(self, tab_type_id: str, tab_id: str = None, **params) -> str:
        """
        Add a new tab of a registered type.
        
        Args:
            tab_type_id: ID of the registered tab type
            tab_id: Optional unique ID for this tab (generated if not provided)
            params: Parameters to pass to the factory function
            
        Returns:
            ID of the created tab
        """
        return self.add(tab_type_id, instance_id=tab_id, **params)
    
    def _add_content_to_container(self, content_widget: QWidget, instance_id: str, content_type: Dict):
        """
        Add a tab to this tab widget.
        
        Args:
            content_widget: Widget to add as a tab
            instance_id: ID of the tab instance
            content_type: Tab type info dictionary
        """
        # Add the tab
        display_name = content_type['display_name']
        index = self.addTab(content_widget, display_name)
        
        # Set tab closability
        closable = content_type.get('closable', False)
        self.set_tab_closable(index, closable)
        
        # Store the instance ID for this tab index
        self._tab_instance_map[index] = instance_id
        
        # Emit signal
        self.tabAdded.emit(instance_id)
        
        # Set as current if it's the first tab
        if self.count() == 1:
            self.setCurrentIndex(0)
    
    def close_tab(self, instance_id: str) -> bool:
        """
        Close a tab by instance ID.
        
        Args:
            instance_id: ID of the tab to close
            
        Returns:
            True if tab was successfully closed
        """
        return self.close_content(instance_id)
    
    def _close_content(self, content_widget: QWidget, instance_id: str) -> bool:
        """
        Close a tab in this tab widget.
        
        Args:
            content_widget: Widget to close
            instance_id: ID of the tab instance
            
        Returns:
            True if tab was successfully closed
        """
        # Find the tab index for this instance ID
        index = None
        for idx, tab_id in list(self._tab_instance_map.items()):
            if tab_id == instance_id:
                index = idx
                break
        
        if index is None:
            return False
        
        # Check if the index is still valid
        if index >= self.count():
            # Invalid index, clean up the map
            if index in self._tab_instance_map:
                del self._tab_instance_map[index]
            return False
        
        # Remove the tab
        self.removeTab(index)
        
        # Clean up the map
        if index in self._tab_instance_map:
            del self._tab_instance_map[index]
        
        # Update indices for remaining tabs - create a new map to avoid modification during iteration
        new_map = {}
        for i in range(self.count()):
            tab_widget = self.widget(i)
            for old_idx, tab_id in list(self._tab_instance_map.items()):
                if old_idx < self.count() and self.widget(old_idx) == tab_widget:
                    new_map[i] = tab_id
                    break
        
        # Replace the old map with the updated one
        self._tab_instance_map = new_map
        
        # Emit signal
        self.tabClosed.emit(instance_id)
        
        return True
    
    @Slot(int)
    def _on_tab_close_requested(self, index: int):
        """
        Handle tab close request from UI.
        
        Args:
            index: Index of the tab to close
        """
        # Check if tab is closable from stored data
        tab_data = self.tabBar().tabData(index)
        if tab_data and not tab_data.get("closable", True):
            print(f"Tab '{self.tabText(index)}' is not closable")
            return
            
        # Continue with original close logic
        if index in self._tab_instance_map:
            instance_id = self._tab_instance_map[index]
            self.close_tab(instance_id)
    
    def navigate_to_container(self, widget=None, info=None):
        """
        Navigate to the appropriate tab.
        
        Args:
            widget: Optional widget to focus on
            info: Optional additional navigation info
            
        Returns:
            True if navigation was successful
        """
        # First ensure parent containers are visible
        if hasattr(self, "container") and self.container:
            self.container.navigate_to_container()
        
        # Switch to specific tab if info contains tab index
        if info and "tab_index" in info:
            tab_index = info["tab_index"]
            if 0 <= tab_index < self.count():
                self.setCurrentIndex(tab_index)
        
        # Activate specific widget if provided
        if widget:
            return self.activate_child(widget)
        
        return True