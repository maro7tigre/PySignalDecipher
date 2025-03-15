"""
Pattern workspace utility for PySignalDecipher.

This module provides utilities specific to the Pattern Recognition workspace.
"""

from PySide6.QtWidgets import QComboBox, QSpinBox

from .base_workspace_utility import BaseWorkspaceUtility


class PatternWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Pattern Recognition workspace.
    
    Provides tools and controls specific to the Pattern Recognition workspace.
    """
    
    def __init__(self, theme_manager, parent=None):
        """
        Initialize the pattern workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
        
        # Set up the UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for the pattern workspace utility."""
        # Create pattern method selection
        method_combo = self._create_combo_box([
            "Correlation", 
            "Feature Matching", 
            "Template Matching"
        ])
        self._create_control_pair("Method:", method_combo)
        
        # Create threshold control
        threshold_spin = QSpinBox()
        threshold_spin.setRange(50, 100)
        threshold_spin.setValue(75)
        threshold_spin.setSuffix("%")
        self._create_control_pair("Threshold:", threshold_spin)
        
        # Create detect button
        self._create_button("Detect Patterns")
        
        # Create save button
        self._create_button("Save Pattern")
        
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