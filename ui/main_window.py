from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import QSize, Qt

from .theme import ThemeManager


class MainWindow(QMainWindow):
    """
    Main application window with support for theme and preferences.
    
    Handles window state restoration and theme application.
    """
    
    def __init__(self, theme_manager, preferences_manager):
        """
        Initialize the main window.
        
        Args:
            theme_manager: Reference to the ThemeManager
            preferences_manager: Reference to the PreferencesManager
        """
        super().__init__()
        
        # Store manager references
        self._theme_manager = theme_manager
        self._preferences_manager = preferences_manager
        
        # Set window properties
        self.setWindowTitle("PySignalDecipher")
        self.setMinimumSize(QSize(800, 600))
        
        # Set up the UI
        self._setup_ui()
        
        # Restore window state
        self._restore_window_state()
        
        # Apply the current theme
        self._theme_manager.apply_theme()
        
    def _setup_ui(self):
        """Set up the user interface."""
        # TODO: Add UI setup code
        pass
        
    def _restore_window_state(self):
        """Restore window state from preferences."""
        self._preferences_manager.restore_window_state(self)
        
    def closeEvent(self, event):
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        # Save window state
        self._preferences_manager.save_window_state(self)
        
        # Accept the event to close the window
        event.accept()