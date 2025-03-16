# PySignalDecipher: Updated Project Planning Document

## 1. Project Development Approach

PySignalDecipher is being developed as a modular, extensible platform following modern software engineering principles. This document defines our development approach, including project architecture, component organization, and implementation status.

### 1.1 Development Philosophy

- **User-Centric Design**: All features prioritize the engineer's workflow and mental model
- **Progressive Disclosure**: Show simple interfaces by default, reveal complexity as needed
- **Modularity**: Maintain strong separation between system components
- **Testability**: Design components that can be tested in isolation
- **Extensibility**: Enable future additions through plugins and extension points

### 1.2 Technology Stack (IMPLEMENTED)

- **Core Language**: Python 3.9+
- **GUI Framework**: PySide6 (Qt for Python)
- **Hardware Interface**: PyVISA with appropriate backends
- **Signal Processing**: NumPy, SciPy, PyWavelets
- **Data Visualization**: PyQtGraph for performance-critical displays
- **Data Storage**: HDF5 for signal data, JSON for configurations

## 2. Core Architecture Components

### 2.1 Service Registry System (IMPLEMENTED)

The Service Registry provides centralized access to application-wide services and managers, making them available throughout the application without excessive parameter passing.

#### 2.1.1 How to Use the Service Registry

Services are initialized in `main.py` and registered with the `ServiceRegistry` class. Components can then access needed services anywhere in the application:

```python
# Initialize in main.py
ServiceRegistry.initialize(
    color_manager=color_manager,
    style_manager=style_manager,
    preferences_manager=preferences_manager,
    theme_manager=theme_manager,
    device_manager=device_manager,
    layout_manager=layout_manager,
    dock_manager=dock_manager
)

# Access in any component
from core.service_registry import ServiceRegistry

class SomeComponent:
    def __init__(self):
        self._theme_manager = ServiceRegistry.get_theme_manager()
        self._device_manager = ServiceRegistry.get_device_manager()
        self._dock_manager = ServiceRegistry.get_dock_manager()
```

#### 2.1.2 Available Services

Currently, the Service Registry provides access to:
- `ColorManager`: Manages color schemes for the application
- `StyleManager`: Handles UI style generation and application
- `ThemeManager`: Coordinates color and style changes
- `PreferencesManager`: Manages persistent user preferences
- `DeviceManager`: Handles hardware device discovery and communication
- `LayoutManager`: Manages workspace layouts and their persistence
- `DockManager`: Manages dockable widgets within workspaces

#### 2.1.3 Adding New Services

When adding new application-wide services:
1. Create the service class in the appropriate module
2. Add a reference variable and getter method in `ServiceRegistry`
3. Update the `initialize` method to accept and store the new service
4. Initialize the service in `main.py` and pass it to the registry

### 2.2 Device Management System (IMPLEMENTED)

The Device Management System provides abstraction for hardware interaction through the `DeviceManager` class.

#### 2.2.1 How to Use the DeviceManager

```python
from core.service_registry import ServiceRegistry

# Get the device manager
device_manager = ServiceRegistry.get_device_manager()

# Connect to a device
device_manager.connect_device("USB0:Device123")

# Send commands
device_manager.send_command("*IDN?")
response = device_manager.query("MEAS:VOLT?")

# Disconnect
device_manager.disconnect_device()
```

#### 2.2.2 Features

- Device discovery and connection management
- Friendly device naming system
- Asynchronous connection using QThread
- Signal-based connection status notification
- Direct command and query methods

### 2.3 Preferences Management System (IMPLEMENTED)

The `PreferencesManager` provides a centralized interface for storing and retrieving user preferences using Qt's QSettings.

#### 2.3.1 How to Use the PreferencesManager

```python
from core.service_registry import ServiceRegistry

# Get the preferences manager
prefs = ServiceRegistry.get_preferences_manager()

# Store a preference
prefs.set_preference("workspace/active_tab", 2)

# Retrieve a preference (with default)
active_tab = prefs.get_preference("workspace/active_tab", 0)

# Store and restore window state
prefs.save_window_state(window)
prefs.restore_window_state(window)
```

## 3. UI Components

### 3.1 Theme System (IMPLEMENTED)

PySignalDecipher implements a comprehensive theming system that allows full customization while providing sensible defaults.

#### 3.1.1 Key Components

- **ColorManager**: Loads colors from JSON files and provides path-based access
- **StyleManager**: Compiles Qt stylesheets based on current colors
- **ThemeManager**: Coordinates color and style changes throughout the application

#### 3.1.2 How to Use the Theme System

```python
from core.service_registry import ServiceRegistry

# Get the theme manager
theme_manager = ServiceRegistry.get_theme_manager()

# Apply theme to a component
my_component.apply_theme(theme_manager)

# Get a color
bg_color = theme_manager.get_color("background.primary")

# Set the active theme
theme_manager.set_theme("dark")
```

### 3.2 Utility Panel System (IMPLEMENTED)

The Utility Panel provides contextual tools and controls based on the active workspace and selected elements.

#### 3.2.1 Key Components

- **UtilityPanel**: Main container for utility components
- **HardwareUtilityPanel**: Controls for hardware connection and configuration
- **WorkspaceUtilityManager**: Manages workspace-specific utilities
- **WidgetUtilityManager**: Manages utilities for selected widgets

#### The BaseWorkspaceUtility class provides a standardized way to create workspace-specific utility panels with auto-layout capabilities.

#### 3.2.2 How to Use the BaseWorkspaceUtility

Extend `BaseWorkspaceUtility` to create utility panels for workspaces:

```python
from ui.utility_panel.workspace_utilities.base_workspace_utility import BaseWorkspaceUtility

class MyWorkspaceUtility(BaseWorkspaceUtility):
    def register_controls(self):
        # Add a combo box
        self.add_combo_box(
            id="my_combo",
            label="Options:",
            items=["Option 1", "Option 2", "Option 3"],
            callback=self._on_option_selected
        )
        
        # Add a button
        self.add_button(
            id="my_button",
            text="Apply",
            callback=self._on_apply_clicked
        )
        
    def _on_option_selected(self, option):
        # Handle option selection
        pass
        
    def _on_apply_clicked(self):
        # Handle button click
        pass
```

### 3.3 Tab-Based Workspace System (IMPLEMENTED)

The application implements a tab-based workspace system with specialized workspaces for different functions.

#### 3.3.1 Workspace Types

- **Basic Signal Analysis**: For fundamental signal visualization
- **Protocol Decoder**: For identifying and decoding communication protocols
- **Pattern Recognition**: For detecting and analyzing signal patterns
- **Signal Separation**: For separating mixed signals into components
- **Signal Origin**: For analyzing signal source and direction
- **Advanced Analysis**: For complex transforms and analysis

#### 3.3.2 How to Create New Workspaces

```python
from ui.workspaces.base_workspace import BaseWorkspace

class CustomWorkspace(BaseWorkspace):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def _initialize_workspace(self):
        # Add workspace-specific components
        pass
        
    def get_workspace_id(self):
        return "custom"
```

### 3.4 Docking System (IMPLEMENTED)

The application uses a flexible docking system within each workspace that allows users to arrange tools according to their workflow needs.

#### 3.4.1 Key Components

- **DockManager**: Central manager for dock widgets across the application
- **DockableWidget**: Base class for all dockable widgets with common functionality
- **SignalViewDock**: Example implementation for signal visualization

#### 3.4.2 Features

- Support for floating, docking, and tabbed arrangements of widgets
- Customizable dock appearance including color options
- Persistent state including position, size, and visibility
- Context menu for dock operations
- Workspace-specific dock management

#### 3.4.3 How to Use the Docking System

```python
from core.service_registry import ServiceRegistry

# Get the dock manager
dock_manager = ServiceRegistry.get_dock_manager()

# Create a new dock widget in a workspace
signal_view = dock_manager.create_dock(
    workspace_id="basic",
    dock_type="signal_view",
    title="Time Domain",
    area=Qt.RightDockWidgetArea
)

# Get an existing dock widget
existing_dock = dock_manager.get_dock("basic", "signal_view_1")

# Remove a dock widget
dock_manager.remove_dock("basic", "signal_view_1")

# Get all docks for a workspace
workspace_docks = dock_manager.get_docks_for_workspace("basic")
```

#### 3.4.4 Creating Custom Dock Widgets

To create a custom dock widget:

1. Create a new class that extends `DockableWidget`
2. Implement the content in `_setup_content()`
3. Register the dock type with the DockManager

```python
from ui.docking.dockable_widget import DockableWidget

class MyCustomDock(DockableWidget):
    def __init__(self, title="My Dock", parent=None, widget_id=None):
        super().__init__(title, parent, widget_id)
        
    def _setup_content(self):
        # Create and set up the content widget
        layout = QVBoxLayout(self._content_widget)
        layout.addWidget(MyCustomWidget())

# Register with dock manager
dock_manager.register_dock_type("my_custom", MyCustomDock)
```

### 3.5 Layout Management System (IMPLEMENTED)

The LayoutManager provides functionality for creating, saving, and restoring workspace layouts.

#### 3.5.1 Key Components

- **LayoutManager**: Main class for layout management
- **LayoutDefinition**: Data class representing a complete layout
- **DockWidgetState**: Data class representing dock widget state
- **LayoutManagerDialog**: Dialog for managing layouts

#### 3.5.2 Features

- Save and restore complete workspace layouts
- Default layouts for each workspace type
- User-defined layouts with custom names
- Layout persistence to files
- Dialog for managing layouts

#### 3.5.3 How to Use the Layout Manager

```python
from core.service_registry import ServiceRegistry

# Get the layout manager
layout_manager = ServiceRegistry.get_layout_manager()

# Create a new layout
layout_id = layout_manager.create_layout(
    workspace_type="basic",
    name="My Custom Layout",
    main_window=main_window,
    is_default=False
)

# Apply a layout
layout_manager.apply_layout(
    workspace_type="basic",
    layout_id=layout_id,
    main_window=main_window
)

# Get the default layout
default_layout = layout_manager.get_default_layout("basic")

# Set a layout as the default
layout_manager.set_layout_as_default("basic", layout_id)
```

## 4. Save/Export/Load/Import System (PLANNED)

### 4.1 Project Files (PLANNED)

Projects (.psd files) will serve as containers for complete work sessions:

- **Content**: Signals, configurations, analysis results, window layouts
- **Format**: HDF5-based container with JSON metadata
- **Versioning**: Schema versioning for backward compatibility

### 4.2 Component-Specific Files (PLANNED)

Individual components will be savable separately for reuse across projects:

| Component | Extension | Description | Format |
|-----------|-----------|-------------|--------|
| Signals | .sigsav | Captured or generated signals with metadata | HDF5 |
| Protocols | .proto | Protocol definitions with parameters | JSON |
| Patterns | .pattern | Signal patterns for recognition | HDF5 + JSON metadata |
| Configs | .sigconf | Device/analysis configurations | JSON |
| Layouts | .layout | Window arrangements | JSON |
| Filters | .filter | Custom signal filters | JSON + Python code |
| Theme | .sigtheme | Custom UI theme | JSON |

### 4.3 Export Formats (PLANNED)

For sharing and external use, data can be exported to standard formats:

#### 4.3.1 Signal Data Exports

- CSV, WAV, NumPy, MATLAB, HDF5, Custom Binary

#### 4.3.2 Visual Exports

- PNG/JPEG, SVG, PDF, EPS, MP4/GIF

#### 4.3.3 Analysis Results

- JSON/XML, CSV, HTML, Markdown

### 4.4 Import Capabilities (PLANNED)

The system will support importing from various sources:

#### 4.4.1 Signal Data Import

- Oscilloscope formats, Standard formats, Raw Binary, IQ Data, SDR Formats

#### 4.4.2 Protocol Definitions

- Standard Protocol Libraries, Custom Protocol Definitions, Script-Based Decoders

## 5. Signal Processing Components (PLANNED)

The core signal processing functionality will be implemented in dedicated modules:

### 5.1 Signal Representation (PLANNED)

- `SignalData` class for unified signal representation
- Metadata support for signal attributes
- Memory-efficient storage for large signals
- Streaming support for real-time analysis

### 5.2 Processing Algorithms (PLANNED)

- Filtering (time and frequency domain)
- Transforms (FFT, wavelet, Hilbert)
- Feature extraction
- Statistical analysis

### 5.3 Protocol Analysis (PLANNED)

- Protocol detection
- Decoding and interpretation
- Timing analysis
- Protocol-specific visualizations

## 6. Implementation Phases

The development of PySignalDecipher is organized into clear phases:

### Phase 1: Core Infrastructure (IN PROGRESS)
- ✅ Theme system - Complete with ColorManager, StyleManager, and ThemeManager implementations
- ✅ Preferences management system - Functional PreferencesManager for persistent settings
- ✅ Tab-based workspace system - Implemented with six specialized workspaces
- ✅ Service Registry system - Fully implemented central registry for application services
- ✅ Device Management system - Complete with connection handling and device discovery
- ✅ Utility Panel system - Implemented with specialized panels for different workspaces
- ✅ Menu system - Fully implemented with proper organization and handlers
- ✅ Docking system - Implemented with DockManager, DockableWidget, and support for layouts
- ✅ Layout management system - Complete with saving, loading, and UI for managing layouts
- 🔄 Signal data model (PLANNED) - File structure defined, implementation pending
- 🔄 Core project structure (PARTIALLY IMPLEMENTED) - Basic structure in place, needs completion

### Phase 2: Basic Functionality (PLANNED)
- 🔄 Hardware interface base classes (PARTIALLY IMPLEMENTED) - DeviceManager implemented, oscilloscope interfaces pending
- ❌ Signal acquisition from hardware - Structure defined, implementation pending
- ❌ Basic signal visualization - Framework planned, implementation pending
- ❌ Simple processing operations - Structure defined, implementation pending
- ❌ Project save/load functionality - Framework planned, implementation pending

### Phase 3: Advanced Analysis (PLANNED)
- ❌ Signal processing algorithms - Structure defined, implementation pending
- ❌ Protocol decoding framework - Structure defined, implementation pending
- ❌ Pattern recognition basics - Structure defined, implementation pending
- ❌ Multiple signal views - Structure defined, implementation pending

### Phase 4: Specialized Features (PLANNED)
- ❌ Complex trigger configurations - Not yet implemented
- ❌ Advanced protocol analysis - Not yet implemented
- ❌ Signal separation algorithms - Not yet implemented
- ❌ Pattern library management - Not yet implemented

### Phase 5: Refinement and Optimization (PLANNED)
- ❌ Performance optimizations - Not yet implemented
- ❌ User experience improvements - Not yet implemented
- ❌ Extended file format support - Not yet implemented
- ❌ Advanced reporting - Not yet implemented

## 7. Developer Guidelines

### 7.1 Using the Service Registry

When developing new components for PySignalDecipher, use the Service Registry to access shared services:

```python
from core.service_registry import ServiceRegistry

class MyComponent:
    def __init__(self):
        # Get required services
        self._theme_manager = ServiceRegistry.get_theme_manager()
        self._device_manager = ServiceRegistry.get_device_manager()
        self._preferences_manager = ServiceRegistry.get_preferences_manager()
        self._dock_manager = ServiceRegistry.get_dock_manager()
        
        # Initialize with the services
        self._setup_ui()
```

### 7.2 Theme Integration

Ensure your components properly integrate with the theme system:

```python
def apply_theme(self, theme_manager=None):
    """Apply theme to the component."""
    # Use provided theme manager or get from registry
    self._theme_manager = theme_manager or ServiceRegistry.get_theme_manager()
    
    # Apply theme to this component
    bg_color = self._theme_manager.get_color("background.primary")
    text_color = self._theme_manager.get_color("text.primary")
    self.setStyleSheet(f"background-color: {bg_color}; color: {text_color};")
    
    # Apply theme to child components
    for child in self.findChildren(BaseThemedWidget):
        if hasattr(child, 'apply_theme') and callable(child.apply_theme):
            child.apply_theme(self._theme_manager)
```

### 7.3 Utility Panel Integration

When creating workspace-specific utilities, extend `BaseWorkspaceUtility`:

```python
from ui.utility_panel.workspace_utilities.base_workspace_utility import BaseWorkspaceUtility

class MyWorkspaceUtility(BaseWorkspaceUtility):
    def register_controls(self):
        # Define controls here
        pass
```

### 7.4 Docking System Integration

When creating new dock widgets, extend `DockableWidget`:

```python
from ui.docking.dockable_widget import DockableWidget

class MyDockWidget(DockableWidget):
    def __init__(self, title="My Dock", parent=None, widget_id=None):
        super().__init__(title, parent, widget_id)
        
    def _setup_content(self):
        # Set up the dock content here
        layout = QVBoxLayout(self._content_widget)
        # Add widgets to the layout
        
    def _add_context_menu_items(self, menu):
        # Add dock-specific context menu items
        action = QAction("My Custom Action", menu)
        action.triggered.connect(self._my_custom_action)
        menu.addAction(action)
        
    def save_state(self):
        # Save dock-specific state
        state = super().save_state()
        state["my_custom_setting"] = self._my_setting
        return state
        
    def restore_state(self, state):
        # Restore dock-specific state
        result = super().restore_state(state)
        if "my_custom_setting" in state:
            self._my_setting = state["my_custom_setting"]
        return result
```

### 7.5 Using the Layout Manager

To integrate with the layout manager:

```python
from core.service_registry import ServiceRegistry

# Create a layout manager dialog
from ui.layout_manager import LayoutManagerDialog

def manage_layouts(self):
    # Get the layout manager
    layout_manager = ServiceRegistry.get_layout_manager()
    
    # Create and show the dialog
    dialog = LayoutManagerDialog(
        self,
        layout_manager,
        workspace_type="my_workspace"
    )
    dialog.exec_()
    
def save_layout(self):
    # Get the layout manager
    layout_manager = ServiceRegistry.get_layout_manager()
    
    # Create a new layout
    layout_manager.create_layout(
        workspace_type="my_workspace",
        name="My Layout",
        main_window=self._main_window
    )
```

## 8. Conclusion

This updated planning document reflects the current state of PySignalDecipher development. Significant progress has been made in implementing the core infrastructure components, with the Service Registry, Device Management system, Theme system, Utility Panel system, Docking system, and Layout Management system now fully implemented. These provide a solid foundation for the remaining components that will be developed in future phases.

Developers should refer to this document for guidance on the project structure, implementation details of existing components, and guidelines for implementing new features that integrate properly with the established architecture.