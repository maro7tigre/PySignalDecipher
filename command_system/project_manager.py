"""
Project manager for handling save and load operations.
"""
import os
from typing import Optional, Dict, Any, Type, Callable

from .observable import Observable
from .command_manager import get_command_manager, CommandManager
from .serialization import ProjectSerializer


class ProjectManager:
    """
    Manages project save and load operations.
    """
    _instance = None
    
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
        self._default_format = ProjectSerializer.DEFAULT_FORMAT
    
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
        if format_type in [ProjectSerializer.FORMAT_JSON, 
                          ProjectSerializer.FORMAT_BINARY, 
                          ProjectSerializer.FORMAT_XML, 
                          ProjectSerializer.FORMAT_YAML]:
            self._default_format = format_type
        else:
            print(f"Unsupported format type: {format_type}")
            
    def get_default_format(self) -> str:
        """Get the current default format."""
        return self._default_format
    
    def get_default_extension(self) -> str:
        """Get the default file extension for the current format."""
        return ProjectSerializer.get_default_extension(self._default_format)
    
    def save_project(self, model: Observable, filename: Optional[str] = None, format_type: Optional[str] = None) -> bool:
        """
        Save the project to a file.
        
        Args:
            model: Observable model to save
            filename: Optional filename to save to (uses current filename if not provided)
            format_type: Optional format type (uses default if not provided)
            
        Returns:
            True if save was successful
        """
        # Use current filename if not provided
        if filename is None:
            if self._current_filename is None:
                return False
            filename = self._current_filename
        else:
            # Update current filename
            self._current_filename = filename
            
        # Use default format if not provided
        format_type = format_type or self._default_format
            
        # Save the model
        success = ProjectSerializer.save_to_file(model, filename, format_type)
        
        # Clear command history after successful save
        if success:
            self._command_manager.clear()
            
        return success
    
    def load_project(self, filename: str, format_type: Optional[str] = None) -> Optional[Observable]:
        """
        Load a project from a file.
        
        Args:
            filename: Path to the file to load
            format_type: Optional format type (will try to deduce from extension if not provided)
            
        Returns:
            Loaded model, or None if loading failed
        """
        # Load the model
        model = ProjectSerializer.load_from_file(filename, format_type)
        
        if model is not None:
            # Update current filename
            self._current_filename = filename
            
            # Clear command history since we're loading a fresh state
            self._command_manager.clear()
        
        return model
    
    def get_current_filename(self) -> Optional[str]:
        """Get the current project filename."""
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
    """Get the singleton project manager instance."""
    return ProjectManager.get_instance()