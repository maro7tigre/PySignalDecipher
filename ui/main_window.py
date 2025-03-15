from PySide6.QtWidgets import QMainWindow, QApplication, QStatusBar, QTabWidget
from PySide6.QtCore import QSize, Qt

from .theme import ThemeManager
from .menus import MenuManager, MenuActionHandler


class MainWindow(QMainWindow):
    """
    Main application window with support for theme and preferences.
    
    Handles window state restoration, theme application, and menu system.
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
        
        # Set up the menu system
        self._setup_menus()
        
        # Set up the UI
        self._setup_ui()
        
        # Restore window state
        self._restore_window_state()
        
        # Apply the current theme
        self._theme_manager.apply_theme()
        
    def _setup_menus(self):
        """Set up the application menu system."""
        # Create menu manager
        self._menu_manager = MenuManager(self, self._theme_manager, self._preferences_manager)
        
        # Create menu action handler
        self._menu_action_handler = MenuActionHandler(self, self._theme_manager, self._preferences_manager)
        
        # Connect menu actions to handler
        self._menu_manager.action_triggered.connect(self._menu_action_handler.handle_action)
        
        # Set the menu bar
        self.setMenuBar(self._menu_manager.menu_bar)
        
        # Apply theme to ensure everything looks correct
        self._theme_manager.apply_theme()
        
    def _setup_ui(self):
        """Set up the user interface."""
        # Create status bar
        self.setStatusBar(QStatusBar(self))
        
        # Create central widget (tab widget for workspaces)
        self._tab_widget = QTabWidget(self)
        self.setCentralWidget(self._tab_widget)
        
        # TODO: Add tabs for each workspace
        self._setup_workspaces()
        
    def _setup_workspaces(self):
        """Set up workspace tabs."""
        # This would create and add workspace tabs
        # For now, we'll just add placeholder tabs
        self._tab_widget.addTab(QTabWidget(), "Basic Signal Analysis")
        self._tab_widget.addTab(QTabWidget(), "Protocol Decoder")
        self._tab_widget.addTab(QTabWidget(), "Pattern Recognition")
        self._tab_widget.addTab(QTabWidget(), "Signal Separation")
        self._tab_widget.addTab(QTabWidget(), "Signal Origin")
        self._tab_widget.addTab(QTabWidget(), "Advanced Analysis")
        
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