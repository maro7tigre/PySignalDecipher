"""
Command-aware tab widget with integrated command system support.

Provides a tab widget that integrates with the ID system and command system
for undo/redo functionality, serialization, and comprehensive state management.
"""
from typing import Any, Dict, Optional, List, Callable, Union, Type
from PySide6.QtWidgets import QTabWidget, QWidget, QTabBar, QVBoxLayout
from PySide6.QtCore import Signal, Slot

from command_system.id_system import get_id_registry, TypeCodes
from command_system.core import get_command_manager, Command, SerializationCommand, Observable
from .base_container import BaseCommandContainer

class CommandTabWidget(QTabWidget, BaseCommandContainer):
    """
    A tab widget with full command system integration.
    
    Manages a collection of tab subcontainers with proper ID tracking,
    serialization support, and undo/redo operations.
    """
    
    # Signals emitted when tabs are modified
    tabAdded = Signal(str)      # subcontainer_id
    tabClosed = Signal(str)     # subcontainer_id
    
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
    
    # MARK: - Tab Registration
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
        return self.register_subcontainer_type(factory_func, observables, None, **options)
    
    def add_tab(self, type_id: str) -> str:
        """
        Add a new tab of the registered type.
        
        Args:
            type_id: ID of the registered tab type
            
        Returns:
            ID of the created tab subcontainer
        """
        # Check if we're in a command execution
        if get_command_manager().is_updating():
            subcontainer_id = self.add_subcontainer(type_id)
            if subcontainer_id:
                # Emit signal for the new tab
                self.tabAdded.emit(subcontainer_id)
            return subcontainer_id
        
        # Create a command for adding a tab
        id_registry = get_id_registry()
        container_id = id_registry.get_id(self)
        cmd = AddTabCommand(type_id, container_id)
        cmd.set_trigger_widget(self.widget_id)
        get_command_manager().execute(cmd)
        return cmd.component_id
    
    # MARK: - Subcontainer Implementation
    def create_subcontainer(self, type_id: str, location: str = None) -> Optional[QWidget]:
        """
        Create an empty tab subcontainer for the specified type.
        
        Args:
            type_id: Type ID of the subcontainer
            location: Location for the subcontainer (tab index)
            
        Returns:
            The created tab container widget, or None if failed
        """
        # Get type info for the display name
        type_info = self._widget_types.get(type_id)
        if not type_info:
            return None
            
        # Get tab name from options or use default
        tab_name = type_info.get("options", {}).get("tab_name", "Tab")
        
        # Create an empty container widget for the tab
        tab_container = QWidget()
        
        # Use a layout for the tab content
        layout = QVBoxLayout(tab_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the tab
        index = self.addTab(tab_container, tab_name)
        
        # Convert location to integer index
        if location is not None:
            try:
                loc_index = int(location)
                # Move tab to the specified location if different
                if loc_index != index:
                    self.tabBar().moveTab(index, loc_index)
                    index = loc_index
            except ValueError:
                pass
        
        # Set tab closability if specified
        closable = type_info.get("options", {}).get("closable", True)
        self.set_tab_closable(index, closable)
        
        # Set as current tab if specified
        if type_info.get("options", {}).get("make_current", True):
            self.setCurrentIndex(index)
            
        # Update tab locations in case of insertion
        self.refresh_location()
        
        return tab_container, index
        
    def refresh_location(self) -> None:
        """Update location IDs for all tabs after changes."""
        # Iterate through all tabs and update their locations
        for i in range(self.count()):
            tab_widget = self.widget(i)
            if tab_widget:
                widget_id = get_id_registry().get_id(tab_widget)
                if widget_id:
                    get_id_registry().update_location(widget_id, str(i))
                    
                    # Also update our locations map
                    if widget_id in self._subcontainers:
                        self._locations_map[widget_id] = str(i)
    
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
    
    # MARK: - Navigation
    def navigate_to_location(self, location: str) -> bool:
        """
        Navigate to a specific tab by index.
        
        Args:
            location: Tab index as string
            
        Returns:
            True if navigation was successful
        """
        try:
            tab_index = int(location)
            if 0 <= tab_index < self.count():
                self.setCurrentIndex(tab_index)
                return True
        except ValueError:
            pass
        
        return False
    
    # MARK: - Event Handlers
    @Slot(int)
    def _on_tab_close_requested(self, index: int) -> None:
        """Handle tab close request from UI."""
        # Check if tab is closable from stored data
        tab_data = self.tabBar().tabData(index)
        if tab_data and not tab_data.get("closable", True):
            # Tab is not closable, ignore the request
            return
            
        # Get the tab widget
        tab_widget = self.widget(index)
        if not tab_widget:
            return
            
        # Get the subcontainer ID
        id_registry = get_id_registry()
        subcontainer_id = id_registry.get_id(tab_widget)
        if not subcontainer_id:
            return
            
        # Get the subcontainer type for recreation
        subcontainer_type = self.get_subcontainer_type(subcontainer_id)
        
        # Check if we're in a command execution
        if get_command_manager().is_updating():
            #TODO: call method to close tab
            return
        
        # Create a command to close the tab
        container_id = id_registry.get_id(self)
        cmd = CloseTabCommand(subcontainer_id, subcontainer_type, container_id, index)
        cmd.set_trigger_widget(self.widget_id)
        get_command_manager().execute(cmd)
    
    @Slot(int)
    def _on_current_changed(self, index: int) -> None:
        """Handle tab selection change."""
        # Skip if we're executing a command
        if get_command_manager().is_updating():
            return
            
        # Create a tab selection command
        old_index = self.currentIndex()
        if old_index != index:  # Extra check to avoid unnecessary commands
            cmd = TabSelectionCommand(self, old_index, index)
            cmd.set_trigger_widget(self.widget_id)
            get_command_manager().execute(cmd)
    
    # MARK: - Custom Event Handling
    def closeEvent(self, event):
        """Handle widget close event."""
        #TODO: serialize before closing
        # Clean up all subcontainers
        for subcontainer_id in list(self._subcontainers.keys()):
            self.close_subcontainer(subcontainer_id)
            
        # Unregister from ID system
        id_registry = get_id_registry()
        id_registry.unregister(self.widget_id)
        
        # Process the event
        super().closeEvent(event)
    
    # MARK: - Overridden QTabWidget methods
    def removeTab(self, index: int) -> None:
        """Override to properly handle tab removal."""
        # Get the widget before removal
        tab_widget = self.widget(index)
        
        # If we have the tab widget, get its ID and emit signal
        if tab_widget:
            subcontainer_id = get_id_registry().get_id(tab_widget)
            if subcontainer_id and subcontainer_id in self._subcontainers:
                self.tabClosed.emit(subcontainer_id)

        # Remove the tab using the parent implementation
        super().removeTab(index)
                
        # Update locations of all tabs
        self.refresh_location()
    
    # MARK: - Advanced Serialization/Deserialization
    #TODO: check if additional seiralization is needed

# MARK: - Command Classes    
class AddTabCommand(SerializationCommand):
    """Command for adding a new tab with serialization support"""
    def __init__(self, type_id, container_id):
        super().__init__(type_id=type_id, container_id=container_id)
        
    
    def execute(self):
        """Execute simply adds the tab"""
        print("AddTabCommand.execute", self.container_id, self.type_id)
        container = get_id_registry().get_widget(self.container_id)
        print("got container", container)
        self.component_id = container.add_subcontainer(self.type_id)
        print("executed")

    def undo(self):
        """Undo saves serialization and closes tab"""
        if self.component_id:
            self.serialize_subcontainer()
            
    def redo(self):
        """Redo restores the tab from serialization"""
        if self.serialized_state:
            self.deserialize_subcontainer()

class CloseTabCommand(SerializationCommand):
    """Command for closing a tab with serialization support"""
    def __init__(self, component_id: str, type_id: str, container_id:str, index):
        super().__init__(component_id, type_id, container_id)
        self.location = str(index)
        
    def execute(self):
        """Execute captures state and closes tab"""
        if self.component_id:
            self.serialize_subcontainer()

    def undo(self):
        """Undo restores the tab"""
        if self.serialized_state:
            self.deserialize_subcontainer()
        
class TabSelectionCommand(Command):
    """Command for changing the selected tab."""
    
    def __init__(self, tab_widget, old_index, new_index):
        """Initialize with tab indices."""
        super().__init__()
        self.tab_widget = tab_widget
        self.old_index = old_index
        self.new_index = new_index
        
    def execute(self):
        """Execute the command to change the selected tab."""
        if 0 <= self.new_index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(self.new_index)
    
    def undo(self):
        """Undo the command by selecting the previous tab."""
        if 0 <= self.old_index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(self.old_index)