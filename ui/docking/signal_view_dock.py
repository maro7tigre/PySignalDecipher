"""
Signal View Dock widget for PySignalDecipher.

This module provides a dockable signal visualization widget.
"""

from PySide6.QtWidgets import QVBoxLayout, QLabel, QMenu, QWidget
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal

from .dockable_widget import DockableWidget


class SignalViewDock(DockableWidget):
    """
    Dockable widget for signal visualization.
    
    Provides a container for signal viewing and analysis with
    appropriate controls and menus.
    """
    
    # Signal emitted when the view configuration changes
    view_config_changed = Signal(dict)
    
    def __init__(self, title="Signal View", parent=None, widget_id=None):
        """
        Initialize the signal view dock.
        
        Args:
            title: Title for the dock widget
            parent: Parent widget
            widget_id: Unique identifier for this widget
        """
        # Generate a widget ID if not provided
        if widget_id is None:
            import uuid
            widget_id = f"signal_view_{str(uuid.uuid4())[:8]}"
            
        super().__init__(title, parent, widget_id)
        
        # Default view configuration
        self._view_config = {
            "display_mode": "time",
            "show_grid": True,
            "show_markers": True,
            "y_scale": "linear"
        }
        
        # Set up the content widget
        self._setup_content()
    
    def _setup_content(self):
        """Set up the content widget with signal visualization."""
        # Create a layout for the content widget
        layout = QVBoxLayout(self._content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder for actual signal view
        # In a real implementation, this would be a custom signal visualization widget
        placeholder = QLabel("Signal Visualization Widget Placeholder")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setAutoFillBackground(False)  # Important: Keep transparent to show parent background
        placeholder.setAttribute(Qt.WA_TranslucentBackground, True)  # Ensure transparency
        
        # No direct styling - rely on QSS
        layout.addWidget(placeholder)
    
    def _add_context_menu_items(self, menu):
        """
        Add signal view specific items to the context menu.
        
        Args:
            menu: Menu to add items to
        """
        # Display mode submenu
        display_menu = QMenu("Display Mode", menu)
        
        # Add display mode options
        time_action = QAction("Time Domain", display_menu)
        time_action.setCheckable(True)
        time_action.setChecked(self._view_config["display_mode"] == "time")
        time_action.triggered.connect(lambda: self._set_display_mode("time"))
        display_menu.addAction(time_action)
        
        freq_action = QAction("Frequency Domain", display_menu)
        freq_action.setCheckable(True)
        freq_action.setChecked(self._view_config["display_mode"] == "frequency")
        freq_action.triggered.connect(lambda: self._set_display_mode("frequency"))
        display_menu.addAction(freq_action)
        
        waterfall_action = QAction("Waterfall", display_menu)
        waterfall_action.setCheckable(True)
        waterfall_action.setChecked(self._view_config["display_mode"] == "waterfall")
        waterfall_action.triggered.connect(lambda: self._set_display_mode("waterfall"))
        display_menu.addAction(waterfall_action)
        
        menu.addMenu(display_menu)
        
        # Add separator
        menu.addSeparator()
        
        # Grid toggle
        grid_action = QAction("Show Grid", menu)
        grid_action.setCheckable(True)
        grid_action.setChecked(self._view_config["show_grid"])
        grid_action.triggered.connect(self._toggle_grid)
        menu.addAction(grid_action)
        
        # Markers toggle
        markers_action = QAction("Show Markers", menu)
        markers_action.setCheckable(True)
        markers_action.setChecked(self._view_config["show_markers"])
        markers_action.triggered.connect(self._toggle_markers)
        menu.addAction(markers_action)
        
        # Y-axis scale submenu
        scale_menu = QMenu("Y-Axis Scale", menu)
        
        linear_action = QAction("Linear", scale_menu)
        linear_action.setCheckable(True)
        linear_action.setChecked(self._view_config["y_scale"] == "linear")
        linear_action.triggered.connect(lambda: self._set_y_scale("linear"))
        scale_menu.addAction(linear_action)
        
        log_action = QAction("Logarithmic", scale_menu)
        log_action.setCheckable(True)
        log_action.setChecked(self._view_config["y_scale"] == "log")
        log_action.triggered.connect(lambda: self._set_y_scale("log"))
        scale_menu.addAction(log_action)
        
        db_action = QAction("Decibel", scale_menu)
        db_action.setCheckable(True)
        db_action.setChecked(self._view_config["y_scale"] == "db")
        db_action.triggered.connect(lambda: self._set_y_scale("db"))
        scale_menu.addAction(db_action)
        
        menu.addMenu(scale_menu)
    
    def _set_display_mode(self, mode):
        """
        Set the display mode.
        
        Args:
            mode: New display mode
        """
        if self._view_config["display_mode"] != mode:
            self._view_config["display_mode"] = mode
            self.view_config_changed.emit(self._view_config)
    
    def _toggle_grid(self, show):
        """
        Toggle grid visibility.
        
        Args:
            show: Whether to show the grid
        """
        if self._view_config["show_grid"] != show:
            self._view_config["show_grid"] = show
            self.view_config_changed.emit(self._view_config)
    
    def _toggle_markers(self, show):
        """
        Toggle marker visibility.
        
        Args:
            show: Whether to show markers
        """
        if self._view_config["show_markers"] != show:
            self._view_config["show_markers"] = show
            self.view_config_changed.emit(self._view_config)
    
    def _set_y_scale(self, scale):
        """
        Set the Y-axis scale.
        
        Args:
            scale: New Y-axis scale
        """
        if self._view_config["y_scale"] != scale:
            self._view_config["y_scale"] = scale
            self.view_config_changed.emit(self._view_config)
    
    def save_state(self):
        """
        Save widget state including view configuration.
        
        Returns:
            dict: State dictionary
        """
        state = super().save_state()
        state["view_config"] = self._view_config.copy()
        return state
    
    def restore_state(self, state):
        """
        Restore widget state including view configuration.
        
        Args:
            state: State dictionary
            
        Returns:
            bool: True if the state was restored successfully
        """
        # Restore base state
        result = super().restore_state(state)
        
        # Restore view configuration
        if "view_config" in state:
            self._view_config = state["view_config"]
            # Emit signal to update the view
            self.view_config_changed.emit(self._view_config)
            
        return result