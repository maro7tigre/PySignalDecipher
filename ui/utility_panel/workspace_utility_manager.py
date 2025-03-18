"""
Workspace utility manager for PySignalDecipher with command system integration.

This module provides a manager for workspace-specific utilities
that dynamically changes based on the active workspace, integrated with the command system.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QLabel
)
from PySide6.QtCore import Qt

from command_system.command_manager import CommandManager
from command_system.command import CommandContext
from ..theme.theme_manager import ThemeManager

# Import workspace utilities
from .workspace_utilities.basic_workspace_utility import BasicWorkspaceUtility
from .workspace_utilities.protocol_workspace_utility import ProtocolWorkspaceUtility
from .workspace_utilities.pattern_workspace_utility import PatternWorkspaceUtility
from .workspace_utilities.separation_workspace_utility import SeparationWorkspaceUtility
from .workspace_utilities.origin_workspace_utility import OriginWorkspaceUtility
from .workspace_utilities.advanced_workspace_utility import AdvancedWorkspaceUtility


class WorkspaceUtilityManager(QWidget):
    """
    Manager for workspace-specific utilities.
    
    Dynamically changes the displayed utilities based on the active workspace.
    Integrated with the command system.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the workspace utility manager.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Command system integration
        self._command_manager = None
        self._command_context = None
        
        # Theme manager will be set by command manager
        self._theme_manager = None
        
        # Create workspace utility instances
        self._workspace_utilities = {}
        self._active_workspace_id = None
        
        # Set up the manager UI
        self._setup_ui()
        
    def set_command_manager(self, command_manager):
        """
        Set the command manager for this utility manager.
        
        Args:
            command_manager: Reference to the CommandManager
        """
        self._command_manager = command_manager
        
        # Create command context
        self._command_context = CommandContext(command_manager)
        
        # Get theme manager from command manager
        self._theme_manager = command_manager.get_service(ThemeManager) if hasattr(command_manager, 'get_service') else None
        
        # Try the legacy method if the service registry approach didn't work
        if not self._theme_manager and hasattr(command_manager, 'get_theme_manager'):
            self._theme_manager = command_manager.get_theme_manager()
        
        # Initialize workspace utilities
        self._initialize_workspace_utilities()
        
        # Apply theme if available
        if self._theme_manager:
            self.apply_theme(self._theme_manager)
        
    def _setup_ui(self):
        """Set up the user interface for the workspace utility manager."""
        # Use a vertical layout to fill the available space
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # Create a stacked widget to switch between workspace utilities
        self._stacked_widget = QStackedWidget()
        
        # Create a default widget for when no utilities are loaded
        self._default_widget = QWidget()
        default_layout = QVBoxLayout(self._default_widget)
        default_label = QLabel("Loading workspace utilities...")
        default_label.setAlignment(Qt.AlignCenter)
        default_layout.addWidget(default_label)
        self._stacked_widget.addWidget(self._default_widget)
        
        # Add the stacked widget to the main layout
        self._main_layout.addWidget(self._stacked_widget)
        
    def _initialize_workspace_utilities(self):
        """Initialize all workspace utilities."""
        # Clear any existing utilities (except default widget)
        for i in range(self._stacked_widget.count() - 1, 0, -1):
            widget = self._stacked_widget.widget(i)
            self._stacked_widget.removeWidget(widget)
            if widget:
                widget.deleteLater()
                
        self._workspace_utilities.clear()
                
        # Make sure theme manager is available
        if not self._theme_manager:
            return
            
        # Create instances of each workspace utility
        self._workspace_utilities = {
            "basic": BasicWorkspaceUtility(self._theme_manager),
            "protocol": ProtocolWorkspaceUtility(self._theme_manager),
            "pattern": PatternWorkspaceUtility(self._theme_manager),
            "separation": SeparationWorkspaceUtility(self._theme_manager),
            "origin": OriginWorkspaceUtility(self._theme_manager),
            "advanced": AdvancedWorkspaceUtility(self._theme_manager)
        }
        
        # Add each utility to the stacked widget
        for utility in self._workspace_utilities.values():
            # Pass command manager to the utility if it supports it
            if hasattr(utility, 'set_command_manager') and callable(getattr(utility, 'set_command_manager')):
                utility.set_command_manager(self._command_manager)
                
            self._stacked_widget.addWidget(utility)
        
        # Show default widget initially
        self._stacked_widget.setCurrentWidget(self._default_widget)
        
    def set_active_workspace(self, workspace_id, workspace_widget):
        """
        Update the displayed utilities based on the active workspace.
        
        Args:
            workspace_id: ID of the active workspace
            workspace_widget: Reference to the workspace widget
        """
        # Store the active workspace ID
        self._active_workspace_id = workspace_id
        
        # Update command context with active workspace
        if self._command_context:
            self._command_context.active_workspace = workspace_id
        
        # Map workspace ID to utility type
        workspace_type = self._get_workspace_type(workspace_id)
        
        if workspace_type in self._workspace_utilities:
            utility = self._workspace_utilities[workspace_type]
            utility.set_workspace(workspace_widget)
            self._stacked_widget.setCurrentWidget(utility)
        else:
            # Show the default widget if no specific utility is available
            self._stacked_widget.setCurrentWidget(self._default_widget)
            
    def _get_workspace_type(self, workspace_id):
        """
        Map workspace ID to utility type.
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            String representing the workspace type
        """
        # If the workspace ID is already a type string, return it
        if workspace_id in self._workspace_utilities:
            return workspace_id
            
        # Try to get workspace type from the active project
        if self._command_manager:
            project = self._command_manager.get_active_project()
            if project:
                workspace_state = project.get_workspace_state(workspace_id)
                return workspace_state.get_setting("type", "basic")
        
        # Default to basic workspace
        return "basic"
            
    def apply_theme(self, theme_manager=None):
        """
        Apply the current theme to all workspace utilities.
        
        Args:
            theme_manager: Optional theme manager reference
        """
        if theme_manager:
            self._theme_manager = theme_manager
        
        # Apply theme to all workspace utilities
        for utility in self._workspace_utilities.values():
            if hasattr(utility, 'apply_theme') and callable(getattr(utility, 'apply_theme')):
                utility.apply_theme(self._theme_manager)
                
        # Apply theme to default widget
        if self._theme_manager:
            bg_color = self._theme_manager.get_color("background.utility", "#F5F5F5")
            self._default_widget.setStyleSheet(f"background-color: {bg_color};")