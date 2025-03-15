"""
Origin workspace utility for PySignalDecipher.

This module provides utilities specific to the Signal Origin workspace.
"""

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
    
    def register_controls(self):
        """Register all controls for the origin workspace utility."""
        # Localization method
        self.add_combo_box(
            id="method",
            label="Method:",
            items=[
                "Direction Finding", 
                "Triangulation", 
                "Signal Strength",
                "Time Difference of Arrival",
                "Frequency Domain Analysis"
            ],
            callback=self._method_changed
        )
        
        # Frequency control
        self.add_double_spin_box(
            id="frequency",
            label="Frequency:",
            minimum=1,
            maximum=6000,
            value=433,
            decimals=3,
            suffix=" MHz"
        )
        
        # Antenna count control
        self.add_spin_box(
            id="antennas",
            label="Antennas:",
            minimum=1,
            maximum=8,
            value=2
        )
        
        # Gain control
        self.add_spin_box(
            id="gain",
            label="Gain:",
            minimum=0,
            maximum=60,
            value=20
        )
        
        # Samples control
        self.add_spin_box(
            id="samples",
            label="Samples:",
            minimum=1,
            maximum=1000,
            value=100
        )
        
        # Refresh rate selection
        self.add_combo_box(
            id="refresh",
            label="Refresh:",
            items=[
                "Manual", "1 sec", "5 sec", "10 sec", "30 sec", "60 sec"
            ]
        )
        
        # Continuous monitoring checkbox
        self.add_check_box(
            id="continuous",
            text="Continuous Monitoring",
            checked=False
        )
        
        # Log results checkbox
        self.add_check_box(
            id="logging",
            text="Log Results",
            checked=True
        )
        
        # Locate button
        self.add_button(
            id="locate",
            text="Locate",
            callback=self._locate
        )
        
        # Show map button
        self.add_button(
            id="map",
            text="Show Map",
            callback=self._show_map
        )
        
        # History button
        self.add_button(
            id="history",
            text="History",
            callback=self._show_history
        )
        
        # Calibrate button
        self.add_button(
            id="calibrate",
            text="Calibrate...",
            callback=self._calibrate
        )
    
    def _method_changed(self, method):
        """
        Handle changes to the selected localization method.
        
        Args:
            method: Name of the selected method
        """
        # Enable/disable controls based on selected method
        is_direction = method == "Direction Finding"
        is_triangulation = method == "Triangulation"
        is_tdoa = method == "Time Difference of Arrival"
        
        # Update antenna count requirements based on method
        min_antennas = 1
        if is_triangulation or is_tdoa:
            min_antennas = 3
        elif is_direction:
            min_antennas = 2
            
        antenna_control = self.get_control("antennas")
        antenna_control.setMinimum(min_antennas)
        if antenna_control.value() < min_antennas:
            antenna_control.setValue(min_antennas)
    
    def _locate(self):
        """Handle locate button click."""
        # Implementation would go here
        pass
    
    def _show_map(self):
        """Handle show map button click."""
        # Implementation would go here
        pass
    
    def _show_history(self):
        """Handle history button click."""
        # Implementation would go here
        pass
    
    def _calibrate(self):
        """Handle calibrate button click."""
        # Implementation would go here
        pass
    
    def _workspace_updated(self):
        """
        Handle updates when the workspace is set or changed.
        """
        if self._workspace:
            # Update from workspace state if needed
            pass