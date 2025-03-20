"""
command_system/ui/widgets/base.py
Base class for all command-aware widgets - with fix for observer_id
"""

from typing import Any, Optional, Callable, TypeVar, Generic, Dict, Type
from ...command import Command, PropertyCommand
from ...command_manager import get_command_manager
from ...observable import Observable

T = TypeVar('T')


class CommandWidgetBase(Generic[T]):
    """
    Base mixin class for command-aware widgets.
    
    This class handles the integration with the command system for widgets.
    It should be used as a mixin with Qt widgets.
    """
    
    def __init__(self):
        """Initialize command widget base."""
        # This will be called by the actual widget's __init__
        self._command_enabled = True
        self._command_manager = get_command_manager()
        self._value_property_name = None  # Must be set by subclass
        self._observable_model = None
        self._observable_property = None
        self._observer_id = None  # Fixed: Initialize the observer_id
        self._is_updating = False
        self._old_value = None
        self._custom_command_factory = None
        
    def _setup_command_widget(self, value_property_name: str):
        """
        Set up the command widget with the property name to track.
        
        Args:
            value_property_name: Name of the widget property to track
        """
        self._value_property_name = value_property_name
        
    def enable_commands(self, enabled: bool = True):
        """
        Enable or disable command creation for this widget.
        
        Args:
            enabled: True to enable commands, False to disable
        """
        self._command_enabled = enabled
        
    def bind_to_model(self, model: Observable, property_name: str):
        """
        Bind widget to an observable model property.
        
        Args:
            model: Observable model
            property_name: Property name to bind to
        """
        # Unbind any existing connection
        self.unbind_from_model()
        
        # Store model and property
        self._observable_model = model
        self._observable_property = property_name
        
        # Connect model changes to widget
        self._observer_id = model.add_property_observer(property_name, self._on_model_property_changed)
        
        # Initial update from model
        self._update_widget_from_model()
        
    def unbind_from_model(self):
        """Unbind widget from model."""
        if self._observable_model and self._observable_property and self._observer_id:
            # Remove observer
            self._observable_model.remove_property_observer(
                self._observable_property, self._observer_id
            )
            self._observable_model = None
            self._observable_property = None
            self._observer_id = None
            
    def _update_widget_from_model(self):
        """Update widget value from bound model."""
        if not self._observable_model or not self._observable_property:
            return
            
        # Get value from model
        value = getattr(self._observable_model, self._observable_property)
        
        # Set widget value without creating a command
        self._is_updating = True
        try:
            self._set_widget_value(value)
        finally:
            self._is_updating = False
            
    def _on_model_property_changed(self, property_name: str, old_value: Any, new_value: Any):
        """Called when bound model property changes."""
        # Update widget without creating a command
        self._is_updating = True
        try:
            self._set_widget_value(new_value)
        finally:
            self._is_updating = False
            
    def _on_widget_value_changed(self, *args, **kwargs):
        """
        Called when widget value changes.
        This should be connected to the widget's value change signal.
        """
        # Skip if we're updating from model
        if self._is_updating:
            return
            
        # Get current value
        new_value = self._get_widget_value()
        
        # Update model if bound
        if self._observable_model and self._observable_property:
            # Get current model value for comparison
            current_model_value = getattr(self._observable_model, self._observable_property)
            
            # Only proceed if value actually changed
            if new_value != current_model_value:
                if self._command_enabled:
                    # Create and execute command
                    cmd = self._create_property_command(new_value)
                    if cmd:  # Only execute if command was created
                        self._command_manager.execute(cmd)
                else:
                    # Update model directly
                    setattr(self._observable_model, self._observable_property, new_value)
                
    def _begin_edit(self):
        """Called when user begins editing the widget value."""
        self._old_value = self._get_widget_value()
        
    def _end_edit(self):
        """Called when user finishes editing the widget value."""
        # If old and new values are different, create a command
        new_value = self._get_widget_value()
        if self._old_value != new_value:
            if self._command_enabled and self._observable_model and self._observable_property:
                cmd = self._create_property_command(new_value, self._old_value)
                self._command_manager.execute(cmd)
                
    def _create_property_command(self, new_value: Any, old_value: Any = None) -> Command:
        """
        Create a property command for the current change.
        
        Args:
            new_value: New property value
            old_value: Optional old value (will be retrieved from model if not provided)
            
        Returns:
            Command for this property change
        """
        # Skip if the value is the same as current model value
        current_model_value = getattr(self._observable_model, self._observable_property, None)
        if new_value == current_model_value:
            return None
            
        if self._custom_command_factory:
            # Use custom command factory if provided
            return self._custom_command_factory(
                self._observable_model, 
                self._observable_property,
                new_value,
                old_value if old_value is not None else current_model_value
            )
        else:
            # Use default PropertyCommand
            return PropertyCommand(
                self._observable_model,
                self._observable_property,
                new_value
            )
            
    def set_command_factory(self, factory: Callable[[Observable, str, Any, Any], Command]):
        """
        Set a custom command factory for this widget.
        
        Args:
            factory: Function that takes (model, property_name, new_value, old_value)
                    and returns a Command instance
        """
        self._custom_command_factory = factory
        
    def _get_widget_value(self) -> Any:
        """
        Get the widget's current value.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _get_widget_value")
        
    def _set_widget_value(self, value: Any):
        """
        Set the widget's value.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _set_widget_value")