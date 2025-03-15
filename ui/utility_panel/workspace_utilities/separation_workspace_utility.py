"""
Separation workspace utility for PySignalDecipher.

This module provides utilities specific to the Signal Separation workspace.
"""

from PySide6.QtWidgets import QComboBox, QSpinBox

from .base_workspace_utility import BaseWorkspaceUtility


class SeparationWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Signal Separation workspace.
    
    Provides tools and controls specific to the Signal Separation workspace.
    """
    
    def __init__(self, theme_manager, parent=None):
        """
        Initialize the separation workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
        
        # Set up the UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for the separation workspace utility."""
        # Create separation method selection
        method_combo = self._create_combo_box([
            "Frequency Domain Filtering", 
            "Independent Component Analysis", 
            "Wavelet Decomposition"
        ])
        self._create_control_pair("Method:", method_combo)
        
        # Create component count control
        component_spin = QSpinBox()
        component_spin.setRange(2, 10)
        component_spin.setValue(3)
        self._create_control_pair("Components:", component_spin)
        
        # Create separate button
        self._create_button("Separate")
        
        # Create export button
        self._create_button("Export")
        
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