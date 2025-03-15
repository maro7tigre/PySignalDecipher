"""
Utility panel for PySignalDecipher.

This module provides a utility panel that appears above the workspace tabs
and contains tools for hardware connection, workspace-specific utilities,
and widget-specific utilities.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot

from .hardware_utility import HardwareUtilityPanel
from .workspace_utility_manager import WorkspaceUtilityManager
from .widget_utility_manager import WidgetUtilityManager


class UtilityPanel(QWidget):
    """
    Main utility panel that combines hardware connection, workspace utilities,
    and widget utilities into a unified interface.
    
    This panel is displayed at the top of the main window and contains
    multiple sections for different types of utilities.
    """
    
    def __init__(self, theme_manager, parent=None):
        """
        Initialize the utility panel.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store references
        self._theme_manager = theme_manager
        
        # Set up the panel layout and sections
        self._setup_ui()
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)
        
    def _setup_ui(self):
        """Set up the user interface for the utility panel."""
        # Main layout (horizontal layout for sections side by side)
        self._main_layout = QHBoxLayout(self)
        self._main_layout.setContentsMargins(4, 4, 4, 4)
        self._main_layout.setSpacing(8)

        # Hardware utility section
        self._hardware_utility = HardwareUtilityPanel(self._theme_manager)
        self._hardware_utility.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._main_layout.addWidget(self._hardware_utility)

        # Workspace utility section
        self._workspace_utility_group = QGroupBox("Workspace Utilities")
        workspace_layout = QVBoxLayout(self._workspace_utility_group)
        workspace_layout.setContentsMargins(4, 12, 4, 4)  # Reduced margins
        self._workspace_utility_manager = WorkspaceUtilityManager(self._theme_manager)

        # Set item height for workspace utilities
        for utility in self._workspace_utility_manager._workspace_utilities.values():
            utility.item_height = 30  # Set to desired height

        workspace_layout.addWidget(self._workspace_utility_manager)
        self._workspace_utility_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._main_layout.addWidget(self._workspace_utility_group, 1)  # Give stretch for workspace utilities

        # Widget utility section
        self._widget_utility_group = QGroupBox("Selected Element")
        widget_layout = QVBoxLayout(self._widget_utility_group)
        widget_layout.setContentsMargins(4, 12, 4, 4)  # Reduced margins
        self._widget_utility_manager = WidgetUtilityManager(self._theme_manager)
        widget_layout.addWidget(self._widget_utility_manager)
        self._widget_utility_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._main_layout.addWidget(self._widget_utility_group, 1)  # Give stretch for widget utilities

    def set_active_workspace(self, workspace_id, workspace_widget):
        """
        Update the workspace utility section based on the active workspace.
        
        Args:
            workspace_id: ID of the active workspace
            workspace_widget: Reference to the workspace widget
        """
        self._workspace_utility_manager.set_active_workspace(workspace_id, workspace_widget)
        
    def set_selected_widget(self, widget_type, widget):
        """
        Update the widget utility section based on the selected widget.
        
        Args:
            widget_type: Type of the selected widget
            widget: Reference to the selected widget
        """
        self._widget_utility_manager.set_selected_widget(widget_type, widget)
        
    def apply_theme(self, theme_manager):
        """
        Apply the current theme to the utility panel.
        
        Args:
            theme_manager: Reference to the ThemeManager
        """
        self._theme_manager = theme_manager
        
        # Apply theme to child components
        self._hardware_utility.apply_theme(theme_manager)
        self._workspace_utility_manager.apply_theme(theme_manager)
        self._widget_utility_manager.apply_theme(theme_manager)