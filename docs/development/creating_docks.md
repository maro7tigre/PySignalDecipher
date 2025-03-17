# Creating Dock Widgets in PySignalDecipher

This guide explains how to create new dock widgets for PySignalDecipher using the template-based system.

## Overview

Dock widgets in PySignalDecipher are modular UI components that can be added to workspaces. They provide specialized functionality like signal visualization, spectrum analysis, protocol decoding, etc.

The docking system has been designed to make it easy to create new dock widgets with minimal code duplication. By following a few simple steps, you can create a new dock widget that integrates seamlessly with the rest of the application.

## Step 1: Create a New Dock Widget File

To create a new dock widget:

1. Navigate to the `ui/docking/dock_types/` directory
2. Copy the `dock_template.py` file (or an existing dock that's similar to what you want to create)
3. Rename the file to match your dock widget type (e.g., `my_analyzer_dock.py`)

## Step 2: Customize the Dock Widget Class

Open your new file and:

1. Rename the class to match your dock widget type (e.g., `MyAnalyzerDock`)
2. Update the docstring to describe your dock's purpose
3. Define any signals your dock needs to communicate with other components
4. Modify the initialization code to set up dock-specific properties
5. Import it and register it in `ui/docking/dock_manager.py`
```python
# ui/docking/dock_manager.py
class DockManager(QObject):
    def _discover_dock_types(self) -> None:
        #...
        from .my_analyzer_dock import MyAnalyzerDock
        DockRegistry.register_dock_type("my_analyzer", MyAnalyzerDock)
```

Example:

```python
class MyAnalyzerDock(DockableWidget):
    """
    Dock widget for my custom analyzer.
    
    Provides analysis of signal data with custom visualization.
    """
    
    # Signal emitted when analysis results change
    analysis_changed = Signal(object)
    
    def __init__(self, title="My Analyzer", parent=None, widget_id=None):
        # Generate a widget ID if not provided
        if widget_id is None:
            import uuid
            widget_id = f"my_analyzer_{str(uuid.uuid4())[:8]}"
            
        super().__init__(title, parent, widget_id)
        
        # Initialize dock-specific properties
        self._settings = {
            "parameter1": 100,
            "parameter2": "value"
        }
        
        # Set up the content widget
        self._setup_content()
```

## Step 3: Implement the Content Widget

The most important method to customize is `_setup_content()`, which creates the UI for your dock:

```python
def _setup_content(self):
    """Set up the content widget for my analyzer."""
    # Create a layout for the content widget
    layout = QVBoxLayout(self._content_widget)
    layout.setContentsMargins(8, 8, 8, 8)
    
    # Add your UI components here
    parameter_label = QLabel("Parameter 1:")
    self._parameter1_spin = QSpinBox()
    self._parameter1_spin.setRange(0, 100)
    self._parameter1_spin.setValue(self._settings["parameter1"])
    self._parameter1_spin.valueChanged.connect(self._on_parameter1_changed)
    
    # Add components to the layout
    parameter_layout = QHBoxLayout()
    parameter_layout.addWidget(parameter_label)
    parameter_layout.addWidget(self._parameter1_spin)
    layout.addLayout(parameter_layout)
    
    # Add your main visualization or content widget
    self._analyzer_view = QWidget()  # Replace with your actual widget
    layout.addWidget(self._analyzer_view, 1)  # 1 = stretch factor
```

## Step 4: Implement State Saving and Restoration

To make your dock's state persistent across application restarts, implement:

1. `save_state()` - Save your dock's state to a dictionary
2. `restore_state()` - Restore your dock's state from a dictionary

Example:

```python
def save_state(self):
    """Save the dock state for serialization."""
    # Get the base state from the parent class
    state = super().save_state()
    
    # Add dock-specific state
    state["settings"] = self._settings.copy()
    state["dock_type"] = "my_analyzer"  # Important for restoring the dock
    
    return state

def restore_state(self, state):
    """Restore the dock state from serialization."""
    # Restore the base state from the parent class
    result = super().restore_state(state)
    
    # Restore dock-specific state
    if "settings" in state:
        self._settings.update(state["settings"])
        
        # Update UI to reflect restored settings
        self._parameter1_spin.setValue(self._settings["parameter1"])
        
    return result
```

## Step 5: Add Context Menu Items (Optional)

To add dock-specific items to the context menu (right-click menu), override the `_add_context_menu_items()` method:

```python
def _add_context_menu_items(self, menu):
    """Add dock-specific items to the context menu."""
    # Add a separator before dock-specific actions
    menu.addSeparator()
    
    # Add a custom action
    analyze_action = QAction("Analyze", menu)
    analyze_action.triggered.connect(self._run_analysis)
    menu.addAction(analyze_action)
    
    # Add a submenu
    options_menu = QMenu("Options", menu)
    
    # Add items to the submenu
    option1 = QAction("Option 1", options_menu)
    option1.setCheckable(True)
    option1.setChecked(self._settings.get("option1", False))
    option1.triggered.connect(lambda checked: self._set_option("option1", checked))
    options_menu.addAction(option1)
    
    menu.addMenu(options_menu)
```

## Step 6: Define Public API Methods

Create methods that other components can use to interact with your dock:

```python
def set_data(self, data):
    """Set data to be analyzed by this dock."""
    self._data = data
    self._update_display()
    
def get_results(self):
    """Get the current analysis results."""
    return self._results
    
def run_analysis(self):
    """Run the analysis with current settings."""
    # Implementation here
    pass
```

## Automatic Registration

The dock widget will be automatically discovered and registered with the `DockManager` at application startup. There's no need to manually register it anywhere else.

## Access to Services

Your dock widget can access application-wide services through the `ServiceRegistry`:

```python
# Get theme manager
self._theme_manager = ServiceRegistry.get_theme_manager()

# Get preferences manager
self._preferences_manager = ServiceRegistry.get_preferences_manager()

# Get device manager
self._device_manager = ServiceRegistry.get_device_manager()
```

## Communication Between Docks

Docks can communicate with each other and with the workspace in several ways:

1. **Signal/Slot Connection**: Define signals in your dock that emit when interesting events occur. Other components can connect to these signals.

2. **Direct Method Calls**: Use the `DockManager` to get references to other docks:
   ```python
   # Get all docks of a specific type in the same workspace
   other_docks = ServiceRegistry.get_dock_manager().get_docks_by_type(
       self.get_workspace_type(), "other_dock_type"
   )
   
   # Call methods on those docks
   for dock in other_docks:
       dock.some_method()
   ```

3. **Through Workspace**: For more complex coordination, you can communicate through the workspace, which can act as a mediator for multiple docks.

## Example Dock Widgets

Review these example dock widgets for reference:

1. `spectrum_analyzer_dock.py` - Dock for spectrum analysis visualization
2. `settings_dock.py` - Dock for managing workspace settings
3. `data_explorer_dock.py` - Dock shows data registry capabilities


## Best Practices

1. **Keep It Focused**: Each dock should have a single, clear responsibility.
2. **Reuse Components**: Use existing UI components when possible.
3. **Handle Theme Changes**: Apply theme changes correctly by implementing `apply_theme()`.
4. **Save/Restore State**: Always implement state saving and restoration.
5. **Document Public API**: Clearly document methods intended for use by other components.
6. **Use Signals for Events**: Use Qt's signal/slot mechanism for event notification.
7. **Keep UI Responsive**: Perform heavy processing in background threads.

By following these guidelines, you can create dock widgets that integrate seamlessly with the PySignalDecipher application and provide a consistent, high-quality user experience.