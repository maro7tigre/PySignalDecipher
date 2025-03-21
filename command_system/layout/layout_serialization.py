"""
Serialization helpers for the layout system.

Handles serialization and deserialization of Qt-specific types.
"""
import json
from typing import Any, Dict, Union

from PySide6.QtCore import Qt


class LayoutEncoder(json.JSONEncoder):
    """JSON encoder that handles Qt-specific types."""
    
    def default(self, obj):
        # Handle Qt.DockWidgetArea
        if obj == Qt.DockWidgetArea.LeftDockWidgetArea:
            return {"__qt_type__": "DockWidgetArea", "value": "LeftDockWidgetArea"}
        elif obj == Qt.DockWidgetArea.RightDockWidgetArea:
            return {"__qt_type__": "DockWidgetArea", "value": "RightDockWidgetArea"}
        elif obj == Qt.DockWidgetArea.TopDockWidgetArea:
            return {"__qt_type__": "DockWidgetArea", "value": "TopDockWidgetArea"}
        elif obj == Qt.DockWidgetArea.BottomDockWidgetArea:
            return {"__qt_type__": "DockWidgetArea", "value": "BottomDockWidgetArea"}
        elif obj == Qt.DockWidgetArea.AllDockWidgetAreas:
            return {"__qt_type__": "DockWidgetArea", "value": "AllDockWidgetAreas"}
        elif obj == Qt.DockWidgetArea.NoDockWidgetArea:
            return {"__qt_type__": "DockWidgetArea", "value": "NoDockWidgetArea"}
            
        # Handle Qt.Orientation
        elif obj == Qt.Orientation.Horizontal:
            return {"__qt_type__": "Orientation", "value": "Horizontal"}
        elif obj == Qt.Orientation.Vertical:
            return {"__qt_type__": "Orientation", "value": "Vertical"}
        
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
            elif value == "RightDockWidgetArea":
                return Qt.DockWidgetArea.RightDockWidgetArea
            elif value == "TopDockWidgetArea":
                return Qt.DockWidgetArea.TopDockWidgetArea
            elif value == "BottomDockWidgetArea":
                return Qt.DockWidgetArea.BottomDockWidgetArea
            elif value == "AllDockWidgetAreas":
                return Qt.DockWidgetArea.AllDockWidgetAreas
            elif value == "NoDockWidgetArea":
                return Qt.DockWidgetArea.NoDockWidgetArea
                
        # Handle Orientation
        elif qt_type == "Orientation":
            if value == "Horizontal":
                return Qt.Orientation.Horizontal
            elif value == "Vertical":
                return Qt.Orientation.Vertical
    
    # Return the original object if not a known Qt type
    return obj_dict


def serialize_layout(layout_data: Dict[str, Any]) -> str:
    """
    Serialize layout data to a JSON string.
    
    Args:
        layout_data: Layout data dictionary
        
    Returns:
        JSON string
    """
    return json.dumps(layout_data, cls=LayoutEncoder, indent=2)


def deserialize_layout(json_str: str) -> Dict[str, Any]:
    """
    Deserialize layout data from a JSON string.
    
    Args:
        json_str: JSON string
        
    Returns:
        Layout data dictionary
    """
    return json.loads(json_str, object_hook=layout_decoder)