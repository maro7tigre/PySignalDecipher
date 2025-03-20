"""
Command implementations for dock operations.
"""
from typing import Dict, List, Optional, Any, Set

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow

from ...command import Command, CompoundCommand
from ...observable import Observable
from .dock_manager import get_dock_manager


class CreateDockCommand(Command):
    """
    Command for creating a new dock widget.
    """
    
    def __init__(self, dock_id: str, dock_widget: QDockWidget, 
                parent_id: Optional[str] = None,
                dock_area: Qt.DockWidgetArea = Qt.RightDockWidgetArea):
        """
        Initialize the create dock command.
        
        Args:
            dock_id: Unique identifier for the dock
            dock_widget: The dock widget to create
            parent_id: Optional parent dock ID
            dock_area: Area to place the dock in
        """
        self.dock_id = dock_id
        self.dock_widget = dock_widget
        self.parent_id = parent_id
        self.dock_area = dock_area
        self.main_window = None
        self.dock_manager = get_dock_manager()
        self.dock_state = None  # Will store dock state for undo/redo
        
    def execute(self) -> None:
        """Execute the command to create the dock."""
        # Get the main window from dock manager
        self.main_window = getattr(self.dock_manager, "_main_window", None)
        
        if self.main_window:
            # Add the dock widget to the main window
            self.main_window.addDockWidget(self.dock_area, self.dock_widget)
            
            # Show the dock
            self.dock_widget.show()
            
            # Register with dock manager
            self.dock_manager.register_dock(self.dock_id, self.dock_widget, self.parent_id)
            
            # Save initial state for undo
            self.dock_manager.save_dock_state(self.dock_id)
            self.dock_state = self.dock_manager._dock_states[self.dock_id].copy()
        
    def undo(self) -> None:
        """Undo the command, removing the dock widget."""
        # Get the dock widget
        dock_widget = self.dock_manager.get_dock_widget(self.dock_id)
        
        if dock_widget and self.main_window:
            # Remove the dock from the main window
            self.main_window.removeDockWidget(dock_widget)
            
            # Hide the dock
            dock_widget.hide()
            
            # Unregister from dock manager
            self.dock_manager.unregister_dock(self.dock_id)


class DeleteDockCommand(Command):
    """
    Command for deleting a dock widget.
    """
    
    def __init__(self, dock_id: str):
        """
        Initialize the delete dock command.
        
        Args:
            dock_id: ID of the dock to delete
        """
        self.dock_id = dock_id
        self.dock_manager = get_dock_manager()
        self.dock_state = None
        self.dock_widget = None
        self.main_window = None
        self.children_states = {}
        
    def execute(self) -> None:
        """Execute the command to delete the dock."""
        # Get the main window and dock widget
        self.main_window = getattr(self.dock_manager, "_main_window", None)
        self.dock_widget = self.dock_manager.get_dock_widget(self.dock_id)
        
        if self.dock_widget and self.main_window:
            # Save state for undo
            self.dock_manager.save_dock_state(self.dock_id)
            
            if self.dock_id in self.dock_manager._dock_states:
                self.dock_state = self.dock_manager._dock_states[self.dock_id].copy()
                
                # Save states of children as well
                for child_id in self.dock_manager.get_all_descendant_docks(self.dock_id):
                    self.dock_manager.save_dock_state(child_id)
                    self.children_states[child_id] = self.dock_manager._dock_states[child_id].copy()
            
            # Remove the dock and all its children from the main window
            self._remove_dock_and_children(self.dock_id)
            
    def undo(self) -> None:
        """Undo the command, restoring the dock widget."""
        if not self.dock_state or not self.dock_widget or not self.main_window:
            return
            
        # First restore this dock's registration
        self.dock_manager._dock_states[self.dock_id] = self.dock_state.copy()
        
        # Restore child docks
        for child_id, child_state in self.children_states.items():
            self.dock_manager._dock_states[child_id] = child_state.copy()
            
        # Add docks back to main window in hierarchy order
        self._restore_dock_hierarchy(self.dock_id)
        
    def _remove_dock_and_children(self, dock_id: str) -> None:
        """
        Remove a dock and all its children.
        
        Args:
            dock_id: ID of the dock to remove
        """
        # Process children first
        for child_id in self.dock_manager.get_child_docks(dock_id):
            self._remove_dock_and_children(child_id)
            
        # Now remove this dock
        dock_widget = self.dock_manager.get_dock_widget(dock_id)
        if dock_widget and self.main_window:
            self.main_window.removeDockWidget(dock_widget)
            dock_widget.hide()
            
        # Unregister from dock manager
        self.dock_manager.unregister_dock(dock_id)
        
    def _restore_dock_hierarchy(self, dock_id: str) -> None:
        """
        Restore a dock and its children in the correct hierarchy.
        
        Args:
            dock_id: ID of the dock to restore
        """
        # Get the dock widget
        dock_widget = self.dock_manager.get_dock_widget(dock_id)
        
        if dock_widget and self.main_window:
            # Restore this dock to the main window
            state = self.dock_manager._dock_states[dock_id]["state"]
            area = state.get("area", Qt.RightDockWidgetArea)
            
            if area is not None:
                self.main_window.addDockWidget(area, dock_widget)
                
            # Set floating state
            dock_widget.setFloating(state.get("floating", False))
            
            # Restore position for floating docks
            if state.get("floating", False) and "position" in state:
                pos = state["position"]
                dock_widget.resize(pos["width"], pos["height"])
                dock_widget.move(pos["x"], pos["y"])
                
            # Show the dock
            dock_widget.setVisible(state.get("visible", True))
            
            # Now restore children
            for child_id in self.dock_manager.get_child_docks(dock_id):
                self._restore_dock_hierarchy(child_id)


class DockLocationCommand(Command):
    """
    Command for changing a dock's location (area, floating state, etc.).
    """
    
    def __init__(self, dock_id: str):
        """
        Initialize the dock location command.
        
        Args:
            dock_id: ID of the dock to change
        """
        self.dock_id = dock_id
        self.dock_manager = get_dock_manager()
        self.old_state = None
        self.new_state = None
        
    def execute(self) -> None:
        """Execute the command."""
        # Save old state before changes
        if self.old_state is None:  # Only on first execute
            self.dock_manager.save_dock_state(self.dock_id)
            self.old_state = self.dock_manager._dock_states[self.dock_id]["state"].copy()
            
        # Save new state after changes
        self.dock_manager.save_dock_state(self.dock_id)
        self.new_state = self.dock_manager._dock_states[self.dock_id]["state"].copy()
        
    def undo(self) -> None:
        """Undo the command."""
        if not self.old_state or self.dock_id not in self.dock_manager._dock_states:
            return
            
        # Restore old state
        self.dock_manager._dock_states[self.dock_id]["state"] = self.old_state
        self.dock_manager.restore_dock_state(self.dock_id)
        
    def redo(self) -> None:
        """Redo the command."""
        if not self.new_state or self.dock_id not in self.dock_manager._dock_states:
            return
            
        # Restore new state
        self.dock_manager._dock_states[self.dock_id]["state"] = self.new_state
        self.dock_manager.restore_dock_state(self.dock_id)


class SaveLayoutCommand(Command):
    """
    Command for saving the current dock layout.
    """
    
    def __init__(self, layout_name: str):
        """
        Initialize the save layout command.
        
        Args:
            layout_name: Name to identify the layout
        """
        self.layout_name = layout_name
        self.dock_manager = get_dock_manager()
        self.old_layout = None
        self.new_layout = None
        
    def execute(self) -> None:
        """Execute the command."""
        # Save the current layout
        self.new_layout = self.dock_manager.serialize_layout()
        
        # TODO: If needed, integrate with a layout manager to store named layouts
        
    def undo(self) -> None:
        """Undo the command."""
        # TODO: If needed, restore the previous layout
        pass
    
    def redo(self) -> None:
        """Redo the command."""
        # Redirect to execute for simplicity
        self.execute()