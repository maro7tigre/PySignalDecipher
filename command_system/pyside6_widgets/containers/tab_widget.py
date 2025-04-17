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
        self._tab_position_to_id = Mapping(update_keys=False, update_values=True)
        self.id_registry.mappings.append(self._tab_position_to_id)
        
        self._tab_closable_map = {}  # tab position -> closable flag
        
        # Connect signals
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.currentChanged.connect(self._on_current_changed)
        
        # Track the current tab position for undo/redo operations
        # Initialize to the current position (usually 0 for a new widget)
        self._last_tab_position = self.currentIndex()
    
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
                # Update the last tab position to match current
                self._last_tab_position = self.currentIndex()
            return subcontainer_id
        
        # Create a command for adding a tab
        cmd = AddTabCommand(type_id, self.get_id())
        cmd.set_trigger_widget(self.get_id())
        get_command_manager().execute(cmd)
        return cmd.component_id
    
    # MARK: - Subcontainer Implementation
    def create_subcontainer(self, type_id: str, position: str = None) -> Tuple[QWidget, str]:
        """
        Create an empty tab subcontainer for the specified type.
        
        Args:
            type_id: Type ID of the subcontainer
            position: Position for the subcontainer (tab position)
            
        Returns:
            Tuple of (tab container widget, ID system location string)
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
        
        # Convert position to integer index if provided
        target_position = index
        if position is not None:
            try:
                pos_index = int(position)
                # Move tab to the specified position if different
                if pos_index != index and 0 <= pos_index < self.count():
                    self.tabBar().moveTab(index, pos_index)
                    target_position = pos_index
            except ValueError:
                pass
        
        # Set tab closability
        self._tab_closable_map[target_position] = closable
        self.set_tab_closable(target_position, closable)
        
        # Set as current tab 
        self.setCurrentIndex(target_position)
        
        # Update the last tab position to match current after adding
        self._last_tab_position = self.currentIndex()
        
        # For ID system location, use the string representation of the position
        tab_location = str(target_position)
        
        return tab_container, tab_location

    def close_tab(self, tab_position: int) -> bool:
        """
        Close a tab at the given position.
        
        Args:
            tab_position: Position of the tab to close
            
        Returns:
            True if successful, False otherwise
        """
        # Validate position
        if not (0 <= tab_position < self.count()):
            return False
            
        # Get the widget at the position
        tab_widget = self.widget(tab_position)
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
        self.removeTab(tab_position)
        
        # Update internal mappings
        self._update_tab_mappings()
        
        # Make sure _last_tab_position is updated if needed
        if self._last_tab_position >= self.count():
            self._last_tab_position = self.currentIndex()
        
        return True
    
    def _update_tab_mappings(self):
        """Update all internal tab mappings after changes."""
        # Clear existing mappings - don't use clear() as it won't properly trigger updates
        for position in list(self._tab_position_to_id):
            self._tab_position_to_id.delete(position)
        self._tab_closable_map.clear()
        
        # Rebuild all mappings
        for i in range(self.count()):
            tab_widget = self.widget(i)
            if tab_widget:
                # Update widget-to-position mapping
                widget_id = self.id_registry.get_id(tab_widget)
                if widget_id:
                    self._tab_position_to_id[i] = widget_id
                    
                    # Update position and location mappings for container
                    self._positions_map[str(i)] = widget_id
                    self._id_to_position_map[widget_id] = str(i)
                    
                    # Update location mappings (for ID system)
                    self._locations_map[str(i)] = widget_id  
                    self._id_to_location_map[widget_id] = str(i)
                    
                # Update closable mapping from tab data
                tab_data = self.tabBar().tabData(i)
                closable = True
                if tab_data and isinstance(tab_data, dict) and 'closable' in tab_data:
                    closable = tab_data['closable']
                self._tab_closable_map[i] = closable
    
    def set_tab_closable(self, position: int, closable: bool = True) -> None:
        """
        Set whether a specific tab should be closable.
        
        Args:
            position: Tab position
            closable: Whether the tab should be closable (True by default)
        """
        # Keep all tabs closable at the Qt level, but control the button visibility
        self.setTabsClosable(True)
        
        # Store closable state in tab data
        tab_data = {"closable": closable}
        self.tabBar().setTabData(position, tab_data)
        self._tab_closable_map[position] = closable
        
        # Get the close button for this tab and control its visibility
        button_position = QTabBar.RightSide
        close_button = self.tabBar().tabButton(position, button_position)
        
        # If we have a button, control its visibility
        if close_button:
            close_button.setVisible(closable)
    
    def is_tab_closable(self, position: int) -> bool:
        """
        Check if a tab can be closed by the user.
        
        Args:
            position: Tab position
            
        Returns:
            True if tab is closable, False otherwise
        """
        # First check our direct mapping
        if position in self._tab_closable_map:
            return self._tab_closable_map[position]
            
        # Fall back to tab data
        tab_data = self.tabBar().tabData(position)
        if tab_data and isinstance(tab_data, dict) and 'closable' in tab_data:
            return tab_data['closable']
            
        # Default to closable
        return True
    
    # MARK: - Navigation
    def navigate_to_position(self, position: str) -> bool:
        """
        Navigate to a specific tab by position.
        
        Args:
            position: Tab position as string
            
        Returns:
            True if navigation was successful
        """
        try:
            tab_position = int(position)
            if 0 <= tab_position < self.count():
                self.setCurrentIndex(tab_position)
                return True
        except ValueError:
            pass
        
        return False
    
    # MARK: - Event Handlers
    @Slot(int)
    def _on_tab_close_requested(self, position: int) -> None:
        """Handle tab close request from UI."""
        # Check if tab is closable using our efficient mapping
        if not self.is_tab_closable(position):
            return
            
        # Get the tab widget
        tab_widget = self.widget(position)
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
            self.close_tab(position)
            return
        
        # Create a command to close the tab
        cmd = CloseTabCommand(subcontainer_id, subcontainer_type, self.get_id(), position)
        cmd.set_trigger_widget(self.get_id())
        get_command_manager().execute(cmd)
    
    @Slot(int)
    def _on_current_changed(self, position: int) -> None:
        """Handle tab selection change."""
        # Skip if we're executing a command to avoid recursion
        if get_command_manager().is_updating():
            return
        
        # Get the old position for the command
        old_position = self._last_tab_position
        
        # Update the last tab position for future changes
        self._last_tab_position = position
            
        # Only create command if position actually changed
        if old_position != position:
            cmd = TabSelectionCommand(self.get_id(), old_position, position)
            cmd.set_trigger_widget(self.get_id())
            get_command_manager().execute(cmd)
    
    # MARK: - Overridden QTabWidget methods
    def addTab(self, widget: QWidget, label: str) -> int:
        """Override to track newly added tabs."""
        result = super().addTab(widget, label)
        self._update_tab_mappings()
        return result
        
    def insertTab(self, position: int, widget: QWidget, label: str) -> int:
        """Override to track tab insertions."""
        result = super().insertTab(position, widget, label)
        self._update_tab_mappings()
        return result
        
    def removeTab(self, position: int) -> None:
        """Override to properly handle tab removal."""
        super().removeTab(position)
        self._update_tab_mappings()
    
    # MARK: - Custom Event Handling
    def closeEvent(self, event):
        """Handle widget close event."""
        # Clean up all subcontainers
        for subcontainer_id in list(self._subcontainers):
            self.close_subcontainer(subcontainer_id)
            
        # Remove tab mappings from the registry's tracking
        if hasattr(self, 'id_registry') and hasattr(self.id_registry, 'mappings'):
            if self._tab_position_to_id in self.id_registry.mappings:
                self.id_registry.mappings.remove(self._tab_position_to_id)
        
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
            'current_position': self.currentIndex(),
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
            
        # Set current position last to avoid multiple signals
        # Check for the new naming first, then fall back to old naming for compatibility
        current_position = None
        if 'current_position' in serialized_data:
            current_position = serialized_data['current_position']
        elif 'current_index' in serialized_data:
            # Backward compatibility
            current_position = serialized_data['current_index']
            
        if current_position is not None and 0 <= current_position < self.count():
            self.setCurrentIndex(current_position)
            # Update our tracking variable
            self._last_tab_position = current_position
                
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
        self.position = None
        
    def execute(self):
        """Execute to add the tab."""
        container = get_id_registry().get_widget(self.container_id)
        if container:
            self.component_id = container.add_subcontainer(self.type_id)
            # Store position for later use
            self.position = container.get_subcontainer_position(self.component_id)

    def undo(self):
        """Undo saves serialization and closes tab."""
        if self.component_id:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Save serialization before closing
                self.serialized_state = container.serialize_subcontainer(self.component_id)
                
                # Close the tab - find position from stored value
                if self.position:
                    try:
                        tab_position = int(self.position)
                        container.close_tab(tab_position)
                    except ValueError:
                        # If position can't be converted to index, try using the mapping
                        position = container.get_subcontainer_position(self.component_id)
                        if position:
                            try:
                                tab_position = int(position)
                                container.close_tab(tab_position)
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
                    self.position if self.position else "0",
                    self.serialized_state
                )
        else:
            # Fall back to normal execute if no serialization available
            self.execute()

class CloseTabCommand(SerializationCommand):
    """Command for closing a tab with serialization support."""
    
    def __init__(self, component_id: str, type_id: str, container_id: str, position: int):
        """
        Initialize with tab information.
        
        Args:
            component_id: ID of the tab component
            type_id: Type ID of the tab 
            container_id: ID of the container
            position: Tab position
        """
        super().__init__()
        self.component_id = component_id
        self.type_id = type_id
        self.container_id = container_id
        self.position = str(position)
        
    def execute(self):
        """Execute captures state and closes tab."""
        container = get_id_registry().get_widget(self.container_id)
        if container and self.component_id:
            # Save serialization before closing
            self.serialized_state = container.serialize_subcontainer(self.component_id)
            
            # Close the tab
            try:
                tab_position = int(self.position)
                container.close_tab(tab_position)
            except ValueError:
                pass

    def undo(self):
        """Undo restores the tab."""
        if self.serialized_state:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Restore from serialization
                container.deserialize_subcontainer(
                    self.type_id,
                    self.position,
                    self.serialized_state
                )
        
class TabSelectionCommand(Command):
    """Command for changing the selected tab."""
    
    def __init__(self, tab_widget_id: str, old_position: int, new_position: int):
        """
        Initialize with tab positions.
        
        Args:
            tab_widget_id: ID of the tab widget
            old_position: Previous tab position
            new_position: New tab position
        """
        super().__init__()
        self.tab_widget_id = tab_widget_id
        self.old_position = old_position
        self.new_position = new_position
        
    def execute(self):
        """Execute the command to change the selected tab."""
        tab_widget = get_id_registry().get_widget(self.tab_widget_id)
        if tab_widget and 0 <= self.new_position < tab_widget.count():
            tab_widget.setCurrentIndex(self.new_position)
            # Update the internal tracking to match
            if hasattr(tab_widget, '_last_tab_position'):
                tab_widget._last_tab_position = self.new_position
    
    def undo(self):
        """Undo the command by selecting the previous tab."""
        tab_widget = get_id_registry().get_widget(self.tab_widget_id)
        if tab_widget and 0 <= self.old_position < tab_widget.count():
            tab_widget.setCurrentIndex(self.old_position)
            # Update the internal tracking to match
            if hasattr(tab_widget, '_last_tab_position'):
                tab_widget._last_tab_position = self.old_position