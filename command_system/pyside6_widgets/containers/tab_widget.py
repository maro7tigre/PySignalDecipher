"""
Command-aware tab widget with integrated command system support.

Provides a tab widget that integrates with the ID system and command system
for undo/redo functionality, serialization, and comprehensive state management.
"""
from typing import Any, Dict, Optional, List, Callable, Union, Type
from PySide6.QtWidgets import QTabWidget, QWidget, QTabBar, QVBoxLayout
from PySide6.QtCore import Signal, Slot

from command_system.id_system import get_id_registry, TypeCodes
from command_system.core import get_command_manager, Command, Observable
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
            subcontainer_id = self.add_subcontainer(type_id, str(self.count()))
            if subcontainer_id:
                # Emit signal for the new tab
                self.tabAdded.emit(subcontainer_id)
            return subcontainer_id
        
        # Create a command for adding a tab
        class AddTabCommand(Command):
            def __init__(self, tab_widget, type_id):
                super().__init__()
                self.tab_widget = tab_widget
                self.type_id = type_id
                self.subcontainer_id = None
                
            def execute(self):
                self.subcontainer_id = self.tab_widget.add_subcontainer(
                    self.type_id, str(self.tab_widget.count())
                )
                
                if self.subcontainer_id:
                    # Emit signal for the new tab
                    self.tab_widget.tabAdded.emit(self.subcontainer_id)
                
            def undo(self):
                if self.subcontainer_id:
                    self.tab_widget.close_subcontainer(self.subcontainer_id)
        
        # Create and execute the command
        cmd = AddTabCommand(self, type_id)
        cmd.set_trigger_widget(self.widget_id)
        get_command_manager().execute(cmd)
        return cmd.subcontainer_id
    
    # MARK: - Subcontainer Implementation
    def create_subcontainer(self, type_id: str, location: str = "0") -> Optional[QWidget]:
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
        try:
            loc_index = int(location)
            # Move tab to the specified location if different
            if loc_index != index:
                self.tabBar().moveTab(index, loc_index)
                index = loc_index
        except ValueError:
            # Use the current index
            pass
        
        # Set tab closability if specified
        closable = type_info.get("options", {}).get("closable", True)
        self.set_tab_closable(index, closable)
        
        # Set as current tab if specified
        if type_info.get("options", {}).get("make_current", True):
            self.setCurrentIndex(index)
            
        # Update tab locations in case of insertion
        self._update_tab_locations()
        
        return tab_container
    
    # Remove the _add_content_to_subcontainer method as we're handling content directly in the base class now
    
    def _update_tab_locations(self) -> None:
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
        
        # Create a command to close the tab
        class CloseTabCommand(Command):
            def __init__(self, tab_widget, subcontainer_id, index, subcontainer_type):
                super().__init__()
                self.tab_widget = tab_widget
                self.subcontainer_id = subcontainer_id
                self.index = index
                self.subcontainer_type = subcontainer_type
                
                # Save serialization for undo
                self.serialized_state = tab_widget.serialize_subcontainer(subcontainer_id)
                
            def execute(self):
                # Close the subcontainer
                self.tab_widget.close_subcontainer(self.subcontainer_id)
                
                # Update tab locations
                self.tab_widget._update_tab_locations()
                
            def undo(self):
                # Check if we have serialized state
                if not self.serialized_state:
                    return
                    
                # Restore the tab using deserialization
                type_id = self.subcontainer_type
                location = str(self.index)  # Restore at the same index
                
                # Deserialize the subcontainer
                self.tab_widget.deserialize_subcontainer(
                    type_id, location, self.serialized_state
                )
                
                # Update tab locations and select the restored tab
                self.tab_widget._update_tab_locations()
                self.tab_widget.navigate_to_location(location)
                
        # Create and execute the command
        cmd = CloseTabCommand(self, subcontainer_id, index, subcontainer_type)
        cmd.set_trigger_widget(self.widget_id)
        get_command_manager().execute(cmd)
    
    @Slot(int)
    def _on_current_changed(self, index: int) -> None:
        """Handle tab selection change."""
        # Skip if we're executing a command
        if get_command_manager().is_updating():
            return
            
        # Create a tab selection command
        class TabSelectionCommand(Command):
            def __init__(self, tab_widget, old_index, new_index):
                super().__init__()
                self.tab_widget = tab_widget
                self.old_index = old_index
                self.new_index = new_index
                
            def execute(self):
                if 0 <= self.new_index < self.tab_widget.count():
                    self.tab_widget.setCurrentIndex(self.new_index)
                
            def undo(self):
                if 0 <= self.old_index < self.tab_widget.count():
                    self.tab_widget.setCurrentIndex(self.old_index)
        
        # Execute the command (only if not triggered by another command)
        old_index = self.currentIndex()
        if old_index != index:  # Extra check to avoid unnecessary commands
            cmd = TabSelectionCommand(self, old_index, index)
            cmd.set_trigger_widget(self.widget_id)
            get_command_manager().execute(cmd)
    
    # MARK: - Custom Event Handling
    def closeEvent(self, event):
        """Handle widget close event."""
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
        
        # Remove the tab using the parent implementation
        super().removeTab(index)
        
        # If we have the tab widget, get its ID and emit signal
        if tab_widget:
            subcontainer_id = get_id_registry().get_id(tab_widget)
            if subcontainer_id and subcontainer_id in self._subcontainers:
                self.tabClosed.emit(subcontainer_id)
                
        # Update locations of all tabs
        self._update_tab_locations()
    
    # MARK: - Advanced Serialization/Deserialization
    def get_serialization(self) -> Dict:
        """
        Get serialized representation of this tab widget.
        
        Returns:
            Dict containing serialized tab widget state
        """
        # Get basic container serialization
        result = super().get_serialization()
        
        # Add tab widget specific properties
        result.update({
            'current_index': self.currentIndex(),
            'tab_position': self.tabPosition(),
            'tabs_closable': self.tabsClosable(),
            'document_mode': self.documentMode(),
            'moving_enabled': self.isMovable(),
        })
        
        return result
    
    def deserialize(self, serialized_data: Dict) -> bool:
        """
        Deserialize and restore tab widget state.
        
        Args:
            serialized_data: Dict containing serialized tab widget state
            
        Returns:
            True if successful, False otherwise
        """
        # Restore subcontainers with parent method
        result = super().deserialize(serialized_data)
        
        # Restore tab widget specific properties
        if 'current_index' in serialized_data:
            current_index = serialized_data['current_index']
            if isinstance(current_index, int) and 0 <= current_index < self.count():
                self.setCurrentIndex(current_index)
                
        if 'tab_position' in serialized_data:
            self.setTabPosition(serialized_data['tab_position'])
            
        if 'tabs_closable' in serialized_data:
            self.setTabsClosable(serialized_data['tabs_closable'])
            
        if 'document_mode' in serialized_data:
            self.setDocumentMode(serialized_data['document_mode'])
            
        if 'moving_enabled' in serialized_data:
            self.setMovable(serialized_data['moving_enabled'])
            
        return result