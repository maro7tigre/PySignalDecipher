from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject


class BaseThemedWidget(QWidget):
    """
    Base class for all themed widgets with common theming functionality.
    
    Provides methods for applying and updating themes, and common widget functionality.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the base themed widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Theme manager reference (set by the apply_theme method)
        self._theme_manager = None
        
    def apply_theme(self, theme_manager):
        """
        Apply the current theme to this widget.
        
        Args:
            theme_manager: Reference to the ThemeManager
        """
        # Store the theme manager reference
        self._theme_manager = theme_manager
        
        # Apply the theme (to be implemented by subclasses)
        self._apply_theme_impl()
        
        # Connect to theme changes if not already connected
        if self._theme_manager and not hasattr(self, "_theme_connected"):
            self._theme_manager.theme_changed.connect(self._on_theme_changed)
            self._theme_connected = True
            
    def _apply_theme_impl(self):
        """
        Implementation of theme application.
        
        To be overridden by subclasses.
        """
        pass
        
    def _on_theme_changed(self, theme_name):
        """
        Handle theme changes.
        
        Args:
            theme_name: Name of the new theme
        """
        # Apply the new theme
        self._apply_theme_impl()
        
    def get_color(self, color_path, default="#000000"):
        """
        Get a color from the theme.
        
        Args:
            color_path: Dot-separated path to the color (e.g., "background.primary")
            default: Default color to return if the color is not found
            
        Returns:
            The color value as a string (e.g., "#1E1E1E")
        """
        if self._theme_manager:
            return self._theme_manager.get_color(color_path, default)
        return default