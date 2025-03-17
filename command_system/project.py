"""
Project model for PySignalDecipher.

This module provides the central Project model that integrates with
the command system for tracking and serializing all project state.
"""

import time
import uuid
import json
import os
from typing import Dict, List, Any, Optional, Set, Type

from .observable import Observable, ObservableProperty
from .command_manager import CommandManager


class SignalData(Observable):
    """
    Represents signal data within a project.
    
    This is a simplified example - in a real implementation, this would
    contain actual signal data and methods for processing.
    """
    
    name = ObservableProperty[str]("")
    sample_rate = ObservableProperty[float](44100.0)
    
    def __init__(self, name: str = "", data=None):
        """
        Initialize signal data.
        
        Args:
            name: Name for the signal
            data: The actual signal data (NumPy array, etc.)
        """
        super().__init__()
        self.id = str(uuid.uuid4())
        self.name = name
        self._data = data or []
        self._metadata = {}
    
    def get_data(self):
        """
        Get the raw signal data.
        
        Returns:
            The signal data
        """
        return self._data
    
    def set_data(self, data):
        """
        Set the signal data.
        
        Args:
            data: New signal data
        """
        self._data = data
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get signal metadata.
        
        Returns:
            Dictionary of metadata
        """
        return self._metadata
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the signal data for storage.
        
        Returns:
            Dictionary with serialized state
        """
        return {
            "id": self.id,
            "name": self.name,
            "sample_rate": self.sample_rate,
            "metadata": self._metadata,
            # Data would require special handling, simplified here
            "data_ref": f"signals/{self.id}/data"  # Reference to where data is stored
        }
    
    @classmethod
    def deserialize(cls, state: Dict[str, Any], data=None) -> 'SignalData':
        """
        Create a signal from serialized state.
        
        Args:
            state: Serialized state
            data: Optional raw data to restore
            
        Returns:
            New SignalData instance
        """
        signal = cls(state.get("name", ""))
        signal.id = state.get("id", str(uuid.uuid4()))
        signal.sample_rate = state.get("sample_rate", 44100.0)
        signal._metadata = state.get("metadata", {})
        
        if data is not None:
            signal._data = data
        
        return signal


class WorkspaceState(Observable):
    """
    Represents the state of a workspace within a project.
    
    This tracks layout, open signals, and other workspace-specific settings.
    """
    
    active_layout_id = ObservableProperty[str]("")
    
    def __init__(self, workspace_id: str):
        """
        Initialize workspace state.
        
        Args:
            workspace_id: ID of the workspace
        """
        super().__init__()
        self.workspace_id = workspace_id
        self._dock_states = {}
        self._settings = {}
    
    def get_dock_state(self, dock_id: str) -> Dict[str, Any]:
        """
        Get the state of a dock widget.
        
        Args:
            dock_id: ID of the dock widget
            
        Returns:
            Dictionary with dock state
        """
        return self._dock_states.get(dock_id, {})
    
    def set_dock_state(self, dock_id: str, state: Dict[str, Any]) -> None:
        """
        Set the state of a dock widget.
        
        Args:
            dock_id: ID of the dock widget
            state: New dock state
        """
        self._dock_states[dock_id] = state
    
    def get_setting(self, key: str, default=None) -> Any:
        """
        Get a workspace setting.
        
        Args:
            key: Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            The setting value
        """
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a workspace setting.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self._settings[key] = value
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize workspace state.
        
        Returns:
            Dictionary with serialized state
        """
        return {
            "workspace_id": self.workspace_id,
            "active_layout_id": self.active_layout_id,
            "dock_states": self._dock_states,
            "settings": self._settings
        }
    
    @classmethod
    def deserialize(cls, state: Dict[str, Any]) -> 'WorkspaceState':
        """
        Create a workspace state from serialized data.
        
        Args:
            state: Serialized state
            
        Returns:
            New WorkspaceState instance
        """
        workspace_id = state.get("workspace_id", "")
        ws = cls(workspace_id)
        ws.active_layout_id = state.get("active_layout_id", "")
        ws._dock_states = state.get("dock_states", {})
        ws._settings = state.get("settings", {})
        return ws


class Project(Observable):
    """
    Represents a complete PySignalDecipher project.
    
    Contains all signals, workspace states, and project settings,
    and provides methods for serialization and deserialization.
    """
    
    name = ObservableProperty[str]("Untitled Project")
    modified = ObservableProperty[bool](False)
    
    def __init__(self, name: str = "Untitled Project"):
        """
        Initialize a new project.
        
        Args:
            name: Project name
        """
        super().__init__()
        self.id = str(uuid.uuid4())
        self.name = name
        self.modified = False
        self.created_time = time.time()
        self.modified_time = time.time()
        
        self._signals: Dict[str, SignalData] = {}
        self._workspaces: Dict[str, WorkspaceState] = {}
        self._command_manager = None  # Will be set later
    
    def set_command_manager(self, command_manager: CommandManager) -> None:
        """
        Set the command manager for this project.
        
        Args:
            command_manager: The command manager
        """
        self._command_manager = command_manager
        if command_manager:
            command_manager.set_active_project(self)
    
    def get_command_manager(self) -> Optional[CommandManager]:
        """
        Get the command manager for this project.
        
        Returns:
            The command manager or None
        """
        return self._command_manager
    
    def mark_modified(self) -> None:
        """Mark the project as modified."""
        self.modified = True
        self.modified_time = time.time()
    
    def add_signal(self, signal: SignalData) -> None:
        """
        Add a signal to the project.
        
        Args:
            signal: The signal to add
        """
        self._signals[signal.id] = signal
        signal.property_changed.connect(lambda *args: self.mark_modified())
        self.mark_modified()
    
    def remove_signal(self, signal_id: str) -> None:
        """
        Remove a signal from the project.
        
        Args:
            signal_id: ID of the signal to remove
        """
        if signal_id in self._signals:
            del self._signals[signal_id]
            self.mark_modified()
    
    def get_signal(self, signal_id: str) -> Optional[SignalData]:
        """
        Get a signal by ID.
        
        Args:
            signal_id: ID of the signal
            
        Returns:
            The signal or None if not found
        """
        return self._signals.get(signal_id)
    
    def get_all_signals(self) -> Dict[str, SignalData]:
        """
        Get all signals in the project.
        
        Returns:
            Dictionary of signal IDs to signals
        """
        return self._signals.copy()
    
    def get_workspace_state(self, workspace_id: str) -> WorkspaceState:
        """
        Get the state for a workspace.
        
        If the workspace state doesn't exist, a new one is created.
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            The workspace state
        """
        if workspace_id not in self._workspaces:
            self._workspaces[workspace_id] = WorkspaceState(workspace_id)
            self._workspaces[workspace_id].property_changed.connect(
                lambda *args: self.mark_modified())
        
        return self._workspaces[workspace_id]
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the project for storage.
        
        Returns:
            Dictionary with serialized project state
        """
        return {
            "id": self.id,
            "name": self.name,
            "created_time": self.created_time,
            "modified_time": self.modified_time,
            "signals": {
                signal_id: signal.serialize()
                for signal_id, signal in self._signals.items()
            },
            "workspaces": {
                workspace_id: workspace.serialize()
                for workspace_id, workspace in self._workspaces.items()
            },
            "command_history": self._serialize_command_history()
        }
    
    def _serialize_command_history(self) -> List[Dict[str, Any]]:
        """
        Serialize command history if available.
        
        Returns:
            List of serialized commands or empty list
        """
        if self._command_manager:
            return self._command_manager.get_serializable_history()
        return []
    
    def save(self, file_path: str) -> bool:
        """
        Save the project to a file.
        
        Args:
            file_path: Path to save the project
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # In a real implementation, you would use a proper serialization
            # format and handle signal data separately (e.g., HDF5)
            project_data = self.serialize()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            self.modified = False
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    @classmethod
    def load(cls, file_path: str, command_manager: Optional[CommandManager] = None) -> Optional['Project']:
        """
        Load a project from a file.
        
        Args:
            file_path: Path to the project file
            command_manager: Optional command manager to restore history
            
        Returns:
            The loaded project or None if loading failed
        """
        try:
            with open(file_path, 'r') as f:
                project_data = json.load(f)
            
            # Create a new project
            project = cls(project_data.get("name", "Untitled Project"))
            project.id = project_data.get("id", str(uuid.uuid4()))
            project.created_time = project_data.get("created_time", time.time())
            project.modified_time = project_data.get("modified_time", time.time())
            
            # Load signals
            for signal_id, signal_data in project_data.get("signals", {}).items():
                # In a real implementation, you would load the actual signal data
                # from a separate file or HDF5 dataset
                signal = SignalData.deserialize(signal_data)
                project.add_signal(signal)
            
            # Load workspace states
            for workspace_id, workspace_data in project_data.get("workspaces", {}).items():
                workspace = WorkspaceState.deserialize(workspace_data)
                project._workspaces[workspace_id] = workspace
                workspace.property_changed.connect(
                    lambda *args: project.mark_modified())
            
            # Set command manager and restore history
            if command_manager:
                project.set_command_manager(command_manager)
                command_history = project_data.get("command_history", [])
                command_manager.restore_history_from_serialized(command_history)
            
            project.modified = False
            return project
        except Exception as e:
            print(f"Error loading project: {e}")
            return None