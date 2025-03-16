"""
Device Manager for PySignalDecipher.

Handles discovery, connection, and communication with hardware devices.
"""

import re
import pyvisa
from typing import Dict, List, Optional, Tuple, Any
from PySide6.QtCore import QObject, Signal, QThread


class DeviceConnectionThread(QThread):
    """Thread for connecting to devices without blocking the UI."""
    
    connection_successful = Signal(object, str)  # Signal emits device object and idn
    connection_failed = Signal(str, list)        # Signal emits error message and available devices
    
    def __init__(self, address):
        """
        Initialize device connection thread.
        
        Args:
            address (str): VISA address for the device
        """
        super().__init__()
        self._address = address
        
    def run(self):
        """Connect to the device using PyVISA."""
        rm = pyvisa.ResourceManager()
        try:
            # Open a connection to the device with appropriate settings
            device = rm.open_resource(self._address)
            
            # Configure for stable communication
            device.timeout = 30000  # 30 seconds timeout for long operations
            device.read_termination = '\n'
            device.write_termination = '\n'
            
            # Clear the device to start with a clean state
            device.write('*CLS')
            
            # Query the device for identification
            idn = device.query('*IDN?')
            self.connection_successful.emit(device, idn)
        except pyvisa.VisaIOError as e:
            # List all connected devices if there's an error
            available_devices = rm.list_resources()
            self.connection_failed.emit(str(e), available_devices)


class DeviceManager(QObject):
    """
    Manages hardware device discovery, connection, and communication.
    
    Provides high-level interface for working with hardware devices,
    abstracting away the details of the underlying communication protocol.
    """
    
    # Signal emitted when a device connection status changes
    connection_status_changed = Signal(bool, str)  # connected, device_name
    
    def __init__(self):
        """Initialize the device manager."""
        super().__init__()
        
        # Connection state
        self._is_connected = False
        self._current_device_name = None
        self._device_object = None
        
        # Map of device addresses to user-friendly names
        self._device_map = {}
        
        # Resource manager
        self._resource_manager = pyvisa.ResourceManager()
    
    def get_available_devices(self) -> List[str]:
        """
        Get a list of available devices.
        
        Returns:
            List of VISA address strings for available devices
        """
        try:
            return self._resource_manager.list_resources()
        except Exception as e:
            # Log error
            print(f"Error listing resources: {e}")
            return []
            
    def get_friendly_device_name(self, address: str) -> str:
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
    
    def get_device_map(self) -> Dict[str, str]:
        """
        Get a mapping of friendly device names to VISA addresses.
        
        Returns:
            Dictionary mapping friendly names to VISA addresses
        """
        device_map = {}
        for address in self.get_available_devices():
            friendly_name = self.get_friendly_device_name(address)
            device_map[friendly_name] = address
        
        self._device_map = device_map
        return device_map
    
    def connect_device(self, address_or_name: str) -> None:
        """
        Connect to a device.
        
        This method starts an asynchronous connection process.
        The result will be emitted via the connection_status_changed signal.
        
        Args:
            address_or_name: VISA address or friendly name of the device
        """
        # Get the actual device address if a friendly name was provided
        address = self._device_map.get(address_or_name, address_or_name)
        
        # Create a connection thread
        self._connection_thread = DeviceConnectionThread(address)
        self._connection_thread.connection_successful.connect(self._on_connection_successful)
        self._connection_thread.connection_failed.connect(self._on_connection_failed)
        self._connection_thread.start()
    
    def disconnect_device(self) -> None:
        """
        Disconnect from the current device.
        
        Closes the connection and updates the connection state.
        """
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
                # Log error
                print(f"Error disconnecting device: {e}")
        
        # Reset state
        self._is_connected = False
        self._current_device_name = None
        self._device_object = None
        
        # Emit connection status
        self.connection_status_changed.emit(False, "")
    
    def is_connected(self) -> bool:
        """
        Check if a device is currently connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected
    
    def get_current_device_name(self) -> Optional[str]:
        """
        Get the name of the currently connected device.
        
        Returns:
            str: Name of the connected device, or None if not connected
        """
        return self._current_device_name
    
    def get_device_object(self) -> Any:
        """
        Get the device object for the connected device.
        
        Returns:
            object: PyVISA resource object for the connected device, or None if not connected
        """
        return self._device_object
    
    def _on_connection_successful(self, device_obj, idn):
        """
        Handle successful connection.
        
        Args:
            device_obj: Connected device object
            idn: Device identification string
        """
        # Store device information
        self._device_object = device_obj
        self._is_connected = True
        
        # Extract device name from IDN string
        device_info = None
        if idn and "," in idn:
            idn_parts = idn.split(",")
            if len(idn_parts) >= 2:
                model = idn_parts[1].strip()
                device_info = model
                
        self._current_device_name = device_info if device_info else "Unknown Device"
        
        # Emit connection status
        self.connection_status_changed.emit(True, idn)
    
    def _on_connection_failed(self, error_msg, available_devices):
        """
        Handle failed connection.
        
        Args:
            error_msg: Error message
            available_devices: List of available devices
        """
        # Log error
        print(f"Connection failed: {error_msg}")
        
        # Update device map with available devices
        self._device_map = {}
        for address in available_devices:
            friendly_name = self.get_friendly_device_name(address)
            self._device_map[friendly_name] = address
        
        # Ensure we're marked as disconnected
        self._is_connected = False
        self._current_device_name = None
        self._device_object = None
        
        # Emit connection failed status
        self.connection_status_changed.emit(False, error_msg)
    
    def send_command(self, command: str) -> None:
        """
        Send a command to the connected device.
        
        Args:
            command: Command string to send
            
        Raises:
            RuntimeError: If no device is connected
        """
        if not self._is_connected or not self._device_object:
            raise RuntimeError("No device connected")
        
        self._device_object.write(command)
    
    def query(self, query_string: str) -> str:
        """
        Send a query to the connected device and get the response.
        
        Args:
            query_string: Query string to send
            
        Returns:
            str: Response from the device
            
        Raises:
            RuntimeError: If no device is connected
        """
        if not self._is_connected or not self._device_object:
            raise RuntimeError("No device connected")
        
        return self._device_object.query(query_string)