"""
Protocol workspace utility for PySignalDecipher.

This module provides utilities specific to the Protocol Decoder workspace.
"""

from PySide6.QtWidgets import QComboBox

from .base_workspace_utility import BaseWorkspaceUtility


class ProtocolWorkspaceUtility(BaseWorkspaceUtility):
    """
    Utility panel for Protocol Decoder workspace.
    
    Provides tools and controls specific to the Protocol Decoder workspace.
    """
    
    def __init__(self, theme_manager, parent=None):
        """
        Initialize the protocol workspace utility.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(theme_manager, parent)
        
        # Set up the UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for the protocol workspace utility."""
        # Create protocol selection
        protocol_combo = self._create_combo_box(["UART", "SPI", "I2C", "CAN"])
        self._create_control_pair("Protocol:", protocol_combo)
        
        # Create baudrate control for serial protocols
        baud_combo = self._create_combo_box(["9600", "115200", "57600", "19200"])
        self._create_control_pair("Baudrate:", baud_combo)
        
        # Create decode button
        self._create_button("Decode")
        
        # Create export button
        self._create_button("Export Data")
        
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