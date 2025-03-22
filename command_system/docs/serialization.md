# PySignalDecipher Serialization System

This document provides a comprehensive explanation of the serialization and project saving/loading system in the PySignalDecipher command system.

## Table of Contents

1. [Overview](#overview)
2. [Core Serialization Components](#core-serialization-components)
   - [ProjectSerializer](#projectserializer)
   - [ObservableEncoder](#observableencoder)
   - [observable_decoder](#observable_decoder)
3. [Project Management](#project-management)
   - [ProjectManager](#projectmanager)
4. [Layout Integration](#layout-integration)
   - [Layout Serialization](#layout-serialization)
   - [Project Integration](#project-integration)
5. [Special Widget Serialization](#special-widget-serialization)
   - [Dock Widget Serialization](#dock-widget-serialization)
6. [Implementation Details](#implementation-details)
   - [Saving Process](#saving-process)
   - [Loading Process](#loading-process)
7. [File Format Support](#file-format-support)
8. [Integration in Demo Applications](#integration-in-demo-applications)

## Overview

The serialization system allows saving and loading the application state, including:

- Model data (Observable objects and their properties)
- UI layouts and dock positions
- Widget configurations

The system is designed to be extensible, supporting multiple file formats and providing clean integration between the core command system and layout management.

## Core Serialization Components

### ProjectSerializer

The `ProjectSerializer` class in `serialization.py` is the main entry point for saving and loading projects:

```python
class ProjectSerializer:
    """
    Handles serialization and deserialization of project data.
    """
    # Define supported file formats
    FORMAT_JSON = "json"
    FORMAT_BINARY = "bin"
    FORMAT_XML = "xml"
    FORMAT_YAML = "yaml"
    
    # Default file extensions for each format
    DEFAULT_EXTENSIONS = {
        FORMAT_JSON: ".json",
        FORMAT_BINARY: ".bin",
        FORMAT_XML: ".xml",
        FORMAT_YAML: ".yaml"
    }
    
    # Default format
    DEFAULT_FORMAT = FORMAT_JSON
    
    @staticmethod
    def save_to_file(model: Observable, filename: str, format_type=None) -> bool:
        """
        Save a model to a file.
        """
        # Implementation details...
    
    @staticmethod
    def load_from_file(filename: str, format_type=None) -> Optional[Observable]:
        """
        Load a model from a file.
        """
        # Implementation details...
```

Key responsibilities:
- Defining supported file formats (JSON, binary, XML, YAML)
- Managing file extensions
- Providing static methods for saving and loading models
- Handling different serialization formats

### ObservableEncoder

The `ObservableEncoder` class in `serialization.py` extends `json.JSONEncoder` to handle serialization of Observable objects and special types:

```python
class ObservableEncoder(json.JSONEncoder):
    """JSON encoder for Observable objects."""
    
    def default(self, obj):
        """Handle special object serialization."""
        if isinstance(obj, Observable):
            return self._serialize_observable(obj)
        elif isinstance(obj, date):
            return {"__type__": "date", "iso": obj.isoformat()}
        elif isinstance(obj, datetime):
            return {"__type__": "datetime", "iso": obj.isoformat()}
        return super().default(obj)
        
    def _serialize_observable(self, obj: Observable) -> Dict[str, Any]:
        """Serialize an Observable object to a dictionary."""
        # Get class to find all ObservableProperty attributes
        cls = obj.__class__
        properties = {}
        
        # Store object ID
        result = {
            "__type__": "observable",
            "__class__": f"{cls.__module__}.{cls.__name__}",
            "id": obj.get_id(),
            "properties": properties
        }
        
        # Collect all observable properties
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, ObservableProperty):
                # Get property value
                value = getattr(obj, attr_name)
                properties[attr_name] = value
                
        return result
```

Key responsibilities:
- Serializing Observable objects to dictionaries
- Including class type information for reconstruction
- Preserving unique IDs
- Special handling for date and datetime objects

### observable_decoder

The `observable_decoder` function in `serialization.py` is the complementary function for deserialization:

```python
def observable_decoder(obj_dict):
    """Decoder hook for deserializing Observable objects and dates."""
    # Skip if not a dictionary
    if not isinstance(obj_dict, dict):
        return obj_dict
        
    # Check for special type markers
    if "__type__" not in obj_dict:
        return obj_dict
        
    obj_type = obj_dict["__type__"]
    
    # Handle date types
    if obj_type == "date":
        return date.fromisoformat(obj_dict["iso"])
    elif obj_type == "datetime":
        return datetime.fromisoformat(obj_dict["iso"])
    
    # Handle observable objects
    if obj_type == "observable":
        class_path = obj_dict["__class__"]
        # Import the class
        module_name, class_name = class_path.rsplit(".", 1)
        
        try:
            # Import the module and get the class
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            
            # Create instance
            instance = cls()
            
            # Set the ID
            instance.set_id(obj_dict["id"])
            
            # Set properties
            for prop_name, prop_value in obj_dict["properties"].items():
                setattr(instance, prop_name, prop_value)
                
            return instance
        except (ImportError, AttributeError) as e:
            print(f"Error deserializing {class_path}: {e}")
            return obj_dict
```

Key responsibilities:
- Reconstructing Observable objects from serialized data
- Importing the correct class dynamically
- Setting object IDs and properties
- Handling special types like dates

## Project Management

### ProjectManager

The `ProjectManager` class in `project_manager.py` provides high-level project operations:

```python
class ProjectManager:
    """
    Manages project save and load operations.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = ProjectManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the project manager."""
        # Initialization...
    
    def register_model_type(self, model_type: str, factory: Callable[[], Observable]) -> None:
        """
        Register a model factory function for creating instances of a specific model type.
        """
        self._model_factory[model_type] = factory
    
    def save_project(self, model: Observable, filename: Optional[str] = None, 
                    format_type: Optional[str] = None, save_layout: Optional[bool] = None) -> bool:
        """
        Save the project to a file.
        """
        # Implementation details...
    
    def load_project(self, filename: str, format_type: Optional[str] = None,
                    load_layout: Optional[bool] = None) -> Optional[Observable]:
        """
        Load a project from a file.
        """
        # Implementation details...
    
    def new_project(self, model_type: str) -> Optional[Observable]:
        """
        Create a new project of the specified type.
        """
        # Implementation details...
```

Key responsibilities:
- Managing project files and formats
- Handling model factories for creating new instances
- Coordinating with layout system for integrated saving
- Maintaining the current filename
- Clearing command history after save/load operations

The core save/load implementation in `ProjectManager`:

```python
def save_project(self, model: Observable, filename: Optional[str] = None, 
                format_type: Optional[str] = None, save_layout: Optional[bool] = None) -> bool:
    """
    Save the project to a file.
    """
    # Use current filename if not provided
    if filename is None:
        if self._current_filename is None:
            return False
        filename = self._current_filename
    else:
        # Update current filename
        self._current_filename = filename
        
    # Use default format if not provided
    format_type = format_type or self._default_format
        
    # Save the model
    success = ProjectSerializer.save_to_file(model, filename, format_type)
    
    # Save layout if enabled and handlers are available
    if success and (save_layout if save_layout is not None else self._save_layouts):
        if self._save_layout_func:
            try:
                self._save_layout_func(filename)
            except Exception as e:
                print(f"Warning: Failed to save layout with project: {e}")
    
    # Clear command history after successful save
    if success:
        self._command_manager.clear()
        
    return success
```

```python
def load_project(self, filename: str, format_type: Optional[str] = None,
                load_layout: Optional[bool] = None) -> Optional[Observable]:
    """
    Load a project from a file.
    """
    # Load the model
    model = ProjectSerializer.load_from_file(filename, format_type)
    
    if model is not None:
        # Update current filename
        self._current_filename = filename
        
        # Clear command history since we're loading a fresh state
        self._command_manager.clear()
        
        # Load layout if enabled and handlers are available
        if load_layout if load_layout is not None else self._save_layouts:
            if self._load_layout_func:
                try:
                    self._load_layout_func(filename)
                except Exception as e:
                    print(f"Warning: Failed to load layout from project: {e}")
    
    return model
```

## Layout Integration

### Layout Serialization

The layout system has its own serialization mechanisms in `layout_serialization.py`:

```python
class LayoutEncoder(json.JSONEncoder):
    """JSON encoder that handles Qt-specific types."""
    
    def default(self, obj):
        # Handle Qt.DockWidgetArea
        if obj == Qt.DockWidgetArea.LeftDockWidgetArea:
            return {"__qt_type__": "DockWidgetArea", "value": "LeftDockWidgetArea"}
        # More Qt types handling...
        
        # Let the base class handle everything else
        return super().default(obj)


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
            # Other areas...
                
        # Handle Orientation
        elif qt_type == "Orientation":
            # Orientation handling...
```

Key responsibilities:
- Serializing Qt-specific types (like DockWidgetArea) that don't have default JSON representations
- Providing conversion between Qt enums and string representations
- Supporting layout serialization with proper type information

### Project Integration

The integration between layouts and projects is handled in `project_integration.py`:

```python
def save_layout_with_project(filename: str) -> bool:
    """
    Save the current layout with the project file.
    
    This is done by appending a special layout section to the end of the 
    project file. The layout data is stored separately from the main project
    data to avoid affecting the command system.
    """
    try:
        # Get layout data
        layout_manager = get_layout_manager()
        layout_data = layout_manager.capture_current_layout()
        
        if not layout_data:
            return False
            
        # Convert to JSON string
        layout_json = json.dumps(layout_data)
        
        # Append to file with a special marker
        with open(filename, 'a', encoding='utf-8') as f:
            f.write("\n__LAYOUT_DATA_BEGIN__\n")
            f.write(layout_json)
            f.write("\n__LAYOUT_DATA_END__\n")
            
        return True
    except Exception as e:
        print(f"Error saving layout with project: {e}")
        return False


def load_layout_from_project(filename: str) -> bool:
    """
    Load and apply layout data from a project file.
    
    Extracts layout data that was appended to the project file
    and applies it to the current UI.
    """
    try:
        # Check if file exists
        if not os.path.exists(filename):
            return False
            
        # Read the file
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract layout data
        start_marker = "__LAYOUT_DATA_BEGIN__"
        end_marker = "__LAYOUT_DATA_END__"
        
        start_pos = content.find(start_marker)
        if start_pos == -1:
            return False  # No layout data found
            
        start_pos += len(start_marker)
        end_pos = content.find(end_marker, start_pos)
        
        if end_pos == -1:
            return False  # Incomplete layout data
            
        # Extract and parse layout JSON
        layout_json = content[start_pos:end_pos].strip()
        layout_data = json.loads(layout_json)
        
        # Apply layout
        layout_manager = get_layout_manager()
        return layout_manager.apply_layout(layout_data)
            
    except Exception as e:
        print(f"Error loading layout from project: {e}")
        return False
```

Key points:
- Layouts are stored as a separate section in the project file
- Special markers (`__LAYOUT_DATA_BEGIN__` and `__LAYOUT_DATA_END__`) delimit the layout data
- The main project data and layout data are kept separate to avoid interference
- The `ProjectSerializer` knows to ignore the layout section when loading model data

## Special Widget Serialization

### Dock Widget Serialization

The `LayoutManager` class in `layout_manager.py` handles serialization of dock widgets and other UI components:

```python
def _capture_widget_state(self, widget: QWidget) -> Dict[str, Any]:
    """
    Capture the state of a specific widget.
    """
    # Skip if widget isn't valid
    if not widget or not widget.isVisible():
        return {}
        
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

The `DockManager` class in `dock_manager.py` also has its own serialization for dock states:

```python
def serialize_layout(self) -> Dict[str, Dict[str, Any]]:
    """
    Serialize the layout state of all docks.
    
    Returns:
        Dictionary containing dock layout state
    """
    # Save current state of all docks
    for dock_id in self._dock_states:
        self.save_dock_state(dock_id)
        
    # Create serializable layout
    layout = {}
    for dock_id, dock_data in self._dock_states.items():
        layout[dock_id] = {
            "state": dock_data["state"],
            "parent_id": dock_data["parent_id"],
            "children": dock_data["children"]
        }
        
    return layout
```

Key points:
- Special handling for different widget types (QSplitter, QTabWidget, QDockWidget)
- Capture of dock-specific properties like floating state and dock area
- Preservation of parent-child relationships for docks
- Capture of geometry, visibility, and other common properties

## Implementation Details

### Saving Process

The saving process follows these steps:

1. The user initiates a save operation, typically through a UI action
2. The `ProjectManager` is called with a model and filename
3. If saving layouts is enabled, the process takes two steps:
   a. First, the model is serialized using `ProjectSerializer` and `ObservableEncoder`
   b. Then, the layout data is appended to the file using `save_layout_with_project`
4. Upon successful save, the command history is cleared

Key code in `ProjectSerializer`:

```python
@staticmethod
def save_to_file(model: Observable, filename: str, format_type=None) -> bool:
    """
    Save a model to a file.
    """
    format_type = format_type or ProjectSerializer.DEFAULT_FORMAT
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        
        if format_type == ProjectSerializer.FORMAT_JSON:
            # Use JSON format
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(model, f, cls=ObservableEncoder, indent=2)
        elif format_type == ProjectSerializer.FORMAT_BINARY:
            # Use pickle for binary format
            import pickle
            with open(filename, 'wb') as f:
                pickle.dump(model, f)
        # Other formats handled similarly...
        
        return True
    except Exception as e:
        print(f"Error saving project: {e}")
        return False
```

### Loading Process

The loading process follows these steps:

1. The user initiates a load operation, typically through a UI action
2. The `ProjectManager` is called with a filename
3. The model is loaded first using `ProjectSerializer` and `observable_decoder`
4. If layout loading is enabled, the layout data is extracted and applied
5. Upon successful load, the command history is cleared

Key code in `ProjectSerializer`:

```python
@staticmethod
def load_from_file(filename: str, format_type=None) -> Optional[Observable]:
    """
    Load a model from a file.
    """
    # If format not specified, guess from extension
    if format_type is None:
        ext = os.path.splitext(filename)[1].lower()
        # Format determination logic...
    
    try:
        if format_type == ProjectSerializer.FORMAT_JSON:
            # Use JSON format
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for layout markers and extract only the JSON part
                start_marker = "__LAYOUT_DATA_BEGIN__"
                start_pos = content.find(start_marker)
                if start_pos != -1:
                    # Only use content before the layout marker
                    content = content[:start_pos]
                
                # Parse the JSON content
                return json.loads(content, object_hook=observable_decoder)
        # Other formats handled similarly...
    except Exception as e:
        print(f"Error loading project: {e}")
        return None
```

## File Format Support

The system supports multiple file formats:

1. **JSON** (Default)
   - Human-readable text format
   - Implementation using `json.dump` and `json.load`
   - Custom encoding via `ObservableEncoder` and `observable_decoder`

2. **Binary**
   - Binary format using pickle
   - More compact but not human-readable
   - Implementation using `pickle.dump` and `pickle.load`

3. **XML**
   - Structured text format
   - Placeholder implementation using ElementTree
   - Not fully implemented in the current version

4. **YAML**
   - Human-readable structured text format
   - Placeholder implementation using PyYAML
   - Not fully implemented in the current version

The file format can be selected using:

```python
# Set default format
project_manager.set_default_format(ProjectSerializer.FORMAT_JSON)

# Get default extension
extension = project_manager.get_default_extension()
```

## Integration in Demo Applications

The serialization system is used in the demo applications:

### File Menu Demo (`file_menu_demo.py`)

```python
def _on_save(self):
    """Handle Save action."""
    # Check if we have a filename
    if self.project_manager.get_current_filename() is None:
        # No filename, do Save As instead
        self._on_save_as()
    else:
        # Save to current filename
        if self.project_manager.save_project(self.model):
            # Update window title to reflect saved state
            self._update_window_title()
        else:
            QMessageBox.critical(self, "Error", "Failed to save the note file.")
```

### Complete Demo (`complete_demo.py`)

```python
def _on_save_as(self):
    """Handle Save As action."""
    # Get file format details
    extension = self.project_manager.get_default_extension()
    
    # Show file dialog
    filename, _ = QFileDialog.getSaveFileName(
        self, "Save Project", "", f"Project Files (*{extension});;All Files (*)"
    )
    
    if not filename:
        return
        
    # Add extension if not present
    if not filename.lower().endswith(extension):
        filename += extension
        
    # Get current layout setting
    include_layout = self.save_layout_action.isChecked()
        
    # Save project
    if self.project_manager.save_project(self.model, filename, save_layout=include_layout):
        # Update window title
        self._update_window_title()
        self.status_label.setText(f"Project saved as: {filename}")
    else:
        QMessageBox.critical(self, "Error", "Failed to save the project file.")
```

These demos showcase:
- Integration with standard file dialogs
- Format selection
- Handling of unsaved changes
- UI updates to reflect file state
- Error handling for save/load operations
- Layout integration with projects