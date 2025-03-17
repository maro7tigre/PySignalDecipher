# Data Sharing in PySignalDecipher

This guide explains how to use the data sharing system in PySignalDecipher to expose and access variables across components.

## Overview

The PySignalDecipher data sharing system provides a central registry where components can:

1. Register data they want to expose to other components
2. Access data provided by other components
3. Get notifications when data changes
4. Search for available data

The system is designed to make data sharing between components simple and standardized, while maintaining loose coupling between them.

## Core Concepts

### Data Registry

The `DataRegistry` is the central component of the data sharing system. It's implemented as a singleton class, so there's only one instance available throughout the application.

### Data Paths

Each piece of data in the registry is identified by a unique path in the format:

```
component_id.data_id
```

For example:
- `signal_view_1.signal_data`
- `spectrum_analyzer_1.fft_size`
- `settings.sample_rate`

### Data Providers and Consumers

- **Providers**: Components that register data in the registry
- **Consumers**: Components that access data from the registry

A component can be both a provider and a consumer.

## Basic Usage with DockableWidget

If your component extends `DockableWidget` (which most dock widgets do), you can use the built-in data registry methods:

### Registering Data (Provider)

```python
# In your dock's __init__ method or elsewhere
self.register_data(
    data_id="sample_rate",  # Will be prefixed with your widget_id
    description="Sample rate in Hz",
    initial_value=44100,
    metadata={"unit": "Hz", "min": 8000, "max": 192000}
)

# Later, update the data when it changes
self.update_data("sample_rate", 48000)
```

### Accessing Data (Consumer)

```python
# Get data from another component
sample_rate = self.get_data(
    provider_id="settings",
    data_id="sample_rate",
    default=44100  # Default value if not found
)

# Use the data
print(f"Current sample rate: {sample_rate} Hz")
```

### Subscribing to Data Changes

```python
# Subscribe to changes in data
self.subscribe_to_data(
    provider_id="settings",
    data_id="sample_rate",
    callback=self._on_sample_rate_changed
)

# Callback method
def _on_sample_rate_changed(self, data_path, new_value):
    print(f"Sample rate changed to {new_value} Hz")
    # Update UI or reconfigure processing
```

## Direct Usage of DataRegistry

If your component doesn't extend `DockableWidget`, you can use the `DataRegistry` directly:

```python
from core.data_registry import get_data_registry

# Get the data registry
registry = get_data_registry()

# Register data
registry.register_data(
    data_path="my_component.my_data",
    description="My data description",
    provider=self,
    initial_value=42
)

# Update data
registry.set_data("my_component.my_data", 43)

# Get data
value = registry.get_data("other_component.other_data", default=0)

# Subscribe to changes
registry.subscribe_to_data(
    "other_component.other_data", 
    callback=self._on_data_changed
)
```

## Advanced Features

### Custom Getters and Setters

You can provide custom getter and setter functions to control how data is accessed and updated:

```python
# Register with custom getter and setter
self.register_data(
    data_id="buffer_size",
    description="Signal buffer size",
    getter=self._get_buffer_size,
    setter=self._set_buffer_size
)

def _get_buffer_size(self):
    # Custom logic to get the current buffer size
    return self._buffer.size

def _set_buffer_size(self, size):
    # Custom logic to set the buffer size
    self._buffer.resize(size)
    # Notify subscribers (important!)
    self._data_registry._notify_data_changed(f"{self._widget_id}.buffer_size", size)
```

### Searching for Data

The data registry provides methods to search for available data:

```python
# Search for data paths containing "frequency"
matching_paths = self.search_data("frequency")

# Search with more options
matching_paths = self.search_data(
    search_term="sample",
    include_description=True,
    include_metadata=True
)

# Get all available data with metadata
all_data = self.get_available_data()
```

## Using the Data Explorer

The application includes a `DataExplorerDock` that provides a UI for:
- Browsing all available data
- Viewing data details and metadata
- Monitoring data changes in real-time
- Searching for specific data

This is useful for debugging and understanding what data is available in the system.

## Best Practices

### 1. Descriptive Data IDs

Choose clear, descriptive data IDs that indicate what the data represents:

✅ Good: `signal_data`, `sample_rate`, `fft_size`
❌ Bad: `data1`, `value`, `x`

### 2. Include Units and Constraints in Metadata

Add metadata to clarify the meaning and constraints of your data:

```python
self.register_data(
    data_id="frequency",
    description="Signal frequency",
    initial_value=1000,
    metadata={
        "unit": "Hz",
        "min": 20,
        "max": 20000,
        "scale": "log"
    }
)
```

### 3. Update Data When It Changes

Always call `update_data()` when the underlying data changes to keep the registry in sync and notify subscribers.

### 4. Use Appropriate Data Types

Choose appropriate data types for your data:
- Primitive types (int, float, bool, str) for simple values
- Lists, dictionaries, or tuples for structured data
- NumPy arrays for large numerical datasets

### 5. Clean Up When Components are Removed

Data is automatically unregistered when a dock is closed. If you're using the registry directly with non-dock components, make sure to unregister data when components are removed:

```python
def cleanup(self):
    registry = get_data_registry()
    registry.unregister_component("my_component")
```

### 6. Document Available Data

Document the data your component provides to help other developers understand what's available:

```
# Data Provided:
# - my_component.signal_data: Raw signal samples (numpy.ndarray)
# - my_component.sample_rate: Sample rate in Hz (int)
# - my_component.is_running: Whether acquisition is active (bool)
```

## Example: Setting Up Data Communication Between Docks

Here's a complete example of communication between a signal source dock and a signal viewer dock:

### Signal Source Dock

```python
class SignalSourceDock(DockableWidget):
    def __init__(self, title="Signal Source", parent=None, widget_id=None):
        super().__init__(title, parent, widget_id)
        
        # Initialize signal data
        self._signal_data = np.zeros(1024)
        self._sample_rate = 44100
        
        # Register data
        self.register_data(
            data_id="signal_data",
            description="Raw signal samples",
            getter=lambda: self._signal_data,  # Use getter to avoid copying large arrays
            metadata={"shape": self._signal_data.shape, "dtype": str(self._signal_data.dtype)}
        )
        
        self.register_data(
            data_id="sample_rate",
            description="Sample rate in Hz",
            initial_value=self._sample_rate,
            metadata={"unit": "Hz", "min": 8000, "max": 192000}
        )
        
    def generate_signal(self, frequency, amplitude):
        """Generate a new signal."""
        t = np.arange(1024) / self._sample_rate
        self._signal_data = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # Update data in registry
        self.update_data("signal_data", self._signal_data)
```

### Signal Viewer Dock

```python
class SignalViewerDock(DockableWidget):
    def __init__(self, title="Signal Viewer", parent=None, widget_id=None):
        super().__init__(title, parent, widget_id)
        
        # Set up UI
        # ...
        
        # Register our own data
        self.register_data(
            data_id="visible_range",
            description="Visible time range in seconds",
            initial_value=(0.0, 1.0)
        )
        
    def set_signal_source(self, source_id):
        """Set the signal source to display."""
        # Subscribe to signal data
        self.subscribe_to_data(
            provider_id=source_id,
            data_id="signal_data",
            callback=self._on_signal_data_changed
        )
        
        # Subscribe to sample rate
        self.subscribe_to_data(
            provider_id=source_id,
            data_id="sample_rate",
            callback=self._on_sample_rate_changed
        )
        
        # Initial data fetch
        signal_data = self.get_data(source_id, "signal_data", np.zeros(0))
        sample_rate = self.get_data(source_id, "sample_rate", 44100)
        
        # Update display
        self._update_display(signal_data, sample_rate)
        
    def _on_signal_data_changed(self, data_path, new_value):
        """Handle signal data changes."""
        sample_rate = self.get_data(
            data_path.split('.')[0],  # Extract source_id from data_path
            "sample_rate", 
            44100
        )
        
        # Update display
        self._update_display(new_value, sample_rate)
        
    def _on_sample_rate_changed(self, data_path, new_value):
        """Handle sample rate changes."""
        source_id = data_path.split('.')[0]
        signal_data = self.get_data(source_id, "signal_data", np.zeros(0))
        
        # Update display
        self._update_display(signal_data, new_value)
```

With this pattern, docks can share data and respond to changes without direct coupling between them.

## Conclusion

The data sharing system in PySignalDecipher provides a standardized way for components to expose and access variables across the project. By using this system, you can create more modular and maintainable components that work together while maintaining loose coupling.