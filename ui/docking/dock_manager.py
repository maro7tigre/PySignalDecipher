"""
Dock Manager for PySignalDecipher.

This module provides a manager for workspace-specific dock widgets,
handling their creation, registration, and state management.
"""

import os
import sys
import importlib
import inspect
from typing import Dict, List, Type, Optional, Any, Set
from PySide6.QtWidgets import QMainWindow, QMenu
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QAction

from core.service_registry import ServiceRegistry
from .dockable_widget import DockableWidget


class DockRegistry:
    """
    Registry of available dock types.
    
    Handles discovery and registration of all available dock widget types.
    """
    
    # Dictionary to store registered dock types
    _dock_types = {}
    
    @classmethod
    def register_dock_type(cls, type_id: str, dock_class: Type[DockableWidget]) -> None:
        """
        Register a dock widget type.
        
        Args:
            type_id: Identifier for this dock type
            dock_class: Class for this dock type
        """
        cls._dock_types[type_id] = dock_class
        print(f"Registered dock type: {type_id}")
    
    @classmethod
    def get_dock_type(cls, type_id: str) -> Optional[Type[DockableWidget]]:
        """
        Get a dock widget type by its ID.
        
        Args:
            type_id: Identifier for the dock type
            
        Returns:
            The dock class, or None if not found
        """
        return cls._dock_types.get(type_id)
    
    @classmethod
    def get_available_dock_types(cls) -> List[str]:
        """
        Get a list of available dock types.
        
        Returns:
            List of dock type identifiers
        """
        return list(cls._dock_types.keys())
    
    @classmethod
    def discover_dock_types(cls) -> None:
        """
        Discover and register all available dock types.
        
        Searches for dock widget classes in the dock_types directory.
        """
        # Get the path to the dock_types directory
        dock_types_dir = os.path.join(os.path.dirname(__file__), "dock_types")
        
        # Create the directory if it doesn't exist
        if not os.path.exists(dock_types_dir):
            os.makedirs(dock_types_dir)
            print(f"Created dock_types directory: {dock_types_dir}")
            
        # Add the directory to the Python path if not already there
        if dock_types_dir not in sys.path:
            sys.path.append(dock_types_dir)
            
        # Load all Python files in the dock_types directory
        for filename in os.listdir(dock_types_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    # Get the module name from the filename
                    module_name = filename[:-3]  # Remove .py extension
                    
                    # Import the module
                    module = importlib.import_module(module_name)
                    
                    # Find all DockableWidget subclasses in the module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, DockableWidget) and 
                            obj != DockableWidget):
                            
                            # Derive the type ID from the class name
                            # Convert CamelCase to snake_case
                            type_id = ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_')
                            
                            # Register the dock type
                            cls.register_dock_type(type_id, obj)
                            
                except (ImportError, AttributeError) as e:
                    print(f"Error loading dock type from {filename}: {e}")


class DockManager(QObject):
    """
    Manages dock widgets for workspaces.
    
    Provides a central point for creating, tracking, and managing
    dock widgets within specific workspaces.
    """
    
    # Signal emitted when a dock widget is added
    dock_added = Signal(str, object)  # workspace_id, dock_widget
    
    # Signal emitted when a dock widget is removed
    dock_removed = Signal(str, str)  # workspace_id, dock_id
    
    # Signal emitted when a dock widget is activated
    dock_activated = Signal(str, str)  # workspace_id, dock_id
    
    def __init__(self, preferences_manager=None, theme_manager=None):
        """
        Initialize the dock manager.
        
        Args:
            preferences_manager: Optional reference to the PreferencesManager
            theme_manager: Optional reference to the ThemeManager
        """
        super().__init__()
        
        # Get references from parameters or registry
        self._preferences_manager = preferences_manager or ServiceRegistry.get_preferences_manager()
        self._theme_manager = theme_manager or ServiceRegistry.get_theme_manager()
        
        # Connect to theme changed signal
        if self._theme_manager:
            self._theme_manager.theme_changed.connect(self.apply_theme)
        
        # Dictionary to store active docks by workspace
        # {workspace_id: {dock_id: dock_widget}}
        self._active_docks = {}
        
        # Dictionary to cache available dock factories by ID
        self._dock_factories = {}
        
        # Reference to the current main window
        self._main_window = None
        
        # Discover available dock types
        self._discover_dock_types()
    
    def _discover_dock_types(self) -> None:
        """Discover and register all available dock types."""
        # Use the DockRegistry to discover dock types
        DockRegistry.discover_dock_types()
        
        # Register built-in dock types
        from .signal_view_dock import SignalViewDock
        DockRegistry.register_dock_type("signal_view", SignalViewDock)
        from .dock_types.settings_dock import SettingsDock
        DockRegistry.register_dock_type("Settings", SettingsDock)
    
    def register_dock_type(self, type_id: str, dock_class: Type[DockableWidget]) -> None:
        """
        Register a dock widget type.
        
        Args:
            type_id: Identifier for this dock type
            dock_class: Class for this dock type
        """
        DockRegistry.register_dock_type(type_id, dock_class)
    
    def get_available_dock_types(self) -> List[str]:
        """
        Get a list of available dock types.
        
        Returns:
            List of dock type identifiers
        """
        return DockRegistry.get_available_dock_types()
    
    def set_main_window(self, main_window: QMainWindow) -> None:
        """
        Set the main window for dock management.
        
        Args:
            main_window: Main window to use
        """
        self._main_window = main_window
    
    def create_dock(self, workspace_id: str, dock_type: str, 
                   title: str = None, dock_id: str = None,
                   area: Qt.DockWidgetArea = Qt.RightDockWidgetArea) -> Optional[DockableWidget]:
        """
        Create a new dock widget.
        
        Args:
            workspace_id: ID of the workspace to add the dock to
            dock_type: Type of dock to create
            title: Title for the dock (uses default if None)
            dock_id: ID for the dock (generated if None)
            area: Dock area to add to
            
        Returns:
            Created dock widget, or None if the type is invalid
        """
        # Get the dock class from the registry
        dock_class = DockRegistry.get_dock_type(dock_type)
        
        if not dock_class:
            print(f"Error: Unknown dock type: {dock_type}")
            return None
            
        if not self._main_window:
            print("Error: No main window set for dock manager")
            return None
            
        # Create the dock widget
        dock = dock_class(title=title or dock_type.replace('_', ' ').title(),
                         parent=self._main_window,
                         widget_id=dock_id)
        
        # Set workspace type
        dock.set_workspace_type(workspace_id)
        
        # Add to the main window
        self._main_window.addDockWidget(area, dock)
        
        # Register in active docks
        if workspace_id not in self._active_docks:
            self._active_docks[workspace_id] = {}
            
        self._active_docks[workspace_id][dock.get_widget_id()] = dock
        
        # Connect to dock signals
        dock.widget_closed.connect(lambda dock_id: self._on_dock_closed(workspace_id, dock_id))
        dock.state_changed.connect(lambda: self._on_dock_state_changed(workspace_id, dock))
        
        # Apply theme
        dock.apply_theme(self._theme_manager)
        
        # Emit added signal
        self.dock_added.emit(workspace_id, dock)
        
        return dock
    
    def remove_dock(self, workspace_id: str, dock_id: str) -> bool:
        """
        Remove a dock widget.
        
        Args:
            workspace_id: ID of the workspace containing the dock
            dock_id: ID of the dock to remove
            
        Returns:
            True if the dock was removed, False if not found
        """
        if (workspace_id not in self._active_docks or
            dock_id not in self._active_docks[workspace_id]):
            return False
            
        # Get the dock
        dock = self._active_docks[workspace_id][dock_id]
        
        # Remove from main window and delete
        self._main_window.removeDockWidget(dock)
        dock.deleteLater()
        
        # Remove from active docks
        del self._active_docks[workspace_id][dock_id]
        
        # Emit removed signal
        self.dock_removed.emit(workspace_id, dock_id)
        
        return True
    
    def get_dock(self, workspace_id: str, dock_id: str) -> Optional[DockableWidget]:
        """
        Get a dock widget by ID.
        
        Args:
            workspace_id: ID of the workspace containing the dock
            dock_id: ID of the dock to get
            
        Returns:
            The dock widget, or None if not found
        """
        if (workspace_id not in self._active_docks or
            dock_id not in self._active_docks[workspace_id]):
            return None
            
        return self._active_docks[workspace_id][dock_id]
    
    def get_docks_for_workspace(self, workspace_id: str) -> Dict[str, DockableWidget]:
        """
        Get all dock widgets for a workspace.
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            Dictionary mapping dock IDs to dock widgets
        """
        return self._active_docks.get(workspace_id, {})
    
    def get_docks_by_type(self, workspace_id: str, dock_type: str) -> List[DockableWidget]:
        """
        Get all dock widgets of a specific type for a workspace.
        
        Args:
            workspace_id: ID of the workspace
            dock_type: Type of dock to get
            
        Returns:
            List of dock widgets matching the type
        """
        result = []
        
        # Get all docks for the workspace
        docks = self.get_docks_for_workspace(workspace_id)
        
        # Filter by dock type
        for dock in docks.values():
            # Check if the dock is an instance of the specified type
            dock_class = DockRegistry.get_dock_type(dock_type)
            if dock_class and isinstance(dock, dock_class):
                result.append(dock)
                
        return result
    
    def activate_dock(self, workspace_id: str, dock_id: str) -> bool:
        """
        Activate a dock widget.
        
        This raises and focuses the dock if it exists.
        
        Args:
            workspace_id: ID of the workspace containing the dock
            dock_id: ID of the dock to activate
            
        Returns:
            True if the dock was activated, False if not found
        """
        dock = self.get_dock(workspace_id, dock_id)
        if not dock:
            return False
            
        # Raise and give focus to the dock
        dock.raise_()
        dock.setFocus()
        
        # Emit activated signal
        self.dock_activated.emit(workspace_id, dock_id)
        
        return True
    
    def _on_dock_closed(self, workspace_id: str, dock_id: str) -> None:
        """
        Handle dock widget closed signal.
        
        Args:
            workspace_id: ID of the workspace containing the dock
            dock_id: ID of the dock that was closed
        """
        # Remove the dock from our tracking
        self.remove_dock(workspace_id, dock_id)
    
    def _on_dock_state_changed(self, workspace_id: str, dock: DockableWidget) -> None:
        """
        Handle dock widget state changed signal.
        
        Args:
            workspace_id: ID of the workspace containing the dock
            dock: Dock that changed state
        """
        # This could be used to persist state changes
        pass
    
    def save_workspace_state(self, workspace_id: str) -> Dict[str, Any]:
        """
        Save the state of all docks in a workspace.
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            State dictionary for the workspace
        """
        state = {
            "docks": {}
        }
        
        if workspace_id in self._active_docks:
            for dock_id, dock in self._active_docks[workspace_id].items():
                state["docks"][dock_id] = dock.save_state()
                
        return state
    
    def restore_workspace_state(self, workspace_id: str, state: Dict[str, Any]) -> bool:
        """
        Restore the state of all docks in a workspace.
        
        Args:
            workspace_id: ID of the workspace
            state: State dictionary for the workspace
            
        Returns:
            True if the state was restored successfully
        """
        if "docks" not in state:
            return False
            
        # Track whether all restorations succeeded
        all_succeeded = True
        
        # Process all dock states
        for dock_id, dock_state in state["docks"].items():
            # Check if the dock already exists
            dock = self.get_dock(workspace_id, dock_id)
            
            if dock:
                # Restore existing dock state
                if not dock.restore_state(dock_state):
                    all_succeeded = False
            else:
                # Create a new dock if type is specified
                if "dock_type" in dock_state:
                    dock_type = dock_state["dock_type"]
                    
                    if dock_type in self.get_available_dock_types():
                        new_dock = self.create_dock(
                            workspace_id,
                            dock_type,
                            dock_id=dock_id
                        )
                        
                        if new_dock:
                            if not new_dock.restore_state(dock_state):
                                all_succeeded = False
                        else:
                            all_succeeded = False
                    else:
                        all_succeeded = False
                else:
                    all_succeeded = False
                    
        return all_succeeded
    
    def create_dock_context_menu(self, workspace_id: str) -> QMenu:
        """
        Create a context menu for adding docks to a workspace.
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            Context menu for adding docks
        """
        menu = QMenu()
        menu.setTitle("Add Widget")
        
        # Add an action for each available dock type
        for dock_type in sorted(self.get_available_dock_types()):
            # Create a display name from the dock type
            display_name = dock_type.replace('_', ' ').title()
            
            action = QAction(display_name, menu)
            action.triggered.connect(
                lambda checked=False, dt=dock_type: 
                self.create_dock(workspace_id, dt)
            )
            menu.addAction(action)
            
        return menu
    
    def apply_theme(self, theme_manager=None) -> None:
        """
        Apply the current theme to all dock widgets.
        
        Args:
            theme_manager: Optional theme manager reference
        """
        if theme_manager:
            self._theme_manager = theme_manager
            
        # Apply theme to all active docks
        for workspace_docks in self._active_docks.values():
            for dock in workspace_docks.values():
                dock.apply_theme(self._theme_manager)
                
    def create_dock_factory(self, workspace_id: str, dock_type: str) -> callable:
        """
        Create a factory function for creating docks of a specific type.
        
        This is useful for creating docks from other components without
        having to remember the workspace ID or dock type.
        
        Args:
            workspace_id: ID of the workspace
            dock_type: Type of dock to create
            
        Returns:
            Factory function that takes title and dock_id as optional arguments
        """
        # Create a factory function for this dock type
        def factory(title=None, dock_id=None, area=Qt.RightDockWidgetArea):
            return self.create_dock(workspace_id, dock_type, title, dock_id, area)
            
        return factory