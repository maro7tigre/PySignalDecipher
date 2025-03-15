import os
import json
from typing import Dict, List, Optional, Any, Callable
from PySide6.QtCore import QObject, Signal, QSettings


class ColorManager(QObject):
    """
    Manages color schemes and provides color values for the application.
    
    Responsible for loading color definitions from JSON files, providing
    a simple API to access colors by name/role, and notifying when the
    active color scheme changes.
    """
    
    # Signal emitted when the color scheme changes
    color_scheme_changed = Signal(str)
    
    def __init__(self):
        """Initialize the ColorManager with settings from previous sessions."""
        super().__init__()
        
        # Path to color definition files
        self._colors_dir = os.path.join("assets", "themes", "colors")
        
        # Dictionary to store loaded color schemes
        self._color_schemes = {}
        
        # Create settings object for persistence
        self._settings = QSettings("PySignalDecipher", "PySignalDecipher")
        
        # Dictionary to store registered observers
        self._observers = {}
        
        # Load available color schemes
        self._load_available_schemes()
        
        # Load the last active scheme from settings, with "dark" as the default
        self._active_scheme = self._settings.value("theme/active_scheme", "dark")
        
    def _load_available_schemes(self) -> None:
        """
        Load all available color schemes from the colors directory.
        
        Reads all JSON files in the colors directory and loads them as color schemes.
        """
        if not os.path.exists(self._colors_dir):
            # Log a warning that the colors directory doesn't exist
            print(f"Warning: Colors directory not found: {self._colors_dir}")
            return
            
        for filename in os.listdir(self._colors_dir):
            if filename.endswith("_colors.json"):
                scheme_name = filename.replace("_colors.json", "")
                self._load_color_scheme(scheme_name)
                
    def _load_color_scheme(self, scheme_name: str) -> bool:
        """
        Load a color scheme from its JSON file.
        
        Args:
            scheme_name: Name of the color scheme to load (without _colors.json)
            
        Returns:
            bool: True if the color scheme was loaded successfully, False otherwise
        """
        file_path = os.path.join(self._colors_dir, f"{scheme_name}_colors.json")
        
        if not os.path.exists(file_path):
            # Log a warning that the color scheme file doesn't exist
            print(f"Warning: Color scheme file not found: {file_path}")
            return False
            
        try:
            with open(file_path, 'r') as f:
                self._color_schemes[scheme_name] = json.load(f)
            return True
        except json.JSONDecodeError:
            # Log an error that the color scheme file is invalid JSON
            print(f"Error: Invalid JSON in color scheme file: {file_path}")
            return False
            
    def get_available_schemes(self) -> List[str]:
        """
        Get a list of available color schemes.
        
        Returns:
            List of color scheme names
        """
        return list(self._color_schemes.keys())
        
    def get_active_scheme(self) -> str:
        """
        Get the name of the currently active color scheme.
        
        Returns:
            Name of the active color scheme
        """
        return self._active_scheme
        
    def set_active_scheme(self, scheme_name: str) -> bool:
        """
        Set the active color scheme.
        
        Args:
            scheme_name: Name of the color scheme to activate
            
        Returns:
            bool: True if the color scheme was activated successfully, False otherwise
        """
        if scheme_name not in self._color_schemes:
            if not self._load_color_scheme(scheme_name):
                # Log an error that the color scheme is not available
                print(f"Error: Color scheme not available: {scheme_name}")
                return False
                
        # Only emit signal if the scheme actually changed
        if self._active_scheme != scheme_name:
            self._active_scheme = scheme_name
            
            # Save the active scheme in settings
            self._settings.setValue("theme/active_scheme", scheme_name)
            
            self.color_scheme_changed.emit(scheme_name)
            
        return True
        
    def get_color(self, color_path: str, default: str = "#000000") -> str:
        """
        Get a color value by its path in the color scheme.
        
        Args:
            color_path: Dot-separated path to the color (e.g., "background.primary")
            default: Default color to return if the color is not found
            
        Returns:
            The color value as a string (e.g., "#1E1E1E")
        """
        if self._active_scheme not in self._color_schemes:
            return default
            
        # Navigate the nested dictionary using the dot-separated path
        color_dict = self._color_schemes[self._active_scheme]
        path_parts = color_path.split('.')
        
        for part in path_parts:
            if not isinstance(color_dict, dict) or part not in color_dict:
                return default
            color_dict = color_dict[part]
            
        if not isinstance(color_dict, str):
            return default
            
        return color_dict
        
    def register_observer(self, observer_id: str, callback: Callable[[str], None]) -> None:
        """
        Register an observer to be notified when the color scheme changes.
        
        Args:
            observer_id: Unique identifier for the observer
            callback: Function to call when the color scheme changes
        """
        self._observers[observer_id] = callback
        self.color_scheme_changed.connect(callback)
        
    def unregister_observer(self, observer_id: str) -> None:
        """
        Unregister an observer.
        
        Args:
            observer_id: Identifier of the observer to unregister
        """
        if observer_id in self._observers:
            self.color_scheme_changed.disconnect(self._observers[observer_id])
            del self._observers[observer_id]
            
    def save_custom_scheme(self, scheme_name: str, colors: Dict[str, Any]) -> bool:
        """
        Save a custom color scheme.
        
        Args:
            scheme_name: Name for the custom scheme
            colors: Dictionary of colors to save
            
        Returns:
            bool: True if the scheme was saved successfully, False otherwise
        """
        if not scheme_name.endswith("_custom"):
            scheme_name = f"{scheme_name}_custom"
            
        file_path = os.path.join(self._colors_dir, f"{scheme_name}_colors.json")
        
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(colors, f, indent=4)
                
            # Add the scheme to the loaded schemes
            self._color_schemes[scheme_name] = colors
            
            return True
        except (IOError, OSError) as e:
            # Log an error that the color scheme could not be saved
            print(f"Error: Could not save color scheme: {e}")
            return False