"""
Workspace-related commands for PySignalDecipher.

This module provides commands for modifying workspace state, including
changing layouts, adding/removing docks, and setting workspace preferences.
"""

from typing import Dict, Any, Optional
import uuid
from PySide6.QtWidgets import QMainWindow, QInputDialog, QMessageBox

from ..command import Command, CommandContext
from ..project import Project, WorkspaceState
from ui.layout_manager import LayoutManagerDialog

from PySide6.QtWidgets import QApplication


class ChangeLayoutCommand(Command):
    """Command to change the active layout of a workspace."""
    
    def __init__(self, context: Optional[CommandContext] = None, workspace=None, new_layout_id: str = None):
        """
        Initialize the command.
        
        Args:
            context: Command execution context
            workspace: The workspace to modify
            new_layout_id: ID of the new layout
        """
        super().__init__(context)
        self.workspace = workspace
        self.new_layout_id = new_layout_id
        self.old_layout_id = workspace.active_layout_id if workspace else None
    
    def execute(self) -> None:
        """Change the active layout."""
        if self.workspace:
            self.workspace.active_layout_id = self.new_layout_id
    
    def undo(self) -> None:
        """Restore the previous layout."""
        if self.workspace:
            self.workspace.active_layout_id = self.old_layout_id
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "workspace_id": self.workspace.workspace_id if self.workspace else None,
            "old_layout_id": self.old_layout_id,
            "new_layout_id": self.new_layout_id
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'ChangeLayoutCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        # Create a context for the command
        cmd = cls()
        cmd.old_layout_id = state.get("old_layout_id")
        cmd.new_layout_id = state.get("new_layout_id")
        
        # Workspace will need to be resolved at runtime
        # based on the workspace_id
        return cmd


class SetDockStateCommand(Command):
    """Command to set the state of a dock widget."""
    
    def __init__(self, context: Optional[CommandContext] = None, 
                workspace=None, dock_id: str = None, new_state: Dict[str, Any] = None):
        """
        Initialize the command.
        
        Args:
            context: Command execution context
            workspace: The workspace containing the dock
            dock_id: ID of the dock widget
            new_state: New state for the dock
        """
        super().__init__(context)
        self.workspace = workspace
        self.dock_id = dock_id
        self.new_state = new_state
        self.old_state = workspace.get_dock_state(dock_id) if workspace and dock_id else {}
    
    def execute(self) -> None:
        """Set the new dock state."""
        if self.workspace and self.dock_id and self.new_state:
            self.workspace.set_dock_state(self.dock_id, self.new_state)
    
    def undo(self) -> None:
        """Restore the previous dock state."""
        if self.workspace and self.dock_id:
            self.workspace.set_dock_state(self.dock_id, self.old_state)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "workspace_id": self.workspace.workspace_id if self.workspace else None,
            "dock_id": self.dock_id,
            "old_state": self.old_state,
            "new_state": self.new_state
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'SetDockStateCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        cmd = cls()
        cmd.dock_id = state.get("dock_id")
        cmd.old_state = state.get("old_state", {})
        cmd.new_state = state.get("new_state", {})
        return cmd


class SetWorkspaceSettingCommand(Command):
    """Command to change a workspace setting."""
    
    def __init__(self, context: Optional[CommandContext] = None, 
                workspace=None, key: str = None, value: Any = None):
        """
        Initialize the command.
        
        Args:
            context: Command execution context
            workspace: The workspace to modify
            key: Setting key
            value: New value
        """
        super().__init__(context)
        self.workspace = workspace
        self.key = key
        self.new_value = value
        self.old_value = workspace.get_setting(key) if workspace and key else None
    
    def execute(self) -> None:
        """Set the new value."""
        if self.workspace and self.key is not None:
            self.workspace.set_setting(self.key, self.new_value)
    
    def undo(self) -> None:
        """Restore the old value."""
        if self.workspace and self.key is not None:
            if self.old_value is None:
                # Setting didn't exist before
                # In a real implementation, you might want to remove the setting
                self.workspace.set_setting(self.key, None)
            else:
                self.workspace.set_setting(self.key, self.old_value)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "workspace_id": self.workspace.workspace_id if self.workspace else None,
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'SetWorkspaceSettingCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        cmd = cls()
        cmd.key = state.get("key")
        cmd.old_value = state.get("old_value")
        cmd.new_value = state.get("new_value")
        return cmd


class CreateDockCommand(Command):
    """Command to create a new dock widget"""
    
    def __init__(self, context: Optional[CommandContext] = None, 
                workspace_state=None, dock_type=None, dock_config=None):
        """
        Initialize the command.
        
        Args:
            context: Command execution context
            workspace_state: Workspace state to add dock to
            dock_type: Type of dock to create
            dock_config: Optional dock configuration
        """
        super().__init__(context)
        self.workspace = workspace_state
        self.dock_type = dock_type
        self.dock_config = dock_config or {}
        self.dock_id = None
        self.dock = None
    
    def execute(self):
        """Create and register the dock"""
        if not self.workspace or not self.dock_type:
            return None
            
        self.dock_id = str(uuid.uuid4())
        
        # Create dock configuration
        dock_state = {
            "type": self.dock_type,
            "id": self.dock_id,
            "config": self.dock_config,
            "position": {"x": 0, "y": 0, "width": 300, "height": 200}
        }
        
        # Add to workspace
        self.workspace.set_dock_state(self.dock_id, dock_state)
        
        return self.dock_id
    
    def undo(self):
        """Remove the dock"""
        if self.dock_id and self.workspace:
            # Remove from workspace
            self.workspace.remove_dock(self.dock_id)
    
    def get_state(self):
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "workspace_id": self.workspace.workspace_id if self.workspace else None,
            "dock_type": self.dock_type,
            "dock_config": self.dock_config,
            "dock_id": self.dock_id
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'CreateDockCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        cmd = cls()
        cmd.dock_type = state.get("dock_type")
        cmd.dock_config = state.get("dock_config", {})
        cmd.dock_id = state.get("dock_id")
        return cmd


class RemoveDockCommand(Command):
    """Command to remove a dock widget"""
    
    def __init__(self, context: Optional[CommandContext] = None, 
                workspace_state=None, dock_id=None):
        """
        Initialize the command.
        
        Args:
            context: Command execution context
            workspace_state: Workspace state to remove dock from
            dock_id: ID of dock to remove
        """
        super().__init__(context)
        self.workspace = workspace_state
        self.dock_id = dock_id
        self.dock_state = None
    
    def execute(self):
        """Remove the dock from the workspace"""
        if not self.workspace or not self.dock_id:
            return False
            
        # Save the dock state for undo
        self.dock_state = self.workspace.get_dock_state(self.dock_id)
        
        # Remove the dock
        self.workspace.remove_dock(self.dock_id)
        return True
    
    def undo(self):
        """Restore the removed dock"""
        if self.workspace and self.dock_id and self.dock_state:
            # Restore the dock
            self.workspace.set_dock_state(self.dock_id, self.dock_state)
    
    def get_state(self):
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "workspace_id": self.workspace.workspace_id if self.workspace else None,
            "dock_id": self.dock_id,
            "dock_state": self.dock_state
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'RemoveDockCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        cmd = cls()
        cmd.dock_id = state.get("dock_id")
        cmd.dock_state = state.get("dock_state")
        return cmd


class ApplyLayoutCommand(Command):
    """Command to apply a layout to a workspace"""
    
    def __init__(self, context: Optional[CommandContext] = None, 
                workspace_id=None, layout_id=None, main_window=None):
        """
        Initialize the command.
        
        Args:
            context: Command execution context
            workspace_id: ID of the workspace
            layout_id: ID of the layout to apply
            main_window: Main window to apply the layout to
        """
        super().__init__(context)
        self.workspace_id = workspace_id
        self.layout_id = layout_id
        self.main_window = main_window
        self.previous_layout_id = None
        self.previous_state = None
    
    def execute(self):
        """Apply the layout to the workspace"""
        if not self.context or not self.workspace_id or not self.layout_id or not self.main_window:
            return False
            
        # Get the layout manager
        layout_manager = self.get_service("LayoutManager")
        if not layout_manager:
            return False
            
        # Save the current layout ID for undo
        self.previous_layout_id = layout_manager.get_active_layout(self.workspace_id)
        if self.previous_layout_id:
            self.previous_layout_id = self.previous_layout_id.id
            
        # Save the current window state for undo
        self.previous_state = self.main_window.saveState()
        
        # Apply the new layout
        result = layout_manager.apply_layout(self.workspace_id, self.layout_id, self.main_window)
        return result
    
    def undo(self):
        """Restore the previous layout"""
        if not self.context or not self.workspace_id or not self.previous_layout_id or not self.main_window:
            return
            
        # Get the layout manager
        layout_manager = self.get_service("LayoutManager")
        if not layout_manager:
            return
            
        # Apply the previous layout
        if self.previous_state:
            self.main_window.restoreState(self.previous_state)
            
        # Set the previous layout as active
        layout_manager.set_active_layout(self.workspace_id, self.previous_layout_id)
    
    def get_state(self):
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "workspace_id": self.workspace_id,
            "layout_id": self.layout_id,
            "previous_layout_id": self.previous_layout_id,
            "previous_state": self.previous_state.toBase64().data().decode('ascii') if self.previous_state else None
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'ApplyLayoutCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        from PySide6.QtCore import QByteArray
        
        cmd = cls()
        cmd.workspace_id = state.get("workspace_id")
        cmd.layout_id = state.get("layout_id")
        cmd.previous_layout_id = state.get("previous_layout_id")
        
        # Convert the previous state back to a QByteArray
        previous_state_str = state.get("previous_state")
        if previous_state_str:
            cmd.previous_state = QByteArray.fromBase64(previous_state_str.encode('ascii'))
            
        return cmd


class SaveLayoutCommand(Command):
    """Command to save the current layout of a workspace"""
    
    def __init__(self, context: Optional[CommandContext] = None, 
                workspace_id=None, main_window=None):
        """
        Initialize the command.
        
        Args:
            context: Command execution context
            workspace_id: ID of the workspace
            main_window: Main window to save the layout from
        """
        super().__init__(context)
        self.workspace_id = workspace_id
        self.main_window = main_window
        self.layout_id = None
        self.layout_name = None
    
    def execute(self):
        """Save the current layout"""
        if not self.context or not self.workspace_id or not self.main_window:
            return False
            
        # Get a layout name from the user
        name, ok = QInputDialog.getText(
            self.main_window, 
            "Save Layout", 
            "Enter a name for this layout:"
        )
        
        if not ok or not name:
            return False
        
        # Get the layout manager
        layout_manager = self.get_service("LayoutManager")
        if not layout_manager:
            return False
            
        # Create a new layout
        self.layout_id = layout_manager.create_layout(
            self.workspace_id,
            name,
            self.main_window
        )
        
        self.layout_name = name
        return bool(self.layout_id)
    
    def undo(self):
        """Remove the saved layout"""
        if not self.context or not self.workspace_id or not self.layout_id:
            return
            
        # Get the layout manager
        layout_manager = self.get_service("LayoutManager")
        if not layout_manager:
            return
            
        # Delete the layout
        layout_manager.delete_layout(self.workspace_id, self.layout_id)
    
    def get_state(self):
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "workspace_id": self.workspace_id,
            "layout_id": self.layout_id,
            "layout_name": self.layout_name
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'SaveLayoutCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        cmd = cls()
        cmd.workspace_id = state.get("workspace_id")
        cmd.layout_id = state.get("layout_id")
        cmd.layout_name = state.get("layout_name")
        return cmd


class ManageLayoutsCommand(Command):
    """Command to manage layouts for a workspace"""
    
    def __init__(self, context: Optional[CommandContext] = None, 
                workspace_id=None):
        """
        Initialize the command.
        
        Args:
            context: Command execution context
            workspace_id: ID of the workspace
        """
        super().__init__(context)
        self.workspace_id = workspace_id
        
    def execute(self):
        """Show the layout manager dialog"""
        if not self.context or not self.workspace_id:
            return False
            
        # Get the layout manager
        layout_manager = self.get_service("LayoutManager")
        if not layout_manager:
            return False
        
        # Get the active window to use as parent
        for window in QApplication.topLevelWidgets():
            if isinstance(window, QMainWindow) and window.isVisible():
                parent = window
                break
        else:
            parent = None
            
        # Show the layout manager dialog
        dialog = LayoutManagerDialog(
            parent,
            layout_manager,
            self.workspace_id
        )
        dialog.exec_()
        return True
    
    def undo(self):
        """Cannot undo showing a dialog"""
        pass
    
    def get_state(self):
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "workspace_id": self.workspace_id
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'ManageLayoutsCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        cmd = cls()
        cmd.workspace_id = state.get("workspace_id")
        return cmd