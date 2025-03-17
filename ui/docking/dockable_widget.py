"""
Dockable Widget base class for PySignalDecipher.

This module provides the base class for all dockable widgets in the application,
with support for serialization, theming, and workspace-specific behavior.
"""

from PySide6.QtWidgets import QDockWidget, QWidget, QMenu, QApplication, QVBoxLayout, QFrame
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QEvent, QSize

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
    
    # Signal emitted when the widget is activated (gets focus)
    widget_activated = Signal(str)  # widget ID
    
    # Signal emitted when the widget title changes
    title_changed = Signal(str, str)  # widget ID, new title
    
    def __init__(self, title, parent=None, widget_id=None):
        """
        Initialize the dockable widget.
        
        Args:
            title: Title for the widget
            parent: Parent widget (typically the main window)
            widget_id: Unique identifier for this widget (defaults to class name)
        """
        super().__init__(title, parent)
        
        # Create a container frame that will receive styling
        self._style_container = QFrame()
        self._style_container.setObjectName("dockStyleContainer")
        self._style_container.setFrameShape(QFrame.NoFrame)
        self._style_container.setAutoFillBackground(True)  # Important for background color
        
        # Create layout for the style container
        self._container_layout = QVBoxLayout(self._style_container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(0)
        
        # Initialize with an empty content widget
        # (subclasses will set their own content)
        self._content_widget = QWidget()
        
        # Make sure content widget is transparent to allow container's background to show
        self._content_widget.setAutoFillBackground(False)
        self._content_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # Set the ObjectName for the content widget to allow QSS targeting
        self._content_widget.setObjectName("dockContent")
        
        # Add content widget to the style container
        self._container_layout.addWidget(self._content_widget)
        
        # Set the style container as the dock widget's widget
        self.setWidget(self._style_container)
        
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
        if self._theme_manager:
            self._theme_manager.theme_changed.connect(self._on_theme_changed)
        
        # Default attributes
        self._active = False
        self._can_close = True
        self._color_option = None
        self._workspace_type = None
        self._workspace = None  # Reference to the containing workspace

        # Set focus policies so that focus events are generated
        self.setFocusPolicy(Qt.StrongFocus)
        self._content_widget.setFocusPolicy(Qt.StrongFocus)
        self._style_container.setFocusPolicy(Qt.StrongFocus)

        # Connect signals
        self._connect_signals()
        
        # Customize context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Install event filter to handle focus events
        self.installEventFilter(self)
        self._content_widget.installEventFilter(self)
        self._style_container.installEventFilter(self)
    
    def _connect_signals(self):
        """Connect internal signals."""
        # Connect visibility changed signal
        self.visibilityChanged.connect(self._on_visibility_changed)
        
        # Connect docking state changed
        self.topLevelChanged.connect(self._on_top_level_changed)
        
        # Connect title changed signal
        self.windowTitleChanged.connect(self._on_title_changed)
    
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
        
    def _on_title_changed(self, title):
        """
        Handle title changes.
        
        Args:
            title: New title
        """
        # Emit title changed signal
        self.title_changed.emit(self._widget_id, title)
    
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
        
    def set_workspace(self, workspace):
        """
        Set the workspace this widget belongs to.
        
        Args:
            workspace: Reference to the workspace widget
        """
        self._workspace = workspace
        
    def get_workspace(self):
        """
        Get the workspace this widget belongs to.
        
        Returns:
            The workspace widget, or None if not set
        """
        return self._workspace
    
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
    
    def get_can_close(self):
        """
        Check if this widget can be closed.
        
        Returns:
            bool: True if the widget can be closed, False otherwise
        """
        return self._can_close
    
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

    def mousePressEvent(self, event):
        """
        Explicitly set focus when the widget is clicked.
        """
        self.setFocus(Qt.MouseFocusReason)
        super().mousePressEvent(event)
        
    def eventFilter(self, obj, event):
        """
        Filter events for this widget.
        
        Args:
            obj: Object that triggered the event
            event: Event object
            
        Returns:
            bool: True if the event was handled, False to continue processing
        """
        if obj == self or obj == self._content_widget or obj == self._style_container:
            if event.type() == QEvent.FocusIn:
                self.set_active(True)
                # Emit the widget_activated signal
                self.widget_activated.emit(self._widget_id)
            elif event.type() == QEvent.FocusOut:
                # Only deactivate if focus is leaving the dock widget
                # and not going to one of its children
                current_focus = QApplication.focusWidget()
                if not self.isAncestorOf(current_focus):
                    self.set_active(False)
        
        # Continue event processing
        return super().eventFilter(obj, event)
    
    def set_active(self, active):
        """
        Set this dock widget as active/inactive.
        
        Args:
            active: Whether the widget is active
        """
        if self._active != active:
            self._active = active
            
            # Set property on both the dock widget and the style container for QSS targeting
            self.setProperty("active", "true" if active else "false")
            self._style_container.setProperty("active", "true" if active else "false")
            
            # Force style update on both widgets
            self.style().unpolish(self)
            self.style().polish(self)
            self._style_container.style().unpolish(self._style_container)
            self._style_container.style().polish(self._style_container)
            
            # Update both widgets
            self.update()
            self._style_container.update()
    
    def is_active(self):
        """
        Check if this dock widget is active.
        
        Returns:
            bool: True if active, False otherwise
        """
        return self._active
    
    def set_color_option(self, color_option):
        """
        Set the color option for this dock widget.
        
        Args:
            color_option: Color option (blue, green, red, neutral, or None)
        """
        if self._color_option != color_option:
            self._color_option = color_option
            
            # Set property on both the dock widget and the style container for QSS targeting
            if color_option:
                self.setProperty("color-option", color_option)
                self._style_container.setProperty("color-option", color_option)
            else:
                self.setProperty("color-option", "")
                self._style_container.setProperty("color-option", "")
            
            # Force style update on both widgets
            self.style().unpolish(self)
            self.style().polish(self)
            self._style_container.style().unpolish(self._style_container)
            self._style_container.style().polish(self._style_container)
            
            # Update both widgets
            self.update()
            self._style_container.update()
    
    def get_color_option(self):
        """
        Get the current color option.
        
        Returns:
            str: Color option or None
        """
        return self._color_option
    
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
        
        # Color submenu
        color_menu = QMenu("Color Option", self)
        
        # Default color action
        default_action = QAction("Default", color_menu)
        default_action.setCheckable(True)
        default_action.setChecked(self._color_option is None)
        default_action.triggered.connect(lambda: self.set_color_option(None))
        color_menu.addAction(default_action)
        
        # Blue color action
        blue_action = QAction("Blue", color_menu)
        blue_action.setCheckable(True)
        blue_action.setChecked(self._color_option == "blue")
        blue_action.triggered.connect(lambda: self.set_color_option("blue"))
        color_menu.addAction(blue_action)
        
        # Green color action
        green_action = QAction("Green", color_menu)
        green_action.setCheckable(True)
        green_action.setChecked(self._color_option == "green")
        green_action.triggered.connect(lambda: self.set_color_option("green"))
        color_menu.addAction(green_action)
        
        # Red color action
        red_action = QAction("Red", color_menu)
        red_action.setCheckable(True)
        red_action.setChecked(self._color_option == "red")
        red_action.triggered.connect(lambda: self.set_color_option("red"))
        color_menu.addAction(red_action)
        
        # Neutral color action
        neutral_action = QAction("Neutral", color_menu)
        neutral_action.setCheckable(True)
        neutral_action.setChecked(self._color_option == "neutral")
        neutral_action.triggered.connect(lambda: self.set_color_option("neutral"))
        color_menu.addAction(neutral_action)
        
        menu.addMenu(color_menu)
        
        # Add separator
        menu.addSeparator()
        
        # Rename action
        rename_action = QAction("Rename...", self)
        rename_action.triggered.connect(self._show_rename_dialog)
        menu.addAction(rename_action)
        
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
    
    def _show_rename_dialog(self):
        """Show a dialog to rename the dock widget."""
        from PySide6.QtWidgets import QInputDialog
        
        # Get the new title
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Dock",
            "Enter new title:",
            text=self.windowTitle()
        )
        
        # Update the title if the user clicked OK
        if ok and new_title:
            self.setWindowTitle(new_title)
    
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
            "workspace_type": self._workspace_type,
            "color_option": self._color_option
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
            
        if "color_option" in state:
            self.set_color_option(state["color_option"])
            
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
            
        # Apply theme to the content widget if it supports it
        content = self._content_widget
        if content and hasattr(content, 'apply_theme') and callable(getattr(content, 'apply_theme', None)):
            try:
                content.apply_theme(self._theme_manager)
            except Exception as e:
                print(f"Error applying theme to content widget: {e}")
                
    def sizeHint(self):
        """
        Provide a size hint for the dock widget.
        
        Subclasses should override this method to provide a suitable size hint.
        
        Returns:
            QSize: Suggested size for the dock
        """
        return QSize(300, 200)
    
    def minimumSizeHint(self):
        """
        Provide a minimum size hint for the dock widget.
        
        Returns:
            QSize: Minimum suggested size for the dock
        """
        return QSize(200, 100)
    
    def get_dock_manager(self):
        """
        Get the dock manager for the application.
        
        This is a convenience method for accessing the DockManager from a dock widget.
        
        Returns:
            The DockManager instance
        """
        return ServiceRegistry.get_dock_manager()
    
    def get_other_docks(self, dock_type=None):
        """
        Get other dock widgets in the same workspace.
        
        Args:
            dock_type: Optional type of docks to filter by
            
        Returns:
            List of dock widgets
        """
        # Get the dock manager
        dock_manager = self.get_dock_manager()
        if not dock_manager:
            return []
            
        # Get all docks for this workspace
        all_docks = dock_manager.get_docks_for_workspace(self._workspace_type)
        
        # Filter out this dock
        other_docks = [dock for dock_id, dock in all_docks.items() if dock_id != self._widget_id]
        
        # Filter by type if specified
        if dock_type:
            # Get the dock class for the specified type
            from .dock_manager import DockRegistry
            dock_class = DockRegistry.get_dock_type(dock_type)
            
            if dock_class:
                other_docks = [dock for dock in other_docks if isinstance(dock, dock_class)]
                
        return other_docks
    
    def get_dock_by_id(self, dock_id):
        """
        Get a dock widget by its ID in the same workspace.
        
        Args:
            dock_id: ID of the dock to get
            
        Returns:
            The dock widget, or None if not found
        """
        # Get the dock manager
        dock_manager = self.get_dock_manager()
        if not dock_manager:
            return None
            
        # Get the dock
        return dock_manager.get_dock(self._workspace_type, dock_id)
        
    def broadcast_message(self, message_type, data=None):
        """
        Broadcast a message to all docks in the same workspace.
        
        This is a simple way to communicate with other docks without tight coupling.
        Each dock can decide to handle or ignore the message as needed.
        
        Args:
            message_type: Type of message to broadcast
            data: Optional data to include with the message
        """
        # Get other docks
        other_docks = self.get_other_docks()
        
        # Broadcast the message to each dock
        for dock in other_docks:
            if hasattr(dock, 'handle_message') and callable(dock.handle_message):
                dock.handle_message(message_type, data, self._widget_id)
    
    def handle_message(self, message_type, data=None, sender_id=None):
        """
        Handle a message from another dock.
        
        Subclasses should override this method to handle messages as needed.
        
        Args:
            message_type: Type of message
            data: Optional data included with the message
            sender_id: ID of the dock that sent the message
        """
        # Default implementation does nothing
        pass