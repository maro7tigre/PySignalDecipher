"""
Protocol workspace utility for PySignalDecipher.

This module provides utilities specific to the Protocol Decoder workspace.
"""

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
    
    def register_controls(self):
        """Register all controls for the protocol workspace utility."""
        # Add protocol selection
        self.add_combo_box(
            id="protocol",
            label="Protocol:",
            items=["UART", "SPI", "I2C", "CAN", "1-Wire", "JTAG", "USB"],
            callback=self._protocol_changed
        )
        
        # Add baudrate selection
        self.add_combo_box(
            id="baudrate",
            label="Baudrate:",
            items=["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
        )
        
        # Add parity selection
        self.add_combo_box(
            id="parity",
            label="Parity:",
            items=["None", "Even", "Odd", "Mark", "Space"]
        )
        
        # Add data bits selection
        self.add_combo_box(
            id="data_bits",
            label="Data Bits:",
            items=["5", "6", "7", "8"]
        )
        
        # Add stop bits selection
        self.add_combo_box(
            id="stop_bits",
            label="Stop Bits:",
            items=["1", "1.5", "2"]
        )
        
        # Add checkboxes
        self.add_check_box(
            id="invert",
            text="Invert Signal",
            checked=False
        )
        
        self.add_check_box(
            id="lsb_first",
            text="LSB First",
            checked=False
        )
        
        self.add_check_box(
            id="filter",
            text="Enable Filtering",
            checked=False
        )
        
        # Add buttons
        self.add_button(
            id="decode",
            text="Decode",
            callback=self._decode_signal
        )
        
        self.add_button(
            id="export",
            text="Export Data",
            callback=self._export_data
        )
        
        self.add_button(
            id="clear",
            text="Clear",
            callback=self._clear_data
        )
        
        self.add_button(
            id="settings",
            text="Protocol Settings...",
            callback=self._show_settings
        )
    
    def _protocol_changed(self, protocol_name):
        """
        Handle protocol selection changes.
        
        Args:
            protocol_name: Selected protocol name
        """
        # Enable/disable controls based on selected protocol
        is_serial = protocol_name == "UART"
        is_spi_i2c = protocol_name in ["SPI", "I2C"]
        
        # Access controls by their ID
        self.get_control("baudrate").setEnabled(is_serial)
        self.get_control("parity").setEnabled(is_serial)
        self.get_control("data_bits").setEnabled(is_serial)
        self.get_control("stop_bits").setEnabled(is_serial)
        self.get_control("lsb_first").setEnabled(is_spi_i2c)
    
    def _decode_signal(self):
        """Handle decode button click."""
        # Implementation would go here
        pass
    
    def _export_data(self):
        """Handle export button click."""
        # Implementation would go here
        pass
    
    def _clear_data(self):
        """Handle clear button click."""
        # Implementation would go here
        pass
    
    def _show_settings(self):
        """Handle settings button click."""
        # Implementation would go here
        pass
    
    def _workspace_updated(self):
        """
        Handle updates when the workspace is set or changed.
        """
        if self._workspace:
            # Update from workspace state if needed
            pass