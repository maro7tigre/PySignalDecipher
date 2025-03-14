# PyVISA for Rigol DS1000Z Series: Comprehensive Guide

This guide covers everything you need to know about using PyVISA to control your Rigol DS1202ZE oscilloscope, with a focus on signal analysis, manipulation, and decryption based on frequency separation.

## Setup and Connection

### Installation
```bash
pip install pyvisa numpy matplotlib scipy
```

You'll also need the backend VISA library:
- NI-VISA: https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html

### Connecting to the Oscilloscope
```python
import pyvisa

# Create a resource manager
rm = pyvisa.ResourceManager()

# List all available devices (important for finding your oscilloscope)
print(rm.list_resources())

# Connect to the oscilloscope (use the appropriate address from the list above)
scope = rm.open_resource('USB0::0x1AB1::0x0517::DS1ZE263609367::INSTR')

# Configuration for stable communication
scope.timeout = 30000  # 30 seconds timeout for long operations
scope.read_termination = '\n'
scope.write_termination = '\n'
```

## Essential SCPI Commands for DS1000Z Series

### Channel Configuration
```python
# Enable Channel 1
scope.write(':CHAN1:DISP ON')

# Vertical scale (V/div) - affects sensitivity
scope.write(':CHAN1:SCAL 0.2')  # 200mV/division

# Vertical offset (position on screen)
scope.write(':CHAN1:OFFS 0')  # 0V offset

# Coupling (DC, AC, GND)
scope.write(':CHAN1:COUP DC')  # DC coupling includes all signal components

# Bandwidth limit (helps reduce noise)
scope.write(':CHAN1:BWL 20M')  # 20MHz bandwidth limit
scope.write(':CHAN1:BWL OFF')  # Full bandwidth
```

### Timebase Settings
```python
# Timebase scale (horizontal, s/div)
scope.write(':TIM:SCAL 0.001')  # 1ms/division

# Timebase mode (MAIN, XY, ROLL)
scope.write(':TIM:MODE MAIN')  # Main timebase mode

# Horizontal offset (position)
scope.write(':TIM:OFFS 0')  # 0s offset

# For detailed analysis, you may use delayed timebase
scope.write(':TIM:DEL:ENAB ON')  # Enable delayed timebase
scope.write(':TIM:DEL:SCAL 0.0001')  # 100μs/div for delayed timebase
scope.write(':TIM:DEL:OFFS 0')  # Delayed timebase offset
```

### Acquisition Settings
```python
# Acquisition mode (NORMal, AVERages, PEAK, HRESolution)
scope.write(':ACQ:TYPE NORM')  # Normal mode
scope.write(':ACQ:TYPE AVER')  # Average mode (reduces noise)
scope.write(':ACQ:TYPE HRES')  # High resolution mode (good for analysis)

# Number of averages (when using AVERages mode)
scope.write(':ACQ:AVER 16')  # Average 16 waveforms

# Memory depth (more points = better resolution for analysis)
scope.write(':ACQ:MDEP 12000000')  # 12M points for deep analysis
# Check your specific model's max memory depth

# Get sample rate (critical for frequency analysis)
sample_rate = float(scope.query(':ACQ:SRAT?'))
print(f"Sample rate: {sample_rate} Sa/s")
```

### Trigger Configuration
```python
# Set trigger mode (EDGE, PULSe, etc.)
scope.write(':TRIG:MODE EDGE')

# Edge trigger settings
scope.write(':TRIG:EDGE:SOUR CHAN1')  # Trigger source
scope.write(':TRIG:EDGE:LEV 0.5')     # Trigger level in volts
scope.write(':TRIG:EDGE:SLOP POS')    # Trigger on rising edge

# Trigger coupling (important for noise rejection)
scope.write(':TRIG:COUP DC')  # DC coupling
scope.write(':TRIG:COUP LFR')  # Low-frequency rejection
scope.write(':TRIG:COUP HFR')  # High-frequency rejection

# Noise rejection for cleaner triggering
scope.write(':TRIG:NREJ ON')

# Set trigger holdoff for complex signals
scope.write(':TRIG:HOLD 0.001')  # 1ms holdoff
```

## Waveform Acquisition - Critical for Analysis

### Preparation for Data Acquisition
```python
# Stop acquisition to ensure stable data during retrieval
scope.write(':STOP')

# Waveform source selection
scope.write(':WAV:SOUR CHAN1')  # Get data from channel 1

# Waveform mode determines the data resolution
scope.write(':WAV:MODE RAW')   # Full memory depth data (best for analysis)
scope.write(':WAV:MODE NORM')  # Screen data only (faster but limited)
scope.write(':WAV:MODE MAX')   # Useful when in RUN state

# Data format (affects processing requirements)
scope.write(':WAV:FORM BYTE')  # 8-bit resolution, most efficient
scope.write(':WAV:FORM WORD')  # 16-bit resolution, more accurate
scope.write(':WAV:FORM ASC')   # ASCII format, easier parsing but inefficient
```

### Getting Waveform Scaling Parameters
```python
# Obtain the preamble - critical for correct scaling
preamble_str = scope.query(':WAV:PRE?')
preamble = preamble_str.split(',')

# Format type (BYTE, WORD, ASC)
format_type = int(preamble[0])

# Point mode (NORMal, MAX, RAW)
point_mode = int(preamble[1])

# Number of points in the data
num_points = int(preamble[2])

# Average count (for average acquisition)
avg_count = int(preamble[3])

# X-axis scaling factors
x_increment = float(preamble[4])  # Time between points
x_origin = float(preamble[5])     # First point time
x_reference = float(preamble[6])  # Referenced position

# Y-axis scaling factors - CRUCIAL for voltage calculations
y_increment = float(preamble[7])  # Voltage per level
y_origin = float(preamble[8])     # Ground level offset
y_reference = float(preamble[9])  # Reference level
```

### Retrieving Full Waveform Data
```python
import numpy as np

# For large memory depths, you'll need to read in chunks
def get_waveform_data(scope, start_pt=1, stop_pt=None, chunk_size=250000):
    """Retrieve waveform data in chunks for large memory depths"""
    
    # Get total points if not specified
    if stop_pt is None:
        points_str = scope.query(':WAV:POIN?')
        stop_pt = int(points_str.strip())
    
    # Prepare to collect all data
    all_data = []
    
    # Read data in chunks
    current_pt = start_pt
    while current_pt <= stop_pt:
        end_pt = min(current_pt + chunk_size - 1, stop_pt)
        
        # Set start and stop points for this chunk
        scope.write(f':WAV:STAR {current_pt}')
        scope.write(f':WAV:STOP {end_pt}')
        
        # Request and read data
        scope.write(':WAV:DATA?')
        chunk_data = scope.read_binary_values('B', is_big_endian=False)
        all_data.extend(chunk_data)
        
        # Move to next chunk
        current_pt = end_pt + 1
    
    return np.array(all_data)

# Get the data
raw_data = get_waveform_data(scope)

# Convert raw data to actual voltage values
voltage_values = (raw_data - y_origin - y_reference) * y_increment

# Create corresponding time array
time_values = np.arange(len(voltage_values)) * x_increment + x_origin
```

## Advanced Data Analysis for Signal Separation

### Frequency Domain Analysis with FFT
```python
from scipy import fft
import numpy as np

def analyze_frequency_content(voltage_values, sample_rate):
    """Perform FFT analysis to identify frequency components"""
    
    # Calculate FFT
    yf = fft.fft(voltage_values)
    N = len(voltage_values)
    xf = fft.fftfreq(N, 1/sample_rate)
    
    # Only take positive frequencies and normalize
    positive_freq = xf[:N//2]
    magnitude = 2.0/N * np.abs(yf[:N//2])
    
    return positive_freq, magnitude

# Get sample rate directly from oscilloscope
sample_rate = float(scope.query(':ACQ:SRAT?'))

# Analyze frequency content
frequencies, magnitudes = analyze_frequency_content(voltage_values, sample_rate)

# Find dominant frequencies
threshold = 0.05 * max(magnitudes)  # 5% of maximum amplitude
dominant_indices = np.where(magnitudes > threshold)[0]
dominant_freqs = frequencies[dominant_indices]
dominant_mags = magnitudes[dominant_indices]

print("Dominant frequencies (Hz):")
for freq, mag in zip(dominant_freqs, dominant_mags):
    print(f"{freq:.2f} Hz - Magnitude: {mag:.5f}")
```

### Signal Separation by Frequency Bands
```python
from scipy import signal

def separate_by_frequency(voltage_values, sample_rate, frequency_ranges):
    """
    Extract multiple signals by filtering into different frequency bands
    
    Args:
        voltage_values: Time-domain signal
        sample_rate: Sampling rate in Hz
        frequency_ranges: List of tuples [(low1, high1), (low2, high2), ...]
    
    Returns:
        List of separated signals corresponding to each frequency band
    """
    nyquist = 0.5 * sample_rate
    separated_signals = []
    
    for low_freq, high_freq in frequency_ranges:
        # Handle lowpass case
        if low_freq == 0:
            b, a = signal.butter(5, high_freq/nyquist, btype='low')
        # Handle highpass case
        elif high_freq >= nyquist:
            b, a = signal.butter(5, low_freq/nyquist, btype='high')
        # Bandpass for everything else
        else:
            b, a = signal.butter(5, [low_freq/nyquist, high_freq/nyquist], btype='band')
        
        # Apply filter
        filtered_signal = signal.filtfilt(b, a, voltage_values)
        separated_signals.append(filtered_signal)
    
    return separated_signals

# Define frequency bands for separation (customize based on your signal)
frequency_bands = [
    (0, 100),       # Low frequency components (0-100 Hz)
    (100, 1000),    # Mid-range (100-1000 Hz)
    (1000, 10000),  # High-frequency (1-10 kHz)
    (10000, 50000)  # Very high frequency (10-50 kHz)
]

# Separate the signal
separated_signals = separate_by_frequency(voltage_values, sample_rate, frequency_bands)

# Each element in separated_signals now contains a filtered version of the original
```

### Pattern/Symbol Recognition in Signals
```python
def detect_patterns(signal, threshold=0.5):
    """
    Simple threshold-based pattern detection
    Returns transitions that might represent symbols
    """
    # Normalize signal
    normalized = (signal - np.min(signal)) / (np.max(signal) - np.min(signal))
    
    # Find transitions
    above_threshold = normalized > threshold
    transitions = np.diff(above_threshold.astype(int))
    
    # Rising edges (0->1)
    rising_indices = np.where(transitions == 1)[0]
    
    # Falling edges (1->0)
    falling_indices = np.where(transitions == -1)[0]
    
    return rising_indices, falling_indices

# For each separated signal, detect transitions
for i, signal in enumerate(separated_signals):
    rising, falling = detect_patterns(signal)
    print(f"Band {i} - Rising edges: {len(rising)}, Falling edges: {len(falling)}")
    
    # Calculate timing between edges for pattern analysis
    if len(rising) > 1:
        time_between_rising = np.diff([time_values[idx] for idx in rising])
        print(f"Average time between symbols: {np.mean(time_between_rising):.6f} seconds")
```

## Complete Signal Processing Pipeline

```python
def process_and_analyze_channel(scope, channel=1):
    """Complete pipeline for acquiring and analyzing a signal"""
    
    # Configure the scope
    scope.write(f':CHAN{channel}:DISP ON')
    scope.write(':STOP')
    scope.write(f':WAV:SOUR CHAN{channel}')
    scope.write(':WAV:MODE RAW')
    scope.write(':WAV:FORM BYTE')
    
    # Get scaling parameters
    preamble = scope.query(':WAV:PRE?').split(',')
    x_increment = float(preamble[4])
    x_origin = float(preamble[5])
    y_increment = float(preamble[7])
    y_origin = float(preamble[8])
    y_reference = float(preamble[9])
    
    # Get data
    raw_data = get_waveform_data(scope)
    
    # Convert to voltage
    voltage_values = (raw_data - y_origin - y_reference) * y_increment
    time_values = np.arange(len(voltage_values)) * x_increment + x_origin
    
    # Get sample rate
    sample_rate = float(scope.query(':ACQ:SRAT?'))
    
    # Analyze frequency content
    frequencies, magnitudes = analyze_frequency_content(voltage_values, sample_rate)
    
    # Identify frequency bands based on peaks
    peak_indices = signal.find_peaks(magnitudes, height=0.05*max(magnitudes))[0]
    
    # Create adaptive frequency bands based on peaks
    bands = []
    for idx in peak_indices:
        center_freq = frequencies[idx]
        # Create band around each peak with ±10% width
        band_width = center_freq * 0.2  # 20% total width (±10%)
        bands.append((max(0, center_freq - band_width/2), 
                     center_freq + band_width/2))
    
    # If no significant peaks, use default bands
    if not bands:
        bands = [(0, 100), (100, 1000), (1000, 10000)]
    
    # Separate signals
    separated_signals = separate_by_frequency(voltage_values, sample_rate, bands)
    
    # Resume acquisition
    scope.write(':RUN')
    
    return {
        'time_values': time_values,
        'voltage_values': voltage_values,
        'sample_rate': sample_rate,
        'frequency_analysis': (frequencies, magnitudes),
        'frequency_bands': bands,
        'separated_signals': separated_signals
    }
```

## Signal Decryption and Advanced Techniques

### Decoding Digital Modulation
```python
def decode_amplitude_modulation(signal, time_values, carrier_freq, sample_rate):
    """Extract message from amplitude modulated signal"""
    # Create carrier wave for demodulation
    t = time_values - time_values[0]
    carrier = np.cos(2 * np.pi * carrier_freq * t)
    
    # Multiply by carrier (homodyne detection)
    demodulated = signal * carrier
    
    # Low-pass filter to extract the envelope
    nyquist = 0.5 * sample_rate
    cutoff = 0.1 * carrier_freq  # Adjust based on expected message bandwidth
    b, a = signal.butter(5, cutoff/nyquist, btype='low')
    envelope = signal.filtfilt(b, a, demodulated)
    
    return envelope
```

### Symbol Timing Recovery
```python
def extract_symbols(signal, time_values, expected_symbol_rate):
    """
    Extract digital symbols from an analog signal
    
    Args:
        signal: Demodulated signal
        time_values: Corresponding time array
        expected_symbol_rate: Approximate symbols per second
    
    Returns:
        Extracted symbols and their timing
    """
    # Normalize signal
    normalized = (signal - np.min(signal)) / (np.max(signal) - np.min(signal))
    
    # Expected samples per symbol
    samples_per_symbol = int(1.0 / (expected_symbol_rate * (time_values[1] - time_values[0])))
    
    # Simple threshold-based symbol detection
    threshold = 0.5
    binary_signal = (normalized > threshold).astype(int)
    
    # Down-sample at symbol centers
    symbols = []
    symbol_times = []
    
    for i in range(samples_per_symbol//2, len(binary_signal), samples_per_symbol):
        if i < len(binary_signal):
            symbols.append(binary_signal[i])
            symbol_times.append(time_values[i])
    
    return np.array(symbols), np.array(symbol_times)
```

## SCPI Commands Reference for Signal Analysis

### Built-in Measurement Commands
```python
# Vertical measurements
Vpp = float(scope.query(':MEAS:VAMP? CHAN1'))
Vmax = float(scope.query(':MEAS:VMAX? CHAN1'))
Vmin = float(scope.query(':MEAS:VMIN? CHAN1'))
Vavg = float(scope.query(':MEAS:VAVG? CHAN1'))

# Time measurements
freq = float(scope.query(':MEAS:FREQ? CHAN1'))
period = float(scope.query(':MEAS:PER? CHAN1'))
rise_time = float(scope.query(':MEAS:RTIM? CHAN1'))
fall_time = float(scope.query(':MEAS:FTIM? CHAN1'))

# Phase measurements between channels
phase = float(scope.query(':MEAS:PHAS? CHAN1,CHAN2'))
```

### Performing Mathematical Operations on the Scope
```python
# Enable math function
scope.write(':MATH:DISP ON')

# Addition/Subtraction
scope.write(':MATH:OPER ADD')  # Add channels
scope.write(':MATH:SOUR1 CHAN1')
scope.write(':MATH:SOUR2 CHAN2')

# FFT on the scope
scope.write(':MATH:OPER FFT')
scope.write(':MATH:FFT:SOUR CHAN1')
scope.write(':MATH:FFT:WIND HANN')  # Window type: RECT, BLAC, HANN, FLAT, TRI

# Filters (if available on your model)
scope.write(':MATH:OPER FILT')
scope.write(':MATH:FILT:TYPE LPAS')  # LPAS, HPAS, BPAS, BSTOP
scope.write(':MATH:FILT:W1 1000')    # Cutoff frequency in Hz
```

## Memory Management for Large Acquisitions

### Managing Memory Depth
```python
# Check maximum memory depth capabilities
scope.write(':ACQ:MDEP?')
max_mem_depth = scope.read()

# For long acquisitions with specific time window
# Set appropriate timebase and memory depth
scope.write(':TIM:SCAL 0.1')         # 100ms/div = 1s window (10 divisions)
scope.write(':ACQ:MDEP 12000000')    # 12M points 

# Calculate optimal settings for your needs
sample_rate = float(scope.query(':ACQ:SRAT?'))
time_window = 10 * float(scope.query(':TIM:SCAL?'))  # 10 divisions
required_points = sample_rate * time_window
print(f"Required memory depth: {required_points}")
```

### Optimizing Data Retrieval
```python
# Determine if you need all the data or can use screen data
if analysis_needs == 'high_frequency':
    scope.write(':WAV:MODE RAW')   # Get all points
else:
    scope.write(':WAV:MODE NORM')  # Get screen data only for faster acquisition
```

## Advanced Triggering for Complex Signals

### Pattern Trigger for Multi-Level Signals
```python
# Setup pattern trigger
scope.write(':TRIG:MODE PATT')
scope.write(':TRIG:PATT:PATT H,L,X,X')  # Set CH1 high, CH2 low, ignore others
```

### Duration Trigger
```python
# Trigger when a pattern lasts for specific duration
scope.write(':TRIG:MODE DUR')
scope.write(':TRIG:DUR:TYP GREA')      # Greater than specified time
scope.write(':TRIG:DUR:TLOWER 0.001')  # Pattern must last >1ms
```

### Setup and Hold Trigger
```python
# Trigger on setup/hold violations
scope.write(':TRIG:MODE SHOL')
scope.write(':TRIG:SHOL:DSRC CHAN1')  # Data source
scope.write(':TRIG:SHOL:CSRC CHAN2')  # Clock source
scope.write(':TRIG:SHOL:SLOP POS')    # Clock edge
scope.write(':TRIG:SHOL:PATT H')      # Data is high
scope.write(':TRIG:SHOL:TYP SETHOL')  # Check both setup and hold times
scope.write(':TRIG:SHOL:STIM 1.0E-9') # 1ns setup time
scope.write(':TRIG:SHOL:HTIM 1.0E-9') # 1ns hold time
```

## Practical Tips for Signal Manipulation

### Noise Reduction Techniques
```python
# On the scope:
scope.write(':ACQ:TYPE AVER')
scope.write(':ACQ:AVER 16')

# In your Python code:
def denoise_signal(signal, sample_rate, cutoff=1000):
    nyquist = 0.5 * sample_rate
    b, a = signal.butter(5, cutoff/nyquist, btype='low')
    return signal.filtfilt(b, a, signal)
```

### Signal Mixing and Extraction
```python
def mix_signals(signal1, signal2, weights=(0.5, 0.5)):
    """Mix two signals with given weights"""
    return weights[0] * signal1 + weights[1] * signal2

def extract_envelope(signal, sample_rate):
    """Extract the envelope of a modulated signal"""
    # Get the analytic signal (signal + j*hilbert(signal))
    analytic_signal = signal.hilbert(signal)
    
    # Amplitude envelope
    amplitude_envelope = np.abs(analytic_signal)
    
    # Low-pass filter for smoother envelope
    nyquist = 0.5 * sample_rate
    cutoff = 0.05 * nyquist  # Adjust based on signal
    b, a = signal.butter(3, cutoff/nyquist, btype='low')
    smooth_envelope = signal.filtfilt(b, a, amplitude_envelope)
    
    return smooth_envelope
```

## Saving and Exporting Data

### Save to Various Formats
```python
# Save raw waveform data to CSV
def save_waveform_to_csv(time_values, voltage_values, filename):
    data = np.column_stack((time_values, voltage_values))
    np.savetxt(filename, data, delimiter=',', 
               header='Time (s),Voltage (V)', comments='')

# Save all analyzed data with metadata
def save_complete_analysis(analysis_results, filename_base):
    # Save raw data
    save_waveform_to_csv(
        analysis_results['time_values'], 
        analysis_results['voltage_values'], 
        f"{filename_base}_raw.csv"
    )
    
    # Save frequency data
    freq_data = np.column_stack(analysis_results['frequency_analysis'])
    np.savetxt(f"{filename_base}_fft.csv", freq_data, delimiter=',',
               header='Frequency (Hz),Magnitude', comments='')
    
    # Save each separated signal
    for i, signal in enumerate(analysis_results['separated_signals']):
        band = analysis_results['frequency_bands'][i]
        save_waveform_to_csv(
            analysis_results['time_values'], 
            signal, 
            f"{filename_base}_band_{band[0]}-{band[1]}Hz.csv"
        )
```

### Capture Screenshots from the Oscilloscope
```python
# Save a screenshot of the current oscilloscope display
def save_screenshot(scope, filename):
    # Set image format to BMP
    scope.write(':SAVE:IMAGe:TYPE BMP')
    scope.write(':SAVE:IMAGe:INVERT OFF')
    scope.write(':SAVE:IMAGe:COLor ON')
    
    # Get the image data
    scope.write(':DISPlay:DATA?')
    raw_data = scope.read_raw()
    
    # The data includes a header we need to remove
    # Format: #9XXXXXXXXX...data... where 9 means 9 digits follow
    header_length = 11
    image_data = raw_data[header_length:-1]  # -1 to remove terminator
    
    # Save to file
    with open(filename, 'wb') as f:
        f.write(image_data)
```

## Conclusion

This guide provides all the essential PyVISA commands and techniques needed to fully control your Rigol DS1202ZE oscilloscope, acquire waveform data, and perform advanced signal analysis, separation, and decryption based on frequency components. You should now have all the tools needed to build your Tkinter application for comprehensive oscilloscope control and signal manipulation.

Remember to properly close the connection when finished:

```python
# Always close the connection to the oscilloscope when done
scope.close()
rm.close()
```