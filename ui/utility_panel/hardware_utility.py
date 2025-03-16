"""
Hardware utility panel for PySignalDecipher.

This module provides a utility panel for hardware connection and control
that appears across all workspaces.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QGroupBox, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot

from core.service_registry import ServiceRegistry
from core.hardware.device_manager import DeviceManager


class HardwareUtilityPanel(QWidget):
    """
    Utility panel for hardware connection and control.
    
    Provides controls for connecting to hardware devices, selecting device
    parameters, and displaying connection status.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the hardware utility panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Get managers from registry
        self._theme_manager = ServiceRegistry.get_theme_manager()
        self._device_manager = ServiceRegistry.get_device_manager()
        
        # Connect to device manager signals
        self._device_manager.connection_status_changed.connect(self._on_connection_status_changed)
        
        # Set up the panel layout and controls
        self._setup_ui()
        
        # Populate the device list initially
        self._refresh_devices()
        
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
        group_layout.setSpacing(4)
        
        # Row 1: Device selection
        device_layout = QHBoxLayout()
        device_layout.setSpacing(4)
        device_label = QLabel("Device:")
        self._device_combo = QComboBox()
        self._device_combo.setMinimumWidth(150)
        self._device_combo.addItem("No devices found")
        
        device_layout.addWidget(device_label)
        device_layout.addWidget(self._device_combo, 1)
        
        # Row 2: Refresh and Connect buttons side by side with expanded width
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.setToolTip("Refresh available devices")
        self._refresh_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self._connect_button = QPushButton("Connect")
        self._connect_button.setToolTip("Connect to the selected device")
        self._connect_button.setProperty("class", "green")  # Use class property for styling
        self._connect_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        buttons_layout.addWidget(self._refresh_button)
        buttons_layout.addWidget(self._connect_button)
        
        # Row 3: Status label
        status_layout = QHBoxLayout()
        status_layout.setSpacing(4)
        self._status_label = QLabel("Not connected")
        
        status_layout.addWidget(self._status_label, 1)
        
        # Add rows to the group layout
        group_layout.addLayout(device_layout)
        group_layout.addLayout(buttons_layout)
        group_layout.addLayout(status_layout)
        
        # Add group to the main layout
        self._main_layout.addWidget(self._hardware_group)
        
        # Connect signals
        self._refresh_button.clicked.connect(self._refresh_devices)
        self._connect_button.clicked.connect(self._toggle_connection)
        
    def _refresh_devices(self):
        """Refresh the list of available devices."""
        self._device_combo.clear()
        
        try:
            # Get device map from device manager
            device_map = self._device_manager.get_device_map()
            
            if not device_map:
                self._device_combo.addItem("No devices found")
                self._connect_button.setEnabled(False)
                return
                
            # Add devices to combo box
            for friendly_name in device_map.keys():
                self._device_combo.addItem(friendly_name)
                
            self._connect_button.setEnabled(True)
                
        except Exception as e:
            # Error finding devices
            self._device_combo.addItem("No devices found")
            self._connect_button.setEnabled(False)
            QMessageBox.warning(self, "Device Error", f"Error finding devices: {str(e)}")
        
    def _toggle_connection(self):
        """Toggle the connection state."""
        if self._device_manager.is_connected():
            # Disconnect from the current device
            self._disconnect()
        else:
            # Connect to the selected device
            self._connect_to_device()
            
    def _connect_to_device(self):
        """Connect to the selected device."""
        friendly_name = self._device_combo.currentText()
        if friendly_name == "No devices found":
            return
            
        # Update UI while connecting
        self._connect_button.setEnabled(False)
        self._refresh_button.setEnabled(False)
        self._status_label.setText(f"Connecting to {friendly_name}...")
        
        # Connect to the device via device manager
        self._device_manager.connect_device(friendly_name)
    
    @Slot(bool, str)
    def _on_connection_status_changed(self, connected, device_info):
        """
        Handle connection status changes from device manager.
        
        Args:
            connected: Whether connected successfully
            device_info: Device information or error message
        """
        if connected:
            # Connected successfully
            self._connect_button.setText("Disconnect")
            self._connect_button.setProperty("class", "red")  # Change to red for disconnect
            
            # Extract just the model information from IDN string if available
            device_name = self._device_manager.get_current_device_name()
            
            self._status_label.setText(f"Connected: {device_name}")
            self._device_combo.setEnabled(False)
            self._refresh_button.setEnabled(False)
            self._connect_button.setEnabled(True)
            
            # Force style sheet update
            self._connect_button.style().unpolish(self._connect_button)
            self._connect_button.style().polish(self._connect_button)
        else:
            # Connection failed or disconnected
            self._connect_button.setText("Connect")
            self._connect_button.setProperty("class", "green")  # Change back to green for connect
            
            if device_info:  # Error message
                self._status_label.setText(f"Connection failed")
                
                # Show error message to user
                QMessageBox.warning(
                    self,
                    "Connection Error",
                    f"Failed to connect to the device: {device_info}"
                )
            else:  # Normal disconnect
                self._status_label.setText("Not connected")
                
            self._device_combo.setEnabled(True)
            self._refresh_button.setEnabled(True)
            self._connect_button.setEnabled(True)
            
            # Force style sheet update
            self._connect_button.style().unpolish(self._connect_button)
            self._connect_button.style().polish(self._connect_button)
            
    def _disconnect(self):
        """Disconnect from the current device."""
        try:
            self._device_manager.disconnect_device()
        except Exception as e:
            QMessageBox.warning(self, "Disconnect Error", f"Error disconnecting: {str(e)}")
        
    def is_connected(self):
        """
        Check if a device is currently connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._device_manager.is_connected()
        
    def get_current_device(self):
        """
        Get the currently connected device.
        
        Returns:
            str: Name/address of the connected device, or None if not connected
        """
        return self._device_manager.get_current_device_name()
    
    def get_device_object(self):
        """
        Get the device object for the connected device.
        
        Returns:
            object: PyVISA resource object for the connected device, or None if not connected
        """
        return self._device_manager.get_device_object()
        
    def apply_theme(self, theme_manager=None):
        """
        Apply the current theme to the hardware utility panel.
        
        Args:
            theme_manager: Optional theme manager reference (uses registry if None)
        """
        if theme_manager:
            self._theme_manager = theme_manager
        
        # Set group box background color
        bg_color = self._theme_manager.get_color("background.secondary")
        self._hardware_group.setStyleSheet(f"QGroupBox {{ background-color: {bg_color}; }}")
        
    def closeEvent(self, event):
        """Handle panel close event to clean up resources."""
        if self._device_manager.is_connected():
            self._disconnect()
        super().closeEvent(event)