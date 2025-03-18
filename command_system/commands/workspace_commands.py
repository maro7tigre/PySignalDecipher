"""
Workspace-related commands for PySignalDecipher.

This module provides commands for modifying workspace state, including
changing layouts, adding/removing docks, and setting workspace preferences.
"""

from typing import Dict, Any, Optional
import uuid

from ..command import Command
from ..project import Project, WorkspaceState


class ChangeLayoutCommand(Command):
    """Command to change the active layout of a workspace."""
    
    def __init__(self, workspace: WorkspaceState, new_layout_id: str):
        """
        Initialize the command.
        
        Args:
            workspace: The workspace to modify
            new_layout_id: ID of the new layout
        """
        self.workspace = workspace
        self.new_layout_id = new_layout_id
        self.old_layout_id = workspace.active_layout_id
    
    def execute(self) -> None:
        """Change the active layout."""
        self.workspace.active_layout_id = self.new_layout_id
    
    def undo(self) -> None:
        """Restore the previous layout."""
        self.workspace.active_layout_id = self.old_layout_id
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "workspace_id": self.workspace.workspace_id,
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
        # This requires a way to find workspaces by ID
        workspace = _get_workspace_by_id(state["workspace_id"])
        cmd = cls(workspace, state["new_layout_id"])
        cmd.old_layout_id = state["old_layout_id"]
        return cmd


class SetDockStateCommand(Command):
    """Command to set the state of a dock widget."""
    
    def __init__(self, workspace: WorkspaceState, dock_id: str, new_state: Dict[str, Any]):
        """
        Initialize the command.
        
        Args:
            workspace: The workspace containing the dock
            dock_id: ID of the dock widget
            new_state: New state for the dock
        """
        self.workspace = workspace
        self.dock_id = dock_id
        self.new_state = new_state
        self.old_state = workspace.get_dock_state(dock_id)
    
    def execute(self) -> None:
        """Set the new dock state."""
        self.workspace.set_dock_state(self.dock_id, self.new_state)
    
    def undo(self) -> None:
        """Restore the previous dock state."""
        self.workspace.set_dock_state(self.dock_id, self.old_state)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "workspace_id": self.workspace.workspace_id,
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
        workspace = _get_workspace_by_id(state["workspace_id"])
        cmd = cls(workspace, state["dock_id"], state["new_state"])
        cmd.old_state = state["old_state"]
        return cmd


class SetWorkspaceSettingCommand(Command):
    """Command to change a workspace setting."""
    
    def __init__(self, workspace: WorkspaceState, key: str, value: Any):
        """
        Initialize the command.
        
        Args:
            workspace: The workspace to modify
            key: Setting key
            value: New value
        """
        self.workspace = workspace
        self.key = key
        self.new_value = value
        self.old_value = workspace.get_setting(key)
    
    def execute(self) -> None:
        """Set the new value."""
        self.workspace.set_setting(self.key, self.new_value)
    
    def undo(self) -> None:
        """Restore the old value."""
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
            "workspace_id": self.workspace.workspace_id,
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
        workspace = _get_workspace_by_id(state["workspace_id"])
        cmd = cls(workspace, state["key"], state["new_value"])
        cmd.old_value = state["old_value"]
        return cmd


class CreateDockCommand(Command):
    """Command to create a new dock widget"""
    
    def __init__(self, workspace_state, dock_type, dock_config=None):
        self.workspace = workspace_state
        self.dock_type = dock_type
        self.dock_config = dock_config or {}
        self.dock_id = None
        self.dock = None
        self.variable_registry = None  # Will be injected
    
    def set_variable_registry(self, registry):
        """Set the variable registry to use"""
        self.variable_registry = registry
    
    def execute(self):
        """Create and register the dock"""
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
        
        # Factory method to create actual dock widget would be called here
        # self.dock = create_dock_widget(self.dock_type, self.dock_id, self.dock_config)
        
        return self.dock_id
    
    def undo(self):
        """Remove the dock"""
        if self.dock_id:
            # Unregister all associated variables
            if self.variable_registry:
                self.variable_registry.unregister_parent(self.dock_id)
            
            # Remove from workspace
            self.workspace.remove_dock(self.dock_id)
    
    def get_state(self):
        return {
            "workspace_id": self.workspace.workspace_id,
            "dock_type": self.dock_type,
            "dock_config": self.dock_config,
            "dock_id": self.dock_id
        }
    
    @classmethod
    def from_state(cls, state):
        workspace = _get_workspace_by_id(state["workspace_id"])
        cmd = cls(workspace, state["dock_type"], state["dock_config"])
        cmd.dock_id = state["dock_id"]
        return cmd


# Helper function - in a real implementation, this would access
# a global registry or use context

def _get_workspace_by_id(workspace_id: str) -> Optional[WorkspaceState]:
    """Get a workspace by ID from some global registry."""
    # Implementation would depend on your application structure
    return None