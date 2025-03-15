"""
Basic workspace utility for PySignalDecipher.

This module provides utilities specific to the Basic Signal Analysis workspace.
"""

from PySide6.QtWidgets import QComboBox

from .base_workspace_utility import BaseWorkspaceUtility


class BasicWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Basic Signal Analysis workspace.
    
    Provides tools and controls specific to the Basic Signal Analysis workspace.
    """
    
    def __init__(self, theme_manager, parent=None):
        """
        Initialize the basic workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
        
        # Set up the UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for the basic workspace utility."""
        # Create signal type control
        signal_type_combo = self._create_combo_box(["Time Domain", "Frequency Domain"])
        self._create_control_pair("Signal Type:", signal_type_combo)
        
        # Create zoom controls
        zoom_combo = self._create_combo_box(["100%", "200%", "50%", "Fit to View"])
        self._create_control_pair("Zoom:", zoom_combo)
        
        # Create quick analysis button
        self._create_button("Quick Analysis")
        
        # Create add signal button
        self._create_button("Add Signal")
        
        # Update the layout to distribute controls
        self._update_layout()
        
    def _workspace_updated(self):
        """
        Handle updates when the workspace is set or changed.
        """
        # Update controls based on workspace state if needed
        if self._workspace:
            # This would typically query the workspace for its current state
            # and update the UI controls accordingly
            pass