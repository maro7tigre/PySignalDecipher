import os
from typing import Dict, Any, Optional, List
from PySide6.QtCore import QObject, Signal, QFile, QTextStream
from PySide6.QtWidgets import QApplication
from command_system.command_manager import CommandManager


class ThemeManager(QObject):
    """
    Coordinates color and style management for the application theme system.
    
    Acts as a facade for the ColorManager and StyleManager, providing a simplified
    interface for theme management across the application.
    """
    
    # Signal emitted when the theme changes
    theme_changed = Signal(str)
    
    def __init__(self, color_manager, style_manager, preferences_manager):
        """
        Initialize the ThemeManager.
        
        Args:
            color_manager: Reference to the ColorManager
            style_manager: Reference to the StyleManager
            preferences_manager: Reference to the PreferencesManager
        """
        super().__init__()
        
        # Get command manager for accessing services if needed
        self._command_manager = CommandManager.instance()
        
        # Store references to managers
        self._color_manager = color_manager
        self._style_manager = style_manager
        self._preferences_manager = preferences_manager
        
        # QSS styles directory
        self._qss_dir = os.path.join("assets", "themes", "qss")
        
        # Dictionary to store loaded QSS styles
        self._qss_styles = {}
        
        # Connect signals
        self._color_manager.color_scheme_changed.connect(self._on_color_scheme_changed)
        
        # Ensure QSS directory exists
        if not os.path.exists(self._qss_dir):
            os.makedirs(self._qss_dir, exist_ok=True)
            
    def _on_color_scheme_changed(self, scheme_name: str) -> None:
        """
        Handle color scheme changes.
        
        Args:
            scheme_name: Name of the new color scheme
        """
        # Apply the styles
        self.apply_theme()
        
        # Save theme preference
        self.save_theme_preferences()
        
        # Forward the signal
        self.theme_changed.emit(scheme_name)
        
    def get_available_themes(self) -> List[str]:
        """
        Get a list of available themes.
        
        Returns:
            List of theme names
        """
        return self._color_manager.get_available_schemes()
        
    def get_active_theme(self) -> str:
        """
        Get the name of the currently active theme.
        
        Returns:
            Name of the active theme
        """
        return self._color_manager.get_active_scheme()
        
    def set_theme(self, theme_name: str) -> bool:
        """
        Set the active theme.
        
        This changes both color scheme and styles.
        
        Args:
            theme_name: Name of the theme to activate
            
        Returns:
            bool: True if the theme was activated successfully, False otherwise
        """
        success = self._color_manager.set_active_scheme(theme_name)
        if success:
            # This will trigger _on_color_scheme_changed through the signal connection
            # Apply the theme explicitly to ensure it's applied
            self.apply_theme()
        return success
        
    def apply_theme(self) -> None:
        """
        Apply the current theme to the application.
        
        This should be called after initializing the theme system.
        """
        active_theme = self.get_active_theme()
        
        # First try to apply QSS if available
        if self.apply_qss_theme(active_theme):
            # QSS theme applied successfully
            pass
        else:
            # Fall back to StyleManager for style generation
            self._style_manager.apply_application_style()
            
    def load_qss_theme(self, theme_name: str) -> str:
        """
        Load a QSS theme file.
        
        Args:
            theme_name: Name of the theme to load
            
        Returns:
            str: QSS content or empty string if not found
        """
        # Check if already loaded
        if theme_name in self._qss_styles:
            return self._qss_styles[theme_name]
            
        # Try to load from file
        file_path = os.path.join(self._qss_dir, f"{theme_name}_theme.qss")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    qss_content = f.read()
                    self._qss_styles[theme_name] = qss_content
                    return qss_content
            except IOError:
                # Log error
                print(f"Error: Could not load QSS file: {file_path}")
                
        return ""
        
    def apply_qss_theme(self, theme_name: str) -> bool:
        """
        Apply a QSS theme.
        
        Args:
            theme_name: Name of the theme to apply
            
        Returns:
            bool: True if the QSS theme was applied, False otherwise
        """
        qss_content = self.load_qss_theme(theme_name)
        if qss_content:
            # Apply QSS to application
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss_content)
                return True
        return False
        
    def get_color(self, color_path: str, default: str = "#000000") -> str:
        """
        Get a color value by its path in the color scheme.
        
        Args:
            color_path: Dot-separated path to the color (e.g., "background.primary")
            default: Default color to return if the color is not found
            
        Returns:
            The color value as a string (e.g., "#1E1E1E")
        """
        return self._color_manager.get_color(color_path, default)
        
    def save_theme_preferences(self) -> None:
        """
        Save theme-related preferences.
        
        This is automatically called when setting a new theme.
        """
        theme = self.get_active_theme()
        self._preferences_manager.set_preference("theme/active_theme", theme)
        
    def load_theme_preferences(self) -> None:
        """
        Load theme-related preferences.
        
        This is automatically called during initialization.
        """
        theme = self._preferences_manager.get_preference("theme/active_theme")
        if theme and theme in self.get_available_themes():
            self.set_theme(theme)