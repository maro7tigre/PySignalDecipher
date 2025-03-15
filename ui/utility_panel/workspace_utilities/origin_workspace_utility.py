"""
Origin workspace utility for PySignalDecipher.

This module provides utilities specific to the Signal Origin workspace.
"""

from PySide6.QtWidgets import QComboBox, QDoubleSpinBox

from .base_workspace_utility import BaseWorkspaceUtility


class OriginWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Signal Origin workspace.
    
    Provides tools and controls specific to the Signal Origin workspace.
    """
    
    def __init__(self, theme_manager, parent=None):
        """
        Initialize the origin workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
        
        # Set up the UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for the origin workspace utility."""
        # Create localization method selection
        method_combo = self._create_combo_box([
            "Direction Finding", 
            "Triangulation", 
            "Signal Strength"
        ])
        self._create_control_pair("Method:", method_combo)
        
        # Create frequency control
        freq_spin = QDoubleSpinBox()
        freq_spin.setRange(1, 6000)
        freq_spin.setValue(433)
        freq_spin.setDecimals(3)
        freq_spin.setSuffix(" MHz")
        self._create_control_pair("Frequency:", freq_spin)
        
        # Create locate button
        self._create_button("Locate")
        
        # Create map button
        self._create_button("Show Map")
        
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