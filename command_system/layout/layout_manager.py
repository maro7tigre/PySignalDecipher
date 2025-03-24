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
        # TODO: Replace layout capturing functionality
        #
        # This method was responsible for:
        # 1. Capturing main window state and geometry
        # 2. Capturing all registered widget states
        # 3. Capturing dock tabification relationships
        #
        # Expected inputs:
        #   - None (uses internal widget registry)
        #
        # Expected outputs:
        #   - Dictionary with complete layout state
        #
        # Called from:
        #   - save_layout_preset()
        #   - save_layout_with_project()
        #
        # Created a data structure with:
        #   - Main window geometry and state
        #   - Individual widget states
        #   - Dock widget relationships and ordering
        pass
    
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
        # TODO: Replace widget state capturing
        #
        # This method was responsible for:
        # 1. Capturing state of a specific widget
        # 2. Adding special handling for different widget types
        #    (QSplitter, QTabWidget, QDockWidget)
        #
        # Expected inputs:
        #   - QWidget instance
        #
        # Expected outputs:
        #   - Dictionary with widget state
        #
        # Called from:
        #   - capture_current_layout()
        #
        # Captured properties like:
        #   - Geometry (position and size)
        #   - Visibility
        #   - Special properties for specific widget types
        pass
        
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
        # TODO: Replace layout application functionality
        #
        # This method was responsible for:
        # 1. Restoring widget states from layout data
        # 2. Restoring main window state
        # 3. Restoring tabified dock relationships
        #
        # Expected inputs:
        #   - Dictionary with layout data
        #
        # Expected outputs:
        #   - Boolean indicating success
        #
        # Called from:
        #   - load_layout_preset()
        #   - load_layout_from_project()
        #
        # Handled scaling for window size differences
        # Restored widgets in specific order (non-docks first, then docks in creation order)
        pass
            
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
        # TODO: Replace widget state restoration
        #
        # This method was responsible for:
        # 1. Getting or creating the widget
        # 2. Applying geometry with scaling
        # 3. Setting visibility and specific widget state
        #
        # Expected inputs:
        #   - Widget ID
        #   - Widget state dictionary
        #   - Horizontal and vertical scaling factors
        #
        # Expected outputs:
        #   - None (modifies widgets directly)
        #
        # Called from:
        #   - apply_layout()
        #
        # Handled specific widget types:
        #   - QSplitter (sizes)
        #   - QTabWidget (current tab)
        #   - QDockWidget (area, floating state)
        pass
        
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
        # TODO: Replace layout preset saving
        #
        # This method was responsible for:
        # 1. Capturing current layout data
        # 2. Storing layout in memory and in file
        # 3. Using serialize_layout() from layout_serialization.py
        #
        # Expected inputs:
        #   - Preset name
        #
        # Expected outputs:
        #   - Boolean indicating success
        #
        # Called:
        #   - self.capture_current_layout() to get layout data
        #   - serialize_layout() from layout_serialization.py to convert to JSON
        #
        # Stored presets in self._layout_presets and in self._layouts_dir directory
        pass

    def load_layout_preset(self, preset_name: str) -> bool:
        # TODO: Replace layout preset loading
        #
        # This method was responsible for:
        # 1. Finding layout preset in memory or on disk
        # 2. Deserializing layout using deserialize_layout()
        # 3. Applying the layout
        #
        # Expected inputs:
        #   - Preset name
        #
        # Expected outputs:
        #   - Boolean indicating success
        #
        # Called:
        #   - deserialize_layout() from layout_serialization.py
        #   - self.apply_layout() to restore the layout
        #
        # Looked for presets in memory first, then in self._layouts_dir directory
        pass
            
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