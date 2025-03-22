# PySignalDecipher Serialization and Project Management System

## Overview

The PySignalDecipher Command System implements a robust serialization and project management architecture that enables applications to save and load their state, including:

1. Observable model data
2. UI layouts
3. Dock configurations
4. Relationships between UI components

This document explores the serialization and project management components, explaining how they work together to provide a complete save/load experience.

## Core Components

The serialization system consists of several key components:

1. **ProjectSerializer**: Handles serialization/deserialization of Observable models
2. **ObservableEncoder**: Custom JSON encoder for Observable objects
3. **ProjectManager**: Coordinates save/load operations
4. **LayoutManager**: Manages UI layout serialization
5. **DockManager**: Manages dock widget serialization

## Serialization Architecture

```
                    ┌─────────────────┐
                    │  ProjectManager │
                    └───────┬─────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
        ┌────────▼─────────┐ ┌─────────▼──────────┐
        │ ProjectSerializer│ │    LayoutManager   │
        └────────┬─────────┘ └─────────┬──────────┘
                 │                     │
        ┌────────▼─────────┐ ┌─────────▼──────────┐
        │ ObservableEncoder│ │ LayoutSerialization│
        └──────────────────┘ └────────────────────┘
```

## File Breakdown

### 1. `serialization.py`

This file contains the core serialization logic for Observable models:

```python
# Key components:
class ObservableEncoder(json.JSONEncoder):
    """JSON encoder for Observable objects."""
    
    def default(self, obj):
        """Handle special object serialization."""
        if isinstance(obj, Observable):
            return self._serialize_observable(obj)
        elif isinstance(obj, date):
            return {"__type__": "date", "iso": obj.isoformat()}
        # ...

def observable_decoder(obj_dict):
    """Decoder hook for deserializing Observable objects and dates."""
    # ...
    if obj_type == "observable":
        class_path = obj_dict["__class__"]
        module_name, class_name = class_path.rsplit(".", 1)
        
        # Import the module and get the class
        module = __import__(module_name, fromlist=[class_name])
        cls = getattr(module, class_name)
        
        # Create instance and restore properties
        instance = cls()
        instance.set_id(obj_dict["id"])
        for prop_name, prop_value in obj_dict["properties"].items():
            setattr(instance, prop_name, prop_value)
```

#### Key Features:

- **ObservableEncoder**: Converts Observable objects to JSON-serializable dictionaries by:
  - Saving the class path (module + class name)
  - Saving the unique ID
  - Collecting and saving all ObservableProperty values

- **observable_decoder**: Converts JSON back to Observable objects by:
  - Importing the original class based on stored class path
  - Creating a new instance
  - Setting the unique ID
  - Restoring all property values

- **ProjectSerializer**: Static class with methods for saving/loading models:
  - Supports multiple formats (JSON, binary, XML, YAML)
  - Handles format detection from file extensions
  - Integrates with layout serialization

### 2. `project_manager.py`

Manages project operations and coordinates between model and layout systems:

```python
class ProjectManager:
    """
    Manages project save and load operations.
    """
    
    # ...
    
    def save_project(self, model: Observable, filename: Optional[str] = None, 
                    format_type: Optional[str] = None, save_layout: Optional[bool] = None) -> bool:
        # ...
        success = ProjectSerializer.save_to_file(model, filename, format_type)
        
        # Save layout if enabled and handlers are available
        if success and (save_layout if save_layout is not None else self._save_layouts):
            if self._save_layout_func:
                self._save_layout_func(filename)
        # ...
    
    def load_project(self, filename: str, format_type: Optional[str] = None,
                    load_layout: Optional[bool] = None) -> Optional[Observable]:
        # Phase 1: Load the model
        model = ProjectSerializer.load_from_file(filename, format_type)
        
        if model is not None:
            # Phase 2: Recreate application structure before loading layout
            if self._structure_recreation_func:
                self._structure_recreation_func(model)
            
            # Phase 3: Load layout if enabled
            if load_layout if load_layout is not None else self._save_layouts:
                if self._load_layout_func:
                    self._load_layout_func(filename)
        # ...
```

#### Key Features:

- **Singleton Pattern**: Provides a global access point via `get_project_manager()`
- **Model Type Registration**: Registers factories for creating different model types
- **Format Management**: Configurable serialization formats (JSON, binary, XML, YAML)
- **Phased Loading**: Loads models, recreates structure, then applies layouts
- **Layout Integration**: Coordinates with layout system for complete state persistence
- **Command Integration**: Clears command history after successful saves

### 3. `layout/layout_serialization.py`

Handles serialization of UI-specific components like dock areas:

```python
class LayoutEncoder(json.JSONEncoder):
    """JSON encoder that handles Qt-specific types."""
    
    def default(self, obj):
        # Handle Qt.DockWidgetArea
        if obj == Qt.DockWidgetArea.LeftDockWidgetArea:
            return {"__qt_type__": "DockWidgetArea", "value": "LeftDockWidgetArea"}
        # ...

def layout_decoder(obj_dict):
    """
    JSON decoder hook that handles Qt-specific types.
    """
    # Check if this is a Qt type we know how to handle
    if isinstance(obj_dict, dict) and "__qt_type__" in obj_dict:
        qt_type = obj_dict["__qt_type__"]
        value = obj_dict["value"]
        
        # Handle DockWidgetArea
        if qt_type == "DockWidgetArea":
            if value == "LeftDockWidgetArea":
                return Qt.DockWidgetArea.LeftDockWidgetArea
            # ...
```

#### Key Features:

- **Custom Qt Type Handling**: Serializes Qt-specific objects like DockWidgetArea and Orientation
- **Layout-Specific Codecs**: Functions to serialize and deserialize UI layout data
- **Debugging Support**: Prints debug information during deserialization

### 4. `layout/project_integration.py`

Connects the layout system with the project management system:

```python
def save_layout_with_project(filename: str) -> bool:
    """
    Save the current layout with the project file.
    
    This is done by appending a special layout section to the end of the 
    project file. The layout data is stored separately from the main project
    data to avoid affecting the command system.
    """
    # ...
    with open(filename, 'a', encoding='utf-8') as f:
        f.write("\n__LAYOUT_DATA_BEGIN__\n")
        f.write(layout_json)
        f.write("\n__LAYOUT_DATA_END__\n")
    # ...

def load_layout_from_project(filename: str) -> bool:
    """
    Load and apply layout data from a project file.
    """
    # ...
    start_marker = "__LAYOUT_DATA_BEGIN__"
    end_marker = "__LAYOUT_DATA_END__"
    
    start_pos = content.find(start_marker)
    if start_pos == -1:
        return False  # No layout data found
    # ...
```

#### Key Features:

- **Layout Storage Strategy**: Appends layout data to the end of project files with markers
- **Loading Logic**: Extracts layout data using markers and applies it to the UI
- **Registration Mechanism**: Registers layout handlers with the project manager
- **Integration Initialization**: Sets up the connection between systems automatically

### 5. `layout/layout_manager.py`

Manages UI layout capture and restoration. This is where the detailed widget-specific serialization happens:

```python
class LayoutManager:
    """
    Manages UI layout saving and restoration without affecting command history.
    """
    
    # ...
    
    def capture_current_layout(self) -> Dict[str, Any]:
        """
        Capture the current UI layout.
        """
        # Capture main window state
        layout_data = {
            "main_window": {
                "geometry": self._main_window.saveGeometry().toBase64().data().decode('ascii'),
                "state": self._main_window.saveState().toBase64().data().decode('ascii'),
                # ...
            },
            "widgets": {},
            "dock_creation_order": self._dock_creation_order.copy()
        }
        
        # Capture registered widget states
        for widget_id, widget in self._registered_widgets.items():
            widget_data = self._capture_widget_state(widget)
            if widget_data:
                layout_data["widgets"][widget_id] = widget_data
        # ...
    
    def _capture_widget_state(self, widget: QWidget) -> Dict[str, Any]:
        """
        Capture the state of a specific widget.
        """
        # Basic widget data
        widget_data = {
            "type": widget.__class__.__name__,
            "geometry": {
                "x": widget.x(),
                "y": widget.y(),
                "width": widget.width(),
                "height": widget.height()
            },
            "visible": widget.isVisible()
        }
        
        # Special handling for different widget types
        if isinstance(widget, QSplitter):
            widget_data["splitter"] = {
                "sizes": widget.sizes()
            }
        elif isinstance(widget, QTabWidget):
            widget_data["tabs"] = {
                "current": widget.currentIndex(),
                "count": widget.count(),
                "tab_names": [widget.tabText(i) for i in range(widget.count())]
            }
        elif isinstance(widget, QDockWidget):
            widget_data["dock"] = {
                "floating": widget.isFloating(),
                "area": self._get_dock_area(widget),
                "object_name": widget.objectName()
            }
            
        return widget_data
```

#### Key Features:

- **Widget State Capture**: Captures properties of registered widgets (position, size, state)
- **Widget Hierarchy**: Tracks parent-child relationships between widgets
- **Scaled Restoration**: Adjusts layouts proportionally when window sizes change
- **Tabified Dock Tracking**: Preserves dock tabification relationships
- **Widget Factory System**: Recreates missing widgets during layout restoration
- **Layout Preset System**: Saves and loads named layout configurations

## Widget Serialization Support

The system provides serialization support for multiple widget types, not just dock widgets. Each widget type receives special handling during both saving and loading:

### QSplitter Widgets

```python
# When saving:
if isinstance(widget, QSplitter):
    widget_data["splitter"] = {
        "sizes": widget.sizes()
    }

# When loading:
if isinstance(widget, QSplitter) and "splitter" in state:
    splitter_data = state["splitter"]
    
    # Scale the sizes
    original_sizes = splitter_data.get("sizes", [])
    scaled_sizes = []
    
    # Scale based on orientation
    orientation = widget.orientation()
    scale = scale_x if orientation == Qt.Orientation.Horizontal else scale_y
    
    for size in original_sizes:
        scaled_sizes.append(int(size * scale))
        
    # Apply scaled sizes
    if scaled_sizes:
        widget.setSizes(scaled_sizes)
```

### QTabWidget Widgets

```python
# When saving:
elif isinstance(widget, QTabWidget):
    widget_data["tabs"] = {
        "current": widget.currentIndex(),
        "count": widget.count(),
        "tab_names": [widget.tabText(i) for i in range(widget.count())]
    }

# When loading:
elif isinstance(widget, QTabWidget) and "tabs" in state:
    tabs_data = state["tabs"]
    
    # Set active tab
    current_tab = tabs_data.get("current", 0)
    if 0 <= current_tab < widget.count():
        widget.setCurrentIndex(current_tab)
```

### QDockWidget Widgets

```python
# When saving:
elif isinstance(widget, QDockWidget):
    widget_data["dock"] = {
        "floating": widget.isFloating(),
        "area": self._get_dock_area(widget),
        "object_name": widget.objectName()
    }

# When loading:
elif isinstance(widget, QDockWidget) and "dock" in state:
    dock_data = state["dock"]
    
    # Store object name if present
    if "object_name" in dock_data and dock_data["object_name"]:
        widget.setObjectName(dock_data["object_name"])
    
    # Set dock area
    if "area" in dock_data and not dock_data.get("floating", False):
        area = dock_data["area"]
        if area is not None and self._main_window:
            # Add to the main window
            self._main_window.addDockWidget(area, widget)
    
    # Set floating state
    if "floating" in dock_data:
        widget.setFloating(dock_data["floating"])
```

### Generic Widget Properties

All widgets also have basic properties captured:

```python
# Basic widget data captured for all widgets
widget_data = {
    "type": widget.__class__.__name__,
    "geometry": {
        "x": widget.x(),
        "y": widget.y(),
        "width": widget.width(),
        "height": widget.height()
    },
    "visible": widget.isVisible()
}
```

## Serialization Process

### Saving a Project:

1. **User invokes save**:
   ```python
   project_manager.save_project(model, "project.json")
   ```

2. **ProjectManager delegates to ProjectSerializer**:
   ```python
   success = ProjectSerializer.save_to_file(model, filename, format_type)
   ```

3. **ProjectSerializer uses ObservableEncoder**:
   ```python
   json.dump(model, f, cls=ObservableEncoder, indent=2)
   ```

4. **ObservableEncoder converts model hierarchy**:
   ```python
   # For each Observable object:
   result = {
       "__type__": "observable",
       "__class__": f"{cls.__module__}.{cls.__name__}",
       "id": obj.get_id(),
       "properties": { ... }
   }
   ```

5. **If layout saving is enabled**:
   ```python
   if save_layout:
       self._save_layout_func(filename)
   ```

6. **Layout data is appended to file**:
   ```python
   with open(filename, 'a', encoding='utf-8') as f:
       f.write("\n__LAYOUT_DATA_BEGIN__\n")
       f.write(layout_json)
       f.write("\n__LAYOUT_DATA_END__\n")
   ```

### Loading a Project:

1. **User invokes load**:
   ```python
   model = project_manager.load_project("project.json")
   ```

2. **ProjectManager delegates to ProjectSerializer**:
   ```python
   model = ProjectSerializer.load_from_file(filename, format_type)
   ```

3. **ProjectSerializer uses observable_decoder**:
   ```python
   json.loads(content, object_hook=observable_decoder)
   ```

4. **observable_decoder reconstructs models**:
   ```python
   # For each Observable object:
   module = __import__(module_name, fromlist=[class_name])
   cls = getattr(module, class_name)
   instance = cls()
   instance.set_id(obj_dict["id"])
   for prop_name, prop_value in obj_dict["properties"].items():
       setattr(instance, prop_name, prop_value)
   ```

5. **Application structure is recreated**:
   ```python
   if self._structure_recreation_func:
       self._structure_recreation_func(model)
   ```

6. **Layout data is extracted and applied**:
   ```python
   layout_json = content[start_pos:end_pos].strip()
   layout_data = json.loads(layout_json)
   layout_manager.apply_layout(layout_data)
   ```

## How Layout Integration Works

The layout system and project system are separate but coordinated:

1. **Layout in Project Files**: Layout data is appended to model data with markers
2. **Two-Phase Loading**: Model is loaded first, then layout is applied
3. **Structure Recreation**: Application structure is recreated before applying layouts
4. **Widget Factory Pattern**: Missing widgets can be recreated using registered factories
5. **Coordinate Systems**: Layout scales are adjusted if window dimensions change
6. **Widget Type Handling**: Different widget types (QSplitter, QTabWidget, QDockWidget) get specialized serialization
7. **Tabification Relationships**: Tabbed dock relationships are preserved during serialization

### Widget Registration

Widgets must be registered with the layout manager to be included in serialization:

```python
# Register individual widgets
layout_manager.register_widget("main_splitter", self.main_splitter)
layout_manager.register_widget("content_splitter", self.content_splitter)
layout_manager.register_widget("top_text", self.top_text)

# Register widget factories for recreating widgets during layout restoration
layout_manager.register_widget_factory("QDockWidget", create_dock_widget_function)
```

## Special Handling

### Qt-Specific Types

Qt objects like DockWidgetArea can't be directly serialized, so they use special handling:

```python
# When saving:
if obj == Qt.DockWidgetArea.LeftDockWidgetArea:
    return {"__qt_type__": "DockWidgetArea", "value": "LeftDockWidgetArea"}

# When loading:
if qt_type == "DockWidgetArea" and value == "LeftDockWidgetArea":
    return Qt.DockWidgetArea.LeftDockWidgetArea
```

### Date and DateTime

Date and datetime objects use ISO format for serialization:

```python
# When saving:
if isinstance(obj, date):
    return {"__type__": "date", "iso": obj.isoformat()}
elif isinstance(obj, datetime):
    return {"__type__": "datetime", "iso": obj.isoformat()}

# When loading:
if obj_type == "date":
    return date.fromisoformat(obj_dict["iso"])
elif obj_type == "datetime":
    return datetime.fromisoformat(obj_dict["iso"])
```

## Format Support

The system supports multiple serialization formats:

| Format | Extension | Description |
|--------|-----------|-------------|
| JSON   | .json     | Default format, human-readable |
| Binary | .bin      | Uses Python's pickle for binary serialization |
| XML    | .xml      | XML format (partial implementation) |
| YAML   | .yaml     | YAML format (partial implementation) |

## Project Manager Lifecycle

The ProjectManager provides a complete file management lifecycle:

1. **New Project**:
   ```python
   model = project_manager.new_project("model_type")
   ```

2. **Save Project**:
   ```python
   project_manager.save_project(model, filename)
   ```

3. **Save As**:
   ```python
   project_manager.save_project(model, new_filename)
   ```

4. **Load Project**:
   ```python
   model = project_manager.load_project(filename)
   ```

5. **Check for Unsaved Changes**:
   ```python
   if cmd_manager.can_undo():
       # Prompt user about unsaved changes
   ```

## Example Usage

```python
# Get the project manager
project_manager = get_project_manager()

# Register model types
project_manager.register_model_type("document", lambda: DocumentModel())

# Set up layout integration
from command_system.layout import extend_project_manager
extend_project_manager()

# Save a project with layout
project_manager.save_project(model, "my_document.json", save_layout=True)

# Load a project with layout
loaded_model = project_manager.load_project("my_document.json", load_layout=True)
```

## UI Integration Example

The serialization system integrates with the UI through the `file_menu_demo.py` example:

```python
def _on_save_as(self):
    # Get current format and extension
    current_format = self.project_manager.get_default_format()
    extension = self.project_manager.get_default_extension()
    
    # Show file dialog
    filename, _ = QFileDialog.getSaveFileName(
        self, "Save Note", "", f"Project Files (*{extension});;All Files (*)"
    )
    
    # Add extension if not present
    if not filename.lower().endswith(extension):
        filename += extension
        
    # Save project
    if self.project_manager.save_project(self.model, filename):
        # Update window title
        self._update_window_title()
    else:
        QMessageBox.critical(self, "Error", "Failed to save the project file.")
```

## Best Practices

1. **Register Model Factories**:
   ```python
   project_manager.register_model_type("note", lambda: NoteModel())
   ```

2. **Use Default Extensions**:
   ```python
   extension = project_manager.get_default_extension()
   ```

3. **Check for Unsaved Changes**:
   ```python
   if self.cmd_manager.can_undo() and not self._confirm_discard_changes():
       return
   ```

4. **Update Window Title**:
   ```python
   if self.cmd_manager.can_undo():
       title = f"*{title}"  # Add asterisk for unsaved changes
   ```

5. **Register Structure Recreation**:
   ```python
   project_manager.register_structure_recreation_func(self._recreate_app_structure)
   ```

## Conclusion

The PySignalDecipher serialization and project management system provides a comprehensive solution for saving and loading application state, including observable models and UI layouts. By using a combination of custom JSON encoders/decoders, layout serialization, and phased loading, the system ensures that applications can save and restore their complete state.