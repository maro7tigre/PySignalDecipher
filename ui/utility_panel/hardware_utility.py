"""
Hardware utility panel for PySignalDecipher.

This module provides a utility panel for hardware connection and control
that appears across all workspaces.
"""

import pyvisa
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QGroupBox, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QThread


class OscilloscopeConnectionThread(QThread):
    """Thread for connecting to the oscilloscope without blocking the UI."""
    
    connection_successful = Signal(object, str)  # Signal emits scope object and idn
    connection_failed = Signal(str, list)        # Signal emits error message and available devices
    
    def __init__(self, address):
        """
        Initialize oscilloscope connection thread.
        
        Args:
            address (str): VISA address for the oscilloscope
        """
        super().__init__()
        self._address = address
        
    def run(self):
        """Connect to the oscilloscope using PyVISA."""
        rm = pyvisa.ResourceManager()
        try:
            # Open a connection to the oscilloscope with appropriate settings
            scope = rm.open_resource(self._address)
            
            # Configure for stable communication
            scope.timeout = 30000  # 30 seconds timeout for long operations
            scope.read_termination = '\n'
            scope.write_termination = '\n'
            
            # Clear the device to start with a clean state
            scope.write('*CLS')
            
            # Query the oscilloscope for identification
            idn = scope.query('*IDN?')
            self.connection_successful.emit(scope, idn)
        except pyvisa.VisaIOError as e:
            # List all connected devices if there's an error
            available_devices = rm.list_resources()
            self.connection_failed.emit(str(e), available_devices)


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
        self._device_object = None
        
        # Map of device addresses to user-friendly names
        self._device_map = {}
        
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
        
    def _get_user_friendly_name(self, address):
        """
        Convert a VISA address to a user-friendly device name.
        
        Args:
            address (str): VISA address
            
        Returns:
            str: User-friendly device name
        """
        # USB devices: USB0::0x1AB1::0x0517::DS1ZE263609367::INSTR
        usb_match = re.search(r'(USB\d+)::.*::.*::([^:]+)::INSTR', address)
        if usb_match:
            usb_id = usb_match.group(1)
            serial = usb_match.group(2)
            return f"{usb_id}:{serial}"
        
        # Network devices: TCPIP0::192.168.1.5::INSTR
        tcpip_match = re.search(r'(TCPIP\d+)::([^:]+)::', address)
        if tcpip_match:
            tcpip_id = tcpip_match.group(1)
            ip = tcpip_match.group(2)
            return f"{tcpip_id}:{ip}"
        
        # GPIB devices: GPIB0::1::INSTR
        gpib_match = re.search(r'(GPIB\d+)::(\d+)::', address)
        if gpib_match:
            gpib_id = gpib_match.group(1)
            addr = gpib_match.group(2)
            return f"{gpib_id}:{addr}"
        
        # If no pattern matches, return a short version of the address
        if len(address) > 20:
            return address[:17] + "..."
        return address
        
    def _refresh_devices(self):
        """Refresh the list of available devices."""
        self._device_combo.clear()
        self._device_map = {}
        
        try:
            # Use PyVISA to list available devices
            rm = pyvisa.ResourceManager()
            devices = rm.list_resources()
            
            if not devices:
                self._device_combo.addItem("No devices found")
                self._connect_button.setEnabled(False)
                return
                
            # Add devices to combo box with user-friendly names
            for address in devices:
                friendly_name = self._get_user_friendly_name(address)
                self._device_combo.addItem(friendly_name)
                self._device_map[friendly_name] = address
                
            self._connect_button.setEnabled(True)
                
        except Exception as e:
            # Error finding devices
            self._device_combo.addItem("No devices found")
            self._connect_button.setEnabled(False)
            QMessageBox.warning(self, "Device Error", f"Error finding devices: {str(e)}")
        
    def _toggle_connection(self):
        """Toggle the connection state."""
        if self._is_connected:
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
            
        # Get the actual device address
        address = self._device_map.get(friendly_name, friendly_name)
            
        # Update UI while connecting
        self._connect_button.setEnabled(False)
        self._refresh_button.setEnabled(False)
        self._status_label.setText(f"Connecting to {friendly_name}...")
        
        # Use a thread to connect without blocking the UI
        self._connection_thread = OscilloscopeConnectionThread(address)
        self._connection_thread.connection_successful.connect(self._on_connection_successful)
        self._connection_thread.connection_failed.connect(self._on_connection_failed)
        self._connection_thread.start()
    
    @Slot(object, str)
    def _on_connection_successful(self, device_obj, idn):
        """
        Handle successful connection.
        
        Args:
            device_obj: Connected device object
            idn: Device identification string
        """
        # Store device information
        self._device_object = device_obj
        self._current_device = self._device_combo.currentText()
        self._is_connected = True
        
        # Update UI
        self._connect_button.setText("Disconnect")
        self._connect_button.setProperty("class", "red")  # Change to red for disconnect
        
        # Extract just the model information from IDN string
        # IDN format is typically: Manufacturer,Model,Serial,Firmware
        device_info = self._current_device
        if idn and "," in idn:
            idn_parts = idn.split(",")
            if len(idn_parts) >= 2:
                model = idn_parts[1].strip()
                device_info = model
            
        self._status_label.setText(f"Connected: {device_info}")
        self._device_combo.setEnabled(False)
        self._refresh_button.setEnabled(False)
        self._connect_button.setEnabled(True)
        
        # Force style sheet update
        self._connect_button.style().unpolish(self._connect_button)
        self._connect_button.style().polish(self._connect_button)
        
        # Emit connection status
        self.connection_status_changed.emit(True, idn)
    
    @Slot(str, list)
    def _on_connection_failed(self, error_msg, available_devices):
        """
        Handle failed connection.
        
        Args:
            error_msg: Error message
            available_devices: List of available devices
        """
        # Update UI
        self._connect_button.setEnabled(True)
        self._refresh_button.setEnabled(True)
        self._status_label.setText(f"Connection failed: {error_msg}")
        
        # Show error message to user
        QMessageBox.warning(
            self,
            "Connection Error",
            f"Failed to connect to the device: {error_msg}"
        )
            
    def _disconnect(self):
        """Disconnect from the current device."""
        if self._device_object:
            try:
                # Return to local control if possible
                try:
                    self._device_object.write(":KEY:FORC")
                except:
                    pass
                
                # Close the connection
                self._device_object.close()
            except Exception as e:
                QMessageBox.warning(self, "Disconnect Error", f"Error disconnecting: {str(e)}")
        
        # Reset state
        self._is_connected = False
        self._current_device = None
        self._device_object = None
        
        # Update UI
        self._connect_button.setText("Connect")
        self._connect_button.setProperty("class", "green")  # Change back to green for connect
        self._status_label.setText("Not connected")
        self._device_combo.setEnabled(True)
        self._refresh_button.setEnabled(True)
        
        # Force style sheet update
        self._connect_button.style().unpolish(self._connect_button)
        self._connect_button.style().polish(self._connect_button)
        
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
    
    def get_device_object(self):
        """
        Get the device object for the connected device.
        
        Returns:
            object: PyVISA resource object for the connected device, or None if not connected
        """
        return self._device_object
        
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
        
    def closeEvent(self, event):
        """Handle panel close event to clean up resources."""
        if self._is_connected:
            self._disconnect()
        super().closeEvent(event)