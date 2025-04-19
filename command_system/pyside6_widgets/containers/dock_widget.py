"""
Command-aware dock widget container with integrated command system support.

Provides a dock widget container that integrates with the ID system and command system
for undo/redo functionality, serialization, and comprehensive state management.
"""
from typing import Any, Dict, Optional, List, Callable, Union, Type, Tuple
from PySide6.QtWidgets import QMainWindow, QDockWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Signal, Slot, Qt, QRect

from command_system.id_system import get_id_registry, ContainerTypeCodes
from command_system.id_system.core.mapping import Mapping
from command_system.core import get_command_manager, Command, SerializationCommand, Observable
from .base_container import BaseCommandContainer

class CommandDockWidget(QMainWindow, BaseCommandContainer):
    """
    A dock widget container with full command system integration.
    
    Manages a collection of dock subcontainers with proper ID tracking,
    serialization support, and undo/redo operations.
    """
    
    # Signals emitted when docks are modified
    dockAdded = Signal(str)      # subcontainer_id
    dockClosed = Signal(str)     # subcontainer_id
    
    def __init__(self, parent=None, container_id=None, location=None):
        """Initialize the command dock widget container."""
        # Initialize QMainWindow
        QMainWindow.__init__(self, parent)
        
        # Initialize container with DOCK type code
        self.initiate_container(ContainerTypeCodes.DOCK, container_id, location)
        
        # Track dock floating state and area
        self._dock_states = {}  # subcontainer_id -> (floating, area, geometry)
        
        # Let QMainWindow be visible even without a central widget
        # This is important because sometimes we might not set a central widget
        # but still want the main window to be visible to hold docks
        self.setMinimumSize(400, 300)
    
    # MARK: - Dock Registration
    def register_dock(self, factory_func: Callable, dock_name: str = None,
                    observables: List[Union[str, Type[Observable]]] = None,
                    closable: bool = True) -> str:
        """
        Register a dock type with factory function.
        
        Args:
            factory_func: Function that creates the dock content
            dock_name: Display name for docks of this type
            observables: List of Observable IDs or Observable classes
            closable: Whether docks of this type can be closed
            
        Returns:
            ID of the registered dock type
        """
        options = {"dock_name": dock_name or "Dock", "closable": closable}
        type_id = self.register_subcontainer_type(factory_func, observables, None, **options)
        return type_id
    
    def add_dock(self, type_id: str, floating: bool = False) -> str:
        """
        Add a new dock of the registered type.
        
        Args:
            type_id: ID of the registered dock type
            floating: Whether the dock should be initially floating
            
        Returns:
            ID of the created dock subcontainer
            
        # TODO: Add more options for positioning and layout of docks
        """
        # Check if we're in a command execution
        if get_command_manager().is_updating():
            # Direct dock addition during command execution
            subcontainer_id = self.add_subcontainer(type_id, str(floating))
            if subcontainer_id:
                # Emit signal for the new dock
                self.dockAdded.emit(subcontainer_id)
            return subcontainer_id
        
        # Create a command for adding a dock
        cmd = AddDockCommand(type_id, self.get_id(), floating)
        cmd.set_trigger_widget(self.get_id())
        get_command_manager().execute(cmd)
        return cmd.component_id
    
    # MARK: - Subcontainer Implementation
    def create_subcontainer(self, type_id: str, position: str = None) -> Tuple[QWidget, str]:
        """
        Create an empty dock subcontainer for the specified type.
        
        Args:
            type_id: Type ID of the subcontainer
            position: Position information (e.g., "True" for floating)
            
        Returns:
            Tuple of (dock container widget, ID system location string)
        """
        # Validate type exists
        type_info = self._widget_types.get(type_id)
        if not type_info:
            return None, None
            
        # Get dock name from options or use default
        dock_name = type_info.get("options", {}).get("dock_name", "Dock")
        closable = type_info.get("options", {}).get("closable", True)
        
        # Parse floating state from position string if provided
        floating = False
        try:
            if position is not None:
                floating = position.lower() == "true"
        except (ValueError, AttributeError):
            pass
        
        # Create a new QDockWidget
        dock_widget = QDockWidget(dock_name, self)
        
        # Create content widget for the dock
        content_widget = QWidget(dock_widget)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        dock_widget.setWidget(content_widget)
        
        # Configure dock widget
        dock_widget.setFloating(floating)
        
        features = QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        if closable:
            features |= QDockWidget.DockWidgetFeature.DockWidgetClosable
        dock_widget.setFeatures(features)
        
        # Add the dock widget to the main window
        # Default to right dock area if not specified
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_widget)
        dock_widget.show()  # Ensure dock is visible
        
        # Connect close event
        dock_widget.closeEvent = lambda event, dock=dock_widget: self._on_dock_close_requested(dock, event)
        
        # Generate a unique location for this dock
        dock_location = str(len(self._subcontainers))
        
        return content_widget, dock_location

    def close_dock(self, subcontainer_id: str) -> bool:
        """
        Close and unregister a dock.
        
        Args:
            subcontainer_id: ID of the subcontainer to close
            
        Returns:
            True if successful, False otherwise
        """
        # Validate subcontainer exists
        content_widget = self.get_subcontainer(subcontainer_id)
        if not content_widget:
            return False
            
        # Find the QDockWidget that contains this content
        dock_widget = None
        for dock in self.findChildren(QDockWidget):
            if dock.widget() == content_widget:
                dock_widget = dock
                break
                
        if not dock_widget:
            return False
        
        # Emit signal before closing
        self.dockClosed.emit(subcontainer_id)
        
        # Close the subcontainer (will handle ID cleanup)
        if not self.close_subcontainer(subcontainer_id):
            return False
        
        # Close and delete the dock widget
        dock_widget.close()
        dock_widget.deleteLater()
        
        return True
    
    # MARK: - Dock State Tracking
    def _update_dock_states(self):
        """Update the internal tracking of dock states."""
        self._dock_states.clear()
        
        # Track all dock widgets and their states
        for dock in self.findChildren(QDockWidget):
            content_widget = dock.widget()
            if content_widget:
                subcontainer_id = self.id_registry.get_id(content_widget)
                if subcontainer_id:
                    # Store floating state, area, and geometry
                    area = self.dockWidgetArea(dock)
                    floating = dock.isFloating()
                    geometry = dock.geometry() if floating else None
                    
                    self._dock_states[subcontainer_id] = (floating, area, geometry)
    
    def get_dock_widget(self, subcontainer_id: str) -> Optional[QDockWidget]:
        """
        Get the QDockWidget for a subcontainer.
        
        Args:
            subcontainer_id: ID of the subcontainer
            
        Returns:
            QDockWidget or None if not found
        """
        content_widget = self.get_subcontainer(subcontainer_id)
        if not content_widget:
            return None
            
        # Find the QDockWidget that contains this content
        for dock in self.findChildren(QDockWidget):
            if dock.widget() == content_widget:
                return dock
                
        return None
    
    # MARK: - Navigation
    def navigate_to_position(self, position: str) -> bool:
        """
        Navigate to a specific dock by position.
        
        Args:
            position: Dock position as string
            
        Returns:
            True if navigation was successful
        """
        # Find dock by position
        subcontainer_id = self.get_subcontainer_at_position(position)
        if not subcontainer_id:
            return False
            
        # Get the dock widget
        dock_widget = self.get_dock_widget(subcontainer_id)
        if not dock_widget:
            return False
            
        # Activate the dock
        dock_widget.raise_()
        dock_widget.setFocus()
        
        return True
    
    # MARK: - Event Handlers
    def _on_dock_close_requested(self, dock_widget: QDockWidget, event):
        """Handle dock close request from UI."""
        # Find the content widget
        content_widget = dock_widget.widget()
        if not content_widget:
            # Let the event pass through
            event.accept()
            return
            
        # Get the subcontainer ID
        id_registry = self.id_registry
        subcontainer_id = id_registry.get_id(content_widget)
        if not subcontainer_id:
            # Let the event pass through
            event.accept()
            return
            
        # Get subcontainer type
        subcontainer_type = self.get_subcontainer_type(subcontainer_id)
        
        # Check if we're in a command execution
        if get_command_manager().is_updating():
            self.close_dock(subcontainer_id)
            event.accept()
            return
        
        # Create a command to close the dock
        cmd = CloseDockCommand(subcontainer_id, subcontainer_type, self.get_id())
        cmd.set_trigger_widget(self.get_id())
        get_command_manager().execute(cmd)
        
        # Prevent the default close behavior
        event.ignore()
    
    # MARK: - Custom Event Handling
    def closeEvent(self, event):
        """Handle widget close event."""
        # Clean up all subcontainers
        for subcontainer_id in list(self._subcontainers):
            self.close_subcontainer(subcontainer_id)
            
        # Unregister from ID system
        self.unregister_widget()
        
        # Process the event
        super().closeEvent(event)
    
    # MARK: - Serialization
    def get_serialization(self) -> Dict:
        """
        Get serialized representation of this dock widget container.
        
        Returns:
            Dict containing serialized dock widget container state
        """
        # Update dock states before serialization
        self._update_dock_states()
        
        result = super().get_serialization()
        
        # Add dock container specific state
        result.update({
            'dock_states': {
                subcontainer_id: {
                    'floating': state[0],
                    'area': state[1],
                    'geometry': {
                        'x': state[2].x() if state[2] else 0,
                        'y': state[2].y() if state[2] else 0,
                        'width': state[2].width() if state[2] else 0,
                        'height': state[2].height() if state[2] else 0
                    } if state[2] else None
                }
                for subcontainer_id, state in self._dock_states.items()
            }
        })
        
        return result
    
    def serialize_subcontainer(self, subcontainer_id: str) -> Dict:
        """
        Serialize a subcontainer with its dock state information.
        
        Args:
            subcontainer_id: ID of the subcontainer to serialize
            
        Returns:
            Dict containing serialized subcontainer state
        """
        # First update dock states
        self._update_dock_states()
        
        # Get basic subcontainer serialization
        serialized = super().serialize_subcontainer(subcontainer_id)
        if not serialized:
            return None
            
        # Add dock-specific state information
        if subcontainer_id in self._dock_states:
            state = self._dock_states[subcontainer_id]
            serialized['dock_state'] = {
                'floating': state[0],
                'area': state[1],
                'geometry': {
                    'x': state[2].x() if state[2] else 0,
                    'y': state[2].y() if state[2] else 0,
                    'width': state[2].width() if state[2] else 0,
                    'height': state[2].height() if state[2] else 0
                } if state[2] else None
            }
            
        return serialized
    
    def deserialize_subcontainer(self, type_id: str, position: str, 
                                serialized_subcontainer: Dict,
                                existing_subcontainer_id: Optional[str] = None) -> str:
        """
        Deserialize and restore a subcontainer with its dock state.
        
        Args:
            type_id: Type ID of the subcontainer
            position: Position information
            serialized_subcontainer: Dict containing serialized subcontainer state
            existing_subcontainer_id: ID of existing subcontainer to update (optional)
            
        Returns:
            ID of the subcontainer
        """
        # Get dock state for proper restoration
        dock_state = serialized_subcontainer.get('dock_state', {})
        floating = dock_state.get('floating', False)
        
        # First deserialize the basic subcontainer
        subcontainer_id = super().deserialize_subcontainer(
            type_id, 
            str(floating),  # Pass floating state as position
            serialized_subcontainer,
            existing_subcontainer_id
        )
        
        if not subcontainer_id:
            return None
            
        # Apply dock-specific state
        dock_widget = self.get_dock_widget(subcontainer_id)
        if dock_widget and dock_state:
            # Apply dock area
            area = dock_state.get('area', Qt.DockWidgetArea.RightDockWidgetArea)
            if not dock_widget.isFloating():
                # First remove it from current area
                self.removeDockWidget(dock_widget)
                # Then add to the correct area
                self.addDockWidget(area, dock_widget)
            
            # Apply floating state
            dock_widget.setFloating(floating)
            
            # Apply geometry if floating
            if floating and 'geometry' in dock_state and dock_state['geometry']:
                geometry = dock_state['geometry']
                dock_widget.setGeometry(
                    geometry.get('x', 0),
                    geometry.get('y', 0),
                    geometry.get('width', 200),
                    geometry.get('height', 200)
                )
            
            # Make the dock visible
            dock_widget.show()
            
        return subcontainer_id


# MARK: - Command Classes    
class AddDockCommand(SerializationCommand):
    """Command for adding a new dock with serialization support."""
    
    def __init__(self, type_id: str, container_id: str, floating: bool = False):
        """
        Initialize with type and container information.
        
        Args:
            type_id: Type ID of the dock to add
            container_id: ID of the container to add the dock to
            floating: Whether the dock should be floating
        """
        super().__init__()
        self.type_id = type_id
        self.container_id = container_id
        self.component_id = None
        self.floating = floating
        
    def execute(self):
        """Execute to add the dock."""
        container = get_id_registry().get_widget(self.container_id)
        if container:
            self.component_id = container.add_subcontainer(self.type_id, str(self.floating))

    def undo(self):
        """Undo saves serialization and closes dock."""
        if self.component_id:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Save serialization before closing
                self.serialized_state = container.serialize_subcontainer(self.component_id)
                
                # Close the dock
                container.close_dock(self.component_id)
            
    def redo(self):
        """Redo restores the dock from serialization."""
        if self.serialized_state:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Restore from serialization
                container.deserialize_subcontainer(
                    self.type_id,
                    str(self.floating),
                    self.serialized_state
                )
        else:
            # Fall back to normal execute if no serialization available
            self.execute()

class CloseDockCommand(SerializationCommand):
    """Command for closing a dock with serialization support."""
    
    def __init__(self, component_id: str, type_id: str, container_id: str):
        """
        Initialize with dock information.
        
        Args:
            component_id: ID of the dock component
            type_id: Type ID of the dock 
            container_id: ID of the container
        """
        super().__init__()
        self.component_id = component_id
        self.type_id = type_id
        self.container_id = container_id
        
    def execute(self):
        """Execute captures state and closes dock."""
        container = get_id_registry().get_widget(self.container_id)
        if container and self.component_id:
            # Save serialization before closing
            self.serialized_state = container.serialize_subcontainer(self.component_id)
            
            # Close the dock
            container.close_dock(self.component_id)

    def undo(self):
        """Undo restores the dock."""
        if self.serialized_state:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Get the floating state for correct restoration
                dock_state = self.serialized_state.get('dock_state', {})
                floating = dock_state.get('floating', False)
                
                # Restore from serialization
                container.deserialize_subcontainer(
                    self.type_id,
                    str(floating),
                    self.serialized_state
                )