"""
Command-aware dock widgets for the command system.
"""

from typing import Optional, Any, Dict, List

from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget

from ...core.command_manager import get_command_manager
from ...core.observable import Observable, ObservableProperty
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
                model: Optional[Observable] = None, dock_type: str = None):
        """
        Initialize the command dock widget.
        
        Args:
            dock_id: Unique identifier for this dock
            title: Title to display in the dock header
            parent: Parent widget (typically the main window)
            model: Optional Observable model associated with this dock
            dock_type: Type identifier for serialization
        """
        super().__init__(title, parent)
        
        # Store properties
        self.dock_id = dock_id
        self.model = model
        self.dock_type = dock_type or self.__class__.__name__

        # Set objectName to match dock_id - this ensures Qt can track the widget
        self.setObjectName(dock_id)
    
        # Get managers
        self.dock_manager = get_dock_manager()
        self.command_manager = get_command_manager()
        
        # Register with dock manager
        if parent and isinstance(parent, QMainWindow):
            self.dock_manager.set_main_window(parent)
        
        # Flag to track changes
        self._is_updating = False
        self._location_command = None
        self._movement_timer = None
        
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

    def moveEvent(self, event):
        """Handle move events for floating docks."""
        super().moveEvent(event)
        if not self._is_updating and self.isFloating():
            self._handle_geometry_change()

    def resizeEvent(self, event):
        """Handle resize events for docks."""
        super().resizeEvent(event)
        if not self._is_updating and self.isFloating():
            self._handle_geometry_change()
        
    def _handle_geometry_change(self):
        """Handle dock geometry change by creating a location command."""
        # Start tracking changes if not already tracking
        if self._location_command is None:
            self._location_command = DockLocationCommand(self.dock_id)
            
        # Use a timer to batch changes instead of creating too many commands
        if self._movement_timer is not None:
            self._movement_timer.stop()
            
        self._movement_timer = QTimer(self)
        self._movement_timer.setSingleShot(True)
        self._movement_timer.timeout.connect(self._finish_geometry_change)
        self._movement_timer.start(150)  # Adjust timing as needed
            
    def _finish_geometry_change(self):
        """Finalize geometry change by executing the command."""
        if self._location_command:
            try:
                self.command_manager.execute(self._location_command)
            except Exception as e:
                print(f"Error executing location command: {e}")
            self._location_command = None
        self._movement_timer = None
            
    def _on_floating_changed(self, floating):
        """Handle dock floating state changes."""
        if not self._is_updating:
            try:
                command = DockLocationCommand(self.dock_id)
                self.command_manager.execute(command)
            except Exception as e:
                print(f"Error on floating change: {e}")
            
    def _on_dock_location_changed(self):
        """Handle dock area changes."""
        if not self._is_updating:
            try:
                command = DockLocationCommand(self.dock_id)
                self.command_manager.execute(command)
            except Exception as e:
                print(f"Error on dock location change: {e}")
            
    def setWidget(self, widget: QWidget):
        """Override to associate widget with this dock."""
        super().setWidget(widget)
        
        # Store widget reference in model if applicable
        if hasattr(self, 'model') and self.model is not None:
            if hasattr(self.model, 'widget') and isinstance(getattr(self.model, 'widget', None), property):
                # If there's a property descriptor for 'widget', use it
                try:
                    setattr(self.model, 'widget', widget)
                except Exception:
                    # Fallback to direct attribute if property setter fails
                    self.model._widget = widget
            else:
                # Otherwise just set the attribute directly
                self.model._widget = widget


class ObservableDockWidget(CommandDockWidget):
    """
    A command-aware dock widget that is also an Observable object.
    This allows binding properties of the dock itself to models.
    """
    
    def __init__(self, dock_id: str, title: str, parent: Optional[QMainWindow] = None,
                model: Optional[Observable] = None, dock_type: str = None):
        """
        Initialize the observable dock widget.
        
        Args:
            dock_id: Unique identifier for this dock
            title: Title to display in the dock header
            parent: Parent widget (typically the main window)
            model: Optional Observable model associated with this dock
            dock_type: Type identifier for serialization
        """
        super().__init__(dock_id, title, parent, model, dock_type)
        
        # Create Observable model for dock properties
        from ...core.observable import Observable, ObservableProperty
        
        # Save initial values for class definition
        _initial_title = title
        _initial_floating = self.isFloating()
        _initial_visible = self.isVisible()
        
        class DockProperties(Observable):
            title = ObservableProperty[str](default=_initial_title)
            is_floating = ObservableProperty[bool](default=_initial_floating)
            is_visible = ObservableProperty[bool](default=_initial_visible)
            
        self.properties = DockProperties()
        self._property_updating = False
        
        # Connect property changes with error protection
        self.properties.add_property_observer('title', self._on_title_property_changed)
        self.properties.add_property_observer('is_floating', self._on_floating_property_changed)
        self.properties.add_property_observer('is_visible', self._on_visible_property_changed)
        
        # Connect widget signals instead of overriding methods
        self.topLevelChanged.connect(self._update_floating_property)
        
    def _on_title_property_changed(self, property_name, old_value, new_value):
        """Update dock title when property changes."""
        if old_value == new_value or self._property_updating:
            return
            
        self._property_updating = True
        try:
            super().setWindowTitle(new_value)
        except Exception as e:
            print(f"Error updating title: {e}")
        finally:
            self._property_updating = False
                
    def _on_floating_property_changed(self, property_name, old_value, new_value):
        """Update dock floating state when property changes."""
        if old_value == new_value or self._property_updating:
            return
            
        self._property_updating = True
        try:
            super().setFloating(new_value)
        except Exception as e:
            print(f"Error updating floating state: {e}")
        finally:
            self._property_updating = False
                
    def _on_visible_property_changed(self, property_name, old_value, new_value):
        """Update dock visibility when property changes."""
        if old_value == new_value or self._property_updating:
            return
            
        self._property_updating = True
        try:
            super().setVisible(new_value)
        except Exception as e:
            print(f"Error updating visibility: {e}")
        finally:
            self._property_updating = False
                
    def _update_floating_property(self, floating):
        """Update floating property when dock state changes."""
        if self._property_updating or self._is_updating:
            return
            
        if self.properties.is_floating != floating:
            self._property_updating = True
            try:
                self.properties.is_floating = floating
            finally:
                self._property_updating = False
            
    def setVisible(self, visible):
        """Override to update the visible property."""
        super().setVisible(visible)
        
        # Update property if different
        if self._property_updating or self._is_updating:
            return
            
        if hasattr(self, 'properties') and self.properties.is_visible != visible:
            self._property_updating = True
            try:
                self.properties.is_visible = visible
            finally:
                self._property_updating = False
                
    def setWindowTitle(self, title):
        """Override to update the title property."""
        super().setWindowTitle(title)
        
        # Update property if different
        if self._property_updating or self._is_updating:
            return
            
        if hasattr(self, 'properties') and self.properties.title != title:
            self._property_updating = True
            try:
                self.properties.title = title
            finally:
                self._property_updating = False