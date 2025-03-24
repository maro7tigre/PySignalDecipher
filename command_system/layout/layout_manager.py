"""
Layout management system for saving and restoring UI layouts.

This system operates independently from the command system and doesn't
affect the undo/redo history when layouts are applied.
"""
import os
import json
from typing import Dict, Any, Optional, Callable, List, Set, Tuple
import uuid

from PySide6.QtWidgets import (
    QWidget, QMainWindow, QSplitter, QTabWidget, 
    QDockWidget, QApplication
)
from PySide6.QtCore import QByteArray, QSize, QPoint, Qt, QRect

from ..ui.dock.dock_manager import get_dock_manager


class LayoutManager:
    """
    Manages UI layout saving and restoration without affecting command history.
    """
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = LayoutManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the layout manager."""
        if LayoutManager._instance is not None:
            raise RuntimeError("Use LayoutManager.get_instance() to get the singleton instance")
            
        LayoutManager._instance = self
        
        # Main window reference
        self._main_window: Optional[QMainWindow] = None
        
        # Widget registry
        self._registered_widgets: Dict[str, QWidget] = {}
        self._widget_factories: Dict[str, Callable[[], QWidget]] = {}
        
        # Layout presets
        self._layout_presets: Dict[str, Dict[str, Any]] = {}
        
        # Default layouts directory
        self._layouts_dir = "layouts"
        
        # Track dock creation order to help with restoration
        self._dock_creation_order: List[str] = []
        
        # Get dock manager
        self._dock_manager = get_dock_manager()
        
        # Serialization callbacks
        self._before_save_callbacks: Dict[str, Callable[[str], None]] = {}
        self._after_save_callbacks: Dict[str, Callable[[str, bool], None]] = {}
        self._before_load_callbacks: Dict[str, Callable[[str], None]] = {}
        self._after_load_callbacks: Dict[str, Callable[[str, bool], None]] = {}
        
    def set_main_window(self, main_window: QMainWindow) -> None:
        """
        Set the main window for the layout manager.
        
        Args:
            main_window: Main application window
        """
        self._main_window = main_window
        self._dock_manager.set_main_window(main_window)
        
    def register_widget(self, widget_id: str, widget: QWidget) -> None:
        """
        Register a widget to be managed by the layout system.
        
        Args:
            widget_id: Unique identifier for the widget
            widget: Widget to register
        """
        self._registered_widgets[widget_id] = widget
        
        # Track dock creation order
        if isinstance(widget, QDockWidget):
            if widget_id not in self._dock_creation_order:
                self._dock_creation_order.append(widget_id)
        
    def unregister_widget(self, widget_id: str) -> None:
        """
        Unregister a widget from the layout system.
        
        Args:
            widget_id: ID of the widget to unregister
        """
        if widget_id in self._registered_widgets:
            del self._registered_widgets[widget_id]
            
            # Remove from dock creation order if present
            if widget_id in self._dock_creation_order:
                self._dock_creation_order.remove(widget_id)
            
    def register_widget_factory(self, widget_type: str, factory: Callable[[], QWidget]) -> None:
        """
        Register a factory function for creating widgets during layout restoration.
        
        Args:
            widget_type: Type identifier for widgets created by this factory
            factory: Function that creates and returns a new widget instance
        """
        self._widget_factories[widget_type] = factory
        
    def set_layouts_directory(self, directory: str) -> None:
        """
        Set the directory for storing layout presets.
        
        Args:
            directory: Path to layout storage directory
        """
        self._layouts_dir = directory
        
        # Create the directory if it doesn't exist
        os.makedirs(self._layouts_dir, exist_ok=True)
        
    def capture_current_layout(self) -> Dict[str, Any]:
        """
        Capture the current layout state.
        
        Returns:
            Dictionary containing the complete layout state
        """
        # Call before save callbacks
        for callback in self._before_save_callbacks.values():
            callback("current_layout")
            
        layout_data = {}
        
        # Use dock manager to capture dock state
        if hasattr(self._dock_manager, "prepare_for_serialization"):
            layout_data["docks"] = self._dock_manager.prepare_for_serialization()
            
        # Capture main window state if available
        if self._main_window:
            layout_data["main_window"] = {
                "geometry": {
                    "x": self._main_window.x(),
                    "y": self._main_window.y(),
                    "width": self._main_window.width(),
                    "height": self._main_window.height()
                },
                "state": self._main_window.saveState().toBase64().data().decode('ascii')
            }
            
        # Capture non-dock widget states
        layout_data["widgets"] = {}
        for widget_id, widget in self._registered_widgets.items():
            # Skip dock widgets (handled by dock manager)
            if isinstance(widget, QDockWidget):
                continue
                
            # Capture widget state
            layout_data["widgets"][widget_id] = self._capture_widget_state(widget)
            
        # Call after save callbacks
        for callback in self._after_save_callbacks.values():
            callback("current_layout", True)
            
        return layout_data
        
    def _capture_widget_state(self, widget: QWidget) -> Dict[str, Any]:
        """
        Capture the state of a widget.
        
        Args:
            widget: Widget to capture state for
            
        Returns:
            Dictionary with widget state
        """
        state = {
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
            state["sizes"] = widget.sizes()
            state["orientation"] = "horizontal" if widget.orientation() == Qt.Horizontal else "vertical"
            
        elif isinstance(widget, QTabWidget):
            state["current_index"] = widget.currentIndex()
            
        return state
            
    def apply_layout(self, layout_data: Dict[str, Any]) -> bool:
        """
        Apply a layout to the current UI.
        
        Args:
            layout_data: Layout data to apply
            
        Returns:
            True if layout was applied successfully
        """
        if not layout_data:
            return False
            
        # Call before load callbacks
        for callback in self._before_load_callbacks.values():
            callback("current_layout")
            
        success = True
        
        # Determine window scaling (for geometry)
        scale_x, scale_y = 1.0, 1.0
        if self._main_window and "main_window" in layout_data:
            saved_width = layout_data["main_window"]["geometry"]["width"]
            saved_height = layout_data["main_window"]["geometry"]["height"]
            current_width = self._main_window.width()
            current_height = self._main_window.height()
            
            if saved_width > 0 and saved_height > 0:
                scale_x = current_width / saved_width
                scale_y = current_height / saved_height
        
        # Restore dock layout if available
        if "docks" in layout_data and hasattr(self._dock_manager, "restore_from_serialization"):
            dock_success = self._dock_manager.restore_from_serialization(layout_data["docks"])
            success = success and dock_success
            
        # Restore main window state if available
        if self._main_window and "main_window" in layout_data:
            try:
                # Restore window geometry with scaling
                geom = layout_data["main_window"]["geometry"]
                self._main_window.resize(int(geom["width"] * scale_x), int(geom["height"] * scale_y))
                
                # Restore window state
                if "state" in layout_data["main_window"]:
                    state_data = layout_data["main_window"]["state"]
                    self._main_window.restoreState(QByteArray.fromBase64(state_data.encode('ascii')))
            except Exception as e:
                print(f"Error restoring main window state: {e}")
                success = False
                
        # Restore non-dock widget states
        if "widgets" in layout_data:
            for widget_id, state in layout_data["widgets"].items():
                try:
                    self._restore_widget_state(widget_id, state, scale_x, scale_y)
                except Exception as e:
                    print(f"Error restoring widget {widget_id}: {e}")
                    success = False
                    
        # Call after load callbacks
        for callback in self._after_load_callbacks.values():
            callback("current_layout", success)
            
        return success
        
    def _restore_widget_state(self, widget_id: str, state: Dict[str, Any], 
                            scale_x: float, scale_y: float) -> None:
        """
        Restore a widget's state.
        
        Args:
            widget_id: ID of the widget to restore
            state: Widget state to restore
            scale_x: Horizontal scaling factor
            scale_y: Vertical scaling factor
        """
        # Get or create the widget
        widget = self._get_or_create_widget(widget_id, state)
        if not widget:
            return
            
        # Restore geometry with scaling
        if "geometry" in state:
            geom = state["geometry"]
            widget.resize(int(geom["width"] * scale_x), int(geom["height"] * scale_y))
            widget.move(int(geom["x"] * scale_x), int(geom["y"] * scale_y))
            
        # Restore visibility
        if "visible" in state:
            widget.setVisible(state["visible"])
            
        # Special handling for different widget types
        if isinstance(widget, QSplitter) and "sizes" in state:
            try:
                # Scale the sizes
                scaled_sizes = [int(size * scale_x) for size in state["sizes"]]
                widget.setSizes(scaled_sizes)
            except Exception as e:
                print(f"Error restoring splitter sizes: {e}")
                
        elif isinstance(widget, QTabWidget) and "current_index" in state:
            try:
                widget.setCurrentIndex(state["current_index"])
            except Exception as e:
                print(f"Error setting tab index: {e}")
        
    def _get_or_create_widget(self, widget_id: str, state: Dict[str, Any]) -> Optional[QWidget]:
        """
        Get a widget by ID or create it if missing.
        
        Args:
            widget_id: Widget identifier
            state: Widget state data
            
        Returns:
            The widget, or None if not found and couldn't be created
        """
        # Check if widget is already registered
        if widget_id in self._registered_widgets:
            return self._registered_widgets[widget_id]
            
        # Try to create the widget using a factory
        widget_type = state.get("type")
        if widget_type in self._widget_factories:
            try:
                # Create new widget using factory
                widget = self._widget_factories[widget_type]()
                
                # Register the new widget
                self._registered_widgets[widget_id] = widget
                
                return widget
            except Exception as e:
                print(f"Error creating widget {widget_id} of type {widget_type}: {e}")
                
        return None
        
    def save_layout_preset(self, preset_name: str) -> bool:
        """
        Save the current layout as a preset.
        
        Args:
            preset_name: Name for the preset
            
        Returns:
            True if saved successfully
        """
        # Call before save callbacks
        for callback in self._before_save_callbacks.values():
            callback(preset_name)
            
        try:
            # Capture current layout
            layout_data = self.capture_current_layout()
            
            # Store in memory
            self._layout_presets[preset_name] = layout_data
            
            # Save to file
            file_path = os.path.join(self._layouts_dir, f"{preset_name}.json")
            
            with open(file_path, 'w') as f:
                json.dump(layout_data, f, indent=2)
                
            # Call after save callbacks
            for callback in self._after_save_callbacks.values():
                callback(preset_name, True)
                
            return True
        except Exception as e:
            print(f"Error saving layout preset: {e}")
            
            # Call after save callbacks with failure
            for callback in self._after_save_callbacks.values():
                callback(preset_name, False)
                
            return False

    def load_layout_preset(self, preset_name: str) -> bool:
        """
        Load a layout preset.
        
        Args:
            preset_name: Name of the preset to load
            
        Returns:
            True if loaded successfully
        """
        # Call before load callbacks
        for callback in self._before_load_callbacks.values():
            callback(preset_name)
            
        # Check if preset exists in memory
        if preset_name in self._layout_presets:
            success = self.apply_layout(self._layout_presets[preset_name])
            
            # Call after load callbacks
            for callback in self._after_load_callbacks.values():
                callback(preset_name, success)
                
            return success
            
        # Try to load from file
        file_path = os.path.join(self._layouts_dir, f"{preset_name}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    layout_data = json.load(f)
                    
                # Store in memory for future use
                self._layout_presets[preset_name] = layout_data
                
                # Apply the layout
                success = self.apply_layout(layout_data)
                
                # Call after load callbacks
                for callback in self._after_load_callbacks.values():
                    callback(preset_name, success)
                    
                return success
            except Exception as e:
                print(f"Error loading layout preset: {e}")
                
                # Call after load callbacks with failure
                for callback in self._after_load_callbacks.values():
                    callback(preset_name, False)
        
        return False
            
    def get_available_presets(self) -> List[str]:
        """
        Get a list of available layout presets.
        
        Returns:
            List of preset names
        """
        presets = set(self._layout_presets.keys())
        
        # Add presets from files
        try:
            if os.path.exists(self._layouts_dir):
                for filename in os.listdir(self._layouts_dir):
                    if filename.endswith(".json"):
                        preset_name = os.path.splitext(filename)[0]
                        presets.add(preset_name)
        except Exception as e:
            print(f"Error listing layout presets: {e}")
            
        return sorted(list(presets))
    
    def delete_layout_preset(self, preset_name: str) -> bool:
        """
        Delete a layout preset.
        
        Args:
            preset_name: Name of the preset to delete
            
        Returns:
            True if deleted successfully
        """
        # Remove from memory
        if preset_name in self._layout_presets:
            del self._layout_presets[preset_name]
            
        # Remove file if it exists
        try:
            file_path = os.path.join(self._layouts_dir, f"{preset_name}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"Error deleting layout preset: {e}")
            
        return False
        
    def add_before_save_callback(self, callback_id: str, callback: Callable[[str], None]) -> None:
        """
        Add a callback to be called before a layout is saved.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call before layout save
        """
        self._before_save_callbacks[callback_id] = callback
        
    def add_after_save_callback(self, callback_id: str, 
                              callback: Callable[[str, bool], None]) -> None:
        """
        Add a callback to be called after a layout is saved.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call after layout save
        """
        self._after_save_callbacks[callback_id] = callback
        
    def add_before_load_callback(self, callback_id: str, callback: Callable[[str], None]) -> None:
        """
        Add a callback to be called before a layout is loaded.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call before layout load
        """
        self._before_load_callbacks[callback_id] = callback
        
    def add_after_load_callback(self, callback_id: str, 
                              callback: Callable[[str, bool], None]) -> None:
        """
        Add a callback to be called after a layout is loaded.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call after layout load
        """
        self._after_load_callbacks[callback_id] = callback
        
    def remove_callback(self, callback_id: str) -> None:
        """
        Remove a callback by ID.
        
        Args:
            callback_id: ID of the callback to remove
        """
        if callback_id in self._before_save_callbacks:
            del self._before_save_callbacks[callback_id]
        if callback_id in self._after_save_callbacks:
            del self._after_save_callbacks[callback_id]
        if callback_id in self._before_load_callbacks:
            del self._before_load_callbacks[callback_id]
        if callback_id in self._after_load_callbacks:
            del self._after_load_callbacks[callback_id]


def get_layout_manager():
    """Get the singleton layout manager instance."""
    return LayoutManager.get_instance()