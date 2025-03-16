"""
Utility panel for PySignalDecipher.

This module provides a utility panel that appears above the workspace tabs
and contains tools for hardware connection, workspace-specific utilities,
and widget-specific utilities.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QTabWidget, QSizePolicy, QSplitter
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QCursor

from core.service_registry import ServiceRegistry
from .hardware_utility import HardwareUtilityPanel
from .workspace_utility_manager import WorkspaceUtilityManager
from .widget_utility_manager import WidgetUtilityManager


class ResizeHandle(QWidget):
    """
    A custom resize handle widget that allows users to resize the utility panel.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the resize handle.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Set fixed height but expand horizontally
        self.setFixedHeight(8)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Set cursor to indicate resizing
        self.setCursor(QCursor(Qt.SizeVerCursor))
        
        # Track mouse press state
        self._pressed = False
        
    def paintEvent(self, event):
        """Draw the handle with subtle indicators for user feedback."""
        from PySide6.QtGui import QPainter, QColor, QPen
        
        painter = QPainter(self)
        painter.setPen(QPen(QColor(120, 120, 120, 100), 1))
        
        # Draw three horizontal lines as a visual indicator
        height = self.height()
        width = self.width()
        
        for i in range(3):
            y = height // 2 - 3 + (i * 3)
            painter.drawLine(20, y, width - 20, y)
            
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self._pressed = True
            # Store global cursor position
            self._start_pos = event.globalPosition().toPoint()
            # Store parent's height
            self._start_height = self.parent().height()
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events for resizing."""
        if self._pressed:
            # Calculate vertical movement
            delta = event.globalPosition().toPoint().y() - self._start_pos.y()
            # Apply new height to parent, ensuring it stays within limits
            new_height = max(100, min(400, self._start_height + delta))
            self.parent().setFixedHeight(new_height)
            
            # Store the new height in settings
            if hasattr(self.parent(), '_preferences_manager'):
                self.parent()._preferences_manager.set_preference(
                    "ui/utility_panel_height", new_height)
                
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class UtilityPanel(QWidget):
    """
    Main utility panel that combines hardware connection, workspace utilities,
    and widget utilities into a unified interface.
    
    This panel is displayed at the top of the main window and contains
    multiple sections for different types of utilities.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the utility panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Get services from registry
        self._theme_manager = ServiceRegistry.get_theme_manager()
        self._preferences_manager = None
        
        # Set up the panel layout and sections
        self._setup_ui()
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Default height
        self._default_height = 150
        self.setFixedHeight(self._default_height)
        
    def _setup_ui(self):
        """Set up the user interface for the utility panel."""
        # Main layout (vertical to include resize handle)
        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)
        
        # Content layout (horizontal layout for sections side by side)
        self._content_widget = QWidget()
        self._main_layout = QHBoxLayout(self._content_widget)
        self._main_layout.setContentsMargins(4, 4, 4, 4)
        self._main_layout.setSpacing(8)

        # Hardware utility section
        self._hardware_utility = HardwareUtilityPanel()
        self._hardware_utility.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._main_layout.addWidget(self._hardware_utility)

        # Workspace utility section
        self._workspace_utility_group = QGroupBox("Workspace Utilities")
        workspace_layout = QVBoxLayout(self._workspace_utility_group)
        workspace_layout.setContentsMargins(4, 12, 4, 4)  # Reduced margins
        self._workspace_utility_manager = WorkspaceUtilityManager()

        workspace_layout.addWidget(self._workspace_utility_manager)
        self._workspace_utility_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._main_layout.addWidget(self._workspace_utility_group, 1)  # Give stretch for workspace utilities

        # Widget utility section
        self._widget_utility_group = QGroupBox("Selected Element")
        widget_layout = QVBoxLayout(self._widget_utility_group)
        widget_layout.setContentsMargins(4, 12, 4, 4)  # Reduced margins
        self._widget_utility_manager = WidgetUtilityManager()
        widget_layout.addWidget(self._widget_utility_manager)
        self._widget_utility_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._main_layout.addWidget(self._widget_utility_group, 1)  # Give stretch for widget utilities
        
        # Add content to the outer layout
        self._outer_layout.addWidget(self._content_widget)
        
        # Add resize handle at the bottom
        self._resize_handle = ResizeHandle()
        self._outer_layout.addWidget(self._resize_handle)

    def set_preferences_manager(self, preferences_manager):
        """
        Set the preferences manager to store panel height.
        
        Args:
            preferences_manager: Reference to the PreferencesManager
        """
        self._preferences_manager = preferences_manager
        
        # Restore saved height if available
        saved_height = self._preferences_manager.get_preference("ui/utility_panel_height")
        if saved_height is not None:
            # Ensure the height is within reasonable bounds
            self.setFixedHeight(max(100, min(400, saved_height)))
        
    def set_active_workspace(self, workspace_id, workspace_widget):
        """
        Update the workspace utility section based on the active workspace.
        
        Args:
            workspace_id: ID of the active workspace
            workspace_widget: Reference to the workspace widget
        """
        self._workspace_utility_manager.set_active_workspace(workspace_id, workspace_widget)
        
    def set_selected_widget(self, widget_type, widget):
        """
        Update the widget utility section based on the selected widget.
        
        Args:
            widget_type: Type of the selected widget
            widget: Reference to the selected widget
        """
        self._widget_utility_manager.set_selected_widget(widget_type, widget)
        
    def apply_theme(self, theme_manager=None):
        """
        Apply the current theme to the utility panel.
        
        Args:
            theme_manager: Optional theme manager reference (uses registry if None)
        """
        if theme_manager:
            self._theme_manager = theme_manager
        
        # Apply theme to child components
        self._hardware_utility.apply_theme(self._theme_manager)
        self._workspace_utility_manager.apply_theme(self._theme_manager)
        self._widget_utility_manager.apply_theme(self._theme_manager)
        
        # Apply theme to resize handle
        handle_color = self._theme_manager.get_color("border.inactive", "#CCCCCC")
        self._resize_handle.setStyleSheet(f"background-color: {handle_color};")