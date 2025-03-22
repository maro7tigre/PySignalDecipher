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
        
        # Default flag to save layouts with projects
        self._save_layouts = True
        
        # Layout handler functions - will be set by layout system if available
        self._save_layout_func = None
        self._load_layout_func = None
        self._structure_recreation_func = None
    
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
    
    def save_project(self, model: Observable, filename: Optional[str] = None, 
                    format_type: Optional[str] = None, save_layout: Optional[bool] = None) -> bool:
        """
        Save the project to a file.
        
        Args:
            model: Observable model to save
            filename: Optional filename to save to (uses current filename if not provided)
            format_type: Optional format type (uses default if not provided)
            save_layout: Optional flag to save layout (uses default setting if not provided)
            
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
        
        # Save layout if enabled and handlers are available
        if success and (save_layout if save_layout is not None else self._save_layouts):
            if self._save_layout_func:
                try:
                    self._save_layout_func(filename)
                except Exception as e:
                    print(f"Warning: Failed to save layout with project: {e}")
        
        # Clear command history after successful save
        if success:
            self._command_manager.clear()
            
        return success
    
    def load_project(self, filename: str, format_type: Optional[str] = None,
                    load_layout: Optional[bool] = None) -> Optional[Observable]:
        """Load a project from a file."""
        # Phase 1: Load the model
        model = ProjectSerializer.load_from_file(filename, format_type)
        
        if model is not None:
            # Update current filename
            self._current_filename = filename
            
            # Clear command history
            self._command_manager.clear()
            
            # Phase 2: Recreate application structure before loading layout
            if self._structure_recreation_func:
                try:
                    self._structure_recreation_func(model)
                except Exception as e:
                    print(f"Warning: Failed to recreate application structure: {e}")
            
            # Phase 3: Load layout if enabled
            if load_layout if load_layout is not None else self._save_layouts:
                if self._load_layout_func:
                    try:
                        self._load_layout_func(filename)
                    except Exception as e:
                        print(f"Warning: Failed to load layout from project: {e}")
        
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

    def register_structure_recreation_func(self, func):
        """
        Register a function to recreate application structure when loading projects.
        
        Args:
            func: Function that takes (model) and recreates necessary UI elements
        """
        self._structure_recreation_func = func


def get_project_manager():
    """Get the singleton project manager instance."""
    return ProjectManager.get_instance()