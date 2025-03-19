# PySignalDecipher Command System - Developer Guidelines

## Introduction

This document serves as a comprehensive guide for developing the command system for PySignalDecipher. The command system is a core component that enables undo/redo functionality, project serialization, and integration with the UI. It provides a framework for tracking all user actions and application state in a consistent manner.

## Goals and Requirements

### Primary Goals

1. **Command Pattern Implementation**: Enable tracking of all user actions as commands that can be executed, undone, and redone
2. **Observable Properties**: Provide a property system that tracks changes and integrates with the command system
3. **Project Serialization**: Support saving and loading project state, including command history
4. **UI Integration**: Streamlined binding between model properties and UI elements
5. **Modularity**: Create a self-contained system that can be easily integrated with the rest of the application

### Key Requirements

1. **Self-contained**: Minimize external dependencies while providing complete functionality
2. **Simple API**: Present a clean, simple interface that hides implementation complexity
3. **Performance**: Efficient execution, especially for frequent operations
4. **Extensibility**: Allow for custom commands and serialization formats
5. **Testability**: Easy to test in isolation and as part of the larger system

### Core Use Cases

This command system is specifically designed to handle these critical use cases:

1. **UI Parameters Management**: Robust handling of various UI widgets (QCheckBox, QComboBox, QSpinBox, etc.) with automatic command generation for changes
2. **Dock Management**: Track position, size, and state of dockable components that can be saved/restored with layouts or projects
3. **Signal Data Handling**: Efficient storage and access of large signal datasets with optimized performance for operations like zooming and scrolling
4. **Parent-Child Component Relationships**: Manage hierarchical relationships between components, ensuring proper cleanup when parent components are deleted

## Architecture Overview

The command system will follow a layered architecture:

1. **User-facing API** - Simple, clean interface for application developers
2. **Core Implementation** - Internal components that implement the required functionality
3. **Extension Points** - Interfaces for customizing and extending the system

### Component Structure

```
command_system/
├── __init__.py                # Exports public API
├── command_manager.py         # Facade and central coordinator
├── command.py                 # Command interfaces and base classes
├── observable.py              # Observable pattern implementation
├── ui/                        # UI integration
│   ├── __init__.py
│   ├── property_binding.py    # Generic property binding
│   ├── qt_bindings.py         # Qt-specific widget bindings
│   └── dock_manager.py        # Dock position/state management
├── data/                      # Data handling components
│   ├── __init__.py
│   ├── signal_data.py         # Signal data management
│   └── storage_manager.py     # Large data storage optimization
└── internal/                  # Hidden implementation details
    ├── __init__.py
    ├── command_history.py     # History tracking
    ├── registry.py            # Object registry
    ├── serialization.py       # Serialization interfaces
    └── storage/
        ├── storage_interface.py
        ├── json_storage.py
        └── hdf5_storage.py    # For signal data
```

## Implementation Phases

The command system should be implemented in these strategic phases to ensure gradual integration and immediate value:

### Phase 1: Core Command Infrastructure (2-3 weeks)

1. **Base Command Implementation**
   - Command interface and base class
   - CompoundCommand for grouping commands
   - Command history tracking

2. **Command Manager**
   - Singleton implementation
   - Execute/undo/redo functionality
   - Basic history management

3. **Basic Observable Properties**
   - Observable base class
   - ObservableProperty descriptor
   - Property change notifications

**Deliverables:**
- Working command execution with undo/redo
- Basic observable property tracking
- Simple unit tests for core functionality

### Phase 2: UI Integration (2-3 weeks)

1. **Property Binding System**
   - Generic binding interface
   - Qt widget bindings (focus on QCheckBox, QComboBox, QSpinBox, QLineEdit)
   - Automatic command generation from property changes

2. **Dock State Management**
   - Commands for dock position/size changes
   - Serialization of dock state
   - Parent-child relationship tracking

3. **Widget State Commands**
   - Specialized commands for common widget types
   - Batch command support for form updates

**Deliverables:**
- Two-way binding between models and UI
- Dock position/size management
- Widget state change tracking with undo/redo

### Phase 3: Serialization & Projects (2-3 weeks)

1. **Object Registry**
   - Object tracking by ID
   - Reference resolution during deserialization
   - Hierarchical object relationships

2. **Project Serialization**
   - Project state serialization
   - Command history serialization
   - Layout state serialization

3. **Storage Implementations**
   - JSON storage for projects
   - Optimized storage for layouts

**Deliverables:**
- Complete project save/load functionality
- Layout save/load functionality
- Command history persistence

### Phase 4: Signal Data Management (3-4 weeks)

1. **Signal Data Representation**
   - Observable signal data model
   - Efficient change tracking for large datasets
   - Signal metadata management

2. **Optimized Storage**
   - HDF5 storage implementation for signals
   - Lazy loading and chunked access
   - Memory management for large signals

3. **Signal Visualization Performance**
   - Chunk-based access strategies
   - Caching for visible regions
   - Asynchronous loading for smooth navigation

**Deliverables:**
- Memory-efficient signal handling
- Performant signal visualization
- Smooth zooming and scrolling

## Component Specifications

### 1. Command Interface

All commands must implement this interface:

```python
class Command(ABC):
    @abstractmethod
    def execute(self):
        """Execute the command."""
        pass
        
    @abstractmethod
    def undo(self):
        """Undo the command."""
        pass
        
    def redo(self):
        """Redo the command (default is to call execute)."""
        self.execute()
        
    @abstractmethod
    def serialize(self):
        """Convert to serializable state."""
        pass
        
    @classmethod
    @abstractmethod
    def deserialize(cls, state, registry):
        """Create from serialized state."""
        pass
```

### 2. Observable Properties

Observable objects track property changes:

```python
class Observable:
    def __init__(self):
        self._property_observers = {}
        self._id = str(uuid.uuid4())
        
    def add_property_observer(self, property_name, callback):
        """Add observer for property changes."""
        if property_name not in self._property_observers:
            self._property_observers[property_name] = {}
            
        observer_id = str(uuid.uuid4())
        self._property_observers[property_name][observer_id] = callback
        return observer_id
        
    def remove_property_observer(self, property_name, observer_id):
        """Remove property observer."""
        if (property_name in self._property_observers and 
            observer_id in self._property_observers[property_name]):
            del self._property_observers[property_name][observer_id]
            return True
        return False
        
    def _notify_property_changed(self, property_name, old_value, new_value):
        """Notify observers of property change."""
        if property_name in self._property_observers:
            for callback in self._property_observers[property_name].values():
                callback(property_name, old_value, new_value)
                
    def get_id(self):
        """Get unique identifier."""
        return self._id
        
    def set_id(self, id_value):
        """Set unique identifier (for deserialization)."""
        self._id = id_value
```

### 3. UI Integration

The UI integration layer provides property binding:

```python
class PropertyBinder:
    def __init__(self):
        self._bindings = {}
        self._command_manager = get_command_manager()
        
    def bind(self, model, property_name, widget, widget_property):
        """Create binding between model property and widget."""
        binding_id = f"{id(model)}:{property_name}:{id(widget)}:{widget_property}"
        
        # Create appropriate binding
        binding = self._create_binding(model, property_name, widget, widget_property)
        
        if binding:
            self._bindings[binding_id] = binding
            binding.activate()
            return binding_id
            
        return None
        
    def unbind(self, binding_id):
        """Remove binding."""
        if binding_id in self._bindings:
            self._bindings[binding_id].deactivate()
            del self._bindings[binding_id]
            return True
        return False
        
    def _create_binding(self, model, property_name, widget, widget_property):
        """Create appropriate binding based on widget type."""
        if isinstance(widget, QLineEdit) and widget_property == "text":
            return LineEditBinding(model, property_name, widget, self._command_manager)
        elif isinstance(widget, QSpinBox) and widget_property == "value":
            return SpinBoxBinding(model, property_name, widget, self._command_manager)
        elif isinstance(widget, QComboBox) and widget_property == "currentIndex":
            return ComboBoxBinding(model, property_name, widget, self._command_manager)
        elif isinstance(widget, QCheckBox) and widget_property == "checked":
            return CheckBoxBinding(model, property_name, widget, self._command_manager)
        # Add more widget types as needed
        return None
```

### 4. Dock Management

Dock management handles dock state:

```python
class DockManager:
    def __init__(self):
        self._command_manager = get_command_manager()
        self._registry = Registry.get_instance()
        self._dock_states = {}
        
    def register_dock(self, dock_id, dock_widget, parent_id=None):
        """Register a dock widget."""
        self._dock_states[dock_id] = {
            "widget": dock_widget,
            "parent_id": parent_id,
            "children": [],
            "state": {}
        }
        
        # Add as child to parent if applicable
        if parent_id and parent_id in self._dock_states:
            self._dock_states[parent_id]["children"].append(dock_id)
            
        # Register with registry
        self._registry.register_object(dock_widget, dock_id)
        
    def unregister_dock(self, dock_id):
        """Unregister a dock widget and its children."""
        if dock_id in self._dock_states:
            # Unregister children first
            for child_id in self._dock_states[dock_id]["children"]:
                self.unregister_dock(child_id)
                
            # Remove from parent's children list
            parent_id = self._dock_states[dock_id]["parent_id"]
            if parent_id and parent_id in self._dock_states:
                if dock_id in self._dock_states[parent_id]["children"]:
                    self._dock_states[parent_id]["children"].remove(dock_id)
                    
            # Unregister from registry
            self._registry.unregister_object(dock_id)
            
            # Remove state
            del self._dock_states[dock_id]
            
    def save_dock_state(self, dock_id):
        """Save the current state of a dock."""
        if dock_id in self._dock_states:
            widget = self._dock_states[dock_id]["widget"]
            self._dock_states[dock_id]["state"] = {
                "geometry": widget.saveGeometry().toBase64().data().decode('ascii'),
                "position": {
                    "x": widget.x(),
                    "y": widget.y(),
                    "width": widget.width(),
                    "height": widget.height()
                },
                "visible": widget.isVisible(),
                "floating": widget.isFloating() if hasattr(widget, "isFloating") else False
            }
            
    def restore_dock_state(self, dock_id):
        """Restore the saved state of a dock."""
        if dock_id in self._dock_states and "state" in self._dock_states[dock_id]:
            widget = self._dock_states[dock_id]["widget"]
            state = self._dock_states[dock_id]["state"]
            
            if "geometry" in state:
                from PySide6.QtCore import QByteArray
                widget.restoreGeometry(QByteArray.fromBase64(state["geometry"].encode('ascii')))
                
            if "position" in state:
                pos = state["position"]
                widget.setGeometry(pos["x"], pos["y"], pos["width"], pos["height"])
                
            if "visible" in state:
                widget.setVisible(state["visible"])
                
            if "floating" in state and hasattr(widget, "setFloating"):
                widget.setFloating(state["floating"])
                
    def serialize_layout(self):
        """Serialize the layout state of all docks."""
        layout = {}
        for dock_id, dock_data in self._dock_states.items():
            self.save_dock_state(dock_id)
            layout[dock_id] = {
                "state": dock_data["state"],
                "parent_id": dock_data["parent_id"],
                "children": dock_data["children"]
            }
        return layout
        
    def deserialize_layout(self, layout):
        """Restore layout from serialized state."""
        # First pass: Update states
        for dock_id, dock_data in layout.items():
            if dock_id in self._dock_states:
                self._dock_states[dock_id]["state"] = dock_data["state"]
                
        # Second pass: Restore states (to handle parent-child dependencies)
        for dock_id in self._dock_states:
            self.restore_dock_state(dock_id)
```

### 5. Signal Data Management

Signal data management handles large datasets:

```python
class SignalData(Observable):
    name = ObservableProperty(default="Signal")
    sample_rate = ObservableProperty(default=44100.0)
    
    def __init__(self, name="Signal", data=None, use_file_storage=True):
        super().__init__()
        self.name = name
        self._use_file_storage = use_file_storage
        self._file_path = None
        self._data_cache = None
        self._metadata = {}
        
        # If data provided, store it
        if data is not None:
            self.set_data(data)
            
    def set_data(self, data):
        """Set signal data, using file storage if enabled."""
        if self._use_file_storage:
            self._store_data_to_file(data)
        else:
            self._data_cache = data
            
    def get_data(self, start=0, end=None):
        """Get full signal data or a segment."""
        if self._use_file_storage and self._file_path:
            return self._load_data_from_file(start, end)
        else:
            if end is None:
                return self._data_cache[start:]
            else:
                return self._data_cache[start:end]
                
    def get_visible_segment(self, start_sample, end_sample, max_points=1000):
        """Get a downsampled segment for visualization."""
        data = self.get_data(start_sample, end_sample)
        
        # If too many points, downsample
        if len(data) > max_points:
            # Simple downsampling by selecting evenly spaced points
            step = len(data) // max_points
            return data[::step]
        
        return data
        
    def _store_data_to_file(self, data):
        """Store data to file using HDF5."""
        import h5py
        import numpy as np
        import tempfile
        import os
        
        # Create temp file if no file path yet
        if not self._file_path:
            temp_dir = tempfile.gettempdir()
            self._file_path = os.path.join(temp_dir, f"signal_{self.get_id()}.h5")
            
        # Write data to file
        with h5py.File(self._file_path, 'w') as f:
            # Convert to numpy array if needed
            if not isinstance(data, np.ndarray):
                data = np.array(data)
                
            # Store data with compression
            f.create_dataset('data', data=data, compression='gzip', compression_opts=9)
            
            # Store metadata
            for key, value in self._metadata.items():
                f.attrs[key] = value
                
    def _load_data_from_file(self, start=0, end=None):
        """Load data segment from file."""
        import h5py
        
        if not self._file_path:
            return None
            
        try:
            with h5py.File(self._file_path, 'r') as f:
                if 'data' in f:
                    if end is None:
                        return f['data'][start:]
                    else:
                        return f['data'][start:end]
                return None
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
            
    def get_metadata(self, key=None, default=None):
        """Get metadata."""
        if key is not None:
            return self._metadata.get(key, default)
        return self._metadata
        
    def set_metadata(self, key, value):
        """Set metadata."""
        self._metadata[key] = value
        
        # Update file if using file storage
        if self._use_file_storage and self._file_path:
            try:
                import h5py
                with h5py.File(self._file_path, 'r+') as f:
                    f.attrs[key] = value
            except Exception as e:
                print(f"Error updating metadata: {e}")
```

## UI Integration Examples

### 1. Basic Property Binding

```python
# Define a model with observable properties
class ChannelSettings(Observable):
    name = ObservableProperty(default="Channel 1")
    enabled = ObservableProperty(default=False)
    amplitude = ObservableProperty(default=1.0)
    color = ObservableProperty(default="#0000FF")
    mode = ObservableProperty(default=0)  # 0 = Normal, 1 = Inverted, 2 = Differential

# Create UI controls
name_edit = QLineEdit()
enabled_checkbox = QCheckBox("Enabled")
amplitude_spinbox = QDoubleSpinBox()
amplitude_spinbox.setRange(0.1, 10.0)
amplitude_spinbox.setSingleStep(0.1)
color_button = QPushButton()
mode_combo = QComboBox()
mode_combo.addItems(["Normal", "Inverted", "Differential"])

# Create model instance
settings = ChannelSettings()

# Create bindings
binder = PropertyBinder()
binder.bind(settings, "name", name_edit, "text")
binder.bind(settings, "enabled", enabled_checkbox, "checked")
binder.bind(settings, "amplitude", amplitude_spinbox, "value")
binder.bind(settings, "mode", mode_combo, "currentIndex")

# Color button needs custom handling
def update_color_button():
    color_button.setStyleSheet(f"background-color: {settings.color};")
    
def pick_color():
    from PySide6.QtWidgets import QColorDialog
    color = QColorDialog.getColor(QColor(settings.color))
    if color.isValid():
        cmd = ChangePropertyCommand(settings, "color", color.name())
        get_command_manager().execute(cmd)
        
color_button.clicked.connect(pick_color)
settings.add_property_observer("color", lambda _, __, ___: update_color_button())
update_color_button()  # Initial update
```

### 2. Dock Management

```python
# Create dock manager
dock_manager = DockManager()

# Create main dock widgets
channel_dock = QDockWidget("Channel Settings")
signal_dock = QDockWidget("Signal View")
spectrum_dock = QDockWidget("Spectrum")

# Register docks with manager
dock_manager.register_dock("channel_dock", channel_dock)
dock_manager.register_dock("signal_dock", signal_dock)
dock_manager.register_dock("spectrum_dock", spectrum_dock)

# Create channel settings widget
channel_settings_widget = QWidget()
layout = QVBoxLayout(channel_settings_widget)

# Create and register child docks
for i in range(4):
    channel_group = QWidget()
    channel_layout = QFormLayout(channel_group)
    
    channel_model = ChannelSettings()
    channel_model.name = f"Channel {i+1}"
    
    name_edit = QLineEdit(channel_model.name)
    enabled_check = QCheckBox("Enabled")
    
    channel_layout.addRow("Name:", name_edit)
    channel_layout.addRow(enabled_check)
    
    # Register with binding system
    binder = PropertyBinder()
    binder.bind(channel_model, "name", name_edit, "text")
    binder.bind(channel_model, "enabled", enabled_check, "checked")
    
    # Add to layout
    layout.addWidget(channel_group)
    
    # Register as child of channel dock
    dock_manager.register_dock(f"channel_{i+1}", channel_group, "channel_dock")

# Set content
channel_dock.setWidget(channel_settings_widget)

# Save layout command
class SaveLayoutCommand(Command):
    def __init__(self, layout_name):
        super().__init__()
        self.layout_name = layout_name
        self.old_layout = None
        self.new_layout = None
        
    def execute(self):
        # Save current layout state
        dock_manager = DockManager.get_instance()
        self.new_layout = dock_manager.serialize_layout()
        
        # Store in layout manager
        layout_manager = LayoutManager.get_instance()
        layout_manager.save_layout(self.layout_name, self.new_layout)
        
    def undo(self):
        if self.old_layout:
            # Restore previous layout if there was one
            layout_manager = LayoutManager.get_instance()
            dock_manager = DockManager.get_instance()
            dock_manager.deserialize_layout(self.old_layout)
            layout_manager.save_layout(self.layout_name, self.old_layout)
        else:
            # If no previous layout, remove the saved one
            layout_manager = LayoutManager.get_instance()
            layout_manager.remove_layout(self.layout_name)
            
    def serialize(self):
        return {
            "layout_name": self.layout_name,
            "old_layout": self.old_layout,
            "new_layout": self.new_layout
        }
        
    @classmethod
    def deserialize(cls, state, registry):
        cmd = cls(state["layout_name"])
        cmd.old_layout = state["old_layout"]
        cmd.new_layout = state["new_layout"]
        return cmd

# Save button action
def save_current_layout():
    from PySide6.QtWidgets import QInputDialog
    
    # Get layout name
    name, ok = QInputDialog.getText(
        None, "Save Layout", "Enter layout name:"
    )
    
    if ok and name:
        # Create and execute command
        cmd = SaveLayoutCommand(name)
        get_command_manager().execute(cmd)
```

### 3. Signal Display Integration

```python
# Signal display widget
class SignalDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = {}  # SignalData objects
        self.view_start = 0
        self.view_samples = 1000
        self.max_display_points = 2000
        
        # Timer for deferred rendering
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_display)
        
    def add_signal(self, signal_id, signal_data):
        """Add a signal to the display."""
        self.signals[signal_id] = signal_data
        
        # Observe name changes
        signal_data.add_property_observer("name", 
            lambda _, __, ___: self.update_display())
            
        self.schedule_update()
        
    def remove_signal(self, signal_id):
        """Remove a signal from the display."""
        if signal_id in self.signals:
            del self.signals[signal_id]
            self.schedule_update()
            
    def set_view_range(self, start, samples):
        """Set the visible sample range."""
        self.view_start = max(0, start)
        self.view_samples = max(100, samples)
        self.schedule_update()
        
    def schedule_update(self):
        """Schedule a deferred update to avoid too many redraws."""
        self.update_timer.start(50)  # 50ms delay
        
    def update_display(self):
        """Update the display with current signal data."""
        # This would update the actual visuals
        # For now, just print what we're doing
        for signal_id, signal in self.signals.items():
            data = signal.get_visible_segment(
                self.view_start, 
                self.view_start + self.view_samples,
                self.max_display_points
            )
            print(f"Displaying {signal.name}: {len(data)} points")
            
        # Trigger repaint
        self.update()
        
    def paintEvent(self, event):
        """Draw the signals."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw background
        painter.fillRect(self.rect(), Qt.white)
        
        # Draw each signal
        for signal_id, signal in self.signals.items():
            data = signal.get_visible_segment(
                self.view_start, 
                self.view_start + self.view_samples,
                self.max_display_points
            )
            
            if data is None or len(data) == 0:
                continue
                
            # Draw signal line
            painter.setPen(QPen(QColor(signal.get_metadata("color", "#0000FF")), 1))
            
            points = []
            x_scale = width / len(data)
            y_mid = height / 2
            
            for i, value in enumerate(data):
                x = i * x_scale
                y = y_mid - (value * (height * 0.4))  # Scale to 40% of height
                points.append(QPointF(x, y))
                
            painter.drawPolyline(points)
```

## Signal Data Handling

### Efficient Signal Data Storage

The key to efficient signal data handling is minimizing memory usage while maintaining responsive visualization. This requires:

1. **File-based Storage**: Store large signals in HDF5 files
2. **Chunked Access**: Load only visible portions of signals
3. **Downsampling**: Reduce data points for visualization
4. **Caching**: Cache recently viewed segments
5. **Asynchronous Loading**: Load data in background threads

#### Signal Data Class

```python
class SignalDataManager:
    def __init__(self):
        self._signals = {}
        self._cache = LRUCache(max_size=20)  # Cache for recently viewed segments
        
    def create_signal(self, name, data=None):
        """Create a new signal."""
        signal = SignalData(name, data)
        self._signals[signal.get_id()] = signal
        return signal
        
    def get_signal(self, signal_id):
        """Get a signal by ID."""
        return self._signals.get(signal_id)
        
    def get_visible_segment(self, signal_id, start, end, max_points=1000):
        """Get a visible segment of signal data, using cache if available."""
        # Create cache key
        cache_key = f"{signal_id}:{start}:{end}:{max_points}"
        
        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        # Get signal
        signal = self.get_signal(signal_id)
        if not signal:
            return None
            
        # Get data segment
        data = signal.get_visible_segment(start, end, max_points)
        
        # Cache result
        self._cache[cache_key] = data
        
        return data

class LRUCache:
    """Least Recently Used Cache."""
    def __init__(self, max_size=100):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
        
    def __getitem__(self, key):
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        raise KeyError(key)
        
    def __setitem__(self, key, value):
        if key in self.cache:
            # Update existing item
            self.cache[key] = value
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # Add new item
            self.cache[key] = value
            self.access_order.append(key)
            
            # Remove oldest if over size
            if len(self.cache) > self.max_size:
                oldest = self.access_order.pop(0)
                del self.cache[oldest]
                
    def __contains__(self, key):
        return key in self.cache
```

### Optimizing Signal Navigation

To ensure smooth zooming and panning:

1. **Viewport Management**: Track the visible portion of signals
2. **Progressive Loading**: Show lower resolution first, then refine
3. **Background Processing**: Load data in background threads
4. **Adaptive Sampling**: Change sampling rate based on zoom level

```python
class SignalViewport:
    def __init__(self, signal_manager):
        self.signal_manager = signal_manager
        self.visible_signals = []  # Signal IDs
        self.start_sample = 0
        self.visible_samples = 1000
        self.zoom_level = 1.0
        self.loading_thread = None
        
    def set_range(self, start, samples):
        """Set the visible sample range."""
        self.start_sample = max(0, start)
        self.visible_samples = max(100, samples)
        self.schedule_update()
        
    def zoom(self, factor, center_position=0.5):
        """Zoom in or out by a factor."""
        # Calculate center sample
        center_sample = self.start_sample + (self.visible_samples * center_position)
        
        # Calculate new visible samples
        new_visible = int(self.visible_samples / factor)
        
        # Calculate new start to maintain center
        new_start = int(center_sample - (new_visible * center_position))
        
        # Update viewport
        self.set_range(new_start, new_visible)
        self.zoom_level *= factor
        
    def pan(self, offset_percentage):
        """Pan by a percentage of visible width."""
        offset_samples = int(self.visible_samples * offset_percentage)
        new_start = max(0, self.start_sample + offset_samples)
        self.set_range(new_start, self.visible_samples)
        
    def schedule_update(self):
        """Schedule a data update in the background."""
        # Cancel any pending update
        if self.loading_thread and self.loading_thread.is_alive():
            self.loading_thread.cancel()
            
        # Start new loading thread
        self.loading_thread = threading.Thread(
            target=self._load_visible_data
        )
        self.loading_thread.daemon = True
        self.loading_thread.start()
        
    def _load_visible_data(self):
        """Load visible signal data in background."""
        # First pass - get lower resolution for immediate display
        for signal_id in self.visible_signals:
            # Use fewer points for immediate feedback
            self.signal_manager.get_visible_segment(
                signal_id, 
                self.start_sample, 
                self.start_sample + self.visible_samples,
                max_points=500  # Lower resolution
            )
            
        # Notify that low-res data is ready
        # (Would use signals/callbacks in real implementation)
        
        # Second pass - get full resolution
        for signal_id in self.visible_signals:
            # Get full resolution for final display
            self.signal_manager.get_visible_segment(
                signal_id, 
                self.start_sample, 
                self.start_sample + self.visible_samples,
                max_points=2000  # Higher resolution
            )
            
        # Notify that full data is ready
```

### Adaptive Sampling

Different zoom levels require different sampling strategies:

1. **Overview Mode**: When viewing the entire signal, use maximum downsampling (e.g., 1000 points)
2. **Navigation Mode**: When viewing large segments, use moderate downsampling (e.g., 5000 points)  
3. **Detail Mode**: When zoomed in close, show raw samples with no downsampling

```python
class AdaptiveSampler:
    """Provides adaptive sampling based on zoom level."""
    
    def __init__(self, max_display_points=2000):
        self.max_display_points = max_display_points
        
    def sample(self, data, start, end, zoom_level):
        """Sample data adaptively based on zoom level."""
        segment = data[start:end]
        segment_length = len(segment)
        
        if segment_length <= self.max_display_points:
            # Detail mode: show all samples
            return segment
            
        if zoom_level < 0.1:
            # Overview mode: maximum downsampling
            # Use min-max sampling to preserve peaks
            return self._min_max_downsample(segment, self.max_display_points)
            
        elif zoom_level < 0.5:
            # Navigation mode: moderate downsampling
            # Use more points for better fidelity
            target_points = min(segment_length, self.max_display_points * 2)
            return self._min_max_downsample(segment, target_points)
            
        else:
            # Detail mode with downsampling
            # Use standard downsampling
            step = segment_length // self.max_display_points
            return segment[::step]
            
    def _min_max_downsample(self, data, target_points):
        """
        Downsample using min-max method to preserve peaks.
        Each output point represents the min and max of a bucket.
        """
        if len(data) <= target_points:
            return data
            
        # Ensure even target for min-max pairs
        if target_points % 2 != 0:
            target_points -= 1
            
        result = []
        bucket_size = len(data) / (target_points / 2)
        
        for i in range(0, int(target_points / 2)):
            start_idx = int(i * bucket_size)
            end_idx = int((i + 1) * bucket_size)
            
            if end_idx > len(data):
                end_idx = len(data)
                
            if start_idx == end_idx:
                if start_idx < len(data):
                    result.append(data[start_idx])
                    result.append(data[start_idx])
                continue
                
            bucket = data[start_idx:end_idx]
            
            # Add min and max from each bucket
            result.append(min(bucket))
            result.append(max(bucket))
            
        return result
```

## Additional Diagrams

### Class Diagram

```
┌───────────────────┐     ┌─────────────────────┐     ┌───────────────────┐
│  CommandManager   │     │     Observable      │     │      Command      │
├───────────────────┤     ├─────────────────────┤     ├───────────────────┤
│ -_instance        │     │ -_property_observers│     │ +execute()        │
│ -_history         │     │ -_id                │     │ +undo()           │
│ -_registry        │◄────┤                     │     │ +redo()           │
├───────────────────┤     ├─────────────────────┤     │ +serialize()      │
│ +execute()        │     │ +add_observer()     │     │ +deserialize()    │
│ +undo()           │     │ +remove_observer()  │     └───────┬───────────┘
│ +redo()           │     │ +notify_changed()   │             │
│ +save_project()   │     └─────────┬───────────┘             │
│ +load_project()   │               │                         │
└─────────┬─────────┘               │                         │
          │                         │                         │
          │                 ┌───────▼───────────┐   ┌─────────▼─────────┐
          │                 │  ObservableProperty│   │  PropertyCommand  │
          │                 ├───────────────────┤   ├───────────────────┤
          │                 │ -default          │   │ -target           │
          │                 │ -name             │   │ -property_name    │
          └────────────────►│ -private_name     │   │ -old_value        │
                            ├───────────────────┤   │ -new_value        │
                            │ +__get__()        │   ├───────────────────┤
                            │ +__set__()        │   │ +execute()        │
                            └───────────────────┘   │ +undo()           │
                                                    └───────────────────┘
```

### Sequence Diagram: Property Change with UI

```
┌──────┐          ┌──────────┐          ┌──────────┐          ┌───────────┐
│ User │          │ QLineEdit │          │ Observable│          │CommandMgr │
└──┬───┘          └────┬─────┘          └─────┬─────┘          └─────┬─────┘
   │                    │                      │                      │
   │ Change text        │                      │                      │
   │ ─────────────────> │                      │                      │
   │                    │                      │                      │
   │                    │ textChanged          │                      │
   │                    │ ──────────────────────────────────────────> │
   │                    │                      │                      │
   │                    │                      │     Create command   │
   │                    │                      │ <─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
   │                    │                      │                      │
   │                    │                      │      execute()       │
   │                    │                      │ <─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
   │                    │                      │                      │
   │                    │                      │ property change      │
   │                    │ <─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │                      │
   │                    │                      │                      │
   │                    │  update display      │                      │
   │ <─ ─ ─ ─ ─ ─ ─ ─ ─ │                      │                      │
   │                    │                      │                      │
```

### State Diagram: Command History

```
              ┌─────────────────┐
              │                 │
              │  Initial State  │
              │  (Empty History)│
              │                 │
              └────────┬────────┘
                       │
                       │ execute(cmd1)
                       ▼
              ┌─────────────────┐
              │                 │          undo()
              │    Command 1    │◄───────────────┐
              │    Executed     │                │
              │                 │                │
              └────────┬────────┘                │
                       │                         │
                       │ execute(cmd2)           │
                       ▼                         │
              ┌─────────────────┐          ┌─────┴───────────┐
              │                 │  undo()  │                 │
              │    Command 2    │◄─────────┤    Command 1    │
              │    Executed     │          │    Undone       │
              │                 │          │                 │
              └────────┬────────┘          └─────┬───────────┘
                       │                         │
                       │ execute(cmd3)           │ redo()
                       │                         │
                       ▼                         ▼
              ┌─────────────────┐          ┌─────────────────┐
              │                 │          │                 │
              │    Command 3    │          │    Command 1    │
              │    Executed     │          │    Redone       │
              │                 │          │                 │
              └─────────────────┘          └─────────────────┘
```

### Architecture Diagram

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│                       User Interface Layer                    │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Dock Widgets│  │ Form Widgets│  │ Signal Visualizers  │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
│                                                               │
└────────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│                     Command System API Layer                  │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │PropertyBinder│ │CommandManager│ │SignalManager│           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                               │
└────────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│                  Command System Core Layer                    │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Command   │  │  Observable │  │Registry     │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │CmdHistory   │  │Serialization│  │DockManager  │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                               │
└────────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│                       Storage Layer                           │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │JsonStorage  │  │HDF5Storage  │  │FileManager  │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Best Practices and Guidelines

### Command Design Principles

1. **Single Responsibility**: Each command should do one thing well
2. **Self-Containment**: Commands should contain all data needed for execution and undo
3. **Immutability**: Command parameters should not change after creation
4. **Serializability**: All commands must support proper serialization
5. **Error Handling**: Commands should handle invalid states gracefully

### Observable Property Guidelines

1. **Minimality**: Observe only properties that need tracking
2. **Granularity**: Use fine-grained properties for precise change tracking
3. **Performance**: Avoid excessive notifications
4. **Dependencies**: Clearly document dependencies between properties
5. **Thread Safety**: Ensure thread-safe property access and notification

### UI Integration Best Practices

1. **Clean Binding**: Use declarative binding where possible
2. **Command Triggers**: Create commands in response to significant UI events
3. **UI Updates**: Update UI in response to model changes, not commands
4. **Batch Updates**: Batch multiple UI updates to prevent flicker
5. **Responsiveness**: Keep UI responsive during command execution

### Signal Data Guidelines

1. **Lazy Loading**: Load only data that is currently needed
2. **Downsampling**: Use appropriate sampling for the current view
3. **Caching**: Cache recently viewed segments
4. **Background Processing**: Process data in background threads
5. **Adaptivity**: Adjust strategies based on data size and zoom level

## Conclusion

The PySignalDecipher command system is designed to handle the complex requirements of signal processing applications, with special attention to UI parameter management, dock handling, and efficient signal data visualization. By following these guidelines, developers can create a robust, maintainable system that supports all the required functionality while providing a clean, intuitive interface for application development.

Key principles to remember:

1. **Simplicity in API Design**: Hide complexity behind clean interfaces
2. **Efficiency in Signal Handling**: Optimize for large datasets and responsive navigation
3. **Robustness in Command Processing**: Ensure reliable execution, undo, and redo
4. **Flexibility in UI Integration**: Support a wide range of UI components
5. **Scalability in Architecture**: Design for growth and extension

This phased implementation approach allows for incremental development and testing, with each phase building on the previous one to deliver a complete, integrated command system.