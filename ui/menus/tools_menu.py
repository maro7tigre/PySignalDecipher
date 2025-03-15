from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction


class ToolsMenu:
    """
    Tools menu implementation for the application.
    
    Contains actions for accessing various tools and utilities.
    """
    
    def __init__(self, menu_manager):
        """
        Initialize the tools menu.
        
        Args:
            menu_manager: Reference to the MenuManager
        """
        self._menu_manager = menu_manager
        
        # Create the menu
        self._menu = QMenu("&Tools")
        
        # Initialize actions
        self._initialize_actions()
        
    def _initialize_actions(self):
        """Set up all actions for this menu."""
        # Signal Library
        signal_library_action = self._menu_manager.create_action(
            self._menu, "tools.signal_library", "&Signal Library",
            status_tip="Access saved signal data"
        )
        self._menu.addAction(signal_library_action)
        
        # Protocol Library
        protocol_library_action = self._menu_manager.create_action(
            self._menu, "tools.protocol_library", "&Protocol Library",
            status_tip="Access saved protocol definitions"
        )
        self._menu.addAction(protocol_library_action)
        
        # Pattern Library
        pattern_library_action = self._menu_manager.create_action(
            self._menu, "tools.pattern_library", "P&attern Library",
            status_tip="Access saved pattern definitions"
        )
        self._menu.addAction(pattern_library_action)
        
        self._menu.addSeparator()
        
        # Plugin Manager
        plugin_manager_action = self._menu_manager.create_action(
            self._menu, "tools.plugin_manager", "Plugin &Manager...",
            status_tip="Manage application plugins"
        )
        self._menu.addAction(plugin_manager_action)
        
        # Script Editor
        script_editor_action = self._menu_manager.create_action(
            self._menu, "tools.script_editor", "&Script Editor",
            status_tip="Open the script editor"
        )
        self._menu.addAction(script_editor_action)
        
        self._menu.addSeparator()
        
        # Settings
        settings_action = self._menu_manager.create_action(
            self._menu, "tools.settings", "&Settings...",
            status_tip="Configure application settings"
        )
        self._menu.addAction(settings_action)
        
    @property
    def menu(self):
        """Get the menu instance."""
        return self._menu