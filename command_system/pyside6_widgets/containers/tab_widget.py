"""
Command-aware tab widget with simplified implementation.

Provides a tab widget that integrates with the command system
for undo/redo functionality while being easy to debug and maintain.
"""
from typing import Any, Dict, Optional, List, Callable, Union, Type
from PySide6.QtWidgets import QTabWidget, QWidget, QTabBar
from PySide6.QtCore import Signal, Slot

from command_system.id_system import get_id_registry, TypeCodes
from command_system.core import get_command_manager, Command, Observable
from .base_container import BaseCommandContainer

class CommandTabWidget(QTabWidget, BaseCommandContainer):
    """
    A tab widget with command system integration.
    
    Tracks tab operations with the ID system for undo/redo support.
    Supports widget type registration and dynamic tab creation.
    """
    
    # Signal emitted when a tab is added or closed
    tabAdded = Signal(str)      # widget_id
    tabClosed = Signal(str)     # widget_id
    
    def __init__(self, parent=None, container_id=None, location=None):
        """Initialize the command tab widget."""
        # Initialize QTabWidget
        QTabWidget.__init__(self, parent)
        
        # Initialize container with TAB_CONTAINER type
        self.initiate_container(TypeCodes.TAB_CONTAINER, container_id, location)
        
        # Connect signals
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.currentChanged.connect(self._on_current_changed)
    
    def addTab(self, widget: QWidget, label: str) -> int:
        """Override to register the widget with this container."""
        # Add the tab using the parent implementation
        index = super().addTab(widget, label)
        
        # Register with container using index as location
        self.register_child(widget, str(index))
        
        # Emit our signal
        widget_id = get_id_registry().get_id(widget)
        if widget_id:
            self.tabAdded.emit(widget_id)
        
        # Update locations of all tabs (in case of insertion)
        self._update_tab_locations()
        
        return index
    
    def insertTab(self, index: int, widget: QWidget, label: str) -> int:
        """Override to register the widget and update locations."""
        # Insert the tab using the parent implementation
        index = super().insertTab(index, widget, label)
        
        # Register with container using index as location
        self.register_child(widget, str(index))
        
        # Emit our signal
        widget_id = get_id_registry().get_id(widget)
        if widget_id:
            self.tabAdded.emit(widget_id)
        
        # Update locations of all tabs
        self._update_tab_locations()
        
        return index
    
    def removeTab(self, index: int) -> None:
        """Override to unregister the widget and update locations."""
        # Get the widget before removal
        widget = self.widget(index)
        if widget:
            widget_id = get_id_registry().get_id(widget)
            
            # Remove the tab using the parent implementation
            super().removeTab(index)
            
            # Unregister from our container
            if widget_id:
                self.unregister_child(widget)
                self.tabClosed.emit(widget_id)
            
            # Update locations of all tabs
            self._update_tab_locations()
    
    def _update_tab_locations(self) -> None:
        """Update location IDs for all tabs."""
        # Iterate through all tabs and update their locations
        for i in range(self.count()):
            widget = self.widget(i)
            if widget:
                widget_id = get_id_registry().get_id(widget)
                if widget_id:
                    get_id_registry().update_location(widget_id, str(i))
    
    def register_tab(self, factory_func: Callable, tab_name: str = None,
                    observables: List[Union[str, Type[Observable]]] = None, 
                    closable: bool = True) -> str:
        """
        Register a tab type with factory function.
        
        Args:
            factory_func: Function that creates the tab content
            tab_name: Display name for tabs of this type
            observables: List of Observable IDs or Observable classes
                         IDs will use existing observables
                         Classes will create new instances
            closable: Whether tabs of this type can be closed
            
        Returns:
            ID of the registered tab type
        """
        options = {"tab_name": tab_name, "closable": closable}
        return self.register_widget_type(factory_func, observables, **options)
    
    def add_tab(self, type_id: str) -> str:
        """
        Add a new tab of the registered type.
        
        Args:
            type_id: ID of the registered tab type
            
        Returns:
            ID of the created tab
        """
        # Check if we're in a command execution
        if get_command_manager().is_updating():
            return self.add_widget(type_id, str(self.count()))
        
        # Create a command for adding a tab
        class AddTabCommand(Command):
            def __init__(self, tab_widget, type_id):
                super().__init__()
                self.tab_widget = tab_widget
                self.type_id = type_id
                self.widget_id = None
                
            def execute(self):
                self.widget_id = self.tab_widget.add_widget(
                    self.type_id, str(self.tab_widget.count())
                )
                
            def undo(self):
                if self.widget_id:
                    # Find the widget
                    id_registry = get_id_registry()
                    widget = id_registry.get_widget(self.widget_id)
                    if widget:
                        # Find its tab index
                        for i in range(self.tab_widget.count()):
                            if self.tab_widget.widget(i) == widget:
                                self.tab_widget.removeTab(i)
                                break
        
        # Create and execute the command
        cmd = AddTabCommand(self, type_id)
        cmd.set_trigger_widget(self.widget_id)
        get_command_manager().execute(cmd)
        
        return cmd.widget_id
    
    def _add_widget_to_container(self, widget: QWidget, location: str, options: Dict) -> None:
        """
        Add a widget as a tab to this tab widget.
        
        Args:
            widget: Widget to add as tab content
            location: Tab index as string (ignored, we append)
            options: Widget type options
        """
        # Get tab name from options or use default
        tab_name = options.get("tab_name", "Tab")
        
        # Add the tab
        index = self.addTab(widget, tab_name)
        
        # Set tab closability if specified
        if "closable" in options:
            self.set_tab_closable(index, options["closable"])
        
        # Set as current tab if specified
        if options.get("make_current", True):
            self.setCurrentIndex(index)
    
    def set_tab_closable(self, index: int, closable: bool = True) -> None:
        """
        Set whether a specific tab should be closable.
        
        Args:
            index: Tab index
            closable: Whether the tab should be closable (True by default)
        """
        # Keep all tabs closable at the Qt level, but control the button visibility
        self.setTabsClosable(True)
        
        # Store closable state in tab data
        self.tabBar().setTabData(index, {"closable": closable})
        
        # Get the close button for this tab and control its visibility
        button_position = QTabBar.RightSide
        close_button = self.tabBar().tabButton(index, button_position)
        
        # If we have a button, control its visibility
        if close_button:
            close_button.setVisible(closable)
    
    @Slot(int)
    def _on_tab_close_requested(self, index: int) -> None:
        """Handle tab close request from UI."""
        # Check if tab is closable from stored data
        tab_data = self.tabBar().tabData(index)
        if tab_data and not tab_data.get("closable", True):
            # Tab is not closable, ignore the request
            return
            
        # Create a command to remove the tab
        class RemoveTabCommand(Command):
            def __init__(self, tab_widget, index):
                super().__init__()
                self.tab_widget = tab_widget
                self.index = index
                self.widget = tab_widget.widget(index)
                self.label = tab_widget.tabText(index)
                self.closable = tab_data.get("closable", True) if tab_data else True
                self.widget_id = get_id_registry().get_id(self.widget)
                
                # Get recreation info for undo
                self.recreation_info = None
                if self.widget_id:
                    widget = get_id_registry().get_widget(self.widget_id)
                    if hasattr(widget, "get_context_info"):
                        self.recreation_info = widget.get_context_info("recreation_info")
                
            def execute(self):
                self.tab_widget.removeTab(self.index)
                
            def undo(self):
                if self.recreation_info:
                    # Recreate using the factory with stored info
                    type_id = self.recreation_info["type_id"]
                    self.tab_widget.add_widget(type_id, str(self.index))
                else:
                    # Fallback to direct insertion
                    new_index = self.tab_widget.insertTab(self.index, self.widget, self.label)
                    # Restore closability state
                    self.tab_widget.set_tab_closable(new_index, self.closable)
        
        # Create and execute the command
        cmd = RemoveTabCommand(self, index)
        cmd.set_trigger_widget(self.widget_id)
        get_command_manager().execute(cmd)
    
    @Slot(int)
    def _on_current_changed(self, index: int) -> None:
        """Handle tab selection change."""
        # Skip if we're executing a command
        if get_command_manager().is_updating():
            return
            
        # Create a simple tab selection command
        class TabSelectionCommand(Command):
            def __init__(self, tab_widget, old_index, new_index):
                super().__init__()
                self.tab_widget = tab_widget
                self.old_index = old_index
                self.new_index = new_index
                
            def execute(self):
                self.tab_widget.setCurrentIndex(self.new_index)
                
            def undo(self):
                self.tab_widget.setCurrentIndex(self.old_index)
        
        # Execute the command (only if not triggered by another command)
        old_index = self.currentIndex()
        if old_index != index:  # Extra check to avoid unnecessary commands
            cmd = TabSelectionCommand(self, old_index, index)
            cmd.set_trigger_widget(self.widget_id)
            get_command_manager().execute(cmd)
    
    def navigate_to_container(self, trigger_widget=None, container_info=None) -> bool:
        """Navigate to the appropriate tab for undo/redo operations."""
        # First navigate to parent container if exists
        super().navigate_to_container(trigger_widget, container_info)
        
        # If we have a trigger widget, find and activate its tab
        if trigger_widget:
            for i in range(self.count()):
                tab_widget = self.widget(i)
                
                # Check if widget is this tab or inside it
                if tab_widget == trigger_widget or trigger_widget in tab_widget.findChildren(QWidget):
                    self.setCurrentIndex(i)
                    trigger_widget.setFocus()
                    return True
        
        # If we have container_info with a tab index
        if container_info and "tab_index" in container_info:
            tab_index = container_info["tab_index"]
            if 0 <= tab_index < self.count():
                self.setCurrentIndex(tab_index)
                return True
        
        return True