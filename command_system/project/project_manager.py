"""
Project manager for handling save and load operations.

This module provides project management functionality, separating
project operations from serialization details.
"""
import os
from typing import Optional, Dict, Any, Callable, List, Type

from ..core.observable import Observable
from ..core.command_manager import get_command_manager


class ProjectManager:
    """
    Manages project save and load operations.
    """
    _instance = None
    
    # Default serialization formats
    FORMAT_JSON = "json"
    FORMAT_BINARY = "bin"
    FORMAT_XML = "xml"
    FORMAT_YAML = "yaml"
    DEFAULT_FORMAT = FORMAT_JSON
    
    # File extensions for formats
    _format_extensions = {
        FORMAT_JSON: ".json",
        FORMAT_BINARY: ".bin",
        FORMAT_XML: ".xml",
        FORMAT_YAML: ".yaml"
    }
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = ProjectManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the project manager."""
        if ProjectManager._instance is not None:
            raise RuntimeError("Use ProjectManager.get_instance() to get the singleton instance")
            
        ProjectManager._instance = self
        self._command_manager = get_command_manager()
        self._current_filename: Optional[str] = None
        self._model_factory: Dict[str, Callable[[], Observable]] = {}
        
        # Default project format
        self._default_format = self.DEFAULT_FORMAT
        
        # Default flag to save layouts with projects
        self._save_layouts = True
        
        # Layout handler functions - will be set by layout system if available
        self._save_layout_func = None
        self._load_layout_func = None
        
        # Project event callbacks
        self._before_save_callbacks: Dict[str, Callable[[Observable, str], None]] = {}
        self._after_save_callbacks: Dict[str, Callable[[Observable, str, bool], None]] = {}
        self._before_load_callbacks: Dict[str, Callable[[str], None]] = {}
        self._after_load_callbacks: Dict[str, Callable[[Observable, str, bool], None]] = {}
    
    def register_model_type(self, model_type: str, factory: Callable[[], Observable]) -> None:
        """
        Register a model factory function for creating instances of a specific model type.
        
        Args:
            model_type: String identifier for the model type
            factory: Function that creates and returns a new instance of the model
        """
        self._model_factory[model_type] = factory
    
    def set_default_format(self, format_type: str) -> None:
        """
        Set the default serialization format for projects.
        
        Args:
            format_type: Format to use (json, bin, xml, yaml)
        """
        if format_type in self._format_extensions:
            self._default_format = format_type
        else:
            print(f"Unsupported format type: {format_type}")
            
    def get_default_format(self) -> str:
        """
        Get the current default format.
        
        Returns:
            Default format identifier
        """
        return self._default_format
    
    def get_default_extension(self) -> str:
        """
        Get the default file extension for the current format.
        
        Returns:
            File extension including dot (e.g., ".json")
        """
        return self._format_extensions.get(self._default_format, ".json")
    
    def register_layout_handlers(self, save_func: Callable, load_func: Callable) -> None:
        """
        Register handlers for saving and loading layouts.
        
        Args:
            save_func: Function for saving layouts, takes (filename) as argument
            load_func: Function for loading layouts, takes (filename) as argument
        """
        self._save_layout_func = save_func
        self._load_layout_func = load_func
    
    def set_save_layouts(self, save_layouts: bool) -> None:
        """
        Set whether layouts should be saved with projects by default.
        
        Args:
            save_layouts: True to save layouts with projects, False to disable
        """
        self._save_layouts = save_layouts
        
    def add_before_save_callback(self, callback_id: str, 
                              callback: Callable[[Observable, str], None]) -> None:
        """
        Add a callback to be called before a project is saved.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call before project save, receives model and filename
        """
        self._before_save_callbacks[callback_id] = callback
        
    def add_after_save_callback(self, callback_id: str, 
                             callback: Callable[[Observable, str, bool], None]) -> None:
        """
        Add a callback to be called after a project is saved.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call after project save,
                      receives model, filename, and success flag
        """
        self._after_save_callbacks[callback_id] = callback
        
    def add_before_load_callback(self, callback_id: str, 
                              callback: Callable[[str], None]) -> None:
        """
        Add a callback to be called before a project is loaded.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call before project load, receives filename
        """
        self._before_load_callbacks[callback_id] = callback
        
    def add_after_load_callback(self, callback_id: str, 
                             callback: Callable[[Observable, str, bool], None]) -> None:
        """
        Add a callback to be called after a project is loaded.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call after project load,
                      receives model, filename, and success flag
        """
        self._after_load_callbacks[callback_id] = callback
        
    def remove_callback(self, callback_id: str) -> None:
        """
        Remove a callback by ID.
        
        Args:
            callback_id: ID of the callback to remove
        """
        if callback_id in self._before_save_callbacks:
            del self._before_save_callbacks[callback_id]
        if callback_id in self._after_save_callbacks:
            del self._after_save_callbacks[callback_id]
        if callback_id in self._before_load_callbacks:
            del self._before_load_callbacks[callback_id]
        if callback_id in self._after_load_callbacks:
            del self._after_load_callbacks[callback_id]
    
    def save_project(self, model: Observable, filename: Optional[str] = None, 
                    format_type: Optional[str] = None, save_layout: Optional[bool] = None) -> bool:
        """
        Save project to file.
        
        Args:
            model: Observable model to save
            filename: Path to save to (uses current filename if None)
            format_type: Serialization format (uses default if None)
            save_layout: Whether to save layout with project (uses default if None)
            
        Returns:
            True if saved successfully
        """
        # Resolve filename and format
        if not filename:
            filename = self._current_filename
            if not filename:
                return False
                
        if not format_type:
            format_type = self._default_format
            
        if save_layout is None:
            save_layout = self._save_layouts
            
        # Call before save callbacks
        for callback in self._before_save_callbacks.values():
            callback(model, filename)
            
        try:
            # TODO: Replace project serialization implementation
            # 1. Delegate to SerializationManager for model serialization
            # 2. Use registered serializers for model objects
            # 3. Support different serialization formats
            
            # Save layout if enabled
            layout_success = True
            if save_layout and self._save_layout_func:
                layout_success = self._save_layout_func(filename)
                
            # Update current filename
            self._current_filename = filename
            
            # Call after save callbacks
            success = True  # Set this based on actual serialization result
            for callback in self._after_save_callbacks.values():
                callback(model, filename, success)
                
            return success and layout_success
        except Exception as e:
            print(f"Error saving project: {e}")
            
            # Call after save callbacks with failure
            for callback in self._after_save_callbacks.values():
                callback(model, filename, False)
                
            return False

    def load_project(self, filename: str, format_type: Optional[str] = None,
                    load_layout: Optional[bool] = None) -> Optional[Observable]:
        """
        Load project from file.
        
        Args:
            filename: Path to load from
            format_type: Serialization format (auto-detect if None)
            load_layout: Whether to load layout with project (uses default if None)
            
        Returns:
            Loaded model, or None if loading failed
        """
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return None
            
        if not format_type:
            # Auto-detect format from extension
            ext = os.path.splitext(filename)[1].lower()
            for fmt, fmt_ext in self._format_extensions.items():
                if ext == fmt_ext:
                    format_type = fmt
                    break
            
            if not format_type:
                format_type = self._default_format
                
        if load_layout is None:
            load_layout = self._save_layouts
            
        # Call before load callbacks
        for callback in self._before_load_callbacks.values():
            callback(filename)
            
        try:
            # TODO: Replace project deserialization implementation
            # 1. Delegate to SerializationManager for model deserialization
            # 2. Use registered factories for object creation
            # 3. Support different serialization formats
            
            # Placeholder until implementation
            model = None
            
            if model:
                # Update current filename
                self._current_filename = filename
                
                # Clear command history
                self._command_manager.clear()
                
                # Load layout if enabled
                if load_layout and self._load_layout_func:
                    self._load_layout_func(filename)
                    
                # Call after load callbacks
                for callback in self._after_load_callbacks.values():
                    callback(model, filename, True)
                    
            return model
        except Exception as e:
            print(f"Error loading project: {e}")
            
            # Call after load callbacks with failure
            for callback in self._after_load_callbacks.values():
                callback(None, filename, False)
                
            return None
    
    def get_current_filename(self) -> Optional[str]:
        """
        Get the current project filename.
        
        Returns:
            Current filename or None if no file is open
        """
        return self._current_filename
    
    def new_project(self, model_type: str) -> Optional[Observable]:
        """
        Create a new project of the specified type.
        
        Args:
            model_type: Type of model to create
            
        Returns:
            New model instance, or None if factory not found
        """
        # Check if we have a factory for this model type
        if model_type not in self._model_factory:
            return None
            
        # Create a new model
        model = self._model_factory[model_type]()
        
        # Clear current filename
        self._current_filename = None
        
        # Clear command history
        self._command_manager.clear()
        
        return model


def get_project_manager():
    """
    Get the singleton project manager instance.
    
    Returns:
        ProjectManager singleton instance
    """
    return ProjectManager.get_instance()