"""
Dock Manager for PySignalDecipher.

This module provides a manager for workspace-specific dock widgets,
handling their creation, registration, and state management.
"""

from typing import Dict, List, Type, Optional, Any
from PySide6.QtWidgets import QMainWindow, QMenu
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QAction

from core.service_registry import ServiceRegistry
from .dockable_widget import DockableWidget


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
        
        # Dictionary to store available dock types
        # Maps string identifiers to dock widget classes
        self._dock_types = {}
        
        # Dictionary to store active docks by workspace
        # {workspace_id: {dock_id: dock_widget}}
        self._active_docks = {}
        
        # Reference to the current main window
        self._main_window = None
    
    def register_dock_type(self, type_id: str, dock_class: Type[DockableWidget]) -> None:
        """
        Register a dock widget type.
        
        Args:
            type_id: Identifier for this dock type
            dock_class: Class for this dock type
        """
        self._dock_types[type_id] = dock_class
    
    def get_available_dock_types(self) -> List[str]:
        """
        Get a list of available dock types.
        
        Returns:
            List of dock type identifiers
        """
        return list(self._dock_types.keys())
    
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
        if dock_type not in self._dock_types:
            print(f"Error: Unknown dock type: {dock_type}")
            return None
            
        if not self._main_window:
            print("Error: No main window set for dock manager")
            return None
            
        # Create the dock widget
        dock_class = self._dock_types[dock_type]
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
                    
                    if dock_type in self._dock_types:
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
        for dock_type in sorted(self._dock_types.keys()):
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