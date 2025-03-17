"""
Signal-related commands for PySignalDecipher.

This module provides commands for creating, modifying, and deleting signals.
"""

import uuid
from typing import Dict, Any, Optional

from ..command import Command
from ..project import Project, SignalData


class AddSignalCommand(Command):
    """Command to add a signal to the project."""
    
    def __init__(self, project: Project, signal: SignalData):
        """
        Initialize the command.
        
        Args:
            project: The project to modify
            signal: The signal to add
        """
        self.project = project
        self.signal = signal
    
    def execute(self) -> None:
        """Add the signal to the project."""
        self.project.add_signal(self.signal)
    
    def undo(self) -> None:
        """Remove the signal from the project."""
        self.project.remove_signal(self.signal.id)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "project_id": self.project.id,
            "signal": self.signal.serialize()
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'AddSignalCommand':
        """
        Create a command from serialized state.
        
        This simplified implementation assumes the project is accessible
        by ID through some global registry. In a real implementation,
        you would need to pass the project context explicitly.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        # This is a simplified implementation - in reality, you'd need
        # to handle obtaining the project reference
        from ..project import Project, SignalData
        # Assume there's a way to get the project by ID
        project = _get_project_by_id(state["project_id"])
        signal = SignalData.deserialize(state["signal"])
        return cls(project, signal)


class RemoveSignalCommand(Command):
    """Command to remove a signal from the project."""
    
    def __init__(self, project: Project, signal_id: str):
        """
        Initialize the command.
        
        Args:
            project: The project to modify
            signal_id: ID of the signal to remove
        """
        self.project = project
        self.signal_id = signal_id
        self.signal = None  # Will be captured during execute
    
    def execute(self) -> None:
        """Remove the signal from the project."""
        # Capture the signal before removing it so we can restore it
        self.signal = self.project.get_signal(self.signal_id)
        if self.signal:
            self.project.remove_signal(self.signal_id)
    
    def undo(self) -> None:
        """Restore the signal to the project."""
        if self.signal:
            self.project.add_signal(self.signal)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "project_id": self.project.id,
            "signal_id": self.signal_id,
            "signal": self.signal.serialize() if self.signal else None
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'RemoveSignalCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        # Similar to AddSignalCommand, this is simplified
        from ..project import Project, SignalData
        project = _get_project_by_id(state["project_id"])
        cmd = cls(project, state["signal_id"])
        if state["signal"]:
            cmd.signal = SignalData.deserialize(state["signal"])
        return cmd


class RenameSignalCommand(Command):
    """Command to rename a signal."""
    
    def __init__(self, signal: SignalData, new_name: str):
        """
        Initialize the command.
        
        Args:
            signal: The signal to rename
            new_name: The new name for the signal
        """
        self.signal = signal
        self.new_name = new_name
        self.old_name = signal.name
    
    def execute(self) -> None:
        """Rename the signal."""
        self.signal.name = self.new_name
    
    def undo(self) -> None:
        """Restore the original name."""
        self.signal.name = self.old_name
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "signal_id": self.signal.id,
            "old_name": self.old_name,
            "new_name": self.new_name
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'RenameSignalCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        # This requires a way to find signals by ID
        signal = _get_signal_by_id(state["signal_id"])
        cmd = cls(signal, state["new_name"])
        cmd.old_name = state["old_name"]
        return cmd


# Helper functions for demonstration - in a real implementation,
# these would access a global registry or use context

def _get_project_by_id(project_id: str) -> Optional[Project]:
    """Get a project by ID from some global registry."""
    # Implementation would depend on your application structure
    return None

def _get_signal_by_id(signal_id: str) -> Optional[SignalData]:
    """Get a signal by ID from some global registry."""
    # Implementation would depend on your application structure
    return None