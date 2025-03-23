# PySignalDecipher Serialization System

This document provides a comprehensive explanation of the serialization and project saving/loading system in the PySignalDecipher command system.

## Table of Contents

1. [Overview](#overview)
2. [Core Serialization Components](#core-serialization-components)
   - [ProjectSerializer](#projectserializer)
   - [ObservableEncoder](#observableencoder)
   - [observable_decoder](#observable_decoder)
3. [Observable Hierarchy Serialization](#observable-hierarchy-serialization)
   - [Parent-Child Relationships](#parent-child-relationships)
   - [Generation Tracking](#generation-tracking)
4. [Project Management](#project-management)
   - [ProjectManager](#projectmanager)
5. [Layout Integration](#layout-integration)
   - [Layout Serialization](#layout-serialization)
   - [Project Integration](#project-integration)
6. [Special Widget Serialization](#special-widget-serialization)
   - [Dock Widget Serialization](#dock-widget-serialization)
7. [Implementation Details](#implementation-details)
   - [Saving Process](#saving-process)
   - [Loading Process](#loading-process)
8. [File Format Support](#file-format-support)
9. [Integration in Demo Applications](#integration-in-demo-applications)

## Overview

The serialization system allows saving and loading the application state, including:

- Model data (Observable objects and their properties)
- Observable hierarchy (parent-child relationships)
- Generation information (object ancestry tracking)
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
        
        # Store object ID, parent_id, and generation info
        result = {
            "__type__": "observable",
            "__class__": f"{cls.__module__}.{cls.__name__}",
            "id": obj.get_id(),
            "parent_id": obj.get_parent_id(),
            "generation": obj.get_generation(),
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
- Preserving hierarchy information (parent_id and generation)
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
            
            # Set parent_id if present
            if "parent_id" in obj_dict:
                instance.set_parent_id(obj_dict["parent_id"])
                
            # Set generation if present
            if "generation" in obj_dict:
                instance.set_generation(obj_dict["generation"])
                
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
- Setting object IDs, parent IDs, and generation information
- Setting object properties
- Handling special types like dates

## Observable Hierarchy Serialization

### Parent-Child Relationships

Observable objects can now maintain parent-child relationships:

```python
class Observable:
    def __init__(self, parent=None):
        # ...other initialization
        self._parent_id = getattr(parent, 'get_id', lambda: None)() if parent else None
        # ...generation initialization

    def get_parent_id(self) -> Optional[str]:
        """Get parent identifier."""
        return self._parent_id
        
    def set_parent_id(self, parent_id: str) -> None:
        """Set parent identifier (for deserialization or reparenting)."""
        self._parent_id = parent_id
```

During serialization, the parent ID is included in the JSON output:

```json
{
  "__type__": "observable",
  "__class__": "myapp.models.ChildModel",
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "parent_id": "550e8400-e29b-41d4-a716-446655440000",
  "generation": 1,
  "properties": {
    "name": "Child Item"
  }
}
```

### Generation Tracking

Generations help track the ancestry of objects:

```python
class Observable:
    def __init__(self, parent=None):
        # ...other initialization
        if parent and hasattr(parent, 'get_generation'):
            self._generation = parent.get_generation() + 1
        else:
            self._generation = 0  # Base generation if no parent
            
    def get_generation(self) -> int:
        """Get object generation."""
        return self._generation
        
    def set_generation(self, generation: int) -> None:
        """Set object generation (for deserialization)."""
        self._generation = generation
```

Benefits of generation tracking:
- Understand object ancestry and depth
- Optimize refresh operations (refresh only newer generations)
- Identify object creation order
- Support cyclical reference detection

## Project Management

### ProjectManager

The `ProjectManager` class in `project_manager.py` provides high-level project operations:

```python
class ProjectManager:
    """
    Manages project save and load operations.
    """
    # ...initialization and singleton methods
    
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
```

The integration with the Observable hierarchy is handled through the dock manager, which maintains parent-child relationships between dock widgets.

### Project Integration

The integration between layouts and projects is handled in `project_integration.py`. When saving layouts with projects, the hierarchy information in Observable objects is preserved.

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
    if isinstance(widget, QDockWidget):
        dock_data = self.dock_manager.get_dock_data(widget)
        if dock_data:
            # Include parent information
            widget_data["dock"] = {
                "floating": widget.isFloating(),
                "area": self._get_dock_area(widget),
                "object_name": widget.objectName(),
                "parent_id": dock_data.get("parent_id")
            }
            
    return widget_data
```

Dock widgets also preserve the Observable hierarchy:

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

## Implementation Details

### Saving Process

The saving process follows these steps:

1. The user initiates a save operation, typically through a UI action
2. The `ProjectManager` is called with a model and filename
3. The model and its hierarchy (parent-child relationships and generations) are serialized
4. If saving layouts is enabled, the layout data is appended to the file
5. Upon successful save, the command history is cleared

### Loading Process

The loading process follows these steps:

1. The user initiates a load operation, typically through a UI action
2. The `ProjectManager` is called with a filename
3. The model is loaded first, including its hierarchy information
4. If layout loading is enabled, the layout data is extracted and applied
5. Upon successful load, the command history is cleared

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

## Integration in Demo Applications

To create parent-child relationships in demo applications, you would use code like:

```python
# Create parent model
parent_model = ProjectModel()

# Create child model with parent reference
child_model = ParameterModel(parent=parent_model)  # This sets parent_id and generation

# When serialized, the hierarchy information will be preserved
project_manager.save_project(parent_model, "project_with_children.json")
```

When this project is loaded, the parent-child relationships will be reconstructed:

```python
# Load the project
loaded_model = project_manager.load_project("project_with_children.json")

# Access child models (this would require your application to maintain references)
# You might have a method like:
child_models = find_child_models(loaded_model)
```

The generation information can be used for various purposes:

```python
# Get model generation
generation = model.get_generation()

# Only refresh models of a certain generation or newer
if model.get_generation() >= min_generation:
    refresh_model(model)
```

These hierarchical relationships and generation tracking provide a powerful foundation for complex application state management.