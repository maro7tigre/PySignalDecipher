from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import QObject, Signal
from command_system.command_manager import CommandManager

from .file_menu import FileMenu
from .edit_menu import EditMenu
from .view_menu import ViewMenu
from .workspace_menu import WorkspaceMenu
from .window_menu import WindowMenu
from .tools_menu import ToolsMenu
from .help_menu import HelpMenu


class MenuManager(QObject):
    """
    Manages the application menu system.
    
    Creates and organizes all menus and their actions, and connects them
    to the appropriate handlers. Provides a central place to access and
    control all menu-related functionality.
    """
    
    # Signal emitted when a menu action is triggered
    action_triggered = Signal(str)
    
    def __init__(self, main_window, theme_manager=None, preferences_manager=None):
        """
        Initialize the menu manager.
        
        Args:
            main_window: Reference to the main application window
            theme_manager: Reference to the ThemeManager
            preferences_manager: Reference to the PreferencesManager
        """
        super().__init__()
        
        # Dictionary to store all created actions
        self._actions = {}
        
        # Get command manager for accessing services if needed
        self._command_manager = CommandManager.instance()
        
        # Get services from command manager if not provided
        if theme_manager is None and self._command_manager:
            from ui.theme.theme_manager import ThemeManager
            theme_manager = self._command_manager.get_service(ThemeManager)
            
        if preferences_manager is None and self._command_manager:
            from utils.preferences_manager import PreferencesManager
            preferences_manager = self._command_manager.get_service(PreferencesManager)
        
        # Store references
        self._main_window = main_window
        self._theme_manager = theme_manager
        self._preferences_manager = preferences_manager
        
        # Create the menu bar
        self._menu_bar = QMenuBar(main_window)
        
        # Create individual menu handlers
        self._file_menu = FileMenu(self)
        self._edit_menu = EditMenu(self)
        self._view_menu = ViewMenu(self, theme_manager)
        self._workspace_menu = WorkspaceMenu(self)
        self._window_menu = WindowMenu(self)
        self._tools_menu = ToolsMenu(self)
        self._help_menu = HelpMenu(self)
        
        # Initialize the menu system
        self._initialize_menus()
        
    def _initialize_menus(self):
        """Set up all menus and their actions."""
        # Add all menus to the menu bar
        self._menu_bar.addMenu(self._file_menu.menu)
        self._menu_bar.addMenu(self._edit_menu.menu)
        self._menu_bar.addMenu(self._view_menu.menu)
        self._menu_bar.addMenu(self._workspace_menu.menu)
        self._menu_bar.addMenu(self._window_menu.menu)
        self._menu_bar.addMenu(self._tools_menu.menu)
        self._menu_bar.addMenu(self._help_menu.menu)
        
    @property
    def menu_bar(self):
        """Get the menu bar instance."""
        return self._menu_bar
        
    def get_action(self, action_id):
        """
        Get an action by its ID.
        
        Args:
            action_id: Unique identifier for the action
            
        Returns:
            The action, or None if not found
        """
        return self._actions.get(action_id)
        
    def register_action(self, action_id, action):
        """
        Register an action with the menu manager.
        
        Args:
            action_id: Unique identifier for the action
            action: The QAction to register
        """
        self._actions[action_id] = action
        action.triggered.connect(lambda: self._handle_action(action_id))
        
    def _handle_action(self, action_id):
        """
        Handle a menu action being triggered.
        
        Args:
            action_id: Identifier of the triggered action
        """
        # Emit the action_triggered signal with the ID
        self.action_triggered.emit(action_id)
        
    def update_action_states(self):
        """Update the enabled/checked state of all actions based on application state."""
        # Get active project and command manager state
        if self._command_manager:
            # Update undo/redo action states
            undo_action = self.get_action("edit.undo")
            if undo_action:
                undo_action.setEnabled(self._command_manager.can_undo())
                
            redo_action = self.get_action("edit.redo")
            if redo_action:
                redo_action.setEnabled(self._command_manager.can_redo())
        
    def create_action(self, parent, action_id, text, shortcut=None, status_tip=None, 
                      icon=None, checkable=False, checked=False):
        """
        Create and register a new QAction.
        
        Args:
            parent: Parent widget for the action
            action_id: Unique identifier for the action
            text: Display text for the action
            shortcut: Optional keyboard shortcut
            status_tip: Optional status tip text
            icon: Optional icon for the action
            checkable: Whether the action is checkable
            checked: Initial checked state if checkable
            
        Returns:
            The created QAction
        """
        action = QAction(text, parent)
        
        if shortcut:
            action.setShortcut(shortcut)
            
        if status_tip:
            action.setStatusTip(status_tip)
            
        if icon:
            action.setIcon(icon)
            
        if checkable:
            action.setCheckable(True)
            action.setChecked(checked)
            
        self.register_action(action_id, action)
        return action