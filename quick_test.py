import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time

# Create a resource manager
rm = pyvisa.ResourceManager()

# Replace with the correct VISA address
rigol_address = 'USB0::0x1AB1::0x0517::DS1ZE263609367::INSTR'  # Update this line

def get_waveform_data(scope, channel):
    """Get waveform data from specified channel."""
    # Set waveform source
    scope.write(f":WAV:SOUR CHAN{channel}")
    # Set waveform format to BYTE
    scope.write(":WAV:FORM BYTE")
    # Set waveform mode to NORMAL
    scope.write(":WAV:MODE NORM")
    
    # Get the waveform preamble
    preamble_str = scope.query(":WAV:PRE?")
    preamble = preamble_str.strip().split(',')
    
    print(f"Channel {channel} preamble: {preamble_str}")
    print(f"Preamble length: {len(preamble)}")
    
    try:
        # Extract scaling factors from preamble - Rigol DS1000Z series format
        # Check documentation for the exact indices if these don't work
        if len(preamble) >= 10:
            x_increment = float(preamble[4])  # Time difference between data points
            x_origin = float(preamble[5])     # First data point time
            y_reference = float(preamble[8])  # Reference position
            y_increment = float(preamble[9])  # Voltage increment per data point
            y_origin = float(preamble[9] if len(preamble) <= 10 else preamble[10])  # Voltage origin
        else:
            print("Warning: Preamble doesn't have enough elements. Using default values.")
            x_increment = 1e-6  # Default to 1μs per sample
            x_origin = 0
            y_reference = 0
            y_increment = 0.1   # Default scale 0.1V per division
            y_origin = 0
    except (ValueError, IndexError) as e:
        print(f"Error parsing preamble: {e}")
        print(f"Raw preamble: {preamble}")
        x_increment = 1e-6
        x_origin = 0
        y_reference = 0
        y_increment = 0.1
        y_origin = 0
    
    # Get the raw waveform data
    scope.write(":WAV:DATA?")
    raw_data = scope.read_raw()
    
    # Remove header bytes and the ending byte
    header_len = 11  # Standard header size for Rigol
    data = raw_data[header_len:-1]
    
    # Convert raw data to numpy array
    data_array = np.frombuffer(data, dtype=np.uint8)
    
    # Apply scaling to get voltage values
    voltages = (data_array - y_reference) * y_increment + y_origin
    
    # Generate time axis
    times = np.arange(0, len(voltages)) * x_increment + x_origin
    
    return times, voltages

try:
    # Open a connection to the oscilloscope
    rigol = rm.open_resource(rigol_address)
    print("Successfully connected to the Rigol DS1202Z-E!")

    # Optionally, you can query the oscilloscope for its identification
    idn = rigol.query('*IDN?')
    print(f"Oscilloscope ID: {idn}")
    
    # Get data from channel 1
    print("Reading data from channel 1...")
    times_ch1, voltages_ch1 = get_waveform_data(rigol, 1)
    
    # Get data from channel 2
    print("Reading data from channel 2...")
    times_ch2, voltages_ch2 = get_waveform_data(rigol, 2)
    
    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(times_ch1, voltages_ch1, label='Channel 1')
    plt.plot(times_ch2, voltages_ch2, label='Channel 2')
    plt.title('Rigol DS1202Z-E Oscilloscope Waveform')
    plt.xlabel('Time (s)')
    plt.ylabel('Voltage (V)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    # Close the connection
    rigol.close()

except pyvisa.VisaIOError as e:
    print(f"Failed to connect to the oscilloscope: {e}")
    
    # List all connected devices
    print("confirm the rigol_address availablity in the Connected devices:")
    print(rm.list_resources())