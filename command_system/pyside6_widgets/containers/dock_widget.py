"""
Command-aware dock container widget with integrated command system support.

Provides a dock widget container that integrates with the ID system and command
system for undo/redo functionality, serialization, and comprehensive dock management.
"""
from typing import Any, Dict, Optional, List, Callable, Union, Type, Tuple
from enum import Enum
from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, 
    QApplication, QSizePolicy
)
from PySide6.QtCore import Signal, Slot, Qt, QTimer, QPoint, QSize, QEvent, QRect
from PySide6.QtGui import QMouseEvent

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

class ImprovedQDockWidget(QDockWidget):
    """Custom QDockWidget that properly handles drag operations."""
    
    dragFinished = Signal()  # Signal emitted when drag is completed
    
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self._is_dragging = False
        self._drag_start_pos = None
        self._drag_start_area = None
        self._drag_start_floating = None
        self._drag_start_geometry = None
        
        # Install event filter on title bar widget to catch mouse events
        title_bar = self.titleBarWidget()
        if title_bar:
            title_bar.installEventFilter(self)
        
        # Filter events on the dock widget itself
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Filter events to detect mouse operations on dock."""
        if event.type() == QEvent.MouseButtonPress:
            # Store initial state when mouse press starts
            if isinstance(event, QMouseEvent) and event.button() == Qt.LeftButton:
                self._is_dragging = True
                self._drag_start_pos = event.globalPos()
                
                # Get the dock area from parent if it's a QMainWindow
                parent = self.parent()
                if parent and isinstance(parent, QMainWindow):
                    self._drag_start_area = parent.dockWidgetArea(self)
                else:
                    self._drag_start_area = None
                
                # Store floating state and geometry
                self._drag_start_floating = self.isFloating()
                self._drag_start_geometry = self.geometry()
                
                print(f"DEBUG: Drag started for {self.windowTitle()}, floating={self._drag_start_floating}, area={self._drag_start_area}")
                
        elif event.type() == QEvent.MouseButtonRelease:
            # When mouse is released, check if we were dragging
            if self._is_dragging and isinstance(event, QMouseEvent) and event.button() == Qt.LeftButton:
                self._is_dragging = False
                
                # Delayed signal to ensure all Qt internal state is updated
                QTimer.singleShot(100, self.dragFinished)
                print(f"DEBUG: Drag finished for {self.windowTitle()}")
        
        return super().eventFilter(obj, event)
    
    def isDragging(self):
        """Check if dock is currently being dragged."""
        return self._is_dragging
    
    def getDragStartState(self):
        """Get the state when drag started."""
        return {
            "area": self._drag_start_area,
            "floating": self._drag_start_floating,
            "geometry": self._drag_start_geometry
        }

class CommandDockWidget(QMainWindow, BaseCommandContainer):
    """
    A dock widget container with full command system integration.
    
    Manages a collection of dock subcontainers with proper ID tracking,
    serialization support, and undo/redo operations.
    """
    
    # Signals emitted when docks are modified
    dockAdded = Signal(str)      # subcontainer_id
    dockClosed = Signal(str)     # subcontainer_id
    dockMoved = Signal(str, int)  # subcontainer_id, area
    
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
        self._dock_data = {}  # {dock_id: {area, title, floating, closable, etc.}}
        
        # Track active docks and their states
        self._dock_states = {}  # {dock_id: {area, floating, geometry, etc.}}
        
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
        if position:
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
        
        # Create the custom dock widget
        dock = ImprovedQDockWidget(dock_title, self)
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
        
        # Connect signals
        dock.dragFinished.connect(lambda: self._on_dock_drag_finished(dock))
        dock.visibilityChanged.connect(lambda visible: self._on_dock_visibility_changed(dock, visible))
        
        # Generate a unique location ID for the ID system
        location_id = f"dock_{len(self._dock_position_to_id)}"
        
        # Capture initial state
        current_state = {
            "area": qt_area,
            "floating": floating, 
            "geometry": dock.geometry() if floating else None,
            "visible": True
        }
        
        # Store container ID for later lookup
        self._dock_states[content_container] = current_state
        
        print(f"DEBUG: Created dock {dock_title} at area {qt_area}, floating={floating}")
        
        return content_container, location_id
    
    def close_dock(self, dock_id: str) -> bool:
        """Close a dock with the given ID."""
        print(f"DEBUG: Closing dock {dock_id}")
        
        # Validate ID
        if dock_id not in self._subcontainers:
            print(f"DEBUG: Dock {dock_id} not found in subcontainers")
            return False
            
        # Get the dock widget
        dock_container = self._subcontainers.get(dock_id)
        if not dock_container:
            print(f"DEBUG: Dock container for {dock_id} not found")
            return False
            
        # Find the QDockWidget parent
        dock_widget = self._find_dock_widget_for_container(dock_container)
        if not dock_widget:
            print(f"DEBUG: Dock widget for {dock_id} not found")
            return False
            
        # Close the subcontainer (will handle ID cleanup)
        if not self.close_subcontainer(dock_id):
            print(f"DEBUG: Failed to close subcontainer for {dock_id}")
            return False
        
        # Emit signal before removing the dock
        self.dockClosed.emit(dock_id)
        
        # Clean up stored states
        if dock_container in self._dock_states:
            del self._dock_states[dock_container]
        
        # Remove the dock from the main window
        dock_widget.setParent(None)
        dock_widget.deleteLater()
        
        # Update internal mappings
        self._update_dock_mappings()
        
        print(f"DEBUG: Successfully closed dock {dock_id}")
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
            
            # Update dock state
            self._dock_states[container] = {
                "area": self.dockWidgetArea(dock),
                "floating": dock.isFloating(),
                "geometry": dock.geometry() if dock.isFloating() else None,
                "visible": dock.isVisible()
            }
    
    # MARK: - Event Handlers
    def _on_dock_drag_finished(self, dock: ImprovedQDockWidget):
        """Handle completion of a dock drag operation."""
        # Skip if we're in a command execution to avoid recursion
        if get_command_manager().is_updating():
            print("DEBUG: Skipping drag finished during command execution")
            return
        
        # Find the container widget
        container = dock.widget()
        if not container:
            print("DEBUG: No container found for dock")
            return
            
        # Get container ID
        dock_id = self.id_registry.get_id(container)
        if not dock_id:
            print("DEBUG: No dock ID found for container")
            return
            
        # Get the start state saved when drag began
        old_state = dock.getDragStartState()
        if not old_state or not old_state["area"]:
            print(f"DEBUG: No valid start state for dock {dock_id}")
            return
            
        # Get current state
        current_state = {
            "area": self.dockWidgetArea(dock),
            "floating": dock.isFloating(),
            "geometry": dock.geometry() if dock.isFloating() else None,
            "visible": dock.isVisible()
        }
        
        # Check if there's an actual state change
        significant_change = (
            old_state["area"] != current_state["area"] or
            old_state["floating"] != current_state["floating"]
        )
        
        # Only create command if there's a significant change
        if significant_change:
            print(f"DEBUG: Creating position command for dock {dock_id}")
            print(f"DEBUG:   Old: area={old_state['area']}, floating={old_state['floating']}")
            print(f"DEBUG:   New: area={current_state['area']}, floating={current_state['floating']}")
            
            # Create a command for this position change
            cmd = DockPositionCommand(
                self.get_id(),
                dock_id,
                old_state,
                current_state
            )
            cmd.set_trigger_widget(self.get_id())
            get_command_manager().execute(cmd)
            
            # Update the dock state
            self._dock_states[container] = current_state
        else:
            print(f"DEBUG: No significant change for dock {dock_id}")
    
    def _on_dock_visibility_changed(self, dock: QDockWidget, visible: bool):
        """Handle dock visibility changes."""
        # Skip if we're in a command execution
        if get_command_manager().is_updating():
            return
            
        # Skip automatic visibility changes during drag operations
        if hasattr(dock, 'isDragging') and dock.isDragging():
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
            # Only handle if it's closable
            features = dock.features()
            if features & QDockWidget.DockWidgetClosable:
                # Check if this dock is registered with us
                if dock_id in self._subcontainers:
                    print(f"DEBUG: Handling visibility change to close dock {dock_id}")
                    
                    # Get the subcontainer type for recreation
                    subcontainer_type = self.get_subcontainer_type(dock_id)
                    
                    # Create a command to close the dock
                    cmd = CloseDockCommand(dock_id, subcontainer_type, self.get_id())
                    cmd.set_trigger_widget(self.get_id())
                    get_command_manager().execute(cmd)
                    return
        
        # Update stored state
        if container in self._dock_states:
            self._dock_states[container]["visible"] = visible
    
    # MARK: - Dock Manipulation Methods
    def set_dock_position(self, dock_id: str, area: DockArea, floating: bool = False, 
                         geometry: Optional[QRect] = None) -> bool:
        """
        Set the position and state of a dock.
        
        Args:
            dock_id: ID of the dock to position
            area: The dock area to move to
            floating: Whether the dock should be floating
            geometry: Optional geometry for floating docks
            
        Returns:
            True if successful, False otherwise
        """
        print(f"DEBUG: Setting dock {dock_id} position to area={area}, floating={floating}")
        
        # Get the dock container
        container = self._subcontainers.get(dock_id)
        if not container:
            print(f"DEBUG: Container for dock {dock_id} not found")
            return False
            
        # Find the dock widget
        dock = self._find_dock_widget_for_container(container)
        if not dock:
            print(f"DEBUG: Dock widget for dock {dock_id} not found")
            return False
        
        # Add to appropriate area first (only if not floating)
        if not floating and area is not None and hasattr(area, 'value'):
            print(f"DEBUG: Adding dock {dock_id} to area {area.value}")
            self.addDockWidget(area.value, dock)
        
        # Set floating state
        if floating:
            print(f"DEBUG: Setting dock {dock_id} to floating")
            dock.setFloating(True)
            
            # Set geometry if provided
            if geometry:
                print(f"DEBUG: Setting dock {dock_id} geometry")
                dock.setGeometry(geometry)
        else:
            # Ensure dock is not floating
            dock.setFloating(False)
        
        # Update stored state
        if container in self._dock_states:
            self._dock_states[container] = {
                "area": area.value if hasattr(area, 'value') else area,
                "floating": floating,
                "geometry": geometry if floating else None,
                "visible": dock.isVisible()
            }
            
        return True
    
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
                
                # Store state
                self._dock_states[container] = {
                    "area": data.get("area", DockArea.RIGHT.value),
                    "floating": data.get("floating", False),
                    "geometry": data.get("geometry"),
                    "visible": data.get("visible", True)
                }
                
        return True

    # MARK: - Utilities
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
        print(f"DEBUG: AddDockCommand execute for type {self.type_id}")
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
        print(f"DEBUG: AddDockCommand undo for dock {self.component_id}")
        if self.component_id:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Save serialization before closing
                self.serialized_state = container.serialize_subcontainer(self.component_id)
                
                # Close the dock
                container.close_dock(self.component_id)
            
    def redo(self):
        """Redo restores the dock from serialization."""
        print(f"DEBUG: AddDockCommand redo for type {self.type_id}")
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
        print(f"DEBUG: CloseDockCommand execute for dock {self.component_id}")
        container = get_id_registry().get_widget(self.container_id)
        if container and self.component_id:
            # Save position
            self.position = container.get_subcontainer_position(self.component_id)
            
            # Save serialization before closing
            self.serialized_state = container.serialize_subcontainer(self.component_id)
            
            # Close the dock
            container.close_dock(self.component_id)

    def undo(self):
        """Undo restores the dock."""
        print(f"DEBUG: CloseDockCommand undo for dock {self.component_id}")
        if self.serialized_state:
            container = get_id_registry().get_widget(self.container_id)
            if container:
                # Restore from serialization
                container.deserialize_subcontainer(
                    self.type_id,
                    self.position,
                    self.serialized_state
                )
        
class DockPositionCommand(Command):
    """Command for changing a dock's position, area, or floating state."""
    
    def __init__(self, container_id: str, dock_id: str, 
                old_state: Dict, new_state: Dict):
        """Initialize with dock position information."""
        super().__init__()
        self.container_id = container_id
        self.dock_id = dock_id
        self.old_state = old_state
        self.new_state = new_state
        
    def execute(self):
        """Execute the command to change the dock position."""
        print(f"DEBUG: DockPositionCommand execute for dock {self.dock_id}")
        # Apply the new state
        self._apply_state(self.new_state)
    
    def undo(self):
        """Undo the command by restoring the previous position."""
        print(f"DEBUG: DockPositionCommand undo for dock {self.dock_id}")
        # Apply the old state
        self._apply_state(self.old_state)
    
    def _apply_state(self, state: Dict):
        """Apply a dock state (position, area, floating)."""
        if not state:
            print(f"DEBUG: No state to apply for dock {self.dock_id}")
            return
            
        container = get_id_registry().get_widget(self.container_id)
        if not container:
            print(f"DEBUG: Container {self.container_id} not found")
            return
            
        # Get the dock container
        dock_container = container._subcontainers.get(self.dock_id)
        if not dock_container:
            print(f"DEBUG: Dock container {self.dock_id} not found")
            return
            
        # Find the dock widget
        dock = container._find_dock_widget_for_container(dock_container)
        if not dock:
            print(f"DEBUG: Dock widget for {self.dock_id} not found")
            return
            
        # Get state values
        area = state.get("area")
        geometry = state.get("geometry")
        floating = state.get("floating", False)
        
        print(f"DEBUG: Applying state - area={area}, floating={floating}")
        
        # Stop any ongoing drag operation
        if hasattr(dock, '_is_dragging'):
            dock._is_dragging = False
        
        # Apply area first (must be done before setting floating)
        if area is not None:
            print(f"DEBUG: Adding dock to area {area}")
            container.addDockWidget(area, dock)
            
        # Apply floating state
        if floating is not None:
            print(f"DEBUG: Setting floating={floating}")
            dock.setFloating(floating)
            
        # Apply geometry if floating
        if floating and geometry:
            print(f"DEBUG: Setting geometry")
            dock.setGeometry(geometry)
            
        # Update container tracking data
        if hasattr(container, '_dock_states') and dock_container in container._dock_states:
            container._dock_states[dock_container] = state.copy()