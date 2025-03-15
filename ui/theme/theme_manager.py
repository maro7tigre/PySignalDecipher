from typing import Dict, Any, Optional, List
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication


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
        
        # Store references to managers
        self._color_manager = color_manager
        self._style_manager = style_manager
        self._preferences_manager = preferences_manager
        
        # Connect signals
        self._color_manager.color_scheme_changed.connect(self._on_color_scheme_changed)
        
    def _on_color_scheme_changed(self, scheme_name: str) -> None:
        """
        Handle color scheme changes.
        
        Args:
            scheme_name: Name of the new color scheme
        """
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
        return self._color_manager.set_active_scheme(theme_name)
        
    def apply_theme(self) -> None:
        """
        Apply the current theme to the application.
        
        This should be called after initializing the theme system.
        """
        self._style_manager.apply_application_style()
        
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