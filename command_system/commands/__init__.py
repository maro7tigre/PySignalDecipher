"""
Command implementations for PySignalDecipher.

This package contains concrete command implementations for different
types of operations in the application.
"""

from .signal_commands import AddSignalCommand, RemoveSignalCommand, RenameSignalCommand
from .workspace_commands import ChangeLayoutCommand, SetDockStateCommand, SetWorkspaceSettingCommand
from .project_commands import RenameProjectCommand, BatchCommand

# Register all commands with the CommandFactory
from ..command import CommandFactory

# Signal commands
CommandFactory.register(AddSignalCommand)
CommandFactory.register(RemoveSignalCommand)
CommandFactory.register(RenameSignalCommand)

# Workspace commands
CommandFactory.register(ChangeLayoutCommand)
CommandFactory.register(SetDockStateCommand)
CommandFactory.register(SetWorkspaceSettingCommand)

# Project commands
CommandFactory.register(RenameProjectCommand)
CommandFactory.register(BatchCommand)

__all__ = [
    # Signal commands
    'AddSignalCommand',
    'RemoveSignalCommand',
    'RenameSignalCommand',
    
    # Workspace commands
    'ChangeLayoutCommand',
    'SetDockStateCommand',
    'SetWorkspaceSettingCommand',
    
    # Project commands
    'RenameProjectCommand',
    'BatchCommand',
]