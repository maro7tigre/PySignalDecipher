from .signal_variable import SignalVariable


class HardwareManager:
    """
    Manages hardware connections via PyVISA and integrates with the command system.
    """
    
    def __init__(self, variable_registry):
        self.variable_registry = variable_registry
        self.resource_manager = None
        self.devices = {}  # Connected devices
        self.device_variables = {}  # Variables linked to device parameters
    
    def initialize(self):
        """Initialize the hardware manager"""
        import pyvisa
        self.resource_manager = pyvisa.ResourceManager()
    
    def get_available_devices(self):
        """Get list of available devices"""
        if not self.resource_manager:
            self.initialize()
        return list(self.resource_manager.list_resources())
    
    def connect_device(self, resource_name, alias=None):
        """Connect to a device and create variables for its parameters"""
        if not self.resource_manager:
            self.initialize()
            
        try:
            # Connect to device
            device = self.resource_manager.open_resource(resource_name)
            device.timeout = 30000
            device.read_termination = '\n'
            device.write_termination = '\n'
            
            # Store device with optional alias
            device_id = alias or resource_name
            self.devices[device_id] = device
            
            # Create device-specific variables
            self._create_device_variables(device_id, device)
            
            return device_id
        except Exception as e:
            print(f"Error connecting to device: {e}")
            return None
    
    def disconnect_device(self, device_id):
        """Disconnect a device and clean up associated variables"""
        if device_id in self.devices:
            # Close connection
            try:
                self.devices[device_id].close()
            except:
                pass
            
            # Remove device
            del self.devices[device_id]
            
            # Unregister associated variables
            if device_id in self.device_variables:
                for var_id in self.device_variables[device_id]:
                    self.variable_registry.unregister_variable(var_id)
                del self.device_variables[device_id]
    
    def _create_device_variables(self, device_id, device):
        """Create variables for device parameters"""
        self.device_variables[device_id] = []
        
        # Example: create standard oscilloscope variables
        if self._is_oscilloscope(device):
            # Create common oscilloscope variables
            for channel in range(1, 5):  # Assuming 4 channels
                # Channel enable variable
                ch_enable_var = SignalVariable(
                    f"CH{channel}_ENABLE", 
                    False, 
                    device_id
                )
                self.variable_registry.register_variable(ch_enable_var)
                self.device_variables[device_id].append(ch_enable_var.id)
                
                # Subscribe to changes to update hardware
                ch_enable_var.subscribe(
                    f"{device_id}_ch{channel}_enable_hw",
                    lambda value, ch=channel: self._set_channel_enable(device_id, ch, value)
                )
                
                # Add more variables like vertical scale, coupling, etc.
    
    def _is_oscilloscope(self, device):
        """Determine if device is an oscilloscope"""
        try:
            idn = device.query("*IDN?")
            # Check for known oscilloscope manufacturers
            return any(name in idn.lower() for name in ["rigol", "tektronix", "keysight", "agilent"])
        except:
            return False
    
    def _set_channel_enable(self, device_id, channel, enable):
        """Set channel enable state on hardware"""
        if device_id in self.devices:
            device = self.devices[device_id]
            try:
                device.write(f":CHAN{channel}:DISP {'ON' if enable else 'OFF'}")
            except Exception as e:
                print(f"Error setting channel {channel} enable to {enable}: {e}")