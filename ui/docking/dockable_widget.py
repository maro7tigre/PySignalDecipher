"""
Dockable Widget base class for PySignalDecipher.

This module provides the base class for all dockable widgets in the application,
with support for serialization, theming, and workspace-specific behavior.
"""

from PySide6.QtWidgets import QDockWidget, QWidget, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QEvent

from core.service_registry import ServiceRegistry
from ..themed_widgets.base_themed_widget import BaseThemedWidget


class DockableWidget(QDockWidget):
    """
    Base class for all dockable widgets in the application.
    
    Provides common functionality for docking, floating, serialization,
    and integration with the theme system.
    """
    
    # Signal emitted when the widget is closed
    widget_closed = Signal(str)  # widget ID
    
    # Signal emitted when the widget state changes (floating, docked, etc.)
    state_changed = Signal()
    
    def __init__(self, title, parent=None, widget_id=None):
        """
        Initialize the dockable widget.
        
        Args:
            title: Title for the widget
            parent: Parent widget (typically the main window)
            widget_id: Unique identifier for this widget (defaults to class name)
        """
        super().__init__(title, parent)
        
        # Initialize with an empty content widget
        # (subclasses will set their own content)
        self._content_widget = QWidget()
        
        # Set the ObjectName for the content widget to allow QSS targeting
        self._content_widget.setObjectName("dockContent")
        
        self.setWidget(self._content_widget)
        
        # Set up object name as widget ID for layout management
        self._widget_id = widget_id or self.__class__.__name__
        self.setObjectName(self._widget_id)
        
        # Set default features
        self.setFeatures(
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable
        )
        
        # Get theme manager from registry
        self._theme_manager = ServiceRegistry.get_theme_manager()
        
        # Connect to theme change signal to update styling when theme changes
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
        
        # Default attributes
        self._can_close = True
        self._workspace_type = None
        
        # Connect signals
        self._connect_signals()
        
        # Customize context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Clear any local stylesheet to ensure QSS theme takes precedence
        self.setStyleSheet("")
    
    def _connect_signals(self):
        """Connect internal signals."""
        # Connect visibility changed signal
        self.visibilityChanged.connect(self._on_visibility_changed)
        
        # Connect docking state changed
        self.topLevelChanged.connect(self._on_top_level_changed)
    
    def _on_visibility_changed(self, visible):
        """
        Handle visibility changes.
        
        Args:
            visible: Whether the widget is visible
        """
        # Emit state changed signal
        self.state_changed.emit()
    
    def _on_top_level_changed(self, top_level):
        """
        Handle changes to floating state.
        
        Args:
            top_level: Whether the widget is now floating
        """
        # Emit state changed signal
        self.state_changed.emit()
        
    def _on_theme_changed(self, theme_name):
        """
        Handle theme changes.
        
        Args:
            theme_name: Name of the new theme
        """
        # Apply new theme
        self.apply_theme(self._theme_manager)
    
    def get_widget_id(self):
        """
        Get the widget's unique identifier.
        
        Returns:
            str: Widget ID
        """
        return self._widget_id
    
    def set_workspace_type(self, workspace_type):
        """
        Set the workspace type this widget belongs to.
        
        Args:
            workspace_type: Type identifier for the workspace
        """
        self._workspace_type = workspace_type
    
    def get_workspace_type(self):
        """
        Get the workspace type this widget belongs to.
        
        Returns:
            str: Workspace type identifier
        """
        return self._workspace_type
    
    def set_can_close(self, can_close):
        """
        Set whether this widget can be closed.
        
        Args:
            can_close: Whether the widget can be closed
        """
        self._can_close = can_close
        features = self.features()
        
        if can_close:
            features |= QDockWidget.DockWidgetClosable
        else:
            features &= ~QDockWidget.DockWidgetClosable
            
        self.setFeatures(features)
    
    def closeEvent(self, event):
        """
        Handle close events.
        
        Args:
            event: Close event
        """
        if not self._can_close:
            event.ignore()
            return
            
        # Emit closed signal before accepting
        self.widget_closed.emit(self._widget_id)
        
        # Accept the event
        event.accept()
        
        # Call the parent class method
        super().closeEvent(event)
    
    def _show_context_menu(self, pos):
        """
        Show the custom context menu.
        
        Args:
            pos: Position where the menu should be shown
        """
        menu = QMenu(self)
        
        # Float action
        float_action = QAction("Float", self)
        float_action.setCheckable(True)
        float_action.setChecked(self.isFloating())
        float_action.triggered.connect(lambda checked: self.setFloating(checked))
        menu.addAction(float_action)
        
        # Close action (if closable)
        if self._can_close:
            close_action = QAction("Close", self)
            close_action.triggered.connect(self.close)
            menu.addAction(close_action)
        
        # Add any additional context menu items
        self._add_context_menu_items(menu)
        
        # Show the menu
        menu.exec_(self.mapToGlobal(pos))
    
    def _add_context_menu_items(self, menu):
        """
        Add additional items to the context menu.
        
        To be overridden by subclasses.
        
        Args:
            menu: Menu to add items to
        """
        pass
    
    def save_state(self):
        """
        Save the widget state for serialization.
        
        To be extended by subclasses to save additional state.
        
        Returns:
            dict: State dictionary
        """
        return {
            "id": self._widget_id,
            "title": self.windowTitle(),
            "geometry": self.saveGeometry().toBase64().data().decode('ascii'),
            "floating": self.isFloating(),
            "visible": self.isVisible(),
            "workspace_type": self._workspace_type
        }
    
    def restore_state(self, state):
        """
        Restore the widget state from serialization.
        
        To be extended by subclasses to restore additional state.
        
        Args:
            state: State dictionary
            
        Returns:
            bool: True if the state was restored successfully
        """
        # Restore basic properties
        if "title" in state:
            self.setWindowTitle(state["title"])
            
        if "floating" in state:
            self.setFloating(state["floating"])
            
        if "visible" in state:
            self.setVisible(state["visible"])
            
        if "workspace_type" in state:
            self._workspace_type = state["workspace_type"]
            
        # Restore geometry if present
        if "geometry" in state:
            from PySide6.QtCore import QByteArray
            try:
                geometry = QByteArray.fromBase64(state["geometry"].encode('ascii'))
                self.restoreGeometry(geometry)
                return True
            except Exception as e:
                print(f"Error restoring geometry for {self._widget_id}: {e}")
                
        return False
    
    def apply_theme(self, theme_manager=None):
        """
        Apply the current theme to the widget.
        
        Args:
            theme_manager: Optional theme manager reference
        """
        if theme_manager:
            self._theme_manager = theme_manager
            
        # The actual styling is handled by the QSS files now,
        # but we can set some specific properties if needed
        
        # Apply theme to the content widget if it supports it
        content = self.widget()
        if content and hasattr(content, 'apply_theme') and callable(content.apply_theme):
            content.apply_theme(self._theme_manager)