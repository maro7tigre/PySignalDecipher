"""
Command-aware dock container widget with integrated command system support.

Provides a dock widget container that integrates with the ID system and command
system for undo/redo functionality and serialization.
"""
from typing import Any, Dict, Optional, List, Callable, Union, Type, Tuple
from enum import Enum
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, 
    QApplication, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QTimer

from command_system.id_system import get_id_registry, ContainerTypeCodes
from command_system.id_system.core.mapping import Mapping
from command_system.core import get_command_manager, Command, SerializationCommand, Observable
from .base_container import BaseCommandContainer

# Define dock area enum matching Qt::DockWidgetArea
class DockArea(Enum):
    LEFT = Qt.LeftDockWidgetArea
    RIGHT = Qt.RightDockWidgetArea
    TOP = Qt.TopDockWidgetArea
    BOTTOM = Qt.BottomDockWidgetArea
    ALL = Qt.AllDockWidgetAreas
    NO_DOCK = 0

class CommandDockWidget(QMainWindow, BaseCommandContainer):
    """
    A dock widget container with command system integration.
    
    Manages a collection of dock subcontainers with proper ID tracking,
    and serialization support.
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
        
        # Enhanced dock tracking with position-to-id mapping
        self._dock_position_to_id = Mapping(update_keys=False, update_values=True)
        self.id_registry.mappings.append(self._dock_position_to_id)
        
        # Store additional data for each dock
        self._dock_data = {}  # {dock_id: {area, title, closable, etc.}}
        
        # Set up a central widget to ensure proper dock behavior
        central = QWidget()
        central.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(central)
        
        # Enable dock nesting
        self.setDockNestingEnabled(True)
    
    # MARK: - Dock Registration
    def register_dock(self, factory_func: Callable, dock_title: str = None,
                     observables: List[Union[str, Type[Observable]]] = None, 
                     closable: bool = True, floating: bool = False,
                     default_area: DockArea = DockArea.RIGHT) -> str:
        """Register a dock type with factory function."""
        options = {
            "dock_title": dock_title or "Dock", 
            "closable": closable,
            "floating": floating,
            "default_area": default_area
        }
        type_id = self.register_subcontainer_type(factory_func, observables, None, **options)
        return type_id
    
    def add_dock(self, type_id: str, area: Optional[DockArea] = None, 
                floating: Optional[bool] = None) -> str:
        """Add a new dock of the registered type."""
        # Check if we're in a command execution
        if get_command_manager().is_updating():
            # Direct dock addition during command execution
            dock_options = {}
            if area is not None:
                dock_options["area"] = area
            if floating is not None:
                dock_options["floating"] = floating
                
            subcontainer_id = self.add_subcontainer(type_id, str(dock_options))
            if subcontainer_id:
                # Emit signal for the new dock
                self.dockAdded.emit(subcontainer_id)
            return subcontainer_id
        
        # Create a command for adding a dock
        cmd = AddDockCommand(type_id, self.get_id(), area, floating)
        cmd.set_trigger_widget(self.get_id())
        get_command_manager().execute(cmd)
        return cmd.component_id
    
    # MARK: - Subcontainer Implementation
    def create_subcontainer(self, type_id: str, position: str = None) -> Tuple[QWidget, str]:
        """Create an empty dock subcontainer for the specified type."""
        # Validate type exists
        type_info = self._widget_types.get(type_id)
        if not type_info:
            return None, None
            
        # Get dock options from type_info or use defaults
        options = type_info.get("options", {})
        dock_title = options.get("dock_title", "Dock")
        closable = options.get("closable", True)
        default_floating = options.get("floating", False)
        default_area = options.get("default_area", DockArea.RIGHT)
        
        # Parse position string if provided (may contain override options)
        override_options = {}
        if position and position.startswith('{') and position.endswith('}'):
            try:
                override_options = eval(position)
            except Exception:
                pass
        
        # Get actual settings with overrides applied
        area = override_options.get("area", default_area)
        floating = override_options.get("floating", default_floating)
        
        # Ensure area is a DockArea enum
        if isinstance(area, DockArea):
            qt_area = area.value
        else:
            try:
                qt_area = int(area)
            except (ValueError, TypeError):
                qt_area = DockArea.RIGHT.value
        
        # Create the dock widget
        dock = QDockWidget(dock_title, self)
        dock.setObjectName(f"dock_{len(self._dock_position_to_id)}")
        dock.setFeatures(QDockWidget.DockWidgetClosable | 
                         QDockWidget.DockWidgetMovable | 
                         QDockWidget.DockWidgetFloatable)
        
        # Create content container
        content_container = QWidget()
        layout = QVBoxLayout(content_container)
        layout.setContentsMargins(0, 0, 0, 0)
        dock.setWidget(content_container)
        
        # Add the dock to the main window
        self.addDockWidget(qt_area, dock)
        
        # Set floating state if needed
        if floating:
            dock.setFloating(True)
        
        # Set closability
        if not closable:
            features = dock.features()
            features &= ~QDockWidget.DockWidgetClosable
            dock.setFeatures(features)
        
        # Connect close signal
        dock.visibilityChanged.connect(lambda visible: self._on_dock_visibility_changed(dock, visible))
        
        # Generate a unique location ID for the ID system
        location_id = f"dock_{len(self._dock_position_to_id)}"
        
        return content_container, location_id
    
    def close_dock(self, dock_id: str) -> bool:
        """Close a dock with the given ID."""
        # Validate ID
        if dock_id not in self._subcontainers:
            return False
            
        # Get the dock widget
        dock_container = self._subcontainers.get(dock_id)
        if not dock_container:
            return False
            
        # Find the QDockWidget parent
        dock_widget = self._find_dock_widget_for_container(dock_container)
        if not dock_widget:
            return False
            
        # Close the subcontainer (will handle ID cleanup)
        if not self.close_subcontainer(dock_id):
            return False
        
        # Emit signal before removing the dock
        self.dockClosed.emit(dock_id)
        
        # Remove the dock from the main window
        dock_widget.setParent(None)
        dock_widget.deleteLater()
        
        # Update internal mappings
        self._update_dock_mappings()
        
        return True
    
    def _find_dock_widget_for_container(self, container: QWidget) -> Optional[QDockWidget]:
        """Find the QDockWidget that contains the given container."""
        # Try to find the dock widget in the parent hierarchy
        parent = container.parent()
        while parent:
            if isinstance(parent, QDockWidget):
                return parent
            parent = parent.parent()
        return None
    
    def _update_dock_mappings(self):
        """Update all internal dock mappings after changes."""
        # Find all QDockWidgets in this container
        docks = self.findChildren(QDockWidget)
        
        # Update mappings for each dock
        for dock in docks:
            # Get the content container (should be our registered widget)
            container = dock.widget()
            if not container:
                continue
                
            # Find the container ID
            container_id = self.id_registry.get_id(container)
            if not container_id:
                continue
                
            # Update data for this dock
            self._dock_data[container_id] = {
                "title": dock.windowTitle(),
                "area": self.dockWidgetArea(dock),
                "floating": dock.isFloating(),
                "visible": dock.isVisible(),
                "features": dock.features(),
                "geometry": dock.geometry() if dock.isFloating() else None,
                "object_name": dock.objectName()
            }
    
    # MARK: - Event Handlers
    def _on_dock_visibility_changed(self, dock: QDockWidget, visible: bool):
        """Handle dock visibility changes."""
        # Skip if we're in a command execution
        if get_command_manager().is_updating():
            return
            
        # Skip if the dock is still in a dock area but temporarily hidden
        # This can happen during drag operations
        if not visible and not dock.isFloating() and self.dockWidgetArea(dock) != Qt.NoDockWidgetArea:
            return
            
        # Find the container widget
        container = dock.widget()
        if not container:
            return
            
        # Get container ID
        dock_id = self.id_registry.get_id(container)
        if not dock_id:
            return
            
        # If the dock is being hidden and it's a manual close
        if not visible:
            # Make sure it's actually a close event, not just a temporary state during drag
            # We use a small delay to verify it's actually closing
            # Create a one-shot timer to check if this is really a close
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._delayed_visibility_check(dock, dock_id))
            timer.start(100)  # 100ms delay to confirm the close
            return
                
    def _delayed_visibility_check(self, dock: QDockWidget, dock_id: str):
        """Check if a dock is actually closed after a short delay."""
        # If the widget has been collected, just return
        if dock.parent() is None:
            return
            
        # If the dock is still not visible, treat it as a close request
        if not dock.isVisible() and dock_id in self._subcontainers:
            # Only handle if it's closable
            features = dock.features()
            if features & QDockWidget.DockWidgetClosable:
                # Get the subcontainer type for recreation
                subcontainer_type = self.get_subcontainer_type(dock_id)
                if not subcontainer_type:
                    return
                
                # Create a command to close the dock
                cmd = CloseDockCommand(dock_id, subcontainer_type, self.get_id())
                cmd.set_trigger_widget(self.get_id())
                get_command_manager().execute(cmd)
    
    # MARK: - Navigation
    def navigate_to_position(self, position: str) -> bool:
        """Navigate to a specific dock by position."""
        # Try to find the dock at this position
        if position in self._dock_position_to_id:
            dock_id = self._dock_position_to_id[position]
            container = self._subcontainers.get(dock_id)
            if container:
                # Find the dock widget
                dock = self._find_dock_widget_for_container(container)
                if dock:
                    # Make sure the dock is visible
                    dock.show()
                    dock.raise_()
                    dock.setFocus()
                    return True
                
        return False
    
    # MARK: - Serialization
    def get_serialization(self) -> Dict:
        """Get serialized representation of this dock widget container."""
        # Update mappings to ensure we have the latest state
        self._update_dock_mappings()
        
        # Get base serialization
        result = super().get_serialization()
        
        # Add dock container specific state
        result.update({
            "dock_data": self._dock_data.copy()
        })
        
        return result
    
    def deserialize(self, serialized_data: Dict) -> bool:
        """Deserialize and restore dock widget container state."""
        # First restore base container state
        if not super().deserialize(serialized_data):
            return False
            
        # Restore dock data if available
        if "dock_data" in serialized_data and isinstance(serialized_data["dock_data"], dict):
            # Store dock data for later use
            self._dock_data = serialized_data["dock_data"].copy()
            
            # Apply dock settings to each dock
            for dock_id, data in self._dock_data.items():
                # Get the dock container
                container = self._subcontainers.get(dock_id)
                if not container:
                    continue
                    
                # Find the dock widget
                dock = self._find_dock_widget_for_container(container)
                if not dock:
                    continue
                    
                # Restore dock settings
                if "title" in data:
                    dock.setWindowTitle(data["title"])
                    
                if "features" in data:
                    dock.setFeatures(data["features"])
                    
                if "area" in data:
                    # Move to the correct area before setting floating
                    self.addDockWidget(data["area"], dock)
                    
                if "floating" in data and data["floating"]:
                    dock.setFloating(True)
                    
                    # Also restore geometry if available
                    if "geometry" in data and data["geometry"]:
                        dock.setGeometry(data["geometry"])
                
                if "visible" in data:
                    dock.setVisible(data["visible"])
                
        return True


# MARK: - Command Classes
class AddDockCommand(SerializationCommand):
    """Command for adding a new dock with serialization support."""
    
    def __init__(self, type_id: str, container_id: str, 
                area: Optional[DockArea] = None, 
                floating: Optional[bool] = None):
        """Initialize with type and container information."""
        super().__init__()
        self.type_id = type_id
        self.container_id = container_id
        self.component_id = None
        self.position = None
        
        # Store override options
        self.override_options = {}
        if area is not None:
            self.override_options["area"] = area
        if floating is not None:
            self.override_options["floating"] = floating
        
    def execute(self):
        """Execute to add the dock."""
        container = get_id_registry().get_widget(self.container_id)
        if container:
            # Convert options to position string
            position = str(self.override_options) if self.override_options else None
            
            # Add the dock
            self.component_id = container.add_subcontainer(self.type_id, position)
            
            # Store position for later use
            self.position = container.get_subcontainer_position(self.component_id)

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
                    self.position if self.position else "0",
                    self.serialized_state
                )
        else:
            # Fall back to normal execute if no serialization available
            self.execute()

class CloseDockCommand(SerializationCommand):
    """Command for closing a dock with serialization support."""
    
    def __init__(self, component_id: str, type_id: str, container_id: str):
        """Initialize with dock information."""
        super().__init__()
        self.component_id = component_id
        self.type_id = type_id
        self.container_id = container_id
        self.position = None
        
    def execute(self):
        """Execute captures state and closes dock."""
        container = get_id_registry().get_widget(self.container_id)
        if container and self.component_id:
            # Save position
            position = container.get_subcontainer_position(self.component_id)
            if position is not None:
                # Ensure position is a string to prevent type conversion errors
                self.position = str(position)
            
            # Save serialization before closing
            self.serialized_state = container.serialize_subcontainer(self.component_id)
            
            # Close the dock
            container.close_dock(self.component_id)

    def undo(self):
        """Undo restores the dock."""
        if self.serialized_state:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Restore from serialization
                container.deserialize_subcontainer(
                    self.type_id,
                    self.position if self.position is not None else "0",
                    self.serialized_state
                )