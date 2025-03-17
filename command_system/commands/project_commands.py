"""
Project-level commands for PySignalDecipher.

This module provides commands for operations on the project as a whole,
such as renaming the project or changing project settings.
"""

from typing import Dict, Any, Optional

from ..command import Command
from ..project import Project


class RenameProjectCommand(Command):
    """Command to rename the project."""
    
    def __init__(self, project: Project, new_name: str):
        """
        Initialize the command.
        
        Args:
            project: The project to rename
            new_name: New name for the project
        """
        self.project = project
        self.new_name = new_name
        self.old_name = project.name
    
    def execute(self) -> None:
        """Rename the project."""
        self.project.name = self.new_name
    
    def undo(self) -> None:
        """Restore the original name."""
        self.project.name = self.old_name
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "project_id": self.project.id,
            "old_name": self.old_name,
            "new_name": self.new_name
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'RenameProjectCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        # This requires a way to find projects by ID
        project = _get_project_by_id(state["project_id"])
        cmd = cls(project, state["new_name"])
        cmd.old_name = state["old_name"]
        return cmd


class BatchCommand(Command):
    """
    Command to execute multiple commands as a batch.
    
    This is similar to CompoundCommand but is specifically for
    project-level operations where multiple steps need to be
    performed atomically.
    """
    
    def __init__(self, project: Project, name: str, commands: list[Command] = None):
        """
        Initialize the batch command.
        
        Args:
            project: The project
            name: Descriptive name for the batch
            commands: Optional list of commands
        """
        self.project = project
        self.name = name
        self.commands = commands or []
    
    def add_command(self, command: Command) -> None:
        """
        Add a command to the batch.
        
        Args:
            command: The command to add
        """
        self.commands.append(command)
    
    def execute(self) -> None:
        """Execute all commands in the batch."""
        for command in self.commands:
            command.execute()
    
    def undo(self) -> None:
        """Undo all commands in reverse order."""
        for command in reversed(self.commands):
            command.undo()
    
    def redo(self) -> None:
        """Redo all commands in the original order."""
        for command in self.commands:
            command.redo()
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            "project_id": self.project.id,
            "name": self.name,
            "commands": [
                {
                    "type": cmd.__class__.__name__,
                    "state": cmd.get_state()
                }
                for cmd in self.commands
            ]
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> 'BatchCommand':
        """
        Create a command from serialized state.
        
        Args:
            state: The serialized state
            
        Returns:
            New command instance
        """
        from ..command import CommandFactory
        project = _get_project_by_id(state["project_id"])
        cmd = cls(project, state["name"])
        
        for command_data in state.get("commands", []):
            command = CommandFactory.create_from_state(
                command_data["type"], 
                command_data["state"]
            )
            if command:
                cmd.add_command(command)
        
        return cmd


# Helper function - in a real implementation, this would access
# a global registry or use context

def _get_project_by_id(project_id: str) -> Optional[Project]:
    """Get a project by ID from some global registry."""
    # Implementation would depend on your application structure
    return None