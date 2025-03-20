"""
Dock management system for handling dock widgets in a Qt application.
"""
from typing import Dict, List, Optional, Any, Set

from PySide6.QtCore import QPoint, QSize, QByteArray, Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow

from ...command_manager import get_command_manager
from ...observable import Observable


class DockManager:
    """
    Manages dock widgets in a Qt application.
    Handles tracking, serialization, and parent-child relationships.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = DockManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the dock manager."""
        if DockManager._instance is not None:
            raise RuntimeError("Use DockManager.get_instance() to get the singleton instance")
            
        DockManager._instance = self
        self._command_manager = get_command_manager()
        self._dock_states: Dict[str, Dict[str, Any]] = {}
        self._main_window: Optional[QMainWindow] = None
        
    def set_main_window(self, main_window: QMainWindow) -> None:
        """
        Set the main window that holds the docks.
        
        Args:
            main_window: Main window instance
        """
        self._main_window = main_window
        
    def register_dock(self, dock_id: str, dock_widget: QDockWidget, parent_id: Optional[str] = None) -> None:
        """
        Register a dock widget with the dock manager.
        
        Args:
            dock_id: Unique identifier for the dock
            dock_widget: The dock widget instance
            parent_id: Optional parent dock ID for hierarchical relationships
        """
        self._dock_states[dock_id] = {
            "widget": dock_widget,
            "parent_id": parent_id,
            "children": [],
            "state": {},
            "model": getattr(dock_widget, "model", None)
        }
        
        # Add as child to parent if applicable
        if parent_id and parent_id in self._dock_states:
            self._dock_states[parent_id]["children"].append(dock_id)
            
        # Save initial state
        self.save_dock_state(dock_id)
        
    def unregister_dock(self, dock_id: str) -> None:
        """
        Unregister a dock widget.
        
        Args:
            dock_id: ID of the dock to unregister
        """
        if dock_id not in self._dock_states:
            return
            
        # Remove from parent's children list
        parent_id = self._dock_states[dock_id]["parent_id"]
        if parent_id and parent_id in self._dock_states:
            if dock_id in self._dock_states[parent_id]["children"]:
                self._dock_states[parent_id]["children"].remove(dock_id)
                
        # Remove state
        del self._dock_states[dock_id]
        
    def get_dock_widget(self, dock_id: str) -> Optional[QDockWidget]:
        """
        Get a dock widget by ID.
        
        Args:
            dock_id: ID of the dock to retrieve
            
        Returns:
            The dock widget, or None if not found
        """
        if dock_id in self._dock_states:
            return self._dock_states[dock_id]["widget"]
        return None
        
    def get_dock_model(self, dock_id: str) -> Optional[Observable]:
        """
        Get the model associated with a dock.
        
        Args:
            dock_id: ID of the dock
            
        Returns:
            The associated model, or None if not found
        """
        if dock_id in self._dock_states:
            return self._dock_states[dock_id]["model"]
        return None
        
    def save_dock_state(self, dock_id: str) -> None:
        """
        Save the current state of a dock.
        
        Args:
            dock_id: ID of the dock to save state for
        """
        if dock_id not in self._dock_states:
            return
            
        dock_widget = self._dock_states[dock_id]["widget"]
        
        # Save geometry and state
        self._dock_states[dock_id]["state"] = {
            "geometry": dock_widget.saveGeometry().toBase64().data().decode('ascii'),
            "position": {
                "x": dock_widget.pos().x(),
                "y": dock_widget.pos().y(),
                "width": dock_widget.width(),
                "height": dock_widget.height()
            },
            "visible": dock_widget.isVisible(),
            "floating": dock_widget.isFloating(),
            "area": self._get_dock_area(dock_widget)
        }
        
    def restore_dock_state(self, dock_id: str) -> bool:
        """
        Restore the saved state of a dock.
        
        Args:
            dock_id: ID of the dock to restore
            
        Returns:
            True if state was restored successfully
        """
        if dock_id not in self._dock_states or "state" not in self._dock_states[dock_id]:
            return False
            
        dock_widget = self._dock_states[dock_id]["widget"]
        state = self._dock_states[dock_id]["state"]
        
        # Restore geometry
        if "geometry" in state:
            try:
                geometry = QByteArray.fromBase64(state["geometry"].encode('ascii'))
                dock_widget.restoreGeometry(geometry)
            except Exception as e:
                print(f"Error restoring dock geometry: {e}")
                
        # Restore position and size for floating docks
        if "position" in state and state.get("floating", False):
            try:
                pos = state["position"]
                dock_widget.resize(pos["width"], pos["height"])
                dock_widget.move(pos["x"], pos["y"])
            except Exception as e:
                print(f"Error restoring dock position: {e}")
                
        # Restore visibility
        if "visible" in state:
            dock_widget.setVisible(state["visible"])
            
        # Restore floating state
        if "floating" in state:
            dock_widget.setFloating(state["floating"])
            
        # Restore dock area
        if "area" in state and self._main_window:
            area = state["area"]
            if area is not None:
                self._main_window.addDockWidget(area, dock_widget)
                
        return True
        
    def _get_dock_area(self, dock_widget: QDockWidget) -> Optional[int]:
        """
        Get the dock area for a dock widget.
        
        Args:
            dock_widget: The dock widget
            
        Returns:
            Qt dock area enum value, or None if not docked
        """
        if not self._main_window or dock_widget.isFloating():
            return None
            
        # Try to determine the dock area - this is an approximation
        # since Qt doesn't provide a direct way to get the current area
        for area in [
            Qt.DockWidgetArea.LeftDockWidgetArea,
            Qt.DockWidgetArea.RightDockWidgetArea,
            Qt.DockWidgetArea.TopDockWidgetArea,
            Qt.DockWidgetArea.BottomDockWidgetArea
        ]:
            if self._main_window.dockWidgetArea(dock_widget) == area:
                return area
                
        return None
        
    def get_child_docks(self, parent_id: str) -> List[str]:
        """
        Get the IDs of all child docks for a parent dock.
        
        Args:
            parent_id: ID of the parent dock
            
        Returns:
            List of child dock IDs
        """
        if parent_id in self._dock_states:
            return self._dock_states[parent_id]["children"].copy()
        return []
        
    def get_all_descendant_docks(self, parent_id: str) -> List[str]:
        """
        Get all descendant docks recursively.
        
        Args:
            parent_id: ID of the parent dock
            
        Returns:
            List of all descendant dock IDs
        """
        result = []
        to_process = self.get_child_docks(parent_id)
        
        while to_process:
            dock_id = to_process.pop(0)
            result.append(dock_id)
            to_process.extend(self.get_child_docks(dock_id))
            
        return result
        
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
        
    def deserialize_layout(self, layout: Dict[str, Dict[str, Any]]) -> bool:
        """
        Restore layout from serialized state.
        
        Args:
            layout: Serialized layout state
            
        Returns:
            True if layout was restored successfully
        """
        try:
            # First pass: Update states
            for dock_id, dock_data in layout.items():
                if dock_id in self._dock_states:
                    self._dock_states[dock_id]["state"] = dock_data["state"]
                    
            # Second pass: Restore states in dependency order (parents first)
            processed = set()
            to_process = [dock_id for dock_id, data in self._dock_states.items() 
                          if data["parent_id"] is None]
            
            while to_process:
                dock_id = to_process.pop(0)
                
                if dock_id in processed:
                    continue
                    
                # Process this dock
                self.restore_dock_state(dock_id)
                processed.add(dock_id)
                
                # Add children to process queue
                children = self.get_child_docks(dock_id)
                to_process.extend([c for c in children if c not in processed])
                
            return True
        except Exception as e:
            print(f"Error deserializing layout: {e}")
            return False


def get_dock_manager():
    """Get the singleton dock manager instance."""
    return DockManager.get_instance()