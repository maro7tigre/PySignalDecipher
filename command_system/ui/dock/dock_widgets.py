"""
Command-aware dock widgets that integrate with the dock management system.
"""
from typing import Optional, Any, Dict, List

from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget

from ...command_manager import get_command_manager
from ...observable import Observable
from .dock_manager import get_dock_manager
from .dock_commands import DockLocationCommand


class CommandDockWidget(QDockWidget):
    """
    A command-aware dock widget that automatically creates commands
    for position, floating state, and other property changes.
    """
    
    # Signal emitted when the dock is about to be closed via the close button
    closeRequested = Signal(str)  # Emits dock_id
    
    def __init__(self, dock_id: str, title: str, parent: Optional[QMainWindow] = None,
                model: Optional[Observable] = None):
        """
        Initialize the command dock widget.
        
        Args:
            dock_id: Unique identifier for this dock
            title: Title to display in the dock header
            parent: Parent widget (typically the main window)
            model: Optional Observable model associated with this dock
        """
        super().__init__(title, parent)
        
        # Store properties
        self.dock_id = dock_id
        self.model = model
        
        # Get managers
        self.dock_manager = get_dock_manager()
        self.command_manager = get_command_manager()
        
        # Register with dock manager
        if parent and isinstance(parent, QMainWindow):
            self.dock_manager.set_main_window(parent)
        
        # Set up event handling
        self.installEventFilter(self)
        
        # Flag to track changes
        self._is_updating = False
        self._location_command = None
        
        # Connect signals
        self.topLevelChanged.connect(self._on_floating_changed)
        self.dockLocationChanged.connect(self._on_dock_location_changed)
        
    def closeEvent(self, event):
        """Handle the close event to emit signal instead of just closing."""
        # Emit signal when close button is clicked
        self.closeRequested.emit(self.dock_id)
        
        # Prevent actual close - this allows the owner to decide whether to close
        # and use proper command-based removal if desired
        event.ignore()
        
    def eventFilter(self, obj, event):
        """
        Filter events to detect dock position and size changes.
        
        Args:
            obj: Object receiving the event
            event: The event
            
        Returns:
            True if event was handled, otherwise let the event propagate
        """
        if obj == self:
            if event.type() == QEvent.Move or event.type() == QEvent.Resize:
                # Create a command if this is a user-initiated change
                if not self._is_updating and self.isFloating():
                    self._handle_geometry_change()
                    
        return super().eventFilter(obj, event)
        
    def _handle_geometry_change(self):
        """Handle dock geometry change by creating a location command."""
        # Start tracking changes if not already tracking
        if self._location_command is None:
            self._location_command = DockLocationCommand(self.dock_id)
            
        # Schedule command execution when event loop is idle
        # This ensures we only create one command for multiple resize/move events
        QTimer.singleShot(100, self._finish_geometry_change)
        
    def _finish_geometry_change(self):
        """Finalize geometry change by executing the command."""
        if self._location_command:
            self.command_manager.execute(self._location_command)
            self._location_command = None
            
    def _on_floating_changed(self, floating):
        """Handle dock floating state changes."""
        if not self._is_updating:
            command = DockLocationCommand(self.dock_id)
            self.command_manager.execute(command)
            
    def _on_dock_location_changed(self):
        """Handle dock area changes."""
        if not self._is_updating:
            command = DockLocationCommand(self.dock_id)
            self.command_manager.execute(command)
            
    def setWidget(self, widget: QWidget):
        """Override to associate widget with this dock."""
        super().setWidget(widget)
        
        # Store widget reference in model if applicable
        if hasattr(self, 'model') and self.model is not None:
            if hasattr(self.model, 'widget') and isinstance(getattr(self.model, 'widget', None), property):
                # If there's a property descriptor for 'widget', use it
                setattr(self.model, 'widget', widget)
            else:
                # Otherwise just set the attribute directly
                self.model._widget = widget


class ObservableDockWidget(CommandDockWidget):
    """
    A command-aware dock widget that is also an Observable object.
    This allows binding properties of the dock itself to models.
    """
    
    def __init__(self, dock_id: str, title: str, parent: Optional[QMainWindow] = None,
                model: Optional[Observable] = None):
        """
        Initialize the observable dock widget.
        
        Args:
            dock_id: Unique identifier for this dock
            title: Title to display in the dock header
            parent: Parent widget (typically the main window)
            model: Optional Observable model associated with this dock
        """
        super().__init__(dock_id, title, parent, model)
        
        # Create Observable model for dock properties
        from ...observable import Observable, ObservableProperty
        
        # Save initial values for class definition
        _initial_title = title
        _initial_floating = self.isFloating()
        _initial_visible = self.isVisible()
        
        class DockProperties(Observable):
            title = ObservableProperty[str](default=_initial_title)
            is_floating = ObservableProperty[bool](default=_initial_floating)
            is_visible = ObservableProperty[bool](default=_initial_visible)
            
        self.properties = DockProperties()
        
        # Connect property changes
        self.properties.add_property_observer('title', self._on_title_property_changed)
        self.properties.add_property_observer('is_floating', self._on_floating_property_changed)
        self.properties.add_property_observer('is_visible', self._on_visible_property_changed)
        
        # Connect widget changes to update the properties
        self.topLevelChanged.connect(self._update_floating_property)
        
    def _on_title_property_changed(self, property_name, old_value, new_value):
        """Update dock title when property changes."""
        if old_value != new_value:
            self._is_updating = True
            try:
                self.setWindowTitle(new_value)
            finally:
                self._is_updating = False
                
    def _on_floating_property_changed(self, property_name, old_value, new_value):
        """Update dock floating state when property changes."""
        if old_value != new_value:
            self._is_updating = True
            try:
                self.setFloating(new_value)
            finally:
                self._is_updating = False
                
    def _on_visible_property_changed(self, property_name, old_value, new_value):
        """Update dock visibility when property changes."""
        if old_value != new_value:
            self._is_updating = True
            try:
                self.setVisible(new_value)
            finally:
                self._is_updating = False
                
    def _update_floating_property(self, floating):
        """Update floating property when dock state changes."""
        if not self._is_updating and self.properties.is_floating != floating:
            self.properties.is_floating = floating
            
    def setVisible(self, visible):
        """Override to update the visible property."""
        super().setVisible(visible)
        
        # Update property if different
        if not self._is_updating and hasattr(self, 'properties'):
            if self.properties.is_visible != visible:
                self.properties.is_visible = visible
                
    def setWindowTitle(self, title):
        """Override to update the title property."""
        super().setWindowTitle(title)
        
        # Update property if different
        if not self._is_updating and hasattr(self, 'properties'):
            if self.properties.title != title:
                self.properties.title = title