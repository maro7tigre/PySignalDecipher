"""
Dock management system for handling dock widgets in a Qt application.
"""
from typing import Dict, List, Optional, Any, Set, Callable, Tuple

from PySide6.QtCore import QPoint, QSize, QByteArray, Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow

from ...core.command_manager import get_command_manager
from ...core.observable import Observable


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
        
        # Dock creation order for restoration
        self._dock_creation_order: List[str] = []
        
        # Serialization callbacks
        self._before_serialize_callbacks: Dict[str, Callable[[], None]] = {}
        self._after_serialize_callbacks: Dict[str, Callable[[Dict], None]] = {}
        self._before_deserialize_callbacks: Dict[str, Callable[[Dict], None]] = {}
        self._after_deserialize_callbacks: Dict[str, Callable[[], None]] = {}
        
        # Dock factory functions
        self._dock_factories: Dict[str, Callable[[], QDockWidget]] = {}
        
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
            "model": getattr(dock_widget, "model", None),
            "type": getattr(dock_widget, "dock_type", dock_widget.__class__.__name__)
        }
        
        # Add as child to parent if applicable
        if parent_id and parent_id in self._dock_states:
            self._dock_states[parent_id]["children"].append(dock_id)
            
        # Track dock creation order
        if dock_id not in self._dock_creation_order:
            self._dock_creation_order.append(dock_id)
            
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
                
        # Remove from creation order if present
        if dock_id in self._dock_creation_order:
            self._dock_creation_order.remove(dock_id)
                
        # Remove state
        del self._dock_states[dock_id]
        
    def register_dock_factory(self, dock_type: str, factory: Callable[[], QDockWidget]) -> None:
        """
        Register a factory function for creating docks during restoration.
        
        Args:
            dock_type: Type identifier for the dock
            factory: Function that creates a new dock widget
        """
        self._dock_factories[dock_type] = factory
        
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
        Save the current state of a dock widget.
        
        Args:
            dock_id: ID of the dock to save state for
        """
        if dock_id not in self._dock_states:
            return
            
        dock_widget = self._dock_states[dock_id]["widget"]
        if not dock_widget:
            return
            
        # Store state information
        state = {
            "visible": dock_widget.isVisible(),
            "floating": dock_widget.isFloating(),
            "area": self._get_dock_area(dock_widget),
            "title": dock_widget.windowTitle()
        }
        
        # Store position and size for floating docks
        if dock_widget.isFloating():
            state["position"] = {
                "x": dock_widget.x(),
                "y": dock_widget.y(),
                "width": dock_widget.width(),
                "height": dock_widget.height()
            }
            
        # Update the state in dock_states
        self._dock_states[dock_id]["state"] = state
        
    def restore_dock_state(self, dock_id: str) -> bool:
        """
        Restore a dock widget's state.
        
        Args:
            dock_id: ID of the dock to restore
            
        Returns:
            True if state was restored
        """
        if dock_id not in self._dock_states:
            return False
            
        dock_widget = self._dock_states[dock_id]["widget"]
        state = self._dock_states[dock_id]["state"]
        
        if not dock_widget or not state or not self._main_window:
            return False
            
        # Set dock title
        if "title" in state:
            dock_widget.setWindowTitle(state["title"])
            
        # Set floating state
        dock_widget.setFloating(state.get("floating", False))
        
        # Restore dock area if docked
        area = state.get("area")
        if not state.get("floating", False) and area is not None:
            self._main_window.addDockWidget(area, dock_widget)
            
        # Restore position for floating docks
        if state.get("floating", False) and "position" in state:
            pos = state["position"]
            dock_widget.resize(pos["width"], pos["height"])
            dock_widget.move(pos["x"], pos["y"])
            
        # Set visibility last
        dock_widget.setVisible(state.get("visible", True))
        
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
            
        # Try to determine the dock area
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
        
    def get_dock_creation_order(self) -> List[str]:
        """
        Get the order in which docks were created.
        
        Returns:
            List of dock IDs in creation order
        """
        return self._dock_creation_order.copy()
        
    def get_tabified_dock_groups(self) -> List[List[str]]:
        """
        Get groups of tabified docks.
        
        Returns:
            List of lists, where each inner list contains dock IDs that are tabified together
        """
        if not self._main_window:
            return []
            
        # Find all dock widgets
        all_docks = [dock for dock_id, dock in 
                   [(dock_id, self.get_dock_widget(dock_id)) for dock_id in self._dock_states]
                   if dock and isinstance(dock, QDockWidget)]
        
        # Track processed docks to avoid duplicates
        processed_docks = set()
        tabified_groups = []
        
        # For each dock, find all docks tabified with it
        for dock in all_docks:
            if dock in processed_docks:
                continue
                
            # Find the dock ID
            dock_id = None
            for d_id, state in self._dock_states.items():
                if state["widget"] == dock:
                    dock_id = d_id
                    break
                    
            if not dock_id:
                continue
                
            # Get tabified docks
            tabified_docks = self._main_window.tabifiedDockWidgets(dock)
            
            # If there are tabified docks, create a group
            if tabified_docks:
                group = [dock_id]
                
                for tabified_dock in tabified_docks:
                    # Find the tabified dock ID
                    tabified_id = None
                    for d_id, state in self._dock_states.items():
                        if state["widget"] == tabified_dock:
                            tabified_id = d_id
                            break
                            
                    if tabified_id:
                        group.append(tabified_id)
                        processed_docks.add(tabified_dock)
                
                tabified_groups.append(group)
                processed_docks.add(dock)
        
        return tabified_groups
        
    def add_before_serialize_callback(self, callback_id: str, callback: Callable[[], None]) -> None:
        """
        Add a callback to be called before serialization.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call before serialization
        """
        self._before_serialize_callbacks[callback_id] = callback
        
    def add_after_serialize_callback(self, callback_id: str, 
                                    callback: Callable[[Dict], None]) -> None:
        """
        Add a callback to be called after serialization.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call after serialization with the serialized data
        """
        self._after_serialize_callbacks[callback_id] = callback
        
    def add_before_deserialize_callback(self, callback_id: str, 
                                       callback: Callable[[Dict], None]) -> None:
        """
        Add a callback to be called before deserialization.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call before deserialization with the serialized data
        """
        self._before_deserialize_callbacks[callback_id] = callback
        
    def add_after_deserialize_callback(self, callback_id: str, 
                                      callback: Callable[[], None]) -> None:
        """
        Add a callback to be called after deserialization.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call after deserialization
        """
        self._after_deserialize_callbacks[callback_id] = callback
        
    def remove_callback(self, callback_id: str) -> None:
        """
        Remove a callback by ID.
        
        Args:
            callback_id: ID of the callback to remove
        """
        if callback_id in self._before_serialize_callbacks:
            del self._before_serialize_callbacks[callback_id]
        if callback_id in self._after_serialize_callbacks:
            del self._after_serialize_callbacks[callback_id]
        if callback_id in self._before_deserialize_callbacks:
            del self._before_deserialize_callbacks[callback_id]
        if callback_id in self._after_deserialize_callbacks:
            del self._after_deserialize_callbacks[callback_id]
            
    def prepare_for_serialization(self) -> Dict[str, Any]:
        """
        Prepare dock state data for serialization.
        
        Returns:
            Dictionary with dock layout information
        """
        # Call before serialize callbacks
        for callback in self._before_serialize_callbacks.values():
            callback()
            
        # Save all dock states first
        for dock_id in self._dock_states:
            self.save_dock_state(dock_id)
            
        # Build serializable structure
        result = {
            "docks": {},
            "tabified_groups": self.get_tabified_dock_groups(),
            "creation_order": self._dock_creation_order.copy()
        }
        
        # Extract dock data without widget references
        for dock_id, state in self._dock_states.items():
            result["docks"][dock_id] = {
                "state": state["state"].copy(),
                "parent_id": state["parent_id"],
                "children": state["children"].copy(),
                "type": state.get("type", "QDockWidget")
            }
            
        # Call after serialize callbacks
        for callback in self._after_serialize_callbacks.values():
            callback(result)
            
        return result
        
    def restore_from_serialization(self, data: Dict[str, Any]) -> bool:
        """
        Restore dock state from serialization data.
        
        Args:
            data: Serialized dock layout data
            
        Returns:
            True if restored successfully
        """
        if not isinstance(data, dict) or "docks" not in data:
            return False
            
        # Call before deserialize callbacks
        for callback in self._before_deserialize_callbacks.values():
            callback(data)
            
        # TODO: Implement dock state restoration from serialization data
        # 1. Create missing docks using factories
        # 2. Restore dock states
        # 3. Restore tabification relationships
        # 4. Restore dock ordering
        
        # Call after deserialize callbacks
        for callback in self._after_deserialize_callbacks.values():
            callback()
            
        return True


def get_dock_manager():
    """
    Get the singleton dock manager instance.
    
    Returns:
        DockManager singleton instance
    """
    return DockManager.get_instance()