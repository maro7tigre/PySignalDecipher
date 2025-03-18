"""
Updated hardware utility panel for PySignalDecipher with command system integration.

This module provides the utility panel for hardware connection and control
that works with the command system instead of service registry.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QGroupBox, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot

from command_system.command_manager import CommandManager
from command_system.observable import Observable, ObservableProperty
from command_system.command import CommandContext


class HardwareUtilityPanel(QWidget):
    """
    Utility panel for hardware connection and control.
    
    Provides controls for connecting to hardware devices, selecting device
    parameters, and displaying connection status. Integrated with command system.
    """
    
    # Signal for notifying connection status changes
    connection_changed = Signal(bool, str)  # connected, device_info
    
    def __init__(self, parent=None):
        """
        Initialize the hardware utility panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Command system integration
        self._command_manager = None
        self._command_context = None
        
        # Theme and device managers (will be set by set_command_manager)
        self._theme_manager = None
        self._device_manager = None
        
        # Set up the panel layout and controls
        self._setup_ui()
        
    def set_command_manager(self, command_manager):
        """
        Set the command manager for hardware operations.
        
        Args:
            command_manager: Reference to the CommandManager
        """
        self._command_manager = command_manager
        
        # Create command context
        self._command_context = CommandContext(command_manager)
        
        # Get hardware manager from command manager
        self._device_manager = command_manager.get_hardware_manager()
        
        # Get theme manager from command manager
        self._theme_manager = command_manager.get_theme_manager()
        
        # Connect to device manager signals if available
        if hasattr(self._device_manager, 'connection_status_changed'):
            self._device_manager.connection_status_changed.connect(self._on_connection_status_changed)
        
        # Populate devices list initially
        self._refresh_devices()
        
        # Apply theme if available
        if self._theme_manager:
            self.apply_theme(self._theme_manager)
        
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
        # Make sure device manager is available
        if not self._device_manager:
            self._device_combo.clear()
            self._device_combo.addItem("No devices found")
            self._connect_button.setEnabled(False)
            return
            
        self._device_combo.clear()
        
        try:
            # Get available devices from device manager
            devices = self._device_manager.get_available_devices()
            
            if not devices:
                self._device_combo.addItem("No devices found")
                self._connect_button.setEnabled(False)
                return
                
            # Add devices to combo box
            for device in devices:
                self._device_combo.addItem(device)
                
            self._connect_button.setEnabled(True)
                
        except Exception as e:
            # Error finding devices
            self._device_combo.addItem("No devices found")
            self._connect_button.setEnabled(False)
            QMessageBox.warning(self, "Device Error", f"Error finding devices: {str(e)}")
        
    def _toggle_connection(self):
        """Toggle the connection state."""
        if not self._device_manager:
            return
            
        if self._is_connected():
            # Disconnect from the current device
            self._disconnect()
        else:
            # Connect to the selected device
            self._connect_to_device()
            
    def _connect_to_device(self):
        """Connect to the selected device."""
        if not self._device_manager:
            return
            
        device_name = self._device_combo.currentText()
        if device_name == "No devices found":
            return
            
        # Update UI while connecting
        self._connect_button.setEnabled(False)
        self._refresh_button.setEnabled(False)
        self._status_label.setText(f"Connecting to {device_name}...")
        
        # Connect to the device via device manager
        device_id = self._device_manager.connect_device(device_name)
        
        if device_id:
            # Connected successfully
            self._on_connection_status_changed(True, device_id)
        else:
            # Connection failed
            self._on_connection_status_changed(False, f"Failed to connect to {device_name}")
    
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
            
            self._status_label.setText(f"Connected: {device_info}")
            self._device_combo.setEnabled(False)
            self._refresh_button.setEnabled(False)
            self._connect_button.setEnabled(True)
            
            # Force style sheet update
            self._connect_button.style().unpolish(self._connect_button)
            self._connect_button.style().polish(self._connect_button)
            
            # Emit connection changed signal
            self.connection_changed.emit(True, device_info)
        else:
            # Connection failed or disconnected
            self._connect_button.setText("Connect")
            self._connect_button.setProperty("class", "green")  # Change back to green for connect
            
            if device_info and device_info.startswith("Failed"):  # Error message
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
            
            # Emit connection changed signal
            self.connection_changed.emit(False, "")
            
    def _disconnect(self):
        """Disconnect from the current device."""
        if not self._device_manager:
            return
            
        try:
            # Find current device ID to disconnect
            connected_devices = self._device_manager.devices.keys() if hasattr(self._device_manager, 'devices') else []
            for device_id in connected_devices:
                self._device_manager.disconnect_device(device_id)
                break
            
            # Update UI
            self._on_connection_status_changed(False, "")
        except Exception as e:
            QMessageBox.warning(self, "Disconnect Error", f"Error disconnecting: {str(e)}")
        
    def _is_connected(self):
        """
        Check if a device is currently connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self._device_manager:
            return False
            
        # Check if there are any devices in the devices dictionary
        return hasattr(self._device_manager, 'devices') and bool(self._device_manager.devices)
        
    def get_current_device(self):
        """
        Get the currently connected device.
        
        Returns:
            str: Name/address of the connected device, or None if not connected
        """
        if not self._device_manager or not self._is_connected():
            return None
            
        # Return the first device ID from the devices dictionary
        connected_devices = list(self._device_manager.devices.keys()) if hasattr(self._device_manager, 'devices') else []
        return connected_devices[0] if connected_devices else None
        
    def apply_theme(self, theme_manager=None):
        """
        Apply the current theme to the hardware utility panel.
        
        Args:
            theme_manager: Optional theme manager reference
        """
        if theme_manager:
            self._theme_manager = theme_manager
        
        if not self._theme_manager:
            return
            
        # Set group box background color
        bg_color = self._theme_manager.get_color("background.secondary", "#F0F0F0")
        self._hardware_group.setStyleSheet(f"QGroupBox {{ background-color: {bg_color}; }}")
        
    def closeEvent(self, event):
        """Handle panel close event to clean up resources."""
        if self._is_connected():
            self._disconnect()
        super().closeEvent(event)