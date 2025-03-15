"""
Hardware utility panel for PySignalDecipher.

This module provides a utility panel for hardware connection and control
that appears across all workspaces.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QGroupBox
)
from PySide6.QtCore import Qt, Signal, Slot


class HardwareUtilityPanel(QWidget):
    """
    Utility panel for hardware connection and control.
    
    Provides controls for connecting to hardware devices, selecting device
    parameters, and displaying connection status.
    """
    
    # Signal emitted when a device connection status changes
    connection_status_changed = Signal(bool, str)  # connected, device_name
    
    def __init__(self, theme_manager, parent=None):
        """
        Initialize the hardware utility panel.
        
        Args:
            theme_manager: Reference to the ThemeManager
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store references
        self._theme_manager = theme_manager
        
        # Connection state
        self._is_connected = False
        self._current_device = None
        
        # Set up the panel layout and controls
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface for the hardware utility panel."""
        # Main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(2)
        
        # Create the hardware group box
        self._hardware_group = QGroupBox("Hardware Connection")
        group_layout = QVBoxLayout(self._hardware_group)
        group_layout.setContentsMargins(4, 12, 4, 4)  # Reduced margins
        group_layout.setSpacing(2)
        
        # Device selection row
        device_layout = QHBoxLayout()
        device_layout.setSpacing(4)
        device_label = QLabel("Device:")
        self._device_combo = QComboBox()
        self._device_combo.setMinimumWidth(150)
        self._device_combo.addItem("No devices found")
        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.setToolTip("Refresh available devices")
        
        device_layout.addWidget(device_label)
        device_layout.addWidget(self._device_combo, 1)
        device_layout.addWidget(self._refresh_button)
        
        # Connection control row
        connect_layout = QHBoxLayout()
        connect_layout.setSpacing(4)
        self._connect_button = QPushButton("Connect")
        self._connect_button.setToolTip("Connect to the selected device")
        self._status_label = QLabel("Not connected")
        
        connect_layout.addWidget(self._connect_button)
        connect_layout.addWidget(self._status_label, 1)
        
        # Add rows to the group layout
        group_layout.addLayout(device_layout)
        group_layout.addLayout(connect_layout)
        
        # Add group to the main layout
        self._main_layout.addWidget(self._hardware_group)
        
        # Connect signals
        self._refresh_button.clicked.connect(self._refresh_devices)
        self._connect_button.clicked.connect(self._toggle_connection)
        
    def _refresh_devices(self):
        """Refresh the list of available devices."""
        # This would be implemented to scan for available hardware
        self._device_combo.clear()
        
        # For now, just add some dummy devices
        self._device_combo.addItem("USBTMC0::0x0699::0x0363::C107676::INSTR")
        self._device_combo.addItem("USBTMC0::0x0957::0x1798::MY12345678::INSTR")
        self._device_combo.addItem("TCPIP0::192.168.1.5::INSTR")
        
    def _toggle_connection(self):
        """Toggle the connection state."""
        if self._is_connected:
            # Disconnect from the current device
            self._disconnect()
        else:
            # Connect to the selected device
            self._connect()
            
    def _connect(self):
        """Connect to the selected device."""
        device = self._device_combo.currentText()
        if device == "No devices found":
            return
            
        # This would actually establish a connection
        # For now, just simulate a successful connection
        self._is_connected = True
        self._current_device = device
        
        # Update UI
        self._connect_button.setText("Disconnect")
        self._status_label.setText("Connected")
        self._device_combo.setEnabled(False)
        self._refresh_button.setEnabled(False)
        
        # Emit connection status
        self.connection_status_changed.emit(True, device)
            
    def _disconnect(self):
        """Disconnect from the current device."""
        # This would actually close the connection
        self._is_connected = False
        self._current_device = None
        
        # Update UI
        self._connect_button.setText("Connect")
        self._status_label.setText("Not connected")
        self._device_combo.setEnabled(True)
        self._refresh_button.setEnabled(True)
        
        # Emit connection status
        self.connection_status_changed.emit(False, "")
        
    def is_connected(self):
        """
        Check if a device is currently connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected
        
    def get_current_device(self):
        """
        Get the currently connected device.
        
        Returns:
            str: Name/address of the connected device, or None if not connected
        """
        return self._current_device
        
    def apply_theme(self, theme_manager):
        """
        Apply the current theme to the hardware utility panel.
        
        Args:
            theme_manager: Reference to the ThemeManager
        """
        self._theme_manager = theme_manager
        
        # Set group box background color
        bg_color = self._theme_manager.get_color("background.secondary")
        self._hardware_group.setStyleSheet(f"QGroupBox {{ background-color: {bg_color}; }}")