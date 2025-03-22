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

from .layout_serialization import serialize_layout, deserialize_layout


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
        
    def set_main_window(self, main_window: QMainWindow) -> None:
        """
        Set the main window for the layout manager.
        
        Args:
            main_window: Main application window
        """
        self._main_window = main_window
        
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
        Capture the current UI layout.
        
        Returns:
            Dictionary containing layout data
        """
        if not self._main_window:
            return {}
            
        # Capture main window state
        layout_data = {
            "main_window": {
                "geometry": self._main_window.saveGeometry().toBase64().data().decode('ascii'),
                "state": self._main_window.saveState().toBase64().data().decode('ascii'),
                "size": {
                    "width": self._main_window.width(),
                    "height": self._main_window.height()
                }
            },
            "widgets": {},
            "dock_creation_order": self._dock_creation_order.copy()
        }
        
        # Capture registered widget states
        for widget_id, widget in self._registered_widgets.items():
            widget_data = self._capture_widget_state(widget)
            if widget_data:
                layout_data["widgets"][widget_id] = widget_data
        
        # Capture dock tabification relationships
        layout_data["tabified_docks"] = self._capture_tabified_docks()
                
        return layout_data
    
    def _capture_tabified_docks(self) -> List[List[str]]:
        """
        Capture groups of tabified docks.
        
        Returns:
            List of lists, where each inner list contains the IDs of docks that are tabified together
        """
        if not self._main_window:
            return []
            
        # Find all dock widgets
        all_docks = [dock for dock_id, dock in self._registered_widgets.items() 
                     if isinstance(dock, QDockWidget)]
        
        # Track processed docks to avoid duplicates
        processed_docks = set()
        tabified_groups = []
        
        # For each dock, find all docks tabified with it
        for dock in all_docks:
            if dock in processed_docks:
                continue
                
            # Get the dock ID
            dock_id = self._get_widget_id(dock)
            if not dock_id:
                continue
                
            # Get tabified docks
            tabified_docks = self._main_window.tabifiedDockWidgets(dock)
            
            # If there are tabified docks, create a group
            if tabified_docks:
                group = [dock_id]
                for tabified_dock in tabified_docks:
                    tabified_id = self._get_widget_id(tabified_dock)
                    if tabified_id:
                        group.append(tabified_id)
                        processed_docks.add(tabified_dock)
                
                tabified_groups.append(group)
                processed_docks.add(dock)
        
        return tabified_groups
        
    def _get_widget_id(self, widget: QWidget) -> Optional[str]:
        """
        Get the ID for a registered widget.
        
        Args:
            widget: Widget to find ID for
            
        Returns:
            Widget ID, or None if not found
        """
        for widget_id, registered_widget in self._registered_widgets.items():
            if registered_widget == widget:
                return widget_id
        return None
        
    def _capture_widget_state(self, widget: QWidget) -> Dict[str, Any]:
        """
        Capture the state of a specific widget.
        
        Args:
            widget: Widget to capture state from
            
        Returns:
            Dictionary with widget state data
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
        
    def _get_dock_area(self, dock_widget: QDockWidget) -> Any:
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
        
    def apply_layout(self, layout_data: Dict[str, Any]) -> bool:
        """
        Apply a saved layout.
        
        Args:
            layout_data: Layout data dictionary
            
        Returns:
            True if layout was applied successfully
        """
        if not self._main_window or not layout_data:
            return False
            
        try:
            # Get main window info
            main_window_data = layout_data.get("main_window", {})
            
            # Calculate scaling factors if window size has changed
            current_size = (self._main_window.width(), self._main_window.height())
            saved_size = main_window_data.get("size", {})
            saved_width = saved_size.get("width", current_size[0])
            saved_height = saved_size.get("height", current_size[1])
            
            # Only scale if dimensions are significantly different
            scale_x = current_size[0] / saved_width if abs(current_size[0] - saved_width) > 10 else 1.0
            scale_y = current_size[1] / saved_height if abs(current_size[1] - saved_height) > 10 else 1.0
            
            # Get dock creation order from layout data
            dock_creation_order = layout_data.get("dock_creation_order", [])
            
            # First, restore basic widget states
            widget_data = layout_data.get("widgets", {})
            
            # First pass: Apply state to non-dock widgets
            for widget_id, state in widget_data.items():
                if not isinstance(self._get_or_create_widget(widget_id, state), QDockWidget):
                    self._restore_widget_state(widget_id, state, scale_x, scale_y)
                    
            # Second pass: Apply state to dock widgets in creation order
            # Restore dock widgets in the saved creation order
            for dock_id in dock_creation_order:
                if dock_id in widget_data:
                    self._restore_widget_state(dock_id, widget_data[dock_id], scale_x, scale_y)
                    
            # Restore main window state if specified
            if "state" in main_window_data:
                try:
                    state_bytes = QByteArray.fromBase64(main_window_data["state"].encode('ascii'))
                    self._main_window.restoreState(state_bytes)
                except Exception as e:
                    print(f"Error restoring main window state: {e}")
                    
            # Restore tabified dock relationships
            self._restore_tabified_docks(layout_data.get("tabified_docks", []))
                
            return True
            
        except Exception as e:
            print(f"Error applying layout: {e}")
            return False
            
    def _restore_tabified_docks(self, tabified_groups: List[List[str]]) -> None:
        """
        Restore tabified dock relationships.
        
        Args:
            tabified_groups: List of groups of tabified dock IDs
        """
        if not self._main_window:
            return
            
        for group in tabified_groups:
            if len(group) < 2:
                continue
                
            # Get the first dock in the group
            first_dock = self._registered_widgets.get(group[0])
            if not first_dock or not isinstance(first_dock, QDockWidget):
                continue
                
            # Tabify the remaining docks with the first one
            for dock_id in group[1:]:
                dock = self._registered_widgets.get(dock_id)
                if dock and isinstance(dock, QDockWidget):
                    self._main_window.tabifyDockWidget(first_dock, dock)
        
    def _restore_widget_state(self, widget_id: str, state: Dict[str, Any], 
                             scale_x: float, scale_y: float) -> None:
        """
        Restore a widget's state.
        
        Args:
            widget_id: ID of the widget to restore
            state: Widget state data
            scale_x: Horizontal scaling factor
            scale_y: Vertical scaling factor
        """
        # Get widget or create if missing
        widget = self._get_or_create_widget(widget_id, state)
        if not widget:
            return
            
        # Apply geometry with scaling
        if "geometry" in state:
            geometry = state["geometry"]
            scaled_geometry = QRect(
                int(geometry["x"] * scale_x),
                int(geometry["y"] * scale_y),
                int(geometry["width"] * scale_x),
                int(geometry["height"] * scale_y)
            )
            widget.setGeometry(scaled_geometry)
            
        # Set visibility
        if "visible" in state:
            widget.setVisible(state["visible"])
            
        # Handle specific widget types
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
                
        elif isinstance(widget, QTabWidget) and "tabs" in state:
            tabs_data = state["tabs"]
            
            # Set active tab
            current_tab = tabs_data.get("current", 0)
            if 0 <= current_tab < widget.count():
                widget.setCurrentIndex(current_tab)
                
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
        Save current layout as a preset.
        
        Args:
            preset_name: Name of the preset
            
        Returns:
            True if saved successfully
        """
        # Capture current layout
        layout_data = self.capture_current_layout()
        if not layout_data:
            return False
            
        # Add to in-memory presets
        self._layout_presets[preset_name] = layout_data
        
        # Save to file
        try:
            os.makedirs(self._layouts_dir, exist_ok=True)
            
            file_path = os.path.join(self._layouts_dir, f"{preset_name}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json_str = serialize_layout(layout_data)
                f.write(json_str)
                
            return True
        except Exception as e:
            print(f"Error saving layout preset: {e}")
            return False
            
    def load_layout_preset(self, preset_name: str) -> bool:
        """
        Load and apply a saved layout preset.
        
        Args:
            preset_name: Name of the preset
            
        Returns:
            True if loaded and applied successfully
        """
        # Check if already in memory
        if preset_name in self._layout_presets:
            return self.apply_layout(self._layout_presets[preset_name])
            
        # Try to load from file
        try:
            file_path = os.path.join(self._layouts_dir, f"{preset_name}.json")
            
            if not os.path.exists(file_path):
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                json_str = f.read()
                layout_data = deserialize_layout(json_str)
                
            # Store in memory for future use
            self._layout_presets[preset_name] = layout_data
            
            # Apply layout
            return self.apply_layout(layout_data)
            
        except Exception as e:
            print(f"Error loading layout preset: {e}")
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


def get_layout_manager():
    """Get the singleton layout manager instance."""
    return LayoutManager.get_instance()