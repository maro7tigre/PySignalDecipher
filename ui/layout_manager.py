"""
Layout Manager for PySignalDecipher.

This module provides a central management system for workspace layouts,
including saving, loading, and applying window configurations.
"""

import os
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QApplication, 
    QMenu, QDialog, QVBoxLayout, QListWidget,
    QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QListWidgetItem
)
from PySide6.QtCore import Qt, QByteArray, QSettings, QObject, Signal
from PySide6.QtGui import QAction
from command_system.command_manager import CommandManager


@dataclass
class DockWidgetState:
    """Data class representing the state of a dock widget."""
    
    # Widget identifier
    id: str
    
    # Visibility state
    visible: bool = True
    
    # Whether the widget is floating
    floating: bool = False
    
    # Geometry when floating (x, y, width, height)
    geometry: Tuple[int, int, int, int] = field(default_factory=lambda: (100, 100, 300, 200))
    
    # Area where the widget is docked
    area: int = Qt.LeftDockWidgetArea
    
    # For tabbed docking, the tab position (index)
    tab_position: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DockWidgetState':
        """Create from dictionary after deserialization."""
        return cls(**data)


@dataclass
class LayoutDefinition:
    """Data class representing a complete layout definition."""
    
    # Layout identifier
    id: str
    
    # Human-readable name
    name: str
    
    # Type of workspace this layout is for
    workspace_type: str
    
    # Whether this is the default layout for the workspace type
    is_default: bool = False
    
    # States of all dock widgets in this layout
    dock_states: Dict[str, DockWidgetState] = field(default_factory=dict)
    
    # Main window state (encoded as Base64 string)
    window_state: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "workspace_type": self.workspace_type,
            "is_default": self.is_default,
            "dock_states": {k: v.to_dict() for k, v in self.dock_states.items()},
            "window_state": self.window_state
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayoutDefinition':
        """Create from dictionary after deserialization."""
        # Create a copy of the data to modify
        data_copy = data.copy()
        
        # Convert dock states dictionaries to DockWidgetState objects
        if "dock_states" in data_copy:
            dock_states = {}
            for k, v in data_copy["dock_states"].items():
                dock_states[k] = DockWidgetState.from_dict(v)
            data_copy["dock_states"] = dock_states
            
        return cls(**data_copy)


class LayoutManager(QObject):
    """
    Manages the arrangement and configuration of dockable windows.
    
    Provides functionality for creating, saving, and loading window layouts,
    as well as applying them to workspace areas.
    """
    
    # Signal emitted when a layout is applied
    layout_applied = Signal(str, str)  # workspace_type, layout_id
    
    # Signal emitted when layouts are changed (added, removed, renamed)
    layouts_changed = Signal()
    
    def __init__(self, preferences_manager=None):
        """
        Initialize the layout manager.
        
        Args:
            preferences_manager: Optional reference to the PreferencesManager
        """
        super().__init__()
        
        # Get command manager for accessing services
        self._command_manager = CommandManager.instance()
        
        # Get preferences manager from parameter or command manager
        self._preferences_manager = preferences_manager
        if self._preferences_manager is None and self._command_manager:
            from utils.preferences_manager import PreferencesManager
            self._preferences_manager = self._command_manager.get_service(PreferencesManager)
        
        # Dictionary to store active layouts by workspace type
        self._active_layouts = {}
        
        # Layouts directory
        self._layouts_dir = os.path.join("assets", "layouts")
        os.makedirs(self._layouts_dir, exist_ok=True)
        
        # Load all available layouts
        self._available_layouts = self._load_available_layouts()
        
        # Load active layout settings
        self._load_active_layout_settings()
    
    def _load_available_layouts(self) -> Dict[str, Dict[str, LayoutDefinition]]:
        """
        Load all available layouts from layout files.
        
        Returns:
            Dictionary mapping workspace types to layout definitions
        """
        layouts = {}
        
        # Check for layout files
        if not os.path.exists(self._layouts_dir):
            return layouts
        
        for filename in os.listdir(self._layouts_dir):
            if filename.endswith(".layout"):
                try:
                    with open(os.path.join(self._layouts_dir, filename), 'r') as f:
                        layout_data = json.load(f)
                        layout = LayoutDefinition.from_dict(layout_data)
                        
                        # Create workspace type entry if it doesn't exist
                        if layout.workspace_type not in layouts:
                            layouts[layout.workspace_type] = {}
                            
                        # Add layout to its workspace type
                        layouts[layout.workspace_type][layout.id] = layout
                except (IOError, json.JSONDecodeError) as e:
                    print(f"Error loading layout file {filename}: {e}")
        
        return layouts
    
    def _load_active_layout_settings(self):
        """Load active layout settings from preferences."""
        if self._preferences_manager:
            active_layouts = self._preferences_manager.get_preference("layouts/active", {})
            if isinstance(active_layouts, dict):
                self._active_layouts = active_layouts
    
    def _save_active_layout_settings(self):
        """Save active layout settings to preferences."""
        if self._preferences_manager:
            self._preferences_manager.set_preference("layouts/active", self._active_layouts)
    
    def get_layouts_for_workspace(self, workspace_type: str) -> Dict[str, LayoutDefinition]:
        """
        Get all layouts available for a specific workspace type.
        
        Args:
            workspace_type: Type identifier for the workspace
            
        Returns:
            Dictionary of layout definitions for the workspace type
        """
        return self._available_layouts.get(workspace_type, {})
    
    def get_default_layout(self, workspace_type: str) -> Optional[LayoutDefinition]:
        """
        Get the default layout for a workspace type.
        
        Args:
            workspace_type: Type identifier for the workspace
            
        Returns:
            Default layout definition, or None if not found
        """
        layouts = self.get_layouts_for_workspace(workspace_type)
        for layout in layouts.values():
            if layout.is_default:
                return layout
        return None
    
    def get_active_layout(self, workspace_type: str) -> Optional[LayoutDefinition]:
        """
        Get the active layout for a workspace type.
        
        Args:
            workspace_type: Type identifier for the workspace
            
        Returns:
            Active layout definition, or None if not found
        """
        # Get the active layout ID
        active_id = self._active_layouts.get(workspace_type)
        if not active_id:
            # If no active layout, use the default
            default_layout = self.get_default_layout(workspace_type)
            if default_layout:
                return default_layout
            return None
            
        # Get the layout by ID
        layouts = self.get_layouts_for_workspace(workspace_type)
        return layouts.get(active_id)
    
    def set_active_layout(self, workspace_type: str, layout_id: str) -> bool:
        """
        Set the active layout for a workspace type.
        
        Args:
            workspace_type: Type identifier for the workspace
            layout_id: ID of the layout to set as active
            
        Returns:
            True if the layout was set, False if not found
        """
        layouts = self.get_layouts_for_workspace(workspace_type)
        if layout_id not in layouts:
            return False
            
        self._active_layouts[workspace_type] = layout_id
        self._save_active_layout_settings()
        return True
    
    def create_layout(self, workspace_type: str, name: str, main_window, 
                      is_default: bool = False) -> str:
        """
        Create a new layout from the current window state.
        
        Args:
            workspace_type: Type identifier for the workspace
            name: Human-readable name for the layout
            main_window: Main window to save the state from
            is_default: Whether this should be the default layout
            
        Returns:
            ID of the created layout
        """
        # Generate a unique ID
        layout_id = str(uuid.uuid4())
        
        # Create the layout definition
        layout = LayoutDefinition(
            id=layout_id,
            name=name,
            workspace_type=workspace_type,
            is_default=is_default
        )
        
        # Save the window state
        self._save_window_state(layout, main_window)
        
        # Add to available layouts
        if workspace_type not in self._available_layouts:
            self._available_layouts[workspace_type] = {}
        self._available_layouts[workspace_type][layout_id] = layout
        
        # If setting as default, update other layouts
        if is_default:
            self._update_default_layout(workspace_type, layout_id)
        
        # Save to file
        self._save_layout_to_file(layout)
        
        # Notify of layout changes
        self.layouts_changed.emit()
        
        return layout_id
    
    def _save_window_state(self, layout: LayoutDefinition, main_window: QMainWindow):
        """
        Save the window state to a layout definition.
        
        Args:
            layout: Layout definition to update
            main_window: Main window to save the state from
        """
        # Save main window state
        window_state = main_window.saveState()
        layout.window_state = self._byte_array_to_string(window_state)
        
        # Save dock widget states
        layout.dock_states = {}
        for dock in main_window.findChildren(QDockWidget):
            # Skip docks without object names
            if not dock.objectName():
                continue
                
            # Create state object
            state = DockWidgetState(
                id=dock.objectName(),
                visible=dock.isVisible(),
                floating=dock.isFloating(),
                area=main_window.dockWidgetArea(dock),
            )
            
            # Save geometry if floating
            if dock.isFloating():
                geo = dock.geometry()
                state.geometry = (geo.x(), geo.y(), geo.width(), geo.height())
            
            # Add to layout
            layout.dock_states[dock.objectName()] = state
    
    def _update_default_layout(self, workspace_type: str, new_default_id: str):
        """
        Update the default layout for a workspace type.
        
        Args:
            workspace_type: Type identifier for the workspace
            new_default_id: ID of the new default layout
        """
        if workspace_type not in self._available_layouts:
            return
            
        # Clear default flag from all other layouts
        for layout_id, layout in self._available_layouts[workspace_type].items():
            if layout_id != new_default_id:
                layout.is_default = False
                # Save changes to file
                self._save_layout_to_file(layout)
    
    def _save_layout_to_file(self, layout: LayoutDefinition):
        """
        Save a layout to a file.
        
        Args:
            layout: Layout definition to save
        """
        filename = os.path.join(self._layouts_dir, f"{layout.id}.layout")
        try:
            with open(filename, 'w') as f:
                json.dump(layout.to_dict(), f, indent=2)
        except IOError as e:
            print(f"Error saving layout file {filename}: {e}")
    
    def apply_layout(self, workspace_type: str, layout_id: str, main_window: QMainWindow) -> bool:
        """
        Apply a layout to a main window.
        
        Args:
            workspace_type: Type identifier for the workspace
            layout_id: ID of the layout to apply
            main_window: Main window to apply the layout to
            
        Returns:
            True if the layout was applied, False if not found
        """
        # Get the layout
        layouts = self.get_layouts_for_workspace(workspace_type)
        if layout_id not in layouts:
            return False
            
        layout = layouts[layout_id]
        
        # Apply dock widget states first
        for dock_id, state in layout.dock_states.items():
            dock = main_window.findChild(QDockWidget, dock_id)
            if dock:
                # Set visibility
                dock.setVisible(state.visible)
                
                # Set floating state
                dock.setFloating(state.floating)
                
                # Set geometry if floating
                if state.floating:
                    x, y, width, height = state.geometry
                    dock.setGeometry(x, y, width, height)
        
        # Apply main window state
        if layout.window_state:
            window_state = self._string_to_byte_array(layout.window_state)
            main_window.restoreState(window_state)
        
        # Update active layout
        self.set_active_layout(workspace_type, layout_id)
        
        # Emit signal
        self.layout_applied.emit(workspace_type, layout_id)
        
        return True
    
    def delete_layout(self, workspace_type: str, layout_id: str) -> bool:
        """
        Delete a layout.
        
        Args:
            workspace_type: Type identifier for the workspace
            layout_id: ID of the layout to delete
            
        Returns:
            True if the layout was deleted, False if not found
        """
        # Check if layout exists
        if (workspace_type not in self._available_layouts or
            layout_id not in self._available_layouts[workspace_type]):
            return False
        
        # Get layout for checking if it's the default
        layout = self._available_layouts[workspace_type][layout_id]
        was_default = layout.is_default
        
        # Remove from available layouts
        del self._available_layouts[workspace_type][layout_id]
        
        # Remove layout file
        filename = os.path.join(self._layouts_dir, f"{layout_id}.layout")
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except IOError as e:
            print(f"Error deleting layout file {filename}: {e}")
        
        # If this was the active layout, clear it
        if self._active_layouts.get(workspace_type) == layout_id:
            if workspace_type in self._active_layouts:
                del self._active_layouts[workspace_type]
            self._save_active_layout_settings()
        
        # If this was the default layout, set a new default if possible
        if was_default and self._available_layouts[workspace_type]:
            # Get the first layout and set it as default
            new_default_id = next(iter(self._available_layouts[workspace_type].keys()))
            new_default = self._available_layouts[workspace_type][new_default_id]
            new_default.is_default = True
            self._save_layout_to_file(new_default)
        
        # Notify of layout changes
        self.layouts_changed.emit()
        
        return True
    
    def rename_layout(self, workspace_type: str, layout_id: str, new_name: str) -> bool:
        """
        Rename a layout.
        
        Args:
            workspace_type: Type identifier for the workspace
            layout_id: ID of the layout to rename
            new_name: New name for the layout
            
        Returns:
            True if the layout was renamed, False if not found
        """
        # Check if layout exists
        if (workspace_type not in self._available_layouts or
            layout_id not in self._available_layouts[workspace_type]):
            return False
        
        # Update name
        self._available_layouts[workspace_type][layout_id].name = new_name
        
        # Save to file
        self._save_layout_to_file(self._available_layouts[workspace_type][layout_id])
        
        # Notify of layout changes
        self.layouts_changed.emit()
        
        return True
    
    def set_layout_as_default(self, workspace_type: str, layout_id: str) -> bool:
        """
        Set a layout as the default for a workspace type.
        
        Args:
            workspace_type: Type identifier for the workspace
            layout_id: ID of the layout to set as default
            
        Returns:
            True if the layout was set as default, False if not found
        """
        # Check if layout exists
        if (workspace_type not in self._available_layouts or
            layout_id not in self._available_layouts[workspace_type]):
            return False
        
        # Update default status
        self._update_default_layout(workspace_type, layout_id)
        self._available_layouts[workspace_type][layout_id].is_default = True
        
        # Save to file
        self._save_layout_to_file(self._available_layouts[workspace_type][layout_id])
        
        # Notify of layout changes
        self.layouts_changed.emit()
        
        return True
    
    def _byte_array_to_string(self, byte_array: QByteArray) -> str:
        """
        Convert a QByteArray to a string.
        
        Args:
            byte_array: QByteArray to convert
            
        Returns:
            Base64-encoded string representation
        """
        return bytes(byte_array.toBase64()).decode('ascii')
    
    def _string_to_byte_array(self, string: str) -> QByteArray:
        """
        Convert a string to a QByteArray.
        
        Args:
            string: Base64-encoded string to convert
            
        Returns:
            QByteArray from the string
        """
        return QByteArray.fromBase64(string.encode('ascii'))


class LayoutManagerDialog(QDialog):
    """
    Dialog for managing layouts.
    
    Allows users to create, rename, delete, and set default layouts.
    """
    
    def __init__(self, parent=None, layout_manager=None, workspace_type=None):
        """
        Initialize the layout manager dialog.
        
        Args:
            parent: Parent widget
            layout_manager: Reference to the LayoutManager
            workspace_type: Type of workspace to manage layouts for
        """
        super().__init__(parent)
        
        self.setWindowTitle("Manage Layouts")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        # If layout_manager is not provided, get it from CommandManager
        if layout_manager is None:
            command_manager = CommandManager.instance()
            if command_manager:
                layout_manager = command_manager.get_service(LayoutManager)
                
        # Store references
        self._layout_manager = layout_manager
        self._workspace_type = workspace_type
        
        # Set up UI
        self._setup_ui()
        
        # Populate layouts
        self._populate_layouts()
        
        # Connect to layout changes
        if self._layout_manager:
            self._layout_manager.layouts_changed.connect(self._populate_layouts)
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Layout list
        self._layout_list = QListWidget()
        layout.addWidget(self._layout_list)
        
        # Layout name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Layout Name:"))
        self._name_input = QLineEdit()
        name_layout.addWidget(self._name_input)
        layout.addLayout(name_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self._create_button = QPushButton("Create New")
        self._create_button.clicked.connect(self._create_layout)
        button_layout.addWidget(self._create_button)
        
        self._rename_button = QPushButton("Rename")
        self._rename_button.clicked.connect(self._rename_layout)
        button_layout.addWidget(self._rename_button)
        
        self._delete_button = QPushButton("Delete")
        self._delete_button.clicked.connect(self._delete_layout)
        button_layout.addWidget(self._delete_button)
        
        self._default_button = QPushButton("Set as Default")
        self._default_button.clicked.connect(self._set_default_layout)
        button_layout.addWidget(self._default_button)
        
        layout.addLayout(button_layout)
        
        # Dialog buttons
        self._button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self._button_box.accepted.connect(self.accept)
        layout.addWidget(self._button_box)
        
        # Connect selection changed
        self._layout_list.itemSelectionChanged.connect(self._update_button_states)
        
        # Initial button states
        self._update_button_states()
    
    def _populate_layouts(self):
        """Populate the layout list with available layouts."""
        self._layout_list.clear()
        
        if not self._workspace_type or not self._layout_manager:
            return
        
        layouts = self._layout_manager.get_layouts_for_workspace(self._workspace_type)
        active_layout_id = self._layout_manager._active_layouts.get(self._workspace_type)
        
        for layout_id, layout in layouts.items():
            item_text = layout.name
            
            # Add indicators for default and active layouts
            indicators = []
            if layout.is_default:
                indicators.append("Default")
            if layout_id == active_layout_id:
                indicators.append("Active")
                
            if indicators:
                item_text += f" ({', '.join(indicators)})"
                
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, layout_id)
            self._layout_list.addItem(item)
    
    def _update_button_states(self):
        """Update the enabled state of buttons based on selection."""
        has_selection = len(self._layout_list.selectedItems()) > 0
        
        self._rename_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)
        self._default_button.setEnabled(has_selection)
        
        # Update name input with selected layout name
        if has_selection:
            selected_item = self._layout_list.selectedItems()[0]
            layout_id = selected_item.data(Qt.UserRole)
            layouts = self._layout_manager.get_layouts_for_workspace(self._workspace_type)
            layout = layouts[layout_id]
            self._name_input.setText(layout.name)
        else:
            self._name_input.clear()
    
    def _create_layout(self):
        """Create a new layout."""
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid layout name.")
            return
            
        # Get the main window
        main_window = self.parent().window()
        
        # Create the layout
        self._layout_manager.create_layout(
            self._workspace_type,
            name,
            main_window,
            is_default=not bool(self._layout_list.count())  # Default if first layout
        )
    
    def _rename_layout(self):
        """Rename the selected layout."""
        # Get selected layout
        selected_items = self._layout_list.selectedItems()
        if not selected_items:
            return
            
        layout_id = selected_items[0].data(Qt.UserRole)
        
        # Get new name
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid layout name.")
            return
            
        # Rename the layout
        self._layout_manager.rename_layout(self._workspace_type, layout_id, name)
    
    def _delete_layout(self):
        """Delete the selected layout."""
        # Get selected layout
        selected_items = self._layout_list.selectedItems()
        if not selected_items:
            return
            
        layout_id = selected_items[0].data(Qt.UserRole)
        
        # Confirm deletion
        layouts = self._layout_manager.get_layouts_for_workspace(self._workspace_type)
        layout = layouts[layout_id]
        
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the layout '{layout.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            self._layout_manager.delete_layout(self._workspace_type, layout_id)
    
    def _set_default_layout(self):
        """Set the selected layout as the default."""
        # Get selected layout
        selected_items = self._layout_list.selectedItems()
        if not selected_items:
            return
            
        layout_id = selected_items[0].data(Qt.UserRole)
        
        # Set as default
        self._layout_manager.set_layout_as_default(self._workspace_type, layout_id)