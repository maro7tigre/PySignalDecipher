"""
Signal variable implementation for PySignalDecipher.

This module provides a specialized variable system for handling signal data
with support for subscriber notifications, file-based storage for large datasets,
and integration with the command system.
"""

import uuid
import os
import json
import numpy as np
import h5py
from typing import Any, Dict, Callable, List, Optional, Set, Union
from PySide6.QtCore import QObject, Signal

from .observable import Observable, ObservableProperty
from .command import Command, CommandFactory


class SignalVariable:
    """
    A variable that can be linked to multiple components and notifies
    subscribers when its value changes.
    
    This class provides a way to manage signal data that may be too large
    to keep entirely in memory, with support for file-based storage and
    retrieval of segments.
    """
    
    def __init__(self, name, initial_value=None, parent_id=None, file_storage=False):
        """
        Initialize a signal variable.
        
        Args:
            name: Name of the variable
            initial_value: Initial value for the variable
            parent_id: ID of the parent component (e.g., dock widget)
            file_storage: Whether to use file-based storage for large data
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.parent_id = parent_id  # Store the parent dock/widget ID
        self.value = initial_value
        self._subscribers = {}  # Dictionary of callback functions keyed by subscriber ID
        self._file_storage = file_storage
        self._file_path = None
        
        # Store data to file if needed
        if file_storage and initial_value is not None:
            self._store_data_to_file(initial_value)
    
    def subscribe(self, subscriber_id, callback):
        """
        Register a subscriber to be notified of value changes.
        
        Args:
            subscriber_id: Unique ID for the subscriber
            callback: Function to call when value changes
            
        Returns:
            The subscriber ID for use in unsubscribe
        """
        self._subscribers[subscriber_id] = callback
        
        # Immediately notify with current value
        if self._file_storage and self._file_path and isinstance(self.value, dict) and 'data_ref' in self.value:
            # For file-based storage, just notify with metadata
            callback(self.value)
        else:
            # For in-memory storage, notify with actual value
            callback(self.value)
        
        return subscriber_id
    
    def unsubscribe(self, subscriber_id):
        """
        Remove a subscriber.
        
        Args:
            subscriber_id: ID of the subscriber to remove
            
        Returns:
            True if subscriber was removed, False otherwise
        """
        if subscriber_id in self._subscribers:
            del self._subscribers[subscriber_id]
            return True
        return False
    
    def clear_subscribers(self):
        """Remove all subscribers."""
        self._subscribers.clear()
    
    def set_value(self, new_value, create_command=True):
        """
        Set the variable's value and notify subscribers.
        
        Args:
            new_value: New value for the variable
            create_command: Whether to create a command for undo/redo
            
        Returns:
            True if value was changed, False otherwise
        """
        # Skip if value hasn't changed
        if self.value == new_value:
            return False
        
        old_value = self.value
        
        # Handle file storage if needed
        if self._file_storage and new_value is not None:
            self._store_data_to_file(new_value)
        
        # Update value
        self.value = new_value
        
        # Create command if requested
        if create_command:
            from .command_manager import CommandManager
            cmd = SignalVariableChangeCommand(self, old_value, new_value)
            CommandManager.instance().execute_command(cmd)
        
        # Notify subscribers
        self._notify_subscribers()
        return True
    
    def _notify_subscribers(self):
        """Notify all subscribers of the current value."""
        for callback in self._subscribers.values():
            if self._file_storage and self._file_path and isinstance(self.value, dict) and 'data_ref' in self.value:
                # For file-based storage, just notify with metadata
                callback(self.value)
            else:
                # For in-memory storage, notify with actual value
                callback(self.value)
    
    def _store_data_to_file(self, data):
        """
        Store large data to a file.
        
        Args:
            data: The data to store
            
        Returns:
            A reference object with metadata and file path
        """
        # Ensure project directory exists
        from .command_manager import CommandManager
        project = CommandManager.instance().get_active_project()
        
        if project is None:
            # Can't store to file without a project
            self._file_storage = False
            return
            
        # Create directory structure if needed
        project_dir = getattr(project, 'directory', None)
        if project_dir is None:
            # Try to get from project file path
            project_file = getattr(project, 'file_path', None)
            if project_file:
                project_dir = os.path.dirname(project_file)
            else:
                # Use temporary directory
                import tempfile
                project_dir = tempfile.gettempdir()
        
        signal_dir = os.path.join(project_dir, 'signals')
        os.makedirs(signal_dir, exist_ok=True)
        
        # Create data file if it doesn't exist
        self._file_path = os.path.join(signal_dir, f"{self.id}.h5")
        
        # Convert data to the right format if needed
        if isinstance(data, dict) and 'data' in data:
            # Extract data from dictionary
            signal_data = data['data']
            metadata = {k: v for k, v in data.items() if k != 'data'}
        else:
            # Assume data is the signal itself
            signal_data = data
            metadata = {}
        
        # Store data to HDF5 file
        try:
            with h5py.File(self._file_path, 'w') as f:
                # Store signal data
                if isinstance(signal_data, np.ndarray):
                    f.create_dataset('data', data=signal_data, compression='gzip', compression_opts=9)
                elif isinstance(signal_data, list):
                    f.create_dataset('data', data=np.array(signal_data), compression='gzip', compression_opts=9)
                
                # Store metadata as attributes
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        f.attrs[key] = value
                
                # Store timestamp
                import time
                f.attrs['timestamp'] = time.time()
            
            # Update value with reference
            if isinstance(data, dict):
                # Keep existing dictionary, but replace data with reference
                self.value = data.copy()
                self.value['data_ref'] = self._file_path
                if 'data' in self.value:
                    del self.value['data']
            else:
                # Create new reference object
                self.value = {
                    'data_ref': self._file_path,
                    'timestamp': time.time()
                }
            
            return self.value
        except Exception as e:
            print(f"Error storing data to file: {e}")
            self._file_storage = False
            self.value = data
            return data
    
    def get_data_segment(self, start=0, length=None):
        """
        Get a segment of data from file storage.
        
        Args:
            start: Starting index
            length: Number of samples to retrieve (None for all)
            
        Returns:
            The data segment
        """
        if not self._file_storage or not self._file_path:
            # For in-memory storage, just return a segment of the value
            if isinstance(self.value, dict) and 'data' in self.value:
                data = self.value['data']
                if isinstance(data, (list, np.ndarray)):
                    if length is None:
                        return data[start:]
                    else:
                        return data[start:start+length]
            return self.value
        
        try:
            with h5py.File(self._file_path, 'r') as f:
                if 'data' in f:
                    if length is None:
                        return f['data'][start:]
                    else:
                        return f['data'][start:start+length]
                return None
        except Exception as e:
            print(f"Error reading data from file: {e}")
            return None
    
    def get_full_data(self):
        """
        Get the full data from file storage.
        
        Warning: This may use a lot of memory for large datasets.
        
        Returns:
            The complete data
        """
        return self.get_data_segment(0)
    
    def get_metadata(self):
        """
        Get metadata for the signal.
        
        Returns:
            Dictionary of metadata
        """
        if not self._file_storage or not self._file_path:
            if isinstance(self.value, dict):
                # Return a copy without the 'data' field
                metadata = self.value.copy()
                if 'data' in metadata:
                    del metadata['data']
                return metadata
            return {}
        
        try:
            with h5py.File(self._file_path, 'r') as f:
                return dict(f.attrs)
        except Exception as e:
            print(f"Error reading metadata from file: {e}")
            return {}
    
    def get_data_properties(self):
        """
        Get properties of the stored data (size, type, etc.)
        
        Returns:
            Dictionary of properties
        """
        if not self._file_storage or not self._file_path:
            if isinstance(self.value, dict) and 'data' in self.value:
                data = self.value['data']
                if isinstance(data, np.ndarray):
                    return {
                        'size': data.size,
                        'shape': data.shape,
                        'dtype': str(data.dtype),
                        'min': float(np.min(data)) if data.size > 0 else None,
                        'max': float(np.max(data)) if data.size > 0 else None,
                        'storage': 'memory'
                    }
                elif isinstance(data, list):
                    return {
                        'size': len(data),
                        'shape': (len(data),),
                        'dtype': type(data[0]).__name__ if data else None,
                        'storage': 'memory'
                    }
            return {'storage': 'memory'}
        
        try:
            with h5py.File(self._file_path, 'r') as f:
                if 'data' in f:
                    dataset = f['data']
                    return {
                        'size': dataset.size,
                        'shape': dataset.shape,
                        'dtype': str(dataset.dtype),
                        'min': float(np.min(dataset)) if dataset.size > 0 else None,
                        'max': float(np.max(dataset)) if dataset.size > 0 else None,
                        'compression': dataset.compression,
                        'compression_opts': dataset.compression_opts,
                        'storage': 'file',
                        'file_path': self._file_path
                    }
                return {'storage': 'file', 'file_path': self._file_path}
        except Exception as e:
            print(f"Error reading data properties from file: {e}")
            return {'storage': 'unknown'}
    
    def set_metadata(self, key, value):
        """
        Set metadata for the signal.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            True if metadata was updated, False otherwise
        """
        if not self._file_storage or not self._file_path:
            if not isinstance(self.value, dict):
                self.value = {'data': self.value}
            self.value[key] = value
            self._notify_subscribers()
            return True
        
        try:
            with h5py.File(self._file_path, 'r+') as f:
                if isinstance(value, (str, int, float, bool)):
                    f.attrs[key] = value
                    
                    # Update in-memory value too
                    if isinstance(self.value, dict):
                        self.value[key] = value
                    
                    self._notify_subscribers()
                    return True
            return False
        except Exception as e:
            print(f"Error setting metadata in file: {e}")
            return False
    
    def serialize(self):
        """
        Serialize the signal variable for storage.
        
        Returns:
            Dictionary with serialized state
        """
        result = {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'file_storage': self._file_storage,
            'file_path': self._file_path,
        }
        
        # Handle value serialization
        if self._file_storage and self._file_path:
            # For file-based storage, just store metadata and reference
            if isinstance(self.value, dict):
                result['value'] = {k: v for k, v in self.value.items() if k != 'data'}
            else:
                result['value'] = {'data_ref': self._file_path}
        else:
            # For in-memory storage, we need to handle different types
            if isinstance(self.value, np.ndarray):
                # Convert numpy array to list for JSON serialization
                result['value'] = {
                    'data': self.value.tolist(),
                    'dtype': str(self.value.dtype),
                    'shape': self.value.shape
                }
            elif isinstance(self.value, dict) and 'data' in self.value and isinstance(self.value['data'], np.ndarray):
                # Handle dictionary with numpy array data
                value_copy = self.value.copy()
                value_copy['data'] = self.value['data'].tolist()
                value_copy['dtype'] = str(self.value['data'].dtype)
                value_copy['shape'] = self.value['data'].shape
                result['value'] = value_copy
            else:
                # For other types, store directly if JSON serializable
                try:
                    json.dumps(self.value)
                    result['value'] = self.value
                except (TypeError, OverflowError):
                    # If not JSON serializable, store metadata only
                    result['value'] = {'type': str(type(self.value))}
        
        return result
    
    @classmethod
    def deserialize(cls, state, base_dir=None):
        """
        Create a signal variable from serialized state.
        
        Args:
            state: Serialized state
            base_dir: Base directory for resolving relative file paths
            
        Returns:
            New SignalVariable instance
        """
        variable = cls(
            state.get('name', ''),
            None,  # Initial value will be set later
            state.get('parent_id')
        )
        
        variable.id = state.get('id', str(uuid.uuid4()))
        variable._file_storage = state.get('file_storage', False)
        
        # Handle file path
        file_path = state.get('file_path')
        if file_path and variable._file_storage:
            if not os.path.isabs(file_path) and base_dir:
                file_path = os.path.join(base_dir, file_path)
            
            if os.path.exists(file_path):
                variable._file_path = file_path
            else:
                # File doesn't exist, fall back to in-memory
                variable._file_storage = False
                variable._file_path = None
        
        # Handle value restoration
        value = state.get('value')
        if variable._file_storage and variable._file_path:
            # For file-based storage, set reference value
            if isinstance(value, dict):
                value['data_ref'] = variable._file_path
            else:
                value = {'data_ref': variable._file_path}
        elif isinstance(value, dict) and 'dtype' in value and 'data' in value:
            # Restore numpy array
            try:
                dtype = np.dtype(value['dtype'])
                if 'shape' in value:
                    # Reshape to original shape
                    arr = np.array(value['data'], dtype=dtype).reshape(value['shape'])
                else:
                    arr = np.array(value['data'], dtype=dtype)
                
                if 'data' in value:
                    # If it was a dictionary with data, restore that structure
                    value_copy = value.copy()
                    value_copy['data'] = arr
                    value = value_copy
                else:
                    # Otherwise, just use the array directly
                    value = arr
            except Exception as e:
                print(f"Error restoring numpy array: {e}")
        
        variable.value = value
        return variable


class SignalVariableChangeCommand(Command):
    """
    Command for changing signal variable values.
    
    This command encapsulates changes to signal variables so they can be
    undone/redone.
    """
    
    def __init__(self, signal_variable, old_value, new_value):
        """
        Initialize the command.
        
        Args:
            signal_variable: The signal variable to change
            old_value: Previous value
            new_value: New value
        """
        super().__init__()
        self.signal_variable = signal_variable
        self.variable_id = signal_variable.id
        self.old_value = old_value
        self.new_value = new_value
    
    def execute(self):
        """Execute the command by setting the new value."""
        if self.signal_variable:
            # Set value without creating another command
            self.signal_variable.set_value(self.new_value, create_command=False)
    
    def undo(self):
        """Undo the command by restoring the old value."""
        if self.signal_variable:
            # Set value without creating another command
            self.signal_variable.set_value(self.old_value, create_command=False)
    
    def get_state(self):
        """
        Get serializable state for this command.
        
        Returns:
            Dictionary with command state
        """
        return {
            'variable_id': self.variable_id,
            'old_value': self._serialize_value(self.old_value),
            'new_value': self._serialize_value(self.new_value)
        }
    
    @classmethod
    def from_state(cls, state):
        """
        Create a command from serialized state.
        
        Args:
            state: Serialized state
            
        Returns:
            New command instance
        """
        from .command_manager import CommandManager
        registry = CommandManager.instance().get_variable_registry()
        
        # Get the variable by ID
        variable_id = state.get('variable_id')
        variable = registry.get_variable(variable_id) if registry else None
        
        if variable:
            cmd = cls(
                variable,
                cls._deserialize_value(state.get('old_value')),
                cls._deserialize_value(state.get('new_value'))
            )
            return cmd
        return None
    
    def _serialize_value(self, value):
        """
        Serialize a value for storage.
        
        Args:
            value: Value to serialize
            
        Returns:
            Serializable representation
        """
        # If file-based, just store reference
        if (self.signal_variable._file_storage and 
            isinstance(value, dict) and 
            'data_ref' in value):
            return {'data_ref': value['data_ref']}
        
        # Handle numpy arrays
        if isinstance(value, np.ndarray):
            return {
                'data': value.tolist(),
                'dtype': str(value.dtype),
                'shape': value.shape
            }
        
        # Handle dictionary with numpy array
        if isinstance(value, dict) and 'data' in value and isinstance(value['data'], np.ndarray):
            value_copy = value.copy()
            value_copy['data'] = value['data'].tolist()
            value_copy['dtype'] = str(value['data'].dtype)
            value_copy['shape'] = value['data'].shape
            return value_copy
        
        # For other types, try direct serialization
        try:
            json.dumps(value)
            return value
        except (TypeError, OverflowError):
            # Not JSON serializable
            return {'type': str(type(value))}
    
    @classmethod
    def _deserialize_value(cls, value):
        """
        Deserialize a value from storage.
        
        Args:
            value: Serialized value
            
        Returns:
            Deserialized value
        """
        # Handle file reference
        if isinstance(value, dict) and 'data_ref' in value:
            return value
        
        # Handle numpy arrays
        if isinstance(value, dict) and 'dtype' in value and 'data' in value:
            try:
                dtype = np.dtype(value['dtype'])
                if 'shape' in value:
                    arr = np.array(value['data'], dtype=dtype).reshape(value['shape'])
                else:
                    arr = np.array(value['data'], dtype=dtype)
                
                if len(value) > 3:  # If it has more keys than data, dtype, shape
                    # It was a dictionary with numpy array
                    value_copy = value.copy()
                    value_copy['data'] = arr
                    return value_copy
                else:
                    # It was just a numpy array
                    return arr
            except Exception as e:
                print(f"Error deserializing numpy array: {e}")
                return value
        
        return value


# Register the command with the command factory
from .command import CommandFactory
CommandFactory.register(SignalVariableChangeCommand)


# Helper functions

def create_signal_variable(name, data=None, parent_id=None, file_storage=True):
    """
    Create a signal variable and register it with the variable registry.
    
    Args:
        name: Name of the variable
        data: Initial data (optional)
        parent_id: ID of the parent component (optional)
        file_storage: Whether to use file-based storage
        
    Returns:
        The created signal variable
    """
    from .command_manager import CommandManager
    registry = CommandManager.instance().get_variable_registry()
    
    variable = SignalVariable(name, data, parent_id, file_storage)
    registry.register_variable(variable)
    
    return variable


def register_signal_file(file_path, name=None, parent_id=None):
    """
    Register an existing signal file with the system.
    
    Args:
        file_path: Path to the signal file
        name: Name for the variable (optional, defaults to filename)
        parent_id: ID of the parent component (optional)
        
    Returns:
        The created signal variable or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        return None
    
    if name is None:
        name = os.path.basename(file_path)
    
    variable = SignalVariable(name, {'data_ref': file_path}, parent_id, True)
    variable._file_path = file_path
    
    from .command_manager import CommandManager
    registry = CommandManager.instance().get_variable_registry()
    registry.register_variable(variable)
    
    return variable