from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from ..themed_widgets.base_themed_widget import BaseThemedWidget


class BaseWorkspace(BaseThemedWidget):
    """
    Base class for all workspace tabs.
    
    Provides common functionality for workspaces such as layout management,
    state persistence, and interaction with the main application.
    """
    
    # Signal emitted when the workspace state changes
    state_changed = Signal()
    
    def __init__(self, parent=None):
        """
        Initialize the base workspace.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set up the main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        self.setLayout(self._main_layout)
        
        # Reference to the preferences manager (set by the set_preferences_manager method)
        self._preferences_manager = None
        
        # Initialize the workspace
        self._initialize_workspace()
        
    def _initialize_workspace(self):
        """
        Initialize the workspace components.
        
        To be overridden by subclasses.
        """
        pass
        
    def _apply_theme_impl(self):
        """
        Apply the current theme to this workspace.
        
        Implementation of the method from BaseThemedWidget.
        """
        # Apply theme to all child widgets that support it
        for child in self.findChildren(BaseThemedWidget):
            if hasattr(child, 'apply_theme') and callable(child.apply_theme):
                child.apply_theme(self._theme_manager)
                
    def set_preferences_manager(self, preferences_manager):
        """
        Set the preferences manager.
        
        Args:
            preferences_manager: Reference to the PreferencesManager
        """
        self._preferences_manager = preferences_manager
        
        # Load workspace state
        self._load_workspace_state()
        
    def _load_workspace_state(self):
        """
        Load workspace state from preferences.
        
        To be overridden by subclasses.
        """
        pass
        
    def _save_workspace_state(self):
        """
        Save workspace state to preferences.
        
        To be overridden by subclasses.
        """
        pass
        
    def get_workspace_id(self):
        """
        Get the unique identifier for this workspace.
        
        To be overridden by subclasses.
        
        Returns:
            str: Unique ID for this workspace
        """
        return "base"