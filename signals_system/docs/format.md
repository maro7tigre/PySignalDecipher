# Signal Format System Documentation

## Overview

The Signal Format System is a flexible and extensible library for reading, writing, and manipulating signal data across different file formats. This library is designed for applications that need to work with time-series data such as sensor readings, audio signals, scientific measurements, and other sequential data.

## Key Features

- **Multiple Format Support**: Built-in support for CSV and JSON formats, with an extensible architecture for adding more formats
- **Unified Data Container**: A standard `SignalData` class to represent signals regardless of source format
- **Time Range Operations**: Filter and extract specific time ranges from signals
- **Multi-Channel Support**: Handle multi-channel signals (e.g., stereo audio, multi-sensor data)
- **Metadata Handling**: Store and retrieve metadata alongside signal values
- **Streaming Capability**: Process large signals in chunks without loading entire files into memory
- **Random Access**: Efficiently read specific time ranges from compatible formats
- **Format Registry**: Automatic format detection based on file extensions

## Installation

```bash
# Add installation instructions for your package
pip install signals-system
```

## Basic Usage

### Reading Signal Data

```python
from signals_system.formats import registry

# Automatically detect format from file extension
signal_format = registry.get_for_file("my_signal.csv")
signal_data = signal_format.read("my_signal.csv")

# Access signal properties
print(f"Number of samples: {signal_data.num_samples}")
print(f"Number of channels: {signal_data.num_channels}")
print(f"Duration: {signal_data.duration} seconds")
print(f"Sample rate: {signal_data.sample_rate} Hz")

# Access signal values
values = signal_data.values  # NumPy array
timestamps = signal_data.timestamps  # NumPy array or None
metadata = signal_data.metadata  # Dictionary
```

### Writing Signal Data

```python
import numpy as np
from signals_system.formats import registry
from signals_system.formats.base import SignalData

# Create signal data
values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
timestamps = np.array([0.0, 0.1, 0.2, 0.3, 0.4])
metadata = {
    "sample_rate": 10.0,
    "source": "sensor_1",
    "unit": "volts"
}

signal_data = SignalData(values=values, timestamps=timestamps, metadata=metadata)

# Write to file
csv_format = registry.get_format("csv")
csv_format.write("my_signal.csv", signal_data)

# Write to different format
json_format = registry.get_format("json")
json_format.write("my_signal.json", signal_data)
```

### Time Range Operations

```python
from signals_system.formats import registry
from signals_system.formats.base import TimeRange

# Read only a specific time range
time_range = TimeRange(start=1.5, end=3.2)
signal_format = registry.get_for_file("long_signal.csv")
partial_signal = signal_format.read("long_signal.csv", time_range=time_range)

# Slice an existing signal by time
full_signal = signal_format.read("long_signal.csv")
time_range = TimeRange(start=1.0, end=2.0)
sliced_signal = full_signal.time_slice(time_range)

# Slice by sample indices
first_1000_samples = full_signal.slice(0, 1000)
```

### Working with Multi-Channel Data

```python
import numpy as np
from signals_system.formats.base import SignalData

# Create multi-channel data
values = np.array([
    [1.0, 2.0, 3.0],  # Values for 3 channels at time 0
    [1.1, 2.1, 3.1],  # Values for 3 channels at time 1
    [1.2, 2.2, 3.2],  # Values for 3 channels at time 2
])
timestamps = np.array([0.0, 0.1, 0.2])

multi_channel_data = SignalData(values=values, timestamps=timestamps)
print(f"Number of channels: {multi_channel_data.num_channels}")  # 3
```

### Streaming Large Signals

```python
from signals_system.formats import registry

# Get a format that supports streaming
csv_format = registry.get_format("csv")

# Open a stream for writing
stream = csv_format.open_stream("large_signal.csv", "w")

# Write data in chunks
for chunk in generate_signal_chunks():
    csv_format.write_chunk(stream, chunk)

# Close the stream
csv_format.close_stream(stream)

# Read in chunks
stream = csv_format.open_stream("large_signal.csv", "r")
while True:
    chunk = csv_format.read_chunk(stream)
    if chunk is None:  # End of file
        break
    process_chunk(chunk)
csv_format.close_stream(stream)
```

### Extracting Metadata Only

```python
from signals_system.formats import registry

# Extract metadata without loading the entire signal
signal_format = registry.get_for_file("large_signal.csv")
metadata = signal_format.get_metadata("large_signal.csv")
print(f"Sample rate: {metadata.get('sample_rate')}")
```

## Format Capabilities

Different formats support different capabilities:

```python
from signals_system.formats import registry
from signals_system.formats.base import FormatCapability

# Find all formats that support compression
compression_formats = registry.find_with_capability(FormatCapability.COMPRESSION)

# Check if a format supports random access
csv_format = registry.get_format("csv")
if csv_format.has_capability(FormatCapability.RANDOM_ACCESS):
    # Use random access features
    pass
```

Available capabilities:
- `RANDOM_ACCESS`: Can read arbitrary time ranges efficiently
- `STREAMING`: Supports incremental writing/reading
- `COMPRESSION`: Supports data compression
- `METADATA`: Supports rich metadata
- `MULTI_CHANNEL`: Supports multiple data channels

## Format Registry

The library maintains a registry of available formats:

```python
from signals_system.formats import registry

# Get a format by name
json_format = registry.get_format("json")

# Get a format for a file extension
csv_format = registry.get_for_extension(".csv")

# Get a format for a file path
format_for_file = registry.get_for_file("my_signal.json")
```

## Creating Custom Formats

You can create custom formats by subclassing `SignalFormat`:

```python
from signals_system.formats.base import SignalFormat, SignalData, FormatCapability
from typing import List, Optional, Union, BinaryIO
from pathlib import Path

class MyCustomFormat(SignalFormat):
    @property
    def name(self) -> str:
        return "CUSTOM"
    
    @property
    def extensions(self) -> List[str]:
        return [".custom"]
    
    @property
    def capabilities(self) -> List[FormatCapability]:
        return [FormatCapability.METADATA]
    
    def read(self, source: Union[str, Path, BinaryIO], time_range=None) -> SignalData:
        # Implement reading logic
        ...
    
    def write(self, destination: Union[str, Path, BinaryIO], data: SignalData, append=False) -> None:
        # Implement writing logic
        ...

# Register your custom format
from signals_system.formats import registry
registry.register(MyCustomFormat)
```

## CSV Format Details

The CSV format stores signal data with the following structure:

```
# metadata: format=csv,version=1.0
# created_at: 2023-01-01T00:00:00.000Z
# sample_rate: 1000.0
# <other metadata key-value pairs>
timestamp,value1,value2,...
0.0,1.0,2.0,...
0.001,1.1,2.1,...
```

- Metadata is stored as comments with the `#` prefix
- First column is usually timestamps
- Subsequent columns are signal values (multiple columns for multi-channel data)

## JSON Format Details

The JSON format stores signal data with the following structure:

```json
{
    "metadata": {
        "format_version": "1.0",
        "created_at": "2023-01-01T00:00:00.000Z",
        "sample_rate": 1000.0,
        "<other metadata>"
    },
    "data": [1.0, 2.0, 3.0, ...],  // For single-channel
    // OR for multi-channel:
    "data": [[1.0, 2.0], [1.1, 2.1], ...],
    "timestamps": [0.0, 0.001, 0.002, ...]
}
```

## Use Cases

### Scientific Data Analysis

```python
from signals_system.formats import registry
from signals_system.formats.base import TimeRange
import matplotlib.pyplot as plt

# Load signal data
signal_format = registry.get_for_file("experiment_data.csv")
signal_data = signal_format.read("experiment_data.csv")

# Extract a specific experiment phase
experiment_phase = signal_data.time_slice(TimeRange(start=10.0, end=20.0))

# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(experiment_phase.timestamps, experiment_phase.values)
plt.title("Experiment Phase Analysis")
plt.xlabel("Time (s)")
plt.ylabel(f"Value ({signal_data.metadata.get('unit', 'unknown')})")
plt.grid(True)
plt.show()
```

### Data Conversion

```python
from signals_system.formats import registry

# Convert from CSV to JSON
csv_format = registry.get_format("csv")
json_format = registry.get_format("json")

signal_data = csv_format.read("signal.csv")
json_format.write("signal.json", signal_data)
```

### Real-time Data Processing

```python
from signals_system.formats import registry
import time

# Setup streaming writer
csv_format = registry.get_format("csv")
stream = csv_format.open_stream("live_data.csv", "w")

# Process data in real-time
try:
    while collect_data():
        # Get new data
        new_values, new_timestamps = get_sensor_data()
        chunk = SignalData(
            values=new_values,
            timestamps=new_timestamps,
            metadata={"source": "live_sensor"}
        )
        
        # Write chunk
        csv_format.write_chunk(stream, chunk)
        
        # Process, analyze, display, etc.
        process_latest_data(chunk)
        
        time.sleep(0.1)  # Collect at 10 Hz
finally:
    # Always close the stream
    csv_format.close_stream(stream)
```

## Advanced Features

### Signal Processing

```python
import numpy as np
from signals_system.formats import registry
from scipy import signal as spsignal

# Load signal
signal_format = registry.get_for_file("audio.csv")
audio_data = signal_format.read("audio.csv")

# Apply a filter
b, a = spsignal.butter(4, 0.2)  # 4th order lowpass filter at 0.2 times Nyquist frequency
filtered_values = spsignal.filtfilt(b, a, audio_data.values)

# Create new filtered signal
filtered_signal = SignalData(
    values=filtered_values,
    timestamps=audio_data.timestamps,
    metadata={**audio_data.metadata, "filter_applied": "butter_lowpass"}
)

# Save filtered signal
signal_format.write("audio_filtered.csv", filtered_signal)
```

### Combining Signals

```python
import numpy as np
from signals_system.formats import registry
from signals_system.formats.base import SignalData

# Load multiple signals
format1 = registry.get_for_file("signal1.csv")
format2 = registry.get_for_file("signal2.csv")

signal1 = format1.read("signal1.csv")
signal2 = format2.read("signal2.csv")

# Combine signals (assuming same timestamps)
combined_values = np.column_stack((signal1.values, signal2.values))
combined_metadata = {
    **signal1.metadata,
    "combined_from": ["signal1.csv", "signal2.csv"]
}

combined_signal = SignalData(
    values=combined_values,
    timestamps=signal1.timestamps,
    metadata=combined_metadata
)

# Write combined signal
format1.write("combined_signal.csv", combined_signal)
```

## Error Handling

```python
from signals_system.formats import registry
from signals_system.formats.base import SignalFormatError

try:
    signal_format = registry.get_for_file("signal.csv")
    signal_data = signal_format.read("signal.csv")
except KeyError:
    print("No format registered for this file extension")
except SignalFormatError as e:
    print(f"Error reading signal: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Considerations

- For large files, use streaming and random access capabilities
- When working with very large datasets, process in chunks rather than loading all at once
- CSV format is human-readable but less efficient than binary formats
- JSON format provides good metadata support but is not efficient for very large signals
- Consider implementing or using more efficient formats (HDF5, binary, etc.) for performance-critical applications

## Future Extensions

The system is designed to be extended with new formats:

- HDF5 Format (planned): For scientific data with complex hierarchical structure
- Binary Format (planned): For efficient storage and high-performance applications
- WAV Format (planned): For audio signals
- Protobuf Format (planned): For efficient serialization and cross-platform compatibility

## Conclusion

The Signal Format System provides a flexible, extensible framework for working with time-series signal data across different formats. Its unified interface simplifies format conversion, data extraction, and signal processing workflows.