"""
Dock manager for dock position and state management.
"""
from command_system.internal.registry import Registry


class DockManager:
    """
    Manages dock widgets and their relationships.
    Handles parent-child relationships and serialization of dock state.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = DockManager()
        return cls._instance
    
    def __init__(self):
        """Initialize dock manager."""
        if DockManager._instance is not None:
            raise RuntimeError("Use DockManager.get_instance() to get the singleton instance")
            
        DockManager._instance = self
        self._registry = Registry.get_instance()
        self._dock_states = {}
        
    def register_dock(self, dock_id, dock_widget, parent_id=None):
        """
        Register a dock widget.
        
        Args:
            dock_id (str): ID for the dock
            dock_widget: Dock widget
            parent_id (str, optional): ID of parent dock
            
        Returns:
            str: The dock ID
        """
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
        
        return dock_id
        
    def unregister_dock(self, dock_id):
        """
        Unregister a dock widget and its children.
        
        Args:
            dock_id (str): ID of the dock
            
        Returns:
            bool: True if dock was unregistered
        """
        if dock_id in self._dock_states:
            # Unregister children first
            children = self._dock_states[dock_id]["children"].copy()
            for child_id in children:
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
            
            return True
            
        return False
        
    def get_dock(self, dock_id):
        """
        Get dock widget by ID.
        
        Args:
            dock_id (str): ID of the dock
            
        Returns:
            Dock widget, or None if not found
        """
        if dock_id in self._dock_states:
            return self._dock_states[dock_id]["widget"]
        return None
        
    def has_dock(self, dock_id):
        """
        Check if dock exists.
        
        Args:
            dock_id (str): ID of the dock
            
        Returns:
            bool: True if dock exists
        """
        return dock_id in self._dock_states
        
    def get_parent_id(self, dock_id):
        """
        Get parent ID of a dock.
        
        Args:
            dock_id (str): ID of the dock
            
        Returns:
            str: Parent ID, or None if no parent
        """
        if dock_id in self._dock_states:
            return self._dock_states[dock_id]["parent_id"]
        return None
        
    def get_children(self, dock_id):
        """
        Get children of a dock.
        
        Args:
            dock_id (str): ID of the dock
            
        Returns:
            list: List of child dock IDs
        """
        if dock_id in self._dock_states:
            return self._dock_states[dock_id]["children"].copy()
        return []
        
    def save_dock_state(self, dock_id):
        """
        Save the current state of a dock.
        
        Args:
            dock_id (str): ID of the dock
            
        Returns:
            bool: True if state was saved
        """
        if dock_id in self._dock_states:
            widget = self._dock_states[dock_id]["widget"]
            
            try:
                self._dock_states[dock_id]["state"] = {
                    "geometry": widget.saveGeometry().toBase64().data().decode('ascii') if hasattr(widget, "saveGeometry") else None,
                    "position": {
                        "x": widget.x(),
                        "y": widget.y(),
                        "width": widget.width(),
                        "height": widget.height()
                    },
                    "visible": widget.isVisible(),
                    "floating": widget.isFloating() if hasattr(widget, "isFloating") else False
                }
                return True
            except Exception as e:
                print(f"Error saving dock state: {e}")
                
        return False
            
    def restore_dock_state(self, dock_id):
        """
        Restore the saved state of a dock.
        
        Args:
            dock_id (str): ID of the dock
            
        Returns:
            bool: True if state was restored
        """
        if dock_id in self._dock_states and "state" in self._dock_states[dock_id]:
            widget = self._dock_states[dock_id]["widget"]
            state = self._dock_states[dock_id]["state"]
            
            try:
                from PySide6.QtCore import QByteArray
                
                # Restore geometry
                if "geometry" in state and state["geometry"] and hasattr(widget, "restoreGeometry"):
                    widget.restoreGeometry(QByteArray.fromBase64(state["geometry"].encode('ascii')))
                    
                # Restore position and size
                if "position" in state:
                    pos = state["position"]
                    widget.setGeometry(pos["x"], pos["y"], pos["width"], pos["height"])
                    
                # Restore visibility
                if "visible" in state:
                    widget.setVisible(state["visible"])
                    
                # Restore floating state
                if "floating" in state and hasattr(widget, "setFloating"):
                    widget.setFloating(state["floating"])
                    
                return True
            except Exception as e:
                print(f"Error restoring dock state: {e}")
                
        return False
        
    def serialize_layout(self):
        """
        Serialize the layout state of all docks.
        
        Returns:
            dict: Serialized layout state
        """
        layout = {}
        
        for dock_id, dock_data in self._dock_states.items():
            # Save current state
            self.save_dock_state(dock_id)
            
            layout[dock_id] = {
                "state": dock_data["state"],
                "parent_id": dock_data["parent_id"],
                "children": dock_data["children"]
            }
            
        return layout
        
    def deserialize_layout(self, layout):
        """
        Restore layout from serialized state.
        
        Args:
            layout (dict): Serialized layout state
            
        Returns:
            bool: True if layout was restored
        """
        if not layout or not isinstance(layout, dict):
            return False
            
        try:
            # First pass: Update states
            for dock_id, dock_data in layout.items():
                if dock_id in self._dock_states:
                    self._dock_states[dock_id]["state"] = dock_data.get("state", {})
                    
                    # Update parent-child relationships
                    parent_id = dock_data.get("parent_id")
                    if parent_id != self._dock_states[dock_id]["parent_id"]:
                        # Remove from old parent
                        old_parent_id = self._dock_states[dock_id]["parent_id"]
                        if old_parent_id and old_parent_id in self._dock_states:
                            if dock_id in self._dock_states[old_parent_id]["children"]:
                                self._dock_states[old_parent_id]["children"].remove(dock_id)
                                
                        # Add to new parent
                        self._dock_states[dock_id]["parent_id"] = parent_id
                        if parent_id and parent_id in self._dock_states:
                            if dock_id not in self._dock_states[parent_id]["children"]:
                                self._dock_states[parent_id]["children"].append(dock_id)
                    
            # Second pass: Restore states (to handle parent-child dependencies)
            for dock_id in self._dock_states:
                self.restore_dock_state(dock_id)
                
            return True
        except Exception as e:
            print(f"Error deserializing layout: {e}")
            return False
            
    def clear(self):
        """Clear all dock states."""
        # Unregister all docks from registry
        for dock_id in list(self._dock_states.keys()):
            self._registry.unregister_object(dock_id)
            
        # Clear dock states
        self._dock_states.clear()