"""
Improved command-aware tab widget with integrated command system support.

Provides a tab widget that integrates with the ID system and command system
for undo/redo functionality, serialization, and comprehensive state management.
"""
from typing import Any, Dict, Optional, List, Callable, Union, Type, Tuple
from PySide6.QtWidgets import QTabWidget, QWidget, QTabBar, QVBoxLayout
from PySide6.QtCore import Signal, Slot, Qt

from command_system.id_system import get_id_registry, ContainerTypeCodes
from command_system.id_system.core.mapping import Mapping
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
        
        # Initialize container with TAB type code
        self.initiate_container(ContainerTypeCodes.TAB, container_id, location)
        
        # Enhanced tab tracking with direct index-to-id mapping using Mapping
        self._tab_index_to_id = Mapping(update_keys=False, update_values=True)
        self.id_registry.mappings.append(self._tab_index_to_id)
        
        self._tab_closable_map = {}  # index -> closable flag
        
        # Connect signals
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.currentChanged.connect(self._on_current_changed)
        
        # Track the current tab index for undo/redo operations
        # Initialize to the current index (usually 0 for a new widget)
        self._last_tab_index = self.currentIndex()
    
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
            closable: Whether tabs of this type can be closed
            
        Returns:
            ID of the registered tab type
        """
        options = {"tab_name": tab_name or "Tab", "closable": closable}
        type_id = self.register_subcontainer_type(factory_func, observables, None, **options)
        return type_id
    
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
            # Direct tab addition during command execution
            subcontainer_id = self.add_subcontainer(type_id)
            if subcontainer_id:
                # Emit signal for the new tab
                self.tabAdded.emit(subcontainer_id)
                # Update the last tab index to match current
                self._last_tab_index = self.currentIndex()
            return subcontainer_id
        
        # Create a command for adding a tab
        cmd = AddTabCommand(type_id, self.get_id())
        cmd.set_trigger_widget(self.get_id())
        get_command_manager().execute(cmd)
        return cmd.component_id
    
    # MARK: - Subcontainer Implementation
    def create_subcontainer(self, type_id: str, location: str = None) -> Tuple[QWidget, str]:
        """
        Create an empty tab subcontainer for the specified type.
        
        Args:
            type_id: Type ID of the subcontainer
            location: Location for the subcontainer (tab index)
            
        Returns:
            Tuple of (tab container widget, location string)
        """
        # Validate type exists
        type_info = self._widget_types.get(type_id)
        if not type_info:
            return None, None
            
        # Get tab name from options or use default
        tab_name = type_info.get("options", {}).get("tab_name", "Tab")
        closable = type_info.get("options", {}).get("closable", True)
        
        # Create an empty container widget for the tab
        tab_container = QWidget()
        
        # Use a layout for the tab content
        layout = QVBoxLayout(tab_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the tab
        index = self.addTab(tab_container, tab_name)
        
        # Convert location to integer index if provided
        target_index = index
        if location is not None:
            try:
                loc_index = int(location)
                # Move tab to the specified location if different
                if loc_index != index and 0 <= loc_index < self.count():
                    self.tabBar().moveTab(index, loc_index)
                    target_index = loc_index
            except ValueError:
                pass
        
        # Set tab closability
        self._tab_closable_map[target_index] = closable
        self.set_tab_closable(target_index, closable)
        
        # Set as current tab 
        self.setCurrentIndex(target_index)
        
        # Update the last tab index to match current after adding
        self._last_tab_index = self.currentIndex()
        
        # Location is the string representation of the index
        tab_location = str(target_index)
        
        return tab_container, tab_location

    def close_tab(self, tab_index: int) -> bool:
        """
        Close a tab at the given index.
        
        Args:
            tab_index: Index of the tab to close
            
        Returns:
            True if successful, False otherwise
        """
        # Validate index
        if not (0 <= tab_index < self.count()):
            return False
            
        # Get the widget at the index
        tab_widget = self.widget(tab_index)
        if not tab_widget:
            return False
            
        # Get the subcontainer ID
        id_registry = self.id_registry
        subcontainer_id = id_registry.get_id(tab_widget)
        if not subcontainer_id:
            return False
            
        # Close the subcontainer (will handle ID cleanup)
        if not self.close_subcontainer(subcontainer_id):
            return False
        
        # Emit signal before removing the tab
        self.tabClosed.emit(subcontainer_id)
        
        # Remove the tab from the widget
        self.removeTab(tab_index)
        
        # Update internal mappings
        self._update_tab_mappings()
        
        # Make sure _last_tab_index is updated if needed
        if self._last_tab_index >= self.count():
            self._last_tab_index = self.currentIndex()
        
        return True
    
    def _update_tab_mappings(self):
        """Update all internal tab mappings after changes."""
        # Clear existing mappings - don't use clear() as it won't properly trigger updates
        for index in list(self._tab_index_to_id):
            self._tab_index_to_id.delete(index)
        self._tab_closable_map.clear()
        
        # Rebuild all mappings
        for i in range(self.count()):
            tab_widget = self.widget(i)
            if tab_widget:
                # Update widget-to-index mapping
                widget_id = self.id_registry.get_id(tab_widget)
                if widget_id:
                    self._tab_index_to_id[i] = widget_id
                    
                    # Update location mappings for container
                    self._locations_map[str(i)] = widget_id
                    self._id_to_location_map[widget_id] = str(i)
                    
                # Update closable mapping from tab data
                tab_data = self.tabBar().tabData(i)
                closable = True
                if tab_data and isinstance(tab_data, dict) and 'closable' in tab_data:
                    closable = tab_data['closable']
                self._tab_closable_map[i] = closable
    
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
        tab_data = {"closable": closable}
        self.tabBar().setTabData(index, tab_data)
        self._tab_closable_map[index] = closable
        
        # Get the close button for this tab and control its visibility
        button_position = QTabBar.RightSide
        close_button = self.tabBar().tabButton(index, button_position)
        
        # If we have a button, control its visibility
        if close_button:
            close_button.setVisible(closable)
    
    def is_tab_closable(self, index: int) -> bool:
        """
        Check if a tab can be closed by the user.
        
        Args:
            index: Tab index
            
        Returns:
            True if tab is closable, False otherwise
        """
        # First check our direct mapping
        if index in self._tab_closable_map:
            return self._tab_closable_map[index]
            
        # Fall back to tab data
        tab_data = self.tabBar().tabData(index)
        if tab_data and isinstance(tab_data, dict) and 'closable' in tab_data:
            return tab_data['closable']
            
        # Default to closable
        return True
    
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
        # Check if tab is closable using our efficient mapping
        if not self.is_tab_closable(index):
            return
            
        # Get the tab widget
        tab_widget = self.widget(index)
        if not tab_widget:
            return
            
        # Get the subcontainer ID
        id_registry = self.id_registry
        subcontainer_id = id_registry.get_id(tab_widget)
        if not subcontainer_id:
            return
            
        # Get the subcontainer type for recreation
        subcontainer_type = self.get_subcontainer_type(subcontainer_id)
        
        # Check if we're in a command execution
        if get_command_manager().is_updating():
            self.close_tab(index)
            return
        
        # Create a command to close the tab
        cmd = CloseTabCommand(subcontainer_id, subcontainer_type, self.get_id(), index)
        cmd.set_trigger_widget(self.get_id())
        get_command_manager().execute(cmd)
    
    @Slot(int)
    def _on_current_changed(self, index: int) -> None:
        """Handle tab selection change."""
        # Skip if we're executing a command to avoid recursion
        if get_command_manager().is_updating():
            return
        
        # Get the old index for the command
        old_index = self._last_tab_index
        
        # Update the last tab index for future changes
        self._last_tab_index = index
            
        # Only create command if index actually changed
        if old_index != index:
            cmd = TabSelectionCommand(self.get_id(), old_index, index)
            cmd.set_trigger_widget(self.get_id())
            get_command_manager().execute(cmd)
    
    # MARK: - Overridden QTabWidget methods
    def addTab(self, widget: QWidget, label: str) -> int:
        """Override to track newly added tabs."""
        result = super().addTab(widget, label)
        self._update_tab_mappings()
        return result
        
    def insertTab(self, index: int, widget: QWidget, label: str) -> int:
        """Override to track tab insertions."""
        result = super().insertTab(index, widget, label)
        self._update_tab_mappings()
        return result
        
    def removeTab(self, index: int) -> None:
        """Override to properly handle tab removal."""
        super().removeTab(index)
        self._update_tab_mappings()
    
    # MARK: - Custom Event Handling
    def closeEvent(self, event):
        """Handle widget close event."""
        # Clean up all subcontainers
        for subcontainer_id in list(self._subcontainers):
            self.close_subcontainer(subcontainer_id)
            
        # Remove tab mappings from the registry's tracking
        if hasattr(self, 'id_registry') and hasattr(self.id_registry, 'mappings'):
            if self._tab_index_to_id in self.id_registry.mappings:
                self.id_registry.mappings.remove(self._tab_index_to_id)
        
        # Unregister from ID system
        self.unregister_widget()
        
        # Process the event
        super().closeEvent(event)
    
    # MARK: - Serialization
    def get_serialization(self) -> Dict:
        """
        Get serialized representation of this tab widget.
        
        Returns:
            Dict containing serialized tab widget state
        """
        result = super().get_serialization()
        
        # Add tab widget specific state
        result.update({
            'current_index': self.currentIndex(),
            'tab_position': self.tabPosition(),
            'tabs_closable': self.tabsClosable(),
            'document_mode': self.documentMode(),
            'moving_enabled': self.isMovable()
        })
        
        return result
    
    def deserialize(self, serialized_data: Dict) -> bool:
        """
        Deserialize and restore tab widget state.
        
        Args:
            serialized_data: Dict containing serialized state
            
        Returns:
            True if successful, False otherwise
        """
        # First restore base container state
        if not super().deserialize(serialized_data):
            return False
            
        # Restore tab widget specific state
        if 'tab_position' in serialized_data:
            self.setTabPosition(serialized_data['tab_position'])
            
        if 'tabs_closable' in serialized_data:
            self.setTabsClosable(serialized_data['tabs_closable'])
            
        if 'document_mode' in serialized_data:
            self.setDocumentMode(serialized_data['document_mode'])
            
        if 'moving_enabled' in serialized_data:
            self.setMovable(serialized_data['moving_enabled'])
            
        # Set current index last to avoid multiple signals
        if 'current_index' in serialized_data:
            index = serialized_data['current_index']
            if 0 <= index < self.count():
                self.setCurrentIndex(index)
                # Update our tracking variable
                self._last_tab_index = index
                
        return True


# MARK: - Command Classes    
class AddTabCommand(SerializationCommand):
    """Command for adding a new tab with serialization support."""
    
    def __init__(self, type_id: str, container_id: str):
        """
        Initialize with type and container information.
        
        Args:
            type_id: Type ID of the tab to add
            container_id: ID of the container to add the tab to
        """
        super().__init__()
        self.type_id = type_id
        self.container_id = container_id
        self.component_id = None
        self.location = None
        
    def execute(self):
        """Execute to add the tab."""
        container = get_id_registry().get_widget(self.container_id)
        if container:
            self.component_id = container.add_subcontainer(self.type_id)
            # Store location for later use
            self.location = container.get_subcontainer_location(self.component_id)

    def undo(self):
        """Undo saves serialization and closes tab."""
        if self.component_id:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Save serialization before closing
                self.serialized_state = container.serialize_subcontainer(self.component_id)
                
                # Close the tab - find index from location
                if self.location:
                    try:
                        tab_index = int(self.location)
                        container.close_tab(tab_index)
                    except ValueError:
                        # If location can't be converted to index, try using the mapping
                        location = container.get_subcontainer_location(self.component_id)
                        if location:
                            try:
                                tab_index = int(location)
                                container.close_tab(tab_index)
                            except ValueError:
                                pass
            
    def redo(self):
        """Redo restores the tab from serialization."""
        if self.serialized_state:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Restore from serialization
                container.deserialize_subcontainer(
                    self.type_id,
                    self.location if self.location else "0",
                    self.serialized_state
                )
        else:
            # Fall back to normal execute if no serialization available
            self.execute()

class CloseTabCommand(SerializationCommand):
    """Command for closing a tab with serialization support."""
    
    def __init__(self, component_id: str, type_id: str, container_id: str, index: int):
        """
        Initialize with tab information.
        
        Args:
            component_id: ID of the tab component
            type_id: Type ID of the tab 
            container_id: ID of the container
            index: Tab index
        """
        super().__init__()
        self.component_id = component_id
        self.type_id = type_id
        self.container_id = container_id
        self.location = str(index)
        
    def execute(self):
        """Execute captures state and closes tab."""
        container = get_id_registry().get_widget(self.container_id)
        print(f"contaiener id : {self.container_id} component id : {self.component_id}")
        if container and self.component_id:
            # Save serialization before closing
            self.serialized_state = container.serialize_subcontainer(self.component_id)
            print(f" Serialized state : {self.serialized_state}")
            # Close the tab
            try:
                tab_index = int(self.location)
                container.close_tab(tab_index)
            except ValueError as e:
                print(f"ValueError occurred: {e}")
                

    def undo(self):
        """Undo restores the tab."""
        print("+++++++++++++++++++++++++")
        if self.serialized_state:
            print(f" Serialized state : {self.serialized_state}")
            container = get_id_registry().get_widget(self.container_id)
            print(f" Container : {container}, with id : {self.container_id}")
            if container:
                # Restore from serialization
                print(f" Location : {self.location}, Type ID : {self.type_id}")
                container.deserialize_subcontainer(
                    self.type_id,
                    self.location,
                    self.serialized_state
                )
        print("++++++++++++++++++++++++++")
        
class TabSelectionCommand(Command):
    """Command for changing the selected tab."""
    
    def __init__(self, tab_widget_id: str, old_index: int, new_index: int):
        """
        Initialize with tab indices.
        
        Args:
            tab_widget_id: ID of the tab widget
            old_index: Previous tab index
            new_index: New tab index
        """
        super().__init__()
        self.tab_widget_id = tab_widget_id
        self.old_index = old_index
        self.new_index = new_index
        
    def execute(self):
        """Execute the command to change the selected tab."""
        tab_widget = get_id_registry().get_widget(self.tab_widget_id)
        if tab_widget and 0 <= self.new_index < tab_widget.count():
            tab_widget.setCurrentIndex(self.new_index)
            # Update the internal tracking to match
            if hasattr(tab_widget, '_last_tab_index'):
                tab_widget._last_tab_index = self.new_index
    
    def undo(self):
        """Undo the command by selecting the previous tab."""
        tab_widget = get_id_registry().get_widget(self.tab_widget_id)
        if tab_widget and 0 <= self.old_index < tab_widget.count():
            tab_widget.setCurrentIndex(self.old_index)
            # Update the internal tracking to match
            if hasattr(tab_widget, '_last_tab_index'):
                tab_widget._last_tab_index = self.old_index