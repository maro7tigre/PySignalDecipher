from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from PySide6.QtGui import QKeySequence


class ViewMenu:
    """
    View menu implementation for the application.
    
    Contains actions for controlling the display and appearance of the application.
    """
    
    def __init__(self, menu_manager, theme_manager):
        """
        Initialize the view menu.
        
        Args:
            menu_manager: Reference to the MenuManager
            theme_manager: Reference to the ThemeManager
        """
        self._menu_manager = menu_manager
        self._theme_manager = theme_manager
        
        # Create the menu
        self._menu = QMenu("&View")
        
        # Initialize actions
        self._initialize_actions()
        
    def _initialize_actions(self):
        """Set up all actions for this menu."""
        # Toolbars submenu
        self._toolbars_menu = QMenu("&Toolbars", self._menu)
        self._menu.addMenu(self._toolbars_menu)
        
        # Add a sample toolbar toggle (would be populated dynamically)
        main_toolbar_action = self._menu_manager.create_action(
            self._toolbars_menu, "view.toolbar.main", "&Main Toolbar",
            checkable=True, checked=True,
            status_tip="Show or hide the main toolbar"
        )
        self._toolbars_menu.addAction(main_toolbar_action)
        
        # Status Bar
        status_bar_action = self._menu_manager.create_action(
            self._menu, "view.status_bar", "&Status Bar",
            checkable=True, checked=True,
            status_tip="Show or hide the status bar"
        )
        self._menu.addAction(status_bar_action)
        
        self._menu.addSeparator()
        
        # Themes submenu
        self._themes_menu = QMenu("&Themes", self._menu)
        self._menu.addMenu(self._themes_menu)
        
        # Populate the themes menu
        self._initialize_themes_menu()
        
        self._menu.addSeparator()
        
        # Full Screen
        full_screen_action = self._menu_manager.create_action(
            self._menu, "view.full_screen", "&Full Screen",
            shortcut="F11",
            checkable=True, checked=False,
            status_tip="Toggle full screen mode"
        )
        self._menu.addAction(full_screen_action)
        
        self._menu.addSeparator()
        
        # Zoom In
        zoom_in_action = self._menu_manager.create_action(
            self._menu, "view.zoom_in", "Zoom &In",
            shortcut=QKeySequence.ZoomIn,
            status_tip="Zoom in"
        )
        self._menu.addAction(zoom_in_action)
        
        # Zoom Out
        zoom_out_action = self._menu_manager.create_action(
            self._menu, "view.zoom_out", "Zoom &Out",
            shortcut=QKeySequence.ZoomOut,
            status_tip="Zoom out"
        )
        self._menu.addAction(zoom_out_action)
        
        # Reset Zoom
        reset_zoom_action = self._menu_manager.create_action(
            self._menu, "view.reset_zoom", "&Reset Zoom",
            shortcut="Ctrl+0",
            status_tip="Reset zoom to default level"
        )
        self._menu.addAction(reset_zoom_action)
        
    def _initialize_themes_menu(self):
        """Set up the themes submenu."""
        # Get available themes
        themes = self._theme_manager.get_available_themes()
        active_theme = self._theme_manager.get_active_theme()
        
        # Create an action group for themes (only one can be active)
        for theme in themes:
            # Create a properly formatted theme name for display
            display_name = theme.replace("_", " ").title()
            
            theme_action = self._menu_manager.create_action(
                self._themes_menu, f"view.theme.{theme}", display_name,
                checkable=True, checked=(theme == active_theme),
                status_tip=f"Switch to the {display_name} theme"
            )
            self._themes_menu.addAction(theme_action)
        
        # Connect to theme changes signal to update menu checkmarks
        self._theme_manager.theme_changed.connect(self.update_theme_menu)
            
    def update_theme_menu(self, theme_name=None):
        """
        Update the checked state of theme actions based on the active theme.
        
        Args:
            theme_name: Optional name of the new theme (unused, we get it from theme_manager)
        """
        active_theme = self._theme_manager.get_active_theme()
        
        for action in self._themes_menu.actions():
            # Extract theme name from the action's data or text
            theme = None
            
            # Try to get the action's ID from the menu manager
            for action_id, registered_action in self._menu_manager._actions.items():
                if registered_action == action and action_id.startswith("view.theme."):
                    theme = action_id.replace("view.theme.", "")
                    break
                    
            # If we couldn't find it in the registered actions, try to extract from text
            if theme is None:
                theme = action.text().replace(" ", "_").lower()
                
            if theme:
                action.setChecked(theme == active_theme)
                
    @property
    def menu(self):
        """Get the menu instance."""
        return self._menu