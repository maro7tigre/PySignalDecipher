"""
Serialization support for the command system.

Provides functionality to save and load Observable model states to/from JSON.
"""
import json
import os
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Type, Union, Optional

from .observable import Observable, ObservableProperty


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
    
    return obj_dict


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
    def get_default_extension(format_type=None):
        """Get the default extension for the given format type."""
        format_type = format_type or ProjectSerializer.DEFAULT_FORMAT
        return ProjectSerializer.DEFAULT_EXTENSIONS.get(format_type, ".json")
    
    @staticmethod
    def save_to_file(model: Observable, filename: str, format_type=None) -> bool:
        """
        Save a model to a file.
        
        Args:
            model: The Observable model to save
            filename: Path to save the file to
            format_type: Format type (json, bin, xml, yaml)
            
        Returns:
            True if save was successful
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
            elif format_type == ProjectSerializer.FORMAT_XML:
                # Use XML format (simplified example)
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.Element("Project")
                    # Serialize model to XML
                    # This is just a placeholder - a real implementation would need
                    # to convert the entire model to XML format
                    ET.SubElement(root, "Model", 
                                 attrib={"class": model.__class__.__name__, 
                                         "id": model.get_id()})
                    tree = ET.ElementTree(root)
                    tree.write(filename)
                except ImportError:
                    print("XML serialization requires xml.etree.ElementTree")
                    return False
            elif format_type == ProjectSerializer.FORMAT_YAML:
                # Use YAML format
                try:
                    import yaml
                    with open(filename, 'w', encoding='utf-8') as f:
                        # Would need a custom YAML dumper for Observable objects
                        yaml.dump({"warning": "YAML serialization not fully implemented"}, f)
                except ImportError:
                    print("YAML serialization requires PyYAML package")
                    return False
            else:
                print(f"Unsupported format type: {format_type}, using JSON")
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(model, f, cls=ObservableEncoder, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    @staticmethod
    def load_from_file(filename: str, format_type=None) -> Optional[Observable]:
        """
        Load a model from a file.
        
        Args:
            filename: Path to the file to load
            format_type: Format type (json, bin, xml, yaml)
            
        Returns:
            Loaded Observable model, or None if loading failed
        """
        # If format not specified, guess from extension
        if format_type is None:
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".json":
                format_type = ProjectSerializer.FORMAT_JSON
            elif ext == ".bin":
                format_type = ProjectSerializer.FORMAT_BINARY
            elif ext == ".xml":
                format_type = ProjectSerializer.FORMAT_XML
            elif ext in [".yaml", ".yml"]:
                format_type = ProjectSerializer.FORMAT_YAML
            else:
                # Default to JSON
                format_type = ProjectSerializer.FORMAT_JSON
        
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
            elif format_type == ProjectSerializer.FORMAT_BINARY:
                # Use pickle for binary format
                import pickle
                with open(filename, 'rb') as f:
                    return pickle.load(f)
            elif format_type == ProjectSerializer.FORMAT_XML:
                # XML loading not implemented
                print("XML deserialization not implemented")
                return None
            elif format_type == ProjectSerializer.FORMAT_YAML:
                # YAML loading not implemented
                print("YAML deserialization not implemented")
                return None
            else:
                print(f"Unsupported format type: {format_type}, trying JSON")
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for layout markers in fallback JSON handling
                    start_marker = "__LAYOUT_DATA_BEGIN__"
                    start_pos = content.find(start_marker)
                    if start_pos != -1:
                        # Only use content before the layout marker
                        content = content[:start_pos]
                    
                    return json.loads(content, object_hook=observable_decoder)
        except Exception as e:
            print(f"Error loading project: {e}")
            return None