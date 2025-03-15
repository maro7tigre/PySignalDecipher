from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction


class HelpMenu:
    """
    Help menu implementation for the application.
    
    Contains actions for accessing documentation, help resources, and information about the application.
    """
    
    def __init__(self, menu_manager):
        """
        Initialize the help menu.
        
        Args:
            menu_manager: Reference to the MenuManager
        """
        self._menu_manager = menu_manager
        
        # Create the menu
        self._menu = QMenu("&Help")
        
        # Initialize actions
        self._initialize_actions()
        
    def _initialize_actions(self):
        """Set up all actions for this menu."""
        # Documentation
        documentation_action = self._menu_manager.create_action(
            self._menu, "help.documentation", "&Documentation",
            status_tip="View application documentation"
        )
        self._menu.addAction(documentation_action)
        
        # Quick Start Guide
        quick_start_action = self._menu_manager.create_action(
            self._menu, "help.quick_start", "&Quick Start Guide",
            status_tip="View the quick start guide"
        )
        self._menu.addAction(quick_start_action)
        
        # Keyboard Shortcuts
        shortcuts_action = self._menu_manager.create_action(
            self._menu, "help.shortcuts", "&Keyboard Shortcuts",
            status_tip="View keyboard shortcuts"
        )
        self._menu.addAction(shortcuts_action)
        
        # Example Projects
        examples_action = self._menu_manager.create_action(
            self._menu, "help.examples", "&Example Projects",
            status_tip="View example projects"
        )
        self._menu.addAction(examples_action)
        
        self._menu.addSeparator()
        
        # Check for Updates
        updates_action = self._menu_manager.create_action(
            self._menu, "help.updates", "Check for &Updates",
            status_tip="Check for application updates"
        )
        self._menu.addAction(updates_action)
        
        self._menu.addSeparator()
        
        # About
        about_action = self._menu_manager.create_action(
            self._menu, "help.about", "&About PySignalDecipher",
            status_tip="Show information about the application"
        )
        self._menu.addAction(about_action)
        
    @property
    def menu(self):
        """Get the menu instance."""
        return self._menu